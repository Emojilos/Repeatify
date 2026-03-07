"""Unit tests for FSRSEngine (TASK-013)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.core.fsrs.engine import FSRSEngine


@pytest.fixture
def engine() -> FSRSEngine:
    return FSRSEngine()


@pytest.fixture
def new_card() -> dict:
    """card_progress row for a brand-new card (never reviewed)."""
    return {
        "stability": None,
        "difficulty": None,
        "fsrs_state": "new",
        "due_date": None,
        "last_review": None,
        "review_count": 0,
    }


@pytest.fixture
def review_card() -> dict:
    """card_progress row for a card currently in the review state."""
    now = datetime.now(timezone.utc)
    return {
        "stability": 10.0,
        "difficulty": 5.0,
        "fsrs_state": "review",
        "due_date": now - timedelta(days=1),  # overdue by 1 day
        "last_review": now - timedelta(days=10),
        "review_count": 5,
    }


# ---------------------------------------------------------------------------
# Test 1: New card rated Good → Learning state, due ~1 day
# ---------------------------------------------------------------------------
def test_new_card_good_rating_produces_learning_state(engine, new_card):
    result = engine.schedule(new_card, rating=3)

    assert result["fsrs_state"] in ("learning", "review"), (
        "After first 'Good' rating the card should move to learning or review"
    )
    now = datetime.now(timezone.utc)
    assert result["due_date"] > now, "due_date must be in the future"
    delta = result["due_date"] - now
    # FSRS-5: first Good interval is typically minutes to ~1 day
    assert delta <= timedelta(days=2), f"Interval too long for first review: {delta}"


# ---------------------------------------------------------------------------
# Test 2: New card rated Again → short relearning interval
# ---------------------------------------------------------------------------
def test_new_card_again_rating_has_minimal_interval(engine, new_card):
    result = engine.schedule(new_card, rating=1)

    now = datetime.now(timezone.utc)
    delta = result["due_date"] - now
    # Again on a new card → very short retry interval (minutes, not days)
    assert delta <= timedelta(hours=1), (
        f"After 'Again' the next review should be very soon, got {delta}"
    )


# ---------------------------------------------------------------------------
# Test 3: Review card rated Easy → long interval (≥ 20 days)
# ---------------------------------------------------------------------------
def test_review_card_easy_rating_produces_long_interval(engine, review_card):
    result = engine.schedule(review_card, rating=4)

    now = datetime.now(timezone.utc)
    delta = result["due_date"] - now
    assert delta >= timedelta(days=20), (
        f"stability=10, Easy should schedule far out; got {delta.days} days"
    )
    assert result["fsrs_state"] == "review"


# ---------------------------------------------------------------------------
# Test 4: review_count increments by 1 on every call
# ---------------------------------------------------------------------------
def test_review_count_increments(engine, new_card):
    result = engine.schedule(new_card, rating=3)
    assert result["review_count"] == 1

    # Simulate the card having been reviewed once
    second_progress = {**new_card, **result}
    result2 = engine.schedule(second_progress, rating=3)
    assert result2["review_count"] == 2


# ---------------------------------------------------------------------------
# Test 5: Again on review card → relearning state
# ---------------------------------------------------------------------------
def test_review_card_again_rating_returns_relearning(engine, review_card):
    result = engine.schedule(review_card, rating=1)

    assert result["fsrs_state"] == "relearning", (
        "Failing a review card should move it to 'relearning'"
    )
    now = datetime.now(timezone.utc)
    delta = result["due_date"] - now
    # Relearning step is short
    assert delta <= timedelta(hours=1), (
        f"Relearning interval should be minimal, got {delta}"
    )


# ---------------------------------------------------------------------------
# Test 6: All 4 ratings produce distinct stability values
# ---------------------------------------------------------------------------
def test_all_ratings_produce_different_stability(engine, new_card):
    stabilities = {
        rating: engine.schedule(new_card, rating=rating)["stability"]
        for rating in (1, 2, 3, 4)
    }
    # Higher rating → higher stability (or at least non-decreasing)
    assert stabilities[1] <= stabilities[2] <= stabilities[3] <= stabilities[4], (
        f"Expected stability to increase with rating, got {stabilities}"
    )


# ---------------------------------------------------------------------------
# Test 7: Invalid rating raises ValueError
# ---------------------------------------------------------------------------
def test_invalid_rating_raises_value_error(engine, new_card):
    with pytest.raises(ValueError, match="Invalid rating"):
        engine.schedule(new_card, rating=0)

    with pytest.raises(ValueError, match="Invalid rating"):
        engine.schedule(new_card, rating=5)


# ---------------------------------------------------------------------------
# Test 8: last_review is set to approximately now
# ---------------------------------------------------------------------------
def test_last_review_is_set_to_now(engine, new_card):
    before = datetime.now(timezone.utc)
    result = engine.schedule(new_card, rating=3)
    after = datetime.now(timezone.utc)

    assert before <= result["last_review"] <= after


# ---------------------------------------------------------------------------
# Test 9: preview_ratings returns all 4 ratings without side effects
# ---------------------------------------------------------------------------
def test_preview_ratings_returns_all_four(engine, review_card):
    previews = engine.preview_ratings(review_card)

    assert set(previews.keys()) == {1, 2, 3, 4}
    for rating_int, info in previews.items():
        assert "due_date" in info
        assert "stability" in info
        assert "difficulty" in info
        assert "fsrs_state" in info
        # No review_count in preview (it's read-only)


# ---------------------------------------------------------------------------
# Test 10: Difficulty stays within [1.0, 10.0] across all ratings
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("rating", [1, 2, 3, 4])
def test_difficulty_stays_in_valid_range(engine, new_card, rating):
    result = engine.schedule(new_card, rating=rating)
    assert 1.0 <= result["difficulty"] <= 10.0, (
        f"difficulty={result['difficulty']} out of [1, 10] for rating={rating}"
    )
