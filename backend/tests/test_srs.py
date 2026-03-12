import os
import time
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi.testclient import TestClient

JWT_SECRET = "test-jwt-secret"


@pytest.fixture(autouse=True)
def _mock_env():
    env = {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_KEY": "test-service-key",
        "JWT_SECRET": JWT_SECRET,
    }
    with patch.dict(os.environ, env):
        yield


@pytest.fixture()
def client():
    from app.main import app

    return TestClient(app)


def _make_token(
    user_id: str = "user-123",
    email: str = "test@example.com",
) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def _mock_srs_card(
    card_id: str = "card-1",
    problem_id: str = "prob-1",
    topic_id: str = "topic-1",
    ease_factor: float = 2.5,
    interval_days: float = 5.0,
    repetition_count: int = 3,
    next_review_date: str | None = None,
    last_review_date: str | None = None,
    status: str = "review",
) -> dict:
    today = date.today()
    return {
        "id": card_id,
        "user_id": "user-123",
        "problem_id": problem_id,
        "topic_id": topic_id,
        "card_type": "problem",
        "ease_factor": ease_factor,
        "interval_days": interval_days,
        "repetition_count": repetition_count,
        "next_review_date": next_review_date or today.isoformat(),
        "last_review_date": last_review_date
        or (today - timedelta(days=5)).isoformat(),
        "status": status,
    }


# --- GET /api/srs/session ---


def test_get_session_returns_due_cards(client):
    """Due cards are returned sorted by urgency."""
    token = _make_token()
    today = date.today()
    cards = [
        _mock_srs_card(
            "card-1",
            "prob-1",
            "topic-1",
            interval_days=5.0,
            next_review_date=today.isoformat(),
            last_review_date=(today - timedelta(days=10)).isoformat(),
        ),
        _mock_srs_card(
            "card-2",
            "prob-2",
            "topic-2",
            interval_days=5.0,
            next_review_date=today.isoformat(),
            last_review_date=(today - timedelta(days=5)).isoformat(),
        ),
    ]
    problems = [
        {
            "id": "prob-1",
            "problem_text": "Problem 1",
            "problem_images": None,
            "hints": None,
            "difficulty": "basic",
            "task_number": 1,
        },
        {
            "id": "prob-2",
            "problem_text": "Problem 2",
            "problem_images": None,
            "hints": None,
            "difficulty": "medium",
            "task_number": 2,
        },
    ]
    topics = [
        {"id": "topic-1", "title": "Topic 1", "task_number": 1},
        {"id": "topic-2", "title": "Topic 2", "task_number": 2},
    ]

    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "srs_cards":
            (
                mock_table.select.return_value
                .eq.return_value
                .lte.return_value
                .neq.return_value
                .execute.return_value
            ) = MagicMock(data=cards)
        elif name == "problems":
            (
                mock_table.select.return_value
                .in_.return_value
                .execute.return_value
            ) = MagicMock(data=problems)
        elif name == "topics":
            (
                mock_table.select.return_value
                .in_.return_value
                .execute.return_value
            ) = MagicMock(data=topics)
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch(
        "app.routers.srs.get_supabase_client",
        return_value=mock_client,
    ):
        resp = client.get(
            "/api/srs/session?max_cards=20",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_due"] == 2
    assert len(data["cards"]) == 2
    # Most urgent card first (card-1 has 10/5=2.0 urgency vs 5/5=1.0)
    assert data["cards"][0]["card_id"] == "card-1"
    assert data["cards"][1]["card_id"] == "card-2"


def test_get_session_empty(client):
    """No due cards → empty session."""
    token = _make_token()

    mock_client = MagicMock()
    (
        mock_client.table.return_value
        .select.return_value
        .eq.return_value
        .lte.return_value
        .neq.return_value
        .execute.return_value
    ) = MagicMock(data=[])

    with patch(
        "app.routers.srs.get_supabase_client",
        return_value=mock_client,
    ):
        resp = client.get(
            "/api/srs/session",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_due"] == 0
    assert data["cards"] == []


def test_get_session_no_auth(client):
    """Should require authentication."""
    resp = client.get("/api/srs/session")
    assert resp.status_code in (401, 403)


def test_get_session_respects_max_cards(client):
    """max_cards limits the session size."""
    token = _make_token()
    today = date.today()
    cards = [
        _mock_srs_card(
            f"card-{i}",
            f"prob-{i}",
            f"topic-{i}",
            next_review_date=today.isoformat(),
            last_review_date=(today - timedelta(days=5)).isoformat(),
        )
        for i in range(10)
    ]

    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "srs_cards":
            (
                mock_table.select.return_value
                .eq.return_value
                .lte.return_value
                .neq.return_value
                .execute.return_value
            ) = MagicMock(data=cards)
        elif name == "problems":
            (
                mock_table.select.return_value
                .in_.return_value
                .execute.return_value
            ) = MagicMock(data=[])
        elif name == "topics":
            (
                mock_table.select.return_value
                .in_.return_value
                .execute.return_value
            ) = MagicMock(data=[])
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch(
        "app.routers.srs.get_supabase_client",
        return_value=mock_client,
    ):
        resp = client.get(
            "/api/srs/session?max_cards=3",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_due"] == 10
    assert len(data["cards"]) == 3


# --- Interleaving ---


def test_interleave_no_3_consecutive_same_topic():
    """Interleave should prevent 3+ consecutive cards from same topic."""
    from app.routers.srs import _interleave

    cards = [
        {"topic_id": "A", "id": "1"},
        {"topic_id": "A", "id": "2"},
        {"topic_id": "A", "id": "3"},
        {"topic_id": "B", "id": "4"},
        {"topic_id": "B", "id": "5"},
    ]
    result = _interleave(cards, max_cards=5)
    assert len(result) == 5

    # Check no 3 consecutive same topic
    for i in range(len(result) - 2):
        topics = [
            result[j]["topic_id"] for j in range(i, i + 3)
        ]
        if topics[0] == topics[1] == topics[2]:
            pytest.fail(
                f"3 consecutive same topic at index {i}: {topics}"
            )


def test_interleave_all_same_topic():
    """If all cards are same topic, still returns them."""
    from app.routers.srs import _interleave

    cards = [{"topic_id": "A", "id": str(i)} for i in range(5)]
    result = _interleave(cards, max_cards=5)
    assert len(result) == 5


def test_interleave_empty():
    """Empty input → empty output."""
    from app.routers.srs import _interleave

    assert _interleave([], max_cards=10) == []


# --- POST /api/srs/review ---


def test_review_good_assessment(client):
    """Good review updates card and returns next review info."""
    token = _make_token()
    card = _mock_srs_card(
        "card-1", "prob-1", "topic-1",
        ease_factor=2.5, interval_days=5.0, repetition_count=3,
    )

    mock_client = MagicMock()
    call_counts = {"srs_cards": 0, "users": 0}

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "srs_cards":
            call_counts["srs_cards"] += 1
            if call_counts["srs_cards"] == 1:
                # select card
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .eq.return_value
                    .maybe_single.return_value
                    .execute.return_value
                ) = MagicMock(data=card)
            else:
                # update card
                (
                    mock_table.update.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{}])
        elif name == "problems":
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data={
                "correct_answer": "42",
                "solution_markdown": "Solution",
                "task_number": 1,
            })
        elif name == "users":
            call_counts["users"] += 1
            if call_counts["users"] == 1:
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .maybe_single.return_value
                    .execute.return_value
                ) = MagicMock(data={
                    "exam_date": "2026-06-19",
                    "current_xp": 100,
                })
            else:
                (
                    mock_table.update.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{}])
        elif name == "user_problem_attempts":
            mock_table.insert.return_value.execute.return_value = (
                MagicMock(data=[{}])
            )
        elif name == "user_topic_progress":
            (
                mock_table.select.return_value
                .eq.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=None)
            mock_table.insert.return_value.execute.return_value = (
                MagicMock(data=[{}])
            )
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch(
        "app.routers.srs.get_supabase_client",
        return_value=mock_client,
    ):
        resp = client.post(
            "/api/srs/review",
            json={
                "card_id": "card-1",
                "answer": "42",
                "time_spent_seconds": 60,
                "self_assessment": "good",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is True
    assert data["correct_answer"] == "42"
    assert data["xp_earned"] == 10
    # good on ef=2.5, interval=5 → 5*2.5=12.5
    assert data["new_ease_factor"] == 2.5
    assert data["new_interval"] > 5.0


def test_review_again_assessment(client):
    """Again review resets interval to 1."""
    token = _make_token()
    card = _mock_srs_card(
        "card-1", "prob-1", "topic-1",
        ease_factor=2.5, interval_days=10.0, repetition_count=5,
    )

    mock_client = MagicMock()
    call_counts = {"srs_cards": 0}

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "srs_cards":
            call_counts["srs_cards"] += 1
            if call_counts["srs_cards"] == 1:
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .eq.return_value
                    .maybe_single.return_value
                    .execute.return_value
                ) = MagicMock(data=card)
            else:
                (
                    mock_table.update.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{}])
        elif name == "problems":
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data={
                "correct_answer": "42",
                "solution_markdown": None,
                "task_number": 1,
            })
        elif name == "users":
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data={
                "exam_date": None,
                "current_xp": 0,
            })
        elif name == "user_problem_attempts":
            mock_table.insert.return_value.execute.return_value = (
                MagicMock(data=[{}])
            )
        elif name == "user_topic_progress":
            (
                mock_table.select.return_value
                .eq.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=None)
            mock_table.insert.return_value.execute.return_value = (
                MagicMock(data=[{}])
            )
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch(
        "app.routers.srs.get_supabase_client",
        return_value=mock_client,
    ):
        resp = client.post(
            "/api/srs/review",
            json={
                "card_id": "card-1",
                "answer": "99",
                "time_spent_seconds": 30,
                "self_assessment": "again",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is False
    assert data["xp_earned"] == 0
    # again → interval=1, ef=2.3
    assert data["new_interval"] == 1.0
    assert data["new_ease_factor"] == 2.3


def test_review_card_not_found(client):
    """Non-existent card → 404."""
    token = _make_token()

    mock_client = MagicMock()
    (
        mock_client.table.return_value
        .select.return_value
        .eq.return_value
        .eq.return_value
        .maybe_single.return_value
        .execute.return_value
    ) = MagicMock(data=None)

    with patch(
        "app.routers.srs.get_supabase_client",
        return_value=mock_client,
    ):
        resp = client.post(
            "/api/srs/review",
            json={
                "card_id": "nonexistent",
                "answer": "1",
                "time_spent_seconds": 10,
                "self_assessment": "good",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 404


def test_review_no_auth(client):
    """Should require authentication."""
    resp = client.post(
        "/api/srs/review",
        json={
            "card_id": "card-1",
            "answer": "1",
            "time_spent_seconds": 10,
            "self_assessment": "good",
        },
    )
    assert resp.status_code in (401, 403)


# --- _ensure_srs_card ---


def test_ensure_srs_card_creates_new():
    """Creates a new SRS card if one doesn't exist."""
    from app.routers.srs import _ensure_srs_card

    mock_client = MagicMock()
    # No existing card
    (
        mock_client.table.return_value
        .select.return_value
        .eq.return_value
        .eq.return_value
        .maybe_single.return_value
        .execute.return_value
    ) = MagicMock(data=None)
    mock_client.table.return_value.insert.return_value.execute.return_value = (
        MagicMock(data=[{}])
    )

    card_id = _ensure_srs_card(
        mock_client, "user-1", "prob-1", "topic-1",
    )
    assert card_id  # non-empty string
    mock_client.table.return_value.insert.assert_called_once()


def test_ensure_srs_card_returns_existing():
    """Returns existing card ID if card already exists."""
    from app.routers.srs import _ensure_srs_card

    mock_client = MagicMock()
    (
        mock_client.table.return_value
        .select.return_value
        .eq.return_value
        .eq.return_value
        .maybe_single.return_value
        .execute.return_value
    ) = MagicMock(data={"id": "existing-card-id"})

    card_id = _ensure_srs_card(
        mock_client, "user-1", "prob-1", "topic-1",
    )
    assert card_id == "existing-card-id"
    mock_client.table.return_value.insert.assert_not_called()
