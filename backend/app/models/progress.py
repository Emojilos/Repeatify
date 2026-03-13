"""Models for progress and activity endpoints."""

from pydantic import BaseModel


class DailyActivity(BaseModel):
    date: str
    sessions_completed: int = 0
    problems_solved: int = 0
    xp_earned: int = 0
    streak_maintained: bool = False


class ActivityCalendarResponse(BaseModel):
    activities: list[DailyActivity]
    current_streak: int = 0
    longest_streak: int = 0
