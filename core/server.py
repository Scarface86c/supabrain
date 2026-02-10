#!/usr/bin/env python3
"""
SupaBrain Core Server
Multi-Layer Memory System for AI Agents
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os

from memory_engine import engine
from rate_limiter import rate_limit_middleware
from auth import auth_middleware

# Import routers
from routes import health, memory, stats, review, tags, learning, identity, recovery, analytics

# Configuration
DEFAULT_AGENT_NAME = os.getenv("DEFAULT_AGENT_NAME", None)  # No default - must be explicit!
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")  # Comma-separated list from env


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
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

# Rate limiting middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limit_middleware)

# Include routers
app.include_router(health.router)
app.include_router(memory.router)
app.include_router(stats.router)
app.include_router(review.router)
app.include_router(tags.router)
app.include_router(learning.router)
app.include_router(identity.router)
app.include_router(recovery.router)
app.include_router(analytics.router)


# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
