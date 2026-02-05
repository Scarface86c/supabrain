#!/bin/bash
#
# SupaBrain One-Command Setup
# Works on: Ubuntu, Debian, macOS
#
# Usage: ./setup.sh
#

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║           🧠 SupaBrain Setup (v0.4.0)                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    PKG_MGR="apt"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
    PKG_MGR="brew"
else
    echo -e "${RED}❌ Unsupported OS: $OSTYPE${NC}"
    echo "Supported: Linux (Ubuntu/Debian) or macOS"
    exit 1
fi

echo -e "${BLUE}Detected OS: $OS${NC}"
echo

# 1. Check/Install PostgreSQL
echo -e "${BLUE}1. Checking PostgreSQL...${NC}"
if ! command -v psql &> /dev/null; then
    echo "   PostgreSQL not found. Installing..."
    
    if [ "$OS" == "linux" ]; then
        sudo apt update
        sudo apt install -y postgresql postgresql-contrib
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
    else
        brew install postgresql@14
        brew services start postgresql@14
    fi
    
    echo -e "   ${GREEN}✅ PostgreSQL installed${NC}"
else
    echo -e "   ${GREEN}✅ PostgreSQL found${NC}"
fi
echo

# 2. Check/Install pgvector
echo -e "${BLUE}2. Checking pgvector extension...${NC}"

if [ "$OS" == "linux" ]; then
    # Check if pgvector is installed
    if sudo -u postgres psql -c "SELECT 1 FROM pg_available_extensions WHERE name='vector'" 2>/dev/null | grep -q 1; then
        echo -e "   ${GREEN}✅ pgvector found${NC}"
    else
        echo "   pgvector not found. Installing..."
        
        # Install build dependencies
        sudo apt install -y build-essential postgresql-server-dev-14 git
        
        # Clone and build pgvector
        cd /tmp
        git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
        cd pgvector
        make
        sudo make install
        cd ..
        rm -rf pgvector
        
        echo -e "   ${GREEN}✅ pgvector installed${NC}"
    fi
else
    # macOS
    brew install pgvector
    echo -e "   ${GREEN}✅ pgvector installed${NC}"
fi
echo

# 3. Create database
echo -e "${BLUE}3. Setting up database...${NC}"

if [ "$OS" == "linux" ]; then
    PSQL_USER="postgres"
    PSQL_CMD="sudo -u postgres psql"
else
    PSQL_USER="$USER"
    PSQL_CMD="psql postgres"
fi

# Check if database exists
if $PSQL_CMD -lqt | cut -d \| -f 1 | grep -qw supabrain; then
    echo "   Database 'supabrain' already exists"
    read -p "   Recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $PSQL_CMD -c "DROP DATABASE supabrain;"
        $PSQL_CMD -c "CREATE DATABASE supabrain;"
        echo -e "   ${GREEN}✅ Database recreated${NC}"
    else
        echo "   Keeping existing database"
    fi
else
    $PSQL_CMD -c "CREATE DATABASE supabrain;"
    echo -e "   ${GREEN}✅ Database created${NC}"
fi

# Enable pgvector
$PSQL_CMD -d supabrain -c "CREATE EXTENSION IF NOT EXISTS vector;"
echo -e "   ${GREEN}✅ pgvector extension enabled${NC}"

# Run migrations
echo "   Running migrations..."
for migration in migrations/*.sql; do
    if [ -f "$migration" ]; then
        echo "      - $(basename $migration)"
        $PSQL_CMD -d supabrain -f "$migration" > /dev/null 2>&1 || echo "      (may already exist, skipping)"
    fi
done
echo -e "   ${GREEN}✅ Migrations complete${NC}"
echo

# 4. Python dependencies
echo -e "${BLUE}4. Installing Python dependencies...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.10+${NC}"
    exit 1
fi

cd core

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   Virtual environment created"
fi

source venv/bin/activate

# Create requirements.txt if missing
if [ ! -f "requirements.txt" ]; then
    cat > requirements.txt << EOF
anthropic>=0.18.0
sentence-transformers>=2.2.0
torch>=2.0.0
fastapi>=0.104.0
uvicorn>=0.24.0
asyncpg>=0.29.0
numpy>=1.24.0
python-dotenv>=1.0.0
requests>=2.31.0
EOF
fi

pip install -q --upgrade pip
pip install -q -r requirements.txt

echo -e "   ${GREEN}✅ Python dependencies installed${NC}"
cd ..
echo

# 5. Create .env if missing
echo -e "${BLUE}5. Configuring environment...${NC}"

if [ ! -f ".env" ]; then
    cat > .env << EOF
# SupaBrain Configuration
DATABASE_URL=postgresql://$PSQL_USER@localhost:5432/supabrain
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
DEVICE=cpu

# API Keys (optional, for sleep cycle LLM)
# ANTHROPIC_API_KEY=your_key_here
EOF
    echo -e "   ${GREEN}✅ .env created${NC}"
    echo -e "   ${YELLOW}⚠️  Edit .env to add ANTHROPIC_API_KEY for sleep cycle${NC}"
else
    echo "   .env already exists"
fi
echo

# 6. Test connection
echo -e "${BLUE}6. Testing database connection...${NC}"

cd core
source venv/bin/activate

python3 << 'PYEOF'
import asyncpg
import asyncio

async def test():
    try:
        conn = await asyncpg.connect('postgresql://postgres@localhost:5432/supabrain')
        result = await conn.fetchval('SELECT 1')
        await conn.close()
        print("   ✅ Database connection OK")
        return True
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

asyncio.run(test())
PYEOF

cd ..
echo

# Summary
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ✅ Setup Complete!                         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo
echo "🎉 SupaBrain is ready!"
echo
echo "Next steps:"
echo
echo "1. (Optional) Add Anthropic API key for sleep cycle:"
echo "   Edit .env and set ANTHROPIC_API_KEY=your_key_here"
echo
echo "2. Start the server:"
echo "   cd core && source venv/bin/activate && python server.py"
echo
echo "3. Try it out:"
echo "   python examples/seed-consciousness.py --name AI --human Human"
echo "   python examples/integrations/simple_script.py"
echo
echo "4. Read the docs:"
echo "   README.md, docs/AUTO_CAPTURE_README.md"
echo
echo "Happy memory building! 🧠"
echo
