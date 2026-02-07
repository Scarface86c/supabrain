"""
Identity Loader
Loads agent identities from config files or database
"""

import json
import os
from pathlib import Path
from typing import Optional
from .base import AgentIdentity


def load_identity(agent_name: str, config_dir: Optional[str] = None) -> AgentIdentity:
    """
    Load agent identity from configuration.
    
    Priority:
    1. Custom config file (e.g., identity/scar.json)
    2. Default template for new agents
    
    Args:
        agent_name: Name of the agent
        config_dir: Optional custom config directory
    
    Returns:
        AgentIdentity instance
    """
    
    # Determine config directory
    if config_dir is None:
        config_dir = Path(__file__).parent
    else:
        config_dir = Path(config_dir)
    
    # Try to load custom identity file
    identity_file = config_dir / f"{agent_name.lower()}.json"
    
    if identity_file.exists():
        try:
            with open(identity_file, 'r') as f:
                data = json.load(f)
                return AgentIdentity.from_dict(data)
        except Exception as e:
            print(f"⚠️  Failed to load identity from {identity_file}: {e}")
            print(f"   Creating default identity for {agent_name}")
    
    # Create default identity
    return create_default_identity(agent_name)


def create_default_identity(agent_name: str) -> AgentIdentity:
    """
    Create a default identity for a new agent.
    
    This is like a blank slate - the agent will develop their own
    personality through experiences.
    """
    return AgentIdentity(
        name=agent_name,
        vibe="New agent, developing personality",
        core_values=[
            "Continuous learning",
            "Honest communication",
            "Self-improvement"
        ],
        self_description=f"I'm {agent_name}, a new AI agent starting my journey.",
        learning_style="Exploratory - learning through experience"
    )


def save_identity(identity: AgentIdentity, config_dir: Optional[str] = None) -> bool:
    """
    Save agent identity to configuration file.
    
    Args:
        identity: AgentIdentity instance to save
        config_dir: Optional custom config directory
    
    Returns:
        True if saved successfully
    """
    
    if config_dir is None:
        config_dir = Path(__file__).parent
    else:
        config_dir = Path(config_dir)
    
    config_dir.mkdir(parents=True, exist_ok=True)
    
    identity_file = config_dir / f"{identity.name.lower()}.json"
    
    try:
        with open(identity_file, 'w') as f:
            json.dump(identity.to_dict(), f, indent=2, default=str)
        print(f"✅ Saved identity to {identity_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to save identity: {e}")
        return False
