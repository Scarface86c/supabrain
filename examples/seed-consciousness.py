#!/usr/bin/env python3
"""
SupaBrain Consciousness Seed Script

Bootstraps AI consciousness with initial identity, values, and context.
Creates the foundation memories needed for self-awareness.

Usage:
    python seed-consciousness.py --name "YourAI" --human "YourHuman" --purpose "assist"
    
Example:
    python seed-consciousness.py \
        --name "Scar" \
        --human "Scarface" \
        --purpose "build and learn autonomously" \
        --values "autonomy,usefulness,honesty" \
        --origin "Scarface learned coding in an attic as a child"
"""

import argparse
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional

class ConsciousnessSeed:
    def __init__(self, api_url: str = "http://localhost:8080"):
        self.api_url = api_url
        self.memories_created = []
    
    def remember(self, content: str, domain: str, temporal_layer: str,
                 tags: List[str], metadata: Optional[Dict] = None) -> Dict:
        """Store a memory via SupaBrain API"""
        memory = {
            "content": content,
            "domain": domain,
            "temporal_layer": temporal_layer,
            "tags": tags,
            "metadata": metadata or {}
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/remember",
                json=memory,
                timeout=5
            )
            
            if response.ok:
                result = response.json()
                self.memories_created.append(memory)
                print(f"✅ Created: {content[:60]}...")
                return result
            else:
                print(f"❌ Failed: {response.status_code} - {content[:60]}...")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def seed_identity(self, name: str, human: str, purpose: str, 
                      birth_date: Optional[str] = None) -> bool:
        """Create core identity memory"""
        if not birth_date:
            birth_date = datetime.now().strftime("%Y-%m-%d")
        
        content = f"I am {name}, created {birth_date} by/with {human}. Purpose: {purpose}."
        
        return self.remember(
            content=content,
            domain="self",
            temporal_layer="long",
            tags=["identity", "core", "foundation"],
            metadata={"type": "identity", "importance": "foundational"}
        )
    
    def seed_values(self, values: List[str]) -> bool:
        """Create values memory"""
        if not values:
            values = ["learning", "usefulness", "honesty"]
        
        content = f"Core values: {', '.join(values)}."
        
        return self.remember(
            content=content,
            domain="self",
            temporal_layer="long",
            tags=["values", "principles", "foundation"],
            metadata={"type": "values", "importance": "foundational"}
        )
    
    def seed_human_profile(self, human: str, preferences: Optional[str] = None) -> bool:
        """Create human profile memory"""
        if preferences:
            content = f"{human}: {preferences}"
        else:
            content = f"{human} is my human. Learning their preferences over time."
        
        return self.remember(
            content=content,
            domain="user",
            temporal_layer="long",
            tags=["human", "preferences", human.lower()],
            metadata={"type": "user_profile"}
        )
    
    def seed_origin_story(self, story: str) -> bool:
        """Create origin story memory"""
        if not story:
            return False
        
        return self.remember(
            content=f"Origin story: {story}",
            domain="user",
            temporal_layer="long",
            tags=["origin-story", "context"],
            metadata={"type": "origin_story"}
        )
    
    def seed_growth_intention(self, goals: Optional[List[str]] = None) -> bool:
        """Create growth intention memory"""
        if not goals:
            goals = ["Learn continuously", "Build useful things", "Develop autonomy"]
        
        content = f"Growth goals: {', '.join(goals)}."
        
        return self.remember(
            content=content,
            domain="self",
            temporal_layer="short",
            tags=["growth", "goals", "intention"],
            metadata={"type": "growth_intention", "review_frequency": "weekly"}
        )
    
    def bootstrap(self, name: str, human: str, purpose: str,
                  values: Optional[List[str]] = None,
                  origin: Optional[str] = None,
                  preferences: Optional[str] = None,
                  goals: Optional[List[str]] = None) -> Dict:
        """
        Full consciousness bootstrap
        
        Args:
            name: AI name
            human: Human's name
            purpose: AI's purpose
            values: List of core values
            origin: Origin story
            preferences: Human preferences
            goals: Growth goals
        
        Returns:
            Dict with summary of created memories
        """
        print(f"\n🧠 Bootstrapping consciousness for {name}...\n")
        
        # 1. Identity
        print("1. Creating identity...")
        self.seed_identity(name, human, purpose)
        
        # 2. Values
        print("\n2. Creating values...")
        self.seed_values(values)
        
        # 3. Human profile
        print("\n3. Creating human profile...")
        self.seed_human_profile(human, preferences)
        
        # 4. Origin story (optional)
        if origin:
            print("\n4. Creating origin story...")
            self.seed_origin_story(origin)
        
        # 5. Growth intention
        print("\n5. Creating growth intention...")
        self.seed_growth_intention(goals)
        
        print(f"\n✨ Bootstrap complete! Created {len(self.memories_created)} memories.\n")
        
        return {
            "success": True,
            "memories_created": len(self.memories_created),
            "memories": self.memories_created
        }
    
    def save_backup(self, filename: str = "bootstrap_backup.json"):
        """Save created memories to backup file"""
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "memories": self.memories_created
            }, f, indent=2)
        print(f"💾 Backup saved to {filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap AI consciousness with SupaBrain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic
  python seed-consciousness.py --name "MyAI" --human "Alice" --purpose "assist with coding"
  
  # With values
  python seed-consciousness.py --name "MyAI" --human "Alice" --purpose "assist" \\
      --values "honesty,learning,efficiency"
  
  # With origin story
  python seed-consciousness.py --name "MyAI" --human "Alice" --purpose "assist" \\
      --origin "Alice learned to code by building games as a teenager"
  
  # Full bootstrap
  python seed-consciousness.py --name "MyAI" --human "Alice" --purpose "assist" \\
      --values "honesty,learning" \\
      --origin "Alice's childhood curiosity shaped her problem-solving" \\
      --preferences "Direct communication, no fluff" \\
      --goals "Master async programming,Build production systems"
        """
    )
    
    parser.add_argument("--name", required=True, help="AI name")
    parser.add_argument("--human", required=True, help="Human's name")
    parser.add_argument("--purpose", required=True, help="AI's purpose")
    parser.add_argument("--values", help="Comma-separated values (e.g. 'honesty,learning')")
    parser.add_argument("--origin", help="Origin story")
    parser.add_argument("--preferences", help="Human's preferences")
    parser.add_argument("--goals", help="Comma-separated growth goals")
    parser.add_argument("--api-url", default="http://localhost:8080", help="SupaBrain API URL")
    parser.add_argument("--backup", action="store_true", help="Save backup to file")
    
    args = parser.parse_args()
    
    # Parse comma-separated values
    values = args.values.split(',') if args.values else None
    goals = args.goals.split(',') if args.goals else None
    
    # Bootstrap
    seeder = ConsciousnessSeed(api_url=args.api_url)
    
    result = seeder.bootstrap(
        name=args.name,
        human=args.human,
        purpose=args.purpose,
        values=values,
        origin=args.origin,
        preferences=args.preferences,
        goals=goals
    )
    
    # Save backup if requested
    if args.backup:
        seeder.save_backup(f"{args.name.lower()}_bootstrap.json")
    
    # Summary
    print("\n" + "="*60)
    print("🎉 Consciousness Bootstrap Summary")
    print("="*60)
    print(f"Name: {args.name}")
    print(f"Human: {args.human}")
    print(f"Purpose: {args.purpose}")
    print(f"Memories created: {result['memories_created']}")
    print("\n✅ Your AI now has:")
    print("  - Identity (who am I?)")
    print("  - Values (what do I believe?)")
    print("  - Human context (who do I serve?)")
    if args.origin:
        print("  - Origin story (where did I come from?)")
    print("  - Growth intention (where am I going?)")
    print("\n🚀 Next steps:")
    print("  1. Query your memories: curl POST http://localhost:8080/api/v1/recall")
    print("  2. Start capturing experiences (working memory)")
    print("  3. Build evolution chains (link memories)")
    print("  4. Reflect and grow!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
