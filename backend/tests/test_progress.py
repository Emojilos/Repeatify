"""Tests for the progress router (activity calendar, dashboard)."""

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


def _make_token(user_id: str = "user-123") -> str:
    payload = {
        "sub": user_id,
        "email": "test@example.com",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def _mock_table(activity_data, streak_data):
    """Create a mock client with table side effect."""
    mock_client = MagicMock()

    act_result = MagicMock(data=activity_data)
    usr_result = MagicMock(data=streak_data)

    def table_effect(name):
        t = MagicMock()
        if name == "user_daily_activity":
            (
                t.select.return_value
                .eq.return_value
                .gte.return_value
                .order.return_value
                .execute.return_value
            ) = act_result
        elif name == "users":
            (
                t.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = usr_result
        return t

    mock_client.table.side_effect = table_effect
    return mock_client


class TestActivityCalendar:
    def test_returns_activities(self, client):
        activity_data = [
            {
                "activity_date": "2026-03-12",
                "sessions_completed": 1,
                "problems_solved": 5,
                "xp_earned": 50,
                "streak_maintained": True,
            },
            {
                "activity_date": "2026-03-13",
                "sessions_completed": 2,
                "problems_solved": 10,
                "xp_earned": 100,
                "streak_maintained": True,
            },
        ]
        streak = {
            "current_streak": 3,
            "longest_streak": 7,
        }
        mc = _mock_table(activity_data, streak)

        patch_target = (
            "app.routers.progress.get_supabase_client"
        )
        with patch(patch_target, return_value=mc):
            token = _make_token()
            resp = client.get(
                "/api/progress/activity-calendar",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["activities"]) == 2
        assert data["activities"][0]["date"] == "2026-03-12"
        assert data["activities"][1]["problems_solved"] == 10
        assert data["current_streak"] == 3
        assert data["longest_streak"] == 7

    def test_empty_calendar(self, client):
        streak = {
            "current_streak": 0,
            "longest_streak": 0,
        }
        mc = _mock_table([], streak)

        patch_target = (
            "app.routers.progress.get_supabase_client"
        )
        with patch(patch_target, return_value=mc):
            token = _make_token()
            resp = client.get(
                "/api/progress/activity-calendar",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["activities"] == []
        assert data["current_streak"] == 0

    def test_requires_auth(self, client):
        resp = client.get(
            "/api/progress/activity-calendar",
        )
        assert resp.status_code in (401, 403)


def _mock_dashboard_client(
    *,
    user_data=None,
    topics_data=None,
    progress_data=None,
    srs_count=0,
    attempts_data=None,
):
    """Create a mock Supabase client for the dashboard endpoint."""
    mock_client = MagicMock()

    if user_data is None:
        user_data = {
            "exam_date": "2026-06-19",
            "current_xp": 250,
            "current_level": 3,
            "current_streak": 5,
        }
    if topics_data is None:
        topics_data = [
            {"id": "t1", "task_number": 1, "title": "Планиметрия"},
            {"id": "t2", "task_number": 2, "title": "Векторы"},
        ]
    if progress_data is None:
        progress_data = [
            {
                "topic_id": "t1",
                "strength_score": 0.8,
                "fire_completed_at": "2026-03-01T00:00:00Z",
            },
        ]
    if attempts_data is None:
        attempts_data = [
            {"is_correct": True},
            {"is_correct": True},
            {"is_correct": False},
        ]

    users_result = MagicMock(data=user_data)
    topics_result = MagicMock(data=topics_data)
    progress_result = MagicMock(data=progress_data)
    srs_result = MagicMock(data=[], count=srs_count)
    attempts_result = MagicMock(data=attempts_data)

    def table_effect(name):
        t = MagicMock()
        if name == "users":
            (
                t.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = users_result
        elif name == "topics":
            (
                t.select.return_value
                .order.return_value
                .execute.return_value
            ) = topics_result
        elif name == "user_topic_progress":
            (
                t.select.return_value
                .eq.return_value
                .execute.return_value
            ) = progress_result
        elif name == "srs_cards":
            (
                t.select.return_value
                .eq.return_value
                .lte.return_value
                .neq.return_value
                .execute.return_value
            ) = srs_result
        elif name == "user_problem_attempts":
            (
                t.select.return_value
                .eq.return_value
                .gte.return_value
                .execute.return_value
            ) = attempts_result
        return t

    mock_client.table.side_effect = table_effect
    return mock_client


PATCH_TARGET = "app.routers.progress.get_supabase_client"


class TestDashboard:
    def test_returns_all_fields(self, client):
        exam_date = (date.today() + timedelta(days=60)).isoformat()
        mc = _mock_dashboard_client(
            user_data={
                "exam_date": exam_date,
                "current_xp": 250,
                "current_level": 3,
                "current_streak": 5,
            },
            srs_count=5,
        )

        with patch(PATCH_TARGET, return_value=mc):
            token = _make_token()
            resp = client.get(
                "/api/progress/dashboard",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["exam_countdown"] == 60
        assert len(data["topics_progress"]) == 2
        assert data["topics_progress"][0]["task_number"] == 1
        assert data["topics_progress"][0]["strength_score"] == 0.8
        assert data["topics_progress"][0]["fire_completed"] is True
        assert data["topics_progress"][1]["strength_score"] == 0.0
        assert data["topics_progress"][1]["fire_completed"] is False
        assert data["today_review_count"] == 5
        assert data["weekly_stats"]["problems_solved"] == 3
        assert data["weekly_stats"]["problems_correct"] == 2
        assert data["current_xp"] == 250
        assert data["current_level"] == 3
        assert data["current_streak"] == 5
        assert len(data["recommendations"]) > 0

    def test_no_exam_date(self, client):
        mc = _mock_dashboard_client(
            user_data={
                "exam_date": None,
                "current_xp": 0,
                "current_level": 1,
                "current_streak": 0,
            },
        )

        with patch(PATCH_TARGET, return_value=mc):
            token = _make_token()
            resp = client.get(
                "/api/progress/dashboard",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["exam_countdown"] is None

    def test_no_review_cards(self, client):
        mc = _mock_dashboard_client(srs_count=0)

        with patch(PATCH_TARGET, return_value=mc):
            token = _make_token()
            resp = client.get(
                "/api/progress/dashboard",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["today_review_count"] == 0

    def test_empty_weekly_stats(self, client):
        mc = _mock_dashboard_client(attempts_data=[])

        with patch(PATCH_TARGET, return_value=mc):
            token = _make_token()
            resp = client.get(
                "/api/progress/dashboard",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["weekly_stats"]["problems_solved"] == 0
        assert data["weekly_stats"]["problems_correct"] == 0
        # Should recommend solving problems
        assert any("не решали" in r for r in data["recommendations"])

    def test_weak_topics_in_recommendations(self, client):
        mc = _mock_dashboard_client(
            progress_data=[
                {"topic_id": "t1", "strength_score": 0.2, "fire_completed_at": None},
                {"topic_id": "t2", "strength_score": 0.3, "fire_completed_at": None},
            ],
            srs_count=0,
        )

        with patch(PATCH_TARGET, return_value=mc):
            token = _make_token()
            resp = client.get(
                "/api/progress/dashboard",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert any("слабые темы" in r for r in data["recommendations"])

    def test_requires_auth(self, client):
        resp = client.get("/api/progress/dashboard")
        assert resp.status_code in (401, 403)
