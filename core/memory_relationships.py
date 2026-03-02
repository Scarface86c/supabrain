#!/usr/bin/env python3
"""
SupaBrain Memory Relationships Module
Handles explicit relationships between memories
"""

from typing import List, Optional, Dict
import asyncpg

try:
    from .exceptions import RelationshipError, ValidationError, MemoryNotFoundError
except ImportError:
    from exceptions import RelationshipError, ValidationError, MemoryNotFoundError  # type: ignore[no-redef]


class MemoryRelationships:
    """Relationship management between memories"""
    
    def __init__(self, db_pool: asyncpg.Pool) -> None:
        self.db_pool: asyncpg.Pool = db_pool
    
    async def create_relationship(
        self,
        from_memory_id: int,
        to_memory_id: int,
        relationship_type: str,
        reason: Optional[str] = None
    ) -> Dict:
        """
        Create explicit relationship between memories
        
        Args:
            from_memory_id: Source memory
            to_memory_id: Target memory
            relationship_type: Type of relationship (see valid_relationship_type constraint)
            reason: Optional explanation
        
        Returns:
            Dict with relationship info
        """
        valid_types = [
            'superseded_by', 'evolved_to', 'originated_from',
            'contradicts', 'reinforces', 'inspired_by', 'related_to'
        ]
        
        if relationship_type not in valid_types:
            raise RelationshipError(f"Invalid relationship type {relationship_type!r}. Must be one of: {valid_types}")
        
        async with self.db_pool.acquire() as conn:
            # Check if both memories exist
            from_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM memories WHERE id = $1)",
                from_memory_id
            )
            to_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM memories WHERE id = $1)",
                to_memory_id
            )
            
            if not from_exists or not to_exists:
                raise RelationshipError("One or both memories do not exist")
            
            # Create relationship (will ignore if duplicate due to unique constraint)
            rel_id = await conn.fetchval("""
                INSERT INTO memory_relationships 
                (from_memory_id, to_memory_id, relationship_type, reason)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (from_memory_id, to_memory_id, relationship_type) 
                DO UPDATE SET reason = EXCLUDED.reason
                RETURNING id
            """, from_memory_id, to_memory_id, relationship_type, reason)
            
            return {
                "success": True,
                "relationship_id": rel_id,
                "from_memory_id": from_memory_id,
                "to_memory_id": to_memory_id,
                "relationship_type": relationship_type
            }
    
    async def get_related_memories(
        self,
        memory_id: int,
        relationship_types: Optional[List[str]] = None,
        direction: str = "both",  # "both", "from", "to"
        limit: int = 20
    ) -> List[Dict]:
        """
        Get memories related to this one
        
        Args:
            memory_id: Central memory
            relationship_types: Filter by types (None = all)
            direction: "both", "from" (outgoing), "to" (incoming)
            limit: Max results
        
        Returns:
            List of related memories with relationship info
        """
        if direction not in ("from", "to", "both"):
            raise ValidationError(f"Invalid direction {direction!r}. Must be 'from', 'to', or 'both'.")

        async with self.db_pool.acquire() as conn:
            # Build relationship type filter clause (shared)
            # Params: $1 = memory_id, $2..$N = relationship_types (if any), last = limit
            if relationship_types:
                rel_placeholders = ','.join([f"${i+2}" for i in range(len(relationship_types))])
                rel_filter = f"AND r.relationship_type IN ({rel_placeholders})"
                limit_param = f"${len(relationship_types) + 2}"
                params = [memory_id, *relationship_types, limit]
            else:
                rel_filter = ""
                limit_param = "$2"
                params = [memory_id, limit]

            # Build query based on direction
            if direction == "from":
                query = f"""
                    SELECT 
                        r.id as rel_id,
                        r.relationship_type,
                        r.reason,
                        r.created_at as relationship_created,
                        m.*
                    FROM memory_relationships r
                    JOIN memories m ON r.to_memory_id = m.id
                    WHERE r.from_memory_id = $1
                    AND m.status = 'active'
                    {rel_filter}
                    LIMIT {limit_param}
                """
            elif direction == "to":
                query = f"""
                    SELECT 
                        r.id as rel_id,
                        r.relationship_type,
                        r.reason,
                        r.created_at as relationship_created,
                        m.*
                    FROM memory_relationships r
                    JOIN memories m ON r.from_memory_id = m.id
                    WHERE r.to_memory_id = $1
                    AND m.status = 'active'
                    {rel_filter}
                    LIMIT {limit_param}
                """
            else:  # both — wrap UNION ALL in CTE so filters apply to combined result
                query = f"""
                    WITH combined AS (
                        SELECT 
                            r.id as rel_id,
                            r.relationship_type,
                            r.reason,
                            r.created_at as relationship_created,
                            'outgoing' as direction,
                            m.*
                        FROM memory_relationships r
                        JOIN memories m ON r.to_memory_id = m.id
                        WHERE r.from_memory_id = $1
                        AND m.status = 'active'
                        
                        UNION ALL
                        
                        SELECT 
                            r.id as rel_id,
                            r.relationship_type,
                            r.reason,
                            r.created_at as relationship_created,
                            'incoming' as direction,
                            m.*
                        FROM memory_relationships r
                        JOIN memories m ON r.from_memory_id = m.id
                        WHERE r.to_memory_id = $1
                        AND m.status = 'active'
                    )
                    SELECT * FROM combined
                    WHERE 1=1
                    {rel_filter.replace('r.relationship_type', 'relationship_type')}
                    LIMIT {limit_param}
                """

            rows = await conn.fetch(query, *params)
            
            results = []
            for row in rows:
                results.append({
                    "memory": {
                        "id": row['id'],
                        "content": row['layer_1_summary'],
                        "tags": row['tags'] or [],
                        "importance_score": row['importance_score'],
                        "created_at": row['created_at'].isoformat(),
                        "memory_type": row['memory_type'],
                        "domain": row['domain']
                    },
                    "relationship": {
                        "id": row['rel_id'],
                        "type": row['relationship_type'],
                        "reason": row['reason'],
                        "created_at": row['relationship_created'].isoformat(),
                        "direction": row.get('direction', 'outgoing' if direction == "from" else 'incoming')
                    }
                })
            
            return results
