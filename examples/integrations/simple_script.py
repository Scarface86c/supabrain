#!/usr/bin/env python3
"""
Simple Script Integration Example

Shows how to add SupaBrain memory to any Python script.
The script analyzes data and captures learnings automatically.
"""

import sys
import os

# Add SupaBrain to path
sys.path.append(os.path.expanduser('~/supabrain/core'))

from auto_capture import (
    capture_learning,
    capture_decision,
    capture_milestone,
    capture_error,
    capture_analysis
)

def analyze_data(data):
    """Analyze some data and capture insights"""
    print("📊 Analyzing data...")
    
    # Do analysis
    avg = sum(data) / len(data)
    max_val = max(data)
    min_val = min(data)
    
    # Capture the analysis result
    capture_analysis(
        f"Analyzed {len(data)} data points: avg={avg:.2f}, max={max_val}, min={min_val}",
        tags=["data-analysis"]
    )
    
    # If we learned something interesting
    if max_val > avg * 2:
        capture_learning(
            "Discovered outlier pattern: max value significantly higher than average",
            tags=["outliers", "pattern"]
        )
    
    return {"avg": avg, "max": max_val, "min": min_val}

def make_decision(results):
    """Make a decision based on results"""
    print("🤔 Making decision...")
    
    if results["max"] > 100:
        decision = "Scale up infrastructure"
        reasoning = "Max value exceeds threshold"
    else:
        decision = "Keep current setup"
        reasoning = "Values within normal range"
    
    # Capture the decision
    capture_decision(
        f"Decision: {decision}. Reasoning: {reasoning}",
        context={"results": results},
        tags=["infrastructure", "decision"]
    )
    
    return decision

def main():
    """Main script workflow"""
    
    # Mark start
    capture_milestone("Starting data analysis script", tags=["script-start"])
    
    try:
        # Get data (simulated)
        data = [10, 25, 30, 15, 120, 22, 18]  # Note: 120 is an outlier
        
        # Analyze
        results = analyze_data(data)
        print(f"Results: {results}")
        
        # Make decision
        decision = make_decision(results)
        print(f"Decision: {decision}")
        
        # Mark completion
        capture_milestone(
            "Data analysis script completed successfully",
            tags=["script-complete", "success"]
        )
        
        print("\n✅ Script complete!")
        print("💡 Memories captured to working memory (will be consolidated during sleep cycle)")
        
    except Exception as e:
        # Capture errors
        capture_error(
            f"Script failed: {str(e)}",
            context={"error_type": type(e).__name__},
            tags=["script-error"]
        )
        raise

if __name__ == "__main__":
    main()

"""
What this example shows:
1. How to import auto_capture functions
2. When to capture different event types:
   - capture_analysis() for analysis results
   - capture_learning() for insights discovered
   - capture_decision() for choices made
   - capture_milestone() for start/end markers
   - capture_error() for failures

3. All memories go to working memory (TTL 1-4h)
4. Sleep cycle will review them later
5. Important ones get promoted to long-term

Run this script:
    python simple_script.py

Then check your memory queue:
    python -c "from supabrain_queue import MemoryQueue; print(MemoryQueue().count())"

Run sleep cycle:
    python ~/supabrain/core/sleep_cycle.py --dry-run  # Preview
    python ~/supabrain/core/sleep_cycle.py             # Actually consolidate
"""
