-- ============================================================================
-- 001_initial_schema.sql
-- Repeatify: ЕГЭ Math Trainer — Initial Database Schema
-- Creates all ENUM types, tables, foreign keys, indexes
-- ============================================================================

-- Enable UUID extension (usually enabled by default in Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- ENUM TYPES
-- ============================================================================

CREATE TYPE difficulty_level AS ENUM ('basic', 'medium', 'hard');

CREATE TYPE problem_difficulty AS ENUM ('basic', 'medium', 'hard', 'olympiad');

CREATE TYPE content_type AS ENUM ('framework', 'inquiry', 'relationships', 'elaboration', 'summary');

CREATE TYPE card_type AS ENUM ('problem', 'concept', 'formula');

CREATE TYPE card_status AS ENUM ('new', 'learning', 'review', 'suspended');

CREATE TYPE session_type AS ENUM ('srs_review', 'fire_learning', 'practice');

CREATE TYPE self_assessment AS ENUM ('again', 'hard', 'good', 'easy');

CREATE TYPE relationship_type AS ENUM ('prerequisite', 'related', 'applies_to');

-- ============================================================================
-- TABLE: users
-- Extends Supabase Auth with application-specific fields
-- ============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name VARCHAR(100),
    exam_date DATE,
    target_score INTEGER CHECK (target_score >= 27 AND target_score <= 100),
    current_xp INTEGER NOT NULL DEFAULT 0,
    current_level INTEGER NOT NULL DEFAULT 1,
    current_streak INTEGER NOT NULL DEFAULT 0,
    longest_streak INTEGER NOT NULL DEFAULT 0,
    last_activity_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- TABLE: topics
-- Catalog of all 19 exam task types and subtopics
-- ============================================================================

CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_number INTEGER NOT NULL CHECK (task_number >= 1 AND task_number <= 19),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    parent_topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
    difficulty_level difficulty_level NOT NULL DEFAULT 'medium',
    max_points INTEGER NOT NULL,
    estimated_study_hours FLOAT,
    order_index INTEGER NOT NULL DEFAULT 0
);

-- ============================================================================
-- TABLE: theory_content
-- FIRe-flow educational materials (Framework, Inquiry, Relationships, Elaboration)
-- ============================================================================

CREATE TABLE theory_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    content_type content_type NOT NULL,
    content_markdown TEXT NOT NULL,
    visual_assets JSONB DEFAULT '[]'::jsonb,
    order_index INTEGER NOT NULL DEFAULT 0
);

-- ============================================================================
-- TABLE: problems
-- Problem/task database covering all 19 exam types
-- ============================================================================

CREATE TABLE problems (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    task_number INTEGER NOT NULL CHECK (task_number >= 1 AND task_number <= 19),
    difficulty problem_difficulty NOT NULL DEFAULT 'medium',
    problem_text TEXT NOT NULL,
    problem_images JSONB DEFAULT '[]'::jsonb,
    correct_answer VARCHAR(50),
    answer_tolerance FLOAT NOT NULL DEFAULT 0,
    solution_markdown TEXT,
    solution_images JSONB DEFAULT '[]'::jsonb,
    hints JSONB DEFAULT '[]'::jsonb,
    source VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- TABLE: user_problem_attempts
-- Records every problem-solving attempt by users
-- ============================================================================

CREATE TABLE user_problem_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    problem_id UUID NOT NULL REFERENCES problems(id) ON DELETE CASCADE,
    user_answer VARCHAR(50),
    is_correct BOOLEAN NOT NULL,
    self_assessment self_assessment,
    time_spent_seconds INTEGER,
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- TABLE: srs_cards
-- Spaced Repetition System cards (SM-2 algorithm)
-- ============================================================================

CREATE TABLE srs_cards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    problem_id UUID REFERENCES problems(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    card_type card_type NOT NULL DEFAULT 'problem',
    ease_factor FLOAT NOT NULL DEFAULT 2.5,
    interval_days FLOAT NOT NULL DEFAULT 1,
    repetition_count INTEGER NOT NULL DEFAULT 0,
    next_review_date DATE NOT NULL DEFAULT CURRENT_DATE,
    last_review_date DATE,
    status card_status NOT NULL DEFAULT 'new',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- TABLE: user_topic_progress
-- Tracks completion of FIRe-flow stages and topic mastery
-- ============================================================================

CREATE TABLE user_topic_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    fire_framework_completed BOOLEAN NOT NULL DEFAULT false,
    fire_inquiry_completed BOOLEAN NOT NULL DEFAULT false,
    fire_relationships_completed BOOLEAN NOT NULL DEFAULT false,
    fire_elaboration_completed BOOLEAN NOT NULL DEFAULT false,
    fire_completed_at TIMESTAMPTZ,
    strength_score FLOAT NOT NULL DEFAULT 0.0 CHECK (strength_score >= 0.0 AND strength_score <= 1.0),
    total_attempts INTEGER NOT NULL DEFAULT 0,
    correct_attempts INTEGER NOT NULL DEFAULT 0,
    last_practiced_at TIMESTAMPTZ,
    UNIQUE (user_id, topic_id)
);

-- ============================================================================
-- TABLE: user_sessions
-- Records individual study/practice sessions
-- ============================================================================

CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_type session_type NOT NULL,
    problems_attempted INTEGER NOT NULL DEFAULT 0,
    problems_correct INTEGER NOT NULL DEFAULT 0,
    xp_earned INTEGER NOT NULL DEFAULT 0,
    duration_seconds INTEGER,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- ============================================================================
-- TABLE: user_daily_activity
-- Daily aggregated activity for streaks and heatmap
-- ============================================================================

CREATE TABLE user_daily_activity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_date DATE NOT NULL DEFAULT CURRENT_DATE,
    sessions_completed INTEGER NOT NULL DEFAULT 0,
    problems_solved INTEGER NOT NULL DEFAULT 0,
    xp_earned INTEGER NOT NULL DEFAULT 0,
    streak_maintained BOOLEAN NOT NULL DEFAULT false,
    UNIQUE (user_id, activity_date)
);

-- ============================================================================
-- TABLE: topic_relationships
-- Connections between topics (FIRe R-stage: Relationships)
-- ============================================================================

CREATE TABLE topic_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    target_topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    relationship_type relationship_type NOT NULL,
    description VARCHAR(300)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_srs_cards_next_review ON srs_cards(user_id, next_review_date, status);
CREATE INDEX idx_attempts_user_problem ON user_problem_attempts(user_id, problem_id, attempted_at);
CREATE INDEX idx_daily_activity_user ON user_daily_activity(user_id, activity_date);
CREATE INDEX idx_problems_topic ON problems(topic_id, difficulty);
