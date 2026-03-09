import os
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _mock_env():
    env = {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_KEY": "test-service-key",
        "JWT_SECRET": "test-jwt-secret",
    }
    with patch.dict(os.environ, env):
        yield


def test_settings_loads_from_env(_mock_env):
    from app.core.config import Settings

    s = Settings()  # type: ignore[call-arg]
    assert s.SUPABASE_URL == "https://test.supabase.co"
    assert s.SUPABASE_SERVICE_KEY == "test-service-key"
    assert s.JWT_SECRET == "test-jwt-secret"


def test_get_supabase_client_returns_client(_mock_env):
    from app.db.supabase_client import get_supabase_client

    client = get_supabase_client()
    assert client is not None


def test_verify_connection_returns_false_with_fake_creds(_mock_env):
    import asyncio

    from app.db.supabase_client import verify_connection

    result = asyncio.run(verify_connection())
    assert result is False  # fake creds should fail
