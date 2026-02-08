"""
Statistics and analytics endpoints
"""

from fastapi import APIRouter, HTTPException
from models import StatsResponse, LayerStatsResponse
from memory_engine import engine

router = APIRouter(prefix="/api/v1", tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
async def get_stats(agent_name: str):
    """Get memory system statistics for an agent"""
    try:
        stats = await engine.get_stats(agent_name=agent_name)
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/analytics")
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


@router.get("/stats/layers", response_model=LayerStatsResponse)
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
