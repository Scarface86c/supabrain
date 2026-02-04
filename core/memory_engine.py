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
        memory_type: Optional[str] = None
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
            
            memory_id = await conn.fetchval(
                """
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
                    memory_type
                ) VALUES ($1, $2, $3, $4, $5::vector, $6::vector, $7, $8, $9, $10)
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
                memory_type
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
        memory_type: Optional[str] = None
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
            
            # Build search query
            # Use layer 1 embedding for initial search (fast)
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
                    1 - (m.layer_1_embedding <=> $2::vector) as similarity
                FROM memories m
                WHERE m.agent_id = $1
            """
            
            params = [agent_id, query_emb_str]
            
            # Optional tag filter
            if tags:
                sql += " AND m.tags && $%d" % (len(params) + 1)
                params.append(tags)
            
            # Optional memory type filter
            if memory_type:
                sql += " AND m.memory_type = $%d" % (len(params) + 1)
                params.append(memory_type)
            
            # Order by similarity and limit
            sql += """
                ORDER BY similarity DESC, m.importance_score DESC
                LIMIT $%d
            """ % (len(params) + 1)
            params.append(limit)
            
            rows = await conn.fetch(sql, *params)
            
            # Format results based on max_layer
            results = []
            for row in rows:
                if row['similarity'] < min_score:
                    continue
                    
                memory = {
                    "id": row['id'],
                    "content": row['layer_1_summary'],  # Always include layer 1
                    "tags": row['tags'],
                    "importance_score": row['importance_score'],
                    "access_count": row['access_count'],
                    "similarity": float(row['similarity']),
                    "created_at": row['created_at'].isoformat(),
                    "memory_type": row['memory_type']
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


# Global instance
engine = MemoryEngine()
