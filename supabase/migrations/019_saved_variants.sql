-- Migration 019: Store saved print variants per user.

CREATE TABLE IF NOT EXISTS saved_variants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    task_number INTEGER NOT NULL CHECK (task_number >= 1 AND task_number <= 19),
    problem_count INTEGER NOT NULL CHECK (problem_count >= 1 AND problem_count <= 100),
    seed INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_saved_variants_user_created
    ON saved_variants(user_id, created_at DESC);

ALTER TABLE saved_variants ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'saved_variants'
          AND policyname = 'saved_variants_select_own'
    ) THEN
        CREATE POLICY "saved_variants_select_own" ON saved_variants
            FOR SELECT USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'saved_variants'
          AND policyname = 'saved_variants_insert_own'
    ) THEN
        CREATE POLICY "saved_variants_insert_own" ON saved_variants
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'saved_variants'
          AND policyname = 'saved_variants_delete_own'
    ) THEN
        CREATE POLICY "saved_variants_delete_own" ON saved_variants
            FOR DELETE USING (auth.uid() = user_id);
    END IF;
END $$;
