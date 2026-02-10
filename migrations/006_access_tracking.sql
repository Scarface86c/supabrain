-- Migration: Add access tracking enhancements for SupaStats
-- Purpose: Complete analytics infrastructure
-- Part of: SupaStats Analytics Dashboard
-- Note: access_count, last_accessed, and memory_access_log already exist from prior migrations

-- Add access frequency score column (new)
ALTER TABLE memories 
ADD COLUMN IF NOT EXISTS access_frequency_score FLOAT DEFAULT 0.0;

-- Add indexes for frequently accessed memories (helps with analytics queries)
CREATE INDEX IF NOT EXISTS idx_memories_access_count 
ON memories(access_count DESC);

CREATE INDEX IF NOT EXISTS idx_memories_last_accessed 
ON memories(last_accessed DESC);

CREATE INDEX IF NOT EXISTS idx_memories_access_frequency 
ON memories(access_frequency_score DESC);

-- Create query analytics table (tracks search effectiveness)
CREATE TABLE IF NOT EXISTS query_analytics (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    results_count INTEGER,
    avg_similarity FLOAT,
    queried_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_query_analytics_agent 
ON query_analytics(agent_id);

CREATE INDEX IF NOT EXISTS idx_query_analytics_queried_at 
ON query_analytics(queried_at DESC);

-- Add comments
COMMENT ON COLUMN memories.access_frequency_score IS 'Computed score based on access frequency and recency (decays over time)';
COMMENT ON TABLE query_analytics IS 'Tracks search queries and their effectiveness for performance tuning';
