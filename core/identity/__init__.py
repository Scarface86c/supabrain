"""
SupaBrain Identity Module
Defines agent personality and self-image
"""

from .base import AgentIdentity
from .loader import load_identity, create_default_identity, save_identity

__all__ = ['AgentIdentity', 'load_identity', 'create_default_identity', 'save_identity']
