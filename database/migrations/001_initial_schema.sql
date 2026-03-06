-- =============================================================================
-- Repeatify — Initial Schema
-- Migration: 001_initial_schema.sql
-- Tables: users, topics, topic_dependencies, cards, user_card_progress,
--         review_logs, user_topic_mastery, study_sessions, daily_activity
-- =============================================================================

-- Enable UUID extension (already available in Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- ENUM types
-- =============================================================================

CREATE TYPE card_type AS ENUM ('basic_qa', 'step_by_step');

CREATE TYPE fsrs_state AS ENUM ('new', 'learning', 'review', 'relearning');

CREATE TYPE session_type AS ENUM ('daily', 'topic_focused', 'diagnostic');

CREATE TYPE study_plan_type AS ENUM ('relaxed', 'standard', 'intensive', 'sprint');

CREATE TYPE relationship_type AS ENUM ('prerequisite', 'related', 'part_of');

-- =============================================================================
-- users
-- Extends auth.users (Supabase Auth) with app-specific profile data.
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    id                  UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name        TEXT,
    exam_date           DATE,
    daily_goal_minutes  SMALLINT NOT NULL DEFAULT 30 CHECK (daily_goal_minutes > 0),
    study_plan_type     study_plan_type NOT NULL DEFAULT 'standard',
    current_streak      INTEGER NOT NULL DEFAULT 0 CHECK (current_streak >= 0),
    longest_streak      INTEGER NOT NULL DEFAULT 0 CHECK (longest_streak >= 0),
    total_cards_reviewed INTEGER NOT NULL DEFAULT 0 CHECK (total_cards_reviewed >= 0),
    timezone            TEXT NOT NULL DEFAULT 'UTC',
    onboarding_done     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- topics
-- Knowledge graph nodes. level: 0 = root section, 1 = topic, 2 = subtopic.
-- =============================================================================

CREATE TABLE IF NOT EXISTS topics (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code             TEXT NOT NULL UNIQUE,
    title            TEXT NOT NULL,
    description      TEXT,
    difficulty       NUMERIC(3, 2) NOT NULL DEFAULT 0.5
                         CHECK (difficulty >= 0.0 AND difficulty <= 1.0),
    level            SMALLINT NOT NULL DEFAULT 1 CHECK (level IN (0, 1, 2)),
    parent_id        UUID REFERENCES topics(id) ON DELETE SET NULL,
    ege_task_numbers INTEGER[] NOT NULL DEFAULT '{}',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_topics_parent_id ON topics(parent_id);
CREATE INDEX IF NOT EXISTS idx_topics_level     ON topics(level);
CREATE INDEX IF NOT EXISTS idx_topics_code      ON topics(code);

-- =============================================================================
-- topic_dependencies
-- Directed edges in the knowledge graph (DAG). weight in [0.0, 1.0].
-- prerequisite_topic_id → dependent_topic_id means "learn A before B".
-- =============================================================================

CREATE TABLE IF NOT EXISTS topic_dependencies (
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prerequisite_topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    dependent_topic_id    UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    weight                NUMERIC(3, 2) NOT NULL DEFAULT 1.0
                              CHECK (weight > 0.0 AND weight <= 1.0),
    relationship_type     relationship_type NOT NULL DEFAULT 'prerequisite',
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (prerequisite_topic_id, dependent_topic_id)
);

CREATE INDEX IF NOT EXISTS idx_topic_dep_prereq   ON topic_dependencies(prerequisite_topic_id);
CREATE INDEX IF NOT EXISTS idx_topic_dep_dependent ON topic_dependencies(dependent_topic_id);

-- =============================================================================
-- cards
-- Flashcard content. Supports two types:
--   basic_qa     – question + answer text/image
--   step_by_step – question + solution_steps JSONB array
-- =============================================================================

CREATE TABLE IF NOT EXISTS cards (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_id           UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    card_type          card_type NOT NULL DEFAULT 'basic_qa',
    question_text      TEXT NOT NULL,
    answer_text        TEXT,
    question_image_url TEXT,
    answer_image_url   TEXT,
    -- JSONB array of step objects: {step_number, title, text, latex, hint}
    solution_steps     JSONB,
    -- JSONB array of hint strings or {level, text} objects
    hints              JSONB NOT NULL DEFAULT '[]',
    difficulty         NUMERIC(3, 2) NOT NULL DEFAULT 0.5
                           CHECK (difficulty >= 0.0 AND difficulty <= 1.0),
    ege_task_number    SMALLINT CHECK (ege_task_number >= 1 AND ege_task_number <= 19),
    source             TEXT,
    is_active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cards_topic_id        ON cards(topic_id);
CREATE INDEX IF NOT EXISTS idx_cards_card_type        ON cards(card_type);
CREATE INDEX IF NOT EXISTS idx_cards_ege_task_number  ON cards(ege_task_number);
CREATE INDEX IF NOT EXISTS idx_cards_is_active        ON cards(is_active);

-- =============================================================================
-- user_card_progress
-- Per-user FSRS state for each card.
-- =============================================================================

CREATE TABLE IF NOT EXISTS user_card_progress (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    card_id          UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    fsrs_state       fsrs_state NOT NULL DEFAULT 'new',
    stability        NUMERIC(10, 4) NOT NULL DEFAULT 0,
    difficulty       NUMERIC(5, 4) NOT NULL DEFAULT 0.3,
    due_date         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_reviewed_at TIMESTAMPTZ,
    interval_days    NUMERIC(10, 4) NOT NULL DEFAULT 0,
    reps             INTEGER NOT NULL DEFAULT 0 CHECK (reps >= 0),
    lapses           INTEGER NOT NULL DEFAULT 0 CHECK (lapses >= 0),
    -- FIRe: implicit credit accumulated from dependent topic answers
    implicit_credit  NUMERIC(6, 4) NOT NULL DEFAULT 0,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (user_id, card_id)
);

CREATE INDEX IF NOT EXISTS idx_ucp_user_id         ON user_card_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_ucp_user_due         ON user_card_progress(user_id, due_date);
CREATE INDEX IF NOT EXISTS idx_ucp_user_state       ON user_card_progress(user_id, fsrs_state);
CREATE INDEX IF NOT EXISTS idx_ucp_card_id          ON user_card_progress(card_id);

-- =============================================================================
-- review_logs
-- Immutable record of every review event.
-- =============================================================================

CREATE TABLE IF NOT EXISTS review_logs (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    card_id          UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    session_id       UUID,  -- FK to study_sessions added after that table
    rating           SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 4),
    -- 1=Again, 2=Hard, 3=Good, 4=Easy
    fsrs_state_before fsrs_state NOT NULL,
    fsrs_state_after  fsrs_state NOT NULL,
    stability_before  NUMERIC(10, 4),
    stability_after   NUMERIC(10, 4),
    interval_before   NUMERIC(10, 4),
    interval_after    NUMERIC(10, 4),
    due_date_after    TIMESTAMPTZ,
    hints_used        SMALLINT NOT NULL DEFAULT 0 CHECK (hints_used >= 0),
    response_time_ms  INTEGER CHECK (response_time_ms >= 0),
    reviewed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_review_logs_user_id    ON review_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_review_logs_card_id    ON review_logs(card_id);
CREATE INDEX IF NOT EXISTS idx_review_logs_session_id ON review_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_review_logs_reviewed_at ON review_logs(reviewed_at);

-- =============================================================================
-- user_topic_mastery
-- Aggregated mastery per topic per user. Drives FIRe propagation.
-- =============================================================================

CREATE TABLE IF NOT EXISTS user_topic_mastery (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id        UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    mastery_level   NUMERIC(5, 4) NOT NULL DEFAULT 0
                        CHECK (mastery_level >= 0.0 AND mastery_level <= 1.0),
    -- FIRe: accumulated credit from answers on dependent topics
    implicit_credit NUMERIC(6, 4) NOT NULL DEFAULT 0,
    cards_total     INTEGER NOT NULL DEFAULT 0 CHECK (cards_total >= 0),
    cards_new       INTEGER NOT NULL DEFAULT 0 CHECK (cards_new >= 0),
    cards_learning  INTEGER NOT NULL DEFAULT 0 CHECK (cards_learning >= 0),
    cards_review    INTEGER NOT NULL DEFAULT 0 CHECK (cards_review >= 0),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (user_id, topic_id)
);

CREATE INDEX IF NOT EXISTS idx_utm_user_id  ON user_topic_mastery(user_id);
CREATE INDEX IF NOT EXISTS idx_utm_topic_id ON user_topic_mastery(topic_id);

-- =============================================================================
-- study_sessions
-- One record per training session.
-- =============================================================================

CREATE TABLE IF NOT EXISTS study_sessions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_type        session_type NOT NULL DEFAULT 'daily',
    -- For topic_focused sessions: which topic was targeted
    topic_id            UUID REFERENCES topics(id) ON DELETE SET NULL,
    cards_reviewed      INTEGER NOT NULL DEFAULT 0 CHECK (cards_reviewed >= 0),
    cards_correct       INTEGER NOT NULL DEFAULT 0 CHECK (cards_correct >= 0),
    cards_incorrect     INTEGER NOT NULL DEFAULT 0 CHECK (cards_incorrect >= 0),
    daily_goal_minutes  SMALLINT,
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at            TIMESTAMPTZ,
    duration_seconds    INTEGER CHECK (duration_seconds >= 0)
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id    ON study_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON study_sessions(user_id, started_at);

-- Add FK from review_logs → study_sessions now that study_sessions exists
ALTER TABLE review_logs
    ADD CONSTRAINT fk_review_logs_session
    FOREIGN KEY (session_id) REFERENCES study_sessions(id) ON DELETE SET NULL;

-- =============================================================================
-- daily_activity
-- One row per (user, date) for streak calculation and heatmap.
-- =============================================================================

CREATE TABLE IF NOT EXISTS daily_activity (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_date     DATE NOT NULL,
    cards_reviewed    INTEGER NOT NULL DEFAULT 0 CHECK (cards_reviewed >= 0),
    minutes_studied   NUMERIC(6, 2) NOT NULL DEFAULT 0 CHECK (minutes_studied >= 0),
    goal_reached      BOOLEAN NOT NULL DEFAULT FALSE,
    streak_freeze_used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (user_id, activity_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_activity_user_id ON daily_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_activity_date    ON daily_activity(user_id, activity_date DESC);

-- =============================================================================
-- Triggers: auto-update updated_at columns
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_cards_updated_at
    BEFORE UPDATE ON cards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_ucp_updated_at
    BEFORE UPDATE ON user_card_progress
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_utm_updated_at
    BEFORE UPDATE ON user_topic_mastery
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_daily_activity_updated_at
    BEFORE UPDATE ON daily_activity
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
