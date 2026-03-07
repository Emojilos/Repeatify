-- =============================================================================
-- Repeatify — Row Level Security Policies
-- Migration: 002_rls_policies.sql
--
-- Strategy:
--   • User-owned tables (users, user_card_progress, review_logs,
--     user_topic_mastery, study_sessions, daily_activity):
--       – RLS enabled
--       – SELECT/INSERT/UPDATE restricted to the row owner (auth.uid())
--       – No direct DELETE exposed to users
--   • Public content tables (topics, topic_dependencies, cards):
--       – RLS enabled
--       – Authenticated users may SELECT
--       – INSERT/UPDATE/DELETE requires service role (bypasses RLS)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Helper: authenticated user check
-- ---------------------------------------------------------------------------

-- Supabase automatically sets auth.uid() for requests made via the SDK.
-- The service_role key bypasses RLS entirely, so we never need to write
-- a "service role" policy — it just works.

-- =============================================================================
-- 1. users
-- =============================================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users: owner can select"
    ON users FOR SELECT
    USING (id = auth.uid());

CREATE POLICY "users: owner can insert"
    ON users FOR INSERT
    WITH CHECK (id = auth.uid());

CREATE POLICY "users: owner can update"
    ON users FOR UPDATE
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());

-- =============================================================================
-- 2. user_card_progress
-- =============================================================================

ALTER TABLE user_card_progress ENABLE ROW LEVEL SECURITY;

CREATE POLICY "ucp: owner can select"
    ON user_card_progress FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "ucp: owner can insert"
    ON user_card_progress FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "ucp: owner can update"
    ON user_card_progress FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- =============================================================================
-- 3. review_logs  (append-only from the client's perspective)
-- =============================================================================

ALTER TABLE review_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "review_logs: owner can select"
    ON review_logs FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "review_logs: owner can insert"
    ON review_logs FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- No UPDATE policy: review_logs are immutable once written.

-- =============================================================================
-- 4. user_topic_mastery
-- =============================================================================

ALTER TABLE user_topic_mastery ENABLE ROW LEVEL SECURITY;

CREATE POLICY "utm: owner can select"
    ON user_topic_mastery FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "utm: owner can insert"
    ON user_topic_mastery FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "utm: owner can update"
    ON user_topic_mastery FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- =============================================================================
-- 5. study_sessions
-- =============================================================================

ALTER TABLE study_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "sessions: owner can select"
    ON study_sessions FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "sessions: owner can insert"
    ON study_sessions FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "sessions: owner can update"
    ON study_sessions FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- =============================================================================
-- 6. daily_activity
-- =============================================================================

ALTER TABLE daily_activity ENABLE ROW LEVEL SECURITY;

CREATE POLICY "daily_activity: owner can select"
    ON daily_activity FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "daily_activity: owner can insert"
    ON daily_activity FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "daily_activity: owner can update"
    ON daily_activity FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- =============================================================================
-- 7. topics  — public read, service-role write
-- =============================================================================

ALTER TABLE topics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "topics: authenticated can select"
    ON topics FOR SELECT
    TO authenticated
    USING (true);

-- No INSERT/UPDATE/DELETE policy for authenticated role.
-- Service role bypasses RLS and may write freely.

-- =============================================================================
-- 8. topic_dependencies  — public read, service-role write
-- =============================================================================

ALTER TABLE topic_dependencies ENABLE ROW LEVEL SECURITY;

CREATE POLICY "topic_dependencies: authenticated can select"
    ON topic_dependencies FOR SELECT
    TO authenticated
    USING (true);

-- =============================================================================
-- 9. cards  — public read, service-role write
-- =============================================================================

ALTER TABLE cards ENABLE ROW LEVEL SECURITY;

CREATE POLICY "cards: authenticated can select"
    ON cards FOR SELECT
    TO authenticated
    USING (true);
