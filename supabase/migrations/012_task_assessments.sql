-- ============================================================================
-- 012_task_assessments.sql
-- Creates task_assessments table for knowledge-map-based study plans.
-- Alters user_study_plan to make time-based columns nullable.
-- ============================================================================

-- ============================================================================
-- TABLE: task_assessments
-- Stores results of 10-problem assessment tests per task_number
-- ============================================================================

CREATE TABLE task_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_number INTEGER NOT NULL CHECK (task_number >= 1 AND task_number <= 19),
    correct_count INTEGER NOT NULL DEFAULT 0,
    total_count INTEGER NOT NULL DEFAULT 10,
    assessed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_task_assessments_user_task ON task_assessments(user_id, task_number);
CREATE INDEX idx_task_assessments_user_latest ON task_assessments(user_id, assessed_at DESC);

-- ============================================================================
-- ALTER: user_study_plan — make time-based columns nullable
-- ============================================================================

ALTER TABLE user_study_plan
    ALTER COLUMN exam_date DROP NOT NULL,
    ALTER COLUMN hours_per_day DROP NOT NULL;

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE task_assessments ENABLE ROW LEVEL SECURITY;

-- User can read and insert own assessments
CREATE POLICY "task_assessments_select_own"
    ON task_assessments
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY "task_assessments_insert_own"
    ON task_assessments
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

-- Service role full access
CREATE POLICY "task_assessments_service_role"
    ON task_assessments
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
