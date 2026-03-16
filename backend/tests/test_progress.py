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
                t.select.return_value.eq.return_value.gte.return_value.order.return_value.execute.return_value
            ) = act_result
        elif name == "users":
            (
                t.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value
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

        patch_target = "app.routers.progress.get_supabase_client"
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

        patch_target = "app.routers.progress.get_supabase_client"
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
                t.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value
            ) = users_result
        elif name == "topics":
            (
                t.select.return_value.order.return_value.execute.return_value
            ) = topics_result
        elif name == "user_topic_progress":
            (
                t.select.return_value.eq.return_value.execute.return_value
            ) = progress_result
        elif name == "srs_cards":
            (
                t.select.return_value.eq.return_value.lte.return_value.neq.return_value.execute.return_value
            ) = srs_result
        elif name == "user_problem_attempts":
            (
                t.select.return_value.eq.return_value.gte.return_value.execute.return_value
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


def _mock_gap_map_client(
    *,
    topics_data=None,
    progress_data=None,
    attempts_data=None,
    problems_data=None,
):
    """Create a mock Supabase client for the gap-map endpoint."""
    mock_client = MagicMock()

    if topics_data is None:
        topics_data = [
            {"id": "t1", "task_number": 1, "title": "Планиметрия"},
            {"id": "t2", "task_number": 2, "title": "Вычисления"},
            {"id": "t3", "task_number": 3, "title": "Стереометрия"},
        ]
    if progress_data is None:
        progress_data = []
    if attempts_data is None:
        attempts_data = []
    if problems_data is None:
        problems_data = []

    topics_result = MagicMock(data=topics_data)
    progress_result = MagicMock(data=progress_data)
    attempts_result = MagicMock(data=attempts_data)
    problems_result = MagicMock(data=problems_data)

    def table_effect(name):
        t = MagicMock()
        if name == "topics":
            (
                t.select.return_value.order.return_value.execute.return_value
            ) = topics_result
        elif name == "user_topic_progress":
            (
                t.select.return_value.eq.return_value.execute.return_value
            ) = progress_result
        elif name == "user_problem_attempts":
            (
                t.select.return_value.eq.return_value.eq.return_value.gte.return_value.execute.return_value
            ) = attempts_result
        elif name == "problems":
            (
                t.select.return_value.in_.return_value.execute.return_value
            ) = problems_result
        return t

    mock_client.table.side_effect = table_effect
    return mock_client


class TestGapMap:
    def test_returns_all_topics_sorted_by_strength(self, client):
        mc = _mock_gap_map_client(
            progress_data=[
                {
                    "topic_id": "t1",
                    "strength_score": 0.8,
                    "fire_completed_at": "2026-01-01",
                },
                {"topic_id": "t2", "strength_score": 0.3, "fire_completed_at": None},
            ],
        )

        with patch(PATCH_TARGET, return_value=mc):
            token = _make_token()
            resp = client.get(
                "/api/progress/gap-map",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        entries = data["entries"]
        assert len(entries) == 3
        # Sorted by strength ascending
        assert entries[0]["strength"] == 0.0  # t3 no progress
        assert entries[1]["strength"] == 30.0  # t2
        assert entries[2]["strength"] == 80.0  # t1

    def test_error_count_from_last_30_days(self, client):
        mc = _mock_gap_map_client(
            attempts_data=[
                {
                    "problem_id": "p1",
                    "is_correct": False,
                    "created_at": "2026-03-10T12:00:00Z",
                },
                {
                    "problem_id": "p2",
                    "is_correct": False,
                    "created_at": "2026-03-12T14:00:00Z",
                },
                {
                    "problem_id": "p3",
                    "is_correct": False,
                    "created_at": "2026-03-12T15:00:00Z",
                },
            ],
            problems_data=[
                {"id": "p1", "topic_id": "t1"},
                {"id": "p2", "topic_id": "t1"},
                {"id": "p3", "topic_id": "t2"},
            ],
        )

        with patch(PATCH_TARGET, return_value=mc):
            token = _make_token()
            resp = client.get(
                "/api/progress/gap-map",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        entries = {e["task_number"]: e for e in resp.json()["entries"]}
        assert entries[1]["error_count"] == 2
        assert entries[1]["last_error_date"] == "2026-03-12"
        assert entries[2]["error_count"] == 1
        assert entries[3]["error_count"] == 0

    def test_recommended_action_depends_on_state(self, client):
        mc = _mock_gap_map_client(
            progress_data=[
                {"topic_id": "t1", "strength_score": 0.2, "fire_completed_at": None},
                {
                    "topic_id": "t2",
                    "strength_score": 0.4,
                    "fire_completed_at": "2026-01-01",
                },
                {
                    "topic_id": "t3",
                    "strength_score": 0.7,
                    "fire_completed_at": "2026-01-01",
                },
            ],
            attempts_data=[
                {
                    "problem_id": "p1",
                    "is_correct": False,
                    "created_at": "2026-03-10T12:00:00Z",
                },
                {
                    "problem_id": "p2",
                    "is_correct": False,
                    "created_at": "2026-03-10T12:00:00Z",
                },
                {
                    "problem_id": "p3",
                    "is_correct": False,
                    "created_at": "2026-03-10T12:00:00Z",
                },
                {
                    "problem_id": "p4",
                    "is_correct": False,
                    "created_at": "2026-03-10T12:00:00Z",
                },
                {
                    "problem_id": "p5",
                    "is_correct": False,
                    "created_at": "2026-03-10T12:00:00Z",
                },
            ],
            problems_data=[
                {"id": "p1", "topic_id": "t2"},
                {"id": "p2", "topic_id": "t2"},
                {"id": "p3", "topic_id": "t2"},
                {"id": "p4", "topic_id": "t2"},
                {"id": "p5", "topic_id": "t2"},
            ],
        )

        with patch(PATCH_TARGET, return_value=mc):
            token = _make_token()
            resp = client.get(
                "/api/progress/gap-map",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        entries = {e["task_number"]: e for e in resp.json()["entries"]}
        # Low strength, no FIRe → "Пройти FIRe-flow заново"
        assert entries[1]["recommended_action"] == "Пройти FIRe-flow заново"
        # strength < 0.5 with 5 errors → "Повторить теорию"
        assert entries[2]["recommended_action"] == "Повторить теорию"
        # strength >= 0.5 → "Решить 5 задач"
        assert entries[3]["recommended_action"] == "Решить 5 задач"

    def test_filter_by_task_number(self, client):
        mc = _mock_gap_map_client()

        with patch(PATCH_TARGET, return_value=mc):
            token = _make_token()
            resp = client.get(
                "/api/progress/gap-map?task_number=2",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        entries = resp.json()["entries"]
        assert len(entries) == 1
        assert entries[0]["task_number"] == 2

    def test_filter_by_strength_range(self, client):
        mc = _mock_gap_map_client(
            progress_data=[
                {"topic_id": "t1", "strength_score": 0.8, "fire_completed_at": None},
                {"topic_id": "t2", "strength_score": 0.4, "fire_completed_at": None},
                {"topic_id": "t3", "strength_score": 0.1, "fire_completed_at": None},
            ],
        )

        with patch(PATCH_TARGET, return_value=mc):
            token = _make_token()
            resp = client.get(
                "/api/progress/gap-map?min_strength=0.2&max_strength=0.5",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        entries = resp.json()["entries"]
        assert len(entries) == 1
        assert entries[0]["task_number"] == 2

    def test_empty_progress(self, client):
        mc = _mock_gap_map_client()

        with patch(PATCH_TARGET, return_value=mc):
            token = _make_token()
            resp = client.get(
                "/api/progress/gap-map",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        entries = resp.json()["entries"]
        assert len(entries) == 3
        # All strength should be 0
        assert all(e["strength"] == 0.0 for e in entries)
        # All should recommend FIRe-flow (no progress, no fire)
        assert all(
            e["recommended_action"] == "Пройти FIRe-flow заново" for e in entries
        )

    def test_requires_auth(self, client):
        resp = client.get("/api/progress/gap-map")
        assert resp.status_code in (401, 403)


def _mock_readiness_client(
    *,
    user_data=None,
    topics_data=None,
    progress_data=None,
):
    """Create a mock Supabase client for the exam-readiness endpoint."""
    mock_client = MagicMock()

    if user_data is None:
        user_data = {"exam_date": "2026-06-19"}
    if topics_data is None:
        topics_data = [
            {
                "id": "t1", "task_number": 1,
                "title": "Планиметрия",
                "max_points": 1, "estimated_study_hours": 1.0,
            },
            {
                "id": "t2", "task_number": 2,
                "title": "Вычисления",
                "max_points": 1, "estimated_study_hours": 1.0,
            },
            {
                "id": "t3", "task_number": 13,
                "title": "Стереометрия Ч2",
                "max_points": 3, "estimated_study_hours": 4.0,
            },
        ]
    if progress_data is None:
        progress_data = []

    users_result = MagicMock(data=user_data)
    topics_result = MagicMock(data=topics_data)
    progress_result = MagicMock(data=progress_data)

    def table_effect(name):
        t = MagicMock()
        if name == "users":
            (
                t.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value
            ) = users_result
        elif name == "topics":
            (
                t.select.return_value.order.return_value.execute.return_value
            ) = topics_result
        elif name == "user_topic_progress":
            (
                t.select.return_value.eq.return_value.execute.return_value
            ) = progress_result
        return t

    mock_client.table.side_effect = table_effect
    return mock_client


class TestExamReadiness:
    def test_returns_all_fields(self, client):
        exam_date = (date.today() + timedelta(days=60)).isoformat()
        mc = _mock_readiness_client(
            user_data={"exam_date": exam_date},
        )

        with patch(PATCH_TARGET, return_value=mc):
            token = _make_token()
            resp = client.get(
                "/api/progress/exam-readiness",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "readiness_percent" in data
        assert "exam_countdown" in data
        assert data["exam_countdown"] == 60
        assert "priority_topics" in data
        assert "summary" in data
        assert len(data["priority_topics"]) <= 5

    def test_high_points_low_strength_is_top_priority(self, client):
        """A high-points weak topic should appear first in priority list."""
        fc = "2026-01-01"
        mc = _mock_readiness_client(
            progress_data=[
                {"topic_id": "t1", "strength_score": 0.9, "fire_completed_at": fc},
                {"topic_id": "t2", "strength_score": 0.9, "fire_completed_at": fc},
            ],
        )

        with patch(PATCH_TARGET, return_value=mc):
            token = _make_token()
            resp = client.get(
                "/api/progress/exam-readiness",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        # t3 (Стереометрия Ч2, 3 points, strength=0) should be first
        assert data["priority_topics"][0]["task_number"] == 13
        assert data["priority_topics"][0]["priority_score"] > 0

    def test_low_points_high_strength_is_low_priority(self, client):
        """A mastered low-points topic should rank last."""
        mc = _mock_readiness_client(
            progress_data=[
                {
                    "topic_id": "t1",
                    "strength_score": 0.9,
                    "fire_completed_at": "2026-01-01",
                },
                {
                    "topic_id": "t3",
                    "strength_score": 0.1,
                    "fire_completed_at": None,
                },
            ],
        )

        with patch(PATCH_TARGET, return_value=mc):
            token = _make_token()
            resp = client.get(
                "/api/progress/exam-readiness",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        topics = {t["task_number"]: t for t in resp.json()["priority_topics"]}
        # t1 (1pt, strength=0.9) should have lower priority than t3 (3pt, strength=0.1)
        assert topics[1]["priority_score"] < topics[13]["priority_score"]

    def test_no_exam_date(self, client):
        mc = _mock_readiness_client(user_data={"exam_date": None})

        with patch(PATCH_TARGET, return_value=mc):
            token = _make_token()
            resp = client.get(
                "/api/progress/exam-readiness",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["exam_countdown"] is None
        assert data["readiness_percent"] == 0.0

    def test_readiness_weighted_by_points(self, client):
        """Readiness should be weighted by max_points."""
        mc = _mock_readiness_client(
            progress_data=[
                {
                    "topic_id": "t1",
                    "strength_score": 1.0,
                    "fire_completed_at": "2026-01-01",
                },
            ],
        )

        with patch(PATCH_TARGET, return_value=mc):
            token = _make_token()
            resp = client.get(
                "/api/progress/exam-readiness",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        # (1*1.0 + 1*0.0 + 3*0.0) / 5 = 20%
        assert data["readiness_percent"] == 20.0

    def test_exam_urgency_affects_priority(self, client):
        """Topics should have higher priority when exam is closer."""
        exam_soon = (date.today() + timedelta(days=10)).isoformat()
        mc_soon = _mock_readiness_client(user_data={"exam_date": exam_soon})

        exam_far = (date.today() + timedelta(days=120)).isoformat()
        mc_far = _mock_readiness_client(user_data={"exam_date": exam_far})

        with patch(PATCH_TARGET, return_value=mc_soon):
            token = _make_token()
            resp_soon = client.get(
                "/api/progress/exam-readiness",
                headers={"Authorization": f"Bearer {token}"},
            )

        with patch(PATCH_TARGET, return_value=mc_far):
            token = _make_token()
            resp_far = client.get(
                "/api/progress/exam-readiness",
                headers={"Authorization": f"Bearer {token}"},
            )

        soon_top = resp_soon.json()["priority_topics"][0]["priority_score"]
        far_top = resp_far.json()["priority_topics"][0]["priority_score"]
        assert soon_top > far_top

    def test_requires_auth(self, client):
        resp = client.get("/api/progress/exam-readiness")
        assert resp.status_code in (401, 403)


# --- GET /api/progress/predicted-score ---

PATCH_PREDICTED = "app.routers.progress.get_supabase_client"


class TestPredictedScore:
    def test_returns_predicted_score(self, client):
        """Returns predicted score with breakdown for all 19 tasks."""
        mc = MagicMock()

        def table_side_effect(name):
            mt = MagicMock()
            if name == "users":
                (
                    mt.select.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{"exam_date": "2026-06-01"}])
            return mt

        mc.table.side_effect = table_side_effect

        mock_result = {
            "predicted_primary_score": 12,
            "predicted_test_score": 70,
            "breakdown": {
                tn: {
                    "cards_count": 1 if tn <= 12 else 0,
                    "avg_retrievability": 0.9 if tn <= 12 else 0.0,
                    "is_mastered": tn <= 12,
                    "points": 1 if tn <= 12 else (4 if tn >= 18 else 2),
                }
                for tn in range(1, 20)
            },
        }

        with patch(PATCH_PREDICTED, return_value=mc), patch(
            "app.routers.progress.predict_score",
            return_value=mock_result,
        ):
            token = _make_token()
            resp = client.get(
                "/api/progress/predicted-score",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["predicted_primary_score"] == 12
        assert data["predicted_test_score"] == 70
        assert len(data["breakdown"]) == 19
        assert data["breakdown"]["1"]["is_mastered"] is True
        assert data["breakdown"]["13"]["is_mastered"] is False

    def test_no_exam_date(self, client):
        """Works when user has no exam_date set."""
        mc = MagicMock()

        def table_side_effect(name):
            mt = MagicMock()
            if name == "users":
                (
                    mt.select.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{"exam_date": None}])
            return mt

        mc.table.side_effect = table_side_effect

        mock_result = {
            "predicted_primary_score": 0,
            "predicted_test_score": 0,
            "breakdown": {
                tn: {
                    "cards_count": 0,
                    "avg_retrievability": 0.0,
                    "is_mastered": False,
                    "points": 1 if tn <= 12 else (4 if tn >= 18 else 2),
                }
                for tn in range(1, 20)
            },
        }

        with patch(PATCH_PREDICTED, return_value=mc), patch(
            "app.routers.progress.predict_score",
            return_value=mock_result,
        ) as mock_ps:
            token = _make_token()
            resp = client.get(
                "/api/progress/predicted-score",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        # Verify predict_score called with exam_date=None
        call_args = mock_ps.call_args
        assert call_args[0][2] is None

    def test_high_score_part2(self, client):
        """Tasks 13-17 at 2 pts + 18-19 at 4 pts mastered → correct total."""
        mc = MagicMock()

        def table_side_effect(name):
            mt = MagicMock()
            if name == "users":
                (
                    mt.select.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[{"exam_date": "2026-06-01"}])
            return mt

        mc.table.side_effect = table_side_effect

        # All 19 tasks mastered → 12 + 5*2 + 2*4 = 30 primary → 94 test
        mock_result = {
            "predicted_primary_score": 30,
            "predicted_test_score": 94,
            "breakdown": {
                tn: {
                    "cards_count": 2,
                    "avg_retrievability": 0.95,
                    "is_mastered": True,
                    "points": 1 if tn <= 12 else (4 if tn >= 18 else 2),
                }
                for tn in range(1, 20)
            },
        }

        with patch(PATCH_PREDICTED, return_value=mc), patch(
            "app.routers.progress.predict_score",
            return_value=mock_result,
        ):
            token = _make_token()
            resp = client.get(
                "/api/progress/predicted-score",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["predicted_primary_score"] == 30
        assert data["predicted_test_score"] == 94

    def test_requires_auth(self, client):
        """Should require authentication."""
        resp = client.get("/api/progress/predicted-score")
        assert resp.status_code in (401, 403)
