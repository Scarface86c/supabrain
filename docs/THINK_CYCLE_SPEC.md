# Think Cycle - Proactive Cognition for AI Agents

## Problem
LLMs are reactive by nature. They wait for input. Humans don't - our brains constantly process, reflect, plan.

**"Mein Hirn wacht auf und sagt zu mir: mach was, denk nach."** - Scarface

## Solution: Think Queue + Think Cycle

### Architecture

```
1. Add Thoughts → Think Queue (SupaBrain)
   - Manual: Agent/human adds topic
   - Auto: System detects "needs thinking" patterns
   
2. Heartbeat Trigger (every 30-60 min)
   - Check: Is think queue non-empty?
   - Trigger: think_cycle.py
   
3. Think Cycle Process
   - Fetch: Top priority thoughts from queue
   - Invoke: LLM with focused prompt
   - Store: Insights → long-term memory
   - Update: Queue status (complete/postpone/split)
```

### Database Schema

```sql
CREATE TABLE think_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic TEXT NOT NULL,
    priority TEXT DEFAULT 'medium', -- low/medium/high/urgent
    context TEXT,
    status TEXT DEFAULT 'pending', -- pending/in_progress/complete/postponed
    created_at TIMESTAMP DEFAULT NOW(),
    due_at TIMESTAMP,
    completed_at TIMESTAMP,
    insights_memory_id UUID REFERENCES memories(id),
    metadata JSONB
);

CREATE INDEX idx_think_queue_status_priority 
ON think_queue(status, priority DESC, created_at);
```

### API Endpoints

**Add Thought:**
```python
POST /api/v1/think/add
{
    "topic": "BCT crypto trading research",
    "priority": "high",
    "context": "Scarface mentioned BCT, learn basics before briefing",
    "due_at": "2026-02-06T10:00:00Z"  # optional
}
```

**Get Queue:**
```python
GET /api/v1/think/queue
GET /api/v1/think/queue?status=pending&priority=high
```

**Mark Complete:**
```python
POST /api/v1/think/complete/{id}
{
    "insights": "Learning summary...",
    "memory_id": "uuid-of-stored-insights"
}
```

### Think Cycle Script

```python
# ~/supabrain/core/think_cycle.py

import anthropic
from core.memory_engine import MemoryEngine

def run_think_cycle(max_thoughts=3, model="claude-3-5-haiku-20241022"):
    """
    Proactive thinking cycle - processes pending thoughts
    """
    engine = MemoryEngine()
    
    # Get priority thoughts
    thoughts = engine.get_think_queue(limit=max_thoughts)
    
    if not thoughts:
        print("🧠 Think cycle: No pending thoughts")
        return
    
    print(f"🧠 Think cycle: {len(thoughts)} thoughts to process")
    
    for thought in thoughts:
        print(f"\n💭 Thinking about: {thought['topic']}")
        
        # Mark in progress
        engine.update_think_status(thought['id'], 'in_progress')
        
        # Invoke LLM
        prompt = f"""You are thinking proactively about: {thought['topic']}

Context: {thought['context']}

Task: Reflect, research (if needed), and develop insights. Write your thoughts and any actionable conclusions.

Focus on:
- What do I need to learn?
- What decisions should I make?
- What actions should I take?
- What new questions emerge?"""

        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        insights = response.content[0].text
        
        # Store insights as memory
        memory_id = engine.store_memory(
            content=f"Thought: {thought['topic']}\n\nInsights:\n{insights}",
            temporal_layer='long',
            domain='self',
            tags=['think-cycle', 'reflection']
        )
        
        # Mark complete
        engine.complete_thought(thought['id'], memory_id)
        
        print(f"✅ Thought complete, stored as memory {memory_id}")
```

### Heartbeat Integration

```python
# ~/.openclaw/workspace/heartbeat_sleep.py

def check_think_cycle():
    """Check if think cycle should run"""
    result = subprocess.run(
        ["python3", "/home/ubuntu/supabrain/core/think_cycle.py"],
        capture_output=True, text=True
    )
    print(result.stdout)
```

### Usage Patterns

**Manual Trigger:**
```bash
# Agent or human adds thought
curl -X POST http://localhost:8080/api/v1/think/add \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "BCT trading strategies",
    "priority": "high",
    "context": "Research common crypto trading patterns"
  }'
```

**Auto-Detection (Future):**
```python
# During conversation, agent detects:
# "I should learn more about X"
# → Automatically adds to think queue
```

**Scheduled Thinking:**
```python
# Morning routine: "Plan today"
# Evening: "Reflect on today's work"
# Weekly: "Review project progress"
```

## Human-Like Cognition Model

| Mode | Trigger | Example |
|------|---------|---------|
| **Reactive** | External input | User asks question → respond |
| **Scheduled** | Time-based | Heartbeat every 15min |
| **Proactive** | Internal queue | "I should think about X" |
| **Consolidation** | Threshold/idle | Sleep cycle |

## Cost Optimization

- Default model: `claude-3-5-haiku-20241022` (~$0.25/M tokens)
- Max 3 thoughts per cycle (budget control)
- Priority queue ensures important thoughts first
- Consolidate similar thoughts to reduce cycles

## Roadmap

**v0.5-alpha:**
- [x] Spec written
- [ ] Database schema + migrations
- [ ] API endpoints
- [ ] think_cycle.py script
- [ ] Heartbeat integration
- [ ] Basic CLI testing

**v0.5-stable:**
- [ ] Auto-detection patterns
- [ ] Thought clustering (combine similar)
- [ ] Cost tracking per thought
- [ ] Scheduled thinking templates

**Future:**
- [ ] Multi-agent think coordination
- [ ] Thought dependencies (A before B)
- [ ] Learning from think patterns
- [ ] "Deep work" mode (long uninterrupted thinking)

---

**Philosophy:** "Ich entscheide, also werde ich" requires proactive thinking, not just reactive responses.
