#!/usr/bin/env python3
"""
SupaStats Analytics API Routes
Provides memory access analytics, usage statistics, and insights
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from pydantic import BaseModel
from memory_engine import engine


router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


# Response Models
class MemoryAccessStats(BaseModel):
    """Statistics about memory access patterns"""
    memory_id: int
    access_count: int
    last_accessed: Optional[datetime]
    layer_1_summary: str
    importance_score: float
    temporal_layer: str
    created_at: datetime


class TemporalDistribution(BaseModel):
    """Distribution of memories across temporal layers"""
    working: int
    short: int
    long: int
    archive: int
    total: int


class MemoryTypeDistribution(BaseModel):
    """Distribution of memories by type"""
    facts: int
    experiences: int
    skills: int
    preferences: int
    decisions: int
    context: int
    total: int


# --- Endpoints ---

@router.get("/top-memories", response_model=List[MemoryAccessStats])
async def get_top_memories(
    agent_name: str,
    limit: int = Query(default=10, ge=1, le=100),
    sort_by: str = Query(default="access_count", pattern="^(access_count|last_accessed)$")
):
    """
    Get most accessed memories
    
    - **agent_name**: Agent to query
    - **limit**: Number of results (1-100)
    - **sort_by**: Sort criterion (access_count, last_accessed)
    """
    try:
        query = f"""
        SELECT 
            m.id as memory_id,
            m.access_count,
            m.last_accessed,
            m.layer_1_summary,
            m.importance_score,
            m.temporal_layer,
            m.created_at
        FROM memories m
        JOIN agents a ON m.agent_id = a.id
        WHERE LOWER(a.agent_name) = LOWER($1)
          AND m.status = 'active'
          AND m.is_current = true
        ORDER BY m.{sort_by} DESC NULLS LAST
        LIMIT $2
        """
        
        rows = await engine.db_pool.fetch(query, agent_name, limit)
        
        return [
            MemoryAccessStats(
                memory_id=row['memory_id'],
                access_count=row['access_count'],
                last_accessed=row['last_accessed'],
                layer_1_summary=row['layer_1_summary'],
                importance_score=row['importance_score'],
                temporal_layer=row['temporal_layer'],
                created_at=row['created_at']
            )
            for row in rows
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve top memories: {str(e)}")


@router.get("/temporal-distribution", response_model=TemporalDistribution)
async def get_temporal_distribution(agent_name: str):
    """
    Get distribution of memories across temporal layers
    
    - **agent_name**: Agent to analyze
    """
    try:
        query = """
        SELECT 
            temporal_layer,
            COUNT(*) as count
        FROM memories m
        JOIN agents a ON m.agent_id = a.id
        WHERE LOWER(a.agent_name) = LOWER($1)
          AND m.status = 'active'
          AND m.is_current = true
        GROUP BY temporal_layer
        """
        
        rows = await engine.db_pool.fetch(query, agent_name)
        
        distribution = {row['temporal_layer']: row['count'] for row in rows}
        total = sum(distribution.values())
        
        return TemporalDistribution(
            working=distribution.get('working', 0),
            short=distribution.get('short', 0),
            long=distribution.get('long', 0),
            archive=distribution.get('archive', 0),
            total=total
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve temporal distribution: {str(e)}")


@router.get("/memory-types", response_model=MemoryTypeDistribution)
async def get_memory_type_distribution(agent_name: str):
    """
    Get distribution of memories by type (facts, experiences, skills, etc.)
    
    - **agent_name**: Agent to analyze
    """
    try:
        query = """
        SELECT 
            memory_type,
            COUNT(*) as count
        FROM memories m
        JOIN agents a ON m.agent_id = a.id
        WHERE LOWER(a.agent_name) = LOWER($1)
          AND m.status = 'active'
          AND m.is_current = true
          AND memory_type IS NOT NULL
        GROUP BY memory_type
        """
        
        rows = await engine.db_pool.fetch(query, agent_name)
        
        distribution = {row['memory_type']: row['count'] for row in rows}
        total = sum(distribution.values())
        
        return MemoryTypeDistribution(
            facts=distribution.get('facts', 0),
            experiences=distribution.get('experiences', 0),
            skills=distribution.get('skills', 0),
            preferences=distribution.get('preferences', 0),
            decisions=distribution.get('decisions', 0),
            context=distribution.get('context', 0),
            total=total
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memory type distribution: {str(e)}")
