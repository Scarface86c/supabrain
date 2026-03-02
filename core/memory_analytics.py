#!/usr/bin/env python3
"""
SupaBrain Memory Analytics
Analytics, statistics, and decay management for memories
"""

from typing import Optional, Dict, Callable, Any
import asyncpg


class MemoryAnalytics:
    """Memory analytics, decay, and statistics"""
    
    def __init__(
        self,
        db_pool: asyncpg.Pool,
        get_agent_id_func: Callable[[str, Any], Any],
        default_agent_name: str
    ) -> None:
        """
        Initialize analytics module
        
        Args:
            db_pool: asyncpg database connection pool
            get_agent_id_func: Function to get agent ID by name
            default_agent_name: Default agent name for operations
        """
        self.db_pool: asyncpg.Pool = db_pool
        self._get_agent_id: Callable[[str, Any], Any] = get_agent_id_func
        self.default_agent_name: str = default_agent_name

    async def update_decay_scores(self, agent_name: Optional[str] = None) -> Dict:
        """
        Recalculate decay_score for all memories of an agent.
        
        Decay formula: exponential decay based on days since last access.
        Half-life = 60 days (after 60 days without access, score halves).
        Minimum decay = 0.1 (memories never disappear completely).
        High-importance memories (>= 0.85) decay 3x slower (half-life = 180 days).
        
        Returns: dict with count of updated memories and average decay score.
        """
        if agent_name is None:
            agent_name = self.default_agent_name
            
        async with self.db_pool.acquire() as conn:
            agent_id = await self._get_agent_id(agent_name, conn)
            if not agent_id:
                return {"updated": 0, "avg_decay_score": 1.0, "error": "Agent not found"}
            
            # Update decay scores using exponential decay
            # lambda = ln(2) / half_life
            # For normal memories: half_life=60d → lambda=0.01155
            # For important memories (>=0.85): half_life=180d → lambda=0.00385
            result = await conn.fetchrow(
                """
                WITH updated AS (
                    UPDATE memories
                    SET
                        decay_score = GREATEST(0.1, 
                            EXP(
                                -CASE WHEN importance_score >= 0.85 THEN 0.00385 ELSE 0.01155 END *
                                GREATEST(0, EXTRACT(EPOCH FROM (
                                    NOW() - COALESCE(last_accessed, created_at)
                                )) / 86400.0)
                            )
                        ),
                        last_decay_check = NOW()
                    WHERE agent_id = $1
                    RETURNING decay_score
                )
                SELECT COUNT(*) as updated, AVG(decay_score) as avg_decay
                FROM updated
                """,
                agent_id
            )
            
            return {
                "updated": result['updated'],
                "avg_decay_score": float(result['avg_decay']) if result['avg_decay'] else 1.0
            }

    async def get_stats(self, agent_name: Optional[str] = None) -> Dict:
        """Get memory statistics for an agent"""
        # Use configured agent name if not specified
        if agent_name is None:
            agent_name = self.default_agent_name
            
        async with self.db_pool.acquire() as conn:
            agent_id = await self._get_agent_id(agent_name, conn)
            
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
                  AND status = 'active'
                """,
                agent_id
            )
            
            return {
                "total_memories": stats['total_memories'],
                "average_importance": float(stats['avg_importance'] or 0),
                "total_accesses": stats['total_accesses'] or 0
            }
    
    async def get_analytics(self, agent_name: Optional[str] = None) -> Dict:
        """Get detailed analytics about memory patterns"""
        # Use configured agent name if not specified
        if agent_name is None:
            agent_name = self.default_agent_name
            
        async with self.db_pool.acquire() as conn:
            agent_id = await self._get_agent_id(agent_name, conn)
            
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

    async def get_layer_stats(self, agent_name: Optional[str] = None) -> dict:
        """
        Get memory count per priority layer
        
        Returns:
            Dict with layer_1 through layer_5 counts
        """
        # Use configured agent name if not specified
        if agent_name is None:
            agent_name = self.default_agent_name
        
        async with self.db_pool.acquire() as conn:
            agent_id = await self._get_agent_id(agent_name, conn)
            if not agent_id:
                # Return empty stats if agent doesn't exist
                return {f"layer_{i}": 0 for i in range(1, 6)}
            
            rows = await conn.fetch("""
                SELECT priority_layer, COUNT(*) as count
                FROM memories
                WHERE agent_id = $1 AND status = 'active'
                GROUP BY priority_layer
                ORDER BY priority_layer
            """, agent_id)
            
            stats = {f"layer_{i}": 0 for i in range(1, 6)}
            for row in rows:
                stats[f"layer_{row['priority_layer']}"] = row['count']
            
            return stats
