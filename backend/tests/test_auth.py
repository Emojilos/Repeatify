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


def _make_expired_token() -> str:
    payload = {
        "sub": "user-123",
        "email": "test@example.com",
        "aud": "authenticated",
        "exp": int(time.time()) - 100,
        "iat": int(time.time()) - 200,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


# --- Registration tests ---


def test_register_success(client):
    mock_user = MagicMock()
    mock_user.id = "new-user-id"

    mock_session = MagicMock()
    mock_session.access_token = "access-tok"
    mock_session.refresh_token = "refresh-tok"
    mock_session.user = mock_user

    mock_result = MagicMock()
    mock_result.session = mock_session
    mock_result.user = mock_user

    mock_client = MagicMock()
    mock_client.auth.sign_up.return_value = mock_result
    mock_client.table.return_value.insert.return_value.execute.return_value = None

    with patch("app.routers.auth.get_supabase_client", return_value=mock_client):
        resp = client.post(
            "/auth/register",
            json={"email": "new@example.com", "password": "Secret123!"},
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["access_token"] == "access-tok"
    assert data["refresh_token"] == "refresh-tok"
    assert data["user_id"] == "new-user-id"


def test_register_no_session(client):
    mock_result = MagicMock()
    mock_result.session = None

    mock_client = MagicMock()
    mock_client.auth.sign_up.return_value = mock_result

    with patch("app.routers.auth.get_supabase_client", return_value=mock_client):
        resp = client.post(
            "/auth/register",
            json={"email": "dup@example.com", "password": "Secret123!"},
        )

    assert resp.status_code == 400


# --- Login tests ---


def test_login_success(client):
    mock_user = MagicMock()
    mock_user.id = "user-123"

    mock_session = MagicMock()
    mock_session.access_token = "access-tok"
    mock_session.refresh_token = "refresh-tok"
    mock_session.user = mock_user

    mock_result = MagicMock()
    mock_result.session = mock_session
    mock_result.user = mock_user

    mock_client = MagicMock()
    mock_client.auth.sign_in_with_password.return_value = mock_result

    with patch("app.routers.auth.get_supabase_client", return_value=mock_client):
        resp = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "Secret123!"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"] == "access-tok"
    assert data["user_id"] == "user-123"


# --- Logout tests ---


def test_logout_with_valid_token(client):
    token = _make_token()
    mock_client = MagicMock()

    with patch("app.routers.auth.get_supabase_client", return_value=mock_client):
        resp = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out successfully"


# --- Protected route (GET /auth/me) tests ---


def test_me_without_token(client):
    resp = client.get("/api/users/me")
    assert resp.status_code in (401, 403)


def test_me_with_expired_token(client):
    token = _make_expired_token()
    resp = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401


def test_me_with_invalid_token(client):
    resp = client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer garbage.token.value"},
    )
    assert resp.status_code == 401


def test_me_with_valid_token(client):
    token = _make_token(user_id="uid-999", email="me@example.com")

    mock_row = {
        "id": "uid-999",
        "display_name": "Test User",
        "exam_date": None,
        "target_score": 80,
        "current_xp": 42,
        "current_level": 2,
        "current_streak": 3,
        "longest_streak": 7,
    }
    mock_resp = MagicMock()
    mock_resp.data = mock_row

    mock_client = MagicMock()
    (
        mock_client.table.return_value
        .select.return_value
        .eq.return_value
        .maybe_single.return_value
        .execute.return_value
    ) = mock_resp

    with patch("app.routers.users.get_supabase_client", return_value=mock_client):
        resp = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "uid-999"
    assert data["email"] == "me@example.com"
    assert data["display_name"] == "Test User"
    assert data["current_xp"] == 42


def test_me_user_not_found(client):
    token = _make_token()

    mock_resp = MagicMock()
    mock_resp.data = None

    mock_client = MagicMock()
    (
        mock_client.table.return_value
        .select.return_value
        .eq.return_value
        .maybe_single.return_value
        .execute.return_value
    ) = mock_resp

    with patch("app.routers.users.get_supabase_client", return_value=mock_client):
        resp = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 404
