"""
SupaBrain custom exceptions

Better error handling through specific exception types.
"""
from typing import Optional, Any


class SupaBrainError(Exception):
    """Base exception for all SupaBrain errors"""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message: str = message
        self.details: dict[str, Any] = details or {}


class MemoryError(SupaBrainError):
    """Memory operation failed"""
    pass


class IdentityError(SupaBrainError):
    """Identity loading/saving failed"""
    pass


class DatabaseError(SupaBrainError):
    """Database operation failed"""
    pass


class EmbeddingError(SupaBrainError):
    """Embedding generation failed"""
    pass


class ValidationError(SupaBrainError):
    """Input validation failed"""
    pass


class QueueError(SupaBrainError):
    """Think queue operation failed"""
    pass


class MemoryNotFoundError(SupaBrainError):
    """Memory not found in database"""
    
    def __init__(self, memory_id: int, message: Optional[str] = None) -> None:
        self.memory_id: int = memory_id
        msg: str = message or f"Memory {memory_id} not found"
        super().__init__(msg)


class InvalidDecisionError(SupaBrainError):
    """Invalid decision in sleep cycle"""
    pass


class RelationshipError(SupaBrainError):
    """Relationship operation failed"""
    pass
