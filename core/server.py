#!/usr/bin/env python3
"""
SupaBrain Core Server
Multi-Layer Memory System for AI Agents
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Optional, Set
import uvicorn
from contextlib import asynccontextmanager
import re
import os

from memory_engine import engine
from tag_system import tag_system
from identity import load_identity
from rate_limiter import rate_limit_middleware
from auth import auth_middleware
from utils.skill_extraction import extract_skills_from_text
from validators import (
    validate_agent_name,
    validate_content,
    validate_tags,
    validate_importance,
    validate_temporal_layer,
    validate_domain,
    ValidationError
)

# Import routers
from routes import health, memory

# Configuration
DEFAULT_AGENT_NAME = os.getenv("DEFAULT_AGENT_NAME", None)  # No default - must be explicit!
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")  # Comma-separated list from env


# Skill extraction patterns
SKILL_PATTERNS = {
    'languages': [r'\b(python|javascript|typescript|rust|go|java|c\+\+|bash|sql|html|css)\b'],
    'frameworks': [
        r'\b(fastapi|flask|django|react|vue|postgresql|postgres|sqlite|redis|mongodb)\b',
        r'\b(numpy|pandas|transformers|sentence-transformers|uvicorn)\b',
    ],
    'tools': [
        r'\b(docker|kubernetes|git|github|vscode|vim|openclaw|supabrain)\b',
        r'\b(whisper|llm|gpt|claude)\b',
    ],
    'concepts': [
        r'\b(autonomous-decision|memory-architecture|api-design|database-design)\b',
        r'\b(system-architecture|learning-tracking|hierarchical-memory)\b',
        r'\b(semantic-search|embedding|vector-database)\b',
    ],
    'learned': [
        r'learned\s+(\w+(?:-\w+)*)',
        r'implemented\s+(\w+(?:-\w+)*)',
        r'built\s+(\w+(?:-\w+)*)',
        r'created\s+(\w+(?:-\w+)*)',
    ],
}


def extract_skills_from_text(text: str, min_length: int = 3) -> List[str]:
    """Extract skills from text content"""
    if not text:
        return []
    
    text_lower = text.lower()
    skills: Set[str] = set()
    
    for category, patterns in SKILL_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            
            for match in matches:
                skill = match[0] if isinstance(match, tuple) and match else match
                
                if skill and len(skill) >= min_length:
                    skill_normalized = skill.strip().lower()
                    if skill_normalized not in {'the', 'and', 'for', 'with', 'from', 'this', 'that'}:
                        skills.add(skill_normalized)
    
    return sorted(list(skills))


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

# CORS middleware (must be first for OPTIONS requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Configured via ALLOWED_ORIGINS env variable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication middleware (optional, env-controlled)
from starlette.middleware.base import BaseHTTPMiddleware
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

# Rate limiting middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limit_middleware)

# Include routers
app.include_router(health.router)
app.include_router(memory.router)

# Pydantic models
class MemoryCreate(BaseModel):
    content: str
    agent_name: str  # REQUIRED - each agent has unique identity
    tags: Optional[List[str]] = []
    source_type: Optional[str] = None
    importance_score: Optional[float] = 0.5
    memory_type: Optional[str] = None  # Auto-classified if not provided
    temporal_layer: Optional[str] = "long"  # working | short | long | archive
    ttl_hours: Optional[float] = None  # Auto-expire for working memory (can be fractional)
    domain: Optional[str] = "general"  # self | user | projects | world | system | general
    
    # Validators
    @validator('agent_name')
    def validate_agent_name_field(cls, v):
        try:
            return validate_agent_name(v)
        except ValidationError as e:
            raise ValueError(str(e))
    
    @validator('content')
    def validate_content_field(cls, v):
        try:
            return validate_content(v)
        except ValidationError as e:
            raise ValueError(str(e))
    
    @validator('tags')
    def validate_tags_field(cls, v):
        if v is None:
            return []
        try:
            return validate_tags(v)
        except ValidationError as e:
            raise ValueError(str(e))
    
    @validator('importance_score')
    def validate_importance_field(cls, v):
        try:
            return validate_importance(v)
        except ValidationError as e:
            raise ValueError(str(e))
    
    @validator('temporal_layer')
    def validate_temporal_layer_field(cls, v):
        try:
            return validate_temporal_layer(v)
        except ValidationError as e:
            raise ValueError(str(e))
    
    @validator('domain')
    def validate_domain_field(cls, v):
        try:
            return validate_domain(v)
        except ValidationError as e:
            raise ValueError(str(e))


class MemoryQuery(BaseModel):
    query: str
    agent_name: str  # REQUIRED - each agent has unique memories
    max_layer: int = 2
    limit: int = 10
    min_score: float = 0.5
    tags: Optional[List[str]] = None
    memory_type: Optional[str] = None  # Filter by type (facts, experiences, etc.)
    temporal_layers: Optional[List[str]] = None  # Filter by temporal layer
    include_archive: bool = False  # Include archived memories
    domain: Optional[str] = None  # Filter by domain (self/user/projects/world/system)
    
    # Validators
    @validator('agent_name')
    def validate_agent_name_field(cls, v):
        try:
            return validate_agent_name(v)
        except ValidationError as e:
            raise ValueError(str(e))
    
    @validator('query')
    def validate_query_field(cls, v):
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        if len(v) > 1000:
            raise ValueError("Query too long (max 1000 characters)")
        return v.strip()
    
    @validator('limit')
    def validate_limit_field(cls, v):
        if not 1 <= v <= 100:
            raise ValueError("Limit must be between 1 and 100")
        return v
    
    @validator('tags')
    def validate_tags_field(cls, v):
        if v is None:
            return None
        try:
            return validate_tags(v)
        except ValidationError as e:
            raise ValueError(str(e))
    
    @validator('domain')
    def validate_domain_field(cls, v):
        if v is None:
            return None
        try:
            return validate_domain(v)
        except ValidationError as e:
            raise ValueError(str(e))


class MemoryResponse(BaseModel):
    id: int
    content: str
    tags: List[str]
    importance_score: float
    access_count: int
    similarity: float
    base_similarity: Optional[float] = None


class LearningTrackRequest(BaseModel):
    skill: str
    agent_id: str = "default"
    memory_id: Optional[int] = None
    notes: Optional[str] = None


class RememberResponse(BaseModel):
    success: bool
    message: str
    memory_id: int


class StatsResponse(BaseModel):
    total_memories: int
    average_importance: float
    total_accesses: int


class TagStatsResponse(BaseModel):
    """Tag statistics response"""
    total_tags: int
    unique_tags: int
    top_tags: List[dict]
    tags_by_category: dict
    memories_with_tags: int


class TagSuggestRequest(BaseModel):
    """Tag suggestion request"""
    content: str
    existing_tags: Optional[List[str]] = []
    limit: Optional[int] = 5


class TagSuggestResponse(BaseModel):
    """Tag suggestion response"""
    suggestions: List[str]
    categories: dict


class TagCanonicalizeRequest(BaseModel):
    """Tag canonicalization request"""
    tags: List[str]


class TagCanonicalizeResponse(BaseModel):
    """Tag canonicalization response"""
    original: List[str]
    canonical: List[str]
    changes: List[dict]


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


@app.post("/api/v1/recall", response_model=List[MemoryResponse])
async def recall(query: MemoryQuery):
    """
    Retrieve memories matching the query using semantic search
    
    Example:
        {
          "query": "What did we build today?",
          "agent_name": "example_agent",
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
async def get_stats(agent_name: str):
    """Get memory system statistics for an agent"""
    try:
        stats = await engine.get_stats(agent_name=agent_name)
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.get("/api/v1/analytics")
async def get_analytics(agent_name: str):
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
async def get_pending_review(agent_name: str, limit: int = 50):
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


# Hierarchical Memory Layer Endpoints (v0.2)

class LayeredRecallRequest(BaseModel):
    query: str
    agent_name: str  # REQUIRED
    start_layer: int = 1
    max_layer: int = 3
    limit_per_layer: int = 10
    min_similarity: float = 0.7
    stop_on_match: bool = True  # Stop drilling if high-confidence match found


class LayerStatsResponse(BaseModel):
    layer_1: int
    layer_2: int
    layer_3: int
    layer_4: int
    layer_5: int
    total: int


class CreateRelationshipRequest(BaseModel):
    from_memory_id: int
    to_memory_id: int
    relationship_type: str
    reason: Optional[str] = None


class RelatedMemory(BaseModel):
    memory: dict
    relationship: dict


@app.post("/api/v1/recall/layered")
async def layered_recall(request: LayeredRecallRequest):
    """
    Smart hierarchical recall - starts with top layers, drills down as needed
    
    This mimics human memory: check critical memories first (Layer 1),
    then recent context (Layer 2), and deeper layers only if needed.
    
    Example:
    {
      "query": "Who is Scarface?",
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


@app.get("/api/v1/stats/layers", response_model=LayerStatsResponse)
async def layer_stats(agent_name: str):
    """
    Get memory distribution across priority layers
    
    Shows how memories are distributed for smart loading:
    - Layer 1: Critical (identity, core)
    - Layer 2: Recent context
    - Layer 3: Knowledge base
    - Layer 4: Historical
    - Layer 5: Archive
    """
    try:
        stats = await engine.get_layer_stats(agent_name=agent_name)
        stats['total'] = sum([stats[f'layer_{i}'] for i in range(1, 6)])
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get layer stats: {str(e)}")


@app.get("/api/v1/recovery/context")
async def context_recovery(agent_name: str):
    """
    Generate context recovery payload for LLM restart
    
    Returns Layer 1 (critical) memories formatted for quick restoration:
    - Identity (who am I?)
    - Core relationships (who is Scarface?)
    - Active projects
    - Recent critical context
    
    This is the "wake up" endpoint - loads only what's essential.
    """
    try:
        # Get Layer 1 memories
        layer1 = await engine.recall_by_layer(
            query="",  # No semantic filter, get all Layer 1
            agent_name=agent_name,
            priority_layer=1,
            limit=100
        )
        
        # Get layer stats for awareness
        stats = await engine.get_layer_stats(agent_name=agent_name)
        
        recovery_payload = {
            "critical_memories": layer1,
            "memory_counts": stats,
            "instructions": {
                "loaded": "Layer 1 (critical identity)",
                "available": f"Layer 2: {stats.get('layer_2', 0)} recent memories",
                "available_deep": f"Layers 3-5: {stats.get('layer_3', 0) + stats.get('layer_4', 0) + stats.get('layer_5', 0)} historical/archived",
                "next_steps": [
                    "Read HEARTBEAT.md for current tasks",
                    "Load Layer 2 if resuming active work",
                    "Query deeper layers on-demand"
                ]
            }
        }
        
        return recovery_payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context recovery failed: {str(e)}")


# Memory Relationship Endpoints

@app.post("/api/v1/memory/relate")
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


@app.get("/api/v1/memory/{memory_id}/related", response_model=List[RelatedMemory])
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
          "tags": [...],
          ...
        },
        "relationship": {
          "id": 5,
          "type": "evolved_to",
          "reason": "Project progressed",
          "direction": "outgoing"
        }
      }
    ]
    """
    try:
        types_list = relationship_types.split(',') if relationship_types else None
        
        results = await engine.get_related_memories(
            memory_id=memory_id,
            relationship_types=types_list,
            direction=direction,
            limit=limit
        )
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get related memories: {str(e)}")


# ============================================================================
# Learning Tracking Endpoints
# ============================================================================

@app.post("/api/v1/learning/track")
async def track_learning(request: LearningTrackRequest):
    """Track learning progress for a skill"""
    try:
        result = await engine.track_learning(
            agent_id=request.agent_id,
            skill=request.skill,
            memory_id=request.memory_id,
            notes=request.notes
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track learning: {str(e)}")


@app.get("/api/v1/learning/progress")
async def get_learning_progress(
    skill: str,
    agent_id: str = "default"
):
    """Get learning progress for a specific skill"""
    try:
        progress = await engine.get_learning_progress(agent_id=agent_id, skill=skill)
        if not progress:
            raise HTTPException(status_code=404, detail=f"No progress found for skill: {skill}")
        return progress
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learning progress: {str(e)}")


@app.get("/api/v1/learning/skills")
async def list_skills(agent_id: str = "default"):
    """List all skills being tracked"""
    try:
        skills = await engine.list_skills(agent_id=agent_id)
        return skills
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list skills: {str(e)}")


@app.get("/api/v1/learning/velocity")
async def get_learning_velocity(
    agent_id: str = "default",
    days: int = 7
):
    """Get learning velocity (learnings per day)"""
    try:
        velocity = await engine.get_learning_velocity(agent_id=agent_id, days=days)
        return velocity
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learning velocity: {str(e)}")


@app.get("/api/v1/tags/stats", response_model=TagStatsResponse)
async def get_tag_stats():
    """Get tag usage statistics"""
    try:
        async with engine.db_pool.acquire() as conn:
            # Get basic stats
            result = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT m.id) as memories_with_tags,
                    COUNT(t.tag) as total_tags,
                    COUNT(DISTINCT t.tag) as unique_tags
                FROM memories m
                CROSS JOIN LATERAL unnest(m.tags) as t(tag)
                WHERE m.tags IS NOT NULL
            """)
            
            # Top tags
            top_tags_result = await conn.fetch("""
                SELECT t.tag, COUNT(*) as count
                FROM memories m
                CROSS JOIN LATERAL unnest(m.tags) as t(tag)
                WHERE m.tags IS NOT NULL
                GROUP BY t.tag
                ORDER BY count DESC
                LIMIT 20
            """)
            
            top_tags = [{"tag": row["tag"], "count": row["count"]} for row in top_tags_result]
            
            # Group tags by category
            all_tags = [row["tag"] for row in top_tags_result]
            tags_by_category = tag_system.group_tags_by_category(all_tags)
            
            return TagStatsResponse(
                total_tags=result["total_tags"],
                unique_tags=result["unique_tags"],
                top_tags=top_tags,
                tags_by_category=tags_by_category,
                memories_with_tags=result["memories_with_tags"]
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/tags/suggest", response_model=TagSuggestResponse)
async def suggest_tags(request: TagSuggestRequest):
    """Suggest tags based on content"""
    try:
        suggestions = tag_system.suggest_tags(
            content=request.content,
            existing_tags=request.existing_tags,
            limit=request.limit
        )
        
        # Group suggestions by category
        categories = tag_system.group_tags_by_category(suggestions)
        
        return TagSuggestResponse(
            suggestions=suggestions,
            categories=categories
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/tags/canonicalize", response_model=TagCanonicalizeResponse)
async def canonicalize_tags_endpoint(request: TagCanonicalizeRequest):
    """Canonicalize tags (apply aliases and normalization)"""
    try:
        original = request.tags
        canonical = tag_system.canonicalize_tags(original)
        
        # Find changes (before deduplication)
        changes = []
        individual_canonical = [tag_system.canonicalize_tag(t) for t in original]
        for orig, canon in zip(original, individual_canonical):
            if orig.lower() != canon:
                changes.append({
                    "original": orig,
                    "canonical": canon,
                    "reason": "alias" if orig.lower() in tag_system.ALIASES else "normalized"
                })
        
        # Add note if deduplicated
        if len(canonical) < len(individual_canonical):
            dupes = len(individual_canonical) - len(canonical)
            changes.append({
                "original": "(duplicates)",
                "canonical": "(removed)",
                "reason": f"deduplicated {dupes} tag(s)"
            })
        
        return TagCanonicalizeResponse(
            original=original,
            canonical=canonical,
            changes=changes
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Identity Endpoints - Agent Personality & Self-Image
# ============================================================================

@app.get("/api/v1/identity/{agent_name}")
async def get_identity(agent_name: str):
    """
    Get agent's identity and personality.
    
    Each agent is unique - same code, different experiences and self-image.
    Like human twins: same DNA, different personalities.
    """
    try:
        identity = load_identity(agent_name)
        return {
            "success": True,
            "identity": identity.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/whoami")
async def whoami(agent_name: str):
    """
    Quick identity check - who am I?
    
    Returns basic identity info for an agent.
    """
    try:
        identity = load_identity(agent_name)
        return {
            "name": identity.name,
            "vibe": identity.vibe,
            "created_at": identity.created_at.isoformat(),
            "self_description": identity.self_description
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
