"""Tests for Study Plan API endpoints (knowledge map)."""

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


def _mock_plan(
    plan_id: str = "plan-1",
    user_id: str = "user-123",
    target_score: int = 80,
) -> dict:
    return {
        "id": plan_id,
        "user_id": user_id,
        "target_score": target_score,
        "plan_data": {
            "target_score": target_score,
            "tasks": [
                {"task_number": i, "status": "not_tested", "correct": None, "total": None, "assessed_at": None}
                for i in range(1, 13)
            ] + [
                {"task_number": i, "status": "not_tested", "correct": None, "total": None, "assessed_at": None}
                for i in [13, 15, 16]
            ],
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True,
    }


# --- POST /api/study-plan/generate ---


class TestGenerateStudyPlan:
    def test_generate_creates_plan(self, client):
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
                json={"target_score": 80},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["target_score"] == 80
        assert data["is_active"] is True
        assert "tasks" in data["plan_data"]

        mock_gen.assert_called_once()

    def test_generate_invalid_target_score(self, client):
        token = _make_token()
        resp = client.post(
            "/api/study-plan/generate",
            json={"target_score": 75},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_generate_no_auth(self, client):
        resp = client.post(
            "/api/study-plan/generate",
            json={"target_score": 80},
        )
        assert resp.status_code in (401, 403)


# --- GET /api/study-plan/current ---


class TestGetCurrentPlan:
    def test_returns_active_plan(self, client):
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

    def test_no_plan_returns_404(self, client):
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
        resp = client.get("/api/study-plan/current")
        assert resp.status_code in (401, 403)


# --- PUT /api/study-plan/recalculate ---


class TestRecalculatePlan:
    def test_recalculate_updates_plan(self, client):
        token = _make_token()
        existing_plan = _mock_plan(target_score=80)
        new_plan = _mock_plan(target_score=70)
        new_plan["target_score"] = 70
        new_plan["plan_data"]["target_score"] = 70

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
                json={"target_score": 70},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        assert resp.json()["target_score"] == 70

    def test_recalculate_no_existing_plan(self, client):
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
                json={"target_score": 70},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 404

    def test_recalculate_no_auth(self, client):
        resp = client.put(
            "/api/study-plan/recalculate",
            json={"target_score": 70},
        )
        assert resp.status_code in (401, 403)


# --- POST /api/study-plan/assess/{task_number} ---


class TestStartAssessment:
    def test_start_returns_problems(self, client):
        token = _make_token()
        problems = [
            {"id": f"p{i}", "task_number": 1, "difficulty": "medium",
             "problem_text": f"Solve {i}", "problem_images": None, "hints": None}
            for i in range(10)
        ]

        with patch(
            "app.routers.study_plan.get_supabase_client",
            return_value=MagicMock(),
        ), patch(
            "app.routers.study_plan.start_assessment",
            return_value=problems,
        ):
            resp = client.post(
                "/api/study-plan/assess/1",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["task_number"] == 1
        assert len(data["problems"]) == 10

    def test_start_invalid_task_number(self, client):
        token = _make_token()
        resp = client.post(
            "/api/study-plan/assess/0",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    def test_start_no_problems(self, client):
        token = _make_token()

        with patch(
            "app.routers.study_plan.get_supabase_client",
            return_value=MagicMock(),
        ), patch(
            "app.routers.study_plan.start_assessment",
            return_value=[],
        ):
            resp = client.post(
                "/api/study-plan/assess/19",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 404


# --- POST /api/study-plan/assess/{task_number}/submit ---


class TestSubmitAssessment:
    def test_submit_returns_result(self, client):
        token = _make_token()
        assessment_result = {
            "task_number": 1,
            "correct_count": 7,
            "total_count": 10,
            "status": "good",
            "details": [
                {"problem_id": "p1", "is_correct": True, "correct_answer": "42", "solution_markdown": None},
            ],
        }
        plan = _mock_plan()

        with patch(
            "app.routers.study_plan.get_supabase_client",
            return_value=MagicMock(),
        ), patch(
            "app.routers.study_plan.submit_assessment",
            return_value=assessment_result,
        ), patch(
            "app.routers.study_plan.get_current_plan",
            return_value=plan,
        ), patch(
            "app.routers.study_plan.generate_plan",
            return_value=plan,
        ):
            resp = client.post(
                "/api/study-plan/assess/1/submit",
                json={"answers": [{"problem_id": "p1", "answer": "42"}]},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["correct_count"] == 7
        assert data["status"] == "good"

    def test_submit_empty_answers(self, client):
        token = _make_token()
        resp = client.post(
            "/api/study-plan/assess/1/submit",
            json={"answers": []},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    def test_submit_invalid_task(self, client):
        token = _make_token()
        resp = client.post(
            "/api/study-plan/assess/20/submit",
            json={"answers": [{"problem_id": "p1", "answer": "42"}]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
