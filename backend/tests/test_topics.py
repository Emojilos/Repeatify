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


def _mock_topic_row(task_number: int = 1, topic_id: str = "topic-1") -> dict:
    return {
        "id": topic_id,
        "task_number": task_number,
        "title": f"Тема {task_number}",
        "description": f"Описание темы {task_number}",
        "difficulty_level": "basic",
        "max_points": 1,
        "estimated_study_hours": 3.0,
        "order_index": task_number,
        "parent_topic_id": None,
    }


def _mock_progress_row(topic_id: str = "topic-1") -> dict:
    return {
        "topic_id": topic_id,
        "user_id": "user-123",
        "strength_score": 0.75,
        "fire_completed_at": "2026-01-15T10:00:00",
        "total_attempts": 10,
        "correct_attempts": 8,
        "last_practiced_at": "2026-03-01T12:00:00",
    }


# --- GET /api/topics ---


def test_list_topics_no_auth(client):
    topics = [_mock_topic_row(i, f"topic-{i}") for i in range(1, 4)]

    mock_client = MagicMock()
    # topics query
    (
        mock_client.table.return_value
        .select.return_value
        .order.return_value
        .execute.return_value
    ) = MagicMock(data=topics)

    with patch("app.routers.topics.get_supabase_client", return_value=mock_client):
        resp = client.get("/api/topics")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert data[0]["task_number"] == 1
    assert data[0]["user_progress"] is None


def test_list_topics_with_auth(client):
    token = _make_token()
    topics = [_mock_topic_row(1, "topic-1"), _mock_topic_row(2, "topic-2")]
    progress = [_mock_progress_row("topic-1")]

    mock_client = MagicMock()

    # We need separate return values for topics.select and user_topic_progress.select
    topics_resp = MagicMock(data=topics)
    progress_resp = MagicMock(data=progress)

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "topics":
            (
                mock_table.select.return_value
                .order.return_value
                .execute
            ).return_value = topics_resp
        elif name == "user_topic_progress":
            (
                mock_table.select.return_value
                .eq.return_value
                .execute
            ).return_value = progress_resp
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.topics.get_supabase_client", return_value=mock_client):
        resp = client.get(
            "/api/topics",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    # topic-1 has progress
    assert data[0]["user_progress"] is not None
    assert data[0]["user_progress"]["strength_score"] == 0.75
    assert data[0]["user_progress"]["fire_completed"] is True
    # topic-2 has no progress
    assert data[1]["user_progress"] is None


def test_list_topics_empty(client):
    mock_client = MagicMock()
    (
        mock_client.table.return_value
        .select.return_value
        .order.return_value
        .execute.return_value
    ) = MagicMock(data=[])

    with patch("app.routers.topics.get_supabase_client", return_value=mock_client):
        resp = client.get("/api/topics")

    assert resp.status_code == 200
    assert resp.json() == []


# --- GET /api/topics/{topic_id} ---


def test_get_topic_no_auth(client):
    topic = _mock_topic_row(5, "topic-5")

    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "topics":
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=topic)
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.topics.get_supabase_client", return_value=mock_client):
        resp = client.get("/api/topics/topic-5")

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "topic-5"
    assert data["task_number"] == 5
    assert data["user_progress"] is None


def test_get_topic_with_progress(client):
    token = _make_token()
    topic = _mock_topic_row(5, "topic-5")
    progress = _mock_progress_row("topic-5")

    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "topics":
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=topic)
        elif name == "user_topic_progress":
            (
                mock_table.select.return_value
                .eq.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=progress)
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.topics.get_supabase_client", return_value=mock_client):
        resp = client.get(
            "/api/topics/topic-5",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["user_progress"]["strength_score"] == 0.75
    assert data["user_progress"]["fire_completed"] is True


def test_get_topic_not_found(client):
    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        (
            mock_table.select.return_value
            .eq.return_value
            .maybe_single.return_value
            .execute.return_value
        ) = MagicMock(data=None)
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.topics.get_supabase_client", return_value=mock_client):
        resp = client.get("/api/topics/nonexistent")

    assert resp.status_code == 404


def test_get_topic_no_user_progress(client):
    """Authenticated user but no progress for this topic."""
    token = _make_token()
    topic = _mock_topic_row(3, "topic-3")

    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "topics":
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=topic)
        elif name == "user_topic_progress":
            (
                mock_table.select.return_value
                .eq.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data=None)
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.topics.get_supabase_client", return_value=mock_client):
        resp = client.get(
            "/api/topics/topic-3",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    assert resp.json()["user_progress"] is None


# --- GET /api/topics/{topic_id}/relationships ---


def test_get_relationships(client):
    rel = {
        "id": "rel-1",
        "source_topic_id": "topic-1",
        "target_topic_id": "topic-5",
        "relationship_type": "prerequisite",
        "description": "Планиметрия нужна для стереометрии",
    }
    related_topic = _mock_topic_row(5, "topic-5")

    mock_client = MagicMock()

    call_order = []

    def table_side_effect(name):
        call_order.append(name)
        mock_table = MagicMock()
        if name == "topics" and len([c for c in call_order if c == "topics"]) == 1:
            # First topics call: verify topic exists
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data={"id": "topic-1"})
        elif name == "topic_relationships":
            (
                mock_table.select.return_value
                .eq.return_value
                .execute.return_value
            ) = MagicMock(data=[rel])
        elif name == "topics":
            # Second topics call: get related topics
            (
                mock_table.select.return_value
                .in_.return_value
                .execute.return_value
            ) = MagicMock(data=[related_topic])
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.topics.get_supabase_client", return_value=mock_client):
        resp = client.get("/api/topics/topic-1/relationships")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["relationship_type"] == "prerequisite"
    assert data[0]["related_topic"]["task_number"] == 5


def test_get_relationships_empty(client):
    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "topics":
            (
                mock_table.select.return_value
                .eq.return_value
                .maybe_single.return_value
                .execute.return_value
            ) = MagicMock(data={"id": "topic-1"})
        elif name == "topic_relationships":
            (
                mock_table.select.return_value
                .eq.return_value
                .execute.return_value
            ) = MagicMock(data=[])
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.topics.get_supabase_client", return_value=mock_client):
        resp = client.get("/api/topics/topic-1/relationships")

    assert resp.status_code == 200
    assert resp.json() == []


def test_get_relationships_topic_not_found(client):
    mock_client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        (
            mock_table.select.return_value
            .eq.return_value
            .maybe_single.return_value
            .execute.return_value
        ) = MagicMock(data=None)
        return mock_table

    mock_client.table.side_effect = table_side_effect

    with patch("app.routers.topics.get_supabase_client", return_value=mock_client):
        resp = client.get("/api/topics/nonexistent/relationships")

    assert resp.status_code == 404
