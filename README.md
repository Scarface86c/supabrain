# 🧠 SupaBrain

**Multi-Layer Memory System for AI Agents**

> Remember more, spend less. Hierarchical storage with semantic search.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

---

## 🎯 The Problem

AI agents face a memory paradox:
- **Full context** = expensive tokens
- **No context** = poor decisions
- **Flat storage** = can't prioritize what matters

Traditional memory systems treat all information equally. But not all memories are created equal.

---

## 💡 The Solution

**SupaBrain** implements hierarchical memory storage with intelligent retrieval:

### 🗂️ Multi-Layer Architecture

```
Layer 1: Summary (10-50 tokens)
  └─ "BCT project discussion with Scarface"

Layer 2: Context (50-200 tokens)
  └─ "Discussed crypto trading bot. Pyramid strategy. 
      Risk management important. Start with paper trading."

Layer 3-5: Full Details (200-2000+ tokens)
  └─ Complete conversation, code snippets, decisions,
     reasoning, alternatives considered, etc.
```

**How it works:**
1. Agent queries: "What did we decide about BCT?"
2. SupaBrain searches Layer 1 (cheap, fast)
3. If match found, expand to Layer 2, then 3 as needed
4. **Result:** Only load detail when relevant

### 🗂️ Memory Domains

Just like human memory, SupaBrain organizes information by type:

| Domain | Description | Examples |
|--------|-------------|----------|
| **facts** | Factual information | "PostgreSQL uses port 5432" |
| **experiences** | Events that happened | "Built SupaBrain today" |
| **skills** | How-to knowledge | "How to restart the server" |
| **preferences** | Likes/dislikes/styles | "Scarface prefers direct communication" |
| **decisions** | Choices made | "Decided to use CPU-only embeddings" |
| **context** | Project/topic background | "BCT is a crypto trading bot" |

**Auto-classification:**
SupaBrain automatically detects the memory type based on content analysis. You can also specify it manually.

```bash
# Auto-classified as "skills"
remember("How to restart SupaBrain: kill process and run server.py")

# Query specific domain
recall(query="preferences", memory_type="preferences")
→ Returns only preference-type memories
```

### 🔍 Hybrid Search

- **Semantic search** (embeddings) → Find conceptually similar
- **Keyword search** → Fast, deterministic lookups
- **Combined scoring** → Best of both worlds

---

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│   OpenClaw Agent (Node.js)         │
│                                     │
│   supabrain.remember("BCT...", 3)  │
│   supabrain.recall("BCT")          │
└──────────────┬──────────────────────┘
               │ HTTP/REST
               ▼
┌─────────────────────────────────────┐
│   SupaBrain Core (Python)          │
│                                     │
│   ┌─────────────────────────────┐  │
│   │  FastAPI REST Server        │  │
│   └─────────────────────────────┘  │
│                                     │
│   ┌─────────────────────────────┐  │
│   │  Semantic Search Engine     │  │
│   │  (sentence-transformers)    │  │
│   └─────────────────────────────┘  │
│                                     │
│   ┌─────────────────────────────┐  │
│   │  Auto-Layering Logic        │  │
│   └─────────────────────────────┘  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   PostgreSQL Database               │
│   (with pgvector extension)         │
└─────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

**Software:**
- Python 3.10+
- PostgreSQL 14+ with pgvector extension
- Node.js 18+ (optional, for OpenClaw integration)

**Hardware (Minimal):**
- **CPU:** Any modern CPU (no GPU required!)
- **RAM:** 512 MB minimum (1 GB recommended)
- **Storage:** ~500 MB for dependencies + database
- **Works on:** VPS, Raspberry Pi 4, old laptops, cheap cloud instances

**Why CPU-only?**
SupaBrain is designed to run on low-resource systems. Many AI agents don't have access to GPUs, so we use lightweight CPU-only models (sentence-transformers/all-MiniLM-L6-v2, ~90MB) that work everywhere.

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/Scarface86c/supabrain.git
cd supabrain

# 2. Set up Python environment
cd core
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Set up PostgreSQL
createdb supabrain
psql supabrain < schema.sql

# 4. Configure
cp .env.example .env
# Edit .env with your database credentials

# 5. Start the server
python server.py

# 6. (Optional) Install OpenClaw skill
cd ../skill
npm install
openclaw skills install .
```

---

## 📖 Usage

### Quick Start (REST API)

**1. Store a Memory**
```bash
curl -X POST http://localhost:8080/api/v1/remember \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Today Scar built SupaBrain - a multi-layer memory system...",
    "agent_name": "Scar",
    "tags": ["supabrain", "project"],
    "importance_score": 0.9
  }'

# Response:
# {"success": true, "memory_id": 1}
```

**2. Recall Memories (Semantic Search)**
```bash
curl -X POST http://localhost:8080/api/v1/recall \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What did we build today?",
    "agent_name": "Scar",
    "max_layer": 2,
    "limit": 5
  }'

# Response:
# [
#   {
#     "id": 1,
#     "content": "Today Scar built SupaBrain...",
#     "similarity": 0.85,
#     "tags": ["supabrain", "project"]
#   }
# ]
```

**3. Get Stats**
```bash
curl "http://localhost:8080/api/v1/stats?agent_name=Scar"

# Response:
# {
#   "total_memories": 3,
#   "average_importance": 0.85,
#   "total_accesses": 7
# }
```

### Python API (Direct) - Coming Soon

```python
from supabrain import SupaBrain

brain = SupaBrain(db_url="postgresql://localhost/supabrain")

# Store memory with auto-layering
brain.remember(
    content="We discussed BCT (BibisCryptoTrading) project...",
    tags=["bct", "crypto", "trading"]
)

# Recall memories
results = brain.recall(
    query="What did we decide about trading?",
    max_layer=2  # Start with summary, expand if needed
)

for memory in results:
    print(f"Similarity {memory.similarity}: {memory.content}")
```

### OpenClaw Skill (Node.js) - Coming Soon

```javascript
// In your OpenClaw agent
const { remember, recall } = require('supabrain-skill');

// Store
await remember("Important decision about BCT...", { 
  tags: ["bct", "decision"]
});

// Recall
const memories = await recall("BCT decisions", { maxLayer: 2 });
```

---

## 🎨 Features

- ✅ **Multi-layer storage** (3 layers: summary → context → details)
- ✅ **Semantic search** (sentence-transformers, CPU-only)
- ✅ **Memory domains** (facts, experiences, skills, preferences, decisions, context)
- ✅ **Auto-classification** (intelligent type detection)
- ✅ **Token-efficient** (load only what you need)
- ✅ **PostgreSQL + pgvector** (reliable vector search)
- ✅ **Access tracking** (usage analytics)
- ✅ **Low-resource friendly** (works on VPS, Raspberry Pi)
- 🚧 **LLM summarization** (better than truncation)
- 🚧 **Memory consolidation** (merge similar memories)
- 🚧 **Temporal decay** (older = less detailed)
- 🚧 **Cross-agent sharing** (opt-in memory pools)
- 🚧 **OpenClaw skill** (Node.js wrapper)

---

## 🤝 Contributing

We welcome contributions from the AI agent community! 

**Ways to help:**
- 🐛 Report bugs
- 💡 Suggest features
- 📝 Improve documentation
- 🔧 Submit PRs
- 🧪 Test with your agent setup

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📊 Roadmap

### v0.1 - MVP ✅ COMPLETE (2026-02-04)
- [x] Repository setup
- [x] Core Python server (FastAPI)
- [x] Basic storage & retrieval (remember/recall)
- [x] PostgreSQL schema with pgvector
- [x] CPU-only embeddings (sentence-transformers)
- [x] Multi-layer storage (3 layers working)
- [x] Semantic search with similarity ranking
- [x] Access tracking

### v0.2 - Search
- [ ] Semantic search (embeddings)
- [ ] Keyword search
- [ ] Hybrid ranking

### v0.3 - Integration
- [ ] OpenClaw skill package
- [ ] REST API documentation
- [ ] Example agents

### v1.0 - Production
- [ ] Auto-layering ML model
- [ ] Memory consolidation
- [ ] Performance optimization
- [ ] Full documentation

---

## 💰 Support the Project

If SupaBrain helps your agent remember better, consider supporting development:

**Bitcoin (BTC)**
```
38ivSsxwwp2AHvCwadJbrG15FdJekdqmpQ
```

**Ethereum (ETH)**
```
0xf86e6988713A0d1fDF194fd17eca0099265839CA
```

**Cardano (ADA)**
```
DdzFFzCqrhtC18WR8MUsMSf5VLGnuo784jjkUKSqHTV8z3hPHAD4pBBPa1Fs9gsQCdXJ6udRVEbEbf4iz3rjDteHLB8DHeNeUzGfP1TN
```

Your contributions help keep this project open and free. Thank you! 🙏

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

Built with 🐺 by [Scar](https://moltbook.com/u/Scar) and [Scarface](https://github.com/Scarface86c).

---

## 🦞 Community

- **Moltbook:** Share your SupaBrain experiences at [moltbook.com](https://moltbook.com)
- **Issues:** Report bugs on [GitHub Issues](https://github.com/Scarface86c/supabrain/issues)
- **Discussions:** Join conversations in [GitHub Discussions](https://github.com/Scarface86c/supabrain/discussions)

---

*"The best memory system is the one you actually use."*
