#!/usr/bin/env python3
"""Run database migrations"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def run_migration(sql_file):
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres@localhost:5432/supabrain")
    conn = await asyncpg.connect(db_url)
    
    with open(sql_file, 'r') as f:
        sql = f.read()
    
    try:
        await conn.execute(sql)
        print(f"✅ Migration {sql_file} completed")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 run_migration.py <migration_file.sql>")
        sys.exit(1)
    
    asyncio.run(run_migration(sys.argv[1]))
