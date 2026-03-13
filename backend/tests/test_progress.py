"""Tests for the progress router (activity calendar)."""

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
