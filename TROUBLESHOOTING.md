# SupaBrain Troubleshooting Guide

Common issues and solutions for SupaBrain deployment and operation.

## Installation Issues

### PostgreSQL Connection Refused

**Symptom:**
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Solutions:**
1. Check PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql
   sudo systemctl start postgresql
   ```

2. Verify port 5432 is listening:
   ```bash
   sudo netstat -plnt | grep 5432
   ```

3. Check PostgreSQL allows local connections:
   ```bash
   # Edit pg_hba.conf
   sudo nano /etc/postgresql/14/main/pg_hba.conf
   
   # Add or verify:
   local   all   postgres   trust
   host    supabrain   postgres   127.0.0.1/32   md5
   ```

4. Restart PostgreSQL:
   ```bash
   sudo systemctl restart postgresql
   ```

### pgvector Extension Not Found

**Symptom:**
```
ERROR: extension "vector" is not available
```

**Solution:**
```bash
# Install pgvector
cd ~
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Create extension in database
psql -U postgres -d supabrain -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Python Dependencies Failed

**Symptom:**
```
ModuleNotFoundError: No module named 'sentence_transformers'
```

**Solution:**
```bash
cd ~/supabrain/core
source venv/bin/activate
pip install -r requirements.txt
```

## Runtime Issues

### API Server Won't Start

**Symptom:**
```
Address already in use: Port 8080
```

**Solutions:**
1. Find and kill process:
   ```bash
   lsof -ti:8080 | xargs kill -9
   ```

2. Or change port:
   ```bash
   # Edit .env
   API_PORT=8081
   ```

### Memory Engine Initialization Fails

**Symptom:**
```
❌ Memory engine initialization failed
```

**Debug steps:**
1. Check database exists:
   ```bash
   psql -U postgres -l | grep supabrain
   ```

2. Run migrations:
   ```bash
   cd ~/supabrain/migrations
   for f in *.sql; do
       echo "Running $f..."
       psql -U postgres -d supabrain -f "$f"
   done
   ```

3. Check model download:
   ```bash
   python3 -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
   ```

### Slow Embedding Generation

**Symptom:**
Memory storage takes 5+ seconds per call

**Causes & Solutions:**
1. **CPU-only embeddings** (expected on non-GPU servers)
   - Use smaller model: `all-MiniLM-L6-v2` (default, fast)
   - Upgrade server with GPU for 10-100x speedup

2. **Model not cached**
   - First run downloads model (~100MB)
   - Subsequent runs use cached model

3. **High memory pressure**
   ```bash
   free -h  # Check available RAM
   # If low, restart server to clear cache
   ```

## Sleep Cycle Issues

### Sleep Cycle Not Running

**Symptom:**
Only 5 archived memories with 200+ total

**Solutions:**
1. Check HEARTBEAT.md integration:
   ```bash
   grep -A 5 "Sleep Cycle" ~/.openclaw/workspace/HEARTBEAT.md
   ```

2. Test manual trigger:
   ```bash
   python3 ~/.openclaw/workspace/heartbeat_sleep.py --force
   ```

3. Check working memory count:
   ```bash
   ~/supabrain/core/venv/bin/python3 ~/.openclaw/workspace/_get_working_count.py
   ```

4. Verify threshold (default: 300):
   ```bash
   grep "WORKING_MEMORY_THRESHOLD" ~/.openclaw/workspace/heartbeat_sleep.py
   ```

### Sleep Cycle Crashes

**Symptom:**
```
ERROR: LLM API timeout
```

**Solutions:**
1. Increase timeout:
   ```bash
   # In sleep_cycle.py
   ANTHROPIC_TIMEOUT = 120  # seconds
   ```

2. Reduce batch size:
   ```bash
   python3 sleep_cycle.py --batch-size 10
   ```

3. Check API key:
   ```bash
   echo $ANTHROPIC_API_KEY
   ```

### Review Decisions Not Applied

**Symptom:**
Sleep cycle runs but memories not promoted/archived

**Debug:**
```bash
# Check review log
psql -U postgres -d supabrain -c "SELECT * FROM review_log ORDER BY created_at DESC LIMIT 10;"

# Verify memory status
psql -U postgres -d supabrain -c "SELECT temporal_layer, status, COUNT(*) FROM memories GROUP BY temporal_layer, status;"
```

## API Issues

### 401 Unauthorized

**Symptom:**
```json
{"detail": "Invalid API key"}
```

**Solutions:**
1. Check authentication requirement:
   ```bash
   grep "REQUIRE_AUTH" ~/supabrain/.env
   ```

2. Disable auth for testing:
   ```bash
   echo "REQUIRE_AUTH=false" >> ~/supabrain/.env
   ```

3. Generate valid key:
   ```bash
   cd ~/supabrain/core
   python3 auth.py generate
   ```

### 429 Too Many Requests

**Symptom:**
```json
{"detail": "Rate limit exceeded"}
```

**Solutions:**
1. Increase rate limit:
   ```bash
   # Edit .env
   RATE_LIMIT_PER_MINUTE=120
   RATE_LIMIT_BURST=200
   ```

2. Disable rate limiting (dev only):
   ```bash
   echo "RATE_LIMIT_ENABLED=false" >> ~/supabrain/.env
   ```

### 500 Internal Server Error

**Debug process:**
1. Check server logs:
   ```bash
   tail -f ~/supabrain/logs/*.log
   ```

2. Test database connection:
   ```bash
   curl http://localhost:8080/health
   ```

3. Check memory engine status:
   ```bash
   curl http://localhost:8080/api/v1/stats?agent_name=YourAgent
   ```

## Search Issues

### Recall Returns No Results

**Symptom:**
Empty array despite having memories

**Solutions:**
1. Check agent name case:
   ```bash
   # Queries are case-insensitive since migration 007
   curl -X POST http://localhost:8080/api/v1/recall \
     -H "Content-Type: application/json" \
     -d '{"agent_name": "scar", "query": "test", "limit": 10}'
   ```

2. Verify memories exist:
   ```bash
   psql -U postgres -d supabrain -c "SELECT COUNT(*) FROM memories WHERE status='active';"
   ```

3. Try broader query:
   ```bash
   # Use empty query to get all memories
   {"agent_name": "YourAgent", "query": "", "limit": 100}
   ```

### Recall Too Slow (>1s)

**Causes & Solutions:**
1. **Missing indexes:**
   ```sql
   -- Run migration 005
   psql -U postgres -d supabrain -f ~/supabrain/migrations/005_add_indexes.sql
   ```

2. **Large result set:**
   - Reduce limit (default: 20, max: 100)
   - Use temporal_layers filter

3. **Database needs vacuum:**
   ```bash
   psql -U postgres -d supabrain -c "VACUUM ANALYZE memories;"
   ```

## Memory Issues

### Memories Not Persisting

**Symptom:**
Store returns success but recall finds nothing

**Debug:**
```bash
# Check database directly
psql -U postgres -d supabrain -c "SELECT id, LEFT(layer_1_summary, 50) FROM memories ORDER BY created_at DESC LIMIT 10;"

# Check agent ID
psql -U postgres -d supabrain -c "SELECT * FROM agents;"
```

### Duplicate Memories

**Symptom:**
Same content stored multiple times

**Causes:**
1. No deduplication (by design - contexts differ)
2. Multiple calls without checking

**Solution:**
```bash
# Search before storing
existing = recall(query="exact content", limit=1)
if not existing:
    remember(content)
```

### Agent "Already Exists" Error

**Symptom:**
```
ERROR: Only one agent allowed per database
```

**Solution:**
This is enforced by design. Each SupaBrain instance = one agent.

If you need multiple agents:
1. Create separate databases
2. Run separate SupaBrain instances
3. Different ports (8080, 8081, ...)

## Performance Optimization

### High Memory Usage

**Check memory:**
```bash
free -h
ps aux | grep python | awk '{sum+=$6} END {print sum/1024 " MB"}'
```

**Solutions:**
1. Reduce model cache:
   - Use smaller embedding model
   - Restart service periodically

2. Database cleanup:
   ```sql
   DELETE FROM memory_access_log WHERE created_at < NOW() - INTERVAL '30 days';
   VACUUM FULL memories;
   ```

### Database Growing Too Fast

**Check size:**
```bash
psql -U postgres -d supabrain -c "SELECT pg_size_pretty(pg_database_size('supabrain'));"
```

**Solutions:**
1. Run sleep cycle more frequently
2. Archive old memories:
   ```sql
   UPDATE memories 
   SET status = 'archived', temporal_layer = 'archive'
   WHERE created_at < NOW() - INTERVAL '90 days' 
   AND status = 'active'
   AND temporal_layer = 'long';
   ```

3. Clean up logs:
   ```sql
   DELETE FROM review_log WHERE created_at < NOW() - INTERVAL '30 days';
   DELETE FROM query_analytics WHERE created_at < NOW() - INTERVAL '30 days';
   ```

## Integration Issues

### OpenClaw Can't Access SupaBrain

**Symptom:**
```
ConnectionError: Failed to connect to http://localhost:8080
```

**Solutions:**
1. Check API is running:
   ```bash
   curl http://localhost:8080/health
   ```

2. Check firewall:
   ```bash
   sudo ufw status
   sudo ufw allow 8080
   ```

3. Verify .env configuration:
   ```bash
   cat ~/supabrain/.env | grep API_
   ```

### Heartbeat Not Triggering Sleep

**Debug:**
```bash
# Test heartbeat script
python3 ~/.openclaw/workspace/heartbeat_sleep.py --dry-run

# Check last activity
cat /tmp/last_activity.txt
date -d @$(cat /tmp/last_activity.txt)

# Force trigger
python3 ~/.openclaw/workspace/heartbeat_sleep.py --force
```

## Getting Help

### Enable Debug Logging

```bash
# Edit server.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Collect Diagnostic Info

```bash
# System info
uname -a
python3 --version
psql --version

# SupaBrain status
curl http://localhost:8080/health
stats --summary

# Database state
psql -U postgres -d supabrain -c "SELECT temporal_layer, status, COUNT(*) FROM memories GROUP BY temporal_layer, status;"
```

### Report Issues

When reporting issues, include:
1. Error message (full traceback)
2. Steps to reproduce
3. System info (OS, Python, PostgreSQL versions)
4. Diagnostic output (health check, stats)

GitHub Issues: https://github.com/yourusername/supabrain/issues

---

**Last Updated:** 2026-02-11  
**Covers:** SupaBrain v0.2.0+
