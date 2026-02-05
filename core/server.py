#!/usr/bin/env python3
"""
SupaBrain Core Server
Multi-Layer Memory System for AI Agents
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from contextlib import asynccontextmanager

from memory_engine import engine


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting SupaBrain...")
    await engine.initialize()
    yield
    # Shutdown
    print("👋 Shutting down SupaBrain...")
    await engine.close()


# Initialize FastAPI app
app = FastAPI(
    title="SupaBrain",
    description="Multi-Layer Memory System for AI Agents with Temporal Memory",
    version="0.2.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class MemoryCreate(BaseModel):
    content: str
    agent_name: Optional[str] = "default"
    tags: Optional[List[str]] = []
    source_type: Optional[str] = None
    importance_score: Optional[float] = 0.5
    memory_type: Optional[str] = None  # Auto-classified if not provided
    temporal_layer: Optional[str] = "long"  # working | short | long | archive
    ttl_hours: Optional[float] = None  # Auto-expire for working memory (can be fractional)
    domain: Optional[str] = "general"  # self | user | projects | world | system | general


class MemoryQuery(BaseModel):
    query: str
    agent_name: Optional[str] = "default"
    max_layer: int = 2
    limit: int = 10
    min_score: float = 0.5
    tags: Optional[List[str]] = None
    memory_type: Optional[str] = None  # Filter by type (facts, experiences, etc.)
    temporal_layers: Optional[List[str]] = None  # Filter by temporal layer
    include_archive: bool = False  # Include archived memories
    domain: Optional[str] = None  # Filter by domain (self/user/projects/world/system)


class MemoryResponse(BaseModel):
    id: int
    content: str
    tags: List[str]
    importance_score: float
    access_count: int
    similarity: float
    base_similarity: Optional[float] = None
    created_at: str
    memory_type: Optional[str] = None
    temporal_layer: Optional[str] = None
    expires_at: Optional[str] = None
    domain: Optional[str] = None


class RememberResponse(BaseModel):
    success: bool
    message: str
    memory_id: int


class StatsResponse(BaseModel):
    total_memories: int
    average_importance: float
    total_accesses: int


# Health check
@app.get("/")
async def root():
    return {
        "service": "SupaBrain",
        "version": "0.2.0",
        "status": "operational",
        "message": "Multi-Layer Memory System with Temporal Memory"
    }


@app.get("/health")
async def health_check():
    """Health check with database connectivity"""
    try:
        if engine.db_pool:
            # Simple DB check
            async with engine.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return {
                "status": "healthy",
                "database": "connected",
                "model": engine.model_name if engine.model else "not loaded"
            }
        else:
            return {
                "status": "initializing",
                "database": "not connected"
            }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


# Memory endpoints
@app.post("/api/v1/remember", response_model=RememberResponse)
async def remember(memory: MemoryCreate):
    """
    Store a new memory with automatic layering and embedding generation
    
    Example:
        {
          "content": "Scarface built SupaBrain today. It uses PostgreSQL and pgvector.",
          "agent_name": "Scar",
          "tags": ["supabrain", "project"],
          "importance_score": 0.8
        }
    """
    try:
        memory_id = await engine.remember(
            content=memory.content,
            agent_name=memory.agent_name,
            tags=memory.tags or [],
            source_type=memory.source_type,
            importance_score=memory.importance_score,
            memory_type=memory.memory_type,
            temporal_layer=memory.temporal_layer,
            ttl_hours=memory.ttl_hours,
            domain=memory.domain
        )
        
        return RememberResponse(
            success=True,
            message="Memory stored successfully",
            memory_id=memory_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store memory: {str(e)}")


@app.post("/api/v1/recall", response_model=List[MemoryResponse])
async def recall(query: MemoryQuery):
    """
    Retrieve memories matching the query using semantic search
    
    Example:
        {
          "query": "What did we build today?",
          "agent_name": "Scar",
          "max_layer": 2,
          "limit": 5
        }
    """
    try:
        results = await engine.recall(
            query=query.query,
            agent_name=query.agent_name,
            max_layer=query.max_layer,
            limit=query.limit,
            min_score=query.min_score,
            tags=query.tags,
            memory_type=query.memory_type,
            temporal_layers=query.temporal_layers,
            include_archive=query.include_archive,
            domain=query.domain
        )
        
        return [MemoryResponse(**r) for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recall memories: {str(e)}")


@app.get("/api/v1/stats", response_model=StatsResponse)
async def get_stats(agent_name: str = "default"):
    """Get memory system statistics for an agent"""
    try:
        stats = await engine.get_stats(agent_name=agent_name)
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.get("/api/v1/analytics")
async def get_analytics(agent_name: str = "default"):
    """
    Get detailed analytics about memory patterns
    
    Returns:
    - Temporal layer distribution (working/short/long/archive)
    - Memory type distribution (facts/experiences/etc)
    - Review decision patterns (promote/delete/archive rates)
    - Recent activity (24h additions)
    
    Useful for understanding memory usage patterns and optimization.
    """
    try:
        analytics = await engine.get_analytics(agent_name=agent_name)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@app.delete("/api/v1/memory/{memory_id}")
async def delete_memory(memory_id: int):
    """Delete a specific memory (TODO: implement)"""
    # TODO: Implement deletion
    raise HTTPException(status_code=501, detail="Not implemented yet")


# Review system endpoints
class ReviewDecision(BaseModel):
    memory_id: int
    decision: str  # promote | extend | archive | delete
    new_layer: Optional[str] = None
    reason: Optional[str] = None
    ttl_hours: Optional[float] = None


@app.get("/api/v1/review/pending")
async def get_pending_review(agent_name: str = "default", limit: int = 50):
    """
    Get memories that need review (expired or pending_review status)
    
    Returns list of memories with metadata to help LLM decide:
    - Content, age, access patterns, importance
    - Expiration info, tags, memory type
    
    Example response:
    {
      "pending_count": 3,
      "memories": [
        {
          "id": 22,
          "content": "User was testing SupaBrain...",
          "temporal_layer": "working",
          "expires_at": "2026-02-04T23:55:12",
          "age_hours": 1.2,
          "access_count": 3,
          "hours_since_access": 0.5,
          "importance_score": 0.5,
          "tags": ["test"],
          "memory_type": "context",
          "status": "expired"
        }
      ]
    }
    """
    try:
        result = await engine.get_pending_review(agent_name=agent_name, limit=limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending reviews: {str(e)}")


@app.post("/api/v1/review/decide")
async def review_decide(decision: ReviewDecision):
    """
    Execute a review decision on a memory
    
    Decisions:
    - promote: Move to long-term (or specified layer), clear expiration
    - extend: Extend TTL in current or new layer
    - archive: Move to archive (low search priority)
    - delete: Soft delete (status='deleted', recoverable)
    
    Example:
    {
      "memory_id": 22,
      "decision": "promote",
      "new_layer": "long",
      "reason": "Important development context"
    }
    
    {
      "memory_id": 23,
      "decision": "extend",
      "new_layer": "short",
      "ttl_hours": 168,
      "reason": "Project still active this week"
    }
    
    {
      "memory_id": 24,
      "decision": "delete",
      "reason": "Test memory, no longer needed"
    }
    """
    try:
        result = await engine.review_decide(
            memory_id=decision.memory_id,
            decision=decision.decision,
            new_layer=decision.new_layer,
            reason=decision.reason,
            ttl_hours=decision.ttl_hours
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute decision: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
