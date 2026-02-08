"""
Tag system endpoints
"""

from fastapi import APIRouter, HTTPException
from models import TagStatsResponse, TagSuggestRequest, TagSuggestResponse, TagCanonicalizeRequest, TagCanonicalizeResponse
from memory_engine import engine
from tag_system import tag_system

router = APIRouter(prefix="/api/v1/tags", tags=["tags"])


@router.get("/stats", response_model=TagStatsResponse)
async def get_tag_stats():
    """Get tag usage statistics"""
    try:
        async with engine.db_pool.acquire() as conn:
            # Get basic stats
            result = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT m.id) as memories_with_tags,
                    COUNT(t.tag) as total_tags,
                    COUNT(DISTINCT t.tag) as unique_tags
                FROM memories m
                CROSS JOIN LATERAL unnest(m.tags) as t(tag)
                WHERE m.tags IS NOT NULL
            """)
            
            # Top tags
            top_tags_result = await conn.fetch("""
                SELECT t.tag, COUNT(*) as count
                FROM memories m
                CROSS JOIN LATERAL unnest(m.tags) as t(tag)
                WHERE m.tags IS NOT NULL
                GROUP BY t.tag
                ORDER BY count DESC
                LIMIT 20
            """)
            
            top_tags = [{"tag": row["tag"], "count": row["count"]} for row in top_tags_result]
            
            # Group tags by category
            all_tags = [row["tag"] for row in top_tags_result]
            tags_by_category = tag_system.group_tags_by_category(all_tags)
            
            return TagStatsResponse(
                total_tags=result["total_tags"],
                unique_tags=result["unique_tags"],
                top_tags=top_tags,
                tags_by_category=tags_by_category,
                memories_with_tags=result["memories_with_tags"]
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest", response_model=TagSuggestResponse)
async def suggest_tags(request: TagSuggestRequest):
    """Suggest tags based on content"""
    try:
        suggestions = tag_system.suggest_tags(
            content=request.content,
            existing_tags=request.existing_tags,
            limit=request.limit
        )
        
        # Group suggestions by category
        categories = tag_system.group_tags_by_category(suggestions)
        
        return TagSuggestResponse(
            suggestions=suggestions,
            categories=categories
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/canonicalize", response_model=TagCanonicalizeResponse)
async def canonicalize_tags_endpoint(request: TagCanonicalizeRequest):
    """Canonicalize tags (apply aliases and normalization)"""
    try:
        original = request.tags
        canonical = tag_system.canonicalize_tags(original)
        
        # Find changes (before deduplication)
        changes = []
        individual_canonical = [tag_system.canonicalize_tag(t) for t in original]
        for orig, canon in zip(original, individual_canonical):
            if orig.lower() != canon:
                changes.append({
                    "original": orig,
                    "canonical": canon,
                    "reason": "alias" if orig.lower() in tag_system.ALIASES else "normalized"
                })
        
        # Add note if deduplicated
        if len(canonical) < len(individual_canonical):
            dupes = len(individual_canonical) - len(canonical)
            changes.append({
                "original": "(duplicates)",
                "canonical": "(removed)",
                "reason": f"deduplicated {dupes} tag(s)"
            })
        
        return TagCanonicalizeResponse(
            original=original,
            canonical=canonical,
            changes=changes
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
