#!/usr/bin/env python3
"""
API Key Authentication for SupaBrain
Optional security layer - can be enabled via environment
"""

import os
import secrets
from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from typing import Optional


# Configuration
AUTH_ENABLED = os.getenv("REQUIRE_AUTH", "false").lower() == "true"
API_KEY = os.getenv("API_KEY", "")

# Generate a secure API key if none is set and auth is enabled
if AUTH_ENABLED and not API_KEY:
    print("⚠️  WARNING: REQUIRE_AUTH=true but no API_KEY set!")
    print("    Generate one with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'")

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = None) -> bool:
    """
    Verify API key from header
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        True if valid, raises HTTPException otherwise
    """
    if not AUTH_ENABLED:
        return True  # Auth disabled, allow all
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    
    return True


async def auth_middleware(request: Request, call_next):
    """
    FastAPI middleware for API key authentication
    Applies to all endpoints except public ones
    """
    
    # Skip auth if disabled
    if not AUTH_ENABLED:
        return await call_next(request)
    
    # Public endpoints (no auth required)
    public_paths = ["/", "/health", "/docs", "/openapi.json", "/redoc"]
    if request.url.path in public_paths:
        return await call_next(request)
    
    # Get API key from header
    api_key = request.headers.get("X-API-Key")
    
    # Verify API key
    try:
        await verify_api_key(api_key)
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )
    
    return await call_next(request)


def generate_api_key() -> str:
    """Generate a secure random API key"""
    return secrets.token_urlsafe(32)


if __name__ == "__main__":
    # CLI tool to generate API keys
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "generate":
        key = generate_api_key()
        print(f"Generated API Key: {key}")
        print(f"\nAdd to .env:")
        print(f"REQUIRE_AUTH=true")
        print(f"API_KEY={key}")
    else:
        print("Usage: python3 auth.py generate")
