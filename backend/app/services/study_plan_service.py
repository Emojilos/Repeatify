"""Study plan generation: personalised weekly/daily study schedule.

Implements the algorithm from PRD 6.1:
1. Determine required tasks by target_score
2. Filter out mastered tasks (from diagnostic)
3. Sort by ROI (points / hours)
4. Distribute across days with 70/30 study/review split
5. Warn if insufficient time
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from math import ceil

# ROI order from PRD 2.1 (highest ROI first)
_ROI_ORDER: list[int] = [7, 6, 4, 8, 1, 2, 12, 9, 3, 5, 10, 11]

# Points per task_number (Part 1 = 1pt each, Part 2 varies)
_POINTS: dict[int, int] = {
    1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1,
    7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1,
    13: 2, 14: 2, 15: 2, 16: 2, 17: 2, 18: 4, 19: 4,
}

# Estimated study hours per task_number (defaults)
_DEFAULT_HOURS: dict[int, float] = {
    1: 2, 2: 3, 3: 3, 4: 3, 5: 4, 6: 4,
    7: 3, 8: 3, 9: 4, 10: 5, 11: 5, 12: 3,
    13: 6, 14: 8, 15: 6, 16: 6, 17: 8, 18: 10, 19: 10,
}

# Required tasks per target_score
_REQUIRED_TASKS: dict[int, list[int]] = {
    70: list(range(1, 13)),              # tasks 1-12
    80: list(range(1, 13)) + [13, 15, 16],  # + Part 2 basics
    90: list(range(1, 13)) + [13, 14, 15, 16, 17],  # + geometry/ineq
    100: list(range(1, 20)),             # all 19 tasks
}


def get_required_tasks(target_score: int) -> list[int]:
    """Return list of task_numbers required for the given target_score."""
    return _REQUIRED_TASKS.get(target_score, list(range(1, 13)))


def _is_mastered(diagnostic_result: dict) -> bool:
    """Determine if a task is considered mastered based on diagnostic result.

    Part 1: correct and fast (< 60s).
    Part 2: level_3 (confident solve).
    """
    task_num = diagnostic_result["task_number"]
    if task_num <= 12:
        return (
            diagnostic_result.get("is_correct") is True
            and (diagnostic_result.get("time_spent_seconds") or 60) < 60
        )
    return diagnostic_result.get("self_assessment") == "level_3"


def _sort_by_roi(task_numbers: list[int]) -> list[int]:
    """Sort task_numbers by ROI order (Part 1 from PRD, Part 2 appended)."""
    roi_index = {tn: i for i, tn in enumerate(_ROI_ORDER)}
    # Part 2 tasks not in _ROI_ORDER get appended by task_number
    max_idx = len(_ROI_ORDER)
    return sorted(task_numbers, key=lambda tn: roi_index.get(tn, max_idx + tn))


def generate_plan(
    client,
    user_id: str,
    target_score: int,
    exam_date_str: str,
    hours_per_day: float,
) -> dict:
    """Generate a study plan and save to user_study_plan.

    Returns the plan dict (same shape as plan_data column).
    """
    exam_date_val = date.fromisoformat(exam_date_str)
    today = date.today()
    days_remaining = max((exam_date_val - today).days, 1)

    # 1) Required tasks for target
    required = get_required_tasks(target_score)

    # 2) Filter out mastered (from diagnostic)
    diag_result = (
        client.table("diagnostic_results")
        .select("task_number,is_correct,self_assessment,time_spent_seconds")
        .eq("user_id", user_id)
        .execute()
    )
    diag_rows = diag_result.data or []
    diag_by_task = {r["task_number"]: r for r in diag_rows}

    mastered = {
        tn for tn in required
        if tn in diag_by_task and _is_mastered(diag_by_task[tn])
    }
    tasks_to_study = [tn for tn in required if tn not in mastered]

    # 3) Sort by ROI
    tasks_to_study = _sort_by_roi(tasks_to_study)

    # 4) Time budget
    total_hours = days_remaining * hours_per_day
    study_hours = total_hours * 0.70  # 70% new material
    review_hours = total_hours * 0.30  # 30% review

    # Estimate needed hours
    needed_hours = sum(_DEFAULT_HOURS.get(tn, 4) for tn in tasks_to_study)

    warning = None
    if needed_hours > study_hours and tasks_to_study:
        warning = (
            f"Недостаточно времени: нужно ~{ceil(needed_hours)}ч на новый материал, "
            f"доступно ~{ceil(study_hours)}ч. "
            "Рекомендуем снизить целевой балл или увеличить часы/день."
        )

    # 5) Distribute across weeks/days
    weeks = _build_weeks(
        tasks_to_study,
        days_remaining,
        hours_per_day,
    )

    plan_data = {
        "target_score": target_score,
        "exam_date": exam_date_str,
        "hours_per_day": hours_per_day,
        "days_remaining": days_remaining,
        "total_hours": round(total_hours, 1),
        "study_hours": round(study_hours, 1),
        "review_hours": round(review_hours, 1),
        "tasks_to_study": tasks_to_study,
        "mastered_tasks": sorted(mastered),
        "warning": warning,
        "weeks": weeks,
    }

    # 6) Persist
    plan_id = str(uuid.uuid4())

    # Deactivate existing plans
    client.table("user_study_plan").update(
        {"is_active": False}
    ).eq("user_id", user_id).eq("is_active", True).execute()

    client.table("user_study_plan").insert({
        "id": plan_id,
        "user_id": user_id,
        "target_score": target_score,
        "exam_date": exam_date_str,
        "hours_per_day": hours_per_day,
        "plan_data": plan_data,
        "is_active": True,
    }).execute()

    return {
        "id": plan_id,
        "user_id": user_id,
        "target_score": target_score,
        "exam_date": exam_date_str,
        "hours_per_day": hours_per_day,
        "plan_data": plan_data,
        "is_active": True,
    }


def _build_weeks(
    tasks: list[int],
    days_remaining: int,
    hours_per_day: float,
) -> list[dict]:
    """Distribute tasks across weeks with daily slots.

    Each week has 7 days. Each day allocates 70% study + 30% review.
    Tasks are assigned sequentially until study hours run out.
    """
    study_minutes_per_day = int(hours_per_day * 60 * 0.70)
    review_minutes_per_day = int(hours_per_day * 60 * 0.30)

    num_weeks = max(ceil(days_remaining / 7), 1)
    weeks: list[dict] = []

    task_idx = 0
    remaining_minutes_for_current_task = 0
    all_tasks_distributed = False

    for week_num in range(1, num_weeks + 1):
        days_in_week = min(7, days_remaining - (week_num - 1) * 7)
        if days_in_week <= 0:
            break

        # Stop generating detailed weeks once all tasks are distributed;
        # just add a summary for the review-only phase
        if all_tasks_distributed:
            remaining_days = days_remaining - (week_num - 1) * 7
            remaining_weeks_count = max(ceil(remaining_days / 7), 1)
            weeks.append({
                "week": week_num,
                "label": "review_phase",
                "summary": f"Повторение и закрепление ({remaining_weeks_count} нед.)",
                "review_minutes_per_day": review_minutes_per_day + study_minutes_per_day,
                "weeks_count": remaining_weeks_count,
                "days": [],
            })
            break

        week_days: list[dict] = []
        for day_offset in range(days_in_week):
            total_days = (week_num - 1) * 7 + day_offset
            day_date = (
                date.today() + timedelta(days=total_days)
            ).isoformat()
            study_tasks: list[dict] = []
            budget = study_minutes_per_day

            while budget > 0 and task_idx < len(tasks):
                tn = tasks[task_idx]
                if remaining_minutes_for_current_task <= 0:
                    remaining_minutes_for_current_task = int(
                        _DEFAULT_HOURS.get(tn, 4) * 60
                    )

                allocated = min(budget, remaining_minutes_for_current_task)
                study_tasks.append({
                    "task_number": tn,
                    "minutes": allocated,
                })
                budget -= allocated
                remaining_minutes_for_current_task -= allocated

                if remaining_minutes_for_current_task <= 0:
                    task_idx += 1

            if task_idx >= len(tasks) and remaining_minutes_for_current_task <= 0:
                all_tasks_distributed = True

            week_days.append({
                "date": day_date,
                "study": study_tasks,
                "study_minutes": study_minutes_per_day - budget,
                "review_minutes": review_minutes_per_day,
            })

        weeks.append({
            "week": week_num,
            "days": week_days,
        })

    return weeks


# Primary → test score conversion table (linear interpolation between points)
_SCORE_CONVERSION: list[tuple[int, int]] = [
    (0, 0),
    (5, 27),
    (7, 40),
    (12, 70),
    (18, 82),
    (24, 94),
    (32, 100),
]


def _primary_to_test_score(primary: int) -> int:
    """Convert primary score to test score via linear interpolation."""
    if primary <= 0:
        return 0
    for i in range(1, len(_SCORE_CONVERSION)):
        p1, t1 = _SCORE_CONVERSION[i - 1]
        p2, t2 = _SCORE_CONVERSION[i]
        if primary <= p2:
            ratio = (primary - p1) / (p2 - p1)
            return round(t1 + ratio * (t2 - t1))
    return 100


def predict_score(
    client,
    user_id: str,
    exam_date: date | None = None,
) -> dict:
    """Predict user's score based on FSRS card retrievability.

    For each task_number, fetches all fsrs_cards, computes avg retrievability,
    and considers the task mastered if avg >= 0.8.
    """
    from app.services.fsrs_service import get_retrievability

    # Fetch all user's FSRS cards
    result = (
        client.table("fsrs_cards")
        .select("id,problem_id,prototype_id,state,stability,difficulty,due,last_review")
        .eq("user_id", user_id)
        .execute()
    )
    cards = result.data or []

    # Map cards to task_number via problems and prototypes
    problem_ids = [c["problem_id"] for c in cards if c.get("problem_id")]
    prototype_ids = [c["prototype_id"] for c in cards if c.get("prototype_id")]

    problem_task_map: dict[str, int] = {}
    if problem_ids:
        p_result = (
            client.table("problems")
            .select("id,task_number")
            .in_("id", problem_ids)
            .execute()
        )
        for p in p_result.data or []:
            problem_task_map[p["id"]] = p["task_number"]

    prototype_task_map: dict[str, int] = {}
    if prototype_ids:
        pr_result = (
            client.table("prototypes")
            .select("id,task_number")
            .in_("id", prototype_ids)
            .execute()
        )
        for pr in pr_result.data or []:
            prototype_task_map[pr["id"]] = pr["task_number"]

    # Group retrievabilities by task_number
    task_retrievabilities: dict[int, list[float]] = {}
    for card in cards:
        tn = (
            problem_task_map.get(card.get("problem_id", ""))
            or prototype_task_map.get(card.get("prototype_id", ""))
        )
        if tn is None:
            continue
        r = get_retrievability(card, exam_date)
        task_retrievabilities.setdefault(tn, []).append(r)

    # Build breakdown and sum points
    breakdown: dict[int, dict] = {}
    total_primary = 0

    for tn in range(1, 20):
        rs = task_retrievabilities.get(tn, [])
        cards_count = len(rs)
        avg_r = sum(rs) / len(rs) if rs else 0.0
        is_mastered = avg_r >= 0.8 and cards_count > 0
        points = _POINTS.get(tn, 0)

        if is_mastered:
            total_primary += points

        breakdown[tn] = {
            "cards_count": cards_count,
            "avg_retrievability": round(avg_r, 4),
            "is_mastered": is_mastered,
            "points": points,
        }

    return {
        "predicted_primary_score": total_primary,
        "predicted_test_score": _primary_to_test_score(total_primary),
        "breakdown": breakdown,
    }


def get_current_plan(client, user_id: str) -> dict | None:
    """Fetch the active study plan for the user. Returns None if none exists."""
    result = (
        client.table("user_study_plan")
        .select("id,user_id,target_score,exam_date,hours_per_day,plan_data,generated_at,is_active")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .order("generated_at", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]
    return None
