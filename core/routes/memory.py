"""
Memory CRUD and recall endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List
from models import MemoryCreate, MemoryQuery, MemoryResponse, RememberResponse
from memory_engine import engine
from tag_system import tag_system
from utils.skill_extraction import extract_skills_from_text

router = APIRouter(prefix="/api/v1", tags=["memory"])


@router.post("/remember", response_model=RememberResponse)
async def remember(memory: MemoryCreate):
    """
    Store a new memory with automatic layering and embedding generation
    NOW WITH AUTO-SKILL EXTRACTION!
    
    Example:
        {
          "content": "Scarface built SupaBrain today. It uses PostgreSQL and pgvector.",
          "agent_name": "example_agent",
          "tags": ["supabrain", "project"],
          "importance_score": 0.8
        }
    """
    try:
        # Canonicalize tags (apply aliases and normalization)
        canonical_tags = tag_system.canonicalize_tags(memory.tags or [])
        
        # Store memory
        memory_id = await engine.remember(
            content=memory.content,
            agent_name=memory.agent_name,
            tags=canonical_tags,
            source_type=memory.source_type,
            importance_score=memory.importance_score,
            memory_type=memory.memory_type,
            temporal_layer=memory.temporal_layer,
            ttl_hours=memory.ttl_hours,
            domain=memory.domain
        )
        
        # Auto-extract and track skills (async, don't block on failure)
        try:
            skills = extract_skills_from_text(memory.content)
            
            # Track top 3 skills maximum per memory
            for skill in skills[:3]:
                await engine.track_learning(
                    agent_id=memory.agent_name,
                    skill=skill,
                    memory_id=memory_id,
                    notes=f"Auto-extracted from memory #{memory_id}"
                )
        except Exception as skill_error:
            # Don't fail the whole request if skill tracking fails
            print(f"⚠️ Skill tracking failed: {skill_error}")
        
        return RememberResponse(
            success=True,
            message="Memory stored successfully",
            memory_id=memory_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store memory: {str(e)}")


@router.post("/recall", response_model=List[MemoryResponse])
async def recall(query: MemoryQuery):
    """
    Retrieve memories matching the query using semantic search
    
    Example:
        {
          "query": "What did Scarface build?",
          "agent_name": "example_agent",
          "limit": 5,
          "min_score": 0.5
        }
    """
    try:
        results = await engine.recall(
            query=query.query,
            agent_name=query.agent_name,
            limit=query.limit,
            min_score=query.min_score,
            max_layer=query.max_layer,
            temporal_layers=query.temporal_layers,
            domain=query.domain,
            tags=query.tags,
            include_archive=query.include_archive
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recall memories: {str(e)}")


# Other endpoints to migrate:
# DELETE /api/v1/memory/{memory_id}
# POST /api/v1/memory/relate
# GET /api/v1/memory/{memory_id}/related
# POST /api/v1/recall/layered
