"""
Health and status endpoints
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SupaBrain",
        "version": "0.2.0",
        "status": "operational",
        "docs": "/docs"
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    Returns database connectivity and model status
    """
    from memory_engine import engine
    
    # Check database connectivity
    try:
        # Simple query to verify connection
        result = await engine.pool.fetch("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "model": engine.model_name
    }
