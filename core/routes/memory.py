"""
Memory CRUD and recall endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel

# Will import models after they're properly extracted
# from models import MemoryCreate, MemoryQuery, MemoryResponse, RememberResponse

router = APIRouter(prefix="/api/v1", tags=["memory"])

# Note: Actual endpoint implementations will be migrated from server.py
# This is the structure - full migration in progress

# Endpoints to migrate:
# POST /api/v1/remember
# POST /api/v1/recall
# POST /api/v1/recall/layered
# DELETE /api/v1/memory/{memory_id}
# POST /api/v1/memory/relate
# GET /api/v1/memory/{memory_id}/related
