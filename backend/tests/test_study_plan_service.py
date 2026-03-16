"""Tests for study plan generation service."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.services.study_plan_service import (
    _build_weeks,
    _is_mastered,
    _sort_by_roi,
    generate_plan,
    get_current_plan,
    get_required_tasks,
)

# --- get_required_tasks ---


class TestGetRequiredTasks:
    def test_target_70_returns_tasks_1_to_12(self):
        tasks = get_required_tasks(70)
        assert tasks == list(range(1, 13))

    def test_target_80_includes_13_15_16(self):
        tasks = get_required_tasks(80)
        assert 13 in tasks
        assert 15 in tasks
        assert 16 in tasks
        assert 14 not in tasks

    def test_target_90_includes_14_17(self):
        tasks = get_required_tasks(90)
        assert 14 in tasks
        assert 17 in tasks

    def test_target_100_all_19(self):
        tasks = get_required_tasks(100)
        assert tasks == list(range(1, 20))


# --- _is_mastered ---


class TestIsMastered:
    def test_part1_correct_fast(self):
        r = {
            "task_number": 7,
            "is_correct": True,
            "time_spent_seconds": 30,
        }
        assert _is_mastered(r) is True

    def test_part1_correct_slow(self):
        r = {
            "task_number": 7,
            "is_correct": True,
            "time_spent_seconds": 90,
        }
        assert _is_mastered(r) is False

    def test_part1_incorrect(self):
        r = {
            "task_number": 7,
            "is_correct": False,
            "time_spent_seconds": 30,
        }
        assert _is_mastered(r) is False

    def test_part2_level_3(self):
        r = {"task_number": 13, "self_assessment": "level_3"}
        assert _is_mastered(r) is True

    def test_part2_level_2(self):
        r = {"task_number": 13, "self_assessment": "level_2"}
        assert _is_mastered(r) is False

    def test_part2_level_0(self):
        r = {"task_number": 13, "self_assessment": "level_0"}
        assert _is_mastered(r) is False


# --- _sort_by_roi ---


class TestSortByROI:
    def test_part1_roi_order(self):
        tasks = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        result = _sort_by_roi(tasks)
        assert result == [7, 6, 4, 8, 1, 2, 12, 9, 3, 5, 10, 11]

    def test_subset(self):
        tasks = [3, 7, 12]
        result = _sort_by_roi(tasks)
        assert result == [7, 12, 3]

    def test_with_part2_appended(self):
        tasks = [7, 6, 13, 15]
        result = _sort_by_roi(tasks)
        assert result[0] == 7
        assert result[1] == 6
        assert 13 in result[2:]
        assert 15 in result[2:]


# --- _build_weeks ---


class TestBuildWeeks:
    def test_single_task_fits_in_one_day(self):
        weeks = _build_weeks(
            [1], days_remaining=7, hours_per_day=3.0,
        )
        assert len(weeks) == 1
        day1 = weeks[0]["days"][0]
        assert len(day1["study"]) > 0
        assert day1["study"][0]["task_number"] == 1

    def test_review_minutes_allocated(self):
        weeks = _build_weeks(
            [1], days_remaining=1, hours_per_day=2.0,
        )
        day = weeks[0]["days"][0]
        assert day["review_minutes"] == int(2.0 * 60 * 0.30)

    def test_multiple_weeks(self):
        weeks = _build_weeks(
            list(range(1, 13)),
            days_remaining=30,
            hours_per_day=1.5,
        )
        assert len(weeks) >= 4

    def test_empty_tasks(self):
        weeks = _build_weeks(
            [], days_remaining=7, hours_per_day=1.0,
        )
        assert len(weeks) == 1
        assert weeks[0]["days"][0]["study"] == []

    def test_task_spans_multiple_days(self):
        weeks = _build_weeks(
            [13], days_remaining=14, hours_per_day=1.0,
        )
        days_with_13 = sum(
            1
            for w in weeks
            for d in w["days"]
            if any(s["task_number"] == 13 for s in d["study"])
        )
        assert days_with_13 > 1


# --- generate_plan ---


def _diag_row(tn, correct=False, sa=None, time=60):
    """Build a diagnostic result dict."""
    return {
        "task_number": tn,
        "is_correct": correct,
        "self_assessment": sa,
        "time_spent_seconds": time,
    }


def _mock_client(diagnostic_data=None):
    """Create a mock Supabase client for plan generation."""
    client = MagicMock()

    diag_result = MagicMock()
    diag_result.data = diagnostic_data or []
    chain = client.table.return_value.select.return_value
    chain.eq.return_value.execute.return_value = diag_result

    upd = client.table.return_value.update.return_value
    upd.eq.return_value.eq.return_value.execute.return_value = (
        MagicMock()
    )
    ins = client.table.return_value.insert.return_value
    ins.execute.return_value = MagicMock()

    return client


class TestGeneratePlan:
    def test_target_70_60_days(self):
        diag = [_diag_row(tn) for tn in range(1, 20)]
        client = _mock_client(diag)
        result = generate_plan(
            client, "user-1", 70, "2026-05-15", 1.5,
        )
        plan = result["plan_data"]
        assert plan["target_score"] == 70
        assert len(plan["tasks_to_study"]) == 12
        assert plan["mastered_tasks"] == []
        assert plan["weeks"]

    def test_target_80_includes_part2(self):
        diag = [
            _diag_row(tn, sa="level_1") for tn in range(1, 20)
        ]
        client = _mock_client(diag)
        result = generate_plan(
            client, "user-1", 80, "2026-05-15", 1.5,
        )
        plan = result["plan_data"]
        assert 13 in plan["tasks_to_study"]
        assert 15 in plan["tasks_to_study"]
        assert 16 in plan["tasks_to_study"]

    def test_mastered_tasks_skipped(self):
        diag = [
            _diag_row(7, correct=True, time=30),
            _diag_row(6, correct=True, time=20),
            _diag_row(4, correct=True, time=45),
            *[
                _diag_row(tn)
                for tn in range(1, 13)
                if tn not in (7, 6, 4)
            ],
            *[
                _diag_row(tn, sa="level_1")
                for tn in range(13, 20)
            ],
        ]
        client = _mock_client(diag)
        result = generate_plan(
            client, "user-1", 70, "2026-05-15", 1.5,
        )
        plan = result["plan_data"]
        assert 7 not in plan["tasks_to_study"]
        assert 6 not in plan["tasks_to_study"]
        assert 4 not in plan["tasks_to_study"]
        assert sorted(plan["mastered_tasks"]) == [4, 6, 7]

    def test_warning_insufficient_time(self):
        diag = [
            _diag_row(tn, sa="level_0")
            for tn in range(1, 20)
        ]
        client = _mock_client(diag)
        result = generate_plan(
            client, "user-1", 70, "2026-03-26", 0.5,
        )
        plan = result["plan_data"]
        assert plan["warning"] is not None
        assert "Недостаточно" in plan["warning"]

    def test_no_warning_sufficient_time(self):
        diag = [
            _diag_row(tn, correct=True, sa="level_3", time=20)
            for tn in range(1, 20)
        ]
        client = _mock_client(diag)
        result = generate_plan(
            client, "user-1", 70, "2026-06-15", 2.0,
        )
        plan = result["plan_data"]
        assert plan["warning"] is None
        assert plan["tasks_to_study"] == []

    def test_roi_ordering_in_plan(self):
        diag = [_diag_row(tn) for tn in range(1, 20)]
        client = _mock_client(diag)
        result = generate_plan(
            client, "user-1", 70, "2026-06-15", 2.0,
        )
        plan = result["plan_data"]
        assert plan["tasks_to_study"][0] == 7
        assert plan["tasks_to_study"][1] == 6

    def test_7030_split(self):
        diag = [_diag_row(tn) for tn in range(1, 20)]
        client = _mock_client(diag)
        result = generate_plan(
            client, "user-1", 70, "2026-05-15", 2.0,
        )
        plan = result["plan_data"]
        total = plan["total_hours"]
        assert plan["study_hours"] == pytest.approx(
            total * 0.70, abs=0.1,
        )
        assert plan["review_hours"] == pytest.approx(
            total * 0.30, abs=0.1,
        )

    def test_plan_persisted(self):
        diag = [_diag_row(tn) for tn in range(1, 20)]
        client = _mock_client(diag)
        result = generate_plan(
            client, "user-1", 70, "2026-05-15", 1.0,
        )
        assert result["is_active"] is True
        assert result["id"]
        client.table.assert_any_call("user_study_plan")

    def test_plan_broken_into_weeks(self):
        diag = [_diag_row(tn) for tn in range(1, 20)]
        client = _mock_client(diag)
        result = generate_plan(
            client, "user-1", 70, "2026-05-15", 1.5,
        )
        plan = result["plan_data"]
        weeks = plan["weeks"]
        assert len(weeks) > 0
        first_week = weeks[0]
        assert "days" in first_week
        assert len(first_week["days"]) <= 7
        day = first_week["days"][0]
        assert "study" in day
        assert "review_minutes" in day


# --- get_current_plan ---


class TestGetCurrentPlan:
    def test_returns_plan(self):
        client = MagicMock()
        plan_row = {
            "id": "plan-1",
            "user_id": "user-1",
            "is_active": True,
            "plan_data": {},
        }
        result_mock = MagicMock()
        result_mock.data = [plan_row]
        chain = (
            client.table.return_value.select.return_value
            .eq.return_value.eq.return_value
            .order.return_value.limit.return_value
        )
        chain.execute.return_value = result_mock
        assert get_current_plan(client, "user-1") == plan_row

    def test_returns_none_when_no_plan(self):
        client = MagicMock()
        result_mock = MagicMock()
        result_mock.data = []
        chain = (
            client.table.return_value.select.return_value
            .eq.return_value.eq.return_value
            .order.return_value.limit.return_value
        )
        chain.execute.return_value = result_mock
        assert get_current_plan(client, "user-1") is None
