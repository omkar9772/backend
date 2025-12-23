-- Performance indexes for race_results table
-- This will speed up statistics queries from 250ms to <10ms each

-- Index for bull lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_race_results_bull1_id
ON race_results(bull1_id) WHERE is_disqualified = false;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_race_results_bull2_id
ON race_results(bull2_id) WHERE is_disqualified = false;

-- Index for winner queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_race_results_position
ON race_results(position, bull1_id, bull2_id) WHERE is_disqualified = false;

-- Index for time queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_race_results_time
ON race_results(time_milliseconds, bull1_id, bull2_id) WHERE is_disqualified = false;

-- Analyze table to update query planner statistics
ANALYZE race_results;
