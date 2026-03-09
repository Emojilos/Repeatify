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
        .maybe_single.return_value
        .execute.return_value
    ) = MagicMock(data=problem)

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
        .maybe_single.return_value
        .execute.return_value
    ) = MagicMock(data=None)

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
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=problem)
        elif name == "user_problem_attempts":
            mock_table.insert.return_value.execute.return_value = MagicMock(data=[{}])
        elif name == "users":
            count = len([t for t in tables_called if t == "users"])
            if count == 1:  # first call: select current_xp
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .maybe_single.return_value
                    .execute.return_value
                ) = MagicMock(data={"current_xp": 50})
            else:  # second call: update
                (
                    mock_table.update.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{}])
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.problems.get_supabase_client", return_value=mock_client):
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
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=problem)
        elif name == "user_problem_attempts":
            mock_table.insert.return_value.execute.return_value = MagicMock(data=[{}])
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.problems.get_supabase_client", return_value=mock_client):
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
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=problem)
        elif name == "user_problem_attempts":
            mock_table.insert.return_value.execute.return_value = MagicMock(data=[{}])
        elif name == "users":
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data={"current_xp": 100})
            (
                mock_table.update.return_value
                .eq.return_value
                .execute.return_value
            ) = MagicMock(data=[{}])
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.problems.get_supabase_client", return_value=mock_client):
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
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=problem)
        elif name == "user_problem_attempts":
            mock_table.insert.return_value.execute.return_value = MagicMock(data=[{}])
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.problems.get_supabase_client", return_value=mock_client):
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
        .maybe_single.return_value
        .execute.return_value
    ) = MagicMock(data=None)

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
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=problem)
        elif name == "user_problem_attempts":
            mock_table.insert.return_value.execute.return_value = MagicMock(data=[{}])
        elif name == "users":
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data={"current_xp": 0})
            (
                mock_table.update.return_value
                .eq.return_value
                .execute.return_value
            ) = MagicMock(data=[{}])
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.problems.get_supabase_client", return_value=mock_client):
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
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=problem)
        elif name == "user_problem_attempts":
            mock_table.insert.return_value.execute.return_value = MagicMock(data=[{}])
        elif name == "users":
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data={"current_xp": 0})
            (
                mock_table.update.return_value
                .eq.return_value
                .execute.return_value
            ) = MagicMock(data=[{}])
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.problems.get_supabase_client", return_value=mock_client):
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
