"""Study plan: knowledge-map based assessment system.

Each task (1-19) has a mastery level determined by a 10-problem assessment test.
No time-based scheduling — just mastery tracking per task type.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from random import sample

def check_answer(
    user_answer: str | None,
    correct_answer: str | None,
    tolerance: float = 0.0,
) -> bool | None:
    """Check answer correctness. Returns None if no correct_answer."""
    if not correct_answer:
        return None
    if not user_answer:
        return False

    user_answer = user_answer.strip()
    correct_answer = correct_answer.strip()

    if user_answer.lower() == correct_answer.lower():
        return True

    if tolerance > 0:
        try:
            diff = abs(float(user_answer) - float(correct_answer))
            return diff <= tolerance
        except ValueError:
            pass

    return False

# Recommended preparation order (by ROI: easiest → hardest, points/effort)
# Part 1: by pass rate (easiest first)
# Part 2: by accessibility and point efficiency
_ROI_ORDER: list[int] = [
    # Part 1 (1 pt each) — quick wins first
    4, 1, 6, 7, 10, 3, 2, 5, 8, 9, 11, 12,
    # Part 2 — most accessible first
    13,  # Уравнения (2 pt) — natural extension of task 6
    15,  # Неравенства (2 pt) — similar to equations
    16,  # Экономическая задача (2 pt) — algorithmic, learnable
    14,  # Стереометрия профильная (3 pt)
    17,  # Планиметрия профильная (3 pt)
    18,  # Параметры (4 pt) — hard but high reward
    19,  # Числа и их свойства (4 pt) — hardest, requires creativity
]

# Points per task_number (EGE 2025 profile math)
# Part 1 (1-12): 1 point each
# Part 2: 13=2, 14=3, 15=2, 16=2, 17=3, 18=4, 19=4
_POINTS: dict[int, int] = {
    1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1,
    7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1,
    13: 2, 14: 3, 15: 2, 16: 2, 17: 3, 18: 4, 19: 4,
}

# Required tasks per target_score (EGE 2025)
# 70 = Part 1 only (12 primary → 70 test)
# 80 = Part 1 + 13, 15, 16 (18 primary → 82 test)
# 90 = Part 1 + 13, 14, 15, 16, 17 (24 primary → 94 test)
# 100 = all tasks (32 primary → 100 test)
_REQUIRED_TASKS: dict[int, list[int]] = {
    70: list(range(1, 13)),
    80: list(range(1, 13)) + [13, 15, 16],
    90: list(range(1, 13)) + [13, 14, 15, 16, 17],
    100: list(range(1, 20)),
}

ASSESSMENT_SIZE = 10


def get_required_tasks(target_score: int) -> list[int]:
    """Return list of task_numbers required for the given target_score."""
    return _REQUIRED_TASKS.get(target_score, list(range(1, 13)))


def _mastery_status(correct: int, total: int) -> str:
    """Compute mastery status from assessment score."""
    if total == 0:
        return "not_tested"
    if correct <= 3:
        return "weak"
    if correct <= 6:
        return "medium"
    if correct <= 9:
        return "good"
    return "mastered"


def _sort_by_roi(task_numbers: list[int]) -> list[int]:
    """Sort task_numbers by ROI order (Part 1 from PRD, Part 2 appended)."""
    roi_index = {tn: i for i, tn in enumerate(_ROI_ORDER)}
    max_idx = len(_ROI_ORDER)
    return sorted(task_numbers, key=lambda tn: roi_index.get(tn, max_idx + tn))


def _get_latest_assessments(client, user_id: str) -> dict[int, dict]:
    """Fetch the most recent assessment per task_number for user.

    Returns dict: task_number -> {correct_count, total_count, assessed_at}
    """
    result = (
        client.table("task_assessments")
        .select("task_number,correct_count,total_count,assessed_at")
        .eq("user_id", user_id)
        .order("assessed_at", desc=True)
        .execute()
    )
    latest: dict[int, dict] = {}
    for row in result.data or []:
        tn = row["task_number"]
        if tn not in latest:
            latest[tn] = row
    return latest


def generate_plan(
    client,
    user_id: str,
    target_score: int,
) -> dict:
    """Generate a knowledge-map study plan and save to user_study_plan.

    Returns the plan dict (same shape as plan_data column).
    """
    required = get_required_tasks(target_score)
    assessments = _get_latest_assessments(client, user_id)

    tasks = []
    for tn in _sort_by_roi(required):
        a = assessments.get(tn)
        if a:
            correct = a["correct_count"]
            total = a["total_count"]
            status = _mastery_status(correct, total)
            tasks.append({
                "task_number": tn,
                "status": status,
                "correct": correct,
                "total": total,
                "assessed_at": a["assessed_at"],
            })
        else:
            tasks.append({
                "task_number": tn,
                "status": "not_tested",
                "correct": None,
                "total": None,
                "assessed_at": None,
            })

    plan_data = {
        "target_score": target_score,
        "tasks": tasks,
    }

    plan_id = str(uuid.uuid4())

    # Deactivate existing plans
    client.table("user_study_plan").update(
        {"is_active": False}
    ).eq("user_id", user_id).eq("is_active", True).execute()

    client.table("user_study_plan").insert({
        "id": plan_id,
        "user_id": user_id,
        "target_score": target_score,
        "plan_data": plan_data,
        "is_active": True,
    }).execute()

    return {
        "id": plan_id,
        "user_id": user_id,
        "target_score": target_score,
        "plan_data": plan_data,
        "is_active": True,
    }


def start_assessment(client, user_id: str, task_number: int) -> list[dict]:
    """Select 10 random problems for a task assessment.

    Returns list of problem dicts (without correct_answer).
    """
    result = (
        client.table("problems")
        .select("id,task_number,difficulty,problem_text,problem_images,hints")
        .eq("task_number", task_number)
        .execute()
    )
    problems = result.data or []

    if len(problems) <= ASSESSMENT_SIZE:
        selected = problems
    else:
        # Try to get a mix of difficulties
        by_diff: dict[str, list[dict]] = {}
        for p in problems:
            by_diff.setdefault(p.get("difficulty", "medium"), []).append(p)

        selected = []
        # Take proportionally from each difficulty
        remaining = ASSESSMENT_SIZE
        diffs = list(by_diff.keys())
        for i, diff in enumerate(diffs):
            pool = by_diff[diff]
            if i == len(diffs) - 1:
                take = remaining
            else:
                take = max(1, remaining // (len(diffs) - i))
            take = min(take, len(pool))
            selected.extend(sample(pool, take))
            remaining -= take

        # Fill up if needed
        if len(selected) < ASSESSMENT_SIZE:
            remaining_problems = [p for p in problems if p not in selected]
            need = ASSESSMENT_SIZE - len(selected)
            selected.extend(sample(remaining_problems, min(need, len(remaining_problems))))

    return [
        {
            "id": p["id"],
            "task_number": p["task_number"],
            "difficulty": p.get("difficulty"),
            "problem_text": p.get("problem_text"),
            "problem_images": p.get("problem_images"),
            "hints": p.get("hints"),
        }
        for p in selected
    ]


def submit_assessment(
    client,
    user_id: str,
    task_number: int,
    answers: list[dict],
) -> dict:
    """Grade assessment answers and persist results.

    answers: list of {problem_id, answer}
    Returns assessment result with per-problem details.
    """
    problem_ids = [a["problem_id"] for a in answers]

    # Fetch correct answers
    problems_result = (
        client.table("problems")
        .select("id,correct_answer,answer_tolerance,solution_markdown")
        .in_("id", problem_ids)
        .execute()
    )
    problems_by_id = {p["id"]: p for p in (problems_result.data or [])}

    correct_count = 0
    details = []

    for a in answers:
        problem = problems_by_id.get(a["problem_id"], {})
        correct_answer = problem.get("correct_answer")
        tolerance = problem.get("answer_tolerance") or 0.0

        is_correct = check_answer(
            a.get("answer"),
            correct_answer,
            tolerance,
        )
        # For Part 2 tasks without correct_answer, treat as incorrect
        if is_correct is None:
            is_correct = False

        if is_correct:
            correct_count += 1

        details.append({
            "problem_id": a["problem_id"],
            "is_correct": is_correct,
            "correct_answer": correct_answer,
            "solution_markdown": problem.get("solution_markdown"),
        })

    total_count = len(answers)

    # Persist assessment
    client.table("task_assessments").insert({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "task_number": task_number,
        "correct_count": correct_count,
        "total_count": total_count,
    }).execute()

    # Create/update FSRS cards for attempted problems
    _ensure_fsrs_cards_from_assessment(client, user_id, details, task_number)

    status = _mastery_status(correct_count, total_count)

    return {
        "task_number": task_number,
        "correct_count": correct_count,
        "total_count": total_count,
        "status": status,
        "details": details,
    }


def _ensure_fsrs_cards_from_assessment(
    client,
    user_id: str,
    details: list[dict],
    task_number: int,
) -> None:
    """Create or update FSRS cards based on assessment results."""
    for item in details:
        problem_id = item["problem_id"]
        is_correct = item["is_correct"]

        # Check if card exists
        existing = (
            client.table("fsrs_cards")
            .select("id")
            .eq("user_id", user_id)
            .eq("problem_id", problem_id)
            .execute()
        )

        if existing.data:
            continue  # Card already exists, FSRS review flow handles updates

        # Create new card with initial params based on correctness
        if is_correct:
            card_data = {
                "state": "review",
                "difficulty": 3.0,
                "stability": 7.0,
            }
        else:
            card_data = {
                "state": "learning",
                "difficulty": 6.0,
                "stability": 1.0,
            }

        now = datetime.now(timezone.utc).isoformat()
        from datetime import timedelta
        due = (datetime.now(timezone.utc) + timedelta(days=card_data["stability"])).isoformat()

        client.table("fsrs_cards").insert({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "problem_id": problem_id,
            "card_type": "problem",
            "difficulty": card_data["difficulty"],
            "stability": card_data["stability"],
            "state": card_data["state"],
            "due": due,
            "last_review": now,
            "reps": 1,
            "lapses": 0 if is_correct else 1,
        }).execute()


# ---------------------------------------------------------------------------
# Score prediction (kept from previous version)
# ---------------------------------------------------------------------------

# Primary → test score conversion table
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
    exam_date=None,
) -> dict:
    """Predict user's score based on FSRS card retrievability."""
    from app.services.fsrs_service import get_retrievability

    result = (
        client.table("fsrs_cards")
        .select("id,problem_id,prototype_id,state,stability,difficulty,due,last_review")
        .eq("user_id", user_id)
        .execute()
    )
    cards = result.data or []

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
    """Fetch the active study plan for the user."""
    result = (
        client.table("user_study_plan")
        .select("id,user_id,target_score,plan_data,generated_at,is_active")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .order("generated_at", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]
    return None
