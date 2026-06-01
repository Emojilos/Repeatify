from types import SimpleNamespace

import pytest
from fastapi.security import HTTPAuthorizationCredentials


@pytest.mark.anyio
async def test_es256_token_without_public_key_falls_back_to_supabase(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test-service-key")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret")

    from app.core import auth

    monkeypatch.setattr(
        auth.jwt,
        "get_unverified_header",
        lambda _token: {"alg": "ES256"},
    )
    monkeypatch.setattr(auth.settings, "JWT_PUBLIC_KEY", "")

    fake_user = SimpleNamespace(id="user-123", email="user@example.com")
    fake_client = SimpleNamespace(
        auth=SimpleNamespace(get_user=lambda _token: SimpleNamespace(user=fake_user))
    )
    monkeypatch.setattr(auth, "get_supabase_client", lambda: fake_client)

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="supabase-es256-token",
    )

    assert await auth.get_current_user(credentials) == {
        "id": "user-123",
        "email": "user@example.com",
    }
