import os
import time
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


def _make_token(user_id: str = "user-123", email: str = "test@example.com") -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def _mock_theory_row(
    content_type: str = "framework",
    topic_id: str = "topic-1",
    order_index: int = 0,
) -> dict:
    return {
        "id": f"theory-{content_type}",
        "topic_id": topic_id,
        "content_type": content_type,
        "content_markdown": f"# {content_type.title()} content\n\nSome $LaTeX$ here.",
        "visual_assets": [],
        "order_index": order_index,
    }


def _mock_update(mock_table):
    """Wire up .update().eq().execute() and .update().eq().eq().execute()."""
    eq1 = mock_table.update.return_value.eq.return_value
    eq1.execute.return_value = MagicMock()
    eq1.eq.return_value.execute.return_value = MagicMock()


def _mock_progress_row(
    topic_id: str = "topic-1",
    fw: bool = False,
    inq: bool = False,
    rel: bool = False,
    elab: bool = False,
    fire_completed_at: str | None = None,
) -> dict:
    return {
        "id": "progress-1",
        "user_id": "user-123",
        "topic_id": topic_id,
        "fire_framework_completed": fw,
        "fire_inquiry_completed": inq,
        "fire_relationships_completed": rel,
        "fire_elaboration_completed": elab,
        "fire_completed_at": fire_completed_at,
        "strength_score": 0.5,
        "total_attempts": 5,
        "correct_attempts": 3,
    }


# --- GET /api/topics/{topic_id}/theory ---


def test_get_theory_with_content(client):
    token = _make_token()
    theory_rows = [
        _mock_theory_row("framework", order_index=0),
        _mock_theory_row("inquiry", order_index=1),
        _mock_theory_row("relationships", order_index=2),
        _mock_theory_row("elaboration", order_index=3),
    ]
    progress = _mock_progress_row(fw=True)

    mock_client = MagicMock()

    call_order = []

    def table_side_effect(name):
        call_order.append(name)
        mock_table = MagicMock()
        if name == "topics":
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data={"id": "topic-1", "title": "Планиметрия"})
        elif name == "theory_content":
            (
                mock_table.select.return_value
                .eq.return_value
                .order.return_value
                .execute.return_value
            ) = MagicMock(data=theory_rows)
        elif name == "user_topic_progress":
            (
                mock_table.select.return_value
                .eq.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=progress)
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.theory.get_supabase_client", return_value=mock_client):
        resp = client.get(
            "/api/topics/topic-1/theory",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["topic_id"] == "topic-1"
    assert data["topic_title"] == "Планиметрия"
    assert len(data["items"]) == 4
    assert data["items"][0]["content_type"] == "framework"
    assert data["fire_progress"]["fire_framework_completed"] is True
    assert data["fire_progress"]["fire_inquiry_completed"] is False


def test_get_theory_no_progress(client):
    """User has no progress for this topic yet."""
    token = _make_token()

    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "topics":
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data={"id": "topic-1", "title": "Планиметрия"})
        elif name == "theory_content":
            (
                mock_table.select.return_value
                .eq.return_value
                .order.return_value
                .execute.return_value
            ) = MagicMock(data=[_mock_theory_row("framework")])
        elif name == "user_topic_progress":
            (
                mock_table.select.return_value
                .eq.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=None)
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.theory.get_supabase_client", return_value=mock_client):
        resp = client.get(
            "/api/topics/topic-1/theory",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["fire_progress"] is None
    assert len(data["items"]) == 1


def test_get_theory_empty_content(client):
    """Topic exists but has no theory content."""
    token = _make_token()

    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "topics":
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data={"id": "topic-1", "title": "Планиметрия"})
        elif name == "theory_content":
            (
                mock_table.select.return_value
                .eq.return_value
                .order.return_value
                .execute.return_value
            ) = MagicMock(data=[])
        elif name == "user_topic_progress":
            (
                mock_table.select.return_value
                .eq.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=None)
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.theory.get_supabase_client", return_value=mock_client):
        resp = client.get(
            "/api/topics/topic-1/theory",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    assert resp.json()["items"] == []


def test_get_theory_topic_not_found(client):
    token = _make_token()

    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        (
            mock_table.select.return_value
            .eq.return_value
            .maybe_single.return_value
            .execute.return_value
        ) = MagicMock(data=None)
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.theory.get_supabase_client", return_value=mock_client):
        resp = client.get(
            "/api/topics/nonexistent/theory",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 404


def test_get_theory_requires_auth(client):
    resp = client.get("/api/topics/topic-1/theory")
    assert resp.status_code in (401, 403)


# --- POST /api/topics/{topic_id}/fire-progress ---


def test_fire_progress_first_stage(client):
    """Mark first FIRe stage on a topic with no prior progress."""
    token = _make_token()

    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "topics":
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data={"id": "topic-1"})
        elif name == "user_topic_progress":
            # No existing progress
            (
                mock_table.select.return_value
                .eq.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=None)
            mock_table.insert.return_value.execute.return_value = MagicMock()
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.theory.get_supabase_client", return_value=mock_client):
        resp = client.post(
            "/api/topics/topic-1/fire-progress",
            json={"stage": "framework"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["stage"] == "framework"
    assert data["completed"] is True
    assert data["all_stages_completed"] is False
    assert data["xp_earned"] == 0


def test_fire_progress_completes_all_stages(client):
    """Mark last FIRe stage → all_stages_completed, XP awarded."""
    token = _make_token()

    # Progress already has 3 stages done, marking the 4th
    existing_progress = _mock_progress_row(fw=True, inq=True, rel=True, elab=False)

    mock_client = MagicMock()

    call_order = []

    def table_side_effect(name):
        call_order.append(name)
        mock_table = MagicMock()
        if name == "topics":
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data={"id": "topic-1"})
        elif name == "user_topic_progress":
            # First call: existing progress lookup
            (
                mock_table.select.return_value
                .eq.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=existing_progress)
            _mock_update(mock_table)
        elif name == "users":
            # award_xp reads user
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data={"current_xp": 100, "current_level": 2})
            _mock_update(mock_table)
        elif name == "user_daily_activity":
            # record_activity: no existing row
            (
                mock_table.select.return_value
                .eq.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=None)
            mock_table.insert.return_value.execute.return_value = MagicMock()
        elif name == "problems":
            # _create_concept_cards: find problems
            (
                mock_table.select.return_value
                .eq.return_value
                .limit.return_value
                .execute.return_value
            ) = MagicMock(data=[])
        elif name == "srs_cards":
            (
                mock_table.select.return_value
                .eq.return_value
                .in_.return_value
                .execute.return_value
            ) = MagicMock(data=[])
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.theory.get_supabase_client", return_value=mock_client):
        resp = client.post(
            "/api/topics/topic-1/fire-progress",
            json={"stage": "elaboration"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["stage"] == "elaboration"
    assert data["all_stages_completed"] is True
    assert data["xp_earned"] == 50
    assert data["fire_completed_at"] is not None


def test_fire_progress_already_completed(client):
    """Completing a stage when all 4 already done — no duplicate XP."""
    token = _make_token()

    existing_progress = _mock_progress_row(
        fw=True, inq=True, rel=True, elab=True,
        fire_completed_at="2026-01-15T10:00:00",
    )

    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "topics":
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data={"id": "topic-1"})
        elif name == "user_topic_progress":
            (
                mock_table.select.return_value
                .eq.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=existing_progress)
            _mock_update(mock_table)
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.theory.get_supabase_client", return_value=mock_client):
        resp = client.post(
            "/api/topics/topic-1/fire-progress",
            json={"stage": "framework"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["all_stages_completed"] is True
    assert data["xp_earned"] == 0  # No duplicate XP


def test_fire_progress_invalid_stage(client):
    token = _make_token()

    mock_client = MagicMock()

    with patch("app.routers.theory.get_supabase_client", return_value=mock_client):
        resp = client.post(
            "/api/topics/topic-1/fire-progress",
            json={"stage": "invalid_stage"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 422


def test_fire_progress_topic_not_found(client):
    token = _make_token()

    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        (
            mock_table.select.return_value
            .eq.return_value
            .maybe_single.return_value
            .execute.return_value
        ) = MagicMock(data=None)
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.theory.get_supabase_client", return_value=mock_client):
        resp = client.post(
            "/api/topics/nonexistent/fire-progress",
            json={"stage": "framework"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 404


def test_fire_progress_requires_auth(client):
    resp = client.post(
        "/api/topics/topic-1/fire-progress",
        json={"stage": "framework"},
    )
    assert resp.status_code in (401, 403)


def test_fire_progress_creates_fsrs_cards(client):
    """When all stages complete, FSRS concept cards are created for prototypes."""
    token = _make_token()

    existing_progress = _mock_progress_row(fw=True, inq=True, rel=True, elab=False)
    prototypes = [{"id": "proto-1"}, {"id": "proto-2"}]

    mock_client = MagicMock()
    inserted_cards = []

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "topics":
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data={"id": "topic-1", "task_number": 6})
        elif name == "user_topic_progress":
            (
                mock_table.select.return_value
                .eq.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=existing_progress)
            _mock_update(mock_table)
        elif name == "users":
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data={"current_xp": 100, "current_level": 2})
            _mock_update(mock_table)
        elif name == "user_daily_activity":
            (
                mock_table.select.return_value
                .eq.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=None)
            mock_table.insert.return_value.execute.return_value = MagicMock()
        elif name == "prototypes":
            (
                mock_table.select.return_value
                .eq.return_value
                .execute.return_value
            ) = MagicMock(data=prototypes)
        elif name == "fsrs_cards":
            # No existing cards
            (
                mock_table.select.return_value
                .eq.return_value
                .in_.return_value
                .execute.return_value
            ) = MagicMock(data=[])

            def capture_insert(card_data):
                inserted_cards.append(card_data)
                result = MagicMock(data=[card_data])
                return MagicMock(
                    execute=MagicMock(return_value=result),
                )

            mock_table.insert.side_effect = capture_insert
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.theory.get_supabase_client", return_value=mock_client):
        resp = client.post(
            "/api/topics/topic-1/fire-progress",
            json={"stage": "elaboration"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    assert len(inserted_cards) == 2
    assert inserted_cards[0]["card_type"] == "concept"
    assert inserted_cards[0]["problem_id"] == "prob-1"
    assert inserted_cards[1]["problem_id"] == "prob-2"
