-- Migration 018: Allow long parser answers for Part 2 problems.
-- Some Shkolkovo task 13+ answers contain formulas and intervals that exceed
-- the old 50-character limit.

ALTER TABLE problems
    ALTER COLUMN correct_answer TYPE TEXT;

ALTER TABLE user_problem_attempts
    ALTER COLUMN user_answer TYPE TEXT;
