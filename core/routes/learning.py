"""
Learning tracking endpoints
"""

from fastapi import APIRouter, HTTPException
from models import LearningTrackRequest
from memory_engine import engine

router = APIRouter(prefix="/api/v1/learning", tags=["learning"])


@router.post("/track")
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid learning data: {str(e)}")
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail="Database connection failed")
    except Exception as e:
        print(f"❌ Unexpected error in track_learning: {e}")
        raise HTTPException(status_code=500, detail="Failed to track learning")


@router.get("/progress")
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
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail="Database connection failed")
    except Exception as e:
        print(f"❌ Unexpected error in get_learning_progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to get learning progress")


@router.get("/skills")
async def list_skills(agent_id: str = "default"):
    """List all skills being tracked"""
    try:
        skills = await engine.list_skills(agent_id=agent_id)
        return skills
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail="Database connection failed")
    except Exception as e:
        print(f"❌ Unexpected error in list_skills: {e}")
        raise HTTPException(status_code=500, detail="Failed to list skills")


@router.get("/velocity")
async def get_learning_velocity(
    agent_id: str = "default",
    days: int = 7
):
    """Get learning velocity (learnings per day)"""
    try:
        velocity = await engine.get_learning_velocity(agent_id=agent_id, days=days)
        return velocity
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail="Database connection failed")
    except Exception as e:
        print(f"❌ Unexpected error in get_learning_velocity: {e}")
        raise HTTPException(status_code=500, detail="Failed to get learning velocity")
