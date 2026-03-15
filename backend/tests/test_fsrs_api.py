"""Tests for FSRS API endpoints (GET /api/fsrs/session, POST /api/fsrs/review)."""

import os
import time
from datetime import datetime, timezone
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


def _mock_fsrs_card(
    card_id: str = "card-1",
    problem_id: str = "prob-1",
    prototype_id: str | None = None,
    task_number: int = 6,
    state: str = "review",
    difficulty: float = 5.0,
    stability: float = 10.0,
    reps: int = 3,
    lapses: int = 0,
) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "id": card_id,
        "user_id": "user-123",
        "problem_id": problem_id,
        "prototype_id": prototype_id,
        "card_type": "problem",
        "difficulty": difficulty,
        "stability": stability,
        "due": now.isoformat(),
        "last_review": now.isoformat(),
        "reps": reps,
        "lapses": lapses,
        "state": state,
        "scheduled_days": 5,
        "elapsed_days": 5,
        "created_at": now.isoformat(),
        "problem_text": "What is 2+2?",
        "problem_images": None,
        "hints": ["Think about addition"],
        "topic_title": "Арифметика",
        "task_number": task_number,
        "retrievability": 0.7,
    }


# --- GET /api/fsrs/session ---


class TestGetFSRSSession:
    def test_returns_due_cards(self, client):
        """Due cards are returned with FSRS fields."""
        token = _make_token()
        session_cards = [
            _mock_fsrs_card("card-1", "prob-1", task_number=6),
            _mock_fsrs_card("card-2", "prob-2", task_number=7),
        ]

        mock_client = MagicMock()
        # total_due count
        (
            mock_client.table.return_value
            .select.return_value
            .eq.return_value
            .lte.return_value
            .neq.return_value
            .execute.return_value
        ) = MagicMock(data=[{"id": "1"}, {"id": "2"}, {"id": "3"}])
        # exam_date
        (
            mock_client.table.return_value
            .select.return_value
            .eq.return_value
            .execute.return_value
        ) = MagicMock(data=[{"exam_date": None}])

        with (
            patch(
                "app.routers.fsrs.get_supabase_client",
                return_value=mock_client,
            ),
            patch(
                "app.routers.fsrs.get_session",
                return_value=session_cards,
            ),
        ):
            resp = client.get(
                "/api/fsrs/session?max_cards=20",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["cards"]) == 2
        assert data["cards"][0]["id"] == "card-1"
        assert data["cards"][0]["difficulty"] == 5.0
        assert data["cards"][0]["stability"] == 10.0
        assert data["cards"][0]["retrievability"] == 0.7
        assert data["cards"][0]["problem_text"] == "What is 2+2?"

    def test_empty_session_for_new_user(self, client):
        """New user with no cards → empty session."""
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
        (
            mock_client.table.return_value
            .select.return_value
            .eq.return_value
            .execute.return_value
        ) = MagicMock(data=[{"exam_date": None}])

        with (
            patch(
                "app.routers.fsrs.get_supabase_client",
                return_value=mock_client,
            ),
            patch(
                "app.routers.fsrs.get_session",
                return_value=[],
            ),
        ):
            resp = client.get(
                "/api/fsrs/session",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_due"] == 0
        assert data["cards"] == []

    def test_session_no_auth(self, client):
        """Should require authentication."""
        resp = client.get("/api/fsrs/session")
        assert resp.status_code in (401, 403)

    def test_session_uses_exam_date(self, client):
        """Exam date is passed to get_session for retention tuning."""
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
        (
            mock_client.table.return_value
            .select.return_value
            .eq.return_value
            .execute.return_value
        ) = MagicMock(data=[{"exam_date": "2026-06-19"}])

        with (
            patch(
                "app.routers.fsrs.get_supabase_client",
                return_value=mock_client,
            ),
            patch(
                "app.routers.fsrs.get_session",
                return_value=[],
            ) as mock_get_session,
        ):
            resp = client.get(
                "/api/fsrs/session",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        # Verify exam_date was passed
        call_args = mock_get_session.call_args
        from datetime import date

        assert call_args.kwargs.get("exam_date") == date(2026, 6, 19)


# --- POST /api/fsrs/review ---


class TestSubmitFSRSReview:
    def _make_review_patches(
        self,
        updated_row: dict,
        correct_answer: str = "42",
        task_number: int = 6,
        topic_id: str = "topic-1",
        exam_date: str | None = "2026-06-19",
        current_xp: int = 100,
        current_level: int = 2,
        retrievability: float = 0.85,
    ):
        """Return context managers for review endpoint."""
        mock_client = MagicMock()

        def table_side_effect(name):
            mock_table = MagicMock()
            if name == "users":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{
                    "exam_date": exam_date,
                    "current_xp": current_xp,
                    "current_level": current_level,
                }])
                (
                    mock_table.update.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{}])
            elif name == "problems":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{
                    "correct_answer": correct_answer,
                    "solution_markdown": "Solution here",
                    "task_number": task_number,
                    "topic_id": topic_id,
                }])
            elif name == "user_problem_attempts":
                mock_table.insert.return_value.execute.return_value = (
                    MagicMock(data=[{}])
                )
            return mock_table

        mock_client.table.side_effect = table_side_effect

        return (
            patch("app.routers.fsrs.get_supabase_client", return_value=mock_client),
            patch("app.routers.fsrs.review_card", return_value=updated_row),
            patch("app.routers.fsrs.get_retrievability", return_value=retrievability),
            patch("app.routers.fsrs._update_topic_progress"),
            patch("app.routers.fsrs.record_activity"),
        )

    def test_review_correct_answer(self, client):
        """Correct answer with Good rating → XP earned, due in future."""
        token = _make_token()
        now = datetime.now(timezone.utc)
        updated_row = {
            "id": "card-1",
            "user_id": "user-123",
            "problem_id": "prob-1",
            "difficulty": 5.5,
            "stability": 15.0,
            "due": now.isoformat(),
            "state": "review",
            "reps": 4,
            "lapses": 0,
            "last_review": now.isoformat(),
        }

        patches = self._make_review_patches(updated_row)

        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            resp = client.post(
                "/api/fsrs/review",
                json={
                    "card_id": "card-1",
                    "rating": 3,
                    "answer": "42",
                    "time_spent_seconds": 45,
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["is_correct"] is True
        assert data["correct_answer"] == "42"
        assert data["solution_markdown"] == "Solution here"
        assert data["xp_earned"] == 10  # Part 1 correct
        assert data["new_difficulty"] == 5.5
        assert data["new_stability"] == 15.0
        assert data["new_state"] == "review"
        assert data["retrievability"] == 0.85

    def test_review_wrong_answer(self, client):
        """Wrong answer with Again rating → no XP."""
        token = _make_token()
        now = datetime.now(timezone.utc)
        updated_row = {
            "id": "card-1",
            "user_id": "user-123",
            "problem_id": "prob-1",
            "difficulty": 7.0,
            "stability": 2.0,
            "due": now.isoformat(),
            "state": "relearning",
            "reps": 4,
            "lapses": 1,
            "last_review": now.isoformat(),
        }

        patches = self._make_review_patches(
            updated_row, retrievability=0.3,
        )

        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            resp = client.post(
                "/api/fsrs/review",
                json={
                    "card_id": "card-1",
                    "rating": 1,
                    "answer": "99",
                    "time_spent_seconds": 30,
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["is_correct"] is False
        assert data["xp_earned"] == 0
        assert data["new_state"] == "relearning"
        assert data["retrievability"] == 0.3

    def test_review_card_not_found(self, client):
        """Non-existent card → 404."""
        token = _make_token()

        mock_client = MagicMock()
        (
            mock_client.table.return_value
            .select.return_value
            .eq.return_value
            .execute.return_value
        ) = MagicMock(data=[{"exam_date": None}])

        with (
            patch(
                "app.routers.fsrs.get_supabase_client",
                return_value=mock_client,
            ),
            patch(
                "app.routers.fsrs.review_card",
                side_effect=ValueError("Card not found"),
            ),
        ):
            resp = client.post(
                "/api/fsrs/review",
                json={
                    "card_id": "nonexistent",
                    "rating": 3,
                    "answer": "1",
                    "time_spent_seconds": 10,
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 404

    def test_review_no_auth(self, client):
        """Should require authentication."""
        resp = client.post(
            "/api/fsrs/review",
            json={
                "card_id": "card-1",
                "rating": 3,
            },
        )
        assert resp.status_code in (401, 403)

    def test_review_invalid_rating(self, client):
        """Rating outside 1-4 → 422."""
        token = _make_token()
        resp = client.post(
            "/api/fsrs/review",
            json={
                "card_id": "card-1",
                "rating": 5,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

        resp2 = client.post(
            "/api/fsrs/review",
            json={
                "card_id": "card-1",
                "rating": 0,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp2.status_code == 422

    def test_review_xp_for_part2(self, client):
        """Part 2 tasks (13-19) only earn XP for good/easy + correct."""
        token = _make_token()
        now = datetime.now(timezone.utc)
        updated_row = {
            "id": "card-1",
            "user_id": "user-123",
            "problem_id": "prob-1",
            "difficulty": 5.0,
            "stability": 10.0,
            "due": now.isoformat(),
            "state": "review",
            "reps": 4,
            "lapses": 0,
            "last_review": now.isoformat(),
        }

        patches = self._make_review_patches(
            updated_row,
            correct_answer="answer",
            task_number=15,
            retrievability=0.8,
        )

        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            resp = client.post(
                "/api/fsrs/review",
                json={
                    "card_id": "card-1",
                    "rating": 3,  # Good
                    "answer": "answer",
                    "time_spent_seconds": 120,
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["is_correct"] is True
        assert data["xp_earned"] == 25  # Part 2 good/easy

    def test_old_srs_endpoints_still_work(self, client):
        """Old /api/srs/session endpoint still accessible (backward compat)."""
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
        assert "cards" in data
        assert "total_due" in data
