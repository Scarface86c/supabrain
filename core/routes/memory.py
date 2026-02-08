"""
Memory CRUD and recall endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from models import (
    MemoryCreate, 
    MemoryQuery, 
    MemoryResponse, 
    RememberResponse,
    LayeredRecallQuery,
    CreateRelationshipRequest,
    RelatedMemory
)
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


@router.post("/recall/layered")
async def layered_recall(request: LayeredRecallQuery):
    """
    Smart hierarchical recall - starts with top layers, drills down as needed
    
    This mimics human memory: check critical memories first (Layer 1),
    then recent context (Layer 2), and deeper layers only if needed.
    
    Example:
    {
      "query": "Who is Scarface?",
      "agent_name": "Scar",
      "start_layer": 1,
      "max_layer": 3,
      "stop_on_match": true
    }
    
    Will search Layer 1 first, and only continue to Layer 2/3 if no good match found.
    """
    try:
        results = []
        layers_searched = []
        
        for layer in range(request.start_layer, request.max_layer + 1):
            # Get memories from this layer
            layer_results = await engine.recall_by_layer(
                query=request.query,
                agent_name=request.agent_name,
                priority_layer=layer,
                limit=request.limit_per_layer
            )
            
            layers_searched.append(layer)
            results.extend(layer_results)
            
            # Early stopping if we found high-confidence matches
            if request.stop_on_match and any(r['similarity'] > 0.85 for r in layer_results):
                break
        
        return {
            "results": results,
            "layers_searched": layers_searched,
            "total_found": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Layered recall failed: {str(e)}")


@router.delete("/memory/{memory_id}")
async def delete_memory(memory_id: int):
    """Delete a specific memory (TODO: implement)"""
    # TODO: Implement deletion
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/memory/relate")
async def create_relationship(request: CreateRelationshipRequest):
    """
    Create explicit relationship between two memories
    
    Valid relationship types:
    - superseded_by: Old memory is replaced by new one
    - evolved_to: Memory evolved into another
    - originated_from: Memory came from this source
    - contradicts: Conflicting information
    - reinforces: Supports/strengthens
    - inspired_by: Was inspired by
    - related_to: General association
    
    Example:
    {
      "from_memory_id": 42,
      "to_memory_id": 50,
      "relationship_type": "evolved_to",
      "reason": "Project progressed to next phase"
    }
    """
    try:
        result = await engine.create_relationship(
            from_memory_id=request.from_memory_id,
            to_memory_id=request.to_memory_id,
            relationship_type=request.relationship_type,
            reason=request.reason
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create relationship: {str(e)}")


@router.get("/memory/{memory_id}/related", response_model=List[RelatedMemory])
async def get_related_memories(
    memory_id: int,
    relationship_types: Optional[str] = None,  # Comma-separated
    direction: str = "both",
    limit: int = 20
):
    """
    Get memories related to this one
    
    Args:
    - memory_id: Central memory
    - relationship_types: Comma-separated types (e.g., "evolved_to,inspired_by")
    - direction: "both", "from" (outgoing), "to" (incoming)
    - limit: Max results
    
    Example:
    GET /api/v1/memory/42/related?relationship_types=evolved_to,inspired_by&direction=from
    
    Returns:
    [
      {
        "memory": {
          "id": 50,
          "content": "...",
          ...
        },
        "relationship": {
          "type": "evolved_to",
          "reason": "...",
          "created_at": "..."
        }
      }
    ]
    """
    try:
        # Parse relationship types
        rel_types = None
        if relationship_types:
            rel_types = [t.strip() for t in relationship_types.split(",")]
        
        results = await engine.get_related_memories(
            memory_id=memory_id,
            relationship_types=rel_types,
            direction=direction,
            limit=limit
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get related memories: {str(e)}")
