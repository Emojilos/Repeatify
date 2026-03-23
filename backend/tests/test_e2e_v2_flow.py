"""End-to-end integration test: full v2 user journey.

Covers the complete new-user flow:
  1. Register
  2. Onboarding (PATCH users/me with target_score, hours_per_day, exam_date)
  3. Generate study plan (all tasks start as not_tested)
  4. Task assessment (10 problems)
  5. FSRS session
  6. FSRS review
  7. Predicted score
"""

import os
import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi.testclient import TestClient

JWT_SECRET = "test-jwt-secret"
USER_ID = "e2e-v2-user-001"
EMAIL = "e2e-v2@example.com"


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
        self._order_desc: bool = False
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

    def order(self, col, **kwargs):
        self._order_col = col
        self._order_desc = kwargs.get("desc", False)
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

        # INSERT
        if self._insert_data is not None:
            now_str = datetime.now(timezone.utc).isoformat()
            rows = (
                self._insert_data
                if isinstance(self._insert_data, list)
                else [self._insert_data]
            )
            for row in rows:
                row.setdefault("created_at", now_str)
                row.setdefault("generated_at", now_str)
            table.extend(rows)
            return _FakeResult(rows)

        # UPDATE
        if self._update_data is not None:
            filtered = self._apply_filters(table)
            for row in filtered:
                row.update(self._update_data)
            return _FakeResult(filtered)

        # SELECT
        filtered = self._apply_filters(table)
        if self._order_col:
            filtered.sort(
                key=lambda r: r.get(self._order_col) or "",
                reverse=self._order_desc,
            )
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
    """Stateful in-memory Supabase mock with seed data for v2 flow."""

    def __init__(self):
        self.tables: dict[str, list[dict]] = defaultdict(list)
        self.auth = MagicMock()
        self._seed()

    def table(self, name: str) -> _FakeTableQuery:
        return _FakeTableQuery(self.tables, name)

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

        # Multiple problems per task_number (for assessments)
        for i in range(1, 20):
            for j in range(1, 11):
                self.tables["problems"].append({
                    "id": f"prob-{i}-{j}",
                    "topic_id": f"topic-{i}",
                    "task_number": i,
                    "difficulty": "medium",
                    "problem_text": f"Задача {i}.{j}: найдите значение выражения",
                    "problem_images": None,
                    "correct_answer": str(i * 10 + j),
                    "answer_tolerance": 0.0,
                    "solution_markdown": f"Ответ: {i * 10 + j}.",
                    "hints": [f"Подсказка {i}.{j}"],
                    "source": "ФИПИ",
                })

        # Prototypes (2 per task_number for first 19 tasks)
        for i in range(1, 20):
            for j in range(1, 3):
                self.tables["prototypes"].append({
                    "id": f"proto-{i}-{j}",
                    "task_number": i,
                    "prototype_code": f"{i}.{j}",
                    "title": f"Прототип {i}.{j}",
                    "difficulty_within_task": "medium",
                    "estimated_study_minutes": 30,
                    "theory_markdown": f"# Теория {i}.{j}\n\n$x^2 + 1$",
                    "key_formulas": [f"$a^{i} = b$"],
                    "solution_algorithm": ["Шаг 1: ...", "Шаг 2: ..."],
                    "common_mistakes": ["Ошибка: не учёл знак"],
                    "related_prototypes": [],
                    "order_index": j,
                })

        # User row (pre-seeded, simulating post-registration state)
        self.tables["users"].append({
            "id": USER_ID,
            "display_name": None,
            "exam_date": None,
            "target_score": None,
            "hours_per_day": None,
            "current_xp": 0,
            "current_level": 1,
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
        })


# All modules whose get_supabase_client needs patching
_PATCHED_MODULES = [
    "app.routers.auth",
    "app.routers.users",
    "app.routers.topics",
    "app.routers.problems",
    "app.routers.fsrs",
    "app.routers.theory",
    "app.routers.progress",
    "app.routers.study_plan",
    "app.routers.prototypes",
]


# ---------------------------------------------------------------------------
# The E2E v2 test
# ---------------------------------------------------------------------------


class TestFullV2UserJourney:
    """Full v2 user path: onboarding → plan → assessment → FSRS."""

    def test_full_v2_journey(self, client):  # noqa: C901
        fake = FakeSupabase()
        token = _make_token()
        headers = {"Authorization": f"Bearer {token}"}
        today = date.today()
        exam_date = (today + timedelta(days=90)).isoformat()

        # Auth mocks
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

        from contextlib import ExitStack

        with ExitStack() as stack:
            for mod in _PATCHED_MODULES:
                stack.enter_context(
                    patch(f"{mod}.get_supabase_client", return_value=fake)
                )

            # Reset rate limiter
            from app.core.rate_limit import limiter
            limiter.reset()

            # =============================================
            # Step 1: Registration (verified in test_e2e_flow.py)
            # User row is pre-seeded to simulate post-registration state.
            # =============================================

            # =============================================
            # Step 2: Onboarding — configure profile
            # =============================================
            resp = client.patch(
                "/api/users/me",
                headers=headers,
                json={
                    "target_score": 80,
                    "exam_date": exam_date,
                    "hours_per_day": 1.5,
                },
            )
            assert resp.status_code == 200
            profile = resp.json()
            assert profile["target_score"] == 80
            assert profile["exam_date"] == exam_date
            assert profile["hours_per_day"] == 1.5

            # Verify profile is persisted
            resp = client.get("/api/users/me", headers=headers)
            assert resp.status_code == 200
            me = resp.json()
            assert me["target_score"] == 80
            assert me["has_study_plan"] is False

            # =============================================
            # Step 3: Generate study plan (all tasks not_tested)
            # =============================================
            resp = client.post(
                "/api/study-plan/generate",
                headers=headers,
                json={
                    "target_score": 80,
                },
            )
            assert resp.status_code == 201
            plan = resp.json()
            assert plan["target_score"] == 80
            assert plan["is_active"] is True
            assert plan["plan_data"] is not None

            plan_data = plan["plan_data"]
            # All tasks should start as not_tested
            for task in plan_data["tasks"]:
                assert task["status"] == "not_tested"

            # =============================================
            # Step 4: GET current plan
            # =============================================
            resp = client.get(
                "/api/study-plan/current", headers=headers
            )
            assert resp.status_code == 200
            current_plan = resp.json()
            assert current_plan["is_active"] is True
            assert current_plan["target_score"] == 80

            # Verify has_study_plan is now True
            resp = client.get("/api/users/me", headers=headers)
            assert resp.status_code == 200
            assert resp.json()["has_study_plan"] is True

            # =============================================
            # Step 5: Task assessment (task 1)
            # =============================================
            resp = client.post(
                "/api/study-plan/assess/1", headers=headers
            )
            assert resp.status_code == 200
            assessment = resp.json()
            assert assessment["task_number"] == 1
            assert len(assessment["problems"]) > 0

            # Submit assessment with correct answers
            answers = []
            for prob in assessment["problems"]:
                # Look up correct answer from seed data
                correct = None
                for p in fake.tables["problems"]:
                    if p["id"] == prob["id"]:
                        correct = p["correct_answer"]
                        break
                answers.append({
                    "problem_id": prob["id"],
                    "answer": correct or "0",
                })

            resp = client.post(
                "/api/study-plan/assess/1/submit",
                headers=headers,
                json={"answers": answers},
            )
            assert resp.status_code == 200
            result = resp.json()
            assert result["task_number"] == 1
            assert result["correct_count"] > 0
            assert result["status"] in ("weak", "medium", "good", "mastered")

            # =============================================
            # Step 6: Verify FSRS cards created from assessment
            # =============================================
            fsrs_cards = fake.tables["fsrs_cards"]
            assert len(fsrs_cards) > 0

            # =============================================
            # Step 7: FSRS session
            # =============================================
            # Make some cards due now for the session
            past_str = (
                datetime.now(timezone.utc) - timedelta(days=1)
            ).isoformat()
            for card in fsrs_cards:
                if card["state"] != "new":
                    card["due"] = past_str
                    card["last_review"] = past_str

            resp = client.get(
                "/api/fsrs/session?max_cards=5", headers=headers
            )
            assert resp.status_code == 200
            session = resp.json()
            assert session["total_due"] > 0
            assert len(session["cards"]) > 0
            assert len(session["cards"]) <= 5

            # Cards should have expected fields
            first_card = session["cards"][0]
            assert "id" in first_card
            assert "difficulty" in first_card
            assert "stability" in first_card
            assert "state" in first_card
            assert "retrievability" in first_card

            # =============================================
            # Step 8: FSRS review
            # =============================================
            card_to_review = first_card
            resp = client.post(
                "/api/fsrs/review",
                headers=headers,
                json={
                    "card_id": card_to_review["id"],
                    "rating": 3,  # Good
                    "answer": "",
                    "time_spent_seconds": 30,
                },
            )
            assert resp.status_code == 200
            review = resp.json()
            assert "new_due" in review
            assert "new_difficulty" in review
            assert "new_stability" in review
            assert "new_state" in review
            assert review["xp_earned"] >= 0

            # Card should be updated in fake DB
            reviewed_card = next(
                c for c in fsrs_cards if c["id"] == card_to_review["id"]
            )
            assert reviewed_card["reps"] >= 1

            # =============================================
            # Step 9: Predicted score
            # =============================================
            resp = client.get(
                "/api/progress/predicted-score", headers=headers
            )
            assert resp.status_code == 200
            score = resp.json()
            assert "predicted_primary_score" in score
            assert "predicted_test_score" in score
            assert "breakdown" in score

            # =============================================
            # Verify data integrity
            # =============================================
            user_row = fake.tables["users"][0]
            assert user_row["target_score"] == 80
            assert user_row["hours_per_day"] == 1.5

            # Task assessment persisted
            assessment_rows = fake.tables["task_assessments"]
            assert len(assessment_rows) >= 1

            # Study plan persisted
            plan_rows = [
                p for p in fake.tables["user_study_plan"]
                if p.get("is_active") is True
            ]
            assert len(plan_rows) == 1

            # XP field exists (may be 0 if only concept cards were reviewed)
            assert user_row["current_xp"] >= 0
