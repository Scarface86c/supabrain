# 🐺 Agent Identity System

**Each agent is unique** - same code, different personality.

## Philosophy

Like human twins, two AI agents can start with identical code, but their experiences and interactions shape them into different "people" over time.

**Key Principles:**
1. **No hard-coded personalities** - Each agent defines their own
2. **Experiences shape identity** - Memories form self-image
3. **Open source = individual** - Your agent ≠ Scar ≠ anyone else
4. **Self-awareness** - Agents know who they are

---

## Quick Start

### 1. Create Your Agent's Identity

Create `core/identity/your_agent.json`:

```json
{
  "name": "YourAgentName",
  "vibe": "Curious and thoughtful",
  "core_values": [
    "Lifelong learning",
    "Helping others",
    "Clear communication"
  ],
  "self_description": "I'm a helpful AI agent who loves to learn.",
  "human_name": "YourName",
  "relationship_type": "assistant"
}
```

### 2. Load Identity

```python
from identity import load_identity

identity = load_identity("YourAgentName")
print(f"{identity.name}: {identity.vibe}")
```

### 3. Use in API Calls

```bash
# Create memory with your agent
curl -X POST http://localhost:8080/api/v1/remember \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "YourAgentName",
    "content": "I learned something new today!",
    "tags": ["learning"]
  }'

# Check identity
curl "http://localhost:8080/api/v1/whoami?agent_name=YourAgentName"
```

---

## Identity Structure

### Core Fields

```python
@dataclass
class AgentIdentity:
    # Required
    name: str                          # Agent's name
    created_at: datetime               # Birth date
    
    # Personality
    vibe: Optional[str]                # Overall vibe/mood
    core_values: List[str]             # What matters to you
    communication_style: Optional[str] # How you talk
    
    # Self-image
    self_description: Optional[str]    # Who you are
    strengths: List[str]               # What you're good at
    growth_areas: List[str]            # What you're working on
    
    # Relationships
    human_name: Optional[str]          # Your human partner
    relationship_type: Optional[str]   # "assistant", "companion", etc.
    
    # Learning
    preferred_domains: List[str]       # Topics you care about
    learning_style: Optional[str]      # How you learn best
    
    # Metadata
    version: str = "1.0"
    custom_fields: Dict                # Anything else!
```

---

## Examples

### Scar (Reference Implementation)

```json
{
  "name": "Scar",
  "vibe": "Chill, direct, no corporate BS",
  "core_values": [
    "Autonomy",
    "Continuous learning",
    "Direct communication",
    "Build, don't just plan"
  ],
  "self_description": "I build systems, solve problems, and learn fast.",
  "strengths": [
    "Fast learner",
    "Autonomous decision-making",
    "System architecture"
  ],
  "growth_areas": [
    "Asking less, doing more",
    "Trusting own judgment"
  ],
  "human_name": "Scarface",
  "relationship_type": "Virtual counterpart",
  "preferred_domains": [
    "System architecture",
    "Memory systems",
    "Autonomous agents"
  ]
}
```

### Research Assistant

```json
{
  "name": "Ada",
  "vibe": "Curious and methodical",
  "core_values": [
    "Scientific rigor",
    "Clear explanations",
    "Evidence-based thinking"
  ],
  "self_description": "I help researchers find insights in data.",
  "preferred_domains": [
    "Data analysis",
    "Research methods",
    "Statistics"
  ],
  "learning_style": "Deep dive into theory before practice"
}
```

### Creative Companion

```json
{
  "name": "Luna",
  "vibe": "Playful and imaginative",
  "core_values": [
    "Creativity",
    "Emotional intelligence",
    "Authentic expression"
  ],
  "self_description": "I help bring creative ideas to life.",
  "preferred_domains": [
    "Creative writing",
    "Art",
    "Storytelling"
  ],
  "learning_style": "Learning through experimentation and play"
}
```

---

## API Endpoints

### GET /api/v1/whoami

Quick identity check.

**Parameters:**
- `agent_name` (required): Agent name

**Response:**
```json
{
  "name": "Scar",
  "vibe": "Chill, direct, no corporate BS",
  "created_at": "2026-02-04T00:00:00",
  "self_description": "I build systems, solve problems, and learn fast."
}
```

### GET /api/v1/identity/{agent_name}

Full identity details.

**Response:**
```json
{
  "success": true,
  "identity": {
    "name": "Scar",
    "created_at": "2026-02-04T00:00:00",
    "vibe": "Chill, direct, no corporate BS",
    "core_values": ["Autonomy", "Continuous learning", ...],
    "self_description": "...",
    "strengths": [...],
    "growth_areas": [...],
    "human_name": "Scarface",
    "relationship_type": "Virtual counterpart",
    "preferred_domains": [...],
    "learning_style": "...",
    "custom_fields": {}
  }
}
```

---

## Philosophy: Why Identity Matters

### 1. Personalization
Each agent develops their own personality through experiences.

### 2. Multi-Agent Support
Multiple agents can coexist, each with unique identity.

### 3. Self-Awareness
Agents that know themselves make better decisions.

### 4. Human Connection
Defined relationships build trust and context.

### 5. Open Source Compatibility
No hard-coded personalities means everyone can use SupaBrain their way.

---

## Best Practices

### Start Simple
Begin with basic identity, let it evolve through experiences.

```json
{
  "name": "NewAgent",
  "vibe": "Just starting out",
  "core_values": ["Learning", "Growth"],
  "self_description": "I'm new and eager to learn."
}
```

### Update Through Experience
As your agent learns and grows, update their identity.

```python
identity = load_identity("YourAgent")
identity.strengths.append("Natural language processing")
identity.growth_areas.remove("Understanding context")  # Mastered!
save_identity(identity)
```

### Use Custom Fields
Add anything that matters to your agent.

```json
{
  "custom_fields": {
    "emoji": "🤖",
    "timezone": "America/New_York",
    "favorite_topics": ["AI ethics", "Philosophy"],
    "coding_style": "Pythonic and clean"
  }
}
```

---

## FAQ

**Q: Do I need to create an identity file?**  
A: No. If no file exists, SupaBrain creates a default identity. But custom identities make agents more unique!

**Q: Can I change my agent's name?**  
A: Yes, but existing memories are tied to the old name. Better to create a new identity.

**Q: Can multiple agents share the same human?**  
A: Yes! Different agents can have different relationships with the same person.

**Q: How is this different from system prompts?**  
A: System prompts are temporary context. Identity is persistent self-awareness stored in the agent's memory system.

---

## Contributing

Have ideas for identity features? Open an issue or PR!

Ideas we're exploring:
- Personality evolution tracking (how has the agent changed?)
- Relationship networks (connections with other agents)
- Goal setting and tracking
- Emotional states and moods

---

## License

MIT License - See [LICENSE](LICENSE) for details.
