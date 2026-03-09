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


def _mock_user_row(overrides: dict | None = None) -> dict:
    row = {
        "id": "user-123",
        "display_name": "Test User",
        "exam_date": None,
        "target_score": None,
        "current_xp": 0,
        "current_level": 1,
        "current_streak": 0,
        "longest_streak": 0,
    }
    if overrides:
        row.update(overrides)
    return row


def _setup_mock_client(row: dict):
    mock_resp = MagicMock()
    mock_resp.data = row
    mock_client = MagicMock()
    (
        mock_client.table.return_value
        .select.return_value
        .eq.return_value
        .maybe_single.return_value
        .execute.return_value
    ) = mock_resp
    return mock_client


# --- PATCH /api/users/me tests ---


def test_patch_me_update_target_score(client):
    token = _make_token()
    row = _mock_user_row()
    mock_client = _setup_mock_client(row)

    # After update, return updated row
    updated_row = _mock_user_row({"target_score": 80})
    updated_resp = MagicMock()
    updated_resp.data = updated_row
    # First call returns original (existence check), second returns updated
    chain = (
        mock_client.table.return_value
        .select.return_value
        .eq.return_value
        .maybe_single.return_value
        .execute
    )
    chain.side_effect = [
        MagicMock(data=row),
        MagicMock(data=updated_row),
    ]

    with patch("app.routers.users.get_supabase_client", return_value=mock_client):
        resp = client.patch(
            "/api/users/me",
            json={"target_score": 80},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["target_score"] == 80


def test_patch_me_update_exam_date(client):
    token = _make_token()
    row = _mock_user_row()
    updated_row = _mock_user_row({"exam_date": "2026-06-19"})

    mock_client = MagicMock()
    chain = (
        mock_client.table.return_value
        .select.return_value
        .eq.return_value
        .maybe_single.return_value
        .execute
    )
    chain.side_effect = [
        MagicMock(data=row),
        MagicMock(data=updated_row),
    ]

    with patch("app.routers.users.get_supabase_client", return_value=mock_client):
        resp = client.patch(
            "/api/users/me",
            json={"exam_date": "2026-06-19"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    assert resp.json()["exam_date"] == "2026-06-19"


def test_patch_me_invalid_target_score_too_high(client):
    token = _make_token()

    resp = client.patch(
        "/api/users/me",
        json={"target_score": 150},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 422


def test_patch_me_invalid_target_score_too_low(client):
    token = _make_token()

    resp = client.patch(
        "/api/users/me",
        json={"target_score": 10},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 422


def test_patch_me_exam_date_in_past(client):
    token = _make_token()

    resp = client.patch(
        "/api/users/me",
        json={"exam_date": "2020-01-01"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 422


def test_patch_me_empty_body(client):
    token = _make_token()
    row = _mock_user_row()
    mock_client = _setup_mock_client(row)

    with patch("app.routers.users.get_supabase_client", return_value=mock_client):
        resp = client.patch(
            "/api/users/me",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 400


def test_patch_me_without_token(client):
    resp = client.patch("/api/users/me", json={"target_score": 80})
    assert resp.status_code in (401, 403)


def test_patch_me_update_display_name(client):
    token = _make_token()
    row = _mock_user_row()
    updated_row = _mock_user_row({"display_name": "New Name"})

    mock_client = MagicMock()
    chain = (
        mock_client.table.return_value
        .select.return_value
        .eq.return_value
        .maybe_single.return_value
        .execute
    )
    chain.side_effect = [
        MagicMock(data=row),
        MagicMock(data=updated_row),
    ]

    with patch("app.routers.users.get_supabase_client", return_value=mock_client):
        resp = client.patch(
            "/api/users/me",
            json={"display_name": "New Name"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    assert resp.json()["display_name"] == "New Name"


# --- GET /api/users/me/stats tests ---


def test_stats_success(client):
    token = _make_token()
    row = _mock_user_row(
        {
            "current_xp": 120,
            "current_level": 3,
            "current_streak": 5,
            "longest_streak": 10,
        }
    )
    mock_client = _setup_mock_client(row)

    # Mock attempts count
    attempts_resp = MagicMock()
    attempts_resp.count = 42
    (
        mock_client.table.return_value
        .select.return_value
        .eq.return_value
        .eq.return_value
        .execute.return_value
    ) = attempts_resp

    with patch("app.routers.users.get_supabase_client", return_value=mock_client):
        resp = client.get(
            "/api/users/me/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["current_xp"] == 120
    assert data["current_level"] == 3
    assert data["current_streak"] == 5
    assert data["longest_streak"] == 10
    assert data["total_problems_solved"] == 42


def test_stats_no_attempts(client):
    token = _make_token()
    row = _mock_user_row()
    mock_client = _setup_mock_client(row)

    attempts_resp = MagicMock()
    attempts_resp.count = 0
    (
        mock_client.table.return_value
        .select.return_value
        .eq.return_value
        .eq.return_value
        .execute.return_value
    ) = attempts_resp

    with patch("app.routers.users.get_supabase_client", return_value=mock_client):
        resp = client.get(
            "/api/users/me/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    assert resp.json()["total_problems_solved"] == 0


def test_stats_without_token(client):
    resp = client.get("/api/users/me/stats")
    assert resp.status_code in (401, 403)


def test_stats_user_not_found(client):
    token = _make_token()
    mock_client = MagicMock()
    (
        mock_client.table.return_value
        .select.return_value
        .eq.return_value
        .maybe_single.return_value
        .execute.return_value
    ) = MagicMock(data=None)

    with patch("app.routers.users.get_supabase_client", return_value=mock_client):
        resp = client.get(
            "/api/users/me/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 404
