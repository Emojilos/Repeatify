"""Progress endpoints: activity calendar (heatmap data)."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.db.supabase_client import get_supabase_client
from app.models.progress import ActivityCalendarResponse, DailyActivity

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/activity-calendar", response_model=ActivityCalendarResponse)
async def activity_calendar(
    user: dict = Depends(get_current_user),
) -> ActivityCalendarResponse:
    """Return daily activity for the last 365 days (heatmap data)."""
    client = get_supabase_client()

    since = (date.today() - timedelta(days=365)).isoformat()

    result = (
        client.table("user_daily_activity")
        .select("activity_date,sessions_completed,problems_solved,xp_earned,streak_maintained")
        .eq("user_id", user["id"])
        .gte("activity_date", since)
        .order("activity_date")
        .execute()
    )

    activities = [
        DailyActivity(
            date=row["activity_date"],
            sessions_completed=row.get("sessions_completed", 0),
            problems_solved=row.get("problems_solved", 0),
            xp_earned=row.get("xp_earned", 0),
            streak_maintained=row.get("streak_maintained", False),
        )
        for row in (result.data or [])
    ]

    # Fetch current streak info from users table
    user_result = (
        client.table("users")
        .select("current_streak,longest_streak")
        .eq("id", user["id"])
        .maybe_single()
        .execute()
    )
    streak_data = user_result.data or {}

    return ActivityCalendarResponse(
        activities=activities,
        current_streak=streak_data.get("current_streak", 0),
        longest_streak=streak_data.get("longest_streak", 0),
    )
