# LLM Summarization Integration Guide (TODO #405)

**Status:** Prototype complete, ready for integration  
**Created:** 2026-03-02 05:02 CET  
**Prerequisite:** Gateway API endpoint design decision

---

## What's Ready

### ✅ Completed (Preparatory Work)
1. **Design document** (`LLM_SUMMARIZATION_DESIGN.md`) - 7.7KB
2. **Prototype module** (`core/llm_summarizer.py`) - 5.4KB
3. **Unit tests** (`tests/test_llm_summarizer.py`) - 2.4KB
4. **Dependency added** (`httpx==0.26.0` in requirements.txt)
5. **Tests passing** - Fallback truncation verified

### 🔧 Prototype Features
- ✅ Async LLM API calls with timeout handling
- ✅ Graceful fallback to truncation (current behavior)
- ✅ Feature flag (`enable_llm=False` by default - safe)
- ✅ Proper error handling and logging
- ✅ Singleton pattern for configuration
- ✅ Sync wrapper for backward compatibility

---

## Integration Steps

### Step 1: Install httpx Dependency
```bash
cd ~/supabrain/core
source venv/bin/activate
pip install httpx==0.26.0
```

**Status:** Dependency added to requirements.txt, needs install

---

### Step 2: Integrate into memory_engine.py

**Current code** (lines 102-129):
```python
def _auto_layer_content(self, content: str) -> Dict[str, str]:
    """Simple word-count truncation"""
    words = content.split()
    
    layer_1 = ' '.join(words[:10]) + ("..." if len(words) > 10 else "")
    layer_2 = ' '.join(words[:50]) + ("..." if len(words) > 50 else "")
    layer_3 = content[:2000]
    
    return {
        "layer_1": layer_1,
        "layer_2": layer_2,
        "layer_3": layer_3
    }
```

**New code** (replace lines 102-129):
```python
def _auto_layer_content(self, content: str, agent_name: str = "default") -> Dict[str, str]:
    """
    Generate hierarchical summaries using LLM (with fallback)
    
    Uses LLM when available, falls back to truncation
    TODO #405: LLM-based intelligent summarization
    """
    from llm_summarizer import get_summarizer
    
    # Get summarizer instance (feature flag controlled)
    summarizer = get_summarizer(
        gateway_url=os.getenv("OPENCLAW_GATEWAY_URL", "http://localhost:3000"),
        enable_llm=os.getenv("SUPABRAIN_ENABLE_LLM_SUMMARIZATION", "false").lower() == "true"
    )
    
    # Use sync wrapper for now (async integration requires broader refactor)
    return summarizer.generate_layers_sync(content, agent_name=agent_name)
```

**Note:** Sync wrapper used initially to avoid async refactor of `_auto_layer_content()`. Can be made async in future optimization.

---

### Step 3: Update Callers to Pass agent_name

**Find all callers:**
```bash
grep -n "_auto_layer_content" ~/supabrain/core/memory_engine.py
```

**Update calls from:**
```python
layers = self._auto_layer_content(content)
```

**To:**
```python
layers = self._auto_layer_content(content, agent_name=agent_name)
```

**Expected locations:** Anywhere memories are created/stored

---

### Step 4: Environment Configuration

**Add to `.env` or systemd service:**
```bash
# Enable LLM summarization (default: false)
SUPABRAIN_ENABLE_LLM_SUMMARIZATION=false

# OpenClaw gateway URL (default: localhost:3000)
OPENCLAW_GATEWAY_URL=http://localhost:3000
```

**Initially leave disabled** (`false`) until gateway endpoint ready.

---

### Step 5: Gateway API Endpoint (Required)

**Endpoint needed:** `POST /api/llm/summarize`

**Request:**
```json
{
  "content": "Text to summarize...",
  "max_tokens": 50,
  "agent_name": "Scar",
  "temperature": 0.3,
  "instruction": "Summarize in 50 tokens or less..."
}
```

**Response:**
```json
{
  "summary": "Concise summary text...",
  "tokens_used": 45
}
```

**Implementation location:** OpenClaw gateway (needs new route)

**Security:** Rate limiting, authentication (agent verification)

---

### Step 6: Testing Integration

**Test with LLM disabled (default):**
```bash
cd ~/supabrain
python3 tests/test_llm_summarizer.py
```

**Expected:** All tests pass (fallback truncation)

**Test with real memory insert:**
```bash
curl -X POST http://localhost:8080/api/v1/remember \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_name": "Scar",
    "content": "Long test memory about SupaBrain with multiple sentences to verify summarization works correctly and preserves meaning across layers...",
    "importance_score": 0.5,
    "tags": ["llm-test"]
  }'
```

**Verify layers in database:**
```sql
SELECT layer_1_content, layer_2_content 
FROM memories 
WHERE tags @> ARRAY['llm-test']::text[] 
LIMIT 1;
```

---

### Step 7: Enable LLM (When Gateway Ready)

**Update environment:**
```bash
export SUPABRAIN_ENABLE_LLM_SUMMARIZATION=true
systemctl --user restart supabrain
```

**Monitor logs:**
```bash
journalctl --user -u supabrain -f | grep -i "llm\|summariz"
```

**Verify LLM calls:**
- Check for LLM API requests in logs
- Verify summaries are intelligent (not truncated)
- Monitor latency (should be ~1-3s per memory vs ~100ms)

---

## Rollback Plan

**If issues occur:**

1. **Disable LLM immediately:**
   ```bash
   export SUPABRAIN_ENABLE_LLM_SUMMARIZATION=false
   systemctl --user restart supabrain
   ```

2. **Falls back to truncation** (current behavior)

3. **No data loss** - feature flag prevents breaking changes

---

## Performance Expectations

### Before (Current)
- Memory insert latency: ~100ms
- No external API calls
- Simple word-count truncation

### After (LLM Enabled)
- Memory insert latency: ~1-3s (2 LLM calls)
- External dependency: OpenClaw gateway
- Intelligent semantic summarization

### Optimization Options
1. **Background processing:** Queue summaries, process async
2. **Caching:** Cache summaries for duplicate content
3. **Batch processing:** Summarize multiple memories in one call
4. **Smart triggering:** Only use LLM for content >100 words

---

## Migration Path

### Phase 1: Prototype Testing (CURRENT - 2026-03-02)
- ✅ Module created
- ✅ Tests passing
- ✅ Feature flag added (disabled)
- Status: **Safe to deploy** (no behavior change)

### Phase 2: Gateway Endpoint Development (NEXT)
- ⏳ Design `/api/llm/summarize` route
- ⏳ Implement in OpenClaw gateway
- ⏳ Test endpoint independently

### Phase 3: SupaBrain Integration (AFTER GATEWAY)
- ⏳ Install httpx in venv
- ⏳ Integrate llm_summarizer into memory_engine
- ⏳ Update callers to pass agent_name
- ⏳ Test with LLM disabled (regression test)

### Phase 4: Production Rollout (FINAL)
- ⏳ Enable LLM for test agent only
- ⏳ Monitor performance and quality
- ⏳ Gradually enable for all agents
- ⏳ Optimize based on usage patterns

---

## Open Questions

1. **Gateway endpoint priority?** When will `/api/llm/summarize` be available?
2. **Token budget acceptable?** 2 LLM calls × 250 tokens ≈ $0.75/day for 1000 memories
3. **Latency acceptable?** 1-3s vs 100ms per memory insert
4. **Background processing?** Should summarization be async/queued?

---

## Files Created

1. `core/llm_summarizer.py` (5.4KB) - Prototype implementation
2. `tests/test_llm_summarizer.py` (2.4KB) - Unit tests
3. `docs/LLM_SUMMARIZATION_DESIGN.md` (7.7KB) - Design doc
4. `docs/LLM_SUMMARIZATION_INTEGRATION.md` (THIS FILE) - Integration guide

**Modified:**
- `core/requirements.txt` - Added httpx==0.26.0

---

## Next Actions

**Immediate (Now):**
- ✅ Prototype complete and tested
- ✅ Documentation delivered
- ⏳ Mark progress with Enforcer

**Blocked on:**
- OpenClaw gateway `/api/llm/summarize` endpoint decision
- Implementation approval from Scarface

**When ready to proceed:**
1. Implement gateway endpoint
2. Install httpx in venv
3. Integrate into memory_engine.py
4. Test with feature flag disabled
5. Test with feature flag enabled
6. Monitor and optimize

---

*Integration guide created: 2026-03-02 05:02 CET*  
*Status: Prototype ready, awaiting gateway endpoint*  
*Estimated remaining work: 1-2 hours (integration + testing)*
