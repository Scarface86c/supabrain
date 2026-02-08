"""
Memory review system endpoints
"""

from fastapi import APIRouter, HTTPException
from models import ReviewDecision
from memory_engine import engine

router = APIRouter(prefix="/api/v1/review", tags=["review"])


@router.get("/pending")
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
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail="Database connection failed")
    except Exception as e:
        print(f"❌ Unexpected error in get_pending_review: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pending reviews")


@router.post("/decide")
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
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail="Database connection failed")
    except Exception as e:
        print(f"❌ Unexpected error in review_decide: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute decision")
