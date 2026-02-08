"""
Context recovery endpoint
"""

from fastapi import APIRouter, HTTPException
from memory_engine import engine

router = APIRouter(prefix="/api/v1/recovery", tags=["recovery"])


@router.get("/context")
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
