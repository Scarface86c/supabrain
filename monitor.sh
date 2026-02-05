#!/bin/bash
# SupaBrain Monitoring Script
# Shows complete system status at a glance

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║           🧠 SupaBrain System Monitor                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo

# 1. Worker Status
echo -e "${BLUE}1. Worker Status${NC}"
WORKER_PID=$(ps aux | grep "[p]ython.*supabrain_worker" | awk '{print $2}')
if [ -n "$WORKER_PID" ]; then
    echo -e "   ${GREEN}✅ Running${NC} (PID: $WORKER_PID)"
    
    # CPU/Memory
    CPU=$(ps -p $WORKER_PID -o %cpu= | tr -d ' ')
    MEM=$(ps -p $WORKER_PID -o %mem= | tr -d ' ')
    echo "   CPU: ${CPU}% | Memory: ${MEM}%"
    
    # Uptime
    ELAPSED=$(ps -p $WORKER_PID -o etime= | tr -d ' ')
    echo "   Uptime: $ELAPSED"
else
    echo -e "   ${RED}❌ Not running${NC}"
fi
echo

# 2. Database Status
echo -e "${BLUE}2. Database Status${NC}"
if psql postgresql://postgres:supabrain2024@localhost:5432/supabrain -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Connected${NC}"
    
    # Memory counts by layer
    echo "   Memory Distribution:"
    psql postgresql://postgres:supabrain2024@localhost:5432/supabrain -t -c "
        SELECT temporal_layer, COUNT(*) 
        FROM memories 
        GROUP BY temporal_layer 
        ORDER BY temporal_layer
    " 2>/dev/null | while read layer count; do
        if [ -n "$layer" ]; then
            echo "      - $layer: $count"
        fi
    done
    
    # Total memories
    TOTAL=$(psql postgresql://postgres:supabrain2024@localhost:5432/supabrain -t -c "SELECT COUNT(*) FROM memories" 2>/dev/null | tr -d ' ')
    echo "   Total memories: $TOTAL"
else
    echo -e "   ${RED}❌ Connection failed${NC}"
fi
echo

# 3. Think Queue Status
echo -e "${BLUE}3. Think Queue${NC}"
QUEUE_FILE="$HOME/.openclaw/workspace/think_queue.json"
if [ -f "$QUEUE_FILE" ]; then
    TOTAL=$(python3 -c "import json; print(len(json.load(open('$QUEUE_FILE'))))" 2>/dev/null || echo "0")
    PENDING=$(python3 -c "import json; q=json.load(open('$QUEUE_FILE')); print(len([t for t in q if t.get('status')=='pending']))" 2>/dev/null || echo "0")
    COMPLETE=$(python3 -c "import json; q=json.load(open('$QUEUE_FILE')); print(len([t for t in q if t.get('status')=='complete']))" 2>/dev/null || echo "0")
    
    echo "   Total: $TOTAL thoughts"
    echo -e "   ${YELLOW}⏳ Pending: $PENDING${NC}"
    echo -e "   ${GREEN}✅ Complete: $COMPLETE${NC}"
    
    # Show pending thoughts
    if [ "$PENDING" -gt "0" ]; then
        echo "   Next up:"
        python3 -c "
import json
q = json.load(open('$QUEUE_FILE'))
pending = [t for t in q if t.get('status')=='pending'][:3]
for t in pending:
    print(f\"      - {t['topic']} ({t['priority']})\")
" 2>/dev/null
    fi
else
    echo -e "   ${YELLOW}⚠️  Queue file not found${NC}"
fi
echo

# 4. Recent Logs
echo -e "${BLUE}4. Recent Logs${NC}"
if [ -f "/tmp/supabrain_worker_pg.log" ]; then
    echo "   Last 5 lines:"
    tail -5 /tmp/supabrain_worker_pg.log | sed 's/^/      /'
else
    echo -e "   ${YELLOW}⚠️  No log file${NC}"
fi
echo

# 5. Configuration
echo -e "${BLUE}5. Configuration${NC}"
if [ -f "$HOME/supabrain/.env" ]; then
    echo "   Database: $(grep DATABASE_URL $HOME/supabrain/.env | cut -d'=' -f2 | cut -d'@' -f2)"
    
    if grep -q "ANTHROPIC_API_KEY=sk-ant" $HOME/supabrain/.env 2>/dev/null; then
        echo -e "   API Key: ${GREEN}✅ Set${NC}"
    else
        echo -e "   API Key: ${YELLOW}⚠️  Not set or invalid${NC}"
    fi
    
    THINK_INTERVAL=$(grep THINK_CHECK_INTERVAL $HOME/supabrain/.env | cut -d'=' -f2 | tr -d ' ' | cut -d'#' -f1)
    echo "   Think Cycle: ${THINK_INTERVAL}s ($(($THINK_INTERVAL / 60))min)"
else
    echo -e "   ${RED}❌ .env not found${NC}"
fi
echo

# 6. Disk Usage
echo -e "${BLUE}6. Disk Usage${NC}"
if [ -f "$HOME/.openclaw/workspace/supabrain.db" ]; then
    DB_SIZE=$(du -h "$HOME/.openclaw/workspace/supabrain.db" | cut -f1)
    echo "   SQLite DB: $DB_SIZE"
fi

QUEUE_SIZE=$(du -h "$HOME/.openclaw/workspace/think_queue.json" 2>/dev/null | cut -f1 || echo "0")
echo "   Think Queue: $QUEUE_SIZE"
echo

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Summary:${NC}"
if [ -n "$WORKER_PID" ] && psql postgresql://postgres:supabrain2024@localhost:5432/supabrain -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ System Operational${NC}"
else
    echo -e "${YELLOW}⚠️  Issues Detected${NC}"
    [ -z "$WORKER_PID" ] && echo "   - Worker not running"
    ! psql postgresql://postgres:supabrain2024@localhost:5432/supabrain -c "SELECT 1" > /dev/null 2>&1 && echo "   - Database not accessible"
fi
echo

echo "Commands:"
echo "  Start worker:  cd ~/supabrain/core && nohup python3 -u supabrain_worker.py > /tmp/supabrain_worker_pg.log 2>&1 &"
echo "  Stop worker:   pkill -f supabrain_worker"
echo "  View logs:     tail -f /tmp/supabrain_worker_pg.log"
echo "  Add thought:   python3 ~/.openclaw/workspace/think_cycle_prototype.py add \"Topic\" \"high\" \"Context\""
echo
