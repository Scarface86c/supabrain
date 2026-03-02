# SupaBrain Decay Score System

> **Implemented:** 2026-02-19  
> **Status:** Active — runs nightly via SleepBeat

---

## What Is Decay Score?

Every memory has a `decay_score` between **0.10** and **1.00**.  
It reflects how "fresh" a memory is — based on how recently it was last accessed.

A memory you haven't touched in 6 months is less relevant than one you recalled yesterday. Decay score captures this.

---

## How It Works

### Exponential Decay Formula

```
decay_score = max(0.10, e^(-λ × days_since_last_access))
```

Where `λ` depends on memory importance:

| Memory Type | Half-life | λ (lambda) | Effect |
|---|---|---|---|
| Normal (importance < 0.85) | 60 days | 0.01155 | Halves every 2 months |
| High importance (≥ 0.85) | 180 days | 0.00385 | Halves every 6 months |

**Minimum:** `decay_score` never drops below `0.10` — memories never completely vanish.

### Visual Example

```
Days since access → decay_score (normal memory)
0 days:   1.000
14 days:  0.851
30 days:  0.707
60 days:  0.500   ← half-life
120 days: 0.250
180 days: 0.125
240 days: 0.100   ← floor (min)
```

---

## Effect on Recall

Decay score acts as a **multiplier on recall scoring**:

```python
final_score = base_similarity × decay_score × access_frequency_boost
```

This means:
- Frequently accessed, recently used memories rank higher
- Old, untouched memories fade in recall results — but never disappear
- High-importance memories stay accessible much longer

---

## When Does It Update?

**Automatic (nightly):** SleepBeat runs at **23:00** and calls the update endpoint.

**Manual trigger:**
```bash
curl -X POST "http://localhost:8080/api/v1/analytics/decay/update?agent_name=Scar"
```

**Response:**
```json
{
  "updated": 273,
  "avg_decay_score": 0.952,
  "message": "Updated decay scores for 273 memories"
}
```

---

## Why This Matters

### The Problem Without Decay
Without decay, a memory accessed once 6 months ago could outrank a memory you've been using daily — just because of slightly better semantic similarity. That's wrong.

### With Decay
Recall reflects both **relevance** (semantic match) and **recency** (how active the memory is). Just like human memory — you remember things you think about often.

---

## Database Column

```sql
memories.decay_score  -- FLOAT, default 1.0
memories.last_decay_check  -- TIMESTAMP, when decay was last recalculated
```

---

## Interaction With Other Scoring

SupaBrain recall uses a multi-factor score:

| Factor | Description | Weight |
|---|---|---|
| `base_similarity` | Embedding cosine similarity | Core |
| `decay_score` | Recency/access decay | × multiplier |
| `access_frequency_score` | How often recalled (30% boost) | + boost |

All three combine to produce the final ranking. The result: memories that are semantically relevant, recently used, and frequently accessed rank highest.

---

## Configuration

Currently hardcoded in `memory_engine.py → update_decay_scores()`:

```python
# Normal memories: half-life 60 days
LAMBDA_NORMAL = 0.01155  # ln(2) / 60

# High-importance memories (>= 0.85): half-life 180 days  
LAMBDA_IMPORTANT = 0.00385  # ln(2) / 180

# Minimum floor
MIN_DECAY = 0.10
```

To adjust half-life values, modify these constants and restart the server.

---

## Tests

Decay score is covered by `tests/test_decay.py` — 15 tests covering:
- Formula accuracy
- High-importance slow decay
- Minimum floor enforcement
- API endpoint
- SleepBeat integration

All 169 tests pass as of implementation date.

---

*Part of SupaBrain's multi-layer memory architecture.*  
*See also: SLEEP_CYCLE_README.md for nightly maintenance.*
