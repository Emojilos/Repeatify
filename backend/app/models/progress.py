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


class TopicProgress(BaseModel):
    task_number: int
    title: str
    strength_score: float = 0.0
    fire_completed: bool = False


class WeeklyStats(BaseModel):
    problems_solved: int = 0
    problems_correct: int = 0


class GapMapEntry(BaseModel):
    task_number: int
    topic: str
    strength: float = 0.0
    error_count: int = 0
    last_error_date: str | None = None
    recommended_action: str


class GapMapResponse(BaseModel):
    entries: list[GapMapEntry]


class DashboardResponse(BaseModel):
    exam_countdown: int | None = None
    topics_progress: list[TopicProgress]
    today_review_count: int = 0
    weekly_stats: WeeklyStats
    recommendations: list[str]
    current_xp: int = 0
    current_level: int = 1
    current_streak: int = 0


class PriorityTopic(BaseModel):
    task_number: int
    title: str
    max_points: int
    strength_score: float = 0.0
    fire_completed: bool = False
    priority_score: float = 0.0
    recommended_action: str


class ExamReadinessResponse(BaseModel):
    readiness_percent: float = 0.0
    exam_countdown: int | None = None
    priority_topics: list[PriorityTopic]
    summary: str
