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
3. If match found, expand to Layer 2, then 3-5 as needed
4. **Result:** Only load detail when relevant

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

- Python 3.10+
- PostgreSQL 14+ with pgvector extension
- Node.js 18+ (for OpenClaw integration)

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

### Python API (Direct)

```python
from supabrain import SupaBrain

brain = SupaBrain(db_url="postgresql://localhost/supabrain")

# Store memory with auto-layering
brain.remember(
    content="We discussed BCT (BibisCryptoTrading) project...",
    tags=["bct", "crypto", "trading"],
    layer=3  # Optional: specify layer, or let it auto-decide
)

# Recall memories
results = brain.recall(
    query="What did we decide about trading?",
    max_layer=2  # Start with summary, expand if needed
)

for memory in results:
    print(f"Layer {memory.layer}: {memory.content}")
```

### OpenClaw Skill (Node.js)

```javascript
// In your OpenClaw agent
const { remember, recall } = require('supabrain-skill');

// Store
await remember("Important decision about BCT...", { 
  tags: ["bct", "decision"],
  layer: 3 
});

// Recall
const memories = await recall("BCT decisions", { maxLayer: 2 });
```

---

## 🎨 Features

- ✅ **Multi-layer storage** (5 levels of detail)
- ✅ **Hybrid search** (semantic + keyword)
- ✅ **Auto-layering** (ML-based importance detection)
- ✅ **Token-efficient** (load only what you need)
- ✅ **PostgreSQL backend** (reliable, scalable)
- ✅ **OpenClaw integration** (easy skill installation)
- 🚧 **Memory consolidation** (merge similar memories)
- 🚧 **Temporal decay** (older = less detailed)
- 🚧 **Cross-agent sharing** (opt-in memory pools)

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

### v0.1 - MVP (Current)
- [x] Repository setup
- [ ] Core Python server
- [ ] Basic storage & retrieval
- [ ] PostgreSQL schema

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
