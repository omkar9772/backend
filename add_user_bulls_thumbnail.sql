-- Add thumbnail_url column to user_bulls_sell table
-- For consistent thumbnail support across all image types

ALTER TABLE user_bulls_sell ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR(500);

-- Add index for faster queries (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_user_bulls_thumbnail_url ON user_bulls_sell(thumbnail_url) WHERE thumbnail_url IS NOT NULL;

-- Analyze table to update statistics
ANALYZE user_bulls_sell;
