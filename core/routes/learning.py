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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track learning: {str(e)}")


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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learning progress: {str(e)}")


@router.get("/skills")
async def list_skills(agent_id: str = "default"):
    """List all skills being tracked"""
    try:
        skills = await engine.list_skills(agent_id=agent_id)
        return skills
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list skills: {str(e)}")


@router.get("/velocity")
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
