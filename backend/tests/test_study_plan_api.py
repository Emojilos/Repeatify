"""Tests for Study Plan API endpoints."""

import os
import time
from datetime import date, datetime, timedelta, timezone
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


def _mock_plan(
    plan_id: str = "plan-1",
    user_id: str = "user-123",
    target_score: int = 80,
    exam_date: str = "2026-07-01",
    hours_per_day: float = 1.5,
) -> dict:
    return {
        "id": plan_id,
        "user_id": user_id,
        "target_score": target_score,
        "exam_date": exam_date,
        "hours_per_day": hours_per_day,
        "plan_data": {
            "target_score": target_score,
            "exam_date": exam_date,
            "hours_per_day": hours_per_day,
            "days_remaining": 60,
            "total_hours": 90.0,
            "study_hours": 63.0,
            "review_hours": 27.0,
            "tasks_to_study": [7, 6, 4],
            "mastered_tasks": [1, 2, 3],
            "warning": None,
            "weeks": [
                {
                    "week": 1,
                    "days": [
                        {
                            "date": date.today().isoformat(),
                            "study": [
                                {"task_number": 7, "minutes": 63},
                            ],
                            "study_minutes": 63,
                            "review_minutes": 27,
                        },
                        {
                            "date": (date.today() + timedelta(days=1)).isoformat(),
                            "study": [
                                {"task_number": 7, "minutes": 63},
                            ],
                            "study_minutes": 63,
                            "review_minutes": 27,
                        },
                    ],
                },
            ],
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True,
    }


# --- POST /api/study-plan/generate ---


class TestGenerateStudyPlan:
    def test_generate_creates_plan(self, client):
        """POST /api/study-plan/generate creates and returns a plan."""
        token = _make_token()
        plan_result = _mock_plan()

        with patch(
            "app.routers.study_plan.get_supabase_client",
            return_value=MagicMock(),
        ), patch(
            "app.routers.study_plan.generate_plan",
            return_value=plan_result,
        ) as mock_gen:
            resp = client.post(
                "/api/study-plan/generate",
                json={
                    "target_score": 80,
                    "exam_date": "2026-07-01",
                    "hours_per_day": 1.5,
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["target_score"] == 80
        assert data["is_active"] is True
        assert data["plan_data"]["tasks_to_study"] == [7, 6, 4]

        # Verify service was called with correct args
        mock_gen.assert_called_once()
        call_kwargs = mock_gen.call_args
        assert call_kwargs.kwargs["target_score"] == 80
        assert call_kwargs.kwargs["hours_per_day"] == 1.5

    def test_generate_invalid_target_score(self, client):
        """Target score not in {70,80,90,100} → 422."""
        token = _make_token()
        resp = client.post(
            "/api/study-plan/generate",
            json={
                "target_score": 75,
                "exam_date": "2026-07-01",
                "hours_per_day": 1.5,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_generate_no_auth(self, client):
        """Should require authentication."""
        resp = client.post(
            "/api/study-plan/generate",
            json={
                "target_score": 80,
                "exam_date": "2026-07-01",
                "hours_per_day": 1.5,
            },
        )
        assert resp.status_code in (401, 403)


# --- GET /api/study-plan/current ---


class TestGetCurrentPlan:
    def test_returns_active_plan(self, client):
        """Returns the active study plan."""
        token = _make_token()
        plan = _mock_plan()

        with patch(
            "app.routers.study_plan.get_supabase_client",
            return_value=MagicMock(),
        ), patch(
            "app.routers.study_plan.get_current_plan",
            return_value=plan,
        ):
            resp = client.get(
                "/api/study-plan/current",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "plan-1"
        assert data["target_score"] == 80
        assert data["is_active"] is True
        assert data["plan_data"] is not None

    def test_no_plan_returns_404(self, client):
        """No active plan → 404."""
        token = _make_token()

        with patch(
            "app.routers.study_plan.get_supabase_client",
            return_value=MagicMock(),
        ), patch(
            "app.routers.study_plan.get_current_plan",
            return_value=None,
        ):
            resp = client.get(
                "/api/study-plan/current",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 404

    def test_current_no_auth(self, client):
        """Should require authentication."""
        resp = client.get("/api/study-plan/current")
        assert resp.status_code in (401, 403)


# --- PUT /api/study-plan/recalculate ---


class TestRecalculatePlan:
    def test_recalculate_updates_plan(self, client):
        """Recalculate with new target_score → plan updated."""
        token = _make_token()
        existing_plan = _mock_plan(target_score=80)
        new_plan = _mock_plan(target_score=70)
        new_plan["plan_data"]["target_score"] = 70
        new_plan["target_score"] = 70

        with patch(
            "app.routers.study_plan.get_supabase_client",
            return_value=MagicMock(),
        ), patch(
            "app.routers.study_plan.get_current_plan",
            return_value=existing_plan,
        ), patch(
            "app.routers.study_plan.generate_plan",
            return_value=new_plan,
        ):
            resp = client.put(
                "/api/study-plan/recalculate",
                json={
                    "target_score": 70,
                    "exam_date": "2026-07-01",
                    "hours_per_day": 1.5,
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["target_score"] == 70

    def test_recalculate_no_existing_plan(self, client):
        """Recalculate without existing plan → 404."""
        token = _make_token()

        with patch(
            "app.routers.study_plan.get_supabase_client",
            return_value=MagicMock(),
        ), patch(
            "app.routers.study_plan.get_current_plan",
            return_value=None,
        ):
            resp = client.put(
                "/api/study-plan/recalculate",
                json={
                    "target_score": 70,
                    "exam_date": "2026-07-01",
                    "hours_per_day": 1.5,
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 404

    def test_recalculate_no_auth(self, client):
        """Should require authentication."""
        resp = client.put(
            "/api/study-plan/recalculate",
            json={
                "target_score": 70,
                "exam_date": "2026-07-01",
                "hours_per_day": 1.5,
            },
        )
        assert resp.status_code in (401, 403)


# --- GET /api/study-plan/today ---


class TestGetTodayTasks:
    def test_today_with_plan_and_due_cards(self, client):
        """Returns due cards count + today's study material from plan."""
        token = _make_token()
        plan = _mock_plan()

        mock_client = MagicMock()

        def table_side_effect(name):
            mock_table = MagicMock()
            if name == "fsrs_cards":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .lte.return_value
                    .neq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{"id": "c1"}, {"id": "c2"}, {"id": "c3"}])
            elif name == "topics":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{"title": "Производная"}])
            return mock_table

        mock_client.table.side_effect = table_side_effect

        with patch(
            "app.routers.study_plan.get_supabase_client",
            return_value=mock_client,
        ), patch(
            "app.routers.study_plan.get_current_plan",
            return_value=plan,
        ):
            resp = client.get(
                "/api/study-plan/today",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["review_cards_due"] == 3
        assert len(data["new_material"]) >= 1
        assert data["new_material"][0]["task_number"] == 7
        assert data["new_material"][0]["title"] == "Производная"
        assert data["total_estimated_minutes"] > 0

    def test_today_no_plan(self, client):
        """No plan → only review cards returned."""
        token = _make_token()

        mock_client = MagicMock()
        (
            mock_client.table.return_value
            .select.return_value
            .eq.return_value
            .lte.return_value
            .neq.return_value
            .execute.return_value
        ) = MagicMock(data=[{"id": "c1"}])

        with patch(
            "app.routers.study_plan.get_supabase_client",
            return_value=mock_client,
        ), patch(
            "app.routers.study_plan.get_current_plan",
            return_value=None,
        ):
            resp = client.get(
                "/api/study-plan/today",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["review_cards_due"] == 1
        assert data["new_material"] == []
        assert data["total_estimated_minutes"] == 2  # 1 card * 2 min

    def test_today_empty(self, client):
        """No due cards, no plan → all zeros."""
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
            "app.routers.study_plan.get_supabase_client",
            return_value=mock_client,
        ), patch(
            "app.routers.study_plan.get_current_plan",
            return_value=None,
        ):
            resp = client.get(
                "/api/study-plan/today",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["review_cards_due"] == 0
        assert data["new_material"] == []
        assert data["total_estimated_minutes"] == 0

    def test_today_no_auth(self, client):
        """Should require authentication."""
        resp = client.get("/api/study-plan/today")
        assert resp.status_code in (401, 403)
