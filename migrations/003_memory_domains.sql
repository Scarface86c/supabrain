-- SupaBrain Memory Domains
-- Migration: Add domain dimension (self/user/projects/world/system)

-- Add domain column
ALTER TABLE memories 
ADD COLUMN IF NOT EXISTS domain VARCHAR(20) DEFAULT 'general';

-- Create index
CREATE INDEX IF NOT EXISTS idx_memories_domain ON memories(domain);

-- Add constraint for valid domains
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint 
    WHERE conname = 'valid_memory_domain'
  ) THEN
    ALTER TABLE memories 
    ADD CONSTRAINT valid_memory_domain 
    CHECK (domain IN ('self', 'user', 'projects', 'world', 'system', 'general'));
  END IF;
END $$;

-- Migrate existing memories based on tags
UPDATE memories 
SET domain = 'self'
WHERE 'self' = ANY(tags);

UPDATE memories 
SET domain = 'user'
WHERE ('scarface' = ANY(tags) OR 'user' = ANY(tags))
  AND domain = 'general';

UPDATE memories 
SET domain = 'projects'
WHERE ('supabrain' = ANY(tags) OR 'bct' = ANY(tags) OR 'project' = ANY(tags))
  AND domain = 'general';

-- Comment
COMMENT ON COLUMN memories.domain IS 'Memory domain: self (about Scar) | user (about Scarface) | projects | world | system | general';
