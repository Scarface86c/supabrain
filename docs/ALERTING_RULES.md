# SupaBrain Alerting Rules (v0.4-beta)

> Prometheus alerting thresholds for production monitoring

## Critical Alerts (Immediate Action)

### Database Connectivity
```yaml
- alert: SupaBrainDatabaseDown
  expr: supabrain_db_connected == 0
  for: 1m
  severity: critical
  description: "SupaBrain cannot connect to PostgreSQL database"
  action: "Check database status, network connectivity, credentials"
```

### Embedding Model Not Loaded
```yaml
- alert: SupaBrainModelNotLoaded
  expr: supabrain_embedding_model_loaded == 0
  for: 5m
  severity: critical
  description: "Embedding model failed to load - semantic search unavailable"
  action: "Check model files, disk space, memory availability"
```

### Server Unreachable
```yaml
- alert: SupaBrainHealthEndpointDown
  expr: up{job="supabrain"} == 0
  for: 2m
  severity: critical
  description: "SupaBrain /health endpoint not responding"
  action: "Check systemd service status, server logs, port 8080 availability"
```

---

## Warning Alerts (Monitor Closely)

### High Error Rate
```yaml
- alert: SupaBrainHighErrorRate
  expr: |
    rate(supabrain_requests_total{status=~"5.."}[5m]) 
    / 
    rate(supabrain_requests_total[5m]) 
    > 0.05
  for: 10m
  severity: warning
  description: "Error rate >5% over 10 minutes"
  action: "Check logs for patterns, review recent changes"
```

### Layer Imbalance (Too Many Working Memories)
```yaml
- alert: SupaBrainWorkingLayerOverloaded
  expr: supabrain_memories_total{layer="layer_1"} > 50
  for: 30m
  severity: warning
  description: "Layer 1 (working memory) has >50 entries - should be critical-only"
  action: "Run SleepBeat to migrate memories to appropriate layers"
```

### Total Memory Growth Spike
```yaml
- alert: SupaBrainMemoryGrowthSpike
  expr: |
    sum(supabrain_memories_total) 
    > 
    sum(supabrain_memories_total offset 1h) * 1.5
  for: 15m
  severity: warning
  description: "Total memories increased >50% in 1 hour"
  action: "Check for runaway memory creation, bot loops, duplicate insertion"
```

### Slow Query Performance
```yaml
- alert: SupaBrainSlowQueries
  expr: |
    histogram_quantile(0.95, 
      rate(supabrain_request_duration_seconds_bucket{endpoint="/api/v1/recall"}[5m])
    ) > 2.0
  for: 10m
  severity: warning
  description: "95th percentile recall latency >2 seconds"
  action: "Check database indexes, query patterns, vector search performance"
```

---

## Informational Alerts (Low Priority)

### Daily Memory Consolidation Needed
```yaml
- alert: SupaBrainSleepBeatOverdue
  expr: |
    time() - supabrain_last_sleepbeat_timestamp > 86400 + 3600
  for: 1h
  severity: info
  description: "SleepBeat hasn't run in >25 hours (expected: daily at 23:00)"
  action: "Check cron job status, manually trigger if needed"
```

### Archive Layer Growing
```yaml
- alert: SupaBrainArchiveGrowth
  expr: supabrain_memories_total{layer="layer_5"} > 1000
  for: 1h
  severity: info
  description: "Archive layer (layer_5) has >1000 memories"
  action: "Consider export/backup, review archival policy"
```

---

## Implementation

### Prometheus Configuration

Add to `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'supabrain'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8080']
        labels:
          instance: 'supabrain-prod'
```

### Alert Rules File

Save above rules to `/etc/prometheus/rules/supabrain.yml`:
```yaml
groups:
  - name: supabrain_alerts
    interval: 30s
    rules:
      # (paste alert rules from above)
```

Load in Prometheus config:
```yaml
rule_files:
  - /etc/prometheus/rules/supabrain.yml
```

### Alert Delivery

**Telegram Integration:**
Configure Alertmanager to send critical/warning alerts to Scarface via Telegram bot.

**Log Aggregation:**
Forward all alerts to `~/.openclaw/workspace/memory/alerts-log.txt` for historical review.

---

## Testing Alerts

### Trigger Test Alert (DB Down)
```bash
# Stop database temporarily
systemctl stop postgresql

# Wait 1min, should trigger SupaBrainDatabaseDown
# Restore:
systemctl start postgresql
```

### Trigger Test Alert (Layer Imbalance)
```bash
# Insert 60 memories into layer_1
for i in {1..60}; do
  curl -X POST http://localhost:8080/api/v1/remember \
    -H 'Content-Type: application/json' \
    -d '{"agent_name":"TestAgent","content":"Test memory '$i'","importance_score":0.9,"priority_layer":1}'
done

# Wait 30min, should trigger SupaBrainWorkingLayerOverloaded
```

---

## Monitoring Dashboard

Recommended Grafana panels:
1. **System Health:** DB status, model loaded, uptime
2. **Request Metrics:** Request rate, error rate, latency (p50/p95/p99)
3. **Layer Distribution:** Stacked area chart of memories per layer
4. **Memory Operations:** Counter for remember/recall/delete operations
5. **Alert Status:** Current firing alerts

---

*Created: 2026-03-02 as part of v0.4-beta hardening*
*Status: Ready for Prometheus integration*
