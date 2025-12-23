-- Add thumbnail_url column to marketplace_listings table
-- For consistent thumbnail support across all image types

ALTER TABLE marketplace_listings ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR(500);

-- Add index for faster queries (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_marketplace_thumbnail_url ON marketplace_listings(thumbnail_url) WHERE thumbnail_url IS NOT NULL;

-- Analyze table to update statistics
ANALYZE marketplace_listings;
