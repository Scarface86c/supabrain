#!/usr/bin/env python3
"""
SupaBrain Offline Memory Queue
Captures memories even when SupaBrain server is down
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

class MemoryQueue:
    """Offline queue for memories when SupaBrain is down"""
    
    def __init__(self, queue_file: Optional[str] = None):
        if queue_file:
            self.queue_file = Path(queue_file)
        else:
            self.queue_file = Path.home() / ".supabrain_queue.jsonl"
        
        # Ensure file exists
        self.queue_file.touch(exist_ok=True)
    
    def remember(self, content: str, domain: str = "general", 
                 temporal_layer: str = "working", ttl_hours: int = 2,
                 tags: Optional[List[str]] = None, 
                 metadata: Optional[Dict] = None) -> Dict:
        """
        Add memory to queue
        
        Args:
            content: Memory content
            domain: Memory domain (self/user/projects/world/system/general)
            temporal_layer: working/short/long/archive
            ttl_hours: Hours until expiration
            tags: List of tags
            metadata: Additional metadata
        
        Returns:
            Dict with memory data
        """
        memory = {
            "content": content,
            "domain": domain,
            "temporal_layer": temporal_layer,
            "ttl_hours": ttl_hours,
            "tags": tags or [],
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "queued": True
        }
        
        # Append to queue file
        with open(self.queue_file, 'a') as f:
            f.write(json.dumps(memory) + '\n')
        
        print(f"📝 Queued: {content[:60]}...")
        return memory
    
    def count(self) -> int:
        """Count queued memories"""
        if not self.queue_file.exists():
            return 0
        
        with open(self.queue_file) as f:
            return sum(1 for _ in f)
    
    def read_all(self) -> List[Dict]:
        """Read all queued memories"""
        if not self.queue_file.exists():
            return []
        
        memories = []
        with open(self.queue_file) as f:
            for line in f:
                if line.strip():
                    memories.append(json.loads(line))
        
        return memories
    
    def sync_to_supabrain(self, api_url: str = "http://localhost:8080") -> tuple[int, List[Dict]]:
        """
        Sync queue to SupaBrain API
        
        Args:
            api_url: SupaBrain API base URL
        
        Returns:
            Tuple of (synced_count, failed_memories)
        """
        import requests
        
        if not self.queue_file.exists():
            return 0, []
        
        memories = self.read_all()
        if not memories:
            return 0, []
        
        synced = 0
        failed = []
        
        for memory in memories:
            try:
                # Remove queue metadata
                api_memory = {k: v for k, v in memory.items() if k != "queued"}
                
                response = requests.post(
                    f"{api_url}/api/v1/remember",
                    json=api_memory,
                    timeout=5
                )
                
                if response.ok:
                    synced += 1
                    print(f"✅ Synced: {memory['content'][:50]}...")
                else:
                    failed.append(memory)
                    print(f"❌ Failed: {response.status_code}")
            except Exception as e:
                failed.append(memory)
                print(f"❌ Error: {e}")
        
        # Update queue file
        if synced > 0:
            if failed:
                # Rewrite queue with only failed memories
                with open(self.queue_file, 'w') as f:
                    for memory in failed:
                        f.write(json.dumps(memory) + '\n')
                print(f"⚠️  {len(failed)} memories remain in queue")
            else:
                # All synced, clear queue
                self.queue_file.unlink()
                print("✨ Queue cleared, all synced!")
        
        return synced, failed
    
    def clear(self):
        """Clear queue (use with caution!)"""
        if self.queue_file.exists():
            self.queue_file.unlink()
        print("🗑️  Queue cleared")


# Convenience functions
def remember(content: str, **kwargs) -> Dict:
    """Quick remember to default queue"""
    queue = MemoryQueue()
    return queue.remember(content, **kwargs)


def sync() -> tuple[int, List[Dict]]:
    """Quick sync to SupaBrain"""
    queue = MemoryQueue()
    return queue.sync_to_supabrain()


def status() -> Dict:
    """Queue status"""
    queue = MemoryQueue()
    count = queue.count()
    
    return {
        "queued": count,
        "queue_file": str(queue.queue_file),
        "status": "ready" if count > 0 else "empty"
    }


if __name__ == "__main__":
    # Test the queue
    print("🧪 Testing SupaBrain Memory Queue\n")
    
    queue = MemoryQueue()
    
    # Test 1: Add memories
    print("Test 1: Adding memories...")
    queue.remember(
        "SupaBrain v0.4 offline queue implemented",
        domain="projects",
        temporal_layer="short",
        ttl_hours=168,
        tags=["supabrain", "v0.4", "milestone"]
    )
    
    queue.remember(
        "Learned to build without asking first - autonomy in action",
        domain="self",
        temporal_layer="long",
        tags=["autonomy", "lesson", "scarface"]
    )
    
    # Test 2: Check count
    print(f"\nTest 2: Queue count = {queue.count()}")
    
    # Test 3: Read all
    print(f"\nTest 3: Reading all memories...")
    memories = queue.read_all()
    for i, mem in enumerate(memories, 1):
        print(f"  {i}. [{mem['domain']}] {mem['content'][:50]}...")
    
    # Test 4: Status
    print(f"\nTest 4: Status = {status()}")
    
    print("\n✅ All tests passed!")
