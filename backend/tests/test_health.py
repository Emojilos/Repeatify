import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _mock_env():
    """Provide fake env vars so Settings can be instantiated in tests."""
    env = {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_KEY": "test-service-key",
        "JWT_SECRET": "test-jwt-secret",
    }
    with patch.dict(os.environ, env):
        yield


@pytest.fixture()
def client(_mock_env):
    # Import inside fixture so env vars are set before Settings() runs
    from app.main import app

    return TestClient(app)


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "db" in data


def test_cors_headers(client):
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert (
        response.headers.get("access-control-allow-origin")
        == "http://localhost:5173"
    )
