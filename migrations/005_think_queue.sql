-- Think Queue: Proactive cognition system
-- v0.5-alpha

CREATE TABLE IF NOT EXISTS think_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic TEXT NOT NULL,
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    context TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'complete', 'postponed')),
    created_at TIMESTAMP DEFAULT NOW(),
    due_at TIMESTAMP,
    completed_at TIMESTAMP,
    insights_memory_id UUID REFERENCES memories(id),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_think_queue_status_priority 
ON think_queue(status, priority DESC, created_at);

CREATE INDEX idx_think_queue_due_at
ON think_queue(due_at) WHERE status = 'pending';

COMMENT ON TABLE think_queue IS 'Proactive thinking queue - topics that need LLM reflection';
COMMENT ON COLUMN think_queue.priority IS 'Thought priority: low/medium/high/urgent';
COMMENT ON COLUMN think_queue.status IS 'Processing status: pending/in_progress/complete/postponed';
COMMENT ON COLUMN think_queue.due_at IS 'Optional deadline for thinking about this topic';
COMMENT ON COLUMN think_queue.insights_memory_id IS 'Link to memory containing the insights from thinking';
