#!/usr/bin/env python3
"""
Pydantic Models for SupaBrain API
"""

from pydantic import BaseModel, validator
from typing import List, Optional
from validators import (
    validate_agent_name,
    validate_content,
    validate_tags,
    validate_importance,
    validate_temporal_layer,
    validate_domain,
    ValidationError
)


class MemoryCreate(BaseModel):
    content: str
    agent_name: str  # REQUIRED - each agent has unique identity
    tags: Optional[List[str]] = []
    source_type: Optional[str] = None
    importance_score: Optional[float] = 0.5
    memory_type: Optional[str] = None  # Auto-classified if not provided
    temporal_layer: Optional[str] = "long"  # working | short | long | archive
    ttl_hours: Optional[float] = None  # Auto-expire for working memory (can be fractional)
    domain: Optional[str] = "general"  # self | user | projects | world | system | general
    
    # Validators
    @validator('agent_name')
    def validate_agent_name_field(cls, v):
        try:
            return validate_agent_name(v)
        except ValidationError as e:
            raise ValueError(str(e))
    
    @validator('content')
    def validate_content_field(cls, v):
        try:
            return validate_content(v)
        except ValidationError as e:
            raise ValueError(str(e))
    
    @validator('tags')
    def validate_tags_field(cls, v):
        if v is None:
            return []
        try:
            return validate_tags(v)
        except ValidationError as e:
            raise ValueError(str(e))
    
    @validator('importance_score')
    def validate_importance_field(cls, v):
        try:
            return validate_importance(v)
        except ValidationError as e:
            raise ValueError(str(e))
    
    @validator('temporal_layer')
    def validate_temporal_layer_field(cls, v):
        try:
            return validate_temporal_layer(v)
        except ValidationError as e:
            raise ValueError(str(e))
    
    @validator('domain')
    def validate_domain_field(cls, v):
        try:
            return validate_domain(v)
        except ValidationError as e:
            raise ValueError(str(e))


class MemoryQuery(BaseModel):
    query: str
    agent_name: str  # REQUIRED - each agent has unique identity
    limit: Optional[int] = 5
    min_score: Optional[float] = 0.0
    max_layer: Optional[int] = 5  # Search up to this priority layer
    temporal_layers: Optional[List[str]] = None  # Filter by temporal layers
    domain: Optional[str] = None  # Filter by domain
    tags: Optional[List[str]] = None  # Filter by tags
    include_archive: Optional[bool] = False  # Include archived memories
    
    # Validators
    @validator('agent_name')
    def validate_agent_name_field(cls, v):
        try:
            return validate_agent_name(v)
        except ValidationError as e:
            raise ValueError(str(e))
    
    @validator('query')
    def validate_query_field(cls, v):
        try:
            return validate_content(v)  # Same rules as content
        except ValidationError as e:
            raise ValueError(str(e))
    
    @validator('limit')
    def validate_limit_field(cls, v):
        if v < 1 or v > 100:
            raise ValueError("Limit must be between 1 and 100")
        return v
    
    @validator('tags')
    def validate_tags_field(cls, v):
        if v is None:
            return None
        try:
            return validate_tags(v)
        except ValidationError as e:
            raise ValueError(str(e))
    
    @validator('domain')
    def validate_domain_field(cls, v):
        if v is None:
            return None
        try:
            return validate_domain(v)
        except ValidationError as e:
            raise ValueError(str(e))


class LayeredRecallQuery(BaseModel):
    query: str
    agent_name: str
    start_layer: Optional[int] = 1
    max_layer: Optional[int] = 3
    limit_per_layer: Optional[int] = 5
    stop_on_match: Optional[bool] = True
    min_score: Optional[float] = 0.5
    
    @validator('agent_name')
    def validate_agent_name_field(cls, v):
        try:
            return validate_agent_name(v)
        except ValidationError as e:
            raise ValueError(str(e))


class MemoryRelation(BaseModel):
    from_memory_id: int
    to_memory_id: int
    relationship_type: str
    reason: Optional[str] = None


class TagSuggestRequest(BaseModel):
    content: str
    existing_tags: Optional[List[str]] = []
    limit: Optional[int] = 5


class TagCanonicalizeRequest(BaseModel):
    tags: List[str]
