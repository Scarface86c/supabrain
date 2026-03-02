#!/usr/bin/env python3
"""
SupaBrain Learning Tracker
Track skill acquisition and learning progress
"""

from typing import Optional, Dict, Any, List
import asyncpg


class MemoryLearning:
    """Learning progress tracking and skill proficiency management"""
    
    def __init__(self, db_pool: asyncpg.Pool) -> None:
        """
        Initialize learning tracker
        
        Args:
            db_pool: asyncpg database connection pool
        """
        self.db_pool: asyncpg.Pool = db_pool

    async def track_learning(self, agent_id: str, skill: str, memory_id: Optional[int] = None, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Track learning progress for a skill
        
        Args:
            agent_id: Agent identifier (e.g., "default")
            skill: Skill name (e.g., "python", "fastapi")
            memory_id: Optional memory ID this learning is associated with
            notes: Optional notes about the learning
        
        Returns:
            Dict with tracking result
        """
        async with self.db_pool.acquire() as conn:
            # Check if skill already exists
            existing = await conn.fetchrow("""
                SELECT * FROM learning_progress
                WHERE agent_id = $1 AND skill = $2
            """, agent_id, skill)
            
            if existing:
                # Update existing
                await conn.execute("""
                    UPDATE learning_progress
                    SET last_practice = NOW(),
                        memory_count = memory_count + 1,
                        notes = COALESCE($3, notes),
                        updated_at = NOW()
                    WHERE agent_id = $1 AND skill = $2
                """, agent_id, skill, notes)
                
                memory_count = existing['memory_count'] + 1
            else:
                # Insert new
                await conn.execute("""
                    INSERT INTO learning_progress 
                    (agent_id, skill, memory_count, notes)
                    VALUES ($1, $2, 1, $3)
                """, agent_id, skill, notes)
                
                memory_count = 1
            
            # Calculate proficiency
            if memory_count >= 50:
                proficiency = "expert"
            elif memory_count >= 21:
                proficiency = "advanced"
            elif memory_count >= 6:
                proficiency = "intermediate"
            else:
                proficiency = "beginner"
            
            # Update proficiency
            await conn.execute("""
                UPDATE learning_progress
                SET proficiency_level = $3
                WHERE agent_id = $1 AND skill = $2
            """, agent_id, skill, proficiency)
            
            return {
                "success": True,
                "skill": skill,
                "memory_count": memory_count,
                "proficiency_level": proficiency
            }
    
    async def get_learning_progress(self, agent_id: str, skill: str) -> Optional[Dict[str, Any]]:
        """Get learning progress for a specific skill"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM learning_progress
                WHERE agent_id = $1 AND skill = $2
            """, agent_id, skill)
            
            if not row:
                return None
            
            # Calculate days learning
            days_learning = (row['last_practice'] - row['first_encounter']).days
            
            return {
                "skill": row['skill'],
                "proficiency_level": row['proficiency_level'],
                "memory_count": row['memory_count'],
                "first_encounter": row['first_encounter'].isoformat(),
                "last_practice": row['last_practice'].isoformat(),
                "days_learning": days_learning,
                "notes": row['notes']
            }
    
    async def list_skills(self, agent_id: str) -> Dict[str, Any]:
        """List all skills being tracked"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT skill, proficiency_level, memory_count, last_practice
                FROM learning_progress
                WHERE agent_id = $1
                ORDER BY last_practice DESC
            """, agent_id)
            
            skills = []
            by_proficiency = {"expert": 0, "advanced": 0, "intermediate": 0, "beginner": 0}
            
            for row in rows:
                skills.append({
                    "skill": row['skill'],
                    "proficiency": row['proficiency_level'],
                    "memory_count": row['memory_count'],
                    "last_practice": row['last_practice'].isoformat()
                })
                by_proficiency[row['proficiency_level']] += 1
            
            return {
                "skills": skills,
                "total_skills": len(skills),
                "by_proficiency": by_proficiency
            }
    
    async def get_learning_velocity(self, agent_id: str, days: int = 7) -> Dict[str, Any]:
        """Get learning velocity (skills learned/practiced in time period)"""
        async with self.db_pool.acquire() as conn:
            # Skills with activity in the period
            rows = await conn.fetch("""
                SELECT skill, memory_count
                FROM learning_progress
                WHERE agent_id = $1 
                  AND last_practice >= NOW() - $2 * INTERVAL '1 day'
                ORDER BY last_practice DESC
            """, agent_id, days)
            
            # New skills (first encounter in period)
            new_skills_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM learning_progress
                WHERE agent_id = $1
                  AND first_encounter >= NOW() - $2 * INTERVAL '1 day'
            """, agent_id, days)
            
            trending_skills = [row['skill'] for row in rows[:5]]  # Top 5
            total_learnings = sum(row['memory_count'] for row in rows)
            
            return {
                "period_days": days,
                "new_skills": new_skills_count,
                "skills_practiced": len(rows),
                "total_learnings": total_learnings,
                "velocity": round(total_learnings / days, 2) if days > 0 else 0,
                "trending_skills": trending_skills
            }
