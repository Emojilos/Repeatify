-- ============================================================================
-- 005_prototypes_and_videos.sql
-- Creates prototypes and video_resources tables for v2 prototype-based learning
-- ============================================================================

-- ============================================================================
-- TABLE: prototypes
-- Task prototypes (subtypes within each of the 19 exam tasks)
-- ============================================================================

CREATE TABLE prototypes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_number INTEGER NOT NULL CHECK (task_number >= 1 AND task_number <= 19),
    prototype_code VARCHAR(10) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    difficulty_within_task VARCHAR(10) NOT NULL CHECK (difficulty_within_task IN ('easy', 'medium', 'hard')),
    estimated_study_minutes INTEGER,
    theory_markdown TEXT,
    key_formulas JSONB DEFAULT '[]'::jsonb,
    solution_algorithm JSONB DEFAULT '[]'::jsonb,
    common_mistakes JSONB DEFAULT '[]'::jsonb,
    related_prototypes JSONB DEFAULT '[]'::jsonb,
    order_index INTEGER NOT NULL DEFAULT 0
);

-- ============================================================================
-- TABLE: video_resources
-- YouTube videos linked to prototypes
-- ============================================================================

CREATE TABLE video_resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prototype_id UUID NOT NULL REFERENCES prototypes(id) ON DELETE CASCADE,
    youtube_video_id VARCHAR(20) NOT NULL,
    title VARCHAR(300) NOT NULL,
    channel_name VARCHAR(100),
    duration_seconds INTEGER,
    timestamps JSONB DEFAULT '[]'::jsonb,
    order_index INTEGER NOT NULL DEFAULT 0
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_prototypes_task_number ON prototypes(task_number);
CREATE INDEX idx_video_resources_prototype ON video_resources(prototype_id);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE prototypes ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_resources ENABLE ROW LEVEL SECURITY;

-- Prototypes: SELECT for authenticated users
CREATE POLICY "prototypes_select_authenticated"
    ON prototypes
    FOR SELECT
    TO authenticated
    USING (true);

-- Prototypes: INSERT/UPDATE/DELETE for service_role only
CREATE POLICY "prototypes_insert_service_role"
    ON prototypes
    FOR INSERT
    TO service_role
    WITH CHECK (true);

CREATE POLICY "prototypes_update_service_role"
    ON prototypes
    FOR UPDATE
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "prototypes_delete_service_role"
    ON prototypes
    FOR DELETE
    TO service_role
    USING (true);

-- Video resources: SELECT for authenticated users
CREATE POLICY "video_resources_select_authenticated"
    ON video_resources
    FOR SELECT
    TO authenticated
    USING (true);

-- Video resources: INSERT/UPDATE/DELETE for service_role only
CREATE POLICY "video_resources_insert_service_role"
    ON video_resources
    FOR INSERT
    TO service_role
    WITH CHECK (true);

CREATE POLICY "video_resources_update_service_role"
    ON video_resources
    FOR UPDATE
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "video_resources_delete_service_role"
    ON video_resources
    FOR DELETE
    TO service_role
    USING (true);
