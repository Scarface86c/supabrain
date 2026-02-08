"""
Agent identity endpoints
"""

from fastapi import APIRouter, HTTPException
from identity import load_identity

router = APIRouter(prefix="/api/v1", tags=["identity"])


@router.get("/identity/{agent_name}")
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


@router.get("/whoami")
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
