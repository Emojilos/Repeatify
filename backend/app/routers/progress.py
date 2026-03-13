"""Progress endpoints: activity calendar, dashboard."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.db.supabase_client import get_supabase_client
from app.models.progress import (
    ActivityCalendarResponse,
    DailyActivity,
    DashboardResponse,
    TopicProgress,
    WeeklyStats,
)

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


def _build_recommendations(
    exam_days: int | None,
    today_review_count: int,
    weekly_stats: WeeklyStats,
    weak_topics: list[TopicProgress],
) -> list[str]:
    """Generate text recommendations based on user state."""
    recs: list[str] = []

    # SRS review reminder
    if today_review_count > 0:
        recs.append(
            f"У вас {today_review_count} карточек на повторение сегодня. "
            "Регулярные повторения — ключ к запоминанию!"
        )

    # Weak topics
    if weak_topics:
        names = ", ".join(t.title for t in weak_topics[:3])
        recs.append(f"Обратите внимание на слабые темы: {names}")

    # Exam urgency
    if exam_days is not None:
        if exam_days <= 14:
            recs.append(
                "До экзамена меньше 2 недель! "
                "Сфокусируйтесь на повторении изученного материала."
            )
        elif exam_days <= 30:
            recs.append(
                "До экзамена меньше месяца. "
                "Уделяйте время ежедневным тренировкам."
            )
        elif exam_days <= 90:
            recs.append(
                "До экзамена ещё есть время. "
                "Старайтесь изучать новые темы и повторять пройденные."
            )

    # Weekly activity
    if weekly_stats.problems_solved == 0:
        recs.append(
            "На этой неделе вы ещё не решали задания. "
            "Попробуйте решить хотя бы 5 задач сегодня!"
        )

    if not recs:
        recs.append("Отличная работа! Продолжайте в том же духе.")

    return recs


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(
    user: dict = Depends(get_current_user),
) -> DashboardResponse:
    """Return aggregated dashboard data: countdown, progress, reviews, stats."""
    client = get_supabase_client()
    today = date.today()

    # --- User data ---
    user_result = (
        client.table("users")
        .select(
            "exam_date,current_xp,current_level,current_streak"
        )
        .eq("id", user["id"])
        .maybe_single()
        .execute()
    )
    user_data = user_result.data or {}

    exam_countdown: int | None = None
    exam_date_str = user_data.get("exam_date")
    if exam_date_str:
        exam_date_val = date.fromisoformat(str(exam_date_str))
        exam_countdown = (exam_date_val - today).days

    # --- Topics + user progress ---
    topics_result = (
        client.table("topics")
        .select("id,task_number,title")
        .order("task_number")
        .execute()
    )
    topics_rows = topics_result.data or []

    progress_result = (
        client.table("user_topic_progress")
        .select("topic_id,strength_score,fire_completed_at")
        .eq("user_id", user["id"])
        .execute()
    )
    progress_map: dict[str, dict] = {
        row["topic_id"]: row for row in (progress_result.data or [])
    }

    topics_progress: list[TopicProgress] = []
    weak_topics: list[TopicProgress] = []
    for t in topics_rows:
        prog = progress_map.get(t["id"], {})
        tp = TopicProgress(
            task_number=t["task_number"],
            title=t["title"],
            strength_score=prog.get("strength_score", 0.0),
            fire_completed=prog.get("fire_completed_at") is not None,
        )
        topics_progress.append(tp)
        if tp.strength_score < 0.5:
            weak_topics.append(tp)

    # --- Today's review count (due SRS cards) ---
    srs_result = (
        client.table("srs_cards")
        .select("id", count="exact")
        .eq("user_id", user["id"])
        .lte("next_review_date", today.isoformat())
        .neq("status", "suspended")
        .execute()
    )
    today_review_count = srs_result.count if srs_result.count is not None else 0

    # --- Weekly stats (last 7 days from user_problem_attempts) ---
    week_ago = (today - timedelta(days=7)).isoformat()
    attempts_result = (
        client.table("user_problem_attempts")
        .select("is_correct")
        .eq("user_id", user["id"])
        .gte("created_at", week_ago)
        .execute()
    )
    attempts_rows = attempts_result.data or []
    weekly_solved = len(attempts_rows)
    weekly_correct = sum(1 for a in attempts_rows if a.get("is_correct"))

    weekly_stats = WeeklyStats(
        problems_solved=weekly_solved,
        problems_correct=weekly_correct,
    )

    # --- Recommendations ---
    recommendations = _build_recommendations(
        exam_days=exam_countdown,
        today_review_count=today_review_count,
        weekly_stats=weekly_stats,
        weak_topics=weak_topics,
    )

    return DashboardResponse(
        exam_countdown=exam_countdown,
        topics_progress=topics_progress,
        today_review_count=today_review_count,
        weekly_stats=weekly_stats,
        recommendations=recommendations,
        current_xp=user_data.get("current_xp", 0),
        current_level=user_data.get("current_level", 1),
        current_streak=user_data.get("current_streak", 0),
    )
