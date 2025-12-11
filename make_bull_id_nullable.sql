-- Migration: Make bull_id nullable in race_results table
-- This allows adding race participants without knowing bull information yet

ALTER TABLE race_results
ALTER COLUMN bull_id DROP NOT NULL;

-- Add a comment explaining this change
COMMENT ON COLUMN race_results.bull_id IS 'Bull ID - nullable to allow recording participants without bull information initially';
