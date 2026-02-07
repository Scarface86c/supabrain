# OpenClaw Integration Guide

**Using your Max Account for SupaBrain Worker!**

## Why OpenClaw Integration?

Instead of requiring separate Anthropic API credits, SupaBrain can route LLM calls through OpenClaw, using your existing Max Account automatically!

**Benefits:**
- ✅ No separate API credits needed
- ✅ Uses your Max Account automatically
- ✅ All LLM calls go through OpenClaw
- ✅ Consistent authentication
- ✅ Easy to set up

## Setup (One-Time)

### 1. Create Worker Agent

```bash
openclaw agents add worker --workspace ~/supabrain/worker-agent --non-interactive
```

This creates a dedicated agent for SupaBrain Worker that uses your Max Account.

### 2. Configure SupaBrain

Edit `~/supabrain/.env`:

```bash
# LLM Backend Configuration
USE_OPENCLAW=true
OPENCLAW_AGENT=worker
```

### 3. Start Worker

```bash
cd ~/supabrain/core
nohup python3 -u supabrain_worker_openclaw.py > /tmp/supabrain_worker_openclaw.log 2>&1 &
```

## How It Works

```
Think Cycle:
  1. Worker finds pending thought in queue
  2. Worker invokes: openclaw agent --agent worker --message "..."
  3. OpenClaw routes to your Max Account
  4. Response comes back to Worker
  5. Worker stores insights in database
```

**Key Point:** The `openclaw agent` command uses your gateway's authentication, which includes your Max Account!

## Verification

Check that it's working:

```bash
# 1. Verify worker agent exists
openclaw agents list | grep worker

# 2. Check worker logs
tail -f /tmp/supabrain_worker_openclaw.log

# Should see:
# ✅ OpenClaw agent 'worker' found
# → Using your Max Account automatically!

# 3. Add a test thought
python3 ~/.openclaw/workspace/think_cycle_prototype.py add \
  "Test OpenClaw integration" \
  "high" \
  "Verify that Max Account is being used"

# 4. Wait 60 seconds, check logs
tail -50 /tmp/supabrain_worker_openclaw.log
```

## Troubleshooting

### "OpenClaw agent 'worker' not found"

```bash
# Create the agent:
openclaw agents add worker --workspace ~/supabrain/worker-agent --non-interactive

# Verify:
openclaw agents list
```

### "OpenClaw agent failed"

```bash
# Test manually:
openclaw agent --agent worker --message "Test" --json

# Check OpenClaw gateway status:
openclaw status
```

### Worker not processing thoughts

```bash
# Check logs for errors:
tail -100 /tmp/supabrain_worker_openclaw.log

# Check if worker is running:
ps aux | grep supabrain_worker_openclaw

# Check think queue:
python3 ~/.openclaw/workspace/think_cycle_prototype.py list
```

## Alternative: Direct API

If you prefer to use direct Anthropic API (requires separate credits):

```bash
# Edit .env
USE_OPENCLAW=false
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE

# Use the original worker (not OpenClaw version):
python3 supabrain_worker.py
```

## Architecture

```
┌─────────────────────────────────────────┐
│  SupaBrain Worker                       │
│  (supabrain_worker_openclaw.py)         │
└───────────────┬─────────────────────────┘
                │
                │ subprocess.run(
                │   'openclaw agent --agent worker ...'
                │ )
                ▼
┌─────────────────────────────────────────┐
│  OpenClaw Gateway                       │
│  - Routes to 'worker' agent             │
│  - Uses Max Account auth                │
└───────────────┬─────────────────────────┘
                │
                │ Anthropic API
                ▼
┌─────────────────────────────────────────┐
│  Your Max Account                       │
│  (unlimited usage!)                     │
└─────────────────────────────────────────┘
```

## Cost Comparison

**With OpenClaw (Recommended):**
- ✅ Uses Max Account
- ✅ Unlimited usage
- ✅ No separate billing

**Direct API:**
- ❌ Requires separate Anthropic account
- ❌ Pay per token (~$0.25/M tokens for Haiku)
- ❌ Credits can run out

---

**Built by Scar 🐺 - SupaBrain v0.5 with OpenClaw Integration**
