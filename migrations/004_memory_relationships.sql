-- SupaBrain Memory Evolution
-- Migration: Add memory relationships for tracking belief evolution

-- Create relationships table
CREATE TABLE IF NOT EXISTS memory_relationships (
  id SERIAL PRIMARY KEY,
  from_memory_id INTEGER NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
  to_memory_id INTEGER NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
  relationship_type VARCHAR(30) NOT NULL,
  reason TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  -- Prevent duplicate relationships
  UNIQUE(from_memory_id, to_memory_id, relationship_type)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_relationships_from ON memory_relationships(from_memory_id);
CREATE INDEX IF NOT EXISTS idx_relationships_to ON memory_relationships(to_memory_id);
CREATE INDEX IF NOT EXISTS idx_relationships_type ON memory_relationships(relationship_type);

-- Add constraint for valid relationship types
ALTER TABLE memory_relationships 
ADD CONSTRAINT IF NOT EXISTS valid_relationship_type 
CHECK (relationship_type IN (
  'superseded_by',
  'evolved_to', 
  'originated_from',
  'contradicts',
  'reinforces',
  'inspired_by',
  'related_to'
));

-- Add versioning columns to memories
ALTER TABLE memories 
ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS superseded_by INTEGER REFERENCES memories(id),
ADD COLUMN IF NOT EXISTS is_current BOOLEAN DEFAULT true;

CREATE INDEX IF NOT EXISTS idx_memories_version ON memories(version);
CREATE INDEX IF NOT EXISTS idx_memories_is_current ON memories(is_current);

-- Comments
COMMENT ON TABLE memory_relationships IS 'Tracks evolution and connections between memories';
COMMENT ON COLUMN memory_relationships.relationship_type IS 'superseded_by | evolved_to | originated_from | contradicts | reinforces | inspired_by | related_to';
COMMENT ON COLUMN memories.version IS 'Version number for belief evolution tracking';
COMMENT ON COLUMN memories.superseded_by IS 'Points to newer version of this memory';
COMMENT ON COLUMN memories.is_current IS 'False if belief has been superseded';
