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
    description="Multi-Layer Memory System for AI Agents",
    version="0.1.0",
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


class MemoryQuery(BaseModel):
    query: str
    agent_name: Optional[str] = "default"
    max_layer: int = 2
    limit: int = 10
    min_score: float = 0.5
    tags: Optional[List[str]] = None


class MemoryResponse(BaseModel):
    id: int
    content: str
    tags: List[str]
    importance_score: float
    access_count: int
    similarity: float
    created_at: str


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
        "version": "0.1.0",
        "status": "operational",
        "message": "Multi-Layer Memory System for AI Agents"
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
            importance_score=memory.importance_score
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
            tags=query.tags
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


@app.delete("/api/v1/memory/{memory_id}")
async def delete_memory(memory_id: int):
    """Delete a specific memory (TODO: implement)"""
    # TODO: Implement deletion
    raise HTTPException(status_code=501, detail="Not implemented yet")


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
