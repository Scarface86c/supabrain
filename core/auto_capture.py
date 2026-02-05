#!/usr/bin/env python3
"""
SupaBrain Auto-Capture System

Automatically captures significant events to working memory.
Hooks into tool calls, analysis, learnings, and decisions.

Usage:
    from auto_capture import auto_capture, CaptureType
    
    auto_capture(CaptureType.LEARNING, "Learned that story > features")
    auto_capture(CaptureType.TOOL_USE, "Executed git push", context={"repo": "supabrain"})
"""

import sys
import os
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import inspect

# Add supabrain_queue to path
sys.path.append(os.path.dirname(__file__))
from supabrain_queue import MemoryQueue

class CaptureType(Enum):
    """Types of events to capture"""
    LEARNING = "learning"           # New insights, patterns recognized
    DECISION = "decision"           # Choices made
    ERROR = "error"                 # Things that went wrong
    USER_FEEDBACK = "user_feedback" # Scarface said something important
    ANALYSIS = "analysis"           # Analyzed documents, code, data
    TOOL_USE = "tool_use"          # Used exec, read, write, web_search
    FILE_READ = "file_read"        # Read a file
    FILE_WRITE = "file_write"      # Wrote/edited a file
    TASK_COMPLETE = "task_complete" # Finished a task
    QUESTION = "question"          # Asked or answered a question
    MILESTONE = "milestone"        # Important achievement

# TTL mapping (hours)
TTL_MAP = {
    CaptureType.LEARNING: 4,       # Keep learnings longer
    CaptureType.DECISION: 3,       # Decisions important
    CaptureType.ERROR: 2,          # Errors medium priority
    CaptureType.USER_FEEDBACK: 4,  # Scarface feedback very important
    CaptureType.ANALYSIS: 2,       # Analysis results medium
    CaptureType.TOOL_USE: 1,       # Tool usage expires fast
    CaptureType.FILE_READ: 1,      # File reads expire fast
    CaptureType.FILE_WRITE: 2,     # File writes medium
    CaptureType.TASK_COMPLETE: 3,  # Completed tasks important
    CaptureType.QUESTION: 2,       # Questions medium
    CaptureType.MILESTONE: 168,    # Milestones = 7 days (move to long-term)
}

# Domain mapping
DOMAIN_MAP = {
    CaptureType.LEARNING: "self",
    CaptureType.DECISION: "projects",
    CaptureType.ERROR: "system",
    CaptureType.USER_FEEDBACK: "user",
    CaptureType.ANALYSIS: "general",
    CaptureType.TOOL_USE: "system",
    CaptureType.FILE_READ: "system",
    CaptureType.FILE_WRITE: "projects",
    CaptureType.TASK_COMPLETE: "projects",
    CaptureType.QUESTION: "general",
    CaptureType.MILESTONE: "projects",
}

# Global queue instance
_queue = None

def get_queue() -> MemoryQueue:
    """Get or create queue instance"""
    global _queue
    if _queue is None:
        _queue = MemoryQueue()
    return _queue

def auto_capture(
    event_type: CaptureType,
    content: str,
    context: Optional[Dict[str, Any]] = None,
    ttl_hours: Optional[int] = None,
    domain: Optional[str] = None,
    tags: Optional[list] = None
) -> Dict:
    """
    Auto-capture an event to working memory
    
    Args:
        event_type: Type of event (CaptureType enum)
        content: Description of what happened
        context: Additional context (optional)
        ttl_hours: Override default TTL (optional)
        domain: Override default domain (optional)
        tags: Additional tags (optional)
    
    Returns:
        Dict with memory data
    """
    # Get defaults
    if ttl_hours is None:
        ttl_hours = TTL_MAP.get(event_type, 2)
    
    if domain is None:
        domain = DOMAIN_MAP.get(event_type, "general")
    
    # Build tags
    event_tags = [event_type.value, "auto-captured"]
    if tags:
        event_tags.extend(tags)
    
    # Get caller info
    caller_frame = inspect.stack()[1]
    caller_info = {
        "function": caller_frame.function,
        "file": os.path.basename(caller_frame.filename),
        "line": caller_frame.lineno
    }
    
    # Merge context
    full_context = {
        "timestamp": datetime.now().isoformat(),
        "caller": caller_info,
        **(context or {})
    }
    
    # Store in queue
    queue = get_queue()
    memory = queue.remember(
        content=content,
        domain=domain,
        temporal_layer="working",
        ttl_hours=ttl_hours,
        tags=event_tags,
        metadata=full_context
    )
    
    return memory

# Convenience functions
def capture_learning(content: str, **kwargs):
    """Capture a learning/insight"""
    return auto_capture(CaptureType.LEARNING, content, **kwargs)

def capture_decision(content: str, **kwargs):
    """Capture a decision made"""
    return auto_capture(CaptureType.DECISION, content, **kwargs)

def capture_error(content: str, **kwargs):
    """Capture an error that occurred"""
    return auto_capture(CaptureType.ERROR, content, **kwargs)

def capture_feedback(content: str, **kwargs):
    """Capture user feedback"""
    return auto_capture(CaptureType.USER_FEEDBACK, content, **kwargs)

def capture_analysis(content: str, **kwargs):
    """Capture analysis results"""
    return auto_capture(CaptureType.ANALYSIS, content, **kwargs)

def capture_tool_use(tool: str, details: str, **kwargs):
    """Capture tool usage"""
    content = f"Used {tool}: {details}"
    return auto_capture(CaptureType.TOOL_USE, content, **kwargs)

def capture_file_op(operation: str, path: str, **kwargs):
    """Capture file operation"""
    event_type = CaptureType.FILE_WRITE if operation in ["write", "edit"] else CaptureType.FILE_READ
    content = f"{operation.capitalize()} file: {path}"
    return auto_capture(event_type, content, context={"path": path}, **kwargs)

def capture_milestone(content: str, **kwargs):
    """Capture a milestone"""
    return auto_capture(CaptureType.MILESTONE, content, **kwargs)

# Stats tracking
def capture_stats() -> Dict:
    """Get capture statistics"""
    queue = get_queue()
    memories = queue.read_all()
    
    # Count by type
    type_counts = {}
    for memory in memories:
        tags = memory.get("tags", [])
        for tag in tags:
            if tag in [t.value for t in CaptureType]:
                type_counts[tag] = type_counts.get(tag, 0) + 1
    
    return {
        "total_captured": len(memories),
        "by_type": type_counts,
        "queue_file": str(queue.queue_file)
    }

if __name__ == "__main__":
    # Test the auto-capture system
    print("🧪 Testing Auto-Capture System\n")
    
    # Test different event types
    print("1. Capturing learning...")
    capture_learning("Story beats features in posts (tested on Moltbook)")
    
    print("\n2. Capturing decision...")
    capture_decision("Using cheap LLM (Haiku) for consolidation to optimize costs")
    
    print("\n3. Capturing tool use...")
    capture_tool_use("git", "pushed 6 commits to supabrain repo")
    
    print("\n4. Capturing milestone...")
    capture_milestone("v0.3 consciousness bootstrap complete")
    
    print("\n5. Capturing file operation...")
    capture_file_op("write", "auto_capture.py")
    
    # Show stats
    print("\n" + "="*60)
    print("📊 Capture Statistics:")
    print("="*60)
    stats = capture_stats()
    print(f"Total captured: {stats['total_captured']}")
    print(f"By type: {stats['by_type']}")
    print(f"Queue file: {stats['queue_file']}")
    print("="*60)
    
    print("\n✅ Auto-capture system working!")
