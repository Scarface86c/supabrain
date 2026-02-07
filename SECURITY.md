# 🔒 Security Guide

**Important**: SupaBrain is currently in ALPHA. Follow these guidelines for secure deployment.

---

## Quick Security Checklist

### Development (Local)
- ✅ CORS: localhost only (default in .env.example)
- ✅ Auth: Disabled by default (REQUIRE_AUTH=false)
- ✅ Rate limiting: Enabled (60/min, 100 burst)
- ✅ Input validation: All inputs sanitized
- ✅ Runs on localhost:8080

### Production (Public)
- ✅ **Configure CORS** - Set ALLOWED_ORIGINS in .env (comma-separated)
- ✅ **Add authentication** - Set REQUIRE_AUTH=true + API_KEY in .env
- ⚠️ **Use HTTPS** - Encrypt all traffic (reverse proxy like nginx)
- ✅ **Input validation** - Implemented (SQL injection protection)
- ✅ **Rate limiting** - Implemented (token bucket, configurable)
- ⚠️ **Monitor logs** - Track suspicious activity (TODO: structured logging)

---

## CORS Configuration ✅ IMPLEMENTED

### Environment Variable Configuration
```bash
# .env (default for development)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Production example
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### Current Implementation
```python
# core/server.py
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # From environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Default:** Falls back to `"*"` (allow all) if `ALLOWED_ORIGINS` not set.  
**Recommended:** Set explicit origins in production!

---

## Authentication

### API Key (Simple) ✅ IMPLEMENTED

**1. Generate key**
```bash
# Using built-in generator
python3 core/auth.py generate

# Or manually
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**2. Add to .env**
```bash
REQUIRE_AUTH=true
API_KEY=your-generated-key-here
```

**3. Restart API**
```bash
bash restart_api.sh
```

**4. Use in requests**
```bash
curl -H "X-API-Key: your-generated-key-here" \
  "http://localhost:8080/api/v1/whoami?agent_name=YourAgent"
```

**Public endpoints** (no auth required):
- `/` - Root
- `/health` - Health check
- `/docs` - API documentation
- `/openapi.json` - OpenAPI spec
- `/redoc` - ReDoc UI

**Implementation:** See `core/auth.py` for the authentication middleware.

---

## Input Validation ✅ IMPLEMENTED

### Current Status
- ✅ SQL injection protection on all inputs
- ✅ Agent name validation (alphanumeric + underscore/hyphen only)
- ✅ Content length limits (max 50KB)
- ✅ Tag validation (alphanumeric, max 50 chars each)
- ✅ Numeric field range validation

### Implementation
```python
# core/validators.py
import re
from typing import List

def validate_agent_name(name: str) -> str:
    """Validate agent name (SQL injection protection)"""
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        raise ValidationError("Invalid characters in agent name")
    if len(name) > 50:
        raise ValidationError("Agent name too long (max 50)")
    return name

# Applied via Pydantic validators in server.py
class MemoryCreate(BaseModel):
    agent_name: str
    content: str
    
    @validator('agent_name')
    def validate_name(cls, v):
        return validate_agent_name(v)
```

**See:** `core/validators.py` for all validation functions and `tests/test_validators.py` for test coverage.

---

## Rate Limiting ✅ IMPLEMENTED

**Token bucket algorithm** with per-IP tracking.

### Configuration (.env)
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60    # Sustained rate
RATE_LIMIT_BURST=100         # Burst capacity
```

### How it works
- **Sustained rate:** 60 requests per minute (1/second)
- **Burst capacity:** 100 requests (allows bursts, then throttles)
- **Per-IP tracking:** Each client has separate bucket
- **Auto-cleanup:** Old buckets removed to prevent memory leaks

### Response when limited
```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "limit": 60,
  "window": "1 minute"
}
```
HTTP Status: `429 Too Many Requests`

**Implementation:** `core/rate_limiter.py` (token bucket) + middleware in `server.py`  
**Tests:** `tests/test_rate_limiting.py`

---

## HTTPS / TLS

### Local Development
HTTP is fine for localhost.

### Production
**Always use HTTPS**. Options:

**1. Reverse Proxy (Recommended)**
```nginx
# nginx.conf
server {
    listen 443 ssl;
    server_name api.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**2. Let's Encrypt (Free)**
```bash
sudo certbot --nginx -d api.yourdomain.com
```

**3. Uvicorn with SSL**
```python
uvicorn.run(
    "server:app",
    host="0.0.0.0",
    port=8080,
    ssl_keyfile="/path/to/key.pem",
    ssl_certfile="/path/to/cert.pem"
)
```

---

## Database Security

### PostgreSQL
```sql
-- Create dedicated user (don't use postgres superuser!)
CREATE USER supabrain_app WITH PASSWORD 'strong-password';
GRANT CONNECT ON DATABASE supabrain TO supabrain_app;
GRANT USAGE ON SCHEMA public TO supabrain_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO supabrain_app;

-- Restrict permissions
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
```

### Connection
```python
# Use environment variables, never hardcode
DATABASE_URL = os.getenv("DATABASE_URL")
# postgresql://supabrain_app:password@localhost/supabrain
```

---

## Monitoring & Logging

### Access Logs
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/access.log'),
        logging.StreamHandler()
    ]
)
```

### Security Events
```python
# Log failed auth attempts
logger.warning(f"Failed auth attempt from {request.client.host}")

# Log suspicious patterns
if len(content) > 10000:
    logger.warning(f"Oversized content from agent {agent_name}")
```

---

## Deployment Checklist

Before going live:

- [ ] Configure CORS (restrict origins)
- [ ] Add authentication (API key minimum)
- [ ] Enable HTTPS (Let's Encrypt or reverse proxy)
- [ ] Set up rate limiting
- [ ] Add input validation
- [ ] Create dedicated DB user
- [ ] Enable access logging
- [ ] Set up monitoring (uptime, errors)
- [ ] Backup strategy (pg_dump cron job)
- [ ] Security headers (CSP, HSTS, etc.)
- [ ] Review .env (no secrets in git!)

---

## Reporting Security Issues

Found a vulnerability?

**Do NOT open a public issue.**

Email: [your-security-email] (TODO)

Or submit via GitHub Security Advisory (private).

---

## Roadmap

**Planned security features:**

- [ ] API key authentication middleware
- [ ] Rate limiting with Redis backend
- [ ] Input sanitization library
- [ ] Audit log for all memory operations
- [ ] Agent-level access control (multi-tenant)
- [ ] Encryption at rest
- [ ] Security headers middleware
- [ ] Automated security scanning (Dependabot)

---

## Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)

---

**Remember**: Security is a journey, not a destination. Keep SupaBrain updated and follow best practices!
