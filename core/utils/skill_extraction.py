#!/usr/bin/env python3
"""
Skill Extraction Utilities
Extracts skills from memory content using pattern matching
"""

import re
from typing import List, Set


# Skill extraction patterns
SKILL_PATTERNS = {
    'languages': [r'\b(python|javascript|typescript|rust|go|java|c\+\+|bash|sql|html|css)\b'],
    'frameworks': [
        r'\b(fastapi|flask|django|react|vue|postgresql|postgres|sqlite|redis|mongodb)\b',
        r'\b(numpy|pandas|transformers|sentence-transformers|uvicorn)\b',
    ],
    'tools': [
        r'\b(docker|kubernetes|git|github|vscode|vim|openclaw|supabrain)\b',
        r'\b(whisper|llm|gpt|claude)\b',
    ],
    'concepts': [
        r'\b(autonomous-decision|memory-architecture|api-design|database-design)\b',
        r'\b(system-architecture|learning-tracking|hierarchical-memory)\b',
        r'\b(semantic-search|embedding|vector-database)\b',
    ],
    'learned': [
        r'learned\s+(\w+(?:-\w+)*)',
        r'implemented\s+(\w+(?:-\w+)*)',
        r'built\s+(\w+(?:-\w+)*)',
        r'created\s+(\w+(?:-\w+)*)',
    ],
}


def extract_skills_from_text(text: str, min_length: int = 3) -> List[str]:
    """
    Extract skills from text content
    
    Args:
        text: Content to analyze
        min_length: Minimum skill name length
    
    Returns:
        Sorted list of unique skills found
    """
    if not text:
        return []
    
    text_lower = text.lower()
    skills: Set[str] = set()
    
    for category, patterns in SKILL_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            
            for match in matches:
                skill = match[0] if isinstance(match, tuple) and match else match
                
                if skill and len(skill) >= min_length:
                    skill_normalized = skill.strip().lower()
                    if skill_normalized not in {'the', 'and', 'for', 'with', 'from', 'this', 'that'}:
                        skills.add(skill_normalized)
    
    return sorted(list(skills))
