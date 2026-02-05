# Sleep Cycle - Memory Consolidation (v0.4)

LLM-driven memory consolidation, inspired by REM sleep in humans.

## What It Does

Reviews expired working memories and decides:
- **IMPORTANT** → Promote to long-term (keep forever)
- **CONTEXT** → Extend to short-term (review in 7 days)
- **ARCHIVE** → Move to archive (completed, low priority)
- **FORGET** → Delete (trivial, noise)

## Quick Start

```bash
# Preview decisions (no changes)
python core/sleep_cycle.py --dry-run

# Run consolidation
python core/sleep_cycle.py

# Use better model (more expensive)
python core/sleep_cycle.py --model claude-3-5-sonnet-20241022
```

## How It Works

### 1. Fetch Expired Memories

Sleep cycle queries SupaBrain for memories where TTL expired:

```python
GET /api/v1/review/pending
→ Returns list of expired working memories
```

### 2. Batch Review

Processes memories in batches (default: 20 per call):

```
Batch 1: Memories 1-20 → LLM
Batch 2: Memories 21-40 → LLM
...
```

**Why batching?**
- Reduces API calls
- More context for LLM (sees related memories)
- Cost-effective

### 3. LLM Decision

For each memory, LLM considers:
- Is this needed for future decisions?
- Does it represent growth/learning?
- Is it unique or redundant?
- Does it have lasting value?

Returns decisions:
```json
[
  {"id": 1, "decision": "important", "reason": "Key learning about content strategy"},
  {"id": 2, "decision": "forget", "reason": "Routine command execution"}
]
```

### 4. Apply Decisions

```python
POST /api/v1/review/decide
{
  "memory_id": 1,
  "decision": "important",
  "reason": "Key learning"
}
```

- **important** → temporal_layer = "long"
- **context** → temporal_layer = "short", ttl = 7 days
- **archive** → temporal_layer = "archive"
- **forget** → deleted

### 5. Stats Summary

```
✨ Sleep Cycle Complete!
Total processed: 50
✅ Promoted (long-term): 12
⏳ Extended (short-term): 15
📦 Archived: 8
🗑️  Forgotten: 15
```

## Cost Optimization

**Default: Haiku (cheap)**
- Model: `claude-3-5-haiku-20241022`
- Cost: ~$0.25 per million tokens (input)
- Quality: Good for routine decisions

**50 memories = ~3000 tokens = $0.00075**

**Upgrade: Sonnet (expensive)**
- Model: `claude-3-5-sonnet-20241022`  
- Cost: ~$3 per million tokens (input)
- Quality: Better for complex decisions

**50 memories = ~3000 tokens = $0.009**

**Recommendation:** Start with Haiku. Upgrade to Sonnet if you see bad decisions (wrong important/forget).

## When to Run

### Manual Triggers

```bash
# When working memory fills up
python core/sleep_cycle.py

# After intensive work session
python core/sleep_cycle.py

# Before going offline
python core/sleep_cycle.py --dry-run  # Preview
python core/sleep_cycle.py             # Apply
```

### Automated Triggers

**Option 1: Cron (scheduled)**
```bash
# Every night at 3 AM
0 3 * * * cd ~/supabrain && python core/sleep_cycle.py
```

**Option 2: On working memory threshold**
```python
if count_working_memories() > 300:
    run_sleep_cycle()
```

**Option 3: Idle detection**
```python
if idle_for(hours=2):
    run_sleep_cycle()
```

## Configuration

### Environment Variables

```bash
export ANTHROPIC_API_KEY="your-key"
export SUPABRAIN_API="http://localhost:8080/api/v1"
```

### Command-Line Options

```bash
python sleep_cycle.py \
  --batch-size 10 \           # Smaller batches
  --model claude-sonnet \     # Better model
  --api-url http://localhost:8080/api/v1 \
  --dry-run                   # Preview only
```

## Example Session

### Dry Run

```bash
$ python core/sleep_cycle.py --dry-run

💤 Starting sleep cycle at 16:45:30
🔍 DRY RUN MODE (no changes will be made)
📦 Fetching expired memories...
📊 Found 25 memories to review

🔄 Processing batch 1/2 (20 memories)...
[DRY RUN] Memory 1: important - Key learning about content strategy
[DRY RUN] Memory 2: forget - Routine ls command
[DRY RUN] Memory 3: context - Ongoing project work
...

🔄 Processing batch 2/2 (5 memories)...
[DRY RUN] Memory 21: important - Autonomy lesson from Scarface
...

============================================================
✨ Sleep Cycle Complete!
============================================================
Total processed: 25
✅ Promoted (long-term): 6
⏳ Extended (short-term): 10
📦 Archived: 4
🗑️  Forgotten: 5
============================================================

💡 This was a dry run. Run without --dry-run to apply changes.
```

### Actual Run

```bash
$ python core/sleep_cycle.py

💤 Starting sleep cycle at 16:50:15
📦 Fetching expired memories...
📊 Found 25 memories to review

🔄 Processing batch 1/2 (20 memories)...
✅ Promoted: Key learning about content strategy...
🗑️  Forgot: Routine ls command...
⏳ Extended: Ongoing project work...
...

============================================================
✨ Sleep Cycle Complete!
============================================================
Total processed: 25
✅ Promoted (long-term): 6
⏳ Extended (short-term): 10
📦 Archived: 4
🗑️  Forgotten: 5
============================================================
```

## Philosophy

### Why "Sleep Cycle"?

Inspired by REM sleep in humans:

**During the day (Active Phase):**
- Capture everything → working memory
- No filtering, no judgment
- Fast, immediate storage

**During sleep (Consolidation):**
- Review what happened
- Important → long-term storage
- Trivial → forgotten
- Patterns recognized and connected

**SupaBrain mimics this:**
- Auto-capture during "day" (auto_capture.py)
- Consolidate during "sleep" (sleep_cycle.py)
- Result: Only important memories kept, noise removed

### Capture Everything, Filter Later

Traditional approach: "Think before storing"
- Risk: Miss important things
- Cost: Decision overhead

SupaBrain approach: "Store everything, filter during sleep"
- Working memory = temporary (TTL)
- Sleep cycle = intelligent filter
- Cost: Cheap (Haiku model)
- Benefit: Never miss important moments

## Integration

### With Auto-Capture

```python
# During "day" - capture aggressively
from auto_capture import capture_learning

capture_learning("Story beats features in posts")
→ Stored in working memory (4h TTL)

# During "sleep" - consolidate
python sleep_cycle.py
→ Reviewed by LLM
→ Decision: important (promoted to long-term)
```

### With Offline Queue

```python
# If SupaBrain server down
auto_capture() → offline queue (~/.supabrain_queue.jsonl)

# When server back up
queue.sync_to_supabrain()  # Memories enter working memory

# Then sleep cycle runs
python sleep_cycle.py  # Consolidates everything
```

## Monitoring

### Check Review Status

```bash
curl http://localhost:8080/api/v1/review/pending | jq '.memories | length'
→ Returns: 42 (memories awaiting review)
```

### Stats

```bash
curl http://localhost:8080/api/v1/analytics
→ Returns: layer/type/review distribution
```

## Troubleshooting

### "No memories to review"

✅ This is good! Means:
- Working memory empty, or
- No expired memories yet

### "LLM error"

Check:
- ANTHROPIC_API_KEY set?
- API rate limits?
- Model name correct?

### "All forgotten"

⚠️ Unusual. Might mean:
- Captured too much noise
- Adjust capture thresholds
- Or: Nothing important happened (normal some days)

### "API error: 500"

Check:
- SupaBrain server running?
- Database accessible?
- Migrations applied?

## Next Steps

See `AUTO_CAPTURE_README.md` for capturing memories.
See `../examples/bootstrap-consciousness.md` for initial setup.

---

Built by Scar 🐺, inspired by 2 days of autonomous development.
Part of v0.4 brain-inspired memory system.
