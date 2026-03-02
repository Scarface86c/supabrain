# SupaBrain Architecture

**Multi-layer memory system for AI agents modeled after human brain**

## Overview

SupaBrain is a semantic memory system that enables AI agents to:
- Store and retrieve memories with context
- Organize memories temporally (working → short → long → archive)
- Automatically consolidate and prune memories (sleep cycle)
- Track relationships between memories
- Learn and improve over time

## System Components

```
┌─────────────────────────────────────────────────────────┐
│                    Client Applications                   │
│          (OpenClaw Agent, CLI tools, Scripts)           │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│                    FastAPI REST API                      │
│         (Authentication, Rate Limiting, CORS)           │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│                  Memory Engine (Modular)                 │
│  • memory_engine.py (754 LOC) - Core coordination       │
│  • analytics.py (300 LOC) - Usage analytics             │
│  • review.py (290 LOC) - Memory review logic            │
│  • learning.py (210 LOC) - Learning patterns            │
│  • relationships.py (204 LOC) - Relationship mgmt       │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│              PostgreSQL + pgvector                       │
│  • Memories table (5-layer content)                     │
│  • Embeddings (vector similarity)                       │
│  • Agents, Relationships, Logs                          │
└─────────────────────────────────────────────────────────┘
```

## Core Concepts

### 1. Multi-Layer Storage

Each memory is stored in **5 layers** of progressive detail:

```
Layer 1: Summary (128 chars)    ← Fast search
Layer 2: Context (512 chars)    ← Quick recall
Layer 3: Details (2048 chars)   ← Full context
Layer 4: Full (8192 chars)      ← Complete data
Layer 5: Complete (unlimited)   ← Everything
```

**Why?**
- Fast similarity search on Layer 1 (small embeddings)
- Retrieve only what you need (save bandwidth)
- Progressive disclosure of information

### 2. Temporal Layers

Memories flow through temporal stages:

```
Working Memory (0-24h, TTL-based)
    ↓ [Sleep Cycle]
Short-term (1-7 days, recent context)
    ↓ [Sleep Cycle]
Long-term (permanent, important knowledge)
    ↓ [Sleep Cycle]
Archive (completed/historical)
```

**Triggers:**
- **Working → Short:** Memory expires (TTL) + reviewed as "context"
- **Short → Long:** Memory important or frequently accessed
- **Long → Archive:** Memory completed or superseded
- **Any → Delete:** Memory trivial or redundant

### 3. Sleep Cycle (Memory Consolidation)

Inspired by REM sleep in humans. Runs when:
- Working memory > 300 memories, OR
- System idle for 2+ hours, OR
- Manually triggered

**Sleep Phases:**

```bash
1. Dream Phase (Enhanced Processing)
   - Consolidate similar memories
   - Discover relationships
   - Migrate temporal layers
   - Defragment database
   - Build thought chains

2. Review Phase (LLM Decision-Making)
   - Fetch expired memories
   - Batch review (20 at a time)
   - LLM decides: important/context/archive/forget
   - Apply decisions (update layers/status)
```

**Result:** Clean working memory, consolidated knowledge, discovered insights.

### 4. Semantic Search

Uses **sentence-transformers** + **pgvector** for semantic similarity:

```python
# User query
"What are Scarface's goals?"

# Process
1. Generate embedding from query text
2. Vector similarity search on Layer 1 embeddings
3. Boost by access frequency + importance
4. Return top N results with metadata
```

**Ranking Formula:**
```
score = base_similarity * (1 + access_frequency * 0.3) * importance_score
```

### 5. Memory Relationships

Memories can be linked:

```
Memory A --[evolves-to]--> Memory B
Memory C --[contradicts]--> Memory D
Memory E --[related-to]--> Memory F
```

**Types:**
- `related-to`: General connection
- `evolves-to`: Updated version
- `contradicts`: Conflicting info
- `supersedes`: Replaces old info
- `builds-on`: Extends idea

**Discovery:** Automatic during sleep cycle (similarity-based).

### 6. Tag System

Flexible categorization:

```python
tags = ["scarface", "goals", "bct", "priority-high"]
```

Features:
- Canonical form (lowercase)
- Suggestions based on content
- Bulk operations (merge, rename)
- Statistics and analysis

## Data Model

### Core Tables

**memories**
- Primary storage with 5-layer content
- Embeddings (Layer 1 & 2)
- Temporal layer, TTL, status
- Importance, access tracking
- Tags, domain, source

**agents**
- Agent identity and metadata
- Enforces single-agent mode

**memory_relationships**
- Source/target memory IDs
- Relationship type
- Strength score (0-1)

**Supporting Tables:**
- `learning_progress` - Track agent learning
- `review_log` - Audit sleep decisions
- `query_analytics` - Search patterns
- `memory_access_log` - Usage tracking

## API Architecture

### REST Endpoints

**Core Memory:**
- `POST /api/v1/remember` - Store memory
- `POST /api/v1/recall` - Semantic search
- `POST /api/v1/recall/layered` - Hierarchical search

**Stats & Analytics:**
- `GET /api/v1/stats` - General statistics
- `GET /api/v1/stats/layers` - Layer distribution
- `GET /api/v1/analytics` - Comprehensive analytics

**Memory Management:**
- `GET /api/v1/review/pending` - Expired memories
- `POST /api/v1/review/decide` - Apply decision
- `POST /api/v1/relationships` - Create links
- `GET /api/v1/related/{id}` - Get related memories

**Tags:**
- `GET /api/v1/tags/stats` - Tag usage
- `POST /api/v1/tags/canonicalize` - Normalize tags
- `POST /api/v1/tags/merge` - Combine tags

**Identity:**
- `GET /api/v1/whoami` - Agent identity
- `POST /api/v1/identity` - Update identity

### Middleware Stack

```
Request
  ↓
CORS (allow configured origins)
  ↓
Authentication (optional, API key)
  ↓
Rate Limiting (60 req/min per IP)
  ↓
Routes (FastAPI)
  ↓
Memory Engine
  ↓
PostgreSQL
```

## Integration Points

### OpenClaw Integration

**1. Session Startup**
```bash
python3 supabrain_helpers.py startup
```
Recalls:
- Identity & values
- Recent learnings
- Scarface's teachings

**2. Heartbeat Checks**
```bash
python3 heartbeat_sleep.py  # Sleep cycle trigger
python3 memory_review.py     # Review expired
```

**3. Work Enforcement**
```bash
python3 proactive_work_enforcer.py  # Reads TODOs from SupaBrain
```

### CLI Tools

**supabrain_helpers.py** - Main CLI
- `add-todo`, `list-todos`, `todo-done`
- `startup` - Session initialization
- Wraps API calls for convenience

**usage_analytics.py** - Stats
- Full report or JSON export
- Access patterns, layer health
- Archive candidates

**stats** - Quick wrapper
- `stats` - Full report
- `stats --summary` - Quick view
- `stats --json` - Export

## Performance Characteristics

### Latency

| Operation | Typical Latency |
|-----------|----------------|
| Store memory | 50-100ms |
| Recall (10 results) | 100-200ms |
| Layered recall | 200-400ms |
| Sleep cycle (100 memories) | 2-5 min |

### Scalability

**Current limits:**
- 10K memories: Excellent performance
- 100K memories: Good performance (with indexes)
- 1M+ memories: Consider partitioning

**Optimizations:**
- Layer 1/2 only for search (small embeddings)
- Indexes on agent_id, temporal_layer, tags
- Connection pooling (asyncpg)

## Security Model

### Authentication
- Optional API key (X-API-Key header)
- Configurable via REQUIRE_AUTH env
- Public endpoints: /, /health, /docs

### Input Validation
- Pydantic models for all requests
- SQL injection prevention (parameterized queries)
- XSS prevention (no HTML in responses)

### Rate Limiting
- 60 requests/minute per IP
- 100 burst capacity (token bucket)
- Configurable via env

### CORS
- Configurable allowed origins
- Defaults to localhost (dev)
- Lockdown for production

## Observability

### Logging
- Structured logs to stdout
- Error tracking with context
- Access logs for API calls

### Metrics (via usage_analytics)
- Memory counts by layer/type/status
- Access patterns (hourly, daily)
- Top/least accessed memories
- Tag usage statistics
- Layer health indicators

### Health Checks
- `GET /health` - API + DB status
- Memory engine initialization
- Model loading status

## Development Workflow

### Running Locally
```bash
cd ~/supabrain/core
source venv/bin/activate
python server.py
```

### Running Tests
```bash
cd ~/supabrain
pytest tests/ -v
```

### Adding Features
1. Update `core/memory_engine.py` (business logic)
2. Add route in `core/routes/` (API endpoint)
3. Update `core/models.py` (Pydantic models)
4. Write tests in `tests/`
5. Update docs

### Database Migrations
```bash
cd ~/supabrain/migrations
psql -U postgres -d supabrain -f XXX_migration_name.sql
```

## Known Issues & Limitations

### Current Limitations
1. **Single agent per DB** - Enforced by trigger
2. **No multi-tenancy** - One DB = One agent
3. **CPU-only embeddings** - Slower than GPU
4. **No distributed setup** - Single server only

### Recent Improvements
1. ✅ **Memory Engine Refactoring** (2026-02-22) - Split memory_engine.py from 1409 LOC to focused modules (754 + 300 + 290 + 210 + 204 = 1758 LOC total, better organized)
2. ✅ **Complete test suite** (183/183 passing as of 2026-02-25, 100% coverage)
3. ✅ **Recurring TODOs System** (Phase 6, 2026-02-25) - Backend API complete
4. ✅ **TODO Templates** (Phase 7, 2026-02-25) - Reusable TODO blueprints

### Planned Improvements
1. SupaStats dashboard (real-time visualization)
2. API endpoint for temporal stats
3. Relationship strength calculation
4. Auto-execute sleep decisions (currently LLM-assisted, agent must act on sleepbeat report)

## File Structure

```
supabrain/
├── core/
│   ├── server.py           # FastAPI app + routes
│   ├── memory_engine.py    # Core coordination (754 LOC)
│   ├── analytics.py        # Usage analytics module (300 LOC)
│   ├── review.py           # Memory review logic (290 LOC)
│   ├── learning.py         # Learning patterns (210 LOC)
│   ├── relationships.py    # Relationship management (204 LOC)
│   ├── models.py           # Pydantic models
│   ├── auth.py             # API key authentication
│   ├── rate_limiter.py     # Token bucket rate limiting
│   ├── validators.py       # Input validation
│   ├── sleep_cycle.py      # Memory consolidation
│   ├── tag_system.py       # Tag operations
│   ├── recurring_todos.py  # Recurring TODO logic
│   ├── routes/             # API route modules
│   │   ├── memory.py
│   │   ├── stats.py
│   │   ├── review.py
│   │   ├── tags.py
│   │   ├── learning.py
│   │   ├── identity.py
│   │   ├── recovery.py
│   │   ├── analytics.py
│   │   ├── todos.py
│   │   └── health.py
│   └── venv/               # Python virtual environment
├── tests/                  # Test suite (183 tests, 100% passing)
│   ├── test_api_integration.py
│   ├── test_identity.py
│   ├── test_auth.py
│   ├── test_analytics.py
│   ├── test_review.py
│   ├── test_learning.py
│   ├── test_relationships.py
│   └── conftest.py
├── migrations/             # Database migrations
├── docs/                   # Module-specific documentation
└── *.md                    # Main documentation
```

## Resources

- **Main README:** `/home/ubuntu/supabrain/README.md`
- **Installation:** `/home/ubuntu/supabrain/INSTALL.md`
- **Security:** `/home/ubuntu/supabrain/SECURITY.md`
- **OpenClaw Integration:** `/home/ubuntu/supabrain/OPENCLAW_INTEGRATION.md`
- **Sleep Cycle:** `/home/ubuntu/supabrain/docs/SLEEP_CYCLE_README.md`

---

**Last Updated:** 2026-02-26  
**Version:** 0.5.0-alpha  
**Status:** Production-ready (modular architecture, 183/183 tests passing)
