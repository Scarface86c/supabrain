#!/usr/bin/env python3
"""
Heartbeat Integration Example

Shows how to integrate SupaBrain with periodic tasks (cron, heartbeat).
Captures routine checks and triggers sleep cycle automatically.
"""

import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.expanduser('~/supabrain/core'))
sys.path.append(os.path.expanduser('~/.openclaw/workspace'))

from auto_capture import capture_learning, capture_milestone, capture_analysis
from heartbeat_sleep import should_run_sleep_cycle, run_sleep_cycle, update_activity

def check_system_health():
    """Check system health and capture findings"""
    print("🏥 Checking system health...")
    
    # Simulate checks
    disk_usage = 45  # percent
    memory_usage = 60  # percent
    cpu_load = 2.5
    
    # Capture analysis
    capture_analysis(
        f"System health: disk={disk_usage}%, memory={memory_usage}%, cpu_load={cpu_load}",
        tags=["health-check", "monitoring"]
    )
    
    # If something interesting
    if disk_usage > 80:
        capture_learning(
            "Disk usage high - might need cleanup soon",
            tags=["system", "warning"]
        )
    
    return {
        "disk": disk_usage,
        "memory": memory_usage,
        "cpu": cpu_load,
        "status": "healthy" if disk_usage < 80 else "warning"
    }

def check_project_status():
    """Check project status"""
    print("📊 Checking project status...")
    
    # Simulate project check
    projects = {
        "supabrain": {"status": "active", "version": "0.4.0-alpha"},
        "other_project": {"status": "idle", "version": "1.2.0"}
    }
    
    for proj, info in projects.items():
        if info["status"] == "active":
            capture_analysis(
                f"Project {proj} active at version {info['version']}",
                tags=["projects", proj]
            )
    
    return projects

def heartbeat_cycle():
    """
    Main heartbeat cycle - runs every 15 minutes
    
    This is what you'd put in cron or HEARTBEAT.md
    """
    print(f"\n💓 Heartbeat at {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)
    
    # 1. Update activity (important for idle detection)
    update_activity()
    print("✅ Activity updated")
    
    # 2. Run periodic checks
    health = check_system_health()
    print(f"   System: {health['status']}")
    
    projects = check_project_status()
    print(f"   Projects: {len(projects)} tracked")
    
    # 3. Check if sleep cycle needed
    print("\n🌙 Checking if sleep cycle needed...")
    should_run, reason = should_run_sleep_cycle()
    
    if should_run:
        print(f"   → {reason}")
        print("   Running sleep cycle...")
        
        success = run_sleep_cycle()
        
        if success:
            print("   ✅ Sleep cycle completed")
            capture_milestone(
                "Sleep cycle completed via heartbeat",
                tags=["sleep-cycle", "automated"]
            )
        else:
            print("   ❌ Sleep cycle failed")
    else:
        print(f"   → {reason}")
        print("   ⏸️  Not needed")
    
    print("="*60)
    print("✅ Heartbeat complete\n")

def continuous_heartbeat(interval_seconds=900):  # 15 minutes
    """
    Run heartbeats continuously (for testing)
    
    In production, use cron instead:
        */15 * * * * python heartbeat_example.py
    """
    print(f"🚀 Starting continuous heartbeat (every {interval_seconds}s)")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            heartbeat_cycle()
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\n\n👋 Stopping heartbeat")
        capture_milestone("Heartbeat stopped (manual)", tags=["heartbeat"])

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Heartbeat integration example")
    parser.add_argument("--continuous", action="store_true",
                        help="Run continuously (for testing)")
    parser.add_argument("--interval", type=int, default=900,
                        help="Interval in seconds (default: 900 = 15min)")
    
    args = parser.parse_args()
    
    if args.continuous:
        continuous_heartbeat(args.interval)
    else:
        # Single heartbeat (cron mode)
        heartbeat_cycle()

"""
Usage:

1. Single heartbeat (for cron):
   python heartbeat_example.py

2. Continuous testing:
   python heartbeat_example.py --continuous --interval 60  # Every minute

3. In cron:
   */15 * * * * cd ~/supabrain && python examples/integrations/heartbeat_example.py

4. In OpenClaw HEARTBEAT.md:
   ## Every Heartbeat (~15 min)
   - Run: python ~/supabrain/examples/integrations/heartbeat_example.py

What it does:
- Tracks activity (for idle detection)
- Runs health/status checks
- Captures findings to memory
- Automatically triggers sleep cycle when needed
- Marks completion milestones

Benefits:
- Never miss important events
- Automatic consolidation
- No manual intervention needed
- Cost-optimized (only runs when needed)
"""
