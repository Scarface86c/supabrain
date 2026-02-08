"""
Integration tests for SupaBrain API
Tests end-to-end flows through the actual API endpoints
"""

import pytest
import pytest_asyncio
import sys
import os
from httpx import AsyncClient, ASGITransport
from datetime import datetime

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from server import app

# Test agent for all tests
TEST_AGENT = "TestAgent"


@pytest_asyncio.fixture
async def client():
    """Create async test client"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoints:
    """Test health and status endpoints"""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root endpoint returns service info"""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "SupaBrain"
        assert "version" in data
        assert data["status"] == "operational"
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint"""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "model" in data


class TestMemoryFlow:
    """Test complete remember → recall flow"""
    
    @pytest.mark.asyncio
    async def test_remember_and_recall(self, client):
        """Test storing and retrieving a memory"""
        # Store a memory
        memory_data = {
            "content": "Integration test memory - API flow test",
            "agent_name": TEST_AGENT,
            "tags": ["test", "integration"],
            "importance_score": 0.8,
            "temporal_layer": "working",
            "ttl_hours": 1
        }
        
        store_response = await client.post("/api/v1/remember", json=memory_data)
        assert store_response.status_code == 200
        
        store_data = store_response.json()
        assert store_data["success"] is True
        assert "memory_id" in store_data
        memory_id = store_data["memory_id"]
        
        # Recall the memory
        recall_data = {
            "query": "integration test",
            "agent_name": TEST_AGENT,
            "limit": 5
        }
        
        recall_response = await client.post("/api/v1/recall", json=recall_data)
        assert recall_response.status_code == 200
        
        memories = recall_response.json()
        assert isinstance(memories, list)
        assert len(memories) > 0
        
        # Verify our memory is in results
        found = any(m["id"] == memory_id for m in memories)
        assert found, f"Memory {memory_id} not found in recall results"
    
    @pytest.mark.asyncio
    async def test_layered_recall(self, client):
        """Test hierarchical layered recall"""
        # Store memories in different layers
        layers = ["working", "short", "long"]
        memory_ids = []
        
        for layer in layers:
            memory_data = {
                "content": f"Layer test memory - {layer} layer",
                "agent_name": TEST_AGENT,
                "tags": ["layertest"],
                "temporal_layer": layer
            }
            
            response = await client.post("/api/v1/remember", json=memory_data)
            assert response.status_code == 200
            memory_ids.append(response.json()["memory_id"])
        
        # Test layered recall
        layered_query = {
            "query": "layer test",
            "agent_name": TEST_AGENT,
            "start_layer": 1,
            "max_layer": 3,
            "limit_per_layer": 5
        }
        
        response = await client.post("/api/v1/recall/layered", json=layered_query)
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert "layers_searched" in data
        assert len(data["layers_searched"]) > 0


class TestStatsEndpoints:
    """Test statistics endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_stats(self, client):
        """Test basic stats endpoint"""
        response = await client.get(f"/api/v1/stats?agent_name={TEST_AGENT}")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_memories" in data
        assert "average_importance" in data
        assert "total_accesses" in data
        assert isinstance(data["total_memories"], int)
    
    @pytest.mark.asyncio
    async def test_get_layer_stats(self, client):
        """Test layer statistics"""
        response = await client.get(f"/api/v1/stats/layers?agent_name={TEST_AGENT}")
        assert response.status_code == 200
        
        data = response.json()
        assert "layer_1" in data
        assert "layer_2" in data
        assert "layer_3" in data
        assert "total" in data


class TestIdentityEndpoints:
    """Test identity endpoints"""
    
    @pytest.mark.asyncio
    async def test_whoami(self, client):
        """Test whoami endpoint"""
        response = await client.get(f"/api/v1/whoami?agent_name={TEST_AGENT}")
        
        # May return 404 if identity doesn't exist, or 200 with default
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "name" in data
            assert "vibe" in data


class TestErrorHandling:
    """Test error handling and validation"""
    
    @pytest.mark.asyncio
    async def test_invalid_remember_data(self, client):
        """Test validation errors return 400"""
        # Missing required field
        invalid_data = {
            "content": "Test"
            # Missing agent_name
        }
        
        response = await client.post("/api/v1/remember", json=invalid_data)
        assert response.status_code == 422  # FastAPI validation error
    
    @pytest.mark.asyncio
    async def test_invalid_recall_query(self, client):
        """Test invalid recall parameters"""
        invalid_query = {
            "query": "",  # Empty query
            "agent_name": TEST_AGENT,
            "limit": 1000  # Too high
        }
        
        response = await client.post("/api/v1/recall", json=invalid_query)
        # Should return validation error
        assert response.status_code in [400, 422]


class TestTagSystem:
    """Test tag operations"""
    
    @pytest.mark.asyncio
    async def test_tag_stats(self, client):
        """Test tag statistics endpoint"""
        response = await client.get("/api/v1/tags/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_tags" in data
        assert "unique_tags" in data
        assert "top_tags" in data
    
    @pytest.mark.asyncio
    async def test_tag_canonicalize(self, client):
        """Test tag canonicalization"""
        canonicalize_data = {
            "tags": ["TEST", "Test", "test", "python"]
        }
        
        response = await client.post("/api/v1/tags/canonicalize", json=canonicalize_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "original" in data
        assert "canonical" in data
        # Should deduplicate
        assert len(data["canonical"]) < len(data["original"])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
