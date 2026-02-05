#!/usr/bin/env python3
"""
Import Memories from Files to SupaBrain
Useful for bootstrapping or migrating existing memory files
"""

import asyncio
import asyncpg
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres@localhost:5432/supabrain")


async def import_file(conn, file_path, domain="general", temporal_layer="long", tags=None):
    """Import a single file as a memory"""
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    if not content.strip():
        print(f"⚠️  Empty file, skipping: {file_path}")
        return False
    
    # Generate tags
    if tags is None:
        tags = []
    
    # Add filename as tag
    filename = Path(file_path).stem
    tags.append(filename)
    tags.append("imported")
    
    # Add date if in filename (e.g., 2026-02-05.md)
    if any(char.isdigit() for char in filename):
        tags.append("dated")
    
    try:
        # Insert memory (simplified - no embedding for now)
        await conn.execute("""
            INSERT INTO memories (content, temporal_layer, domain, tags, agent_name, created_at)
            VALUES ($1, $2, $3, $4, 'importer', NOW())
        """, content, temporal_layer, domain, tags)
        
        print(f"✅ Imported: {file_path} ({len(content)} chars)")
        return True
        
    except Exception as e:
        print(f"❌ Error importing {file_path}: {e}")
        return False


async def import_directory(conn, dir_path, domain="general", temporal_layer="long", pattern="*.md"):
    """Import all files matching pattern from directory"""
    
    directory = Path(dir_path)
    if not directory.exists():
        print(f"❌ Directory not found: {dir_path}")
        return 0
    
    files = list(directory.glob(pattern))
    
    if not files:
        print(f"⚠️  No files matching '{pattern}' in {dir_path}")
        return 0
    
    print(f"\n📂 Importing {len(files)} files from {dir_path}...")
    
    success = 0
    for file in files:
        tags = [f"dir:{directory.name}"]
        if await import_file(conn, str(file), domain, temporal_layer, tags):
            success += 1
    
    return success


async def import_memory_md(conn, memory_file):
    """Import MEMORY.md - special handling for curated memories"""
    
    if not Path(memory_file).exists():
        print(f"❌ {memory_file} not found")
        return False
    
    print(f"\n📄 Importing {memory_file} (curated long-term memory)...")
    
    with open(memory_file) as f:
        content = f.read()
    
    # Split into sections (by ## headers)
    sections = []
    current_section = {"title": "", "content": ""}
    
    for line in content.split('\n'):
        if line.startswith('## '):
            if current_section["content"]:
                sections.append(current_section)
            current_section = {"title": line[3:].strip(), "content": ""}
        else:
            current_section["content"] += line + "\n"
    
    if current_section["content"]:
        sections.append(current_section)
    
    print(f"   Found {len(sections)} sections")
    
    # Import each section as separate memory
    success = 0
    for section in sections:
        if not section["content"].strip():
            continue
        
        # Determine domain from section title
        title_lower = section["title"].lower()
        if any(word in title_lower for word in ["who i am", "identity", "soul"]):
            domain = "self"
        elif any(word in title_lower for word in ["scarface", "human", "user"]):
            domain = "user"
        elif any(word in title_lower for word in ["project", "bct", "supabrain"]):
            domain = "projects"
        elif any(word in title_lower for word in ["lesson", "learned", "mistake"]):
            domain = "self"
        else:
            domain = "general"
        
        memory_content = f"# {section['title']}\n\n{section['content']}"
        
        tags = ["MEMORY.md", "curated", section['title'].lower().replace(' ', '-')]
        
        try:
            await conn.execute("""
                INSERT INTO memories (content, temporal_layer, domain, tags, agent_name)
                VALUES ($1, 'long', $2, $3, 'scar')
            """, memory_content, domain, tags)
            
            print(f"   ✅ Imported section: {section['title'][:50]}...")
            success += 1
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return success


async def main():
    parser = argparse.ArgumentParser(description="Import memories from files to SupaBrain")
    parser.add_argument('--file', help='Import single file')
    parser.add_argument('--dir', help='Import directory')
    parser.add_argument('--pattern', default='*.md', help='File pattern (default: *.md)')
    parser.add_argument('--memory-md', help='Import MEMORY.md with section parsing')
    parser.add_argument('--daily-logs', help='Import daily log directory (e.g., memory/)')
    parser.add_argument('--domain', default='general', help='Memory domain')
    parser.add_argument('--layer', default='long', help='Temporal layer')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be imported')
    
    args = parser.parse_args()
    
    if not any([args.file, args.dir, args.memory_md, args.daily_logs]):
        parser.print_help()
        return
    
    print("🧠 SupaBrain Memory Importer")
    print(f"   Database: {DB_URL}")
    print(f"   Dry run: {args.dry_run}")
    print()
    
    if args.dry_run:
        print("⚠️  DRY RUN - No data will be written")
        print()
    
    # Connect to database
    conn = await asyncpg.connect(DB_URL)
    print("✅ Connected to database")
    
    try:
        total = 0
        
        if args.file:
            if not args.dry_run:
                success = await import_file(conn, args.file, args.domain, args.layer)
                total += 1 if success else 0
            else:
                print(f"Would import: {args.file}")
        
        if args.dir:
            if not args.dry_run:
                total += await import_directory(conn, args.dir, args.domain, args.layer, args.pattern)
            else:
                files = list(Path(args.dir).glob(args.pattern))
                print(f"Would import {len(files)} files from {args.dir}")
        
        if args.memory_md:
            if not args.dry_run:
                total += await import_memory_md(conn, args.memory_md)
            else:
                print(f"Would import sections from: {args.memory_md}")
        
        if args.daily_logs:
            if not args.dry_run:
                total += await import_directory(conn, args.daily_logs, "general", "long", "*.md")
            else:
                files = list(Path(args.daily_logs).glob("*.md"))
                print(f"Would import {len(files)} daily logs from {args.daily_logs}")
        
        print(f"\n✅ Import complete: {total} memories imported")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
