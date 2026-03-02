#!/usr/bin/env python3
"""
SupaBrain Memory Review
Review system for expired and pending memories (SleepBeat workflow)
"""

from typing import Optional, Dict, Callable, Any
import asyncpg

try:
    from .exceptions import MemoryNotFoundError, InvalidDecisionError
except ImportError:
    from exceptions import MemoryNotFoundError, InvalidDecisionError  # type: ignore[no-redef]


class MemoryReview:
    """Memory review system for SleepBeat and manual review workflows"""
    
    def __init__(
        self,
        db_pool: asyncpg.Pool,
        get_agent_id_func: Callable[[str, Any], Any],
        default_agent_name: str
    ) -> None:
        """
        Initialize review module
        
        Args:
            db_pool: asyncpg database connection pool
            get_agent_id_func: Function to get agent ID by name
            default_agent_name: Default agent name for operations
        """
        self.db_pool: asyncpg.Pool = db_pool
        self._get_agent_id: Callable[[str, Any], Any] = get_agent_id_func
        self.default_agent_name: str = default_agent_name

    async def get_pending_review(
        self,
        agent_name: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get memories that need review (expired or pending_review status)
        
        Returns:
            Dictionary with pending_count and list of memories
        """
        # Use configured agent name if not specified
        if agent_name is None:
            agent_name = self.default_agent_name
        
        async with self.db_pool.acquire() as conn:
            # Get agent ID (case-insensitive)
            agent_id = await self._get_agent_id(agent_name, conn)
            
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
    ) -> Dict[str, Any]:
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
                raise MemoryNotFoundError(memory_id=memory_id)
            
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
                raise InvalidDecisionError(f"Invalid decision: {decision}. Must be promote, extend, archive, or delete.")
            
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
