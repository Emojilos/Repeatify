"""XP and level system.

Centralises XP award rules, level thresholds, and the helper that
persists changes to the ``users`` table.
"""

from __future__ import annotations

# XP rewards per action type
XP_PART1_CORRECT = 10   # tasks 1-12 correct answer
XP_PART2_CORRECT = 25   # tasks 13-19 (good/easy only)
XP_FIRE_COMPLETE = 50   # completed all 4 FIRe stages for a topic
XP_SESSION_BONUS = 30   # completed an SRS session
XP_STREAK_BONUS = 5     # daily streak maintained

# Level table: (min_xp, level_number, name)
# Sorted ascending by min_xp.
LEVEL_TABLE: list[tuple[int, int, str]] = [
    (0, 1, "Новичок"),
    (100, 2, "Ученик"),
    (300, 3, "Практикант"),
    (600, 4, "Решатель"),
    (1000, 5, "Знаток"),
    (1500, 6, "Эксперт"),
    (2500, 7, "Мастер"),
    (4000, 8, "Гуру"),
    (6000, 9, "Легенда"),
    (10000, 10, "Бог ЕГЭ"),
]


def calculate_level(xp: int) -> tuple[int, str]:
    """Return ``(level_number, level_name)`` for the given XP total."""
    level_num = 1
    level_name = LEVEL_TABLE[0][2]
    for min_xp, num, name in LEVEL_TABLE:
        if xp >= min_xp:
            level_num = num
            level_name = name
        else:
            break
    return level_num, level_name


def xp_for_next_level(current_xp: int) -> int | None:
    """Return the XP threshold for the next level, or ``None`` if max."""
    for min_xp, _num, _name in LEVEL_TABLE:
        if current_xp < min_xp:
            return min_xp
    return None


def calculate_problem_xp(
    is_correct: bool,
    task_number: int,
    self_assessment: str,
) -> int:
    """Return XP earned for a single problem attempt."""
    if not is_correct:
        return 0
    if task_number >= 13:
        return XP_PART2_CORRECT if self_assessment in ("good", "easy") else 0
    return XP_PART1_CORRECT


def award_xp(
    client,
    user_id: str,
    xp_amount: int,
) -> tuple[int, int | None]:
    """Persist XP award and recalculate level.

    Returns ``(new_total_xp, new_level_reached)`` where
    *new_level_reached* is the level number if the user levelled up,
    otherwise ``None``.
    """
    if xp_amount <= 0:
        # Fetch current XP for the response even when nothing changes
        row = (
            client.table("users")
            .select("current_xp,current_level")
            .eq("id", user_id)
            .execute()
        )
        current_xp = (row.data[0] if row.data else {}).get("current_xp", 0)
        return current_xp, None

    # Fetch current state
    user_result = (
        client.table("users")
        .select("current_xp,current_level")
        .eq("id", user_id)
        .execute()
    )
    if not user_result.data:
        return 0, None

    old_xp = user_result.data[0].get("current_xp") or 0
    old_level = user_result.data[0].get("current_level") or 1
    new_xp = old_xp + xp_amount
    new_level, _ = calculate_level(new_xp)

    update_data: dict = {"current_xp": new_xp}
    levelled_up: int | None = None
    if new_level != old_level:
        update_data["current_level"] = new_level
        levelled_up = new_level

    client.table("users").update(update_data).eq("id", user_id).execute()
    return new_xp, levelled_up
