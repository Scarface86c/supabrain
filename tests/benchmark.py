#!/usr/bin/env python3
"""
SupaBrain Performance Benchmark

Tests performance of key operations:
- Memory capture (auto-capture)
- Queue operations (offline queue)
- Sleep cycle (consolidation)
- Memory retrieval

Run with: python tests/benchmark.py
"""

import sys
import os
import time
from statistics import mean, stdev

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
sys.path.append(os.path.expanduser('~/.openclaw/workspace'))

from auto_capture import auto_capture, CaptureType
from supabrain_queue import MemoryQueue

def benchmark_function(func, iterations=100, warmup=10):
    """
    Benchmark a function
    
    Returns: (mean_ms, stdev_ms, min_ms, max_ms)
    """
    # Warmup
    for _ in range(warmup):
        func()
    
    # Actual benchmark
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms
    
    return {
        "mean": mean(times),
        "stdev": stdev(times) if len(times) > 1 else 0,
        "min": min(times),
        "max": max(times),
        "iterations": iterations
    }

def test_auto_capture():
    """Test auto-capture performance"""
    auto_capture(
        CaptureType.LEARNING,
        "Test learning capture for benchmark",
        tags=["benchmark"]
    )

def test_queue_write():
    """Test queue write performance"""
    queue = MemoryQueue("/tmp/benchmark_queue.jsonl")
    queue.remember(
        "Benchmark memory",
        domain="system",
        temporal_layer="working",
        ttl_hours=1,
        tags=["benchmark"]
    )

def test_queue_read():
    """Test queue read performance"""
    queue = MemoryQueue("/tmp/benchmark_queue.jsonl")
    memories = queue.read_all()
    return len(memories)

def run_benchmarks():
    """Run all benchmarks"""
    print("🏎️  SupaBrain Performance Benchmark")
    print("="*60)
    
    # Setup
    os.makedirs("tests", exist_ok=True)
    
    # 1. Auto-capture
    print("\n1. Auto-Capture Performance")
    print("-" * 60)
    results = benchmark_function(test_auto_capture, iterations=100)
    print(f"   Mean:   {results['mean']:.3f} ms")
    print(f"   StDev:  {results['stdev']:.3f} ms")
    print(f"   Min:    {results['min']:.3f} ms")
    print(f"   Max:    {results['max']:.3f} ms")
    print(f"   → {1000 / results['mean']:.0f} captures/second")
    
    # 2. Queue write
    print("\n2. Queue Write Performance")
    print("-" * 60)
    results = benchmark_function(test_queue_write, iterations=100)
    print(f"   Mean:   {results['mean']:.3f} ms")
    print(f"   StDev:  {results['stdev']:.3f} ms")
    print(f"   Min:    {results['min']:.3f} ms")
    print(f"   Max:    {results['max']:.3f} ms")
    print(f"   → {1000 / results['mean']:.0f} writes/second")
    
    # 3. Queue read
    print("\n3. Queue Read Performance")
    print("-" * 60)
    results = benchmark_function(test_queue_read, iterations=100)
    print(f"   Mean:   {results['mean']:.3f} ms")
    print(f"   StDev:  {results['stdev']:.3f} ms")
    print(f"   Min:    {results['min']:.3f} ms")
    print(f"   Max:    {results['max']:.3f} ms")
    print(f"   → {1000 / results['mean']:.0f} reads/second")
    
    # Cleanup
    if os.path.exists("/tmp/benchmark_queue.jsonl"):
        os.remove("/tmp/benchmark_queue.jsonl")
    
    print("\n" + "="*60)
    print("✅ Benchmark complete!")
    print("\nInterpretation:")
    print("- Auto-capture: <1ms is excellent, <10ms is good")
    print("- Queue ops: <5ms is excellent, <20ms is good")
    print("- Higher = slower (need optimization)")

def load_test():
    """Test with high load"""
    print("\n\n🔥 Load Test: 1000 captures")
    print("="*60)
    
    queue = MemoryQueue("/tmp/load_test_queue.jsonl")
    
    start = time.time()
    for i in range(1000):
        queue.remember(
            f"Load test memory {i}",
            domain="system",
            temporal_layer="working",
            ttl_hours=1,
            tags=["load-test"]
        )
    end = time.time()
    
    elapsed = end - start
    rate = 1000 / elapsed
    
    print(f"Time:     {elapsed:.2f} seconds")
    print(f"Rate:     {rate:.0f} captures/second")
    print(f"Avg:      {elapsed/1000*1000:.2f} ms per capture")
    
    # Cleanup
    if os.path.exists("/tmp/load_test_queue.jsonl"):
        os.remove("/tmp/load_test_queue.jsonl")
    
    print("="*60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SupaBrain performance benchmark")
    parser.add_argument("--load-test", action="store_true",
                        help="Run load test (1000 captures)")
    
    args = parser.parse_args()
    
    run_benchmarks()
    
    if args.load_test:
        load_test()
    
    print("\n💡 Tip: Run with --load-test to test high-volume scenarios")

"""
Expected Performance (on typical hardware):

Auto-capture: ~0.5-2ms per capture
  - Excellent: Fast enough for real-time capture
  - Can capture 500-2000 events/second

Queue operations: ~1-5ms
  - Excellent: File I/O is fast
  - Bottleneck would be disk, not code

Interpretation:
- <1ms: Excellent (no optimization needed)
- 1-10ms: Good (acceptable for most use cases)
- 10-50ms: Okay (might want to optimize)
- >50ms: Slow (needs optimization)

Optimization opportunities:
1. Batch queue writes (write multiple at once)
2. Use in-memory buffer before file write
3. Compress queue file
4. Use binary format instead of JSON
"""
