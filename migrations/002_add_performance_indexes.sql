-- Migration 002: Add Performance Indexes
-- Date: 2026-02-08
-- Purpose: Add indexes for commonly queried columns to improve query performance
-- Expected impact: 10-100x speedup on filtered queries

-- Agent name filtering (most common query pattern)
CREATE INDEX IF NOT EXISTS idx_memories_agent_name ON memories(agent_name);

-- Temporal layer filtering (layer-based queries)
CREATE INDEX IF NOT EXISTS idx_memories_temporal_layer ON memories(temporal_layer);

-- Time-based queries (sorting, range queries)
CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at DESC);

-- Tag search (GIN index for array contains operations)
CREATE INDEX IF NOT EXISTS idx_memories_tags ON memories USING GIN(tags);

-- Domain filtering
CREATE INDEX IF NOT EXISTS idx_memories_domain ON memories(domain);

-- Status filtering (for review system)
CREATE INDEX IF NOT EXISTS idx_memories_status ON memories(status) 
WHERE status IS NOT NULL;

-- Composite index for common query pattern (agent + layer)
CREATE INDEX IF NOT EXISTS idx_memories_agent_layer ON memories(agent_name, temporal_layer);

-- Priority layer for hierarchical recall
CREATE INDEX IF NOT EXISTS idx_memories_priority_layer ON memories(priority_layer);

-- Importance score for sorting
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance_score DESC);

-- Analyze tables to update statistics
ANALYZE memories;

-- Verify indexes were created
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'memories'
ORDER BY indexname;
