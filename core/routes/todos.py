#!/usr/bin/env python3
"""
TODO Management API Routes
Provides endpoints for managing TODO lifecycle via tags
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from memory_engine import engine
import asyncpg
import json

router = APIRouter(prefix="/api/v1/todos", tags=["todos"])


class TodoStatusUpdate(BaseModel):
    """Update TODO status"""
    memory_id: int
    status: str  # open, in-progress, completed, blocked, cancelled


class TodoListResponse(BaseModel):
    """TODO list response"""
    memory_id: int
    content: str
    status: str
    importance: float
    created_at: str
    tags: List[str]


class RecurringPattern(BaseModel):
    """Recurring TODO pattern"""
    frequency: str  # daily, weekly, monthly, yearly
    interval: int = 1  # Every N days/weeks/months/years
    days_of_week: Optional[List[int]] = None  # 0-6 for weekly
    day_of_month: Optional[int] = None  # 1-31 for monthly
    end_date: Optional[str] = None  # ISO format, optional


@router.get("/list", response_model=List[TodoListResponse])
async def list_todos(
    agent_name: str,
    status: Optional[str] = Query(default="open", pattern="^(open|in-progress|completed|blocked|cancelled|all)$"),
    limit: int = Query(default=50, ge=1, le=200)
) -> List[TodoListResponse]:
    """
    List TODOs for an agent
    
    - **agent_name**: Agent to query
    - **status**: Filter by status (open, in-progress, completed, blocked, cancelled, all)
    - **limit**: Max results (1-200)
    """
    try:
        # Build status filter
        if status == "all":
            status_filter = """
                AND ('todo:open' = ANY(m.tags) OR 
                     'todo:in-progress' = ANY(m.tags) OR 
                     'todo:completed' = ANY(m.tags) OR 
                     'todo:blocked' = ANY(m.tags) OR
                     'todo:cancelled' = ANY(m.tags))
            """
        else:
            status_filter = f"AND 'todo:{status}' = ANY(m.tags)"
        
        query = f"""
        SELECT 
            m.id as memory_id,
            m.layer_1_summary as content,
            m.importance_score as importance,
            m.created_at,
            m.tags,
            CASE 
                WHEN 'todo:completed' = ANY(m.tags) THEN 'completed'
                WHEN 'todo:in-progress' = ANY(m.tags) THEN 'in-progress'
                WHEN 'todo:blocked' = ANY(m.tags) THEN 'blocked'
                WHEN 'todo:cancelled' = ANY(m.tags) THEN 'cancelled'
                ELSE 'open'
            END as status
        FROM memories m
        JOIN agents a ON m.agent_id = a.id
        WHERE LOWER(a.agent_name) = LOWER($1)
          AND 'todo' = ANY(m.tags)
          AND m.status = 'active'
          {status_filter}
        ORDER BY 
            CASE status
                WHEN 'in-progress' THEN 1
                WHEN 'open' THEN 2
                WHEN 'blocked' THEN 3
                WHEN 'completed' THEN 4
                WHEN 'cancelled' THEN 5
            END,
            m.importance_score DESC,
            m.created_at DESC
        LIMIT $2
        """
        
        rows = await engine.db_pool.fetch(query, agent_name, limit)
        
        return [
            TodoListResponse(
                memory_id=row['memory_id'],
                content=row['content'],
                status=row['status'],
                importance=row['importance'],
                created_at=row['created_at'].isoformat(),
                tags=row['tags']
            )
            for row in rows
        ]
        
    except asyncpg.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error listing TODOs: {str(e)}")


@router.post("/update-status")
async def update_todo_status(update: TodoStatusUpdate) -> dict:
    """
    Update TODO status by adding/removing status tags
    
    - **memory_id**: Memory ID of the TODO
    - **status**: New status (open, in-progress, completed, blocked, cancelled)
    """
    valid_statuses = ['open', 'in-progress', 'completed', 'blocked', 'cancelled']
    if update.status not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    try:
        async with engine.db_pool.acquire() as conn:
            # Get current tags
            row = await conn.fetchrow("""
                SELECT tags FROM memories WHERE id = $1 AND status = 'active'
            """, update.memory_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="TODO not found")
            
            current_tags = list(row['tags'])
            
            # Remove all existing status tags
            status_tags = ['todo:open', 'todo:in-progress', 'todo:completed', 'todo:blocked', 'todo:cancelled']
            new_tags = [tag for tag in current_tags if tag not in status_tags]
            
            # Remove priority tags when marking as completed or cancelled (Bug fix 2026-02-21)
            if update.status in ['completed', 'cancelled']:
                priority_tags = ['priority-high', 'priority-medium', 'priority-low']
                new_tags = [tag for tag in new_tags if tag not in priority_tags]
            
            # Add new status tag
            new_tags.append(f'todo:{update.status}')
            
            # Update database
            await conn.execute("""
                UPDATE memories
                SET tags = $1,
                    updated_at = NOW()
                WHERE id = $2
            """, new_tags, update.memory_id)
            
            return {
                "status": "ok",
                "memory_id": update.memory_id,
                "new_status": update.status,
                "message": f"TODO status updated to '{update.status}'"
            }
            
    except HTTPException:
        raise
    except asyncpg.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error updating TODO: {str(e)}")


@router.post("/bulk-complete")
async def bulk_complete_todos(
    agent_name: str,
    memory_ids: List[int]
) -> dict:
    """
    Mark multiple TODOs as completed
    
    - **agent_name**: Agent name (for verification)
    - **memory_ids**: List of memory IDs to mark as completed
    """
    try:
        async with engine.db_pool.acquire() as conn:
            agent_id = await engine._get_agent_id(agent_name, conn)
            if not agent_id:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            updated = 0
            for memory_id in memory_ids:
                # Get current tags
                row = await conn.fetchrow("""
                    SELECT tags FROM memories 
                    WHERE id = $1 AND agent_id = $2 AND status = 'active'
                """, memory_id, agent_id)
                
                if row:
                    current_tags = list(row['tags'])
                    status_tags = ['todo:open', 'todo:in-progress', 'todo:blocked']
                    new_tags = [tag for tag in current_tags if tag not in status_tags]
                    # Remove priority tags when completing (Bug fix 2026-02-21)
                    priority_tags = ['priority-high', 'priority-medium', 'priority-low']
                    new_tags = [tag for tag in new_tags if tag not in priority_tags]
                    new_tags.append('todo:completed')
                    
                    await conn.execute("""
                        UPDATE memories
                        SET tags = $1, updated_at = NOW()
                        WHERE id = $2
                    """, new_tags, memory_id)
                    updated += 1
            
            return {
                "status": "ok",
                "updated": updated,
                "total_requested": len(memory_ids),
                "message": f"Marked {updated} TODOs as completed"
            }
            
    except HTTPException:
        raise
    except asyncpg.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error in bulk update: {str(e)}")


@router.post("/{memory_id}/recurrence")
async def set_recurring_pattern(
    memory_id: int,
    pattern: RecurringPattern
) -> dict:
    """
    Set recurring pattern for a TODO
    
    - **memory_id**: TODO memory ID
    - **pattern**: Recurring pattern configuration
    
    Example patterns:
    - Daily: {"frequency": "daily", "interval": 1}
    - Weekly on Mon/Wed/Fri: {"frequency": "weekly", "interval": 1, "days_of_week": [0,2,4]}
    - Monthly on 15th: {"frequency": "monthly", "interval": 1, "day_of_month": 15}
    - Yearly: {"frequency": "yearly", "interval": 1}
    - With end date: {..., "end_date": "2027-12-31"}
    """
    valid_frequencies = ['daily', 'weekly', 'monthly', 'yearly']
    if pattern.frequency not in valid_frequencies:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid frequency. Must be one of: {', '.join(valid_frequencies)}"
        )
    
    if pattern.interval < 1:
        raise HTTPException(status_code=400, detail="Interval must be >= 1")
    
    try:
        async with engine.db_pool.acquire() as conn:
            # Verify TODO exists and is active
            row = await conn.fetchrow("""
                SELECT id, tags FROM memories 
                WHERE id = $1 AND status = 'active' AND 'todo' = ANY(tags)
            """, memory_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="TODO not found")
            
            # Convert pattern to JSONB (asyncpg requires JSON string for JSONB columns)
            pattern_json = pattern.model_dump()
            
            # Update recurring pattern
            await conn.execute("""
                UPDATE memories
                SET recurring_pattern = $1::jsonb,
                    updated_at = NOW()
                WHERE id = $2
            """, json.dumps(pattern_json), memory_id)
            
            return {
                "status": "ok",
                "memory_id": memory_id,
                "pattern": pattern_json,
                "message": "Recurring pattern set successfully"
            }
            
    except HTTPException:
        raise
    except asyncpg.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error setting pattern: {str(e)}")


@router.get("/{memory_id}/instances")
async def get_recurring_instances(
    memory_id: int,
    limit: int = Query(default=50, ge=1, le=200)
) -> dict:
    """
    Get all instances of a recurring TODO
    
    - **memory_id**: Parent TODO memory ID
    - **limit**: Max results (1-200)
    
    Returns all TODOs that were created from this recurring parent,
    ordered by creation date (newest first).
    """
    try:
        async with engine.db_pool.acquire() as conn:
            # Verify parent exists
            parent = await conn.fetchrow("""
                SELECT id, layer_1_summary, recurring_pattern
                FROM memories
                WHERE id = $1 AND status = 'active'
            """, memory_id)
            
            if not parent:
                raise HTTPException(status_code=404, detail="Parent TODO not found")
            
            # Get all instances (children with this parent_id)
            instances = await conn.fetch("""
                SELECT 
                    id as memory_id,
                    layer_1_summary as content,
                    created_at,
                    updated_at,
                    tags,
                    importance_score as importance,
                    CASE 
                        WHEN 'todo:completed' = ANY(tags) THEN 'completed'
                        WHEN 'todo:in-progress' = ANY(tags) THEN 'in-progress'
                        WHEN 'todo:blocked' = ANY(tags) THEN 'blocked'
                        WHEN 'todo:cancelled' = ANY(tags) THEN 'cancelled'
                        ELSE 'open'
                    END as status
                FROM memories
                WHERE parent_id = $1
                  AND status = 'active'
                ORDER BY created_at DESC
                LIMIT $2
            """, memory_id, limit)
            
            return {
                "parent_id": memory_id,
                "parent_content": parent['layer_1_summary'],
                "recurring_pattern": parent['recurring_pattern'],
                "total_instances": len(instances),
                "instances": [dict(row) for row in instances]
            }
            
    except HTTPException:
        raise
    except asyncpg.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error fetching instances: {str(e)}")
