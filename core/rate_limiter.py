#!/usr/bin/env python3
"""
Rate Limiting Middleware for SupaBrain API
Simple token bucket implementation with in-memory storage
"""

import time
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import os


class RateLimiter:
    """Token bucket rate limiter with per-IP tracking"""
    
    def __init__(self, requests_per_minute: int = 60, burst_size: int = 100):
        """
        Initialize rate limiter
        
        Args:
            requests_per_minute: Sustained rate limit (tokens per minute)
            burst_size: Maximum burst capacity (bucket size)
        """
        self.rate = requests_per_minute / 60.0  # Tokens per second
        self.burst_size = burst_size
        self.buckets: Dict[str, Tuple[float, float]] = {}  # {ip: (tokens, last_update)}
        
    def _get_bucket(self, key: str) -> Tuple[float, float]:
        """Get or create bucket for key (IP address)"""
        if key not in self.buckets:
            self.buckets[key] = (self.burst_size, time.time())
        return self.buckets[key]
    
    def _update_bucket(self, key: str) -> float:
        """Update bucket tokens based on time elapsed"""
        tokens, last_update = self._get_bucket(key)
        now = time.time()
        elapsed = now - last_update
        
        # Add tokens based on elapsed time (refill)
        tokens = min(self.burst_size, tokens + elapsed * self.rate)
        
        self.buckets[key] = (tokens, now)
        return tokens
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed (consume 1 token)"""
        tokens = self._update_bucket(key)
        
        if tokens >= 1.0:
            self.buckets[key] = (tokens - 1.0, time.time())
            return True
        return False
    
    def cleanup_old_entries(self, max_age_seconds: int = 3600):
        """Remove old bucket entries to prevent memory leak"""
        now = time.time()
        self.buckets = {
            k: v for k, v in self.buckets.items()
            if now - v[1] < max_age_seconds
        }


# Global rate limiter instance
# Configuration from environment
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
RATE_LIMIT_BURST = int(os.getenv("RATE_LIMIT_BURST", "100"))

rate_limiter = RateLimiter(
    requests_per_minute=RATE_LIMIT_PER_MINUTE,
    burst_size=RATE_LIMIT_BURST
)


async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware for rate limiting"""
    
    # Skip rate limiting if disabled
    if not RATE_LIMIT_ENABLED:
        return await call_next(request)
    
    # Skip rate limiting for health check endpoints
    if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
        return await call_next(request)
    
    # Get client IP (handle proxies via X-Forwarded-For)
    client_ip = request.headers.get("X-Forwarded-For", request.client.host).split(",")[0].strip()
    
    # Check rate limit
    if not rate_limiter.is_allowed(client_ip):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Rate limit exceeded. Please try again later.",
                "limit": RATE_LIMIT_PER_MINUTE,
                "window": "1 minute"
            }
        )
    
    # Cleanup old entries periodically (1% chance per request)
    import random
    if random.random() < 0.01:
        rate_limiter.cleanup_old_entries()
    
    return await call_next(request)
