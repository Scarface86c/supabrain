# Integration Examples

Practical examples showing how to integrate SupaBrain into your projects.

## Examples

### 1. Simple Script Integration

**File:** `simple_script.py`

Shows basic integration for any Python script:
- Import auto_capture functions
- Capture events as they happen
- Different event types (analysis, learning, decision, error)
- Automatic consolidation via sleep cycle

**Use when:** You have a Python script that does analysis, makes decisions, or processes data.

```bash
python simple_script.py
```

### 2. Heartbeat Integration

**File:** `heartbeat_example.py`

Shows integration with periodic tasks (cron, heartbeat):
- Activity tracking
- Periodic checks (system health, project status)
- Automatic sleep cycle triggers
- Can run continuously or as cron job

**Use when:** You have periodic tasks (monitoring, checks, maintenance).

```bash
# Single run (cron mode)
python heartbeat_example.py

# Continuous (testing)
python heartbeat_example.py --continuous --interval 60
```

## Integration Patterns

### Pattern 1: Capture at Key Points

```python
from auto_capture import capture_milestone, capture_learning

# At start
capture_milestone("Starting important task")

# When learning something
if new_insight:
    capture_learning(f"Discovered: {insight}")

# At completion
capture_milestone("Task complete")
```

### Pattern 2: Capture Decisions

```python
from auto_capture import capture_decision

# When making a choice
if condition:
    action = "scale_up"
    reason = "Load exceeded threshold"
else:
    action = "maintain"
    reason = "Load normal"

capture_decision(
    f"Decision: {action}. Reason: {reason}",
    context={"load": current_load},
    tags=["infrastructure"]
)
```

### Pattern 3: Capture Analysis Results

```python
from auto_capture import capture_analysis

# After analyzing data
results = analyze(data)

capture_analysis(
    f"Analyzed {len(data)} items: {summary(results)}",
    context=results,
    tags=["data-analysis"]
)
```

### Pattern 4: Error Handling

```python
from auto_capture import capture_error

try:
    risky_operation()
except Exception as e:
    capture_error(
        f"Operation failed: {str(e)}",
        context={"error_type": type(e).__name__},
        tags=["error", "operation"]
    )
    raise
```

## Memory Flow

```
1. Your Script
   ↓
2. capture_*() functions
   ↓
3. Offline Queue (~/.supabrain_queue.jsonl)
   ↓
4. Working Memory (when SupaBrain server up)
   ↓
5. Sleep Cycle (periodic review)
   ↓
6. Long-term Storage (important memories)
```

## Best Practices

### Do:
✅ Capture at key decision points
✅ Include context in captures
✅ Use appropriate event types
✅ Tag memories for findability
✅ Run sleep cycle regularly

### Don't:
❌ Capture trivial actions (e.g., every print statement)
❌ Capture sensitive data (passwords, tokens)
❌ Forget to run sleep cycle (memories pile up)
❌ Capture redundant information
❌ Skip error captures (you'll want to remember failures)

## Cost Optimization

**Aggressive Capture:**
- Pro: Never miss anything
- Con: Higher consolidation costs

**Selective Capture:**
- Pro: Lower costs
- Con: Might miss important moments

**Recommended:** Start aggressive, adjust based on sleep cycle stats.

**Typical costs with Haiku model:**
- 50 memories/day × $0.0008 = **$0.04/day**
- 1000 memories/day × $0.0008 × 20 = **$0.16/day**

## Integration Checklist

When adding SupaBrain to a project:

- [ ] Import auto_capture functions
- [ ] Identify key decision points
- [ ] Add captures at those points
- [ ] Choose appropriate event types
- [ ] Add meaningful tags
- [ ] Include context when useful
- [ ] Set up sleep cycle automation
- [ ] Test with --dry-run first
- [ ] Monitor consolidation results
- [ ] Adjust capture strategy as needed

## Troubleshooting

**Q: My memories aren't being captured**
A: Check if offline queue is working:
```bash
python -c "from supabrain_queue import MemoryQueue; print(MemoryQueue().count())"
```

**Q: Sleep cycle never runs**
A: Check activity timestamp and threshold:
```bash
python heartbeat_sleep.py  # Should show status
```

**Q: Too many trivial memories**
A: Adjust your capture strategy - be more selective about what events to capture.

**Q: Important memories getting forgotten**
A: Review sleep cycle decisions with --dry-run. Might need to switch to better model (Sonnet).

## Next Steps

1. Pick an integration pattern
2. Add to your project
3. Test with simple_script.py
4. Run sleep cycle
5. Check results
6. Iterate

## Support

- Docs: See [AUTO_CAPTURE_README.md](../../docs/AUTO_CAPTURE_README.md)
- Sleep cycle: See [SLEEP_CYCLE_README.md](../../docs/SLEEP_CYCLE_README.md)
- Issues: https://github.com/Scarface86c/supabrain/issues
