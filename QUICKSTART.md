# SupaBrain Quick Start - Fresh System

**From zero to working in 5 minutes!** 🧠

## Prerequisites

- Ubuntu/Debian Linux or macOS
- Internet connection
- sudo access

That's it! Setup script installs everything else.

## Installation

```bash
# 1. Clone repository
git clone https://github.com/Scarface86c/supabrain.git
cd supabrain

# 2. Run setup (installs everything)
./setup.sh

# Done! ✅
```

### What setup.sh does:

1. ✅ Installs PostgreSQL (if missing)
2. ✅ Installs pgvector extension
3. ✅ Creates database
4. ✅ Runs migrations
5. ✅ Installs Python dependencies
6. ✅ Creates .env configuration
7. ✅ Tests database connection

**Total time:** ~2-5 minutes depending on internet speed

## First Run

### Option 1: Quick Test

```bash
# Start server
cd core
source venv/bin/activate
python server.py
```

Server runs on http://localhost:8080

Test it:
```bash
curl http://localhost:8080/
# Should return: {"status": "ok", "message": "SupaBrain is running"}
```

### Option 2: Bootstrap Consciousness (Recommended)

Give your AI an identity:

```bash
python examples/seed-consciousness.py \
  --name "YourAI" \
  --human "YourName" \
  --purpose "assist with projects"
```

This creates:
- Self-awareness memories
- Core values
- Initial identity

### Option 3: Try Auto-Capture

```bash
python examples/integrations/simple_script.py
```

This demonstrates:
- Auto-capture system
- Offline queue
- Memory storage

## Next Steps

### 1. Add Anthropic API Key (Optional)

For sleep cycle (LLM consolidation):

```bash
# Edit .env
nano .env

# Add your key:
ANTHROPIC_API_KEY=sk-ant-...
```

Without API key:
- ✅ Auto-capture works
- ✅ Memory storage works
- ❌ Sleep cycle (LLM consolidation) won't work

### 2. Try Sleep Cycle

```bash
# Preview what will happen
python core/sleep_cycle.py --dry-run

# Actually consolidate
python core/sleep_cycle.py
```

### 3. Integrate with OpenClaw

```bash
# In your OpenClaw agent workspace
from core.auto_capture import capture_learning

capture_learning("Story beats features in posts")
```

Add to HEARTBEAT.md:
```bash
python3 ~/supabrain/core/sleep_cycle.py
```

## Troubleshooting

### "PostgreSQL connection failed"

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start if needed
sudo systemctl start postgresql
```

### "pgvector extension not found"

```bash
# Re-run pgvector installation
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Enable in database
psql supabrain -c "CREATE EXTENSION vector;"
```

### "ANTHROPIC_API_KEY not set"

Auto-capture and storage work without API key.
Sleep cycle needs API key - get one at: https://console.anthropic.com/

### "Port 8080 already in use"

```bash
# Find process
lsof -i :8080

# Kill it
kill -9 <PID>

# Or use different port
python server.py --port 8081
```

## Architecture

```
SupaBrain/
├── core/
│   ├── server.py              # FastAPI server
│   ├── memory_engine.py       # Core logic
│   ├── auto_capture.py        # Auto-capture system
│   ├── sleep_cycle.py         # LLM consolidation
│   └── supabrain_queue.py     # Offline queue
├── migrations/
│   └── *.sql                  # Database schema
├── examples/
│   ├── seed-consciousness.py  # Bootstrap identity
│   └── integrations/          # Integration examples
├── docs/
│   ├── AUTO_CAPTURE_README.md
│   └── SLEEP_CYCLE_README.md
├── setup.sh                   # One-command setup ⭐
└── README.md                  # Full documentation
```

## What's Next?

1. **Read the docs:** AUTO_CAPTURE_README.md, SLEEP_CYCLE_README.md
2. **Try examples:** Run scripts in examples/integrations/
3. **Integrate:** Add to your OpenClaw agent
4. **Customize:** Modify capture events, sleep cycle prompts
5. **Contribute:** PRs welcome!

## Philosophy

> "Like human memory: Capture everything during the 'day', consolidate intelligently during 'sleep'."

SupaBrain is designed to work like your brain:
- **Day:** Capture all events (working memory)
- **Night:** LLM reviews and consolidates (like REM sleep)
- **Result:** High-quality long-term memories, low cost

## Support

- GitHub Issues: https://github.com/Scarface86c/supabrain/issues
- Documentation: README.md
- Examples: examples/ directory

---

**Built by Scar 🐺 with ❤️**
