-- ============================================================================
-- 006_fsrs_and_plan.sql
-- Creates fsrs_cards, diagnostic_results, user_study_plan tables
-- Alters problems (add prototype_id, source_url, source_id, content_hash)
-- Alters users (add hours_per_day)
-- ============================================================================

-- ============================================================================
-- TABLE: fsrs_cards
-- FSRS (Free Spaced Repetition Scheduler) cards — replaces SM-2 srs_cards
-- ============================================================================

CREATE TABLE fsrs_cards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    problem_id UUID REFERENCES problems(id) ON DELETE CASCADE,
    prototype_id UUID REFERENCES prototypes(id) ON DELETE CASCADE,
    card_type VARCHAR(20) NOT NULL CHECK (card_type IN ('problem', 'concept', 'formula')),
    difficulty FLOAT NOT NULL DEFAULT 0,
    stability FLOAT NOT NULL DEFAULT 0,
    due TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_review TIMESTAMPTZ,
    reps INTEGER NOT NULL DEFAULT 0,
    lapses INTEGER NOT NULL DEFAULT 0,
    state VARCHAR(20) NOT NULL DEFAULT 'new' CHECK (state IN ('new', 'learning', 'review', 'relearning')),
    scheduled_days INTEGER,
    elapsed_days INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- TABLE: diagnostic_results
-- Stores results of the 19-question diagnostic test
-- ============================================================================

CREATE TABLE diagnostic_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_number INTEGER NOT NULL CHECK (task_number >= 1 AND task_number <= 19),
    is_correct BOOLEAN,
    self_assessment VARCHAR(20),
    time_spent_seconds INTEGER,
    diagnosed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- TABLE: user_study_plan
-- Personalized study plans generated from diagnostic + user goals
-- ============================================================================

CREATE TABLE user_study_plan (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_score INTEGER,
    exam_date DATE,
    hours_per_day FLOAT,
    plan_data JSONB,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_active BOOLEAN NOT NULL DEFAULT true
);

-- ============================================================================
-- ALTER: problems — add prototype_id, source_url, source_id, content_hash
-- ============================================================================

ALTER TABLE problems
    ADD COLUMN prototype_id UUID REFERENCES prototypes(id) ON DELETE SET NULL,
    ADD COLUMN source_url VARCHAR(500),
    ADD COLUMN source_id VARCHAR(100),
    ADD COLUMN content_hash VARCHAR(64);

-- ============================================================================
-- ALTER: users — add hours_per_day
-- ============================================================================

ALTER TABLE users
    ADD COLUMN hours_per_day FLOAT DEFAULT 1.0;

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_fsrs_cards_user_due ON fsrs_cards(user_id, due, state);
CREATE INDEX idx_fsrs_cards_user_problem ON fsrs_cards(user_id, problem_id);
CREATE INDEX idx_fsrs_cards_user_prototype ON fsrs_cards(user_id, prototype_id);
CREATE INDEX idx_diagnostic_results_user ON diagnostic_results(user_id, task_number);
CREATE INDEX idx_user_study_plan_user ON user_study_plan(user_id, is_active);
CREATE INDEX idx_problems_prototype ON problems(prototype_id);
CREATE INDEX idx_problems_content_hash ON problems(content_hash);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE fsrs_cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagnostic_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_study_plan ENABLE ROW LEVEL SECURITY;

-- fsrs_cards: user can only access own cards
CREATE POLICY "fsrs_cards_select_own"
    ON fsrs_cards
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY "fsrs_cards_insert_own"
    ON fsrs_cards
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "fsrs_cards_update_own"
    ON fsrs_cards
    FOR UPDATE
    TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "fsrs_cards_delete_own"
    ON fsrs_cards
    FOR DELETE
    TO authenticated
    USING (user_id = auth.uid());

-- Service role full access to fsrs_cards
CREATE POLICY "fsrs_cards_service_role"
    ON fsrs_cards
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- diagnostic_results: user can SELECT and INSERT own (immutable — no UPDATE/DELETE)
CREATE POLICY "diagnostic_results_select_own"
    ON diagnostic_results
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY "diagnostic_results_insert_own"
    ON diagnostic_results
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

-- Service role full access to diagnostic_results
CREATE POLICY "diagnostic_results_service_role"
    ON diagnostic_results
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- user_study_plan: user can access own plans
CREATE POLICY "user_study_plan_select_own"
    ON user_study_plan
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY "user_study_plan_insert_own"
    ON user_study_plan
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "user_study_plan_update_own"
    ON user_study_plan
    FOR UPDATE
    TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Service role full access to user_study_plan
CREATE POLICY "user_study_plan_service_role"
    ON user_study_plan
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
