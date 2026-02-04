-- SupaBrain PostgreSQL Schema
-- Multi-Layer Memory System for AI Agents

-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- Agents table (for multi-agent support)
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Memories table (hierarchical storage)
CREATE TABLE memories (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
    
    -- Content at different layers
    layer_1_summary TEXT,           -- 10-50 tokens
    layer_2_context TEXT,           -- 50-200 tokens  
    layer_3_details TEXT,           -- 200-1000 tokens
    layer_4_full TEXT,              -- 1000-2000 tokens
    layer_5_complete TEXT,          -- Full detail + metadata
    
    -- Embeddings for semantic search (768-dim for sentence-transformers)
    layer_1_embedding vector(768),
    layer_2_embedding vector(768),
    
    -- Metadata
    tags TEXT[],                    -- Keywords for fast filtering
    importance_score FLOAT DEFAULT 0.5,  -- 0.0-1.0 for auto-layering
    access_count INTEGER DEFAULT 0,      -- Track usage
    last_accessed TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Optional context
    source_type VARCHAR(50),        -- 'conversation', 'task', 'decision', etc.
    related_memory_ids INTEGER[]    -- Links to related memories
);

-- Indexes for performance
CREATE INDEX idx_memories_agent ON memories(agent_id);
CREATE INDEX idx_memories_tags ON memories USING GIN(tags);
CREATE INDEX idx_memories_created ON memories(created_at DESC);
CREATE INDEX idx_memories_importance ON memories(importance_score DESC);
CREATE INDEX idx_memories_source ON memories(source_type);

-- Vector similarity search indexes
CREATE INDEX idx_layer1_embedding ON memories 
    USING ivfflat (layer_1_embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX idx_layer2_embedding ON memories 
    USING ivfflat (layer_2_embedding vector_cosine_ops)
    WITH (lists = 100);

-- Full-text search on all layers
CREATE INDEX idx_memories_fts ON memories 
    USING GIN(to_tsvector('english', 
        COALESCE(layer_1_summary, '') || ' ' || 
        COALESCE(layer_2_context, '') || ' ' ||
        COALESCE(layer_3_details, '')
    ));

-- Memory access log (for analytics)
CREATE TABLE memory_access_log (
    id SERIAL PRIMARY KEY,
    memory_id INTEGER REFERENCES memories(id) ON DELETE CASCADE,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
    layer_accessed INTEGER,
    access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    query_text TEXT,
    relevance_score FLOAT
);

-- Trigger to update access count
CREATE OR REPLACE FUNCTION update_memory_access()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE memories 
    SET access_count = access_count + 1,
        last_accessed = CURRENT_TIMESTAMP
    WHERE id = NEW.memory_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER memory_accessed
    AFTER INSERT ON memory_access_log
    FOR EACH ROW
    EXECUTE FUNCTION update_memory_access();

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER memories_updated
    BEFORE UPDATE ON memories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Helper views

-- View: Most accessed memories
CREATE VIEW top_memories AS
SELECT 
    m.id,
    m.layer_1_summary,
    m.access_count,
    m.importance_score,
    m.last_accessed,
    a.agent_name
FROM memories m
JOIN agents a ON m.agent_id = a.id
ORDER BY m.access_count DESC, m.importance_score DESC;

-- View: Recent memories by agent
CREATE VIEW recent_memories AS
SELECT 
    m.id,
    a.agent_name,
    m.layer_1_summary,
    m.tags,
    m.created_at
FROM memories m
JOIN agents a ON m.agent_id = a.id
ORDER BY m.created_at DESC;

-- Seed default agent (optional)
INSERT INTO agents (agent_name, metadata) 
VALUES ('default', '{"description": "Default agent for testing"}')
ON CONFLICT (agent_name) DO NOTHING;

-- Comments for documentation
COMMENT ON TABLE memories IS 'Hierarchical memory storage with 5 layers of detail';
COMMENT ON COLUMN memories.layer_1_summary IS 'Brief summary (10-50 tokens) for quick scanning';
COMMENT ON COLUMN memories.layer_2_context IS 'Context and key points (50-200 tokens)';
COMMENT ON COLUMN memories.layer_3_details IS 'Detailed information (200-1000 tokens)';
COMMENT ON COLUMN memories.importance_score IS 'ML-derived importance score (0.0-1.0)';
