#!/usr/bin/env python3
"""
SupaBrain Stats Dashboard

Simple CLI dashboard showing memory statistics.
Useful for monitoring and debugging.

Usage:
    python tools/stats_dashboard.py          # One-time view
    python tools/stats_dashboard.py --watch  # Live updates
"""

import sys
import os
import time
import argparse
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
sys.path.append(os.path.expanduser('~/.openclaw/workspace'))

from supabrain_queue import MemoryQueue

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_queue_stats():
    """Get offline queue statistics"""
    queue = MemoryQueue()
    memories = queue.read_all()
    
    if not memories:
        return {
            "total": 0,
            "by_domain": {},
            "by_layer": {},
            "by_type": {}
        }
    
    # Count by domain
    by_domain = {}
    by_layer = {}
    by_type = {}
    
    for mem in memories:
        # Domain
        domain = mem.get("domain", "unknown")
        by_domain[domain] = by_domain.get(domain, 0) + 1
        
        # Layer
        layer = mem.get("temporal_layer", "unknown")
        by_layer[layer] = by_layer.get(layer, 0) + 1
        
        # Type (from tags)
        tags = mem.get("tags", [])
        for tag in tags:
            if tag != "auto-captured":
                by_type[tag] = by_type.get(tag, 0) + 1
    
    return {
        "total": len(memories),
        "by_domain": by_domain,
        "by_layer": by_layer,
        "by_type": by_type
    }

def format_bar(count, max_count, width=20):
    """Format a simple bar chart"""
    if max_count == 0:
        return "█" * 0
    filled = int((count / max_count) * width)
    return "█" * filled + "░" * (width - filled)

def display_stats(stats):
    """Display statistics in a nice format"""
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "🧠 SupaBrain Stats Dashboard" + " " * 15 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    # Timestamp
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Total
    print("┌─ Total Queued Memories ──────────────────────────────────┐")
    print(f"│  {stats['total']:>5} memories waiting for consolidation")
    print("└───────────────────────────────────────────────────────────┘")
    print()
    
    # By domain
    if stats["by_domain"]:
        print("┌─ By Domain ───────────────────────────────────────────────┐")
        max_count = max(stats["by_domain"].values())
        for domain, count in sorted(stats["by_domain"].items(), key=lambda x: -x[1]):
            bar = format_bar(count, max_count, 25)
            print(f"│  {domain:12s} {count:>4} {bar}")
        print("└───────────────────────────────────────────────────────────┘")
        print()
    
    # By layer
    if stats["by_layer"]:
        print("┌─ By Temporal Layer ───────────────────────────────────────┐")
        max_count = max(stats["by_layer"].values())
        for layer, count in sorted(stats["by_layer"].items(), key=lambda x: -x[1]):
            bar = format_bar(count, max_count, 25)
            print(f"│  {layer:12s} {count:>4} {bar}")
        print("└───────────────────────────────────────────────────────────┘")
        print()
    
    # By type (top 10)
    if stats["by_type"]:
        print("┌─ By Event Type (Top 10) ──────────────────────────────────┐")
        sorted_types = sorted(stats["by_type"].items(), key=lambda x: -x[1])[:10]
        max_count = max(count for _, count in sorted_types)
        for event_type, count in sorted_types:
            bar = format_bar(count, max_count, 25)
            print(f"│  {event_type:12s} {count:>4} {bar}")
        print("└───────────────────────────────────────────────────────────┘")
        print()
    
    # Status message
    if stats["total"] == 0:
        print("✅ No memories in queue (all consolidated or server down)")
    elif stats["total"] < 50:
        print("✅ Queue healthy (< 50 memories)")
    elif stats["total"] < 200:
        print("⚠️  Queue growing (50-200 memories) - consider running sleep cycle")
    else:
        print("🚨 Queue high (> 200 memories) - run sleep cycle soon!")
    
    print()

def watch_mode(interval=5):
    """Watch mode - refresh every interval seconds"""
    print("👁️  Watch mode active (Ctrl+C to stop)")
    print(f"Refreshing every {interval} seconds...")
    print()
    time.sleep(2)
    
    try:
        while True:
            clear_screen()
            stats = get_queue_stats()
            display_stats(stats)
            print(f"⏱️  Next refresh in {interval}s (Ctrl+C to stop)")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n👋 Stopped watching")

def main():
    parser = argparse.ArgumentParser(
        description="SupaBrain stats dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View current stats
  python tools/stats_dashboard.py
  
  # Watch mode (refresh every 5s)
  python tools/stats_dashboard.py --watch
  
  # Custom refresh interval
  python tools/stats_dashboard.py --watch --interval 10
        """
    )
    
    parser.add_argument("--watch", action="store_true",
                        help="Watch mode (live updates)")
    parser.add_argument("--interval", type=int, default=5,
                        help="Refresh interval in seconds (default: 5)")
    
    args = parser.parse_args()
    
    if args.watch:
        watch_mode(args.interval)
    else:
        stats = get_queue_stats()
        display_stats(stats)

if __name__ == "__main__":
    main()

"""
What this dashboard shows:
- Total queued memories
- Breakdown by domain (self/user/projects/etc)
- Breakdown by temporal layer (working/short/long)
- Top 10 event types
- Health status (queue size warnings)

Use cases:
- Quick health check
- Debugging memory capture
- Monitoring queue growth
- Understanding memory distribution
- Deciding when to run sleep cycle

Integration:
Add to your monitoring scripts or run periodically to track system health.
"""
