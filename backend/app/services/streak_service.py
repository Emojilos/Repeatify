"""Daily activity tracking and streak management.

Records user activity per day in ``user_daily_activity`` and keeps
``users.current_streak`` / ``users.longest_streak`` up to date.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta


def record_activity(
    client,
    user_id: str,
    *,
    problems_solved: int = 0,
    sessions_completed: int = 0,
    xp_earned: int = 0,
    today: date | None = None,
) -> dict:
    """Record or update today's activity row and refresh the user streak.

    Returns the (possibly updated) ``user_daily_activity`` row as a dict.
    """
    today = today or date.today()
    today_str = today.isoformat()

    # Upsert daily activity row
    existing = (
        client.table("user_daily_activity")
        .select("*")
        .eq("user_id", user_id)
        .eq("activity_date", today_str)
        .maybe_single()
        .execute()
    )

    if existing.data:
        row = existing.data
        old_sessions = row.get("sessions_completed") or 0
        client.table("user_daily_activity").update({
            "problems_solved": (row.get("problems_solved") or 0) + problems_solved,
            "sessions_completed": old_sessions + sessions_completed,
            "xp_earned": (row.get("xp_earned") or 0) + xp_earned,
            "streak_maintained": True,
        }).eq("id", row["id"]).execute()
        # Row already existed → streak was already counted for today
        return row
    else:
        row_id = str(uuid.uuid4())
        new_row = {
            "id": row_id,
            "user_id": user_id,
            "activity_date": today_str,
            "problems_solved": problems_solved,
            "sessions_completed": sessions_completed,
            "xp_earned": xp_earned,
            "streak_maintained": True,
        }
        client.table("user_daily_activity").insert(new_row).execute()
        # First activity today → update streak
        _update_streak(client, user_id, today)
        return new_row


def _update_streak(client, user_id: str, today: date) -> None:
    """Recalculate ``current_streak`` based on yesterday's activity."""
    yesterday_str = (today - timedelta(days=1)).isoformat()

    yesterday_row = (
        client.table("user_daily_activity")
        .select("id")
        .eq("user_id", user_id)
        .eq("activity_date", yesterday_str)
        .maybe_single()
        .execute()
    )

    # Fetch current user streak info
    user_result = (
        client.table("users")
        .select("current_streak,longest_streak")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    if not user_result.data:
        return

    old_streak = user_result.data.get("current_streak") or 0
    longest = user_result.data.get("longest_streak") or 0

    if yesterday_row.data:
        # Continuing a streak
        new_streak = old_streak + 1
    else:
        # No activity yesterday → streak resets to 1 (today counts)
        new_streak = 1

    new_longest = max(longest, new_streak)

    update_data: dict = {
        "current_streak": new_streak,
        "last_activity_date": today.isoformat(),
    }
    if new_longest != longest:
        update_data["longest_streak"] = new_longest

    client.table("users").update(update_data).eq("id", user_id).execute()
