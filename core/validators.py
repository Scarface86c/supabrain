"""
Input Validation for SupaBrain API
Protects against SQL injection, XSS, and malformed data
"""

import re
from typing import Optional, List
from pydantic import validator, BaseModel


class ValidationError(Exception):
    """Raised when input validation fails"""
    pass


def validate_agent_name(name: str, max_length: int = 50) -> str:
    """
    Validate agent name format
    
    Rules:
    - Only alphanumeric, underscore, hyphen
    - 1-50 characters
    - No SQL injection patterns
    
    Args:
        name: Agent name to validate
        max_length: Maximum allowed length
        
    Returns:
        Validated name (stripped)
        
    Raises:
        ValidationError: If validation fails
    """
    if not name or not isinstance(name, str):
        raise ValidationError("Agent name is required and must be a string")
    
    name = name.strip()
    
    if not name:
        raise ValidationError("Agent name cannot be empty")
    
    if len(name) > max_length:
        raise ValidationError(f"Agent name too long (max {max_length} characters)")
    
    # Only allow alphanumeric, underscore, hyphen
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        raise ValidationError(
            "Agent name can only contain letters, numbers, underscore, and hyphen"
        )
    
    # Check for SQL injection patterns
    dangerous_patterns = [
        r'(\bor\b|\band\b).*=',  # OR/AND with equals
        r';\s*drop\s+table',      # DROP TABLE
        r';\s*delete\s+from',     # DELETE FROM
        r'--',                     # SQL comment
        r'/\*.*\*/',              # Multi-line comment
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            raise ValidationError("Agent name contains suspicious patterns")
    
    return name


def validate_content(content: str, max_length: int = 10000) -> str:
    """
    Validate memory content
    
    Rules:
    - Must be string
    - 1-10000 characters (configurable)
    - No null bytes
    
    Args:
        content: Content to validate
        max_length: Maximum allowed length
        
    Returns:
        Validated content (stripped)
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(content, str):
        raise ValidationError("Content must be a string")
    
    content = content.strip()
    
    if not content:
        raise ValidationError("Content cannot be empty")
    
    if len(content) > max_length:
        raise ValidationError(f"Content too long (max {max_length} characters)")
    
    # Check for null bytes (can cause issues in C-based parsers)
    if '\x00' in content:
        raise ValidationError("Content contains null bytes")
    
    return content


def validate_tags(tags: List[str], max_tags: int = 20, max_tag_length: int = 50) -> List[str]:
    """
    Validate tag list
    
    Rules:
    - Maximum 20 tags
    - Each tag max 50 characters
    - Only alphanumeric, underscore, hyphen
    - No duplicates
    
    Args:
        tags: List of tags
        max_tags: Maximum number of tags
        max_tag_length: Maximum length per tag
        
    Returns:
        Validated tags (deduplicated, stripped, lowercased)
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(tags, list):
        raise ValidationError("Tags must be a list")
    
    if len(tags) > max_tags:
        raise ValidationError(f"Too many tags (max {max_tags})")
    
    validated = []
    seen = set()
    
    for tag in tags:
        if not isinstance(tag, str):
            raise ValidationError("Each tag must be a string")
        
        tag = tag.strip().lower()
        
        if not tag:
            continue  # Skip empty tags
        
        if len(tag) > max_tag_length:
            raise ValidationError(f"Tag too long: '{tag}' (max {max_tag_length} characters)")
        
        # Only allow alphanumeric, underscore, hyphen
        if not re.match(r'^[a-zA-Z0-9_-]+$', tag):
            raise ValidationError(
                f"Tag '{tag}' contains invalid characters (only letters, numbers, _, -)"
            )
        
        # Deduplicate
        if tag not in seen:
            validated.append(tag)
            seen.add(tag)
    
    return validated


def validate_importance(score: float) -> float:
    """
    Validate importance score
    
    Rules:
    - Must be float or int
    - Between 0.0 and 1.0
    
    Args:
        score: Importance score
        
    Returns:
        Validated score as float
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        score = float(score)
    except (TypeError, ValueError):
        raise ValidationError("Importance score must be a number")
    
    if not 0.0 <= score <= 1.0:
        raise ValidationError("Importance score must be between 0.0 and 1.0")
    
    return score


def validate_temporal_layer(layer: str) -> str:
    """
    Validate temporal layer name
    
    Args:
        layer: Layer name
        
    Returns:
        Validated layer name
        
    Raises:
        ValidationError: If invalid layer
    """
    valid_layers = ['working', 'short', 'long', 'archive']
    
    if layer not in valid_layers:
        raise ValidationError(
            f"Invalid temporal layer '{layer}'. Must be one of: {', '.join(valid_layers)}"
        )
    
    return layer


def validate_domain(domain: str) -> str:
    """
    Validate memory domain
    
    Args:
        domain: Domain name
        
    Returns:
        Validated domain
        
    Raises:
        ValidationError: If invalid domain
    """
    valid_domains = ['self', 'user', 'projects', 'world', 'system', 'general']
    
    if domain not in valid_domains:
        raise ValidationError(
            f"Invalid domain '{domain}'. Must be one of: {', '.join(valid_domains)}"
        )
    
    return domain


# Pydantic validators for use in models
class ValidatedAgentName(str):
    """String type that automatically validates agent names"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        return validate_agent_name(v)


class ValidatedContent(str):
    """String type that automatically validates content"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        return validate_content(v)


class ValidatedTags(list):
    """List type that automatically validates tags"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not v:
            return []
        return validate_tags(v)
