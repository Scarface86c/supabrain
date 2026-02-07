#!/usr/bin/env python3
"""
Test Rate Limiting Middleware
"""

import unittest
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../core'))

from rate_limiter import RateLimiter


class TestRateLimiter(unittest.TestCase):
    """Test rate limiting functionality"""
    
    def test_basic_rate_limiting(self):
        """Test that rate limiting allows requests within limits"""
        limiter = RateLimiter(requests_per_minute=60, burst_size=10)
        
        # Should allow first 10 requests (burst)
        for i in range(10):
            self.assertTrue(
                limiter.is_allowed("test_ip"),
                f"Request {i+1} should be allowed within burst"
            )
        
        # 11th request should be denied (no refill yet)
        self.assertFalse(
            limiter.is_allowed("test_ip"),
            "Request beyond burst should be denied"
        )
    
    def test_token_refill(self):
        """Test that tokens refill over time"""
        limiter = RateLimiter(requests_per_minute=60, burst_size=5)
        
        # Consume all tokens
        for i in range(5):
            self.assertTrue(limiter.is_allowed("test_ip"))
        
        # Wait for 1 second (should refill 1 token at 60/min = 1/sec)
        time.sleep(1.1)
        
        # Should allow 1 more request
        self.assertTrue(
            limiter.is_allowed("test_ip"),
            "Token should refill after waiting"
        )
    
    def test_multiple_ips(self):
        """Test that different IPs have separate buckets"""
        limiter = RateLimiter(requests_per_minute=60, burst_size=5)
        
        # IP1 consumes all tokens
        for i in range(5):
            self.assertTrue(limiter.is_allowed("ip1"))
        
        # IP1 should be denied
        self.assertFalse(limiter.is_allowed("ip1"))
        
        # IP2 should still be allowed (separate bucket)
        self.assertTrue(limiter.is_allowed("ip2"))
    
    def test_cleanup(self):
        """Test that old entries are cleaned up"""
        limiter = RateLimiter(requests_per_minute=60, burst_size=10)
        
        # Create some buckets
        limiter.is_allowed("ip1")
        limiter.is_allowed("ip2")
        limiter.is_allowed("ip3")
        
        self.assertEqual(len(limiter.buckets), 3)
        
        # Cleanup with short max_age (0 seconds)
        limiter.cleanup_old_entries(max_age_seconds=0)
        
        # All buckets should be removed
        self.assertEqual(len(limiter.buckets), 0)


if __name__ == "__main__":
    unittest.main()
