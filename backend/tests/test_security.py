"""Tests for security features: rate limiting, CORS, input validation."""

import os
from unittest.mock import MagicMock, patch

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


# --- Rate limiting on auth endpoints ---


class TestRateLimiting:
    def test_login_rate_limit_exceeded(self, client):
        """6 login requests in a row should trigger 429."""
        from supabase_auth.errors import AuthApiError

        mock_client = MagicMock()
        mock_client.auth.sign_in_with_password.side_effect = AuthApiError(
            "Invalid credentials", 401, None,
        )

        with patch(
            "app.routers.auth.get_supabase_client",
            return_value=mock_client,
        ):
            # Default rate limit is 5/minute for auth
            statuses = []
            for _ in range(7):
                resp = client.post(
                    "/auth/login",
                    json={
                        "email": "test@example.com",
                        "password": "Secret123!",
                    },
                )
                statuses.append(resp.status_code)

            # At least one should be 429
            assert 429 in statuses

    def test_register_rate_limit_exceeded(self, client):
        """6 register requests in a row should trigger 429."""
        mock_result = MagicMock()
        mock_result.session = None

        mock_client = MagicMock()
        mock_client.auth.sign_up.return_value = mock_result

        with patch(
            "app.routers.auth.get_supabase_client",
            return_value=mock_client,
        ):
            statuses = []
            for _ in range(7):
                resp = client.post(
                    "/auth/register",
                    json={
                        "email": "test@example.com",
                        "password": "Secret123!",
                    },
                )
                statuses.append(resp.status_code)

            assert 429 in statuses


# --- Input validation ---


class TestInputValidation:
    def test_register_password_too_short(self, client):
        """Password with fewer than 6 chars should be rejected."""
        resp = client.post(
            "/auth/register",
            json={"email": "test@example.com", "password": "abc"},
        )
        assert resp.status_code == 422

    def test_register_password_too_long(self, client):
        """Password with more than 128 chars should be rejected."""
        resp = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "x" * 129,
            },
        )
        assert resp.status_code == 422

    def test_register_invalid_email(self, client):
        """Invalid email format should be rejected."""
        resp = client.post(
            "/auth/register",
            json={"email": "not-an-email", "password": "Secret123!"},
        )
        assert resp.status_code == 422

    def test_login_empty_password_rejected(self, client):
        """Empty password should be rejected."""
        resp = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": ""},
        )
        assert resp.status_code == 422

    def test_attempt_invalid_self_assessment(self, client):
        """Invalid self_assessment enum value should be rejected (422)."""
        import time

        import jwt

        token = jwt.encode(
            {
                "sub": "user-123",
                "email": "t@t.com",
                "aud": "authenticated",
                "exp": int(time.time()) + 3600,
                "iat": int(time.time()),
            },
            JWT_SECRET,
            algorithm="HS256",
        )
        resp = client.post(
            "/api/problems/some-id/attempt",
            json={
                "answer": "42",
                "time_spent_seconds": 30,
                "self_assessment": "invalid_value",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_attempt_answer_too_long(self, client):
        """Answer longer than 50 chars should be rejected."""
        import time

        import jwt

        token = jwt.encode(
            {
                "sub": "user-123",
                "email": "t@t.com",
                "aud": "authenticated",
                "exp": int(time.time()) + 3600,
                "iat": int(time.time()),
            },
            JWT_SECRET,
            algorithm="HS256",
        )
        resp = client.post(
            "/api/problems/some-id/attempt",
            json={
                "answer": "x" * 51,
                "time_spent_seconds": 30,
                "self_assessment": "good",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_profile_target_score_out_of_range(self, client):
        """target_score above 100 should be rejected."""
        import time

        import jwt

        token = jwt.encode(
            {
                "sub": "user-123",
                "email": "t@t.com",
                "aud": "authenticated",
                "exp": int(time.time()) + 3600,
                "iat": int(time.time()),
            },
            JWT_SECRET,
            algorithm="HS256",
        )
        resp = client.patch(
            "/api/users/me",
            json={"target_score": 150},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422


# --- correct_answer never leaked in GET ---


class TestCorrectAnswerNotLeaked:
    def test_get_problem_hides_correct_answer(self, client):
        """GET /api/problems/{id} must never include correct_answer."""
        import time

        import jwt

        token = jwt.encode(
            {
                "sub": "user-123",
                "email": "t@t.com",
                "aud": "authenticated",
                "exp": int(time.time()) + 3600,
                "iat": int(time.time()),
            },
            JWT_SECRET,
            algorithm="HS256",
        )

        mock_row = {
            "id": "prob-1",
            "topic_id": "topic-1",
            "task_number": 1,
            "difficulty": "basic",
            "problem_text": "Find x",
            "problem_images": None,
            "hints": ["hint1"],
            "source": "ФИПИ",
            "correct_answer": "42",
            "solution_markdown": "x = 42",
            "answer_tolerance": 0.0,
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

        with patch(
            "app.routers.problems.get_supabase_client",
            return_value=mock_client,
        ):
            resp = client.get(
                "/api/problems/prob-1",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "correct_answer" not in data
        assert "solution_markdown" not in data
        assert "answer_tolerance" not in data


# --- CORS configuration ---


class TestCORSConfiguration:
    def test_cors_allows_configured_origin(self, client):
        """Requests from configured origins should include CORS headers."""
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_cors_blocks_unknown_origin(self, client):
        """Requests from unknown origins should not get CORS headers."""
        resp = client.options(
            "/health",
            headers={
                "Origin": "https://evil.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("access-control-allow-origin") != "https://evil.example.com"

    def test_cors_restricts_methods(self, client):
        """Only allowed HTTP methods should be listed."""
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        allowed = resp.headers.get("access-control-allow-methods", "")
        # Should not be wildcard
        assert "*" not in allowed or allowed == ""

    def test_cors_restricts_headers(self, client):
        """Only allowed headers should be listed."""
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        allowed = resp.headers.get("access-control-allow-headers", "")
        assert "authorization" in allowed.lower() or "*" not in allowed
