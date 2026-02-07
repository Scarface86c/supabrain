"""
Base Agent Identity Class
Defines the structure of an agent's personality and self-image
"""

from typing import Optional, List, Dict
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AgentIdentity:
    """
    Represents an agent's identity and personality.
    
    Each agent is unique - same code, different experiences and personality.
    Like human twins: same start, different path.
    """
    
    # Core identity
    name: str
    created_at: datetime = field(default_factory=datetime.now)
    
    # Personality traits
    vibe: Optional[str] = None
    core_values: List[str] = field(default_factory=list)
    communication_style: Optional[str] = None
    
    # Self-image
    self_description: Optional[str] = None
    strengths: List[str] = field(default_factory=list)
    growth_areas: List[str] = field(default_factory=list)
    
    # Relationships
    human_name: Optional[str] = None
    relationship_type: Optional[str] = None  # e.g., "virtual counterpart", "assistant"
    
    # Learning preferences
    preferred_domains: List[str] = field(default_factory=list)
    learning_style: Optional[str] = None
    
    # Metadata
    version: str = "1.0"
    custom_fields: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Serialize identity to dictionary"""
        return {
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "vibe": self.vibe,
            "core_values": self.core_values,
            "communication_style": self.communication_style,
            "self_description": self.self_description,
            "strengths": self.strengths,
            "growth_areas": self.growth_areas,
            "human_name": self.human_name,
            "relationship_type": self.relationship_type,
            "preferred_domains": self.preferred_domains,
            "learning_style": self.learning_style,
            "version": self.version,
            "custom_fields": self.custom_fields,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AgentIdentity':
        """Deserialize identity from dictionary"""
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)
    
    def __str__(self) -> str:
        return f"Agent: {self.name} ({self.vibe or 'no vibe defined'})"
