"""Unit tests for the SRS engine (modified SM-2 algorithm)."""

from datetime import date

import pytest

from app.services.srs_engine import (
    MIN_EASE_FACTOR,
    ReviewResult,
    SRSCard,
    _exam_countdown_factor,
    calculate_next_review,
)

TODAY = date(2026, 3, 13)


# --- exam countdown factor ---


def test_countdown_no_exam():
    assert _exam_countdown_factor(None, TODAY) == 1.0


def test_countdown_less_than_14_days():
    exam = date(2026, 3, 20)  # 7 days away
    assert _exam_countdown_factor(exam, TODAY) == 0.60


def test_countdown_less_than_30_days():
    exam = date(2026, 4, 5)  # 23 days away
    assert _exam_countdown_factor(exam, TODAY) == 0.75


def test_countdown_less_than_90_days():
    exam = date(2026, 5, 15)  # 63 days away
    assert _exam_countdown_factor(exam, TODAY) == 1.00


def test_countdown_90_plus_days():
    exam = date(2026, 9, 1)  # 172 days away
    assert _exam_countdown_factor(exam, TODAY) == 1.20


def test_countdown_boundary_14():
    exam = TODAY + __import__("datetime").timedelta(days=14)
    assert _exam_countdown_factor(exam, TODAY) == 0.75  # 14 is NOT < 14


def test_countdown_boundary_30():
    exam = TODAY + __import__("datetime").timedelta(days=30)
    assert _exam_countdown_factor(exam, TODAY) == 1.00  # 30 is NOT < 30


def test_countdown_boundary_90():
    exam = TODAY + __import__("datetime").timedelta(days=90)
    assert _exam_countdown_factor(exam, TODAY) == 1.20  # 90 is NOT < 90


# --- self_assessment: again ---


def test_again_resets_interval():
    card = SRSCard(ease_factor=2.5, interval_days=10.0, repetition_count=5)
    result = calculate_next_review(card, "again", today=TODAY)
    assert result.new_interval == 1.0
    assert result.new_ease_factor == 2.3  # 2.5 - 0.2


def test_again_next_review_date():
    card = SRSCard(ease_factor=2.5, interval_days=10.0)
    result = calculate_next_review(card, "again", today=TODAY)
    assert result.next_review_date == date(2026, 3, 14)  # tomorrow


# --- self_assessment: hard ---


def test_hard_interval():
    card = SRSCard(ease_factor=2.5, interval_days=5.0)
    result = calculate_next_review(card, "hard", today=TODAY)
    assert result.new_interval == 6.0  # 5 * 1.2 = 6.0
    assert result.new_ease_factor == 2.35  # 2.5 - 0.15


def test_hard_next_review_date():
    card = SRSCard(ease_factor=2.5, interval_days=5.0)
    result = calculate_next_review(card, "hard", today=TODAY)
    assert result.next_review_date == date(2026, 3, 19)  # +6 days


# --- self_assessment: good ---


def test_good_interval():
    card = SRSCard(ease_factor=2.5, interval_days=5.0)
    result = calculate_next_review(card, "good", today=TODAY)
    assert result.new_interval == 12.5  # 5 * 2.5
    assert result.new_ease_factor == 2.5  # unchanged


def test_good_next_review_date():
    card = SRSCard(ease_factor=2.5, interval_days=5.0)
    result = calculate_next_review(card, "good", today=TODAY)
    # round(12.5) = 12 (banker's rounding in Python)
    assert result.next_review_date == date(2026, 3, 25)  # +12 days


# --- self_assessment: easy ---


def test_easy_interval():
    card = SRSCard(ease_factor=2.5, interval_days=5.0)
    result = calculate_next_review(card, "easy", today=TODAY)
    # 5 * 2.5 * 1.3 = 16.25
    assert result.new_interval == 16.25
    assert result.new_ease_factor == 2.65  # 2.5 + 0.15


def test_easy_larger_than_good():
    card = SRSCard(ease_factor=2.5, interval_days=5.0)
    good = calculate_next_review(card, "good", today=TODAY)
    easy = calculate_next_review(card, "easy", today=TODAY)
    assert easy.new_interval > good.new_interval


# --- ease_factor minimum ---


def test_ef_floor_on_again():
    card = SRSCard(ease_factor=1.4, interval_days=3.0)
    result = calculate_next_review(card, "again", today=TODAY)
    # 1.4 - 0.2 = 1.2 → clamped to 1.3
    assert result.new_ease_factor == MIN_EASE_FACTOR


def test_ef_floor_on_hard():
    card = SRSCard(ease_factor=1.35, interval_days=3.0)
    result = calculate_next_review(card, "hard", today=TODAY)
    # 1.35 - 0.15 = 1.2 → clamped to 1.3
    assert result.new_ease_factor == MIN_EASE_FACTOR


def test_ef_never_below_min_after_series_of_again():
    card = SRSCard(ease_factor=2.5, interval_days=10.0)
    for _ in range(20):
        result = calculate_next_review(card, "again", today=TODAY)
        card = SRSCard(
            ease_factor=result.new_ease_factor,
            interval_days=result.new_interval,
        )
    assert card.ease_factor >= MIN_EASE_FACTOR


# --- exam countdown integration ---


def test_good_with_exam_compression_30d():
    """Exam in 20 days → 0.75 factor compresses intervals."""
    card = SRSCard(ease_factor=2.5, interval_days=5.0)
    exam = date(2026, 4, 2)  # 20 days away
    result = calculate_next_review(card, "good", exam_date=exam, today=TODAY)
    # 5 * 2.5 = 12.5, * 0.75 = 9.375 → 9.38
    assert result.new_interval == 9.38


def test_good_with_exam_compression_14d():
    """Exam in 10 days → 0.60 factor, aggressive compression."""
    card = SRSCard(ease_factor=2.5, interval_days=5.0)
    exam = date(2026, 3, 23)  # 10 days away
    result = calculate_next_review(card, "good", exam_date=exam, today=TODAY)
    # 5 * 2.5 = 12.5, * 0.60 = 7.5
    assert result.new_interval == 7.5


def test_good_with_exam_relaxed():
    """Exam 120 days away → 1.20 factor, intervals expanded."""
    card = SRSCard(ease_factor=2.5, interval_days=5.0)
    exam = date(2026, 7, 11)  # 120 days away
    result = calculate_next_review(card, "good", exam_date=exam, today=TODAY)
    # 5 * 2.5 = 12.5, * 1.20 = 15.0
    assert result.new_interval == 15.0


def test_again_with_exam_compression():
    """Even with compression, again interval stays at min 1."""
    card = SRSCard(ease_factor=2.5, interval_days=10.0)
    exam = date(2026, 3, 20)  # 7 days
    result = calculate_next_review(card, "again", exam_date=exam, today=TODAY)
    # 1 * 0.60 = 0.6 → clamped to 1.0
    assert result.new_interval == 1.0


# --- minimum interval ---


def test_minimum_interval_is_one():
    card = SRSCard(ease_factor=1.3, interval_days=0.5)
    result = calculate_next_review(card, "hard", today=TODAY)
    # 0.5 * 1.2 = 0.6 → clamped to 1.0
    assert result.new_interval >= 1.0


# --- invalid assessment ---


def test_invalid_assessment_raises():
    card = SRSCard(ease_factor=2.5, interval_days=5.0)
    with pytest.raises(ValueError, match="Invalid self_assessment"):
        calculate_next_review(card, "invalid", today=TODAY)


# --- return type ---


def test_returns_review_result():
    card = SRSCard(ease_factor=2.5, interval_days=5.0)
    result = calculate_next_review(card, "good", today=TODAY)
    assert isinstance(result, ReviewResult)
    assert isinstance(result.next_review_date, date)
    assert isinstance(result.new_interval, float)
    assert isinstance(result.new_ease_factor, float)
