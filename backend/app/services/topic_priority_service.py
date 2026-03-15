"""Topic priority calculation for exam readiness recommendations.

Prioritises topics by ROI: (max_points / study_hours) * weakness * urgency.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TopicInfo:
    """Minimal topic data required for priority scoring."""

    task_number: int
    title: str
    max_points: int
    estimated_study_hours: float


@dataclass
class UserTopicState:
    """User-specific progress on a topic."""

    strength_score: float = 0.0  # 0.0–1.0
    fire_completed: bool = False


def _exam_urgency(exam_days_remaining: int | None) -> float:
    """Return an urgency multiplier based on days until exam.

    Closer exam → higher urgency so weak high-value topics surface faster.
    """
    if exam_days_remaining is None:
        return 1.0
    if exam_days_remaining <= 14:
        return 2.0
    if exam_days_remaining <= 30:
        return 1.5
    if exam_days_remaining <= 90:
        return 1.0
    return 0.8


def calculate_topic_priority(
    topic: TopicInfo,
    progress: UserTopicState,
    exam_days_remaining: int | None,
) -> float:
    """Calculate priority score for a topic.

    Formula: (max_points / estimated_study_hours) * weakness_score * exam_urgency

    Higher score → topic should be studied first.
    """
    hours = topic.estimated_study_hours
    study_hours = hours if hours and hours > 0 else 1.0
    points_per_hour = topic.max_points / study_hours

    # Weakness: 1.0 means totally weak, 0.0 means fully mastered
    weakness_score = 1.0 - progress.strength_score

    urgency = _exam_urgency(exam_days_remaining)

    return round(points_per_hour * weakness_score * urgency, 4)


def estimate_readiness(
    topics: list[tuple[TopicInfo, UserTopicState]],
) -> float:
    """Estimate overall exam readiness as a percentage (0–100).

    Weighted average of strength scores, weighted by max_points.
    """
    total_weight = 0
    weighted_strength = 0.0
    for topic, progress in topics:
        total_weight += topic.max_points
        weighted_strength += topic.max_points * progress.strength_score
    if total_weight == 0:
        return 0.0
    return round((weighted_strength / total_weight) * 100, 1)
