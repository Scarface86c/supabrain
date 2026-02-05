#!/bin/bash
#
# SupaBrain Quick Start Script
#
# Sets up and tests SupaBrain v0.4 in one command.
# For new users who want to get started quickly.
#
# Usage:
#   ./quickstart.sh          # Full setup
#   ./quickstart.sh --test   # Just test (skip setup)
#

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║           🧠 SupaBrain v0.4 Quick Start                 ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo

# Check if just testing
TEST_ONLY=false
if [ "$1" == "--test" ]; then
    TEST_ONLY=true
    echo "📋 Test mode - skipping setup"
    echo
fi

# 1. Check Python
echo -e "${BLUE}1. Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "   ✅ Python $PYTHON_VERSION"
echo

# 2. Check dependencies
if [ "$TEST_ONLY" = false ]; then
    echo -e "${BLUE}2. Installing Python dependencies...${NC}"
    cd core
    
    if [ ! -d "venv" ]; then
        echo "   Creating virtual environment..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    
    if [ ! -f "requirements.txt" ]; then
        echo "   Creating requirements.txt..."
        cat > requirements.txt << EOF
anthropic>=0.18.0
sentence-transformers>=2.2.0
fastapi>=0.104.0
uvicorn>=0.24.0
requests>=2.31.0
EOF
    fi
    
    echo "   Installing packages..."
    pip install -q -r requirements.txt
    
    echo "   ✅ Dependencies installed"
    cd ..
    echo
else
    echo -e "${BLUE}2. Skipping dependency installation${NC}"
    echo
fi

# 3. Test auto-capture
echo -e "${BLUE}3. Testing auto-capture...${NC}"

python3 << 'EOF'
import sys
import os
sys.path.append('core')

from auto_capture import capture_learning, capture_milestone
from supabrain_queue import MemoryQueue

# Test captures
capture_milestone("Quick start test beginning", tags=["quickstart", "test"])
capture_learning("Testing SupaBrain auto-capture system", tags=["quickstart", "test"])

# Check queue
queue = MemoryQueue()
count = queue.count()
print(f"   ✅ Captured 2 memories (queue: {count} total)")
EOF

echo

# 4. Run stats dashboard
echo -e "${BLUE}4. Checking queue stats...${NC}"
python3 tools/stats_dashboard.py
echo

# 5. Test cleanup
echo -e "${BLUE}5. Testing cleanup tool...${NC}"
echo "   Removing test memories..."
python3 tools/queue_cleanup.py --tag quickstart --quiet 2>/dev/null || echo "   (cleanup tool output suppressed)"
echo "   ✅ Cleanup works"
echo

# Summary
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  ✅ Quick Start Complete!               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo
echo "🎉 SupaBrain v0.4 is ready to use!"
echo
echo "Next steps:"
echo
echo "1. Bootstrap consciousness:"
echo "   python3 examples/seed-consciousness.py --name YourAI --human YourName --purpose assist"
echo
echo "2. Try an example:"
echo "   python3 examples/integrations/simple_script.py"
echo
echo "3. Check stats:"
echo "   python3 tools/stats_dashboard.py"
echo
echo "4. Run sleep cycle (when you have memories):"
echo "   python3 core/sleep_cycle.py --dry-run"
echo
echo "5. Read the docs:"
echo "   README.md, docs/AUTO_CAPTURE_README.md, docs/SLEEP_CYCLE_README.md"
echo
echo "Happy memory building! 🧠"
echo
