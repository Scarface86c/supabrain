#!/usr/bin/env python3
"""
SupaBrain Background Worker
Standalone process for proactive cognition and memory consolidation

Runs independently of OpenClaw - all-in-one solution!
"""

import asyncio
import asyncpg
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# Configuration
THINK_CHECK_INTERVAL = 900  # 15 minutes
SLEEP_CHECK_INTERVAL = 1800  # 30 minutes
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres@localhost:5432/supabrain")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
THINK_QUEUE_FILE = Path.home() / ".openclaw/workspace/think_queue.json"


class SupaBrainWorker:
    """Background worker for proactive cognition"""
    
    def __init__(self):
        self.db_pool = None
        self.anthropic = None
        self.running = False
        
    async def initialize(self):
        """Initialize connections"""
        print("🧠 SupaBrain Worker starting...")
        
        # Database pool
        self.db_pool = await asyncpg.create_pool(
            DB_URL,
            min_size=2,
            max_size=5
        )
        print("✅ Database connected")
        
        # Anthropic client (if API key available)
        if ANTHROPIC_API_KEY:
            self.anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
            print("✅ Anthropic API configured")
        else:
            print("⚠️  Anthropic API key not set - LLM features disabled")
        
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
    
    async def process_think_cycle(self):
        """Process pending thoughts with LLM"""
        if not self.anthropic:
            return  # Skip if no API key
        
        queue = self.load_think_queue()
        pending = [t for t in queue if t['status'] == 'pending']
        
        if not pending:
            return
        
        # Sort by priority
        priority_order = {'urgent': 4, 'high': 3, 'medium': 2, 'low': 1}
        pending.sort(key=lambda t: priority_order.get(t['priority'], 0), reverse=True)
        
        # Process top 3
        for thought in pending[:3]:
            print(f"\n💭 Thinking about: {thought['topic']}")
            
            try:
                # Mark in progress
                thought['status'] = 'in_progress'
                self.save_think_queue(queue)
                
                # Invoke LLM
                prompt = f"""You are thinking proactively about: {thought['topic']}

Context: {thought['context']}

Task: Reflect, research (if you have web access), and develop insights. Write your thoughts and any actionable conclusions.

Focus on:
- What do I need to learn?
- What decisions should I make?
- What actions should I take?
- What new questions emerge?

Be concise but thorough. Write like you're making notes for yourself."""

                response = self.anthropic.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                insights = response.content[0].text
                
                # Store as memory
                async with self.db_pool.acquire() as conn:
                    # Generate embedding (simplified - would use sentence-transformers in production)
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
        if not self.anthropic:
            return  # Skip if no API key
        
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
                # Run sleep cycle (import from sleep_cycle.py would be better)
                # For now, just log
                print("   (Sleep cycle execution - TODO: integrate sleep_cycle.py)")
            
    # ===== MAIN LOOP =====
    
    async def run(self):
        """Main worker loop"""
        await self.initialize()
        
        last_think = 0
        last_sleep = 0
        
        print("\n🚀 Worker running...")
        print(f"   Think cycle: every {THINK_CHECK_INTERVAL}s")
        print(f"   Sleep cycle: every {SLEEP_CHECK_INTERVAL}s")
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
