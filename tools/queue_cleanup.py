#!/usr/bin/env python3
"""
Queue Cleanup Tool

Clean up unwanted memories from offline queue.
Useful after benchmarks or testing.

Usage:
    python tools/queue_cleanup.py --tag benchmark  # Remove benchmark memories
    python tools/queue_cleanup.py --dry-run --tag test  # Preview only
"""

import sys
import os
import argparse
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

from supabrain_queue import MemoryQueue

def cleanup_by_tag(tag, dry_run=False):
    """Remove memories with specific tag"""
    queue = MemoryQueue()
    memories = queue.read_all()
    
    if not memories:
        print("✅ Queue is empty")
        return 0
    
    # Find memories to remove
    to_remove = []
    to_keep = []
    
    for mem in memories:
        tags = mem.get("tags", [])
        if tag in tags:
            to_remove.append(mem)
        else:
            to_keep.append(mem)
    
    print(f"📊 Found {len(memories)} total memories")
    print(f"🗑️  {len(to_remove)} memories match tag '{tag}'")
    print(f"✅ {len(to_keep)} memories will be kept")
    print()
    
    if dry_run:
        print("🔍 DRY RUN - showing first 10 memories to remove:")
        for i, mem in enumerate(to_remove[:10], 1):
            print(f"   {i}. [{mem.get('domain', '?')}] {mem['content'][:60]}...")
        if len(to_remove) > 10:
            print(f"   ... and {len(to_remove) - 10} more")
        print()
        print("💡 Run without --dry-run to actually remove")
        return 0
    
    if to_remove:
        # Rewrite queue with only kept memories
        import json
        import shutil
        
        # Backup first
        backup_file = f"{queue.queue_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(queue.queue_file, backup_file)
        print(f"💾 Backup created: {backup_file}")
        
        # Write kept memories
        with open(queue.queue_file, 'w') as f:
            for mem in to_keep:
                f.write(json.dumps(mem) + '\n')
        
        print(f"✅ Removed {len(to_remove)} memories")
        print(f"✅ Kept {len(to_keep)} memories")
        print(f"✅ New queue size: {len(to_keep)}")
    else:
        print("✅ No memories to remove")
    
    return len(to_remove)

def cleanup_old(days, dry_run=False):
    """Remove memories older than N days"""
    import json
    from datetime import timedelta
    
    queue = MemoryQueue()
    memories = queue.read_all()
    
    if not memories:
        print("✅ Queue is empty")
        return 0
    
    now = datetime.now()
    cutoff = now - timedelta(days=days)
    
    to_remove = []
    to_keep = []
    
    for mem in memories:
        timestamp_str = mem.get("timestamp")
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str)
            if timestamp < cutoff:
                to_remove.append(mem)
            else:
                to_keep.append(mem)
        else:
            to_keep.append(mem)  # Keep if no timestamp
    
    print(f"📊 Found {len(memories)} total memories")
    print(f"🗑️  {len(to_remove)} memories older than {days} days")
    print(f"✅ {len(to_keep)} memories will be kept")
    print()
    
    if dry_run:
        print("🔍 DRY RUN - showing oldest 10 memories:")
        sorted_remove = sorted(to_remove, key=lambda m: m.get("timestamp", ""))
        for i, mem in enumerate(sorted_remove[:10], 1):
            ts = mem.get("timestamp", "unknown")
            print(f"   {i}. {ts} [{mem.get('domain', '?')}] {mem['content'][:50]}...")
        if len(to_remove) > 10:
            print(f"   ... and {len(to_remove) - 10} more")
        print()
        print("💡 Run without --dry-run to actually remove")
        return 0
    
    if to_remove:
        # Rewrite queue
        import shutil
        
        backup_file = f"{queue.queue_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(queue.queue_file, backup_file)
        print(f"💾 Backup created: {backup_file}")
        
        with open(queue.queue_file, 'w') as f:
            for mem in to_keep:
                f.write(json.dumps(mem) + '\n')
        
        print(f"✅ Removed {len(to_remove)} memories")
        print(f"✅ Kept {len(to_keep)} memories")
    else:
        print("✅ No memories to remove")
    
    return len(to_remove)

def main():
    parser = argparse.ArgumentParser(
        description="Clean up offline queue",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Remove benchmark memories (dry-run first)
  python tools/queue_cleanup.py --tag benchmark --dry-run
  python tools/queue_cleanup.py --tag benchmark
  
  # Remove old memories
  python tools/queue_cleanup.py --older-than 7 --dry-run
  python tools/queue_cleanup.py --older-than 7
        """
    )
    
    parser.add_argument("--tag", help="Remove memories with this tag")
    parser.add_argument("--older-than", type=int, metavar="DAYS",
                        help="Remove memories older than N days")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview what would be removed")
    
    args = parser.parse_args()
    
    if not args.tag and not args.older_than:
        parser.error("Must specify --tag or --older-than")
    
    if args.tag:
        removed = cleanup_by_tag(args.tag, dry_run=args.dry_run)
    elif args.older_than:
        removed = cleanup_old(args.older_than, dry_run=args.dry_run)
    
    if removed > 0 and not args.dry_run:
        print()
        print("💡 Run stats dashboard to see new queue state:")
        print("   python tools/stats_dashboard.py")

if __name__ == "__main__":
    main()
