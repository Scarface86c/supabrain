# SupaBrain Load Testing Plan (v0.4-beta)

> Stress testing scenarios to validate production readiness

## Objectives

1. **Validate concurrent operation handling** (100+ simultaneous requests)
2. **Identify performance bottlenecks** (database, embeddings, API)
3. **Confirm error handling under load** (timeouts, connection limits)
4. **Establish baseline metrics** (latency, throughput, resource usage)

---

## Test Scenarios

### 1. Concurrent Recall Operations (Read Heavy)

**Goal:** Stress test semantic search with 100 concurrent recall requests

**Setup:**
```bash
# Create test script: load_test_recall.sh
cat > ~/supabrain/tests/load_test_recall.sh << 'EOF'
#!/bin/bash
# Parallel recall test

AGENT="LoadTestAgent"
QUERIES=(
  "machine learning concepts"
  "project goals and objectives"
  "recent decisions and changes"
  "technical implementation details"
  "important relationships and people"
)

run_recall() {
  QUERY="${QUERIES[$RANDOM % ${#QUERIES[@]}]}"
  START=$(date +%s%3N)
  
  RESPONSE=$(curl -s -X POST http://localhost:8080/api/v1/recall \
    -H 'Content-Type: application/json' \
    -d "{\"agent_name\":\"$AGENT\",\"query\":\"$QUERY\",\"limit\":10}")
  
  END=$(date +%s%3N)
  DURATION=$((END - START))
  
  if echo "$RESPONSE" | jq -e '. | length > 0' > /dev/null 2>&1; then
    echo "SUCCESS: ${DURATION}ms - $QUERY"
  else
    echo "FAIL: ${DURATION}ms - $QUERY - $RESPONSE"
  fi
}

export -f run_recall
export QUERIES

# Run 100 concurrent recalls
seq 1 100 | parallel -j 100 run_recall

EOF
chmod +x ~/supabrain/tests/load_test_recall.sh
```

**Execute:**
```bash
time ~/supabrain/tests/load_test_recall.sh | tee ~/supabrain/tests/recall_load_results.txt
```

**Success Criteria:**
- ✅ All 100 requests complete successfully
- ✅ P95 latency < 3 seconds
- ✅ No database connection pool exhaustion
- ✅ No memory leaks (check with `systemctl status supabrain`)

---

### 2. Bulk Memory Insertion (Write Heavy)

**Goal:** Test rapid memory insertion (1000 memories in 1 minute)

**Setup:**
```bash
cat > ~/supabrain/tests/load_test_insert.sh << 'EOF'
#!/bin/bash
# Bulk insert test

AGENT="LoadTestAgent"

insert_memory() {
  ID=$1
  START=$(date +%s%3N)
  
  RESPONSE=$(curl -s -X POST http://localhost:8080/api/v1/remember \
    -H 'Content-Type: application/json' \
    -d "{
      \"agent_name\":\"$AGENT\",
      \"content\":\"Load test memory $ID: $(date) - Random data $(uuidgen)\",
      \"importance_score\":0.5,
      \"temporal_layer\":\"working\",
      \"tags\":[\"load-test\",\"batch-$((ID / 100))\"]
    }")
  
  END=$(date +%s%3N)
  DURATION=$((END - START))
  
  if echo "$RESPONSE" | jq -e '.memory_id' > /dev/null 2>&1; then
    MEMORY_ID=$(echo "$RESPONSE" | jq -r '.memory_id')
    echo "SUCCESS: ${DURATION}ms - Memory #$MEMORY_ID created"
  else
    echo "FAIL: ${DURATION}ms - $RESPONSE"
  fi
}

export -f insert_memory

# Insert 1000 memories (50 concurrent at a time)
seq 1 1000 | parallel -j 50 insert_memory

EOF
chmod +x ~/supabrain/tests/load_test_insert.sh
```

**Execute:**
```bash
time ~/supabrain/tests/load_test_insert.sh | tee ~/supabrain/tests/insert_load_results.txt
```

**Success Criteria:**
- ✅ All 1000 insertions complete
- ✅ P95 latency < 2 seconds per insert
- ✅ Database disk I/O remains healthy
- ✅ Embedding generation doesn't bottleneck

**Cleanup:**
```bash
# Delete all load test memories after testing
curl -X DELETE "http://localhost:8080/api/v1/memory/batch?agent_name=LoadTestAgent&tag=load-test"
```

---

### 3. Mixed Workload (Real-World Simulation)

**Goal:** Simulate realistic usage with 70% reads, 20% writes, 10% deletes

**Setup:**
```bash
cat > ~/supabrain/tests/load_test_mixed.sh << 'EOF'
#!/bin/bash
# Mixed workload test

AGENT="LoadTestAgent"

mixed_operation() {
  ROLL=$((RANDOM % 100))
  
  if [ $ROLL -lt 70 ]; then
    # 70% Recall
    curl -s -X POST http://localhost:8080/api/v1/recall \
      -H 'Content-Type: application/json' \
      -d "{\"agent_name\":\"$AGENT\",\"query\":\"test query\",\"limit\":5}" > /dev/null
    echo "RECALL"
    
  elif [ $ROLL -lt 90 ]; then
    # 20% Insert
    curl -s -X POST http://localhost:8080/api/v1/remember \
      -H 'Content-Type: application/json' \
      -d "{\"agent_name\":\"$AGENT\",\"content\":\"Mixed test $(date +%s)\",\"importance_score\":0.5}" > /dev/null
    echo "INSERT"
    
  else
    # 10% Stats query
    curl -s "http://localhost:8080/api/v1/stats?agent_name=$AGENT" > /dev/null
    echo "STATS"
  fi
}

export -f mixed_operation

# Run 500 mixed operations (25 concurrent)
seq 1 500 | parallel -j 25 mixed_operation | sort | uniq -c

EOF
chmod +x ~/supabrain/tests/load_test_mixed.sh
```

**Execute:**
```bash
time ~/supabrain/tests/load_test_mixed.sh
```

**Success Criteria:**
- ✅ All operations complete
- ✅ No failed requests
- ✅ Balanced workload distribution (~350 recalls, ~100 inserts, ~50 stats)

---

### 4. Sustained Load (Endurance Test)

**Goal:** Run moderate load for 1 hour to detect memory leaks, connection leaks

**Setup:**
```bash
cat > ~/supabrain/tests/load_test_endurance.sh << 'EOF'
#!/bin/bash
# 1-hour endurance test

AGENT="LoadTestAgent"
END_TIME=$(($(date +%s) + 3600))  # Run for 1 hour

while [ $(date +%s) -lt $END_TIME ]; do
  # 10 ops/second average
  for i in {1..10}; do
    curl -s -X POST http://localhost:8080/api/v1/recall \
      -H 'Content-Type: application/json' \
      -d "{\"agent_name\":\"$AGENT\",\"query\":\"sustained test\",\"limit\":5}" > /dev/null &
  done
  sleep 1
  
  # Log progress every 5 minutes
  if [ $(($(date +%s) % 300)) -eq 0 ]; then
    MEMORY=$(systemctl --user status supabrain.service | grep "Memory:" | awk '{print $2}')
    echo "$(date): Memory usage: $MEMORY"
  fi
done

wait
echo "Endurance test complete: 1 hour sustained load"
EOF
chmod +x ~/supabrain/tests/load_test_endurance.sh
```

**Execute:**
```bash
~/supabrain/tests/load_test_endurance.sh | tee ~/supabrain/tests/endurance_results.txt
```

**Success Criteria:**
- ✅ Memory usage stays stable (< ±20% fluctuation)
- ✅ No database connection pool leaks
- ✅ No gradual performance degradation

---

## Metrics to Monitor

During all tests, monitor:

### Prometheus Metrics
```bash
# Request rate
rate(supabrain_requests_total[1m])

# Error rate
rate(supabrain_requests_total{status=~"5.."}[1m])

# Latency percentiles
histogram_quantile(0.95, rate(supabrain_request_duration_seconds_bucket[5m]))

# Memory operations
rate(supabrain_memory_operations_total[1m])
```

### System Resources
```bash
# CPU usage
top -bn1 | grep supabrain

# Memory usage
systemctl --user status supabrain.service | grep Memory

# Database connections
psql -U scar_user -d supabrain_db -c "SELECT count(*) FROM pg_stat_activity WHERE datname='supabrain_db';"

# Disk I/O
iostat -x 5
```

---

## Expected Baselines (Reference)

Based on current hardware (Ubuntu VM, 4GB RAM, 2 CPU cores):

- **Recall latency (p95):** 1-2 seconds
- **Insert latency (p95):** 500ms - 1 second
- **Throughput:** ~50-100 operations/second
- **Memory usage:** 300-500MB steady state
- **DB connections:** 5-10 active

**Note:** Baselines will be established after first test run.

---

## Failure Scenarios to Test

### Database Connection Loss
```bash
# Simulate DB failure during load
systemctl stop postgresql  # During test
# Expected: HTTPException 503, graceful degradation
# Restore: systemctl start postgresql
```

### Port Unavailability
```bash
# Block port 8080
sudo iptables -A INPUT -p tcp --dport 8080 -j DROP
# Expected: Connection timeouts, client retries
# Restore: sudo iptables -D INPUT -p tcp --dport 8080 -j DROP
```

### Disk Full Scenario
```bash
# Fill disk to 95%
dd if=/dev/zero of=/tmp/fillup.img bs=1M count=5000
# Expected: Graceful error handling, no corruption
# Restore: rm /tmp/fillup.img
```

---

## Prerequisites

### Install GNU Parallel
```bash
sudo apt-get install parallel -y
```

### Create Test Directory
```bash
mkdir -p ~/supabrain/tests
```

### Seed Test Data
```bash
# Insert 100 baseline memories for recall testing
for i in {1..100}; do
  curl -X POST http://localhost:8080/api/v1/remember \
    -H 'Content-Type: application/json' \
    -d "{\"agent_name\":\"LoadTestAgent\",\"content\":\"Baseline memory $i about various topics like ML, coding, projects, and systems\",\"importance_score\":0.6,\"tags\":[\"baseline\"]}"
done
```

---

## Execution Schedule

**Day 1:**
- Test 1: Concurrent Recall (30min)
- Test 2: Bulk Insert (30min)

**Day 2:**
- Test 3: Mixed Workload (1hr)
- Test 4: Endurance Test (1hr)

**Day 3:**
- Failure scenario testing (2hr)
- Results analysis & report

---

## Results Documentation

After each test, capture:
1. **Raw logs:** Save to `~/supabrain/tests/<test_name>_results.txt`
2. **Metrics snapshot:** Export Prometheus data for test duration
3. **Resource usage:** CPU, memory, disk I/O stats
4. **Failures:** Count, types, error messages
5. **Performance:** Latency percentiles (p50, p95, p99)

**Summary Report:** Update `~/supabrain/docs/LOAD_TEST_RESULTS.md` with findings.

---

*Created: 2026-03-02 as part of v0.4-beta hardening*
*Status: Ready for execution*
*Prerequisites: GNU Parallel, baseline test data*
