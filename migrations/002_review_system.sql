-- SupaBrain Review System
-- Migration: Add review/status management

-- Add status column
ALTER TABLE memories 
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';

-- Create index for status queries
CREATE INDEX IF NOT EXISTS idx_memories_status ON memories(status);

-- Add constraint for valid statuses
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint 
    WHERE conname = 'valid_memory_status'
  ) THEN
    ALTER TABLE memories 
    ADD CONSTRAINT valid_memory_status 
    CHECK (status IN ('active', 'expired', 'pending_review', 'archived', 'deleted'));
  END IF;
END $$;

-- Create review_log table for audit trail
CREATE TABLE IF NOT EXISTS review_log (
  id SERIAL PRIMARY KEY,
  memory_id INTEGER REFERENCES memories(id) ON DELETE CASCADE,
  decision VARCHAR(20) NOT NULL,  -- promote, extend, archive, delete
  old_layer VARCHAR(20),
  new_layer VARCHAR(20),
  reason TEXT,
  reviewed_by VARCHAR(100) DEFAULT 'agent',
  reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_review_log_memory ON review_log(memory_id);
CREATE INDEX IF NOT EXISTS idx_review_log_reviewed_at ON review_log(reviewed_at DESC);

-- Mark expired memories as needing review
UPDATE memories 
SET status = 'expired'
WHERE expires_at IS NOT NULL 
  AND expires_at < NOW() 
  AND status = 'active';

-- Comments
COMMENT ON COLUMN memories.status IS 'Memory status: active | expired | pending_review | archived | deleted';
COMMENT ON TABLE review_log IS 'Audit log of memory review decisions';
