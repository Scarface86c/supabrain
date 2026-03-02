"""
Tests for rate_limiter.py - Token bucket rate limiting
Coverage: RateLimiter class + middleware integration
"""

import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from rate_limiter import RateLimiter, rate_limit_middleware


class TestRateLimiterBasics:
    """Test core RateLimiter functionality"""
    
    def test_initialization(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter(requests_per_minute=60, burst_size=100)
        
        assert limiter.rate == 1.0  # 60/60 = 1 token/second
        assert limiter.burst_size == 100
        assert limiter.buckets == {}
    
    def test_first_request_allowed(self):
        """Test that first request is always allowed (full bucket)"""
        limiter = RateLimiter(requests_per_minute=60, burst_size=10)
        
        assert limiter.is_allowed("client1") is True
    
    def test_burst_limit(self):
        """Test burst capacity enforcement"""
        limiter = RateLimiter(requests_per_minute=60, burst_size=5)
        
        # First 5 requests should succeed (burst capacity)
        for i in range(5):
            assert limiter.is_allowed("client1") is True, f"Request {i+1} should succeed"
        
        # 6th request should fail (bucket empty)
        assert limiter.is_allowed("client1") is False
    
    def test_token_refill(self):
        """Test that tokens refill over time"""
        limiter = RateLimiter(requests_per_minute=60, burst_size=10)  # 1 token/second
        
        # Consume all tokens
        for _ in range(10):
            limiter.is_allowed("client1")
        
        # Next request should fail (empty bucket)
        assert limiter.is_allowed("client1") is False
        
        # Wait 2 seconds → +2 tokens
        time.sleep(2.1)
        
        # Should allow 2 requests now
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is False  # Out of tokens again
    
    def test_multiple_clients(self):
        """Test that different IPs have independent buckets"""
        limiter = RateLimiter(requests_per_minute=60, burst_size=5)
        
        # Exhaust client1's bucket
        for _ in range(5):
            limiter.is_allowed("client1")
        
        # client1 should be blocked
        assert limiter.is_allowed("client1") is False
        
        # client2 should still have full bucket
        assert limiter.is_allowed("client2") is True
    
    def test_cleanup_old_entries(self):
        """Test that old bucket entries are removed"""
        limiter = RateLimiter(requests_per_minute=60, burst_size=10)
        
        # Create buckets for 3 clients
        limiter.is_allowed("client1")
        limiter.is_allowed("client2")
        limiter.is_allowed("client3")
        
        assert len(limiter.buckets) == 3
        
        # Manually set client1's timestamp to 2 hours ago
        tokens, _ = limiter.buckets["client1"]
        limiter.buckets["client1"] = (tokens, time.time() - 7200)
        
        # Cleanup entries older than 1 hour
        limiter.cleanup_old_entries(max_age_seconds=3600)
        
        assert len(limiter.buckets) == 2
        assert "client1" not in limiter.buckets
        assert "client2" in limiter.buckets
        assert "client3" in limiter.buckets


@pytest.mark.asyncio
class TestRateLimitMiddleware:
    """Test FastAPI middleware integration"""
    
    async def test_middleware_allows_request(self):
        """Test that valid request passes through middleware"""
        # Mock request
        request = Mock(spec=Request)
        request.url.path = "/api/v1/recall"
        request.client = Mock(host="192.168.1.100")
        request.headers = {}
        
        # Mock call_next (simulates next middleware/endpoint)
        call_next = AsyncMock(return_value=Mock(status_code=200))
        
        # Create fresh limiter
        with patch('rate_limiter.RATE_LIMIT_ENABLED', True):
            with patch('rate_limiter.rate_limiter', RateLimiter(requests_per_minute=60, burst_size=10)):
                response = await rate_limit_middleware(request, call_next)
        
        assert response.status_code == 200
        call_next.assert_called_once_with(request)
    
    async def test_middleware_blocks_excessive_requests(self):
        """Test that rate limit is enforced"""
        limiter = RateLimiter(requests_per_minute=60, burst_size=3)
        
        request = Mock(spec=Request)
        request.url.path = "/api/v1/recall"
        request.client = Mock(host="192.168.1.100")
        request.headers = {}
        
        call_next = AsyncMock(return_value=Mock(status_code=200))
        
        with patch('rate_limiter.RATE_LIMIT_ENABLED', True):
            with patch('rate_limiter.rate_limiter', limiter):
                # First 3 requests should pass
                for i in range(3):
                    response = await rate_limit_middleware(request, call_next)
                    assert response.status_code == 200, f"Request {i+1} should succeed"
                
                # 4th request should be blocked
                response = await rate_limit_middleware(request, call_next)
                assert isinstance(response, JSONResponse)
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    async def test_middleware_disabled(self):
        """Test that middleware can be disabled via environment"""
        limiter = RateLimiter(requests_per_minute=1, burst_size=1)  # Very restrictive
        
        request = Mock(spec=Request)
        request.url.path = "/api/v1/recall"
        request.client = Mock(host="192.168.1.100")
        request.headers = {}
        
        call_next = AsyncMock(return_value=Mock(status_code=200))
        
        # Disable rate limiting
        with patch('rate_limiter.RATE_LIMIT_ENABLED', False):
            with patch('rate_limiter.rate_limiter', limiter):
                # Should allow unlimited requests when disabled
                for _ in range(10):
                    response = await rate_limit_middleware(request, call_next)
                    assert response.status_code == 200
    
    async def test_middleware_health_check_exempt(self):
        """Test that health check endpoints are exempt from rate limiting"""
        limiter = RateLimiter(requests_per_minute=1, burst_size=1)
        
        call_next = AsyncMock(return_value=Mock(status_code=200))
        
        # Exhaust bucket for regular endpoint
        request = Mock(spec=Request)
        request.url.path = "/api/v1/recall"
        request.client = Mock(host="192.168.1.100")
        request.headers = {}
        
        with patch('rate_limiter.RATE_LIMIT_ENABLED', True):
            with patch('rate_limiter.rate_limiter', limiter):
                # Exhaust the bucket
                await rate_limit_middleware(request, call_next)
                
                # Next regular request should be blocked
                response = await rate_limit_middleware(request, call_next)
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
                
                # But health check should still work
                health_request = Mock(spec=Request)
                health_request.url.path = "/health"
                health_request.client = Mock(host="192.168.1.100")
                health_request.headers = {}
                
                response = await rate_limit_middleware(health_request, call_next)
                assert response.status_code == 200
    
    async def test_x_forwarded_for_header(self):
        """Test that X-Forwarded-For header is respected (proxy support)"""
        limiter = RateLimiter(requests_per_minute=60, burst_size=2)
        
        call_next = AsyncMock(return_value=Mock(status_code=200))
        
        # Request with X-Forwarded-For header
        request = Mock(spec=Request)
        request.url.path = "/api/v1/recall"
        request.client = Mock(host="10.0.0.1")  # Proxy IP
        request.headers = {"X-Forwarded-For": "203.0.113.42, 10.0.0.1"}  # Real client IP, proxy IP
        
        with patch('rate_limiter.RATE_LIMIT_ENABLED', True):
            with patch('rate_limiter.rate_limiter', limiter):
                # Exhaust bucket for the real client IP
                await rate_limit_middleware(request, call_next)
                await rate_limit_middleware(request, call_next)
                
                # Should be rate limited based on X-Forwarded-For IP, not proxy IP
                response = await rate_limit_middleware(request, call_next)
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
                
                # Verify the correct IP was used by checking bucket
                assert "203.0.113.42" in limiter.buckets
    
    async def test_missing_client_attribute(self):
        """Test handling of missing request.client (TestClient environment)"""
        limiter = RateLimiter(requests_per_minute=60, burst_size=10)
        
        # Mock request without client attribute (simulates TestClient)
        request = Mock(spec=Request)
        request.url.path = "/api/v1/recall"
        request.client = None  # TestClient doesn't set this
        request.headers = {}
        
        call_next = AsyncMock(return_value=Mock(status_code=200))
        
        with patch('rate_limiter.RATE_LIMIT_ENABLED', True):
            with patch('rate_limiter.rate_limiter', limiter):
                # Should not crash, should use fallback IP
                response = await rate_limit_middleware(request, call_next)
                assert response.status_code == 200
                
                # Verify fallback IP was used
                assert "127.0.0.1" in limiter.buckets


class TestRateLimiterEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_zero_rate_blocks_all(self):
        """Test that rate=0 blocks all requests after burst"""
        limiter = RateLimiter(requests_per_minute=0, burst_size=3)
        
        # Burst should still work
        for _ in range(3):
            assert limiter.is_allowed("client1") is True
        
        # No refill happens (rate=0)
        time.sleep(1)
        assert limiter.is_allowed("client1") is False
    
    def test_very_high_rate(self):
        """Test handling of very high request rates"""
        limiter = RateLimiter(requests_per_minute=6000, burst_size=1000)
        
        assert limiter.rate == 100.0  # 6000/60 = 100 tokens/second
        
        # Should allow many rapid requests
        for _ in range(1000):
            assert limiter.is_allowed("client1") is True
    
    def test_bucket_max_capacity(self):
        """Test that bucket doesn't exceed burst_size"""
        limiter = RateLimiter(requests_per_minute=60, burst_size=10)
        
        # Consume some tokens
        limiter.is_allowed("client1")
        limiter.is_allowed("client1")
        limiter.is_allowed("client1")
        
        # Manually set timestamp to 1 hour ago to simulate long wait
        tokens, _ = limiter.buckets["client1"]
        limiter.buckets["client1"] = (tokens, time.time() - 3600)
        
        # Update bucket (should refill to max, not beyond)
        refilled_tokens = limiter._update_bucket("client1")
        assert refilled_tokens == 10.0  # Should not exceed burst_size
