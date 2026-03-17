"""Tests for the srs_cards → fsrs_cards migration script.

Tests the pure conversion functions (no DB access required).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add tools/migrations to sys.path so we can import the script
_tools_migrations = str(
    Path(__file__).resolve().parent.parent.parent
    / "tools"
    / "migrations",
)
if _tools_migrations not in sys.path:
    sys.path.insert(0, _tools_migrations)

from migrate_srs_to_fsrs import (  # noqa: E402
    convert_card,
    ease_to_difficulty,
    map_status,
)


class TestEaseToDifficulty:
    """ease_factor → difficulty conversion (inverted scale)."""

    def test_high_ease_low_difficulty(self):
        """ease 2.5 (easiest SM-2) → D ≈ 2.0 (easiest FSRS)."""
        d = ease_to_difficulty(2.5)
        assert d == pytest.approx(2.0, abs=0.5)

    def test_low_ease_high_difficulty(self):
        """ease 1.3 (hardest SM-2) → D ≈ 8.0 (hardest FSRS)."""
        d = ease_to_difficulty(1.3)
        assert d == pytest.approx(8.0, abs=0.5)

    def test_medium_ease(self):
        """ease 1.9 (midpoint) → D ≈ 5.0."""
        d = ease_to_difficulty(1.9)
        assert 3.0 < d < 7.0

    def test_ease_above_max_clamped(self):
        """ease > 2.5 is clamped to 2.5."""
        d = ease_to_difficulty(3.0)
        assert d == ease_to_difficulty(2.5)

    def test_ease_below_min_clamped(self):
        """ease < 1.3 is clamped to 1.3."""
        d = ease_to_difficulty(1.0)
        assert d == ease_to_difficulty(1.3)

    def test_monotonic_decrease(self):
        """Higher ease → lower difficulty (monotonic)."""
        d1 = ease_to_difficulty(1.3)
        d2 = ease_to_difficulty(1.9)
        d3 = ease_to_difficulty(2.5)
        assert d1 > d2 > d3


class TestMapStatus:
    """SM-2 status → FSRS state mapping."""

    def test_new(self):
        assert map_status("new") == "new"

    def test_learning(self):
        assert map_status("learning") == "learning"

    def test_review(self):
        assert map_status("review") == "review"

    def test_suspended_maps_to_review(self):
        assert map_status("suspended") == "review"

    def test_unknown_maps_to_new(self):
        assert map_status("unknown_status") == "new"


class TestConvertCard:
    """Full card conversion from srs_card dict to fsrs_card dict."""

    def _make_srs_card(self, **overrides) -> dict:
        base = {
            "id": "srs-card-1",
            "user_id": "user-1",
            "problem_id": "prob-1",
            "topic_id": "topic-1",
            "card_type": "problem",
            "ease_factor": 2.5,
            "interval_days": 10.0,
            "repetition_count": 5,
            "next_review_date": "2025-07-01",
            "last_review_date": "2025-06-21",
            "status": "review",
            "created_at": "2025-06-01T00:00:00+00:00",
        }
        base.update(overrides)
        return base

    def test_basic_conversion(self):
        """Standard review card converts correctly."""
        srs = self._make_srs_card()
        fsrs = convert_card(srs, prototype_id="proto-1")

        assert fsrs["user_id"] == "user-1"
        assert fsrs["problem_id"] == "prob-1"
        assert fsrs["prototype_id"] == "proto-1"
        assert fsrs["card_type"] == "problem"
        assert fsrs["state"] == "review"
        assert fsrs["reps"] == 5
        assert fsrs["lapses"] == 0
        assert fsrs["stability"] == 10.0
        # ease 2.5 → low difficulty
        assert fsrs["difficulty"] == pytest.approx(2.0, abs=0.5)
        assert "2025-07-01" in fsrs["due"]

    def test_new_card(self):
        """New card keeps state='new'."""
        srs = self._make_srs_card(status="new", ease_factor=2.5, interval_days=1.0)
        fsrs = convert_card(srs, prototype_id=None)
        assert fsrs["state"] == "new"
        assert fsrs["prototype_id"] is None

    def test_suspended_becomes_review(self):
        """Suspended card becomes review."""
        srs = self._make_srs_card(status="suspended")
        fsrs = convert_card(srs, prototype_id=None)
        assert fsrs["state"] == "review"

    def test_hard_card_high_difficulty(self):
        """Card with low ease → high difficulty."""
        srs = self._make_srs_card(ease_factor=1.3)
        fsrs = convert_card(srs, prototype_id=None)
        assert fsrs["difficulty"] == pytest.approx(8.0, abs=0.5)

    def test_stability_equals_interval(self):
        """stability = interval_days from SM-2."""
        srs = self._make_srs_card(interval_days=30.0)
        fsrs = convert_card(srs, prototype_id=None)
        assert fsrs["stability"] == 30.0

    def test_unique_ids(self):
        """Each converted card gets a unique UUID."""
        srs = self._make_srs_card()
        fsrs1 = convert_card(srs, prototype_id=None)
        fsrs2 = convert_card(srs, prototype_id=None)
        assert fsrs1["id"] != fsrs2["id"]

    def test_missing_fields_use_defaults(self):
        """Missing/None fields fall back to safe defaults."""
        srs = self._make_srs_card(
            ease_factor=None,
            interval_days=None,
            repetition_count=None,
            status=None,
            next_review_date=None,
            last_review_date=None,
        )
        fsrs = convert_card(srs, prototype_id=None)
        # Should not crash; uses defaults
        assert fsrs["difficulty"] == pytest.approx(2.0, abs=0.5)  # default ease 2.5
        assert fsrs["stability"] == 1.0  # default interval 1.0
        assert fsrs["reps"] == 0
        assert fsrs["state"] == "new"
        assert fsrs["last_review"] is None

    def test_scheduled_days_from_interval(self):
        """scheduled_days derived from interval_days."""
        srs = self._make_srs_card(interval_days=7.5)
        fsrs = convert_card(srs, prototype_id=None)
        assert fsrs["scheduled_days"] == 8  # rounded

    def test_last_review_preserved(self):
        """last_review_date is carried over as ISO string."""
        srs = self._make_srs_card(last_review_date="2025-06-21")
        fsrs = convert_card(srs, prototype_id=None)
        assert "2025-06-21" in fsrs["last_review"]
