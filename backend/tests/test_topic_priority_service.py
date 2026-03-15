"""Tests for topic_priority_service: priority scoring and readiness estimation."""

from app.services.topic_priority_service import (
    TopicInfo,
    UserTopicState,
    calculate_topic_priority,
    estimate_readiness,
)


def _topic(task_number=1, max_points=1, hours=1.0):
    return TopicInfo(
        task_number=task_number,
        title=f"Topic {task_number}",
        max_points=max_points,
        estimated_study_hours=hours,
    )


class TestCalculateTopicPriority:
    def test_high_points_low_strength_high_priority(self):
        """A topic with high max_points and low strength should rank high."""
        score = calculate_topic_priority(
            _topic(max_points=4, hours=2.0),
            UserTopicState(strength_score=0.1),
            exam_days_remaining=60,
        )
        # (4/2) * 0.9 * 1.0 = 1.8
        assert score == 1.8

    def test_low_points_high_strength_low_priority(self):
        """A topic with low max_points and high strength should rank low."""
        score = calculate_topic_priority(
            _topic(max_points=1, hours=1.0),
            UserTopicState(strength_score=0.9),
            exam_days_remaining=60,
        )
        # (1/1) * 0.1 * 1.0 = 0.1
        assert score == 0.1

    def test_fully_mastered_zero_priority(self):
        """A fully mastered topic (strength=1.0) should have priority 0."""
        score = calculate_topic_priority(
            _topic(max_points=4, hours=1.0),
            UserTopicState(strength_score=1.0),
            exam_days_remaining=30,
        )
        assert score == 0.0

    def test_exam_urgency_under_14_days(self):
        """Urgency doubles when exam is under 14 days away."""
        base = calculate_topic_priority(
            _topic(max_points=2, hours=1.0),
            UserTopicState(strength_score=0.0),
            exam_days_remaining=60,
        )
        urgent = calculate_topic_priority(
            _topic(max_points=2, hours=1.0),
            UserTopicState(strength_score=0.0),
            exam_days_remaining=10,
        )
        assert urgent == base * 2.0

    def test_exam_urgency_under_30_days(self):
        """Urgency is 1.5x when exam is 14-30 days away."""
        score = calculate_topic_priority(
            _topic(max_points=2, hours=1.0),
            UserTopicState(strength_score=0.0),
            exam_days_remaining=20,
        )
        # (2/1) * 1.0 * 1.5 = 3.0
        assert score == 3.0

    def test_exam_urgency_over_90_days(self):
        """Urgency is reduced when exam is far away."""
        score = calculate_topic_priority(
            _topic(max_points=2, hours=1.0),
            UserTopicState(strength_score=0.0),
            exam_days_remaining=120,
        )
        # (2/1) * 1.0 * 0.8 = 1.6
        assert score == 1.6

    def test_exam_urgency_no_exam(self):
        """Default urgency when no exam date is set."""
        score = calculate_topic_priority(
            _topic(max_points=2, hours=1.0),
            UserTopicState(strength_score=0.0),
            exam_days_remaining=None,
        )
        # (2/1) * 1.0 * 1.0 = 2.0
        assert score == 2.0

    def test_zero_study_hours_defaults_to_one(self):
        """Zero or None study hours should not cause division by zero."""
        score = calculate_topic_priority(
            _topic(max_points=2, hours=0.0),
            UserTopicState(strength_score=0.0),
            exam_days_remaining=60,
        )
        # (2/1.0) * 1.0 * 1.0 = 2.0
        assert score == 2.0

    def test_ordering_high_value_weak_beats_low_value_weak(self):
        """Higher max_points topic should outrank lower one at same strength."""
        high = calculate_topic_priority(
            _topic(max_points=4, hours=2.0),
            UserTopicState(strength_score=0.3),
            exam_days_remaining=60,
        )
        low = calculate_topic_priority(
            _topic(max_points=1, hours=2.0),
            UserTopicState(strength_score=0.3),
            exam_days_remaining=60,
        )
        assert high > low


class TestEstimateReadiness:
    def test_no_topics(self):
        assert estimate_readiness([]) == 0.0

    def test_fully_mastered(self):
        topics = [
            (_topic(max_points=1), UserTopicState(strength_score=1.0)),
            (_topic(max_points=2), UserTopicState(strength_score=1.0)),
        ]
        assert estimate_readiness(topics) == 100.0

    def test_no_progress(self):
        topics = [
            (_topic(max_points=1), UserTopicState(strength_score=0.0)),
            (_topic(max_points=2), UserTopicState(strength_score=0.0)),
        ]
        assert estimate_readiness(topics) == 0.0

    def test_weighted_by_max_points(self):
        """Higher-point topics should weigh more in readiness."""
        topics = [
            (_topic(max_points=1), UserTopicState(strength_score=1.0)),
            (_topic(max_points=4), UserTopicState(strength_score=0.0)),
        ]
        # (1*1.0 + 4*0.0) / 5 = 0.2 → 20%
        assert estimate_readiness(topics) == 20.0

    def test_partial_progress(self):
        topics = [
            (_topic(max_points=2), UserTopicState(strength_score=0.5)),
            (_topic(max_points=2), UserTopicState(strength_score=0.8)),
        ]
        # (2*0.5 + 2*0.8) / 4 = 2.6/4 = 0.65 → 65%
        assert estimate_readiness(topics) == 65.0
