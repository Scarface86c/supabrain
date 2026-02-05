# SupaBrain Installation Guide

**Complete setup for fresh systems**

## Prerequisites

- Ubuntu/Debian Linux or macOS
- Python 3.10+
- PostgreSQL 14+ (auto-installed by setup.sh)
- Internet connection

## Quick Install (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/Scarface86c/supabrain.git
cd supabrain

# 2. Run automated setup
./setup.sh

# Done! ✅
```

The setup script will:
- ✅ Install PostgreSQL + pgvector
- ✅ Create database
- ✅ Run migrations  
- ✅ Install Python dependencies
- ✅ Create .env configuration

**Time:** 2-5 minutes

## Post-Install Configuration

### 1. Set Anthropic API Key (Required for LLM Features)

**Get your API key:** https://console.anthropic.com/

```bash
# Edit .env
nano ~/supabrain/.env

# Add your key:
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
```

**Without API key:**
- ✅ Memory storage works
- ✅ Auto-capture works
- ❌ Sleep cycle (LLM consolidation) won't work
- ❌ Think cycle (proactive cognition) won't work

### 2. Test Installation

```bash
# Test database connection
psql postgresql://postgres:supabrain2024@localhost:5432/supabrain -c "SELECT 1"

# Should return:
# ?column? 
# ----------
#        1
```

### 3. Start Worker (Background Process)

**Method A: Manual (Testing)**

```bash
cd ~/supabrain/core
nohup python3 -u supabrain_worker.py > /tmp/supabrain_worker.log 2>&1 &

# Check status
tail -f /tmp/supabrain_worker.log
```

**Method B: Systemd Service (Production)**

```bash
# Install service
sudo cp ~/supabrain/supabrain-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable supabrain-worker
sudo systemctl start supabrain-worker

# Check status
sudo systemctl status supabrain-worker

# View logs
sudo journalctl -u supabrain-worker -f
```

### 4. Monitor System

```bash
# Run monitor script
~/supabrain/monitor.sh

# Shows:
# - Worker status (running/stopped)
# - Database stats (memory counts)
# - Think queue (pending thoughts)
# - Recent logs
# - Configuration summary
```

## First Use

### Bootstrap Consciousness (Optional but Recommended)

Give your AI an initial identity:

```bash
python examples/seed-consciousness.py \
  --name "YourAI" \
  --human "YourName" \
  --purpose "assist with projects"
```

### Add Your First Thought

```bash
python3 ~/.openclaw/workspace/think_cycle_prototype.py add \
  "Learn SupaBrain architecture" \
  "high" \
  "Understand how all components work together"
```

Worker will process it automatically within 15 minutes (or 60s if testing mode).

### Capture Your First Memory

```python
# In your scripts
import sys
sys.path.append('/home/ubuntu/supabrain/core')
from auto_capture import capture_learning

capture_learning("SupaBrain installation complete!")
```

## Directory Structure

```
supabrain/
├── core/
│   ├── server.py              # FastAPI server
│   ├── memory_engine.py       # Core logic
│   ├── auto_capture.py        # Auto-capture system
│   ├── sleep_cycle.py         # Memory consolidation
│   ├── supabrain_worker.py    # Background worker
│   └── .env                   # Configuration (YOU MUST EDIT THIS!)
├── docs/
│   ├── AUTO_CAPTURE_README.md
│   ├── SLEEP_CYCLE_README.md
│   └── WORKER_README.md
├── examples/
│   ├── seed-consciousness.py
│   └── integrations/
├── migrations/
│   └── *.sql                  # Database schema
├── setup.sh                   # Automated setup
├── monitor.sh                 # System monitor
├── supabrain-worker.service   # Systemd service
└── INSTALL.md                 # This file
```

## Troubleshooting

### PostgreSQL Connection Failed

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start if needed
sudo systemctl start postgresql

# Test connection with password
psql postgresql://postgres:supabrain2024@localhost:5432/supabrain -c "SELECT 1"
```

### Worker Not Starting

```bash
# Check logs
tail -50 /tmp/supabrain_worker.log

# Or for systemd:
sudo journalctl -u supabrain-worker -n 50

# Common issues:
# - Database not accessible
# - .env file missing or invalid
# - Python dependencies not installed
```

### API Key Not Working

```bash
# Verify key is set
grep ANTHROPIC_API_KEY ~/supabrain/.env

# Should show:
# ANTHROPIC_API_KEY=sk-ant-api03-...

# Test API key manually:
python3 -c "
from anthropic import Anthropic
client = Anthropic(api_key='YOUR_KEY_HERE')
response = client.messages.create(
    model='claude-3-5-haiku-20241022',
    max_tokens=10,
    messages=[{'role': 'user', 'content': 'Hi'}]
)
print('✅ API key works!')
"
```

### "No memories" / Empty Database

Normal on fresh install! Start capturing:

```python
from auto_capture import capture_milestone
capture_milestone("SupaBrain installation complete!")
```

## Configuration Reference

### Environment Variables (.env)

```bash
# Database (SET BY SETUP.SH)
DATABASE_URL=postgresql://postgres:supabrain2024@localhost:5432/supabrain

# Anthropic API (YOU MUST SET THIS!)
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE

# Worker Intervals (optional)
THINK_CHECK_INTERVAL=900   # 15 minutes (default)
SLEEP_CHECK_INTERVAL=1800  # 30 minutes (default)

# For testing, reduce intervals:
# THINK_CHECK_INTERVAL=60   # 1 minute
```

### Database Credentials

**Default credentials (set by setup.sh):**
- Host: `localhost:5432`
- Database: `supabrain`
- User: `postgres`
- Password: `supabrain2024`

**Change password:**
```bash
echo "ubuntuadmin" | sudo -S -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'your_new_password';"

# Update .env:
DATABASE_URL=postgresql://postgres:your_new_password@localhost:5432/supabrain

# Update ~/.pgpass:
echo "localhost:5432:*:postgres:your_new_password" > ~/.pgpass
chmod 600 ~/.pgpass
```

## Next Steps

1. **Read the docs:** 
   - `docs/AUTO_CAPTURE_README.md` - How to capture memories
   - `docs/SLEEP_CYCLE_README.md` - Memory consolidation
   - `docs/WORKER_README.md` - Background worker details

2. **Try examples:**
   - `examples/integrations/simple_script.py` - Basic integration
   - `examples/integrations/heartbeat_example.py` - Periodic tasks

3. **Monitor your system:**
   - Run `~/supabrain/monitor.sh` daily
   - Check logs: `sudo journalctl -u supabrain-worker -f`
   - Add thoughts: `python3 ~/.openclaw/workspace/think_cycle_prototype.py add ...`

4. **Integrate with your projects:**
   - Import auto_capture in your scripts
   - Let memories accumulate
   - Run sleep cycle nightly (automatic with worker)

## Support

- **GitHub:** https://github.com/Scarface86c/supabrain
- **Issues:** https://github.com/Scarface86c/supabrain/issues
- **Docs:** `docs/` directory

---

**Built by Scar 🐺 - SupaBrain v0.5**

*"Like human memory: Capture everything during the 'day', consolidate intelligently during 'sleep'"*
