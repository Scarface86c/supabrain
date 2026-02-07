#!/usr/bin/env python3
"""
Tag System - Improved memory tagging with categories and hierarchies

Features:
- Tag categories (type, project, skill, priority, status, domain)
- Tag aliases (sb → supabrain)
- Tag canonicalization
- Tag suggestions
- Tag statistics
"""

from typing import List, Set, Dict, Tuple, Optional
import re
from collections import Counter, defaultdict

class TagSystem:
    """Improved tagging system with categories, aliases, and suggestions"""
    
    # Standard tag categories
    CATEGORIES = {
        "type": ["implementation", "design", "documentation", "test", "bug-fix", "refactoring", "review"],
        "project": ["supabrain", "think-cycle", "learning-tracking", "dream-phase", "bct"],
        "skill": ["python", "postgresql", "sql", "fastapi", "bash", "docker", "git", "autonomous-decision"],
        "priority": ["critical", "high", "medium", "low"],
        "status": ["complete", "in-progress", "blocked", "planned", "deprecated"],
        "domain": ["self", "scarface", "system", "project", "world", "general"],
        "source": ["daily-log", "thought-cycle", "auto-captured", "manual"],
    }
    
    # Tag aliases (variants → canonical)
    ALIASES = {
        # Project aliases
        "sb": "supabrain",
        "tc": "think-cycle",
        "lt": "learning-tracking",
        "dp": "dream-phase",
        
        # Type aliases
        "impl": "implementation",
        "doc": "documentation",
        "docs": "documentation",
        
        # Skill aliases
        "pg": "postgresql",
        "postgres": "postgresql",
        "db": "database",
        "py": "python",
        
        # Status aliases
        "done": "complete",
        "wip": "in-progress",
    }
    
    # Common tag patterns (for extraction from content)
    EXTRACTION_PATTERNS = {
        "implementation": r'\b(implement|built|created|added|developed)\b',
        "design": r'\b(design|architected|planned|structured)\b',
        "test": r'\b(test|tested|verify|verified)\b',
        "bug-fix": r'\b(fix|fixed|bug|error|issue)\b',
        "complete": r'\b(complete|completed|finished|done)\b',
        "in-progress": r'\b(building|developing|working on)\b',
    }
    
    def __init__(self):
        # Build reverse lookup: tag → category
        self.tag_to_category = {}
        for category, tags in self.CATEGORIES.items():
            for tag in tags:
                self.tag_to_category[tag] = category
        
        # Build canonical tag set (all valid tags)
        self.canonical_tags = set()
        for tags in self.CATEGORIES.values():
            self.canonical_tags.update(tags)
    
    def canonicalize_tag(self, tag: str) -> str:
        """
        Convert tag to canonical form
        
        Args:
            tag: Raw tag (may have alias)
        
        Returns:
            Canonical tag name
        """
        tag_lower = tag.lower().strip()
        
        # Apply aliases
        if tag_lower in self.ALIASES:
            return self.ALIASES[tag_lower]
        
        return tag_lower
    
    def validate_tag(self, tag: str) -> bool:
        """
        Check if tag is valid (in known categories or follows hierarchy format)
        
        Args:
            tag: Tag to validate
        
        Returns:
            True if valid
        """
        canonical = self.canonicalize_tag(tag)
        
        # Check if in canonical tags
        if canonical in self.canonical_tags:
            return True
        
        # Check if hierarchical (parent:child)
        if ':' in canonical:
            parts = canonical.split(':')
            # Check if parent is valid
            return parts[0] in self.canonical_tags
        
        # Unknown tags are allowed (for flexibility)
        return True
    
    def get_category(self, tag: str) -> Optional[str]:
        """
        Get category for a tag
        
        Args:
            tag: Tag name
        
        Returns:
            Category name or None
        """
        canonical = self.canonicalize_tag(tag)
        
        # Direct lookup
        if canonical in self.tag_to_category:
            return self.tag_to_category[canonical]
        
        # Check hierarchical
        if ':' in canonical:
            parent = canonical.split(':')[0]
            if parent in self.tag_to_category:
                return self.tag_to_category[parent]
        
        return None
    
    def get_tags_by_category(self, category: str) -> List[str]:
        """Get all tags in a category"""
        return self.CATEGORIES.get(category, [])
    
    def suggest_tags(self, content: str, existing_tags: List[str] = None, limit: int = 5) -> List[str]:
        """
        Suggest tags based on content
        
        Args:
            content: Memory content to analyze
            existing_tags: Tags already applied
            limit: Maximum suggestions
        
        Returns:
            List of suggested tags
        """
        existing_tags = existing_tags or []
        existing_set = set(self.canonicalize_tag(t) for t in existing_tags)
        suggestions = []
        
        content_lower = content.lower()
        
        # Extract from patterns
        for tag, pattern in self.EXTRACTION_PATTERNS.items():
            if re.search(pattern, content_lower, re.IGNORECASE):
                canonical = self.canonicalize_tag(tag)
                if canonical not in existing_set:
                    suggestions.append(canonical)
        
        # Extract project names (if mentioned)
        for project in self.CATEGORIES["project"]:
            if project in content_lower:
                if project not in existing_set:
                    suggestions.append(project)
        
        # Extract skills (if mentioned)
        for skill in self.CATEGORIES["skill"]:
            if skill in content_lower:
                if skill not in existing_set:
                    suggestions.append(skill)
        
        # Limit results
        return suggestions[:limit]
    
    def canonicalize_tags(self, tags: List[str]) -> List[str]:
        """
        Canonicalize a list of tags
        
        Args:
            tags: Raw tags
        
        Returns:
            Canonicalized tags (deduplicated)
        """
        canonical = [self.canonicalize_tag(t) for t in tags]
        # Remove duplicates while preserving order
        seen = set()
        result = []
        for tag in canonical:
            if tag not in seen:
                seen.add(tag)
                result.append(tag)
        return result
    
    def group_tags_by_category(self, tags: List[str]) -> Dict[str, List[str]]:
        """
        Group tags by their categories
        
        Args:
            tags: List of tags
        
        Returns:
            Dict mapping category → tags
        """
        groups = defaultdict(list)
        uncategorized = []
        
        for tag in tags:
            category = self.get_category(tag)
            if category:
                groups[category].append(tag)
            else:
                uncategorized.append(tag)
        
        if uncategorized:
            groups["other"] = uncategorized
        
        return dict(groups)
    
    def find_similar_tags(self, tag: str, all_tags: List[str], threshold: float = 0.7) -> List[str]:
        """
        Find tags similar to given tag (for suggesting consolidation)
        
        Args:
            tag: Target tag
            all_tags: All known tags
            threshold: Similarity threshold (0-1)
        
        Returns:
            List of similar tags
        """
        tag_lower = tag.lower()
        similar = []
        
        for other in all_tags:
            if tag == other:
                continue
            
            other_lower = other.lower()
            
            # Simple similarity: check if one is substring of other
            if tag_lower in other_lower or other_lower in tag_lower:
                similar.append(other)
            
            # Check if same words in different order
            tag_words = set(tag_lower.split('-'))
            other_words = set(other_lower.split('-'))
            if tag_words == other_words:
                similar.append(other)
        
        return similar


# Global instance
tag_system = TagSystem()


if __name__ == "__main__":
    # Test cases
    print("🏷️  Tag System Tests\n")
    
    # Test canonicalization
    print("1. Canonicalization:")
    test_tags = ["sb", "impl", "pg", "done", "supabrain"]
    for tag in test_tags:
        canonical = tag_system.canonicalize_tag(tag)
        print(f"   {tag} → {canonical}")
    
    # Test validation
    print("\n2. Validation:")
    test_tags = ["implementation", "supabrain", "invalid-tag-xyz", "supabrain:memory"]
    for tag in test_tags:
        valid = tag_system.validate_tag(tag)
        print(f"   {tag}: {'✅' if valid else '❌'}")
    
    # Test category detection
    print("\n3. Category Detection:")
    test_tags = ["implementation", "python", "critical", "complete", "supabrain"]
    for tag in test_tags:
        category = tag_system.get_category(tag)
        print(f"   {tag} → {category}")
    
    # Test tag suggestions
    print("\n4. Tag Suggestions:")
    test_content = "Implemented dream phase using PostgreSQL. Build complete!"
    suggestions = tag_system.suggest_tags(test_content)
    print(f"   Content: {test_content}")
    print(f"   Suggestions: {suggestions}")
    
    # Test grouping
    print("\n5. Tag Grouping:")
    test_tags = ["implementation", "supabrain", "python", "critical", "complete", "random-tag"]
    grouped = tag_system.group_tags_by_category(test_tags)
    for category, tags in grouped.items():
        print(f"   {category}: {tags}")
