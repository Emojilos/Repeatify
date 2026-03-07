"""Streak service: record daily activity and maintain streak counters."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from supabase import Client


def record_activity(
    sb: Client,
    user_id: str,
    activity_date: date,
    cards_reviewed: int,
    minutes_studied: float = 0.0,
) -> dict[str, Any]:
    """Record a user's daily activity and update streak counters.

    A day is counted toward the streak when ``cards_reviewed`` is at least
    50% of the user's daily card target (derived from ``daily_goal_minutes``
    at a rate of 2 cards per minute).

    Args:
        sb: Supabase service-role client.
        user_id: Authenticated user UUID.
        activity_date: The local calendar date for this activity.
        cards_reviewed: Number of cards reviewed in this activity batch.
        minutes_studied: Time studied in minutes (optional, for heatmap).

    Returns:
        Dict with: goal_reached, current_streak, longest_streak.
    """
    # ------------------------------------------------------------------
    # 1. Fetch user profile (daily_goal_minutes, longest_streak)
    # ------------------------------------------------------------------
    user_resp = (
        sb.table("users")
        .select("daily_goal_minutes, current_streak, longest_streak")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    user_row: dict[str, Any] = user_resp.data or {}
    daily_goal_minutes: int = user_row.get("daily_goal_minutes") or 30
    prev_longest: int = user_row.get("longest_streak") or 0

    # Daily card goal = 2 cards/minute; 50% threshold for streak credit
    daily_card_goal = max(1, daily_goal_minutes * 2)
    goal_reached = cards_reviewed >= daily_card_goal // 2

    # ------------------------------------------------------------------
    # 2. Upsert daily_activity row (merge on conflict)
    # ------------------------------------------------------------------
    date_str = activity_date.isoformat()
    existing_resp = (
        sb.table("daily_activity")
        .select("id, cards_reviewed, minutes_studied")
        .eq("user_id", user_id)
        .eq("activity_date", date_str)
        .maybe_single()
        .execute()
    )
    existing = existing_resp.data

    if existing:
        merged_cards = (existing.get("cards_reviewed") or 0) + cards_reviewed
        merged_minutes = float(existing.get("minutes_studied") or 0) + minutes_studied
        merged_goal = merged_cards >= daily_card_goal // 2
        sb.table("daily_activity").update(
            {
                "cards_reviewed": merged_cards,
                "minutes_studied": merged_minutes,
                "goal_reached": merged_goal,
            }
        ).eq("id", existing["id"]).execute()
        goal_reached = merged_goal
    else:
        sb.table("daily_activity").insert(
            {
                "user_id": user_id,
                "activity_date": date_str,
                "cards_reviewed": cards_reviewed,
                "minutes_studied": minutes_studied,
                "goal_reached": goal_reached,
            }
        ).execute()

    # ------------------------------------------------------------------
    # 3. Fetch all goal_reached days for this user to compute streak
    # ------------------------------------------------------------------
    rows_resp = (
        sb.table("daily_activity")
        .select("activity_date, goal_reached")
        .eq("user_id", user_id)
        .eq("goal_reached", True)
        .order("activity_date", desc=True)
        .execute()
    )
    goal_dates: set[date] = set()
    for row in rows_resp.data or []:
        raw = row.get("activity_date")
        if raw:
            goal_dates.add(_parse_date(raw))

    # ------------------------------------------------------------------
    # 4. Compute current streak (consecutive days ending at activity_date)
    # ------------------------------------------------------------------
    current_streak = _compute_streak(goal_dates, activity_date)

    # ------------------------------------------------------------------
    # 5. Update users counters
    # ------------------------------------------------------------------
    new_longest = max(prev_longest, current_streak)
    sb.table("users").update(
        {
            "current_streak": current_streak,
            "longest_streak": new_longest,
        }
    ).eq("id", user_id).execute()

    return {
        "goal_reached": goal_reached,
        "current_streak": current_streak,
        "longest_streak": new_longest,
    }


def reset_streak_if_missed(
    sb: Client,
    user_id: str,
    today: date,
) -> int:
    """Check if a day was missed and reset streak accordingly.

    Call this at the start of a new session to detect gap days.

    Args:
        sb: Supabase service-role client.
        user_id: Authenticated user UUID.
        today: Today's local calendar date.

    Returns:
        The updated current_streak value (0 if missed, unchanged otherwise).
    """
    yesterday = today - timedelta(days=1)

    # Fetch the most recent goal_reached day
    rows_resp = (
        sb.table("daily_activity")
        .select("activity_date, goal_reached")
        .eq("user_id", user_id)
        .eq("goal_reached", True)
        .order("activity_date", desc=True)
        .limit(1)
        .execute()
    )
    rows = rows_resp.data or []

    if not rows:
        # No activity at all — streak is already 0
        return 0

    last_date = _parse_date(rows[0]["activity_date"])
    if last_date >= yesterday:
        # Streak still alive (activity yesterday or today)
        return _fetch_current_streak(sb, user_id)

    # Gap detected — reset streak
    sb.table("users").update({"current_streak": 0}).eq("id", user_id).execute()
    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compute_streak(goal_dates: set[date], anchor: date) -> int:
    """Count consecutive days with goal_reached, ending at ``anchor``.

    Walks backwards from ``anchor`` until a missing day is found.
    """
    streak = 0
    cursor = anchor
    while cursor in goal_dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _parse_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    # ISO format "YYYY-MM-DD" (may include time component)
    return date.fromisoformat(str(value)[:10])


def _fetch_current_streak(sb: Client, user_id: str) -> int:
    resp = (
        sb.table("users")
        .select("current_streak")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    return (resp.data or {}).get("current_streak") or 0
