"""Tests for Prototype API endpoints."""

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


def _mock_prototype(
    proto_id: str = "proto-1",
    task_number: int = 6,
    prototype_code: str = "6.1",
    title: str = "Площади фигур",
    difficulty: str = "easy",
) -> dict:
    return {
        "id": proto_id,
        "task_number": task_number,
        "prototype_code": prototype_code,
        "title": title,
        "description": "Вычисление площадей",
        "difficulty_within_task": difficulty,
        "estimated_study_minutes": 30,
        "theory_markdown": "# Площади\n\nФормула: $S = ab$",
        "key_formulas": [{"name": "Площадь прямоугольника", "formula": "S = ab"}],
        "solution_algorithm": [{"step": 1, "text": "Определить тип фигуры"}],
        "common_mistakes": [{"mistake": "Перепутать формулы"}],
        "related_prototypes": [{"code": "6.2", "title": "Углы"}],
        "order_index": 0,
    }


def _mock_video(
    video_id: str = "vid-1",
    prototype_id: str = "proto-1",
) -> dict:
    return {
        "id": video_id,
        "prototype_id": prototype_id,
        "youtube_video_id": "dQw4w9WgXcQ",
        "title": "Площади фигур — разбор",
        "channel_name": "Школково",
        "duration_seconds": 600,
        "timestamps": [
            {"time": 0, "label": "Intro"},
            {"time": 120, "label": "Формулы"},
        ],
        "order_index": 0,
    }


def _mock_problem(
    problem_id: str = "prob-1",
    prototype_id: str = "proto-1",
    task_number: int = 6,
) -> dict:
    return {
        "id": problem_id,
        "topic_id": "topic-6",
        "task_number": task_number,
        "difficulty": "medium",
        "problem_text": "Найдите площадь прямоугольника 3x4",
        "problem_images": None,
        "hints": ["Вспомните формулу"],
        "source": "ФИПИ",
        "prototype_id": prototype_id,
        "source_url": None,
        "content_hash": None,
    }


# --- GET /api/prototypes ---


class TestListPrototypes:
    def test_returns_all_prototypes(self, client):
        """List all prototypes sorted by task_number and order_index."""
        token = _make_token()
        protos = [
            _mock_prototype("proto-1", 6, "6.1"),
            _mock_prototype("proto-2", 6, "6.2", title="Углы"),
            _mock_prototype("proto-3", 7, "7.1", title="Производная"),
        ]

        mock_client = MagicMock()
        (
            mock_client.table.return_value
            .select.return_value
            .order.return_value
            .order.return_value
            .execute.return_value
        ) = MagicMock(data=protos, count=3)

        with patch(
            "app.routers.prototypes.get_supabase_client",
            return_value=mock_client,
        ):
            resp = client.get(
                "/api/prototypes",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert data["items"][0]["prototype_code"] == "6.1"
        assert data["items"][2]["task_number"] == 7

    def test_filter_by_task_number(self, client):
        """Filter prototypes by task_number query param."""
        token = _make_token()
        protos = [
            _mock_prototype("proto-1", 6, "6.1"),
            _mock_prototype("proto-2", 6, "6.2", title="Углы"),
        ]

        mock_client = MagicMock()
        (
            mock_client.table.return_value
            .select.return_value
            .eq.return_value
            .order.return_value
            .order.return_value
            .execute.return_value
        ) = MagicMock(data=protos, count=2)

        with patch(
            "app.routers.prototypes.get_supabase_client",
            return_value=mock_client,
        ):
            resp = client.get(
                "/api/prototypes?task_number=6",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert all(p["task_number"] == 6 for p in data["items"])

    def test_empty_list(self, client):
        """No prototypes → empty items, total=0."""
        token = _make_token()

        mock_client = MagicMock()
        (
            mock_client.table.return_value
            .select.return_value
            .order.return_value
            .order.return_value
            .execute.return_value
        ) = MagicMock(data=[], count=0)

        with patch(
            "app.routers.prototypes.get_supabase_client",
            return_value=mock_client,
        ):
            resp = client.get(
                "/api/prototypes",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_auth_required(self, client):
        """No token → 401/403."""
        resp = client.get("/api/prototypes")
        assert resp.status_code in (401, 403)


# --- GET /api/prototypes/{id} ---


class TestGetPrototype:
    def test_returns_full_detail(self, client):
        """Returns full prototype with theory_markdown, key_formulas, etc."""
        token = _make_token()
        proto = _mock_prototype()

        mock_client = MagicMock()
        (
            mock_client.table.return_value
            .select.return_value
            .eq.return_value
            .execute.return_value
        ) = MagicMock(data=[proto])

        with patch(
            "app.routers.prototypes.get_supabase_client",
            return_value=mock_client,
        ):
            resp = client.get(
                "/api/prototypes/proto-1",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "proto-1"
        assert data["prototype_code"] == "6.1"
        assert data["theory_markdown"] is not None
        assert "Площади" in data["theory_markdown"]
        assert len(data["key_formulas"]) == 1
        assert len(data["solution_algorithm"]) == 1
        assert len(data["common_mistakes"]) == 1
        assert len(data["related_prototypes"]) == 1

    def test_not_found(self, client):
        """Non-existent prototype → 404."""
        token = _make_token()

        mock_client = MagicMock()
        (
            mock_client.table.return_value
            .select.return_value
            .eq.return_value
            .execute.return_value
        ) = MagicMock(data=[])

        with patch(
            "app.routers.prototypes.get_supabase_client",
            return_value=mock_client,
        ):
            resp = client.get(
                "/api/prototypes/nonexistent",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 404

    def test_auth_required(self, client):
        resp = client.get("/api/prototypes/proto-1")
        assert resp.status_code in (401, 403)


# --- GET /api/prototypes/{id}/videos ---


class TestGetPrototypeVideos:
    def test_returns_videos(self, client):
        """Returns video resources for a prototype."""
        token = _make_token()
        videos = [
            _mock_video("vid-1"),
            _mock_video("vid-2"),
        ]

        mock_client = MagicMock()

        def table_side_effect(name):
            mock_table = MagicMock()
            if name == "prototypes":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{"id": "proto-1"}])
            elif name == "video_resources":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .order.return_value
                    .execute.return_value
                ) = MagicMock(data=videos)
            return mock_table

        mock_client.table.side_effect = table_side_effect

        with patch(
            "app.routers.prototypes.get_supabase_client",
            return_value=mock_client,
        ):
            resp = client.get(
                "/api/prototypes/proto-1/videos",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["youtube_video_id"] == "dQw4w9WgXcQ"
        assert data[0]["channel_name"] == "Школково"
        assert len(data[0]["timestamps"]) == 2

    def test_empty_videos(self, client):
        """Prototype with no videos → empty list."""
        token = _make_token()

        mock_client = MagicMock()

        def table_side_effect(name):
            mock_table = MagicMock()
            if name == "prototypes":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{"id": "proto-1"}])
            elif name == "video_resources":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .order.return_value
                    .execute.return_value
                ) = MagicMock(data=[])
            return mock_table

        mock_client.table.side_effect = table_side_effect

        with patch(
            "app.routers.prototypes.get_supabase_client",
            return_value=mock_client,
        ):
            resp = client.get(
                "/api/prototypes/proto-1/videos",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        assert resp.json() == []

    def test_prototype_not_found(self, client):
        """Non-existent prototype → 404."""
        token = _make_token()

        mock_client = MagicMock()

        def table_side_effect(name):
            mock_table = MagicMock()
            if name == "prototypes":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[])
            return mock_table

        mock_client.table.side_effect = table_side_effect

        with patch(
            "app.routers.prototypes.get_supabase_client",
            return_value=mock_client,
        ):
            resp = client.get(
                "/api/prototypes/nonexistent/videos",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 404

    def test_auth_required(self, client):
        resp = client.get("/api/prototypes/proto-1/videos")
        assert resp.status_code in (401, 403)


# --- GET /api/prototypes/{id}/problems ---


class TestGetPrototypeProblems:
    def test_returns_problems_with_pagination(self, client):
        """Returns problems linked to prototype with pagination."""
        token = _make_token()
        problems = [
            _mock_problem("prob-1"),
            _mock_problem("prob-2"),
        ]

        mock_client = MagicMock()

        def table_side_effect(name):
            mock_table = MagicMock()
            if name == "prototypes":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{"id": "proto-1", "task_number": 6}])
            elif name == "problems":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .order.return_value
                    .range.return_value
                    .execute.return_value
                ) = MagicMock(data=problems, count=2)
            elif name == "topics":
                (
                    mock_table.select.return_value
                    .in_.return_value
                    .execute.return_value
                ) = MagicMock(data=[{"id": "topic-6", "max_points": 1}])
            return mock_table

        mock_client.table.side_effect = table_side_effect

        with patch(
            "app.routers.prototypes.get_supabase_client",
            return_value=mock_client,
        ):
            resp = client.get(
                "/api/prototypes/proto-1/problems?page=1&page_size=10",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["items"]) == 2
        assert data["items"][0]["prototype_id"] == "proto-1"
        assert data["items"][0]["max_points"] == 1

    def test_empty_problems(self, client):
        """Prototype with no problems → empty items."""
        token = _make_token()

        mock_client = MagicMock()

        def table_side_effect(name):
            mock_table = MagicMock()
            if name == "prototypes":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{"id": "proto-1", "task_number": 6}])
            elif name == "problems":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .order.return_value
                    .range.return_value
                    .execute.return_value
                ) = MagicMock(data=[], count=0)
            return mock_table

        mock_client.table.side_effect = table_side_effect

        with patch(
            "app.routers.prototypes.get_supabase_client",
            return_value=mock_client,
        ):
            resp = client.get(
                "/api/prototypes/proto-1/problems",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_prototype_not_found(self, client):
        """Non-existent prototype → 404."""
        token = _make_token()

        mock_client = MagicMock()

        def table_side_effect(name):
            mock_table = MagicMock()
            if name == "prototypes":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[])
            return mock_table

        mock_client.table.side_effect = table_side_effect

        with patch(
            "app.routers.prototypes.get_supabase_client",
            return_value=mock_client,
        ):
            resp = client.get(
                "/api/prototypes/nonexistent/problems",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 404

    def test_auth_required(self, client):
        resp = client.get("/api/prototypes/proto-1/problems")
        assert resp.status_code in (401, 403)
