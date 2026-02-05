#!/usr/bin/env python3
"""
SupaBrain Memory Engine
Core logic for storing and retrieving memories
"""

import asyncpg
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Optional, Dict
import os
from dotenv import load_dotenv

load_dotenv()


class MemoryEngine:
    """Multi-layer memory storage and retrieval"""
    
    def __init__(self):
        self.db_pool = None
        self.model = None
        self.model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.device = os.getenv("DEVICE", "cpu")
        
    async def initialize(self):
        """Initialize database pool and embedding model"""
        # Database connection pool
        db_url = os.getenv("DATABASE_URL", "postgresql://postgres@localhost:5432/supabrain")
        self.db_pool = await asyncpg.create_pool(
            db_url,
            min_size=2,
            max_size=10
        )
        
        # Load embedding model (CPU-only)
        print(f"Loading embedding model: {self.model_name} on {self.device}")
        self.model = SentenceTransformer(self.model_name, device=self.device)
        print("✓ Memory engine initialized")
        
    async def close(self):
        """Close database connections"""
        if self.db_pool:
            await self.db_pool.close()
            
    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding vector for text"""
        return self.model.encode(text, convert_to_numpy=True)
    
    def _auto_layer_content(self, content: str) -> Dict[str, str]:
        """
        Automatically create multi-layer representation
        
        Layer 1: Summary (10-50 tokens)
        Layer 2: Context (50-200 tokens)  
        Layer 3+: Full details
        
        For MVP: Simple truncation
        TODO: Use LLM for proper summarization
        """
        words = content.split()
        
        # Layer 1: First ~10 words
        layer_1 = ' '.join(words[:10]) + ("..." if len(words) > 10 else "")
        
        # Layer 2: First ~50 words  
        layer_2 = ' '.join(words[:50]) + ("..." if len(words) > 50 else "")
        
        # Layer 3: Full content (up to reasonable limit)
        layer_3 = content[:2000]
        
        return {
            "layer_1": layer_1,
            "layer_2": layer_2,
            "layer_3": layer_3
        }
    
    def _classify_memory_type(self, content: str, tags: List[str]) -> str:
        """
        Auto-classify memory type based on content and tags
        
        Types:
        - facts: Factual information
        - experiences: Events that happened
        - skills: How to do something
        - preferences: Likes/dislikes/styles
        - decisions: Choices made
        - context: Project/topic background
        """
        content_lower = content.lower()
        tags_str = ' '.join(tags).lower()
        
        # Preference indicators
        if any(word in content_lower for word in ['prefer', 'like', 'hate', 'love', 'dislike', 'values', 'style']):
            return 'preferences'
        
        # Decision indicators
        if any(word in content_lower for word in ['decided', 'decision', 'chose', 'will use', 'strategy']):
            return 'decisions'
        
        # Experience indicators (past tense, events)
        if any(word in content_lower for word in ['built', 'created', 'today', 'yesterday', 'happened', 'did']):
            return 'experiences'
        
        # Skill indicators
        if any(word in content_lower for word in ['how to', 'guide', 'tutorial', 'steps to', 'method']):
            return 'skills'
        
        # Context indicators (project info)
        if any(word in tags_str for word in ['project', 'system', 'overview', 'about']):
            return 'context'
        
        # Default: facts
        return 'facts'
    
    async def remember(
        self,
        content: str,
        agent_name: str = "default",
        tags: Optional[List[str]] = None,
        source_type: Optional[str] = None,
        importance_score: float = 0.5,
        memory_type: Optional[str] = None,
        temporal_layer: str = "long",
        ttl_hours: Optional[int] = None,
        domain: str = "general"
    ) -> int:
        """
        Store a new memory
        
        Returns:
            memory_id: ID of stored memory
        """
        if tags is None:
            tags = []
        
        # Auto-classify memory type if not provided
        if memory_type is None:
            memory_type = self._classify_memory_type(content, tags)
            
        # Generate layers
        layers = self._auto_layer_content(content)
        
        # Generate embeddings for layer 1 and 2
        emb_1 = self._generate_embedding(layers["layer_1"])
        emb_2 = self._generate_embedding(layers["layer_2"])
        
        # Get or create agent
        async with self.db_pool.acquire() as conn:
            # Ensure agent exists
            agent_id = await conn.fetchval(
                """
                INSERT INTO agents (agent_name, metadata)
                VALUES ($1, '{}'::jsonb)
                ON CONFLICT (agent_name) DO UPDATE SET agent_name = $1
                RETURNING id
                """,
                agent_name
            )
            
            # Store memory
            # Convert embeddings to pgvector format
            emb_1_str = '[' + ','.join(map(str, emb_1.tolist())) + ']'
            emb_2_str = '[' + ','.join(map(str, emb_2.tolist())) + ']'
            
            # Calculate expiration if TTL is set
            expires_at = None
            if ttl_hours and temporal_layer == 'working':
                expires_at = f"NOW() + INTERVAL '{ttl_hours} hours'"
            
            memory_id = await conn.fetchval(
                f"""
                INSERT INTO memories (
                    agent_id,
                    layer_1_summary,
                    layer_2_context,
                    layer_3_details,
                    layer_1_embedding,
                    layer_2_embedding,
                    tags,
                    importance_score,
                    source_type,
                    memory_type,
                    temporal_layer,
                    expires_at,
                    domain
                ) VALUES ($1, $2, $3, $4, $5::vector, $6::vector, $7, $8, $9, $10, $11, {expires_at or 'NULL'}, $12)
                RETURNING id
                """,
                agent_id,
                layers["layer_1"],
                layers["layer_2"],
                layers["layer_3"],
                emb_1_str,
                emb_2_str,
                tags,
                importance_score,
                source_type,
                memory_type,
                temporal_layer,
                domain
            )
            
        return memory_id
    
    async def recall(
        self,
        query: str,
        agent_name: str = "default",
        max_layer: int = 2,
        limit: int = 10,
        min_score: float = 0.5,
        tags: Optional[List[str]] = None,
        memory_type: Optional[str] = None,
        temporal_layers: Optional[List[str]] = None,
        include_archive: bool = False,
        domain: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for memories matching query
        
        Args:
            query: Search query
            agent_name: Agent to search for
            max_layer: Maximum detail layer to return (1-5)
            limit: Maximum results
            min_score: Minimum similarity score (0-1)
            tags: Optional tag filter
            
        Returns:
            List of matching memories with relevance scores
        """
        # Generate query embedding
        query_emb = self._generate_embedding(query)
        query_emb_str = '[' + ','.join(map(str, query_emb.tolist())) + ']'
        
        async with self.db_pool.acquire() as conn:
            # Get agent ID
            agent_id = await conn.fetchval(
                "SELECT id FROM agents WHERE agent_name = $1",
                agent_name
            )
            
            if not agent_id:
                return []
            
            # Default temporal layers (exclude archive unless requested)
            if temporal_layers is None:
                temporal_layers = ['working', 'short', 'long']
                if include_archive:
                    temporal_layers.append('archive')
            
            # Temporal layer scoring weights
            layer_weights = {
                'working': 1.5,
                'short': 1.2,
                'long': 1.0,
                'archive': 0.5
            }
            
            # Build search query
            # Use layer 1 embedding for initial search (fast)
            # Add temporal weighting to final score
            sql = """
                SELECT 
                    m.id,
                    m.layer_1_summary,
                    m.layer_2_context,
                    m.layer_3_details,
                    m.tags,
                    m.importance_score,
                    m.access_count,
                    m.created_at,
                    m.memory_type,
                    m.temporal_layer,
                    m.expires_at,
                    m.domain,
                    (1 - (m.layer_1_embedding <=> $2::vector)) as base_similarity,
                    (1 - (m.layer_1_embedding <=> $2::vector)) * 
                        CASE m.temporal_layer
                            WHEN 'working' THEN 1.5
                            WHEN 'short' THEN 1.2
                            WHEN 'long' THEN 1.0
                            WHEN 'archive' THEN 0.5
                            ELSE 1.0
                        END as weighted_similarity
                FROM memories m
                WHERE m.agent_id = $1
                  AND (m.expires_at IS NULL OR m.expires_at > NOW())
            """
            
            params = [agent_id, query_emb_str]
            
            # Temporal layer filter
            if temporal_layers:
                sql += " AND m.temporal_layer = ANY($%d)" % (len(params) + 1)
                params.append(temporal_layers)
            
            # Optional tag filter
            if tags:
                sql += " AND m.tags && $%d" % (len(params) + 1)
                params.append(tags)
            
            # Optional memory type filter
            if memory_type:
                sql += " AND m.memory_type = $%d" % (len(params) + 1)
                params.append(memory_type)
            
            # Optional domain filter
            if domain:
                sql += " AND m.domain = $%d" % (len(params) + 1)
                params.append(domain)
            
            # Order by weighted similarity (temporal + base) and importance
            sql += """
                ORDER BY weighted_similarity DESC, m.importance_score DESC
                LIMIT $%d
            """ % (len(params) + 1)
            params.append(limit)
            
            rows = await conn.fetch(sql, *params)
            
            # Format results based on max_layer
            results = []
            for row in rows:
                if row['weighted_similarity'] < min_score:
                    continue
                    
                memory = {
                    "id": row['id'],
                    "content": row['layer_1_summary'],  # Always include layer 1
                    "tags": row['tags'],
                    "importance_score": row['importance_score'],
                    "access_count": row['access_count'],
                    "similarity": float(row['weighted_similarity']),
                    "base_similarity": float(row['base_similarity']),
                    "created_at": row['created_at'].isoformat(),
                    "memory_type": row['memory_type'],
                    "temporal_layer": row['temporal_layer'],
                    "expires_at": row['expires_at'].isoformat() if row['expires_at'] else None,
                    "domain": row['domain']
                }
                
                # Add more detail based on max_layer
                if max_layer >= 2 and row['layer_2_context']:
                    memory['content'] = row['layer_2_context']
                    
                if max_layer >= 3 and row['layer_3_details']:
                    memory['content'] = row['layer_3_details']
                
                results.append(memory)
            
            # Log access for top results
            if results:
                memory_ids = [r['id'] for r in results]
                await conn.execute(
                    """
                    INSERT INTO memory_access_log (memory_id, agent_id, layer_accessed, query_text, relevance_score)
                    SELECT unnest($1::int[]), $2, $3, $4, unnest($5::float[])
                    """,
                    memory_ids,
                    agent_id,
                    max_layer,
                    query,
                    [r['similarity'] for r in results]
                )
            
        return results
    
    async def get_stats(self, agent_name: str = "default") -> Dict:
        """Get memory statistics for an agent"""
        async with self.db_pool.acquire() as conn:
            agent_id = await conn.fetchval(
                "SELECT id FROM agents WHERE agent_name = $1",
                agent_name
            )
            
            if not agent_id:
                return {
                    "total_memories": 0,
                    "average_importance": 0.0,
                    "total_accesses": 0
                }
            
            stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total_memories,
                    AVG(importance_score) as avg_importance,
                    SUM(access_count) as total_accesses
                FROM memories
                WHERE agent_id = $1
                """,
                agent_id
            )
            
            return {
                "total_memories": stats['total_memories'],
                "average_importance": float(stats['avg_importance'] or 0),
                "total_accesses": stats['total_accesses'] or 0
            }
    
    async def get_analytics(self, agent_name: str = "default") -> Dict:
        """Get detailed analytics about memory patterns"""
        async with self.db_pool.acquire() as conn:
            agent_id = await conn.fetchval(
                "SELECT id FROM agents WHERE agent_name = $1",
                agent_name
            )
            
            if not agent_id:
                return {"error": "Agent not found"}
            
            # Temporal layer distribution
            layer_stats = await conn.fetch(
                """
                SELECT 
                    temporal_layer,
                    COUNT(*) as count,
                    AVG(importance_score) as avg_importance,
                    SUM(access_count) as total_accesses
                FROM memories
                WHERE agent_id = $1 AND status = 'active'
                GROUP BY temporal_layer
                ORDER BY 
                    CASE temporal_layer
                        WHEN 'working' THEN 1
                        WHEN 'short' THEN 2
                        WHEN 'long' THEN 3
                        WHEN 'archive' THEN 4
                    END
                """,
                agent_id
            )
            
            # Memory type distribution
            type_stats = await conn.fetch(
                """
                SELECT 
                    memory_type,
                    COUNT(*) as count,
                    AVG(importance_score) as avg_importance
                FROM memories
                WHERE agent_id = $1 AND status = 'active'
                GROUP BY memory_type
                ORDER BY count DESC
                """,
                agent_id
            )
            
            # Review statistics
            review_stats = await conn.fetch(
                """
                SELECT 
                    decision,
                    COUNT(*) as count
                FROM review_log rl
                JOIN memories m ON m.id = rl.memory_id
                WHERE m.agent_id = $1
                GROUP BY decision
                ORDER BY count DESC
                """,
                agent_id
            )
            
            # Recent activity
            recent_count = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM memories
                WHERE agent_id = $1 
                  AND created_at > NOW() - INTERVAL '24 hours'
                """,
                agent_id
            )
            
            return {
                "layer_distribution": [
                    {
                        "layer": row['temporal_layer'],
                        "count": row['count'],
                        "avg_importance": float(row['avg_importance']),
                        "total_accesses": row['total_accesses']
                    }
                    for row in layer_stats
                ],
                "type_distribution": [
                    {
                        "type": row['memory_type'],
                        "count": row['count'],
                        "avg_importance": float(row['avg_importance'])
                    }
                    for row in type_stats
                ],
                "review_decisions": [
                    {
                        "decision": row['decision'],
                        "count": row['count']
                    }
                    for row in review_stats
                ],
                "recent_additions_24h": recent_count
            }
    
    async def get_pending_review(
        self,
        agent_name: str = "default",
        limit: int = 50
    ) -> Dict:
        """
        Get memories that need review (expired or pending_review status)
        
        Returns:
            Dictionary with pending_count and list of memories
        """
        async with self.db_pool.acquire() as conn:
            # Get agent ID
            agent_id = await conn.fetchval(
                "SELECT id FROM agents WHERE agent_name = $1",
                agent_name
            )
            
            if not agent_id:
                return {"pending_count": 0, "memories": []}
            
            # First, mark expired memories as needing review
            await conn.execute(
                """
                UPDATE memories 
                SET status = 'expired'
                WHERE agent_id = $1
                  AND expires_at IS NOT NULL 
                  AND expires_at < NOW() 
                  AND status = 'active'
                """,
                agent_id
            )
            
            # Get all memories needing review
            rows = await conn.fetch(
                """
                SELECT 
                    id,
                    layer_1_summary as content,
                    temporal_layer,
                    expires_at,
                    created_at,
                    last_accessed,
                    access_count,
                    importance_score,
                    tags,
                    memory_type,
                    status,
                    EXTRACT(EPOCH FROM (NOW() - created_at))/3600 as age_hours,
                    EXTRACT(EPOCH FROM (NOW() - COALESCE(last_accessed, created_at)))/3600 as hours_since_access
                FROM memories
                WHERE agent_id = $1
                  AND status IN ('expired', 'pending_review')
                ORDER BY expires_at ASC NULLS LAST, created_at DESC
                LIMIT $2
                """,
                agent_id,
                limit
            )
            
            memories = []
            for row in rows:
                memories.append({
                    "id": row['id'],
                    "content": row['content'],
                    "temporal_layer": row['temporal_layer'],
                    "expires_at": row['expires_at'].isoformat() if row['expires_at'] else None,
                    "created_at": row['created_at'].isoformat(),
                    "last_accessed": row['last_accessed'].isoformat() if row['last_accessed'] else None,
                    "age_hours": float(row['age_hours']),
                    "hours_since_access": float(row['hours_since_access']),
                    "access_count": row['access_count'],
                    "importance_score": row['importance_score'],
                    "tags": row['tags'],
                    "memory_type": row['memory_type'],
                    "status": row['status']
                })
            
            return {
                "pending_count": len(memories),
                "memories": memories
            }
    
    async def review_decide(
        self,
        memory_id: int,
        decision: str,
        new_layer: Optional[str] = None,
        reason: Optional[str] = None,
        ttl_hours: Optional[int] = None
    ) -> Dict:
        """
        Execute a review decision on a memory
        
        Args:
            memory_id: Memory to update
            decision: promote | extend | archive | delete
            new_layer: New temporal layer (if promote/extend)
            reason: Optional reason for decision
            ttl_hours: New TTL if extending
            
        Returns:
            Success status and updated memory info
        """
        async with self.db_pool.acquire() as conn:
            # Get current memory state
            current = await conn.fetchrow(
                "SELECT temporal_layer, status FROM memories WHERE id = $1",
                memory_id
            )
            
            if not current:
                raise ValueError(f"Memory {memory_id} not found")
            
            old_layer = current['temporal_layer']
            new_status = 'active'
            
            # Execute decision
            if decision == 'promote':
                # Promote to long-term or specified layer
                if not new_layer:
                    new_layer = 'long'
                
                await conn.execute(
                    """
                    UPDATE memories 
                    SET temporal_layer = $1,
                        status = $2,
                        expires_at = NULL,
                        importance_score = GREATEST(importance_score, 0.7)
                    WHERE id = $3
                    """,
                    new_layer,
                    new_status,
                    memory_id
                )
            
            elif decision == 'extend':
                # Extend in current or new layer with new TTL
                if not new_layer:
                    new_layer = old_layer
                
                if not ttl_hours:
                    # Default: short = 7 days, working = 1 day
                    ttl_hours = 168 if new_layer == 'short' else 24
                
                await conn.execute(
                    f"""
                    UPDATE memories 
                    SET temporal_layer = $1,
                        status = $2,
                        expires_at = NOW() + INTERVAL '{ttl_hours} hours'
                    WHERE id = $3
                    """,
                    new_layer,
                    new_status,
                    memory_id
                )
            
            elif decision == 'archive':
                # Move to archive
                await conn.execute(
                    """
                    UPDATE memories 
                    SET temporal_layer = 'archive',
                        status = 'archived',
                        expires_at = NULL
                    WHERE id = $1
                    """,
                    memory_id
                )
                new_layer = 'archive'
                new_status = 'archived'
            
            elif decision == 'delete':
                # Soft delete
                await conn.execute(
                    """
                    UPDATE memories 
                    SET status = 'deleted'
                    WHERE id = $1
                    """,
                    memory_id
                )
                new_layer = old_layer
                new_status = 'deleted'
            
            else:
                raise ValueError(f"Invalid decision: {decision}")
            
            # Log the decision
            await conn.execute(
                """
                INSERT INTO review_log (
                    memory_id, decision, old_layer, new_layer, reason
                ) VALUES ($1, $2, $3, $4, $5)
                """,
                memory_id,
                decision,
                old_layer,
                new_layer,
                reason
            )
            
            return {
                "success": True,
                "memory_id": memory_id,
                "decision": decision,
                "old_layer": old_layer,
                "new_layer": new_layer,
                "new_status": new_status
            }


# Global instance
engine = MemoryEngine()
