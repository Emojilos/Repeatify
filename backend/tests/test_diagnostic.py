"""Tests for diagnostic test endpoints and service."""

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


def _make_problems(
    task_numbers: list[int] | None = None,
) -> list[dict]:
    """Generate mock problems for task_numbers 1-19."""
    if task_numbers is None:
        task_numbers = list(range(1, 20))
    return [
        {
            "id": f"prob-{tn}",
            "task_number": tn,
            "problem_text": f"Problem for task {tn}",
            "problem_images": None,
            "difficulty": "medium",
        }
        for tn in task_numbers
    ]


def _result_item(
    tn: int,
    is_correct: bool | None = None,
    self_assessment: str | None = None,
    time_spent: int = 60,
) -> dict:
    return {
        "task_number": tn,
        "is_correct": is_correct,
        "self_assessment": self_assessment,
        "time_spent_seconds": time_spent,
    }


# --- Service unit tests ---


class TestDiagnosticService:
    def test_check_answer_correct_exact(self):
        from app.services.diagnostic_service import (
            check_diagnostic_answer,
        )

        assert check_diagnostic_answer("42", "42") is True

    def test_check_answer_correct_case_insensitive(self):
        from app.services.diagnostic_service import (
            check_diagnostic_answer,
        )

        assert check_diagnostic_answer("Answer", "answer") is True

    def test_check_answer_incorrect(self):
        from app.services.diagnostic_service import (
            check_diagnostic_answer,
        )

        assert check_diagnostic_answer("99", "42") is False

    def test_check_answer_no_correct_answer(self):
        from app.services.diagnostic_service import (
            check_diagnostic_answer,
        )

        assert check_diagnostic_answer("42", None) is None
        assert check_diagnostic_answer("42", "") is None

    def test_check_answer_no_user_answer(self):
        from app.services.diagnostic_service import (
            check_diagnostic_answer,
        )

        assert check_diagnostic_answer(None, "42") is False
        assert check_diagnostic_answer("", "42") is False

    def test_check_answer_with_tolerance(self):
        from app.services.diagnostic_service import (
            check_diagnostic_answer,
        )

        result_close = check_diagnostic_answer(
            "3.14", "3.15", tolerance=0.02,
        )
        assert result_close is True
        result_far = check_diagnostic_answer(
            "3.14", "3.20", tolerance=0.02,
        )
        assert result_far is False

    def test_select_problems_picks_one_per_task(self):
        from app.services.diagnostic_service import (
            select_problems_for_diagnostic,
        )

        mock_client = MagicMock()
        (
            mock_client.table.return_value
            .select.return_value
            .order.return_value
            .execute.return_value
        ) = MagicMock(data=_make_problems())

        result = select_problems_for_diagnostic(
            mock_client, "user-1",
        )
        assert len(result) == 19
        task_numbers = [p["task_number"] for p in result]
        assert sorted(task_numbers) == list(range(1, 20))

    def test_select_problems_prefers_medium(self):
        from app.services.diagnostic_service import (
            select_problems_for_diagnostic,
        )

        problems = [
            {
                "id": "easy-1",
                "task_number": 1,
                "problem_text": "Easy",
                "problem_images": None,
                "difficulty": "basic",
            },
            {
                "id": "med-1",
                "task_number": 1,
                "problem_text": "Medium",
                "problem_images": None,
                "difficulty": "medium",
            },
            {
                "id": "hard-1",
                "task_number": 1,
                "problem_text": "Hard",
                "problem_images": None,
                "difficulty": "hard",
            },
        ]

        mock_client = MagicMock()
        (
            mock_client.table.return_value
            .select.return_value
            .order.return_value
            .execute.return_value
        ) = MagicMock(data=problems)

        # Run multiple times — should always pick medium
        for _ in range(10):
            result = select_problems_for_diagnostic(
                mock_client, "user-1",
            )
            assert len(result) == 1
            assert result[0]["problem_id"] == "med-1"

    def test_has_existing_diagnostic_true(self):
        from app.services.diagnostic_service import (
            has_existing_diagnostic,
        )

        mock_client = MagicMock()
        (
            mock_client.table.return_value
            .select.return_value
            .eq.return_value
            .execute.return_value
        ) = MagicMock(data=[{"id": "diag-1"}])

        assert has_existing_diagnostic(mock_client, "u1") is True

    def test_has_existing_diagnostic_false(self):
        from app.services.diagnostic_service import (
            has_existing_diagnostic,
        )

        mock_client = MagicMock()
        (
            mock_client.table.return_value
            .select.return_value
            .eq.return_value
            .execute.return_value
        ) = MagicMock(data=[])

        assert has_existing_diagnostic(mock_client, "u1") is False


# --- POST /api/diagnostic/start ---


class TestStartDiagnostic:
    def test_start_returns_19_problems(self, client):
        """Returns exactly 19 problems (one per task)."""
        token = _make_token()

        with (
            patch(
                "app.routers.diagnostic.get_supabase_client",
                return_value=MagicMock(),
            ),
            patch(
                "app.routers.diagnostic.has_existing_diagnostic",
                return_value=False,
            ),
            patch(
                "app.routers.diagnostic"
                ".select_problems_for_diagnostic",
                return_value=[
                    {
                        "problem_id": f"prob-{tn}",
                        "task_number": tn,
                        "problem_text": f"Problem {tn}",
                        "problem_images": None,
                    }
                    for tn in range(1, 20)
                ],
            ),
        ):
            resp = client.post(
                "/api/diagnostic/start",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 19
        assert len(data["problems"]) == 19
        task_nums = [
            p["task_number"] for p in data["problems"]
        ]
        assert sorted(task_nums) == list(range(1, 20))

    def test_start_conflict_if_already_taken(self, client):
        """409 if user already has diagnostic results."""
        token = _make_token()

        with (
            patch(
                "app.routers.diagnostic.get_supabase_client",
                return_value=MagicMock(),
            ),
            patch(
                "app.routers.diagnostic.has_existing_diagnostic",
                return_value=True,
            ),
        ):
            resp = client.post(
                "/api/diagnostic/start",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert resp.status_code == 409

    def test_start_no_auth(self, client):
        """Should require authentication."""
        resp = client.post("/api/diagnostic/start")
        assert resp.status_code in (401, 403)


# --- POST /api/diagnostic/submit ---


def _build_results() -> list[dict]:
    """Build 19 result dicts for mocking grade_and_persist."""
    results = []
    for tn in range(1, 20):
        if tn <= 12:
            results.append(
                _result_item(tn, is_correct=tn <= 6),
            )
        else:
            results.append(
                _result_item(
                    tn,
                    self_assessment="level_2",
                    time_spent=120,
                ),
            )
    return results


class TestSubmitDiagnostic:
    def _make_answers(self) -> list[dict]:
        """Create 19 mock answers."""
        answers = []
        for tn in range(1, 20):
            if tn <= 12:
                answers.append({
                    "task_number": tn,
                    "answer": str(tn * 10),
                    "time_spent_seconds": 60,
                })
            else:
                answers.append({
                    "task_number": tn,
                    "self_assessment": "level_2",
                    "time_spent_seconds": 120,
                })
        return answers

    def test_submit_grades_correctly(self, client):
        """Grades Part 1 and stores Part 2 self_assessment."""
        token = _make_token()
        results = _build_results()

        with (
            patch(
                "app.routers.diagnostic.get_supabase_client",
                return_value=MagicMock(),
            ),
            patch(
                "app.routers.diagnostic.grade_and_persist",
                return_value=results,
            ),
        ):
            resp = client.post(
                "/api/diagnostic/submit",
                json={"answers": self._make_answers()},
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) == 19
        assert data["total_correct"] == 6
        assert data["total_answered"] == 19

    def test_submit_auto_checks_part1(self, client):
        """Part 1 auto-checked against correct_answer."""
        token = _make_token()

        results = []
        for tn in range(1, 20):
            if tn <= 12:
                results.append(
                    _result_item(tn, is_correct=tn == 7),
                )
            else:
                results.append(
                    _result_item(
                        tn,
                        self_assessment="level_2",
                        time_spent=120,
                    ),
                )

        with (
            patch(
                "app.routers.diagnostic.get_supabase_client",
                return_value=MagicMock(),
            ),
            patch(
                "app.routers.diagnostic.grade_and_persist",
                return_value=results,
            ),
        ):
            resp = client.post(
                "/api/diagnostic/submit",
                json={"answers": self._make_answers()},
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_correct"] == 1

    def test_submit_stores_self_assessment_part2(self, client):
        """Part 2 (tasks 13-19) stores self_assessment."""
        token = _make_token()

        results = []
        for tn in range(1, 20):
            if tn <= 12:
                results.append(
                    _result_item(tn, is_correct=True),
                )
            else:
                results.append(
                    _result_item(
                        tn,
                        self_assessment="level_2",
                        time_spent=120,
                    ),
                )

        with (
            patch(
                "app.routers.diagnostic.get_supabase_client",
                return_value=MagicMock(),
            ),
            patch(
                "app.routers.diagnostic.grade_and_persist",
                return_value=results,
            ),
        ):
            resp = client.post(
                "/api/diagnostic/submit",
                json={"answers": self._make_answers()},
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        part2 = [
            r for r in data["results"]
            if r["task_number"] >= 13
        ]
        for r in part2:
            assert r["self_assessment"] == "level_2"
            assert r["is_correct"] is None

    def test_submit_no_auth(self, client):
        """Should require authentication."""
        resp = client.post(
            "/api/diagnostic/submit",
            json={"answers": []},
        )
        assert resp.status_code in (401, 403)

    def test_submit_duplicate_task_numbers(self, client):
        """Duplicate task_numbers -> 422."""
        token = _make_token()

        answers = [
            {
                "task_number": 1,
                "answer": "10",
                "time_spent_seconds": 60,
            }
            for _ in range(19)
        ]

        with patch(
            "app.routers.diagnostic.get_supabase_client",
            return_value=MagicMock(),
        ):
            resp = client.post(
                "/api/diagnostic/submit",
                json={"answers": answers},
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert resp.status_code == 422


# --- POST /api/diagnostic/retake ---


class TestRetakeDiagnostic:
    def test_retake_allows_even_with_existing(self, client):
        """Retake works even if already taken."""
        token = _make_token()

        with (
            patch(
                "app.routers.diagnostic.get_supabase_client",
                return_value=MagicMock(),
            ),
            patch(
                "app.routers.diagnostic"
                ".select_problems_for_diagnostic",
                return_value=[
                    {
                        "problem_id": f"prob-{tn}",
                        "task_number": tn,
                        "problem_text": f"Problem {tn}",
                        "problem_images": None,
                    }
                    for tn in range(1, 20)
                ],
            ),
        ):
            resp = client.post(
                "/api/diagnostic/retake",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 19


# --- GET /api/diagnostic/results ---


class TestGetDiagnosticResults:
    def test_returns_results(self, client):
        """Returns existing diagnostic results."""
        token = _make_token()

        mock_client = MagicMock()
        (
            mock_client.table.return_value
            .select.return_value
            .eq.return_value
            .order.return_value
            .execute.return_value
        ) = MagicMock(data=[
            _result_item(1, is_correct=True, time_spent=30),
            _result_item(
                2, is_correct=False, time_spent=45,
            ),
            _result_item(
                13,
                self_assessment="level_2",
                time_spent=120,
            ),
        ])

        with patch(
            "app.routers.diagnostic.get_supabase_client",
            return_value=mock_client,
        ):
            resp = client.get(
                "/api/diagnostic/results",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) == 3
        assert data["total_correct"] == 1
        assert data["total_answered"] == 3

    def test_no_results_404(self, client):
        """No diagnostic results -> 404."""
        token = _make_token()

        mock_client = MagicMock()
        (
            mock_client.table.return_value
            .select.return_value
            .eq.return_value
            .order.return_value
            .execute.return_value
        ) = MagicMock(data=[])

        with patch(
            "app.routers.diagnostic.get_supabase_client",
            return_value=mock_client,
        ):
            resp = client.get(
                "/api/diagnostic/results",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert resp.status_code == 404

    def test_results_no_auth(self, client):
        """Should require authentication."""
        resp = client.get("/api/diagnostic/results")
        assert resp.status_code in (401, 403)


# --- initialize_fsrs_from_diagnostic ---


class TestInitializeFsrsFromDiagnostic:
    """Tests for FSRS card initialization from diagnostic results (TASK-014)."""

    def test_mapping_part1_correct_fast(self):
        """Part 1, correct < 1 min -> S=30, D=2, state=review."""
        from app.services.diagnostic_service import (
            _diagnostic_to_fsrs_params,
        )

        state, d, s = _diagnostic_to_fsrs_params({
            "task_number": 7,
            "is_correct": True,
            "time_spent_seconds": 30,
        })
        assert state == "review"
        assert d == pytest.approx(2.0)
        assert s == pytest.approx(30.0)

    def test_mapping_part1_correct_slow(self):
        """Part 1, correct >= 1 min -> S=7, D=4, state=review."""
        from app.services.diagnostic_service import (
            _diagnostic_to_fsrs_params,
        )

        state, d, s = _diagnostic_to_fsrs_params({
            "task_number": 3,
            "is_correct": True,
            "time_spent_seconds": 90,
        })
        assert state == "review"
        assert d == pytest.approx(4.0)
        assert s == pytest.approx(7.0)

    def test_mapping_part1_incorrect(self):
        """Part 1, incorrect -> S=1, D=6, state=learning."""
        from app.services.diagnostic_service import (
            _diagnostic_to_fsrs_params,
        )

        state, d, s = _diagnostic_to_fsrs_params({
            "task_number": 5,
            "is_correct": False,
            "time_spent_seconds": 120,
        })
        assert state == "learning"
        assert d == pytest.approx(6.0)
        assert s == pytest.approx(1.0)

    def test_mapping_part2_level_3(self):
        """Part 2, level_3 -> S=14, D=3, state=review."""
        from app.services.diagnostic_service import (
            _diagnostic_to_fsrs_params,
        )

        state, d, s = _diagnostic_to_fsrs_params({
            "task_number": 14,
            "self_assessment": "level_3",
            "time_spent_seconds": 300,
        })
        assert state == "review"
        assert d == pytest.approx(3.0)
        assert s == pytest.approx(14.0)

    def test_mapping_part2_level_2(self):
        """Part 2, level_2 -> S=3, D=5, state=learning."""
        from app.services.diagnostic_service import (
            _diagnostic_to_fsrs_params,
        )

        state, d, s = _diagnostic_to_fsrs_params({
            "task_number": 15,
            "self_assessment": "level_2",
            "time_spent_seconds": 200,
        })
        assert state == "learning"
        assert d == pytest.approx(5.0)
        assert s == pytest.approx(3.0)

    def test_mapping_part2_level_1(self):
        """Part 2, level_1 -> S=1, D=7, state=learning."""
        from app.services.diagnostic_service import (
            _diagnostic_to_fsrs_params,
        )

        state, d, s = _diagnostic_to_fsrs_params({
            "task_number": 16,
            "self_assessment": "level_1",
            "time_spent_seconds": 60,
        })
        assert state == "learning"
        assert d == pytest.approx(7.0)
        assert s == pytest.approx(1.0)

    def test_mapping_part2_level_0(self):
        """Part 2, level_0 -> state=new (needs theory)."""
        from app.services.diagnostic_service import (
            _diagnostic_to_fsrs_params,
        )

        state, d, s = _diagnostic_to_fsrs_params({
            "task_number": 13,
            "self_assessment": "level_0",
            "time_spent_seconds": 10,
        })
        assert state == "new"
        assert d == 0.0
        assert s == 0.0

    def test_initialize_creates_cards_for_prototypes(self):
        """Creates FSRS cards for each prototype linked to task_number."""
        from app.services.diagnostic_service import (
            initialize_fsrs_from_diagnostic,
        )

        mock_client = MagicMock()

        # Mock prototypes: task 7 has 2 prototypes
        protos = [
            {"id": "proto-7a", "task_number": 7},
            {"id": "proto-7b", "task_number": 7},
        ]
        problems = [
            {"id": "prob-7a", "task_number": 7},
        ]

        call_count = 0

        def mock_table(name):
            nonlocal call_count
            m = MagicMock()
            if name == "prototypes":
                (
                    m.select.return_value
                    .order.return_value
                    .execute.return_value
                ) = MagicMock(data=protos)
            elif name == "problems":
                (
                    m.select.return_value
                    .order.return_value
                    .execute.return_value
                ) = MagicMock(data=problems)
            elif name == "fsrs_cards":
                m.insert.return_value.execute.return_value = (
                    MagicMock(data=[])
                )
            return m

        mock_client.table = mock_table

        results = [
            {
                "task_number": 7,
                "is_correct": True,
                "self_assessment": None,
                "time_spent_seconds": 30,
            },
        ]

        cards = initialize_fsrs_from_diagnostic(
            mock_client, "user-1", results,
        )

        # Should create 2 cards (one per prototype)
        assert len(cards) == 2
        # All cards should be concept type (prototype-based)
        assert all(c["card_type"] == "concept" for c in cards)
        # Should have review state (correct < 1 min)
        assert all(c["state"] == "review" for c in cards)
        assert all(c["difficulty"] == 2.0 for c in cards)
        assert all(c["stability"] == 30.0 for c in cards)
        # Prototype IDs assigned
        proto_ids = {c["prototype_id"] for c in cards}
        assert proto_ids == {"proto-7a", "proto-7b"}

    def test_initialize_falls_back_to_problems(self):
        """If no prototypes exist, creates cards for problems."""
        from app.services.diagnostic_service import (
            initialize_fsrs_from_diagnostic,
        )

        mock_client = MagicMock()

        problems = [
            {"id": "prob-3a", "task_number": 3},
            {"id": "prob-3b", "task_number": 3},
        ]

        def mock_table(name):
            m = MagicMock()
            if name == "prototypes":
                (
                    m.select.return_value
                    .order.return_value
                    .execute.return_value
                ) = MagicMock(data=[])  # No prototypes
            elif name == "problems":
                (
                    m.select.return_value
                    .order.return_value
                    .execute.return_value
                ) = MagicMock(data=problems)
            elif name == "fsrs_cards":
                m.insert.return_value.execute.return_value = (
                    MagicMock(data=[])
                )
            return m

        mock_client.table = mock_table

        results = [
            {
                "task_number": 3,
                "is_correct": False,
                "self_assessment": None,
                "time_spent_seconds": 120,
            },
        ]

        cards = initialize_fsrs_from_diagnostic(
            mock_client, "user-1", results,
        )

        assert len(cards) == 2
        assert all(c["card_type"] == "problem" for c in cards)
        assert all(c["state"] == "learning" for c in cards)
        assert all(c["difficulty"] == 6.0 for c in cards)

    def test_initialize_level0_creates_new_state_cards(self):
        """level_0 creates cards with state=new, no last_review."""
        from app.services.diagnostic_service import (
            initialize_fsrs_from_diagnostic,
        )

        mock_client = MagicMock()

        protos = [{"id": "proto-13a", "task_number": 13}]

        def mock_table(name):
            m = MagicMock()
            if name == "prototypes":
                (
                    m.select.return_value
                    .order.return_value
                    .execute.return_value
                ) = MagicMock(data=protos)
            elif name == "problems":
                (
                    m.select.return_value
                    .order.return_value
                    .execute.return_value
                ) = MagicMock(data=[])
            elif name == "fsrs_cards":
                m.insert.return_value.execute.return_value = (
                    MagicMock(data=[])
                )
            return m

        mock_client.table = mock_table

        results = [
            {
                "task_number": 13,
                "is_correct": None,
                "self_assessment": "level_0",
                "time_spent_seconds": 10,
            },
        ]

        cards = initialize_fsrs_from_diagnostic(
            mock_client, "user-1", results,
        )

        assert len(cards) == 1
        assert cards[0]["state"] == "new"
        assert cards[0]["last_review"] is None
        assert cards[0]["difficulty"] == 0.0
        assert cards[0]["stability"] == 0.0

    def test_submit_calls_initialize_fsrs(self, client):
        """POST /api/diagnostic/submit initializes FSRS cards."""
        token = _make_token()
        results = _build_results()

        answers = []
        for tn in range(1, 20):
            if tn <= 12:
                answers.append({
                    "task_number": tn,
                    "answer": str(tn * 10),
                    "time_spent_seconds": 60,
                })
            else:
                answers.append({
                    "task_number": tn,
                    "self_assessment": "level_2",
                    "time_spent_seconds": 120,
                })

        with (
            patch(
                "app.routers.diagnostic.get_supabase_client",
                return_value=MagicMock(),
            ),
            patch(
                "app.routers.diagnostic.grade_and_persist",
                return_value=results,
            ),
            patch(
                "app.routers.diagnostic"
                ".initialize_fsrs_from_diagnostic",
            ) as mock_init,
        ):
            resp = client.post(
                "/api/diagnostic/submit",
                json={"answers": answers},
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        assert resp.status_code == 200
        # Verify initialize_fsrs_from_diagnostic was called
        mock_init.assert_called_once()
        call_args = mock_init.call_args
        assert call_args[0][1] == "user-123"  # user_id
        assert len(call_args[0][2]) == 19  # 19 results

    def test_part1_correct_exactly_60s_is_slow(self):
        """Part 1 correct at exactly 60s -> slow path (S=7, D=4)."""
        from app.services.diagnostic_service import (
            _diagnostic_to_fsrs_params,
        )

        state, d, s = _diagnostic_to_fsrs_params({
            "task_number": 1,
            "is_correct": True,
            "time_spent_seconds": 60,
        })
        assert state == "review"
        assert d == pytest.approx(4.0)
        assert s == pytest.approx(7.0)
