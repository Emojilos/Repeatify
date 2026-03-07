"""Unit tests for study plan planner and service."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from app.core.study_plan.planner import (
    NEW_CARDS_LIMIT,
    SPRINT_PRIORITY_TASKS,
    determine_mode,
    new_cards_limit,
)
from app.services.study_plan_service import StudyPlan, _parse_date, get_study_plan


# ---------------------------------------------------------------------------
# determine_mode — boundary value tests
# ---------------------------------------------------------------------------


class TestDetermineMode:
    def test_270_days_relaxed(self):
        assert determine_mode(270) == "relaxed"

    def test_181_days_relaxed(self):
        assert determine_mode(181) == "relaxed"

    def test_180_days_standard(self):
        assert determine_mode(180) == "standard"

    def test_150_days_standard(self):
        assert determine_mode(150) == "standard"

    def test_61_days_standard(self):
        assert determine_mode(61) == "standard"

    def test_60_days_intensive(self):
        assert determine_mode(60) == "intensive"

    def test_21_days_intensive(self):
        assert determine_mode(21) == "intensive"

    def test_20_days_sprint(self):
        assert determine_mode(20) == "sprint"

    def test_10_days_sprint(self):
        assert determine_mode(10) == "sprint"

    def test_0_days_sprint(self):
        assert determine_mode(0) == "sprint"


# ---------------------------------------------------------------------------
# new_cards_limit
# ---------------------------------------------------------------------------


class TestNewCardsLimit:
    def test_sprint_limit(self):
        assert new_cards_limit("sprint") == NEW_CARDS_LIMIT["sprint"]

    def test_intensive_limit(self):
        assert new_cards_limit("intensive") == NEW_CARDS_LIMIT["intensive"]

    def test_standard_limit(self):
        assert new_cards_limit("standard") == NEW_CARDS_LIMIT["standard"]

    def test_relaxed_limit(self):
        assert new_cards_limit("relaxed") == NEW_CARDS_LIMIT["relaxed"]

    def test_sprint_limit_less_than_intensive(self):
        assert new_cards_limit("sprint") < new_cards_limit("intensive")

    def test_intensive_less_than_standard(self):
        assert new_cards_limit("intensive") < new_cards_limit("standard")


# ---------------------------------------------------------------------------
# SPRINT_PRIORITY_TASKS
# ---------------------------------------------------------------------------


class TestSprintPriorityTasks:
    def test_contains_tasks_1_to_12(self):
        assert SPRINT_PRIORITY_TASKS == set(range(1, 13))

    def test_task_13_not_priority(self):
        assert 13 not in SPRINT_PRIORITY_TASKS


# ---------------------------------------------------------------------------
# _parse_date helper
# ---------------------------------------------------------------------------


class TestParseDate:
    def test_iso_string(self):
        assert _parse_date("2026-06-01") == date(2026, 6, 1)

    def test_datetime_string(self):
        assert _parse_date("2026-06-01T00:00:00") == date(2026, 6, 1)

    def test_date_object_passthrough(self):
        d = date(2026, 6, 1)
        assert _parse_date(d) == d


# ---------------------------------------------------------------------------
# get_study_plan service
# ---------------------------------------------------------------------------


def _make_supabase_mock(exam_date_str: str | None = None) -> MagicMock:
    """Return a mock Supabase client that returns the given exam_date."""
    sb = MagicMock()
    user_data = {"exam_date": exam_date_str, "daily_goal_minutes": 30} if exam_date_str else {}
    (
        sb.table.return_value
        .select.return_value
        .eq.return_value
        .maybe_single.return_value
        .execute.return_value
    ) = MagicMock(data=user_data if exam_date_str else None)
    # update chain (for persisting study_plan_type)
    (
        sb.table.return_value
        .update.return_value
        .eq.return_value
        .execute.return_value
    ) = MagicMock(data=None)
    return sb


class TestGetStudyPlan:
    def test_no_exam_date_returns_relaxed(self):
        sb = MagicMock()
        (
            sb.table.return_value
            .select.return_value
            .eq.return_value
            .maybe_single.return_value
            .execute.return_value
        ) = MagicMock(data=None)

        plan = get_study_plan(sb, "user-123")

        assert plan.mode == "relaxed"
        assert plan.exam_date is None
        assert plan.days_until_exam == 9999

    def test_sprint_mode_for_near_exam(self):
        exam_date = (date.today() + timedelta(days=10)).isoformat()
        sb = _make_supabase_mock(exam_date)

        plan = get_study_plan(sb, "user-123")

        assert plan.mode == "sprint"
        assert plan.days_until_exam == 10
        assert plan.new_cards_limit == NEW_CARDS_LIMIT["sprint"]

    def test_intensive_mode(self):
        exam_date = (date.today() + timedelta(days=45)).isoformat()
        sb = _make_supabase_mock(exam_date)

        plan = get_study_plan(sb, "user-123")

        assert plan.mode == "intensive"

    def test_standard_mode(self):
        exam_date = (date.today() + timedelta(days=120)).isoformat()
        sb = _make_supabase_mock(exam_date)

        plan = get_study_plan(sb, "user-123")

        assert plan.mode == "standard"

    def test_relaxed_mode(self):
        exam_date = (date.today() + timedelta(days=200)).isoformat()
        sb = _make_supabase_mock(exam_date)

        plan = get_study_plan(sb, "user-123")

        assert plan.mode == "relaxed"

    def test_returns_study_plan_dataclass(self):
        exam_date = (date.today() + timedelta(days=30)).isoformat()
        sb = _make_supabase_mock(exam_date)

        plan = get_study_plan(sb, "user-123")

        assert isinstance(plan, StudyPlan)
        assert plan.exam_date is not None
