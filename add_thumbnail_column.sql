-- Add thumbnail_url column to bulls table for optimized list loading
-- This enables serving 30-50 KB thumbnails instead of 300-500 KB originals

ALTER TABLE bulls ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR(500);

-- Add index for faster queries (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_bulls_thumbnail_url ON bulls(thumbnail_url) WHERE thumbnail_url IS NOT NULL;

-- Analyze table to update statistics
ANALYZE bulls;
