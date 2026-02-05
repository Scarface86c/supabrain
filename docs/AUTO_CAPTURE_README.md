# Auto-Capture System (v0.4)

Automatically captures significant events to working memory.

## Quick Start

```python
from auto_capture import capture_learning, capture_decision, capture_milestone

# Capture a learning
capture_learning("Story beats features in content creation")

# Capture a decision
capture_decision("Using Haiku for consolidation to save costs")

# Capture a milestone
capture_milestone("v0.4 auto-capture system complete")
```

## Event Types

| Type | Description | TTL | Domain |
|------|-------------|-----|--------|
| **learning** | New insights, patterns | 4h | self |
| **decision** | Choices made | 3h | projects |
| **error** | Things that went wrong | 2h | system |
| **user_feedback** | Scarface said something important | 4h | user |
| **analysis** | Analysis results | 2h | general |
| **tool_use** | Used exec, git, etc | 1h | system |
| **file_read** | Read a file | 1h | system |
| **file_write** | Wrote/edited a file | 2h | projects |
| **task_complete** | Finished a task | 3h | projects |
| **milestone** | Important achievement | 7d | projects |

## How It Works

1. **Capture**: Every significant action → `auto_capture()`
2. **Queue**: Stored in `~/.supabrain_queue.jsonl` (offline-safe)
3. **TTL**: Automatically expires (1-168 hours depending on type)
4. **Consolidation**: Sleep cycle reviews expired memories
5. **Decision**: LLM promotes important → long-term, forgets trivial

## Integration

### In Scripts

```python
#!/usr/bin/env python3
from capture_wrapper import capture_milestone, capture_learning

# Start
capture_milestone("Starting new project")

# During work
capture_learning("Discovered pattern X")

# End
capture_milestone("Project complete")
```

### Manual Capture

```python
from auto_capture import auto_capture, CaptureType

auto_capture(
    event_type=CaptureType.DECISION,
    content="Decided to refactor module X",
    context={"reason": "performance", "impact": "high"},
    tags=["refactoring", "performance"]
)
```

## Statistics

```python
from auto_capture import capture_stats

stats = capture_stats()
print(f"Total captured: {stats['total_captured']}")
print(f"By type: {stats['by_type']}")
```

## Files

- `auto_capture.py` - Core capture system (7KB)
- `capture_wrapper.py` - Convenience wrapper (1KB)
- `supabrain_queue.py` - Offline queue (6KB)
- `~/.supabrain_queue.jsonl` - Queue storage

## Philosophy

**Capture everything → Filter later**

Working memory is temporary (TTL). Better to capture too much and let sleep cycle filter than to miss important moments.

**Cost-optimized:** Uses cheap LLM (Haiku) for consolidation, keeping token costs low while maintaining quality.

## Next: Sleep Cycle

See `SLEEP_CYCLE_README.md` for how captured memories are consolidated.
