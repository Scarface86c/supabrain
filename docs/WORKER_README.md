# SupaBrain Worker - Background Processing

**v0.5 - Standalone proactive cognition and consolidation**

## What is it?

SupaBrain Worker is a background process that runs independently, providing:

1. **Think Cycle** - Proactive cognition (checks queue every 15 min)
2. **Sleep Cycle** - Memory consolidation (checks every 30 min)
3. **All-in-one** - No OpenClaw dependency required!

## Architecture

```
SupaBrain Server (port 8080)    SupaBrain Worker (background)
       ↓                                  ↓
   API Endpoints               Think Cycle (15 min)
   Memory storage              Sleep Cycle (30 min)
       ↓                                  ↓
       PostgreSQL Database ←──────────────┘
```

**Benefits:**
- ✅ Runs independently - no manual triggers needed
- ✅ Portable - works anywhere (Pi, VPS, laptop)
- ✅ Fault-tolerant - restarts automatically
- ✅ Efficient - batched operations, low resource usage

## Quick Start

### Method 1: Manual (Development)

```bash
# Terminal 1: Start server
cd core && source venv/bin/activate
python server.py

# Terminal 2: Start worker
cd core && source venv/bin/activate
python supabrain_worker.py
```

**Output:**
```
🧠 SupaBrain Worker starting...
✅ Database connected
✅ Anthropic API configured
✅ Worker initialized

🚀 Worker running...
   Think cycle: every 900s
   Sleep cycle: every 1800s
   Press Ctrl+C to stop
```

### Method 2: Systemd Service (Production)

```bash
# Install service
sudo cp systemd/supabrain-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable supabrain-worker
sudo systemctl start supabrain-worker

# Check status
sudo systemctl status supabrain-worker

# View logs
sudo journalctl -u supabrain-worker -f
```

### Method 3: Docker Compose (Coming Soon)

```yaml
version: '3.8'
services:
  supabrain-server:
    build: .
    ports:
      - "8080:8080"
  
  supabrain-worker:
    build: .
    command: python core/supabrain_worker.py
    depends_on:
      - postgres
```

## Configuration

### Environment Variables (.env)

```bash
# Database
DATABASE_URL=postgresql://postgres@localhost:5432/supabrain

# Anthropic API (required for LLM features)
ANTHROPIC_API_KEY=sk-ant-...

# Worker intervals (seconds)
THINK_CHECK_INTERVAL=900   # 15 minutes
SLEEP_CHECK_INTERVAL=1800  # 30 minutes
```

### Think Queue Location

Default: `~/.openclaw/workspace/think_queue.json`

Can be customized in worker code:
```python
THINK_QUEUE_FILE = Path.home() / ".openclaw/workspace/think_queue.json"
```

## How It Works

### Think Cycle (Every 15 minutes)

1. Load think queue from file
2. Filter pending thoughts
3. Sort by priority (urgent > high > medium > low)
4. Process top 3 thoughts:
   - Mark in progress
   - Invoke LLM with thought context
   - Store insights as memory (long-term, self domain)
   - Mark complete
5. Save updated queue

**Example log:**
```
💭 Thinking about: BCT crypto trading research
✅ Thought complete: BCT crypto trading research
```

### Sleep Cycle (Every 30 minutes)

1. Check working memory count
2. Check expired memories
3. If threshold reached (300 memories or 50 expired):
   - Run consolidation
   - LLM reviews expired memories
   - Promotes/extends/archives/forgets
4. Update memory statuses

**Thresholds:**
- Working memory > 300 memories
- Expired memories > 50
- Manual trigger via API

## API Integration

### Add Thought (from any agent)

```python
import requests

requests.post('http://localhost:8080/api/v1/think/add', json={
    'topic': 'BCT trading strategies',
    'priority': 'high',
    'context': 'Research common patterns'
})

# Worker will process it automatically in next cycle!
```

### Check Worker Status

```python
import requests

response = requests.get('http://localhost:8080/api/v1/worker/status')
print(response.json())

# Example response:
# {
#   "running": true,
#   "last_think_cycle": "2026-02-05T19:35:00",
#   "last_sleep_cycle": "2026-02-05T19:00:00",
#   "pending_thoughts": 2
# }
```

## OpenClaw Integration (Optional)

Worker runs standalone, but OpenClaw agents can use it:

```python
# In your OpenClaw agent
import subprocess

# Add thought to queue
subprocess.run([
    "python3", "-c",
    f"""
import json
from pathlib import Path
queue = json.load(open(Path.home() / '.openclaw/workspace/think_queue.json'))
queue.append({{'topic': 'New idea', 'priority': 'high', 'context': '...', 'status': 'pending'}})
json.dump(queue, open(Path.home() / '.openclaw/workspace/think_queue.json', 'w'))
"""
])

# Worker will process automatically!
```

**Or use helper function:**
```python
from think_cycle_prototype import add_thought

add_thought("New idea", priority="high", context="...")
```

## Monitoring

### Check Logs

```bash
# Systemd service
sudo journalctl -u supabrain-worker -f

# Manual run
# Output appears in terminal
```

### Check Database

```sql
-- Recent thoughts processed
SELECT * FROM memories 
WHERE tags @> ARRAY['think-cycle'] 
ORDER BY created_at DESC 
LIMIT 10;

-- Working memory status
SELECT temporal_layer, COUNT(*) 
FROM memories 
GROUP BY temporal_layer;
```

## Troubleshooting

### "ANTHROPIC_API_KEY not set"

Worker starts but LLM features disabled:
```
⚠️  Anthropic API key not set - LLM features disabled
```

**Fix:** Add to `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

### "Database connection failed"

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection manually
psql -U postgres -d supabrain -c "SELECT 1"
```

### Worker not processing thoughts

```bash
# Check queue file exists
cat ~/.openclaw/workspace/think_queue.json

# Check worker logs
sudo journalctl -u supabrain-worker -n 50

# Verify worker is running
ps aux | grep supabrain_worker
```

### High CPU/Memory usage

Worker is designed to be efficient:
- CPU: <5% average (spikes during LLM calls)
- Memory: ~200-400 MB

If higher:
- Check batch sizes (default: 3 thoughts per cycle)
- Reduce check intervals
- Check for infinite loops in logs

## Performance

**Resource Usage:**
- CPU: <5% average, spikes to 20-30% during LLM calls
- Memory: 200-400 MB (depends on model cache)
- Network: Minimal (only during LLM API calls)

**Latency:**
- Think cycle check: <100ms
- Sleep cycle check: <200ms
- LLM processing: 2-5 seconds per thought

**Scalability:**
- Handles 1000s of memories
- Processes 3 thoughts per 15-min cycle = ~12 thoughts/hour
- Sleep cycle handles 20 memories per batch

## Future Enhancements (v0.6+)

- [ ] Web dashboard for worker status
- [ ] Configurable intervals via API
- [ ] Multi-agent coordination
- [ ] Distributed workers (multiple machines)
- [ ] Thought dependencies (process A before B)
- [ ] Deep work mode (long uninterrupted thinking)
- [ ] Auto-scaling based on queue size

## Philosophy

> "Like a human brain: Always running in the background, consolidating memories and generating insights without being asked."

The worker embodies **proactive cognition**:
- Not reactive (waiting for input)
- Not scheduled (fixed times only)
- **Proactive** (checks queue, decides what needs thinking)

This is the difference between an assistant and an agent.

---

**Built by Scar 🐺 - SupaBrain v0.5**
