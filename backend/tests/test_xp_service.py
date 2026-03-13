"""Unit tests for the XP / level service."""

from app.services.xp_service import (
    LEVEL_TABLE,
    XP_FIRE_COMPLETE,
    XP_PART1_CORRECT,
    XP_PART2_CORRECT,
    XP_SESSION_BONUS,
    XP_STREAK_BONUS,
    calculate_level,
    calculate_problem_xp,
    xp_for_next_level,
)

# --- calculate_level ---


class TestCalculateLevel:
    def test_zero_xp(self):
        level, name = calculate_level(0)
        assert level == 1
        assert name == "Новичок"

    def test_boundary_100(self):
        level, _ = calculate_level(100)
        assert level == 2

    def test_just_below_boundary(self):
        level, _ = calculate_level(99)
        assert level == 1

    def test_level_3(self):
        level, name = calculate_level(300)
        assert level == 3
        assert name == "Практикант"

    def test_mid_level(self):
        level, _ = calculate_level(450)
        assert level == 3

    def test_max_level(self):
        level, name = calculate_level(10000)
        assert level == 10
        assert name == "Бог ЕГЭ"

    def test_above_max(self):
        level, _ = calculate_level(99999)
        assert level == 10

    def test_all_boundaries(self):
        for min_xp, expected_level, expected_name in LEVEL_TABLE:
            level, name = calculate_level(min_xp)
            assert level == expected_level
            assert name == expected_name


# --- xp_for_next_level ---


class TestXpForNextLevel:
    def test_level_1(self):
        assert xp_for_next_level(0) == 100

    def test_level_1_midway(self):
        assert xp_for_next_level(50) == 100

    def test_level_2(self):
        assert xp_for_next_level(100) == 300

    def test_max_level(self):
        assert xp_for_next_level(10000) is None

    def test_above_max(self):
        assert xp_for_next_level(99999) is None


# --- calculate_problem_xp ---


class TestCalculateProblemXp:
    def test_correct_part1(self):
        assert calculate_problem_xp(True, 1, "good") == XP_PART1_CORRECT

    def test_correct_part1_any_assessment(self):
        for assessment in ("again", "hard", "good", "easy"):
            assert calculate_problem_xp(True, 5, assessment) == XP_PART1_CORRECT

    def test_incorrect(self):
        assert calculate_problem_xp(False, 1, "good") == 0

    def test_correct_part2_good(self):
        assert calculate_problem_xp(True, 13, "good") == XP_PART2_CORRECT

    def test_correct_part2_easy(self):
        assert calculate_problem_xp(True, 15, "easy") == XP_PART2_CORRECT

    def test_correct_part2_hard(self):
        assert calculate_problem_xp(True, 14, "hard") == 0

    def test_correct_part2_again(self):
        assert calculate_problem_xp(True, 19, "again") == 0

    def test_incorrect_part2(self):
        assert calculate_problem_xp(False, 13, "good") == 0


# --- XP constants ---


class TestXpConstants:
    def test_part1(self):
        assert XP_PART1_CORRECT == 10

    def test_part2(self):
        assert XP_PART2_CORRECT == 25

    def test_fire(self):
        assert XP_FIRE_COMPLETE == 50

    def test_session(self):
        assert XP_SESSION_BONUS == 30

    def test_streak(self):
        assert XP_STREAK_BONUS == 5


# --- level table consistency ---


class TestLevelTable:
    def test_sorted_ascending(self):
        xps = [t[0] for t in LEVEL_TABLE]
        assert xps == sorted(xps)

    def test_unique_levels(self):
        levels = [t[1] for t in LEVEL_TABLE]
        assert len(levels) == len(set(levels))

    def test_starts_at_zero(self):
        assert LEVEL_TABLE[0][0] == 0

    def test_starts_at_level_1(self):
        assert LEVEL_TABLE[0][1] == 1
