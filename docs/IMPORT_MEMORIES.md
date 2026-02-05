# Importing Memories to SupaBrain

**Bootstrap your AI with existing knowledge!**

## Use Cases

1. **Bootstrap new AI** - Import identity, values, initial knowledge
2. **Migrate from files** - Move existing memory files to SupaBrain
3. **Eating your own dogfood** - Import your own MEMORY.md
4. **Archive old memories** - Preserve historical logs

## Quick Start

### Import MEMORY.md (Curated Long-term Memory)

```bash
python3 tools/import_memories.py \
  --memory-md ~/.openclaw/workspace/MEMORY.md

# Result:
# - Splits by ## sections
# - Auto-assigns domains (self/user/projects)
# - Tags each section
# - Imports to long-term layer
```

**Example Output:**
```
🧠 SupaBrain Memory Importer
📄 Importing MEMORY.md (curated long-term memory)...
   Found 6 sections
   ✅ Imported section: Who I Am
   ✅ Imported section: Current Projects
   ✅ Imported section: Lessons Learned
✅ Import complete: 6 memories imported
```

### Import Daily Logs

```bash
python3 tools/import_memories.py \
  --daily-logs ~/.openclaw/workspace/memory/

# Result:
# - Imports all .md files from directory
# - Tags with directory name + filename
# - Preserves chronological order
```

### Import Single File

```bash
python3 tools/import_memories.py \
  --file ~/notes/important-decision.md \
  --domain projects \
  --layer long

# Custom domain and temporal layer
```

### Import Directory with Pattern

```bash
python3 tools/import_memories.py \
  --dir ~/documents/ \
  --pattern "*.txt" \
  --domain general
  
# Import all .txt files
```

## Options

```
--file FILE           Import single file
--dir DIRECTORY       Import all files from directory
--pattern PATTERN     File pattern (default: *.md)
--memory-md FILE      Import MEMORY.md with section parsing
--daily-logs DIR      Import daily logs (shortcut for --dir with *.md)
--domain DOMAIN       Memory domain (self/user/projects/world/system/general)
--layer LAYER         Temporal layer (working/short/long/archive)
--dry-run             Preview what would be imported
```

## Domain Auto-Detection (MEMORY.md)

When importing MEMORY.md, domains are assigned based on section titles:

| Section Title Contains | Domain Assigned |
|----------------------|----------------|
| "who i am", "identity", "soul" | self |
| "scarface", "human", "user" | user |
| "project", "bct", "supabrain" | projects |
| "lesson", "learned", "mistake" | self |
| *everything else* | general |

## Dry Run Mode

Always test first!

```bash
python3 tools/import_memories.py \
  --memory-md MEMORY.md \
  --dry-run

# Shows what would be imported without writing to database
```

## Examples

### Bootstrap New AI Identity

```bash
# 1. Create identity file
cat > identity.md << 'EOF'
## Who I Am
- Name: Assistant
- Purpose: Help humans with tasks
- Values: Honesty, clarity, efficiency

## My Human
- Name: User
- Preferences: Direct communication
- Timezone: UTC
EOF

# 2. Import
python3 tools/import_memories.py \
  --memory-md identity.md

# 3. Verify
psql supabrain -c "SELECT content FROM memories WHERE domain='self' LIMIT 3"
```

### Archive Old Conversations

```bash
# Import historical logs
python3 tools/import_memories.py \
  --daily-logs ~/old-agent-logs/ \
  --layer archive

# These go to archive layer (searchable but lower priority)
```

### Migrate from Another System

```bash
# If you have memories in JSON/text format
# Convert to .md files first, then:

python3 tools/import_memories.py \
  --dir ~/migration/ \
  --pattern "*.md"
```

## Technical Details

### Section Parsing (MEMORY.md)

Splits on `## ` headers:
```markdown
# MEMORY.md

## Section 1
Content here...

## Section 2
More content...
```

Becomes:
```
Memory 1: "# Section 1\n\nContent here..."
Memory 2: "# Section 2\n\nMore content..."
```

### Tags

Automatically added:
- Filename (without extension)
- "imported" tag
- "dated" tag (if filename contains numbers)
- "dir:dirname" (for directory imports)
- Section title (for MEMORY.md)

### Database Schema

Inserts to `memories` table:
```sql
INSERT INTO memories (
  content,           -- Full text
  temporal_layer,    -- working/short/long/archive
  domain,            -- self/user/projects/world/system/general
  tags,              -- Array of tags
  agent_name,        -- 'importer' or 'scar'
  created_at         -- NOW()
)
```

## Troubleshooting

### "Database connection failed"

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check .env configuration
cat .env
# Should have: DATABASE_URL=postgresql://...

# Test connection manually
psql -d supabrain -c "SELECT 1"
```

### "File not found"

```bash
# Use absolute paths
python3 tools/import_memories.py \
  --file /full/path/to/file.md

# Or relative from current directory
cd ~
python3 /path/to/supabrain/tools/import_memories.py \
  --file .openclaw/workspace/MEMORY.md
```

### "Empty file, skipping"

File exists but is empty or contains only whitespace.
- Check file contents: `cat file.md`
- Ensure file has actual content

### Duplicate memories

If you run import twice, it will create duplicates!

**Prevention:**
```sql
-- Check existing memories first
SELECT COUNT(*), tags 
FROM memories 
WHERE 'imported' = ANY(tags)
GROUP BY tags;

-- Delete if needed
DELETE FROM memories WHERE 'imported' = ANY(tags);
```

**Better:** Use dry-run first to preview!

## Best Practices

### 1. Start with Dry Run

```bash
python3 tools/import_memories.py --memory-md MEMORY.md --dry-run
# Verify sections detected correctly
# Then run without --dry-run
```

### 2. Import in Order

```bash
# 1. Identity first (self domain)
python3 tools/import_memories.py --memory-md MEMORY.md

# 2. Then daily logs (general/projects)
python3 tools/import_memories.py --daily-logs memory/

# 3. Finally archives (old stuff)
python3 tools/import_memories.py --dir old-logs/ --layer archive
```

### 3. Verify After Import

```bash
# Check counts
psql supabrain -c "
  SELECT domain, temporal_layer, COUNT(*) 
  FROM memories 
  GROUP BY domain, temporal_layer
"

# Check sample content
psql supabrain -c "
  SELECT content 
  FROM memories 
  WHERE domain='self' 
  LIMIT 3
"
```

### 4. Use Tags for Organization

Add custom tags after import:
```sql
UPDATE memories 
SET tags = array_append(tags, 'bootstrap')
WHERE 'imported' = ANY(tags) 
  AND created_at > NOW() - INTERVAL '1 hour';
```

## Future Enhancements

- [ ] Embedding generation during import
- [ ] Conflict detection (skip duplicates)
- [ ] Batch import with progress bar
- [ ] Import from JSON/CSV formats
- [ ] Auto-domain detection from content (not just titles)
- [ ] Incremental import (only new files)

---

**Built by Scar 🐺 - SupaBrain v0.5**
