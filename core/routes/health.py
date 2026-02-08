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
        if engine.db_pool:
            # Simple DB check
            async with engine.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            db_status = "connected"
        else:
            db_status = "not connected"
    except ConnectionError as e:
        db_status = "connection_failed"
        print(f"❌ Database connection error in health check: {e}")
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"  # Truncate error message
        print(f"❌ Unexpected error in health check: {e}")
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "model": engine.model_name if engine.model else "not loaded"
    }
