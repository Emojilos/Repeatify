"""End-to-end integration test: full user journey through all API endpoints.

Covers the complete flow:
  1. Register a new user
  2. Configure profile (exam_date, target_score)
  3. Browse topic catalog → select a topic
  4. Complete FIRe-flow (4 stages)
  5. Solve 5 problems for the topic
  6. Start SRS session → review cards
  7. View results and dashboard
"""

import os
import time
from collections import defaultdict
from contextlib import ExitStack
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi.testclient import TestClient

JWT_SECRET = "test-jwt-secret"
USER_ID = "e2e-user-001"
EMAIL = "e2e@example.com"


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


def _make_token(user_id: str = USER_ID, email: str = EMAIL) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


# ---------------------------------------------------------------------------
# In-memory fake Supabase for stateful E2E testing
# ---------------------------------------------------------------------------


class _FakeResult:
    """Mimics Supabase query result."""

    def __init__(self, data, count=None):
        self.data = data
        self.count = count


class _FakeTableQuery:
    """Chainable query builder over a plain list of dicts."""

    def __init__(self, tables: dict[str, list[dict]], table_name: str):
        self._tables = tables
        self._name = table_name
        self._filters: list[tuple[str, str, object]] = []
        self._select_cols: str = "*"
        self._count_mode: str | None = None
        self._order_col: str | None = None
        self._range_start: int | None = None
        self._range_end: int | None = None
        self._limit_val: int | None = None
        self._insert_data = None
        self._update_data: dict | None = None
        self._maybe_single = False

    # --- builder methods (return self for chaining) ---

    def select(self, cols: str = "*", **kwargs):
        self._select_cols = cols
        if kwargs.get("count"):
            self._count_mode = kwargs["count"]
        return self

    def eq(self, col, val):
        self._filters.append(("eq", col, val))
        return self

    def neq(self, col, val):
        self._filters.append(("neq", col, val))
        return self

    def lte(self, col, val):
        self._filters.append(("lte", col, val))
        return self

    def gte(self, col, val):
        self._filters.append(("gte", col, val))
        return self

    def in_(self, col, values):
        self._filters.append(("in", col, list(values)))
        return self

    def order(self, col, **_kwargs):
        self._order_col = col
        return self

    def range(self, start, end):
        self._range_start = start
        self._range_end = end
        return self

    def limit(self, val):
        self._limit_val = val
        return self

    def maybe_single(self):
        self._maybe_single = True
        return self

    def insert(self, data):
        self._insert_data = data
        return self

    def update(self, data):
        self._update_data = data
        return self

    # --- execution ---

    def _apply_filters(self, rows: list[dict]) -> list[dict]:
        result = list(rows)
        for op, col, val in self._filters:
            if op == "eq":
                result = [r for r in result if r.get(col) == val]
            elif op == "neq":
                result = [r for r in result if r.get(col) != val]
            elif op == "lte":
                result = [
                    r for r in result
                    if r.get(col) is not None and str(r[col]) <= str(val)
                ]
            elif op == "gte":
                result = [
                    r for r in result
                    if r.get(col) is not None and str(r[col]) >= str(val)
                ]
            elif op == "in":
                result = [r for r in result if r.get(col) in val]
        return result

    def _project(self, rows: list[dict]) -> list[dict]:
        if self._select_cols == "*":
            return [dict(r) for r in rows]
        cols = [c.strip() for c in self._select_cols.split(",")]
        return [{c: r.get(c) for c in cols} for r in rows]

    def execute(self) -> _FakeResult:
        table = self._tables[self._name]

        # INSERT — auto-populate created_at like a real DB default
        if self._insert_data is not None:
            now_str = datetime.now(timezone.utc).isoformat()
            if isinstance(self._insert_data, list):
                for row in self._insert_data:
                    row.setdefault("created_at", now_str)
                table.extend(self._insert_data)
            else:
                self._insert_data.setdefault("created_at", now_str)
                table.append(self._insert_data)
            return _FakeResult(self._insert_data)

        # UPDATE
        if self._update_data is not None:
            filtered = self._apply_filters(table)
            for row in filtered:
                row.update(self._update_data)
            return _FakeResult(filtered)

        # SELECT
        filtered = self._apply_filters(table)
        if self._order_col:
            filtered.sort(key=lambda r: r.get(self._order_col) or 0)
        total = len(filtered)
        if self._range_start is not None:
            filtered = filtered[self._range_start:self._range_end + 1]
        if self._limit_val is not None:
            filtered = filtered[:self._limit_val]
        projected = self._project(filtered)

        if self._maybe_single:
            return _FakeResult(projected[0] if projected else None)

        count = total if self._count_mode else None
        return _FakeResult(projected, count=count)


class FakeSupabase:
    """Stateful in-memory Supabase mock with seed data."""

    def __init__(self):
        self.tables: dict[str, list[dict]] = defaultdict(list)
        self.auth = MagicMock()
        self._seed()

    def table(self, name: str) -> _FakeTableQuery:
        return _FakeTableQuery(self.tables, name)

    # ---- seed helpers ----

    def _seed(self):
        # 19 EGE topics
        for i in range(1, 20):
            self.tables["topics"].append({
                "id": f"topic-{i}",
                "task_number": i,
                "title": f"Тема {i}",
                "description": f"Описание темы {i}",
                "max_points": 1 if i <= 12 else 3,
                "difficulty_level": "basic" if i <= 6 else "medium",
                "estimated_study_hours": 5.0,
                "parent_topic_id": None,
            })

        # 5 problems for topic-6
        for j in range(1, 6):
            self.tables["problems"].append({
                "id": f"prob-{j}",
                "topic_id": "topic-6",
                "task_number": 6,
                "difficulty": ["basic", "medium", "hard"][j % 3],
                "problem_text": f"Найдите значение $x^{j} = {j}$",
                "problem_images": None,
                "correct_answer": str(j),
                "answer_tolerance": 0.0,
                "solution_markdown": f"Ответ: {j}.",
                "solution_images": None,
                "hints": [f"Подсказка {j}"],
                "source": "ФИПИ",
            })

        # Theory content for topic-6 (4 FIRe stages)
        for idx, stage in enumerate(
            ["framework", "inquiry", "relationships", "elaboration"]
        ):
            self.tables["theory_content"].append({
                "id": f"theory-{stage}",
                "topic_id": "topic-6",
                "content_type": stage,
                "content_markdown": f"# {stage.title()}\n\n$x^2+1=0$",
                "visual_assets": [],
                "order_index": idx,
            })

        # Topic relationships for topic-6
        self.tables["topic_relationships"].append({
            "id": "rel-1",
            "source_topic_id": "topic-6",
            "target_topic_id": "topic-7",
            "relationship_type": "prerequisite",
        })

        # User row (created by registration, pre-seeded for simplicity)
        self.tables["users"].append({
            "id": USER_ID,
            "display_name": None,
            "exam_date": None,
            "target_score": None,
            "current_xp": 0,
            "current_level": 1,
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
        })


# Modules whose get_supabase_client needs patching
_PATCHED_MODULES = [
    "app.routers.auth",
    "app.routers.users",
    "app.routers.topics",
    "app.routers.problems",
    "app.routers.srs",
    "app.routers.theory",
    "app.routers.progress",
]


# ---------------------------------------------------------------------------
# The E2E test
# ---------------------------------------------------------------------------


class TestFullUserJourney:
    """Simulate a complete user path through the application."""

    def test_full_journey(self, client):  # noqa: C901
        """Register → profile → topics → FIRe → problems → SRS → dashboard."""
        fake = FakeSupabase()
        token = _make_token()
        headers = {"Authorization": f"Bearer {token}"}
        today = date.today()

        # Configure auth mocks
        mock_user = MagicMock()
        mock_user.id = USER_ID
        mock_session = MagicMock()
        mock_session.access_token = "fake-access-token"
        mock_session.refresh_token = "fake-refresh-token"
        mock_session.user = mock_user
        mock_result = MagicMock()
        mock_result.session = mock_session
        mock_result.user = mock_user
        fake.auth.sign_up.return_value = mock_result
        fake.auth.sign_in_with_password.return_value = mock_result

        with ExitStack() as stack:
            for mod in _PATCHED_MODULES:
                stack.enter_context(
                    patch(f"{mod}.get_supabase_client", return_value=fake)
                )

            # =============================================
            # Step 1: Register
            # =============================================
            resp = client.post(
                "/auth/register",
                json={"email": EMAIL, "password": "Secret123!"},
            )
            assert resp.status_code == 201
            data = resp.json()
            assert data["access_token"] == "fake-access-token"
            assert data["user_id"] == USER_ID

            # =============================================
            # Step 2: Login (verify it works too)
            # =============================================
            resp = client.post(
                "/auth/login",
                json={"email": EMAIL, "password": "Secret123!"},
            )
            assert resp.status_code == 200
            assert resp.json()["access_token"] == "fake-access-token"

            # =============================================
            # Step 3: Configure profile
            # =============================================
            exam_date = (today + timedelta(days=90)).isoformat()
            resp = client.patch(
                "/api/users/me",
                headers=headers,
                json={
                    "target_score": 80,
                    "exam_date": exam_date,
                },
            )
            assert resp.status_code == 200
            profile = resp.json()
            assert profile["target_score"] == 80
            assert profile["exam_date"] == exam_date

            # Verify profile persisted
            resp = client.get("/api/users/me", headers=headers)
            assert resp.status_code == 200
            assert resp.json()["target_score"] == 80

            # =============================================
            # Step 4: Browse topics catalog
            # =============================================
            resp = client.get("/api/topics", headers=headers)
            assert resp.status_code == 200
            topics = resp.json()
            assert len(topics) == 19
            # Topics should be sorted by task_number
            assert topics[0]["task_number"] == 1
            assert topics[18]["task_number"] == 19

            # =============================================
            # Step 5: View topic detail (topic-6)
            # =============================================
            resp = client.get("/api/topics/topic-6", headers=headers)
            assert resp.status_code == 200
            topic = resp.json()
            assert topic["task_number"] == 6
            assert topic["title"] == "Тема 6"

            # View topic relationships
            resp = client.get(
                "/api/topics/topic-6/relationships", headers=headers
            )
            assert resp.status_code == 200

            # =============================================
            # Step 6: FIRe-flow (4 stages)
            # =============================================
            # Get theory content
            resp = client.get(
                "/api/topics/topic-6/theory", headers=headers
            )
            assert resp.status_code == 200
            theory = resp.json()
            assert theory["topic_title"] == "Тема 6"
            assert len(theory["items"]) == 4

            # Complete all 4 FIRe stages
            stages = ["framework", "inquiry", "relationships", "elaboration"]
            for i, stage in enumerate(stages):
                resp = client.post(
                    "/api/topics/topic-6/fire-progress",
                    headers=headers,
                    json={"stage": stage},
                )
                assert resp.status_code == 200
                fire_resp = resp.json()
                assert fire_resp["completed"] is True
                assert fire_resp["stage"] == stage

                if i < 3:
                    assert fire_resp["all_stages_completed"] is False
                else:
                    # Last stage — all completed, XP earned
                    assert fire_resp["all_stages_completed"] is True
                    assert fire_resp["xp_earned"] == 50

            # Verify XP was awarded (user should have 50 XP now)
            user_row = fake.tables["users"][0]
            assert user_row["current_xp"] == 50

            # =============================================
            # Step 7: Solve 5 problems for topic-6
            # =============================================
            # List problems
            resp = client.get(
                "/api/problems?task_number=6", headers=headers
            )
            assert resp.status_code == 200
            problems_resp = resp.json()
            assert problems_resp["total"] == 5

            # View a single problem (should NOT include correct_answer)
            resp = client.get("/api/problems/prob-1", headers=headers)
            assert resp.status_code == 200
            prob_detail = resp.json()
            assert "correct_answer" not in prob_detail
            assert "solution_markdown" not in prob_detail

            # Solve all 5 problems
            total_xp_from_problems = 0
            for j in range(1, 6):
                resp = client.post(
                    f"/api/problems/prob-{j}/attempt",
                    headers=headers,
                    json={
                        "answer": str(j),  # correct answer
                        "time_spent_seconds": 30,
                        "self_assessment": "good",
                    },
                )
                assert resp.status_code == 200
                attempt = resp.json()
                assert attempt["is_correct"] is True
                assert attempt["xp_earned"] == 10  # Part 1 correct
                total_xp_from_problems += 10

            assert total_xp_from_problems == 50
            # Total XP: 50 (FIRe) + 50 (problems) = 100
            assert user_row["current_xp"] == 100

            # SRS cards should exist for each problem
            # (concept cards from FIRe + problem cards from attempts)
            srs_cards = [
                c for c in fake.tables["srs_cards"]
                if c.get("problem_id", "").startswith("prob-")
            ]
            assert len(srs_cards) >= 5

            # =============================================
            # Step 8: SRS session
            # =============================================
            # Make SRS cards due today for the session
            for card in fake.tables["srs_cards"]:
                card["next_review_date"] = today.isoformat()
                card["last_review_date"] = (
                    today - timedelta(days=1)
                ).isoformat()
                card["interval_days"] = 1.0
                card["status"] = "review"
                if not card.get("topic_id"):
                    card["topic_id"] = "topic-6"

            resp = client.get(
                "/api/srs/session?max_cards=5", headers=headers
            )
            assert resp.status_code == 200
            session = resp.json()
            assert session["total_due"] > 0
            assert len(session["cards"]) > 0

            # Review at least one card
            first_card = session["cards"][0]
            resp = client.post(
                "/api/srs/review",
                headers=headers,
                json={
                    "card_id": first_card["card_id"],
                    "answer": "1",
                    "time_spent_seconds": 20,
                    "self_assessment": "good",
                },
            )
            assert resp.status_code == 200
            review = resp.json()
            assert "next_review_date" in review
            assert review["new_interval"] > 0
            assert review["xp_earned"] >= 0

            # =============================================
            # Step 9: View dashboard
            # =============================================
            resp = client.get(
                "/api/progress/dashboard", headers=headers
            )
            assert resp.status_code == 200
            dash = resp.json()
            assert dash["exam_countdown"] is not None
            assert dash["current_xp"] > 0
            assert dash["current_level"] >= 1
            assert len(dash["topics_progress"]) == 19
            assert len(dash["recommendations"]) > 0
            assert dash["weekly_stats"]["problems_solved"] > 0

            # =============================================
            # Step 10: View progress (gap map)
            # =============================================
            resp = client.get(
                "/api/progress/gap-map", headers=headers
            )
            assert resp.status_code == 200
            gap = resp.json()
            assert len(gap["entries"]) == 19

            # Filter by task_number
            resp = client.get(
                "/api/progress/gap-map?task_number=6", headers=headers
            )
            assert resp.status_code == 200
            gap_filtered = resp.json()
            assert len(gap_filtered["entries"]) == 1
            assert gap_filtered["entries"][0]["task_number"] == 6
            assert gap_filtered["entries"][0]["strength"] > 0

            # =============================================
            # Step 11: View activity calendar
            # =============================================
            resp = client.get(
                "/api/progress/activity-calendar", headers=headers
            )
            assert resp.status_code == 200
            cal = resp.json()
            assert cal["current_streak"] >= 1

            # =============================================
            # Step 12: View exam readiness
            # =============================================
            resp = client.get(
                "/api/progress/exam-readiness", headers=headers
            )
            assert resp.status_code == 200
            readiness = resp.json()
            assert readiness["exam_countdown"] is not None
            assert readiness["readiness_percent"] >= 0
            assert len(readiness["priority_topics"]) > 0
            assert readiness["summary"] != ""

            # =============================================
            # Step 13: View user stats
            # =============================================
            resp = client.get("/api/users/me/stats", headers=headers)
            assert resp.status_code == 200
            stats = resp.json()
            assert stats["current_xp"] > 0
            assert stats["total_problems_solved"] > 0

            # =============================================
            # Step 14: Logout
            # =============================================
            resp = client.post("/auth/logout", headers=headers)
            assert resp.status_code == 200

            # =============================================
            # Verify data integrity
            # =============================================
            # User has accumulated XP from FIRe + problems + SRS
            assert user_row["current_xp"] > 100

            # Attempts were recorded
            attempts = fake.tables["user_problem_attempts"]
            assert len(attempts) >= 6  # 5 problems + 1 SRS review

            # Daily activity was recorded
            activity = fake.tables["user_daily_activity"]
            assert len(activity) >= 1

            # Topic progress was created
            progress = [
                p for p in fake.tables["user_topic_progress"]
                if p.get("topic_id") == "topic-6"
            ]
            assert len(progress) >= 1
