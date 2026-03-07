"""Unit tests for streak_service (TASK-019)."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock, call

import pytest

from app.services.streak_service import (
    _compute_streak,
    _parse_date,
    record_activity,
    reset_streak_if_missed,
)


# ---------------------------------------------------------------------------
# _parse_date helper
# ---------------------------------------------------------------------------


def test_parse_date_from_string():
    assert _parse_date("2026-03-07") == date(2026, 3, 7)


def test_parse_date_with_time_component():
    assert _parse_date("2026-03-07T12:00:00") == date(2026, 3, 7)


def test_parse_date_from_date_object():
    d = date(2026, 3, 7)
    assert _parse_date(d) is d


# ---------------------------------------------------------------------------
# _compute_streak helper
# ---------------------------------------------------------------------------


def test_compute_streak_empty():
    assert _compute_streak(set(), date(2026, 3, 7)) == 0


def test_compute_streak_single_day():
    today = date(2026, 3, 7)
    assert _compute_streak({today}, today) == 1


def test_compute_streak_three_consecutive():
    today = date(2026, 3, 7)
    dates = {today, today - timedelta(1), today - timedelta(2)}
    assert _compute_streak(dates, today) == 3


def test_compute_streak_gap_breaks_streak():
    today = date(2026, 3, 7)
    # Gap on day-2
    dates = {today, today - timedelta(1), today - timedelta(3)}
    assert _compute_streak(dates, today) == 2


def test_compute_streak_anchor_not_in_dates():
    today = date(2026, 3, 7)
    yesterday = today - timedelta(1)
    # Today missing → streak = 0 even if yesterday was active
    assert _compute_streak({yesterday}, today) == 0


# ---------------------------------------------------------------------------
# record_activity
# ---------------------------------------------------------------------------


def _make_sb(
    daily_goal_minutes: int = 30,
    current_streak: int = 0,
    longest_streak: int = 0,
    existing_activity: dict | None = None,
    goal_dates: list[str] | None = None,
):
    """Build a MagicMock Supabase client for streak_service tests."""
    sb = MagicMock()

    # users select
    sb.table("users").select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "daily_goal_minutes": daily_goal_minutes,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
    }

    # daily_activity select (existing row check)
    sb.table("daily_activity").select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = (
        existing_activity
    )

    # daily_activity select (goal dates query)
    goal_rows = [{"activity_date": d, "goal_reached": True} for d in (goal_dates or [])]
    sb.table("daily_activity").select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value.data = (
        goal_rows
    )

    return sb


def test_record_activity_first_day_goal_reached():
    """First ever activity that reaches the goal sets streak=1."""
    today = date(2026, 3, 7)
    # goal: 30 min → card target = 60, threshold = 30; pass 35 cards
    sb = _make_sb(daily_goal_minutes=30, goal_dates=["2026-03-07"])

    result = record_activity(sb, "user-1", today, cards_reviewed=35)

    assert result["goal_reached"] is True
    assert result["current_streak"] == 1
    assert result["longest_streak"] == 1


def test_record_activity_below_threshold_no_streak():
    """Cards below 50% threshold → goal_reached=False, streak=0."""
    today = date(2026, 3, 7)
    # goal: 30 min → threshold=30 cards; only 5 reviewed
    sb = _make_sb(daily_goal_minutes=30, goal_dates=[])

    result = record_activity(sb, "user-1", today, cards_reviewed=5)

    assert result["goal_reached"] is False
    assert result["current_streak"] == 0


def test_record_activity_extends_existing_streak():
    """Three consecutive days → streak=3."""
    today = date(2026, 3, 7)
    prior_dates = [
        "2026-03-05",
        "2026-03-06",
        "2026-03-07",
    ]
    sb = _make_sb(daily_goal_minutes=30, longest_streak=2, goal_dates=prior_dates)

    result = record_activity(sb, "user-1", today, cards_reviewed=40)

    assert result["current_streak"] == 3
    assert result["longest_streak"] == 3


def test_record_activity_updates_longest_streak():
    """When current streak exceeds previous longest, longest_streak updates."""
    today = date(2026, 3, 7)
    dates = [f"2026-03-{d:02d}" for d in range(1, 8)]  # 7 consecutive days
    sb = _make_sb(daily_goal_minutes=30, longest_streak=5, goal_dates=dates)

    result = record_activity(sb, "user-1", today, cards_reviewed=50)

    assert result["current_streak"] == 7
    assert result["longest_streak"] == 7


def test_record_activity_merges_existing_row():
    """When a row already exists for the date, cards_reviewed are merged."""
    today = date(2026, 3, 7)
    existing = {"id": "act-uuid-1", "cards_reviewed": 10, "minutes_studied": 5.0}
    sb = _make_sb(daily_goal_minutes=30, existing_activity=existing, goal_dates=["2026-03-07"])

    result = record_activity(sb, "user-1", today, cards_reviewed=25)

    # UPDATE should be called (not INSERT) with merged totals.
    # There are two update calls: daily_activity and users — check any has merged cards.
    all_update_calls = sb.table.return_value.update.call_args_list
    merged_payloads = [c[0][0] for c in all_update_calls if "cards_reviewed" in c[0][0]]
    assert merged_payloads, "Expected an update with cards_reviewed"
    assert merged_payloads[0]["cards_reviewed"] == 35  # 10 + 25


def test_record_activity_inserts_new_row_when_no_existing():
    """No existing row → INSERT into daily_activity."""
    today = date(2026, 3, 7)
    sb = _make_sb(daily_goal_minutes=30, goal_dates=["2026-03-07"])

    record_activity(sb, "user-1", today, cards_reviewed=35, minutes_studied=15.0)

    insert_call = sb.table("daily_activity").insert.call_args
    assert insert_call is not None
    payload = insert_call[0][0]
    assert payload["cards_reviewed"] == 35
    assert payload["minutes_studied"] == 15.0


# ---------------------------------------------------------------------------
# reset_streak_if_missed
# ---------------------------------------------------------------------------


def _make_sb_reset(last_goal_date: str | None, current_streak: int = 5):
    sb = MagicMock()

    goal_rows = (
        [{"activity_date": last_goal_date, "goal_reached": True}]
        if last_goal_date
        else []
    )
    sb.table("daily_activity").select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = (
        goal_rows
    )
    sb.table("users").select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "current_streak": current_streak
    }
    return sb


def test_reset_streak_no_missed_day():
    """Activity yesterday → streak intact, no reset."""
    today = date(2026, 3, 7)
    yesterday = "2026-03-06"
    sb = _make_sb_reset(last_goal_date=yesterday, current_streak=5)

    result = reset_streak_if_missed(sb, "user-1", today)

    # update should NOT have been called (no reset)
    sb.table("users").update.assert_not_called()
    assert result == 5


def test_reset_streak_gap_resets_to_zero():
    """Gap of 2+ days → streak reset to 0."""
    today = date(2026, 3, 7)
    sb = _make_sb_reset(last_goal_date="2026-03-05")

    result = reset_streak_if_missed(sb, "user-1", today)

    sb.table("users").update.assert_called_once_with({"current_streak": 0})
    assert result == 0


def test_reset_streak_no_previous_activity():
    """User with no activity at all → 0 streak."""
    today = date(2026, 3, 7)
    sb = _make_sb_reset(last_goal_date=None)

    result = reset_streak_if_missed(sb, "user-1", today)

    assert result == 0
    sb.table("users").update.assert_not_called()
