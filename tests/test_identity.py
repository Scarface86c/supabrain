"""
Unit tests for identity module
Tests AgentIdentity class and identity loading/saving
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import sys
import os

# Add core directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from identity import AgentIdentity, load_identity, create_default_identity, save_identity
from identity.loader import save_identity


class TestAgentIdentity:
    """Tests for AgentIdentity class"""
    
    def test_create_basic_identity(self):
        """Test creating a basic identity"""
        identity = AgentIdentity(
            name="TestAgent",
            vibe="Test vibe"
        )
        
        assert identity.name == "TestAgent"
        assert identity.vibe == "Test vibe"
        assert isinstance(identity.created_at, datetime)
        assert identity.core_values == []
        assert identity.strengths == []
    
    def test_create_full_identity(self):
        """Test creating identity with all fields"""
        identity = AgentIdentity(
            name="FullAgent",
            vibe="Complete",
            core_values=["honesty", "learning"],
            communication_style="Direct",
            self_description="I am a test agent",
            strengths=["coding", "testing"],
            growth_areas=["patience"],
            human_name="Tester",
            relationship_type="assistant",
            preferred_domains=["tech", "science"],
            learning_style="hands-on"
        )
        
        assert identity.name == "FullAgent"
        assert len(identity.core_values) == 2
        assert "coding" in identity.strengths
        assert identity.human_name == "Tester"
    
    def test_to_dict(self):
        """Test serialization to dictionary"""
        identity = AgentIdentity(
            name="DictAgent",
            vibe="Serializable",
            core_values=["value1", "value2"]
        )
        
        data = identity.to_dict()
        
        assert isinstance(data, dict)
        assert data["name"] == "DictAgent"
        assert data["vibe"] == "Serializable"
        assert len(data["core_values"]) == 2
        assert isinstance(data["created_at"], str)  # Should be ISO format
    
    def test_from_dict(self):
        """Test deserialization from dictionary"""
        data = {
            "name": "FromDict",
            "created_at": "2026-02-08T12:00:00",
            "vibe": "Deserialized",
            "core_values": ["test"],
            "communication_style": None,
            "self_description": None,
            "strengths": [],
            "growth_areas": [],
            "human_name": None,
            "relationship_type": None,
            "preferred_domains": [],
            "learning_style": None,
            "version": "1.0",
            "custom_fields": {}
        }
        
        identity = AgentIdentity.from_dict(data)
        
        assert identity.name == "FromDict"
        assert identity.vibe == "Deserialized"
        assert isinstance(identity.created_at, datetime)
        assert len(identity.core_values) == 1
    
    def test_roundtrip_serialization(self):
        """Test that to_dict -> from_dict preserves data"""
        original = AgentIdentity(
            name="Roundtrip",
            vibe="Test",
            core_values=["a", "b", "c"],
            strengths=["x", "y"]
        )
        
        data = original.to_dict()
        restored = AgentIdentity.from_dict(data)
        
        assert restored.name == original.name
        assert restored.vibe == original.vibe
        assert restored.core_values == original.core_values
        assert restored.strengths == original.strengths
    
    def test_str_representation(self):
        """Test string representation"""
        identity = AgentIdentity(name="StrAgent", vibe="Friendly")
        
        str_repr = str(identity)
        
        assert "StrAgent" in str_repr
        assert "Friendly" in str_repr
    
    def test_str_representation_no_vibe(self):
        """Test string representation without vibe"""
        identity = AgentIdentity(name="NoVibe")
        
        str_repr = str(identity)
        
        assert "NoVibe" in str_repr
        assert "no vibe defined" in str_repr
    
    def test_custom_fields(self):
        """Test custom fields dictionary"""
        identity = AgentIdentity(
            name="CustomAgent",
            custom_fields={"key1": "value1", "key2": 42}
        )
        
        assert identity.custom_fields["key1"] == "value1"
        assert identity.custom_fields["key2"] == 42


class TestIdentityLoader:
    """Tests for identity loading and saving"""
    
    def setup_method(self):
        """Create temporary directory for tests"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.temp_dir)
    
    def test_create_default_identity(self):
        """Test creating default identity"""
        identity = create_default_identity("NewAgent")
        
        assert identity.name == "NewAgent"
        assert "New agent" in identity.vibe
        assert len(identity.core_values) > 0
        assert identity.self_description is not None
    
    def test_save_identity(self):
        """Test saving identity to file"""
        identity = AgentIdentity(
            name="SaveTest",
            vibe="Saveable"
        )
        
        success = save_identity(identity, config_dir=self.temp_dir)
        
        assert success
        
        # Check file exists
        identity_file = Path(self.temp_dir) / "savetest.json"
        assert identity_file.exists()
        
        # Check file content
        with open(identity_file, 'r') as f:
            data = json.load(f)
            assert data["name"] == "SaveTest"
            assert data["vibe"] == "Saveable"
    
    def test_load_existing_identity(self):
        """Test loading existing identity from file"""
        # Create and save identity
        original = AgentIdentity(
            name="LoadTest",
            vibe="Loadable",
            core_values=["test1", "test2"]
        )
        save_identity(original, config_dir=self.temp_dir)
        
        # Load it back
        loaded = load_identity("LoadTest", config_dir=self.temp_dir)
        
        assert loaded.name == "LoadTest"
        assert loaded.vibe == "Loadable"
        assert len(loaded.core_values) == 2
    
    def test_load_nonexistent_identity(self):
        """Test loading non-existent identity creates default"""
        identity = load_identity("NonExistent", config_dir=self.temp_dir)
        
        assert identity.name == "NonExistent"
        assert "New agent" in identity.vibe
        assert len(identity.core_values) > 0
    
    def test_load_identity_case_insensitive(self):
        """Test that identity loading is case-insensitive"""
        # Save with mixed case
        identity = AgentIdentity(name="MixedCase", vibe="Test")
        save_identity(identity, config_dir=self.temp_dir)
        
        # Load with different case
        loaded = load_identity("MIXEDCASE", config_dir=self.temp_dir)
        
        assert loaded.name == "MixedCase"
        assert loaded.vibe == "Test"
    
    def test_save_identity_creates_directory(self):
        """Test that save_identity creates directory if it doesn't exist"""
        nested_dir = Path(self.temp_dir) / "nested" / "path"
        
        identity = AgentIdentity(name="Nested", vibe="Test")
        success = save_identity(identity, config_dir=str(nested_dir))
        
        assert success
        assert nested_dir.exists()
        assert (nested_dir / "nested.json").exists()
    
    def test_load_corrupted_identity_file(self):
        """Test loading corrupted JSON file falls back to default"""
        # Create corrupted JSON file
        identity_file = Path(self.temp_dir) / "corrupted.json"
        with open(identity_file, 'w') as f:
            f.write("{ invalid json }")
        
        # Should fall back to default
        identity = load_identity("Corrupted", config_dir=self.temp_dir)
        
        assert identity.name == "Corrupted"
        assert "New agent" in identity.vibe


class TestIdentityIntegration:
    """Integration tests for identity system"""
    
    def setup_method(self):
        """Create temporary directory for tests"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.temp_dir)
    
    def test_complete_identity_lifecycle(self):
        """Test creating, saving, loading, modifying, saving again"""
        # Create
        identity = create_default_identity("Lifecycle")
        identity.vibe = "Evolving"
        identity.strengths.append("persistence")
        
        # Save
        save_identity(identity, config_dir=self.temp_dir)
        
        # Load
        loaded = load_identity("Lifecycle", config_dir=self.temp_dir)
        assert loaded.vibe == "Evolving"
        assert "persistence" in loaded.strengths
        
        # Modify
        loaded.growth_areas.append("patience")
        loaded.core_values.append("kindness")
        
        # Save again
        save_identity(loaded, config_dir=self.temp_dir)
        
        # Load again
        final = load_identity("Lifecycle", config_dir=self.temp_dir)
        assert "patience" in final.growth_areas
        assert "kindness" in final.core_values
    
    def test_multiple_agents_same_directory(self):
        """Test storing multiple agent identities in same directory"""
        agents = ["Agent1", "Agent2", "Agent3"]
        
        for agent_name in agents:
            identity = AgentIdentity(
                name=agent_name,
                vibe=f"{agent_name} vibe"
            )
            save_identity(identity, config_dir=self.temp_dir)
        
        # Load all and verify
        for agent_name in agents:
            loaded = load_identity(agent_name, config_dir=self.temp_dir)
            assert loaded.name == agent_name
            assert f"{agent_name} vibe" in loaded.vibe


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
