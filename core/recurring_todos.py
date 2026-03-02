"""
Recurring TODO logic for SupaBrain
Created: 2026-02-24
Purpose: Handle creation of next recurring TODO instances
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def calculate_next_occurrence(
    last_completion: datetime,
    pattern: Dict[str, Any]
) -> Optional[datetime]:
    """
    Calculate next occurrence date based on recurring pattern.
    
    Args:
        last_completion: When the TODO was last completed
        pattern: Recurring pattern dict with frequency, interval, etc.
        
    Returns:
        Next occurrence datetime or None if pattern ended
    """
    frequency = pattern.get('frequency')
    interval = pattern.get('interval', 1)
    end_date_str = pattern.get('end_date')
    
    # Check if recurrence ended
    if end_date_str:
        end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        if datetime.now(end_date.tzinfo) > end_date:
            return None
    
    next_date = last_completion
    
    if frequency == 'daily':
        next_date = last_completion + timedelta(days=interval)
        
    elif frequency == 'weekly':
        next_date = last_completion + timedelta(weeks=interval)
        
    elif frequency == 'monthly':
        # Simple approach: add interval months
        month = last_completion.month + interval
        year = last_completion.year
        while month > 12:
            month -= 12
            year += 1
        try:
            next_date = last_completion.replace(year=year, month=month)
        except ValueError:
            # Day doesn't exist in target month (e.g., Feb 30)
            # Fall back to last day of month
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            next_date = last_completion.replace(year=year, month=month, day=last_day)
            
    elif frequency == 'yearly':
        next_date = last_completion.replace(year=last_completion.year + interval)
        
    else:
        logger.warning(f"Unknown frequency: {frequency}")
        return None
    
    return next_date


def process_recurring_todos(db_conn) -> int:
    """
    Process all completed recurring TODOs and create next instances.
    
    Args:
        db_conn: PostgreSQL database connection
        
    Returns:
        Number of new recurring instances created
    """
    created_count = 0
    
    with db_conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Find completed TODOs with recurring patterns
        cur.execute("""
            SELECT id, layer_1_summary, tags, importance_score, recurring_pattern, updated_at
            FROM memories
            WHERE recurring_pattern IS NOT NULL
            AND 'todo:completed' = ANY(tags)
            AND (last_recurrence_check IS NULL 
                 OR last_recurrence_check < updated_at)
            ORDER BY updated_at DESC
        """)
        
        recurring_todos = cur.fetchall()
        
        for todo in recurring_todos:
            try:
                pattern = todo['recurring_pattern']
                completion_time = todo['updated_at']
                
                # Calculate next occurrence
                next_date = calculate_next_occurrence(completion_time, pattern)
                
                if next_date is None:
                    # Recurrence ended, mark as checked
                    cur.execute("""
                        UPDATE memories
                        SET last_recurrence_check = NOW()
                        WHERE id = %s
                    """, (todo['id'],))
                    logger.info(f"Recurring TODO {todo['id']} ended")
                    continue
                
                # Create new instance
                # Remove completed status, add open status
                new_tags = [t for t in todo['tags'] if t != 'todo:completed']
                if 'todo:open' not in new_tags:
                    new_tags.append('todo:open')
                
                # Extract content (remove old dates if any)
                content = todo['layer_1_summary']
                
                # Add due date annotation
                content_with_date = f"{content}\nDue: {next_date.strftime('%Y-%m-%d')}"
                
                cur.execute("""
                    INSERT INTO memories (
                        layer_1_summary, tags, importance_score, 
                        recurring_pattern, parent_id,
                        created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    content_with_date,
                    new_tags,
                    todo['importance_score'],
                    pattern,
                    todo['id'],  # Link to parent
                    next_date,
                    next_date
                ))
                
                # Update parent's last_recurrence_check
                cur.execute("""
                    UPDATE memories
                    SET last_recurrence_check = NOW()
                    WHERE id = %s
                """, (todo['id'],))
                
                created_count += 1
                logger.info(f"Created recurring instance for TODO {todo['id']}, due {next_date}")
                
            except (psycopg2.Error, KeyError, ValueError, TypeError) as e:
                logger.error(f"Error processing recurring TODO {todo['id']}: {e}")
                continue
        
        db_conn.commit()
    
    return created_count


if __name__ == "__main__":
    # Standalone execution for cron
    logging.basicConfig(level=logging.INFO)
    
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL not found in environment")
        exit(1)
    
    # Parse connection string
    # Format: postgresql://user:pass@host:port/dbname
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
    if not match:
        logger.error("Invalid DATABASE_URL format")
        exit(1)
    
    user, password, host, port, dbname = match.groups()
    
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        
        count = process_recurring_todos(conn)
        logger.info(f"✅ Processed recurring TODOs: {count} new instances created")
        
        conn.close()
        
    except (psycopg2.OperationalError, psycopg2.Error) as e:
        logger.error(f"Database connection failed: {e}")
        exit(1)
