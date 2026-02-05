#!/usr/bin/env python3
"""
SupaBrain Sleep Cycle - LLM-driven Memory Consolidation

Consolidates expired working memories like REM sleep in humans.
Reviews memories and decides: promote/extend/archive/forget.

Usage:
    python sleep_cycle.py --dry-run  # Preview without changes
    python sleep_cycle.py             # Run consolidation
"""

import anthropic
import json
import argparse
from datetime import datetime
from typing import List, Dict, Tuple
import requests

# Configuration
SUPABRAIN_API = "http://localhost:8080/api/v1"
DEFAULT_MODEL = "claude-3-5-haiku-20241022"  # Cheap model for consolidation

class SleepCycle:
    def __init__(self, api_url: str = SUPABRAIN_API, model: str = DEFAULT_MODEL):
        self.api_url = api_url
        self.model = model
        self.client = anthropic.Anthropic()
        
    def get_expired_memories(self) -> List[Dict]:
        """Get memories that need review from SupaBrain API"""
        try:
            response = requests.get(
                f"{self.api_url}/review/pending",
                timeout=5
            )
            if response.ok:
                data = response.json()
                return data.get("memories", [])
            else:
                print(f"❌ API error: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error fetching memories: {e}")
            return []
    
    def format_batch(self, memories: List[Dict]) -> str:
        """Format memory batch for LLM review"""
        formatted = []
        for i, mem in enumerate(memories, 1):
            formatted.append(f"{i}. [{mem.get('domain', 'unknown')}] {mem['content'][:100]}...")
        return "\n".join(formatted)
    
    def consolidate_batch(self, memories: List[Dict]) -> List[Dict]:
        """
        Use LLM to review a batch of memories
        
        Returns list of decisions: [{"id": 1, "decision": "important", "reason": "..."}]
        """
        if not memories:
            return []
        
        prompt = f"""You are reviewing {len(memories)} memories from working memory (expired TTL).

For each memory, decide:
- **IMPORTANT**: Promote to long-term (key learnings, decisions, insights needed for future)
- **CONTEXT**: Extend to short-term (ongoing projects, might need soon, review in 7 days)
- **ARCHIVE**: Move to archive (completed tasks, historical records worth keeping)
- **FORGET**: Delete (trivial actions, noise, redundant information)

Consider:
- Is this information needed for future decisions?
- Does it represent growth/learning?
- Is it unique or redundant?
- Does it have lasting value?

Memories to review:
{self.format_batch(memories)}

Return ONLY a JSON array (no other text):
[
  {{"id": 1, "decision": "important", "reason": "Key learning about content strategy"}},
  {{"id": 2, "decision": "forget", "reason": "Routine command execution"}},
  ...
]

Decisions must be: important, context, archive, or forget.
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse response
            content = response.content[0].text.strip()
            
            # Extract JSON (handle markdown code blocks)
            if content.startswith("```"):
                # Remove markdown wrapper
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            decisions = json.loads(content)
            return decisions
            
        except Exception as e:
            print(f"❌ LLM error: {e}")
            return []
    
    def apply_decisions(self, memories: List[Dict], decisions: List[Dict], dry_run: bool = False) -> Dict:
        """
        Apply consolidation decisions
        
        Returns stats: {promoted, extended, archived, forgotten}
        """
        stats = {
            "promoted": 0,
            "extended": 0,
            "archived": 0,
            "forgotten": 0
        }
        
        for memory, decision_data in zip(memories, decisions):
            decision = decision_data.get("decision")
            reason = decision_data.get("reason", "")
            memory_id = memory.get("id")
            
            if dry_run:
                print(f"[DRY RUN] Memory {memory_id}: {decision} - {reason}")
                stats[f"{decision}d" if decision != "forget" else "forgotten"] += 1
                continue
            
            try:
                # Call SupaBrain API to apply decision
                response = requests.post(
                    f"{self.api_url}/review/decide",
                    json={
                        "memory_id": memory_id,
                        "decision": decision,
                        "reason": reason
                    },
                    timeout=5
                )
                
                if response.ok:
                    if decision == "important":
                        stats["promoted"] += 1
                        print(f"✅ Promoted: {memory['content'][:50]}...")
                    elif decision == "context":
                        stats["extended"] += 1
                        print(f"⏳ Extended: {memory['content'][:50]}...")
                    elif decision == "archive":
                        stats["archived"] += 1
                        print(f"📦 Archived: {memory['content'][:50]}...")
                    else:  # forget
                        stats["forgotten"] += 1
                        print(f"🗑️  Forgot: {memory['content'][:50]}...")
                else:
                    print(f"❌ Failed to apply decision for memory {memory_id}")
                    
            except Exception as e:
                print(f"❌ Error applying decision: {e}")
        
        return stats
    
    def run(self, batch_size: int = 20, dry_run: bool = False) -> Dict:
        """
        Run full sleep cycle
        
        Args:
            batch_size: Number of memories to process per LLM call
            dry_run: If True, preview decisions without applying
        
        Returns:
            Dict with consolidation statistics
        """
        print(f"💤 Starting sleep cycle at {datetime.now().strftime('%H:%M:%S')}")
        if dry_run:
            print("🔍 DRY RUN MODE (no changes will be made)")
        
        # Get expired memories
        print("📦 Fetching expired memories...")
        memories = self.get_expired_memories()
        
        if not memories:
            print("✅ No memories to review!")
            return {"total": 0}
        
        print(f"📊 Found {len(memories)} memories to review\n")
        
        # Process in batches
        total_stats = {
            "promoted": 0,
            "extended": 0,
            "archived": 0,
            "forgotten": 0
        }
        
        for i in range(0, len(memories), batch_size):
            batch = memories[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(memories) + batch_size - 1) // batch_size
            
            print(f"🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} memories)...")
            
            # Get LLM decisions
            decisions = self.consolidate_batch(batch)
            
            if not decisions:
                print("⚠️  No decisions from LLM, skipping batch")
                continue
            
            # Apply decisions
            batch_stats = self.apply_decisions(batch, decisions, dry_run=dry_run)
            
            # Aggregate stats
            for key in total_stats:
                total_stats[key] += batch_stats[key]
            
            print()  # Blank line between batches
        
        # Summary
        print("="*60)
        print("✨ Sleep Cycle Complete!")
        print("="*60)
        print(f"Total processed: {len(memories)}")
        print(f"✅ Promoted (long-term): {total_stats['promoted']}")
        print(f"⏳ Extended (short-term): {total_stats['extended']}")
        print(f"📦 Archived: {total_stats['archived']}")
        print(f"🗑️  Forgotten: {total_stats['forgotten']}")
        print("="*60)
        
        if dry_run:
            print("\n💡 This was a dry run. Run without --dry-run to apply changes.")
        
        total_stats["total"] = len(memories)
        return total_stats


def main():
    parser = argparse.ArgumentParser(
        description="SupaBrain Sleep Cycle - Consolidate memories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (preview decisions)
  python sleep_cycle.py --dry-run
  
  # Run consolidation
  python sleep_cycle.py
  
  # Use different model
  python sleep_cycle.py --model claude-3-5-sonnet-20241022
  
  # Custom batch size
  python sleep_cycle.py --batch-size 10
        """
    )
    
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview decisions without applying")
    parser.add_argument("--batch-size", type=int, default=20,
                        help="Memories per LLM call (default: 20)")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"LLM model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--api-url", default=SUPABRAIN_API,
                        help="SupaBrain API URL")
    
    args = parser.parse_args()
    
    # Run sleep cycle
    cycle = SleepCycle(api_url=args.api_url, model=args.model)
    stats = cycle.run(batch_size=args.batch_size, dry_run=args.dry_run)
    
    # Exit code based on results
    if stats.get("total", 0) == 0:
        exit(0)  # Nothing to do
    elif stats.get("promoted", 0) + stats.get("extended", 0) > 0:
        exit(0)  # Success
    else:
        exit(1)  # All forgotten (might be unusual)


if __name__ == "__main__":
    main()
