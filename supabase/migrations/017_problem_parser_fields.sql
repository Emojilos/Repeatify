-- Migration 017: Store parser metadata for imported Shkolkovo problems.
-- These fields mirror data/raw/shkolkovo/task_N.json so imports do not lose
-- categorization, source image references, or parse quality information.

ALTER TABLE problems
    ADD COLUMN IF NOT EXISTS category VARCHAR(200),
    ADD COLUMN IF NOT EXISTS subcategory VARCHAR(200),
    ADD COLUMN IF NOT EXISTS source_image_urls JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS parse_status VARCHAR(20) NOT NULL DEFAULT 'ok'
        CHECK (parse_status IN ('ok', 'partial')),
    ADD COLUMN IF NOT EXISTS parse_errors JSONB DEFAULT '[]'::jsonb;

CREATE INDEX IF NOT EXISTS idx_problems_source_id ON problems(source, source_id);
CREATE INDEX IF NOT EXISTS idx_problems_category ON problems(task_number, category, subcategory);
CREATE INDEX IF NOT EXISTS idx_problems_parse_status ON problems(parse_status);
