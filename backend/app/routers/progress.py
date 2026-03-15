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
    ExamReadinessResponse,
    GapMapEntry,
    GapMapResponse,
    PriorityTopic,
    TopicProgress,
    WeeklyStats,
)
from app.services.topic_priority_service import (
    TopicInfo,
    UserTopicState,
    calculate_topic_priority,
    estimate_readiness,
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
        .execute()
    )
    streak_data = user_result.data[0] if user_result.data else {}

    return ActivityCalendarResponse(
        activities=activities,
        current_streak=streak_data.get("current_streak", 0),
        longest_streak=streak_data.get("longest_streak", 0),
    )


def _recommend_action(strength: float, error_count: int, fire_completed: bool) -> str:
    """Pick a recommended action based on topic state."""
    if not fire_completed and strength < 0.3:
        return "Пройти FIRe-flow заново"
    if strength < 0.5 or error_count >= 5:
        return "Повторить теорию"
    return "Решить 5 задач"


@router.get("/gap-map", response_model=GapMapResponse)
async def gap_map(
    user: dict = Depends(get_current_user),
    task_number: int | None = None,
    min_strength: float | None = None,
    max_strength: float | None = None,
) -> GapMapResponse:
    """Return gap map: per-topic weakness analysis with recommendations."""
    client = get_supabase_client()
    today = date.today()
    thirty_days_ago = (today - timedelta(days=30)).isoformat()

    # --- All topics ---
    topics_result = (
        client.table("topics")
        .select("id,task_number,title")
        .order("task_number")
        .execute()
    )
    topics_rows = topics_result.data or []

    # --- User topic progress ---
    progress_result = (
        client.table("user_topic_progress")
        .select("topic_id,strength_score,fire_completed_at")
        .eq("user_id", user["id"])
        .execute()
    )
    progress_map: dict[str, dict] = {
        row["topic_id"]: row for row in (progress_result.data or [])
    }

    # --- Error attempts in last 30 days ---
    attempts_result = (
        client.table("user_problem_attempts")
        .select("problem_id,is_correct,created_at")
        .eq("user_id", user["id"])
        .eq("is_correct", False)
        .gte("created_at", thirty_days_ago)
        .execute()
    )
    error_attempts = attempts_result.data or []

    # --- Map problem_id → topic_id via problems table ---
    problem_ids = list({a["problem_id"] for a in error_attempts})
    problem_topic_map: dict[str, str] = {}
    if problem_ids:
        problems_result = (
            client.table("problems")
            .select("id,topic_id")
            .in_("id", problem_ids)
            .execute()
        )
        problem_topic_map = {
            row["id"]: row["topic_id"]
            for row in (problems_result.data or [])
        }

    # Count errors and track last error date per topic
    topic_errors: dict[str, int] = {}
    topic_last_error: dict[str, str] = {}
    for attempt in error_attempts:
        tid = problem_topic_map.get(attempt["problem_id"])
        if tid:
            topic_errors[tid] = topic_errors.get(tid, 0) + 1
            err_date = attempt.get("created_at", "")
            if err_date > topic_last_error.get(tid, ""):
                topic_last_error[tid] = err_date

    # --- Build entries ---
    entries: list[GapMapEntry] = []
    for t in topics_rows:
        tn = t["task_number"]
        tid = t["id"]

        # Apply task_number filter
        if task_number is not None and tn != task_number:
            continue

        prog = progress_map.get(tid, {})
        strength = prog.get("strength_score", 0.0)
        fire_completed = prog.get("fire_completed_at") is not None

        # Apply strength filters
        if min_strength is not None and strength < min_strength:
            continue
        if max_strength is not None and strength > max_strength:
            continue

        error_count = topic_errors.get(tid, 0)
        last_error = topic_last_error.get(tid)
        # Trim to date only if present
        last_error_date = last_error[:10] if last_error else None

        entries.append(
            GapMapEntry(
                task_number=tn,
                topic=t["title"],
                strength=round(strength * 100, 1),
                error_count=error_count,
                last_error_date=last_error_date,
                recommended_action=_recommend_action(
                    strength, error_count, fire_completed
                ),
            )
        )

    # Sort by strength ascending (weakest first)
    entries.sort(key=lambda e: e.strength)

    return GapMapResponse(entries=entries)


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
        .execute()
    )
    user_data = user_result.data[0] if user_result.data else {}

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


def _readiness_summary(readiness: float, exam_days: int | None) -> str:
    """Generate a human-readable readiness summary."""
    if exam_days is not None and exam_days <= 0:
        return "Экзамен уже состоялся или проходит сегодня."

    level = (
        "Отличная подготовка!"
        if readiness >= 80
        else "Хорошая подготовка, но есть над чем поработать."
        if readiness >= 60
        else "Средний уровень — усильте слабые темы."
        if readiness >= 40
        else "Подготовка на начальном этапе — сфокусируйтесь на приоритетных темах."
    )

    if exam_days is not None:
        return f"Готовность {readiness}%. {level} До экзамена {exam_days} дн."
    return f"Готовность {readiness}%. {level}"


@router.get("/exam-readiness", response_model=ExamReadinessResponse)
async def exam_readiness(
    user: dict = Depends(get_current_user),
) -> ExamReadinessResponse:
    """Return exam readiness assessment with top-5 priority topics."""
    client = get_supabase_client()
    today = date.today()

    # --- User data (exam_date) ---
    user_result = (
        client.table("users")
        .select("exam_date")
        .eq("id", user["id"])
        .execute()
    )
    user_data = user_result.data[0] if user_result.data else {}

    exam_countdown: int | None = None
    exam_date_str = user_data.get("exam_date")
    if exam_date_str:
        exam_date_val = date.fromisoformat(str(exam_date_str))
        exam_countdown = (exam_date_val - today).days

    # --- All topics with max_points and estimated_study_hours ---
    topics_result = (
        client.table("topics")
        .select("id,task_number,title,max_points,estimated_study_hours")
        .order("task_number")
        .execute()
    )
    topics_rows = topics_result.data or []

    # --- User progress ---
    progress_result = (
        client.table("user_topic_progress")
        .select("topic_id,strength_score,fire_completed_at")
        .eq("user_id", user["id"])
        .execute()
    )
    progress_map: dict[str, dict] = {
        row["topic_id"]: row for row in (progress_result.data or [])
    }

    # --- Calculate priorities ---
    scored: list[tuple[float, TopicInfo, UserTopicState, dict]] = []
    all_pairs: list[tuple[TopicInfo, UserTopicState]] = []

    for t in topics_rows:
        prog = progress_map.get(t["id"], {})
        topic_info = TopicInfo(
            task_number=t["task_number"],
            title=t["title"],
            max_points=t["max_points"],
            estimated_study_hours=t.get("estimated_study_hours") or 1.0,
        )
        user_state = UserTopicState(
            strength_score=prog.get("strength_score", 0.0),
            fire_completed=prog.get("fire_completed_at") is not None,
        )
        priority = calculate_topic_priority(topic_info, user_state, exam_countdown)
        scored.append((priority, topic_info, user_state, t))
        all_pairs.append((topic_info, user_state))

    # Sort by priority descending, take top 5
    scored.sort(key=lambda x: x[0], reverse=True)
    top5 = scored[:5]

    priority_topics = [
        PriorityTopic(
            task_number=info.task_number,
            title=info.title,
            max_points=info.max_points,
            strength_score=state.strength_score,
            fire_completed=state.fire_completed,
            priority_score=score,
            recommended_action=_recommend_action(
                state.strength_score, 0, state.fire_completed
            ),
        )
        for score, info, state, _ in top5
    ]

    readiness = estimate_readiness(all_pairs)
    summary = _readiness_summary(readiness, exam_countdown)

    return ExamReadinessResponse(
        readiness_percent=readiness,
        exam_countdown=exam_countdown,
        priority_topics=priority_topics,
        summary=summary,
    )
