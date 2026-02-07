# 🔒 Security Guide

**Important**: SupaBrain is currently in ALPHA. Follow these guidelines for secure deployment.

---

## Quick Security Checklist

### Development (Local)
- ✅ Default CORS allows all origins (`*`)
- ✅ No authentication required
- ✅ Runs on localhost:8080

### Production (Public)
- ⚠️ **Configure CORS** - Restrict allowed origins
- ⚠️ **Add authentication** - API key or OAuth
- ⚠️ **Use HTTPS** - Encrypt all traffic
- ⚠️ **Input validation** - Sanitize all inputs
- ⚠️ **Rate limiting** - Prevent abuse
- ⚠️ **Monitor logs** - Track suspicious activity

---

## CORS Configuration

### Current (Development)
```python
# core/server.py
allow_origins=["*"]  # ⚠️ INSECURE - allows any website
```

### Production Configuration

**Option 1: Environment Variable**
```bash
# .env
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

**Option 2: Config File**
```python
# core/config.py
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# core/server.py
from config import ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "Authorization"],
)
```

---

## Authentication

### API Key (Simple)

**1. Generate key**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**2. Add to .env**
```bash
API_KEY=your-secret-key-here
REQUIRE_AUTH=true
```

**3. Implement middleware** (TODO - not yet implemented)
```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
```

**4. Use in requests**
```bash
curl -H "X-API-Key: your-secret-key-here" \
  http://localhost:8080/api/v1/stats?agent_name=YourAgent
```

---

## Input Validation

### Current Status
- ⚠️ Minimal validation
- ⚠️ No SQL injection protection on agent_name
- ⚠️ No length limits on content

### Recommended
```python
import re
from pydantic import validator

class MemoryCreate(BaseModel):
    content: str
    agent_name: str
    
    @validator('agent_name')
    def validate_agent_name(cls, v):
        # Only alphanumeric, underscore, hyphen
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid agent name format')
        if len(v) > 50:
            raise ValueError('Agent name too long')
        return v
    
    @validator('content')
    def validate_content(cls, v):
        if len(v) > 10000:  # 10KB limit
            raise ValueError('Content too long')
        return v
```

---

## Rate Limiting

**Not yet implemented** - Recommended for production:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/v1/remember")
@limiter.limit("10/minute")
async def remember(request: Request, memory: MemoryCreate):
    ...
```

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
