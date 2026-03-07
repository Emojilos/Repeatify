"""Adaptive study plan: mode determination and new-card limits."""

from __future__ import annotations

from typing import Literal

StudyMode = Literal["relaxed", "standard", "intensive", "sprint"]

# Days-until-exam thresholds (inclusive upper bound for each mode)
_SPRINT_MAX_DAYS = 20
_INTENSIVE_MAX_DAYS = 60
_STANDARD_MAX_DAYS = 180

# New-cards-per-day limits per mode
NEW_CARDS_LIMIT: dict[StudyMode, int] = {
    "sprint": 5,
    "intensive": 10,
    "standard": 15,
    "relaxed": 20,
}

# EGE task numbers prioritised in sprint mode
SPRINT_PRIORITY_TASKS: set[int] = set(range(1, 13))  # tasks 1–12


def determine_mode(days_until_exam: int) -> StudyMode:
    """Return the study mode based on days remaining until the exam.

    Thresholds:
        sprint:    days_until_exam <= 20
        intensive: 21 <= days_until_exam <= 60
        standard:  61 <= days_until_exam <= 180
        relaxed:   days_until_exam > 180
    """
    if days_until_exam <= _SPRINT_MAX_DAYS:
        return "sprint"
    if days_until_exam <= _INTENSIVE_MAX_DAYS:
        return "intensive"
    if days_until_exam <= _STANDARD_MAX_DAYS:
        return "standard"
    return "relaxed"


def new_cards_limit(mode: StudyMode) -> int:
    """Return the maximum number of new cards per session for the given mode."""
    return NEW_CARDS_LIMIT[mode]
