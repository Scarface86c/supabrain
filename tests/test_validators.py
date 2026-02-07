"""
Unit tests for input validators
"""

import pytest
from core.validators import (
    validate_agent_name,
    validate_content,
    validate_tags,
    validate_importance,
    validate_temporal_layer,
    validate_domain,
    ValidationError
)


class TestAgentNameValidation:
    """Test agent name validation"""
    
    def test_valid_names(self):
        """Valid agent names should pass"""
        assert validate_agent_name("Scar") == "Scar"
        assert validate_agent_name("Agent123") == "Agent123"
        assert validate_agent_name("my-agent") == "my-agent"
        assert validate_agent_name("test_agent") == "test_agent"
    
    def test_strips_whitespace(self):
        """Whitespace should be stripped"""
        assert validate_agent_name("  Scar  ") == "Scar"
    
    def test_sql_injection_blocked(self):
        """SQL injection patterns should be rejected"""
        with pytest.raises(ValidationError, match="suspicious patterns"):
            validate_agent_name("Test'; DROP TABLE memories--")
        
        with pytest.raises(ValidationError, match="suspicious patterns"):
            validate_agent_name("admin' OR '1'='1")
        
        with pytest.raises(ValidationError, match="suspicious patterns"):
            validate_agent_name("test; DELETE FROM users")
    
    def test_invalid_characters(self):
        """Special characters should be rejected"""
        with pytest.raises(ValidationError, match="only contain"):
            validate_agent_name("test@agent")
        
        with pytest.raises(ValidationError, match="only contain"):
            validate_agent_name("test agent")  # space not allowed
        
        with pytest.raises(ValidationError, match="only contain"):
            validate_agent_name("test.agent")
    
    def test_empty_name(self):
        """Empty names should be rejected"""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_agent_name("")
        
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_agent_name("   ")
    
    def test_too_long(self):
        """Names exceeding max length should be rejected"""
        long_name = "A" * 51
        with pytest.raises(ValidationError, match="too long"):
            validate_agent_name(long_name)


class TestContentValidation:
    """Test content validation"""
    
    def test_valid_content(self):
        """Valid content should pass"""
        assert validate_content("Hello world") == "Hello world"
        assert validate_content("Multi\nline\ncontent") == "Multi\nline\ncontent"
    
    def test_strips_whitespace(self):
        """Whitespace should be stripped"""
        assert validate_content("  test  ") == "test"
    
    def test_empty_content(self):
        """Empty content should be rejected"""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_content("")
        
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_content("   ")
    
    def test_null_bytes(self):
        """Null bytes should be rejected"""
        with pytest.raises(ValidationError, match="null bytes"):
            validate_content("test\x00content")
    
    def test_too_long(self):
        """Content exceeding max length should be rejected"""
        long_content = "A" * 10001
        with pytest.raises(ValidationError, match="too long"):
            validate_content(long_content)


class TestTagsValidation:
    """Test tags validation"""
    
    def test_valid_tags(self):
        """Valid tags should pass"""
        assert validate_tags(["test", "validation"]) == ["test", "validation"]
        assert validate_tags(["tag-1", "tag_2"]) == ["tag-1", "tag_2"]
    
    def test_strips_and_lowercases(self):
        """Tags should be stripped and lowercased"""
        assert validate_tags(["  Test  ", "VALIDATION"]) == ["test", "validation"]
    
    def test_deduplicates(self):
        """Duplicate tags should be removed"""
        assert validate_tags(["test", "test", "validation"]) == ["test", "validation"]
        assert validate_tags(["Test", "test"]) == ["test"]
    
    def test_skips_empty(self):
        """Empty tags should be skipped"""
        assert validate_tags(["test", "", "  ", "valid"]) == ["test", "valid"]
    
    def test_too_many_tags(self):
        """More than max tags should be rejected"""
        too_many = ["tag" + str(i) for i in range(21)]
        with pytest.raises(ValidationError, match="Too many tags"):
            validate_tags(too_many)
    
    def test_invalid_characters(self):
        """Tags with invalid characters should be rejected"""
        with pytest.raises(ValidationError, match="invalid characters"):
            validate_tags(["test@tag"])
        
        with pytest.raises(ValidationError, match="invalid characters"):
            validate_tags(["test tag"])
    
    def test_tag_too_long(self):
        """Tags exceeding max length should be rejected"""
        long_tag = "A" * 51
        with pytest.raises(ValidationError, match="Tag too long"):
            validate_tags([long_tag])


class TestImportanceValidation:
    """Test importance score validation"""
    
    def test_valid_scores(self):
        """Valid scores should pass"""
        assert validate_importance(0.0) == 0.0
        assert validate_importance(0.5) == 0.5
        assert validate_importance(1.0) == 1.0
    
    def test_accepts_int(self):
        """Integer scores should be converted to float"""
        assert validate_importance(0) == 0.0
        assert validate_importance(1) == 1.0
    
    def test_out_of_range(self):
        """Scores outside 0-1 should be rejected"""
        with pytest.raises(ValidationError, match="between 0.0 and 1.0"):
            validate_importance(-0.1)
        
        with pytest.raises(ValidationError, match="between 0.0 and 1.0"):
            validate_importance(1.1)
    
    def test_invalid_type(self):
        """Non-numeric values should be rejected"""
        with pytest.raises(ValidationError, match="must be a number"):
            validate_importance("0.5")


class TestTemporalLayerValidation:
    """Test temporal layer validation"""
    
    def test_valid_layers(self):
        """Valid layers should pass"""
        for layer in ['working', 'short', 'long', 'archive']:
            assert validate_temporal_layer(layer) == layer
    
    def test_invalid_layer(self):
        """Invalid layers should be rejected"""
        with pytest.raises(ValidationError, match="Invalid temporal layer"):
            validate_temporal_layer("invalid")


class TestDomainValidation:
    """Test domain validation"""
    
    def test_valid_domains(self):
        """Valid domains should pass"""
        for domain in ['self', 'user', 'projects', 'world', 'system', 'general']:
            assert validate_domain(domain) == domain
    
    def test_invalid_domain(self):
        """Invalid domains should be rejected"""
        with pytest.raises(ValidationError, match="Invalid domain"):
            validate_domain("invalid")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
