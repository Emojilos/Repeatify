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


def _mock_problem_row(
    problem_id: str = "prob-1",
    task_number: int = 1,
    topic_id: str = "topic-1",
    difficulty: str = "basic",
) -> dict:
    return {
        "id": problem_id,
        "topic_id": topic_id,
        "task_number": task_number,
        "difficulty": difficulty,
        "problem_text": f"Solve problem {problem_id}",
        "problem_images": None,
        "correct_answer": "42",
        "answer_tolerance": 0.0,
        "solution_markdown": "The answer is 42.",
        "solution_images": None,
        "hints": ["Think about the number"],
        "source": "ФИПИ",
    }


# --- GET /api/problems ---


def test_list_problems(client):
    token = _make_token()
    problems = [_mock_problem_row(f"prob-{i}", task_number=1) for i in range(3)]
    topics_data = [{"id": "topic-1", "max_points": 1}]

    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "problems":
            result = MagicMock(data=problems, count=3)
            (
                mock_table.select.return_value
                .eq.return_value
                .order.return_value
                .range.return_value
                .execute
            ).return_value = result
        elif name == "topics":
            (
                mock_table.select.return_value
                .in_.return_value
                .execute
            ).return_value = MagicMock(data=topics_data)
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.problems.get_supabase_client", return_value=mock_client):
        resp = client.get(
            "/api/problems?task_number=1",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["items"][0]["max_points"] == 1
    # correct_answer must NOT be in list items
    assert "correct_answer" not in data["items"][0]


def test_list_problems_no_auth(client):
    """Should require authentication."""
    resp = client.get("/api/problems")
    assert resp.status_code in (401, 403)


def test_list_problems_with_filters(client):
    token = _make_token()
    problems = [_mock_problem_row("prob-1", task_number=5, difficulty="hard")]

    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "problems":
            result = MagicMock(data=problems, count=1)
            (
                mock_table.select.return_value
                .eq.return_value
                .eq.return_value
                .eq.return_value
                .order.return_value
                .range.return_value
                .execute
            ).return_value = result
        elif name == "topics":
            (
                mock_table.select.return_value
                .in_.return_value
                .execute
            ).return_value = MagicMock(data=[{"id": "topic-1", "max_points": 2}])
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.problems.get_supabase_client", return_value=mock_client):
        resp = client.get(
            "/api/problems?task_number=5&difficulty=hard&topic_id=topic-1",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1


# --- GET /api/problems/{id} ---


def test_get_problem(client):
    token = _make_token()
    problem = _mock_problem_row("prob-1")

    mock_client = MagicMock()
    (
        mock_client.table.return_value
        .select.return_value
        .eq.return_value
        .execute.return_value
    ) = MagicMock(data=[problem])

    with patch("app.routers.problems.get_supabase_client", return_value=mock_client):
        resp = client.get(
            "/api/problems/prob-1",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "prob-1"
    assert data["problem_text"] == "Solve problem prob-1"
    # correct_answer must NOT be in response
    assert "correct_answer" not in data


def test_get_problem_not_found(client):
    token = _make_token()

    mock_client = MagicMock()
    (
        mock_client.table.return_value
        .select.return_value
        .eq.return_value
        .execute.return_value
    ) = MagicMock(data=[])

    with patch("app.routers.problems.get_supabase_client", return_value=mock_client):
        resp = client.get(
            "/api/problems/nonexistent",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 404


# --- POST /api/problems/{id}/attempt ---


def test_attempt_correct_part1(client):
    """Correct answer for Part 1 task → is_correct=True, xp_earned=10."""
    token = _make_token()
    problem = _mock_problem_row("prob-1", task_number=3)  # Part 1

    mock_client = MagicMock()

    tables_called = []

    def table_side_effect(name):
        tables_called.append(name)
        mock_table = MagicMock()
        if name == "problems":
            (
                mock_table.select.return_value
                .eq.return_value
                .execute.return_value
            ) = MagicMock(data=[problem])
        elif name == "user_problem_attempts":
            mock_table.insert.return_value.execute.return_value = MagicMock(data=[{}])
        elif name == "users":
            count = len([t for t in tables_called if t == "users"])
            if count == 1:  # first call: select current_xp
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{"current_xp": 50, "current_level": 1}])
            else:  # second call: update
                (
                    mock_table.update.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{}])
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with (
        patch("app.routers.problems.get_supabase_client", return_value=mock_client),
        patch("app.routers.problems._ensure_fsrs_card"),
    ):
        resp = client.post(
            "/api/problems/prob-1/attempt",
            json={"answer": "42", "time_spent_seconds": 60, "self_assessment": "good"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is True
    assert data["correct_answer"] == "42"
    assert data["xp_earned"] == 10
    assert data["solution_markdown"] == "The answer is 42."
    assert "attempt_id" in data


def test_attempt_wrong_answer(client):
    """Wrong answer → is_correct=False, xp_earned=0."""
    token = _make_token()
    problem = _mock_problem_row("prob-1", task_number=1)

    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "problems":
            (
                mock_table.select.return_value
                .eq.return_value
                .execute.return_value
            ) = MagicMock(data=[problem])
        elif name == "user_problem_attempts":
            mock_table.insert.return_value.execute.return_value = MagicMock(data=[{}])
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with (
        patch("app.routers.problems.get_supabase_client", return_value=mock_client),
        patch("app.routers.problems._ensure_fsrs_card"),
    ):
        resp = client.post(
            "/api/problems/prob-1/attempt",
            json={"answer": "99", "time_spent_seconds": 30, "self_assessment": "again"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is False
    assert data["correct_answer"] == "42"
    assert data["xp_earned"] == 0


def test_attempt_part2_correct_good(client):
    """Part 2 correct with good assessment → xp_earned=25."""
    token = _make_token()
    problem = _mock_problem_row("prob-1", task_number=15)  # Part 2

    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "problems":
            (
                mock_table.select.return_value
                .eq.return_value
                .execute.return_value
            ) = MagicMock(data=[problem])
        elif name == "user_problem_attempts":
            mock_table.insert.return_value.execute.return_value = MagicMock(data=[{}])
        elif name == "users":
            (
                mock_table.select.return_value
                .eq.return_value
                .execute.return_value
            ) = MagicMock(data=[{"current_xp": 100, "current_level": 2}])
            (
                mock_table.update.return_value
                .eq.return_value
                .execute.return_value
            ) = MagicMock(data=[{}])
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with (
        patch("app.routers.problems.get_supabase_client", return_value=mock_client),
        patch("app.routers.problems._ensure_fsrs_card"),
    ):
        resp = client.post(
            "/api/problems/prob-1/attempt",
            json={"answer": "42", "time_spent_seconds": 120, "self_assessment": "good"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is True
    assert data["xp_earned"] == 25


def test_attempt_part2_correct_hard(client):
    """Part 2 correct with hard assessment → xp_earned=0 (only good/easy get XP)."""
    token = _make_token()
    problem = _mock_problem_row("prob-1", task_number=14)

    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "problems":
            (
                mock_table.select.return_value
                .eq.return_value
                .execute.return_value
            ) = MagicMock(data=[problem])
        elif name == "user_problem_attempts":
            mock_table.insert.return_value.execute.return_value = MagicMock(data=[{}])
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with (
        patch("app.routers.problems.get_supabase_client", return_value=mock_client),
        patch("app.routers.problems._ensure_fsrs_card"),
    ):
        resp = client.post(
            "/api/problems/prob-1/attempt",
            json={"answer": "42", "time_spent_seconds": 300, "self_assessment": "hard"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is True
    assert data["xp_earned"] == 0


def test_attempt_problem_not_found(client):
    token = _make_token()

    mock_client = MagicMock()
    (
        mock_client.table.return_value
        .select.return_value
        .eq.return_value
        .execute.return_value
    ) = MagicMock(data=[])

    with patch("app.routers.problems.get_supabase_client", return_value=mock_client):
        resp = client.post(
            "/api/problems/nonexistent/attempt",
            json={"answer": "1", "time_spent_seconds": 10, "self_assessment": "good"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 404


def test_attempt_invalid_self_assessment(client):
    """Invalid self_assessment → 422 validation error."""
    token = _make_token()
    resp = client.post(
        "/api/problems/prob-1/attempt",
        json={"answer": "42", "time_spent_seconds": 10, "self_assessment": "invalid"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_attempt_case_insensitive(client):
    """Answer comparison should be case-insensitive."""
    token = _make_token()
    problem = _mock_problem_row("prob-1", task_number=1)
    problem["correct_answer"] = "ABC"

    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "problems":
            (
                mock_table.select.return_value
                .eq.return_value
                .execute.return_value
            ) = MagicMock(data=[problem])
        elif name == "user_problem_attempts":
            mock_table.insert.return_value.execute.return_value = MagicMock(data=[{}])
        elif name == "users":
            (
                mock_table.select.return_value
                .eq.return_value
                .execute.return_value
            ) = MagicMock(data=[{"current_xp": 0, "current_level": 1}])
            (
                mock_table.update.return_value
                .eq.return_value
                .execute.return_value
            ) = MagicMock(data=[{}])
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with (
        patch("app.routers.problems.get_supabase_client", return_value=mock_client),
        patch("app.routers.problems._ensure_fsrs_card"),
    ):
        resp = client.post(
            "/api/problems/prob-1/attempt",
            json={"answer": "abc", "time_spent_seconds": 10, "self_assessment": "good"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    assert resp.json()["is_correct"] is True


def test_attempt_with_tolerance(client):
    """Numeric answer within tolerance should be correct."""
    token = _make_token()
    problem = _mock_problem_row("prob-1", task_number=1)
    problem["correct_answer"] = "3.14"
    problem["answer_tolerance"] = 0.01

    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "problems":
            (
                mock_table.select.return_value
                .eq.return_value
                .execute.return_value
            ) = MagicMock(data=[problem])
        elif name == "user_problem_attempts":
            mock_table.insert.return_value.execute.return_value = MagicMock(data=[{}])
        elif name == "users":
            (
                mock_table.select.return_value
                .eq.return_value
                .execute.return_value
            ) = MagicMock(data=[{"current_xp": 0, "current_level": 1}])
            (
                mock_table.update.return_value
                .eq.return_value
                .execute.return_value
            ) = MagicMock(data=[{}])
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with (
        patch("app.routers.problems.get_supabase_client", return_value=mock_client),
        patch("app.routers.problems._ensure_fsrs_card"),
    ):
        resp = client.post(
            "/api/problems/prob-1/attempt",
            json={
                "answer": "3.15",
                "time_spent_seconds": 10,
                "self_assessment": "good",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    assert resp.json()["is_correct"] is True


# --- FSRS card integration ---


class TestDetermineFsrsRating:
    """Tests for _determine_fsrs_rating helper."""

    def test_incorrect_returns_again(self):
        from app.routers.problems import _determine_fsrs_rating

        assert _determine_fsrs_rating(is_correct=False, time_spent_seconds=10) == 1

    def test_incorrect_slow_returns_again(self):
        from app.routers.problems import _determine_fsrs_rating

        assert _determine_fsrs_rating(is_correct=False, time_spent_seconds=120) == 1

    def test_correct_fast_returns_easy(self):
        from app.routers.problems import _determine_fsrs_rating

        assert _determine_fsrs_rating(is_correct=True, time_spent_seconds=30) == 4

    def test_correct_slow_returns_good(self):
        from app.routers.problems import _determine_fsrs_rating

        assert _determine_fsrs_rating(is_correct=True, time_spent_seconds=60) == 3

    def test_correct_boundary_60s_returns_good(self):
        from app.routers.problems import _determine_fsrs_rating

        assert _determine_fsrs_rating(is_correct=True, time_spent_seconds=59) == 4
        assert _determine_fsrs_rating(is_correct=True, time_spent_seconds=60) == 3


class TestEnsureFsrsCard:
    """Tests for FSRS card creation/review on problem attempt."""

    def test_creates_new_fsrs_card_on_first_attempt(self):
        """First attempt creates a new FSRS card and reviews it."""
        from app.routers.problems import _ensure_fsrs_card

        mock_client = MagicMock()
        # No existing card
        (
            mock_client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .execute.return_value
        ) = MagicMock(data=[])

        create_patch = patch(
            "app.routers.problems.fsrs_create_card",
            return_value={"id": "card-1"},
        )
        review_patch = patch(
            "app.routers.problems.fsrs_review_card",
        )
        with create_patch as mock_create, review_patch as mock_review:
            _ensure_fsrs_card(mock_client, "user-1", "prob-1", True, 30)

        mock_create.assert_called_once_with(
            mock_client, "user-1", card_type="problem", problem_id="prob-1",
        )
        # correct + fast → Easy (4)
        mock_review.assert_called_once_with(mock_client, "card-1", 4, "user-1")

    def test_reviews_existing_fsrs_card(self):
        """Repeat attempt reviews existing card, does not create new."""
        from app.routers.problems import _ensure_fsrs_card

        mock_client = MagicMock()
        # Existing card found
        (
            mock_client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .execute.return_value
        ) = MagicMock(data=[{"id": "existing-card-1"}])

        with (
            patch("app.routers.problems.fsrs_create_card") as mock_create,
            patch("app.routers.problems.fsrs_review_card") as mock_review,
        ):
            _ensure_fsrs_card(mock_client, "user-1", "prob-1", False, 120)

        mock_create.assert_not_called()
        # incorrect → Again (1)
        mock_review.assert_called_once_with(mock_client, "existing-card-1", 1, "user-1")

    def test_no_srs_card_created(self, client):
        """After attempt, srs_cards table should NOT be accessed."""
        token = _make_token()
        problem = _mock_problem_row("prob-1", task_number=3)

        tables_accessed = []
        mock_client = MagicMock()

        def table_side_effect(name):
            tables_accessed.append(name)
            mock_table = MagicMock()
            if name == "problems":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[problem])
            elif name == "user_problem_attempts":
                (
                    mock_table.insert.return_value
                    .execute
                ).return_value = MagicMock(data=[{}])
            elif name == "users":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{"current_xp": 0, "current_level": 1}])
                (
                    mock_table.update.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{}])
            return mock_table

        mock_client.table.side_effect = table_side_effect

        with (
            patch("app.routers.problems.get_supabase_client", return_value=mock_client),
            patch("app.routers.problems._ensure_fsrs_card"),
        ):
            resp = client.post(
                "/api/problems/prob-1/attempt",
                json={
                    "answer": "42",
                    "time_spent_seconds": 10,
                    "self_assessment": "good",
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        assert "srs_cards" not in tables_accessed

    def test_attempt_calls_ensure_fsrs_card(self, client):
        """Verify attempt endpoint calls _ensure_fsrs_card with correct args."""
        token = _make_token()
        problem = _mock_problem_row("prob-1", task_number=3)

        mock_client = MagicMock()

        def table_side_effect(name):
            mock_table = MagicMock()
            if name == "problems":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[problem])
            elif name == "user_problem_attempts":
                (
                    mock_table.insert.return_value
                    .execute
                ).return_value = MagicMock(data=[{}])
            elif name == "users":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{"current_xp": 0, "current_level": 1}])
                (
                    mock_table.update.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{}])
            return mock_table

        mock_client.table.side_effect = table_side_effect

        with (
            patch("app.routers.problems.get_supabase_client", return_value=mock_client),
            patch("app.routers.problems._ensure_fsrs_card") as mock_ensure,
        ):
            resp = client.post(
                "/api/problems/prob-1/attempt",
                json={
                    "answer": "42",
                    "time_spent_seconds": 60,
                    "self_assessment": "good",
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        mock_ensure.assert_called_once_with(
            mock_client, "user-123", "prob-1", True, 60,
        )
