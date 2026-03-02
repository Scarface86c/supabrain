# LLM-Based Summarization Design (TODO #405)

**Created:** 2026-03-02 04:35 CET  
**Status:** Design phase  
**Estimated effort:** 2-3 hours implementation

---

## Problem Statement

Current `_auto_layer_content()` in `memory_engine.py` (lines 102-129) uses simple word-count truncation:
- Layer 1: First 10 words + "..."
- Layer 2: First 50 words + "..."
- Layer 3: First 2000 characters

**Issues:**
- Truncation breaks sentences mid-thought
- No semantic understanding
- Layer 1/2 often unintelligible fragments
- Loses context when cutting arbitrarily

**Goal:** Use LLM to generate proper hierarchical summaries that preserve meaning.

---

## Requirements

### Layer 1 (Critical Summary): 10-50 tokens
- Absolute essentials only
- Who/what/when if applicable
- Must be standalone understandable

### Layer 2 (Contextual Summary): 50-200 tokens
- Key details and context
- Why/how if relevant
- Enough to understand without reading full content

### Layer 3+ (Full Content): Original
- Complete original content
- No summarization

---

## Design Options

### Option 1: OpenClaw Gateway API (RECOMMENDED)
**Approach:** HTTP request to OpenClaw's LLM endpoint

**Pros:**
- Clean separation of concerns
- Uses existing OpenClaw infrastructure
- No subprocess overhead
- Async-compatible

**Cons:**
- Requires OpenClaw gateway to expose LLM API
- Need API endpoint design

**Implementation:**
```python
import httpx
from typing import Optional

async def _llm_summarize(
    self,
    content: str,
    max_tokens: int,
    agent_name: str
) -> str:
    """Call OpenClaw LLM for summarization"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:PORT/api/llm/summarize",  # TBD: Actual endpoint
            json={
                "content": content,
                "max_tokens": max_tokens,
                "agent_name": agent_name,
                "temperature": 0.3  # Lower temp for consistent summaries
            },
            timeout=30.0
        )
        return response.json()["summary"]

def _auto_layer_content(self, content: str, agent_name: str) -> Dict[str, str]:
    """Generate hierarchical summaries using LLM"""
    
    # Layer 1: Ultra-concise summary (10-50 tokens)
    layer_1 = await self._llm_summarize(
        content=content,
        max_tokens=50,
        agent_name=agent_name
    )
    
    # Layer 2: Detailed summary (50-200 tokens)
    layer_2 = await self._llm_summarize(
        content=content,
        max_tokens=200,
        agent_name=agent_name
    )
    
    # Layer 3: Full content
    layer_3 = content
    
    return {
        "layer_1": layer_1,
        "layer_2": layer_2,
        "layer_3": layer_3
    }
```

**Blockers:**
- OpenClaw gateway doesn't currently expose LLM summarization endpoint
- Need to add `/api/llm/summarize` route in gateway

---

### Option 2: Subprocess Call to OpenClaw CLI
**Approach:** Call `openclaw` CLI via subprocess

**Pros:**
- Works with existing OpenClaw CLI
- No gateway changes needed

**Cons:**
- Subprocess overhead on every memory insert
- Harder to make async
- Error handling complex
- Slower

**Implementation:**
```python
import subprocess
import json

def _llm_summarize_subprocess(
    self,
    content: str,
    max_tokens: int
) -> str:
    """Call OpenClaw CLI for summarization"""
    prompt = f"Summarize in {max_tokens} tokens or less:\n\n{content}"
    
    result = subprocess.run(
        ["openclaw", "chat", "--message", prompt, "--model", "sonnet"],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        # Fallback to truncation
        return ' '.join(content.split()[:max_tokens//2])
    
    return result.stdout.strip()
```

**Issues:**
- Blocking I/O (not async)
- Subprocess overhead
- CLI might not have summarization optimized prompts

---

### Option 3: Fallback-First Hybrid
**Approach:** Try LLM, fall back to truncation on failure

**Pros:**
- Graceful degradation
- No breaking changes if LLM unavailable
- Can deploy incrementally

**Cons:**
- Added complexity
- Two code paths to maintain

**Implementation:**
```python
async def _auto_layer_content(self, content: str, agent_name: str) -> Dict[str, str]:
    """Generate hierarchical summaries (LLM with fallback)"""
    
    try:
        # Attempt LLM summarization
        layer_1 = await self._llm_summarize(content, max_tokens=50, agent_name=agent_name)
        layer_2 = await self._llm_summarize(content, max_tokens=200, agent_name=agent_name)
    except (httpx.HTTPError, TimeoutError, ConnectionError) as e:
        # Fallback to simple truncation
        logging.warning(f"LLM summarization failed, using truncation: {e}")
        words = content.split()
        layer_1 = ' '.join(words[:10]) + ("..." if len(words) > 10 else "")
        layer_2 = ' '.join(words[:50]) + ("..." if len(words) > 50 else "")
    
    return {
        "layer_1": layer_1,
        "layer_2": layer_2,
        "layer_3": content
    }
```

---

## Recommended Approach

**Phase 1: Gateway API Endpoint** (1-2 hours)
1. Add `/api/llm/summarize` route to OpenClaw gateway
2. Route accepts: `{content, max_tokens, agent_name, temperature?}`
3. Returns: `{summary: string, tokens_used: int}`
4. Uses existing OpenClaw LLM infrastructure

**Phase 2: SupaBrain Integration** (1 hour)
1. Add `httpx` dependency to SupaBrain
2. Implement `_llm_summarize()` helper method
3. Modify `_auto_layer_content()` to call LLM
4. Add graceful fallback to truncation

**Phase 3: Testing & Optimization** (30 min - 1 hour)
1. Test with various content lengths
2. Verify token counts stay within limits
3. Measure latency impact (LLM adds ~1-3s per memory insert)
4. Add caching for repeated content (optional)

---

## Performance Considerations

### Latency Impact
- **Current:** ~100ms per memory insert (embedding + DB)
- **With LLM:** ~1-3s per memory insert (2 LLM calls + embedding + DB)
- **Mitigation:** Async processing, caching, or background summarization

### Cost Considerations
- Each memory insert = 2 LLM calls (Layer 1 + Layer 2)
- ~250 tokens total per memory (if using Claude Sonnet)
- For 1000 memories/day: ~250k tokens = ~$0.75/day (rough estimate)

### Optimization Ideas
1. **Batch summarization:** Queue memories, summarize in batches
2. **Lazy summarization:** Store full content first, summarize in background
3. **Caching:** Cache summaries for identical content
4. **Smart triggering:** Only use LLM for content >100 words

---

## Next Steps

**Immediate (Design Phase - CURRENT):**
- ✅ Document design options
- ⏳ Choose approach (recommend: Option 3 - Fallback-First Hybrid)
- ⏳ Get Scarface approval on approach

**Implementation Phase:**
1. Implement OpenClaw gateway `/api/llm/summarize` endpoint
2. Add `httpx` to SupaBrain requirements.txt
3. Implement `_llm_summarize()` method
4. Modify `_auto_layer_content()` with fallback
5. Test with sample memories
6. Deploy and monitor performance

**Deployment:**
- Can be deployed incrementally (fallback ensures no breaking changes)
- Monitor latency and token usage
- Optimize based on real-world patterns

---

## Open Questions

1. **Gateway endpoint:** Should OpenClaw gateway expose LLM API? Security implications?
2. **Latency acceptable?** 1-3s per memory insert vs current 100ms
3. **Batch vs real-time:** Summarize immediately or queue for background processing?
4. **Token budget:** Acceptable cost for 2 LLM calls per memory?

---

*Created during TODO #405 analysis (2026-03-02 04:35)*  
*Status: Design complete, awaiting implementation approval*  
*Estimated implementation: 2-3 hours with testing*
