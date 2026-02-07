#!/usr/bin/env python3
"""
SupaBrain Background Worker - OpenClaw Integration
Uses OpenClaw agent for LLM processing (Max Account!)

Standalone process for proactive cognition and memory consolidation
"""

import asyncio
import asyncpg
import json
import os
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Configuration
THINK_CHECK_INTERVAL = int(os.getenv("THINK_CHECK_INTERVAL", "60"))  # TEST: 60s
SLEEP_CHECK_INTERVAL = int(os.getenv("SLEEP_CHECK_INTERVAL", "1800"))  # 30 min
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:supabrain2024@localhost:5432/supabrain")
OPENCLAW_AGENT = os.getenv("OPENCLAW_AGENT", "worker")  # Worker agent ID
THINK_QUEUE_FILE = Path.home() / ".openclaw/workspace/think_queue.json"


class SupaBrainWorker:
    """Background worker for proactive cognition via OpenClaw"""
    
    def __init__(self):
        self.db_pool = None
        self.running = False
        
    async def initialize(self):
        """Initialize connections"""
        print("🧠 SupaBrain Worker (OpenClaw Edition) starting...")
        
        # Database pool
        self.db_pool = await asyncpg.create_pool(
            DB_URL,
            min_size=2,
            max_size=5
        )
        print("✅ Database connected")
        
        # Verify OpenClaw agent exists
        result = subprocess.run(['openclaw', 'agents', 'list'], capture_output=True, text=True)
        if OPENCLAW_AGENT in result.stdout:
            print(f"✅ OpenClaw agent '{OPENCLAW_AGENT}' found")
            print("   → Using your Max Account automatically!")
        else:
            print(f"⚠️  OpenClaw agent '{OPENCLAW_AGENT}' not found - run: openclaw agents add {OPENCLAW_AGENT}")
        
        self.running = True
        print("✅ Worker initialized")
        
    async def close(self):
        """Cleanup connections"""
        self.running = False
        if self.db_pool:
            await self.db_pool.close()
        print("👋 Worker shutdown complete")
    
    # ===== THINK CYCLE =====
    
    def load_think_queue(self):
        """Load think queue from file"""
        if not THINK_QUEUE_FILE.exists():
            return []
        try:
            with open(THINK_QUEUE_FILE) as f:
                return json.load(f)
        except:
            return []
    
    def save_think_queue(self, queue):
        """Save think queue to file"""
        THINK_QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(THINK_QUEUE_FILE, 'w') as f:
            json.dump(queue, f, indent=2)
    
    def invoke_openclaw_agent(self, prompt, timeout=60):
        """Invoke OpenClaw agent for LLM processing"""
        try:
            result = subprocess.run(
                [
                    'openclaw', 'agent',
                    '--agent', OPENCLAW_AGENT,
                    '--message', prompt,
                    '--json',
                    '--timeout', str(timeout)
                ],
                capture_output=True,
                text=True,
                timeout=timeout + 10
            )
            
            if result.returncode == 0:
                # Parse JSON response
                try:
                    data = json.loads(result.stdout)
                    # Extract agent's response
                    if 'reply' in data and isinstance(data['reply'], str):
                        return data['reply']
                    elif 'text' in data:
                        return data['text']
                    # Fallback: return whole JSON as string
                    return json.dumps(data, indent=2)
                except:
                    # If JSON parsing fails, return stdout
                    return result.stdout.strip()
            else:
                raise Exception(f"OpenClaw agent failed (code {result.returncode}): {result.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception(f"OpenClaw agent timeout ({timeout}s)")
        except Exception as e:
            raise Exception(f"OpenClaw agent error: {e}")
    
    async def process_think_cycle(self):
        """Process pending thoughts with OpenClaw LLM"""
        # Load from file-based queue
        queue = self.load_think_queue()
        pending = [t for t in queue if t.get('status') == 'pending']
        
        if not pending:
            return
        
        # Sort by priority
        priority_order = {'urgent': 4, 'high': 3, 'medium': 2, 'low': 1}
        pending.sort(key=lambda t: priority_order.get(t.get('priority', 'medium'), 0), reverse=True)
        
        # Process top 3
        for thought in pending[:3]:
            print(f"\n💭 Thinking about: {thought['topic']}")
            
            # Mark in progress
            thought['status'] = 'in_progress'
            self.save_think_queue(queue)
            
            try:
                # Invoke OpenClaw agent
                prompt = f"""You are thinking proactively about: {thought['topic']}

Context: {thought['context']}

Task: Reflect, research, and develop insights. Write your thoughts and actionable conclusions.

Focus on:
- What do I need to learn?
- What decisions should I make?
- What actions should I take?
- What new questions emerge?

Be concise but thorough. Write like you're making notes for yourself."""

                insights = self.invoke_openclaw_agent(prompt, timeout=60)
                
                # Store as memory
                async with self.db_pool.acquire() as conn:
                    content = f"Thought: {thought['topic']}\n\nInsights:\n{insights}"
                    
                    await conn.execute("""
                        INSERT INTO memories (content, temporal_layer, domain, tags, agent_name)
                        VALUES ($1, 'long', 'self', $2, 'worker')
                    """, content, ['think-cycle', 'reflection', thought['topic']])
                
                # Mark complete
                thought['status'] = 'complete'
                thought['completed_at'] = datetime.now().isoformat()
                thought['insights'] = insights[:200] + "..." if len(insights) > 200 else insights
                self.save_think_queue(queue)
                
                print(f"✅ Thought complete: {thought['topic']}")
                
            except Exception as e:
                print(f"❌ Error processing thought: {e}")
                thought['status'] = 'pending'  # Reset to try again later
                self.save_think_queue(queue)
    
    # ===== SLEEP CYCLE =====
    
    async def process_sleep_cycle(self):
        """Check and run sleep cycle if needed"""
        async with self.db_pool.acquire() as conn:
            # Check working memory count
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM memories 
                WHERE temporal_layer = 'working' 
                AND (expires_at IS NULL OR expires_at > NOW())
            """)
            
            # Check expired memories
            expired = await conn.fetchval("""
                SELECT COUNT(*) FROM memories 
                WHERE temporal_layer = 'working' 
                AND expires_at IS NOT NULL 
                AND expires_at < NOW()
            """)
            
            if count > 300 or expired > 50:
                print(f"\n💤 Sleep cycle triggered (working: {count}, expired: {expired})")
                print("   (Sleep cycle execution - TODO: integrate with OpenClaw)")
            
    # ===== MAIN LOOP =====
    
    async def run(self):
        """Main worker loop"""
        await self.initialize()
        
        last_think = 0
        last_sleep = 0
        
        print("\n🚀 Worker running...")
        print(f"   Think cycle: every {THINK_CHECK_INTERVAL}s ({THINK_CHECK_INTERVAL//60} min)")
        print(f"   Sleep cycle: every {SLEEP_CHECK_INTERVAL}s ({SLEEP_CHECK_INTERVAL//60} min)")
        print(f"   Press Ctrl+C to stop\n")
        
        try:
            while self.running:
                now = time.time()
                
                # Think cycle check
                if now - last_think >= THINK_CHECK_INTERVAL:
                    await self.process_think_cycle()
                    last_think = now
                
                # Sleep cycle check
                if now - last_sleep >= SLEEP_CHECK_INTERVAL:
                    await self.process_sleep_cycle()
                    last_sleep = now
                
                # Sleep briefly
                await asyncio.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Shutdown requested...")
        finally:
            await self.close()


async def main():
    """Entry point"""
    worker = SupaBrainWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
