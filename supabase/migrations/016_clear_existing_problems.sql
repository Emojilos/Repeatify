-- Migration 016: Clear existing problem bank.
-- Removes legacy problem records before importing a new parsed dataset.
-- Dependent attempts and SRS cards are removed by ON DELETE CASCADE.

DELETE FROM problems;
