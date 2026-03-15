"""Diagnostic test service: problem selection and answer grading."""

from __future__ import annotations

import random
import uuid


def select_problems_for_diagnostic(client, user_id: str) -> list[dict]:
    """Select 19 problems (one per task_number 1-19), medium difficulty preferred.

    Returns list of dicts with problem_id, task_number, problem_text, problem_images.
    """
    result = (
        client.table("problems")
        .select("id,task_number,problem_text,problem_images,difficulty")
        .order("task_number")
        .execute()
    )
    all_problems = result.data or []

    # Group by task_number
    by_task: dict[int, list[dict]] = {}
    for p in all_problems:
        tn = p["task_number"]
        by_task.setdefault(tn, []).append(p)

    selected: list[dict] = []
    for task_num in range(1, 20):
        candidates = by_task.get(task_num, [])
        if not candidates:
            continue

        # Prefer medium difficulty, fallback to any
        medium = [c for c in candidates if c.get("difficulty") == "medium"]
        pool = medium if medium else candidates
        chosen = random.choice(pool)

        selected.append({
            "problem_id": chosen["id"],
            "task_number": chosen["task_number"],
            "problem_text": chosen["problem_text"],
            "problem_images": chosen.get("problem_images"),
        })

    return selected


def check_diagnostic_answer(
    user_answer: str | None,
    correct_answer: str | None,
    tolerance: float = 0.0,
) -> bool | None:
    """Check answer correctness. Returns None if no correct_answer (Part 2)."""
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


def grade_and_persist(
    client,
    user_id: str,
    answers: list[dict],
) -> list[dict]:
    """Grade diagnostic answers and persist to diagnostic_results.

    answers: list of {task_number, answer, self_assessment, time_spent_seconds}
    Returns list of DiagnosticResultItem dicts.
    """
    # Fetch correct answers for all problems
    task_numbers = [a["task_number"] for a in answers]
    prob_result = (
        client.table("problems")
        .select("id,task_number,correct_answer,answer_tolerance")
        .in_("task_number", task_numbers)
        .execute()
    )
    all_problems = prob_result.data or []

    # Build lookup: task_number -> best problem match for checking
    correct_by_task: dict[int, dict] = {}
    for p in all_problems:
        tn = p["task_number"]
        if tn not in correct_by_task:
            correct_by_task[tn] = p

    results: list[dict] = []
    rows_to_insert: list[dict] = []

    for answer in answers:
        task_num = answer["task_number"]
        is_part2 = task_num >= 13

        if is_part2:
            # Part 2: self-assessment only
            is_correct = None
            self_assessment = answer.get("self_assessment")
        else:
            # Part 1: auto-check answer
            prob = correct_by_task.get(task_num, {})
            is_correct = check_diagnostic_answer(
                answer.get("answer"),
                prob.get("correct_answer"),
                prob.get("answer_tolerance") or 0.0,
            )
            self_assessment = None

        result_item = {
            "task_number": task_num,
            "is_correct": is_correct,
            "self_assessment": self_assessment,
            "time_spent_seconds": answer["time_spent_seconds"],
        }
        results.append(result_item)

        rows_to_insert.append({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "task_number": task_num,
            "is_correct": is_correct,
            "self_assessment": self_assessment,
            "time_spent_seconds": answer["time_spent_seconds"],
        })

    # Bulk insert into diagnostic_results
    if rows_to_insert:
        client.table("diagnostic_results").insert(rows_to_insert).execute()

    return results


def has_existing_diagnostic(client, user_id: str) -> bool:
    """Check if user already has diagnostic results."""
    result = (
        client.table("diagnostic_results")
        .select("id")
        .eq("user_id", user_id)
        .execute()
    )
    return bool(result.data)
