"""Modified SM-2 spaced repetition algorithm with exam countdown factor."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

MIN_EASE_FACTOR = 1.3


@dataclass
class SRSCard:
    """Represents the current state of an SRS card."""

    ease_factor: float = 2.5
    interval_days: float = 1.0
    repetition_count: int = 0


@dataclass
class ReviewResult:
    """Result of calculate_next_review."""

    next_review_date: date
    new_interval: float
    new_ease_factor: float


def _exam_countdown_factor(exam_date: date | None, today: date | None = None) -> float:
    """Compress or expand intervals based on proximity to exam.

    <14 days  → 0.60  (aggressive compression)
    <30 days  → 0.75
    <90 days  → 1.00  (normal)
    >=90 days → 1.20  (relaxed)
    No exam   → 1.00
    """
    if exam_date is None:
        return 1.0
    if today is None:
        today = date.today()
    days_remaining = (exam_date - today).days
    if days_remaining < 14:
        return 0.60
    if days_remaining < 30:
        return 0.75
    if days_remaining < 90:
        return 1.00
    return 1.20


def calculate_next_review(
    card: SRSCard,
    self_assessment: str,
    exam_date: date | None = None,
    today: date | None = None,
) -> ReviewResult:
    """Calculate the next review date using modified SM-2 algorithm.

    Parameters
    ----------
    card: Current SRS card state.
    self_assessment: One of "again", "hard", "good", "easy".
    exam_date: Optional exam date for countdown factor.
    today: Override for current date (used in tests).

    Returns
    -------
    ReviewResult with next_review_date, new_interval, and new_ease_factor.
    """
    if today is None:
        today = date.today()

    ef = card.ease_factor
    interval = card.interval_days

    if self_assessment == "again":
        interval = 1.0
        ef -= 0.2
    elif self_assessment == "hard":
        interval *= 1.2
        ef -= 0.15
    elif self_assessment == "good":
        interval *= ef
    elif self_assessment == "easy":
        interval *= ef * 1.3
        ef += 0.15
    else:
        msg = f"Invalid self_assessment: {self_assessment}"
        raise ValueError(msg)

    # Enforce minimum ease factor
    ef = max(ef, MIN_EASE_FACTOR)

    # Apply exam countdown factor
    countdown = _exam_countdown_factor(exam_date, today)
    adjusted_interval = interval * countdown

    # Minimum interval is 1 day
    adjusted_interval = max(adjusted_interval, 1.0)

    next_review = today + timedelta(days=round(adjusted_interval))

    return ReviewResult(
        next_review_date=next_review,
        new_interval=round(adjusted_interval, 2),
        new_ease_factor=round(ef, 2),
    )
