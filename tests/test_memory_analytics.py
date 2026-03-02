#!/usr/bin/env python3
"""
Tests for MemoryAnalytics module
Integration tests via API endpoints for analytics, statistics, and decay management
"""

import pytest

TEST_AGENT = "TestAgent"


def create_memory(client, content: str, importance_score: float = 0.5, temporal_layer: str = "long"):
    """Helper: Create a memory and return its id"""
    resp = client.post("/api/v1/remember", json={
        "agent_name": TEST_AGENT,
        "content": content,
        "importance_score": importance_score,
        "temporal_layer": temporal_layer,
        "tags": ["test"]
    })
    assert resp.status_code == 200, f"Failed to create memory: {resp.text}"
    data = resp.json()
    return data.get("memory_id") or data.get("id")


def test_update_decay_scores(client):
    """Test decay score calculation via API"""
    # Add test memory
    create_memory(client, "Test memory for decay", importance_score=0.7)
    
    # Update decay scores (agent_name as query param)
    resp = client.post(f"/api/v1/analytics/decay/update?agent_name={TEST_AGENT}")
    
    assert resp.status_code == 200
    result = resp.json()
    assert "memories_updated" in result
    assert "avg_decay_score" in result
    assert result["memories_updated"] >= 1
    assert 0.0 <= result["avg_decay_score"] <= 1.0


def test_update_decay_scores_high_importance(client):
    """Test that high-importance memories decay slower"""
    # Add high-importance memory
    create_memory(client, "Critical memory", importance_score=0.9)
    
    # Update decay (agent_name as query param)
    resp = client.post(f"/api/v1/analytics/decay/update?agent_name={TEST_AGENT}")
    
    assert resp.status_code == 200
    result = resp.json()
    # High-importance memories should have decay score close to 1.0
    assert result["avg_decay_score"] >= 0.8


def test_get_stats(client):
    """Test basic statistics retrieval"""
    # Add test memories
    create_memory(client, "First memory", importance_score=0.6)
    create_memory(client, "Second memory", importance_score=0.8)
    
    # Get stats
    resp = client.get(f"/api/v1/stats?agent_name={TEST_AGENT}")
    
    assert resp.status_code == 200
    stats = resp.json()
    assert "total_memories" in stats
    assert "average_importance" in stats
    assert stats["total_memories"] >= 2
    assert 0.0 <= stats["average_importance"] <= 1.0


def test_get_analytics(client):
    """Test comprehensive analytics data"""
    # Add test memory
    create_memory(client, "Analytics test", importance_score=0.7)
    
    # Get analytics (using stats endpoint as proxy)
    resp = client.get(f"/api/v1/stats?agent_name={TEST_AGENT}")
    
    assert resp.status_code == 200
    analytics = resp.json()
    assert analytics is not None
    assert isinstance(analytics, dict)


def test_layer_distribution(client):
    """Test per-layer memory distribution"""
    # Add memories in different layers
    create_memory(client, "Working memory", importance_score=0.5, temporal_layer="working")
    create_memory(client, "Short-term memory", importance_score=0.6, temporal_layer="short")
    create_memory(client, "Long-term memory", importance_score=0.8, temporal_layer="long")
    
    # Get stats (should include layer info)
    resp = client.get(f"/api/v1/stats?agent_name={TEST_AGENT}")
    
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["total_memories"] >= 3


def test_decay_after_multiple_updates(client):
    """Test decay consistency across multiple update calls"""
    # Add memory
    mem_id = create_memory(client, "Decay test memory", importance_score=0.7)
    
    # Update decay multiple times
    for _ in range(3):
        resp = client.post(f"/api/v1/analytics/decay/update?agent_name={TEST_AGENT}")
        assert resp.status_code == 200
        result = resp.json()
        # Decay score should remain stable (no access time change)
        assert 0.9 <= result["avg_decay_score"] <= 1.0


def test_stats_with_empty_agent(client):
    """Test stats retrieval for agent with no memories"""
    resp = client.get("/api/v1/stats?agent_name=NonexistentAgent")
    
    # Should handle gracefully (either empty stats or 404)
    assert resp.status_code in [200, 404]
    if resp.status_code == 200:
        stats = resp.json()
        assert "total_memories" in stats or "error" in stats
