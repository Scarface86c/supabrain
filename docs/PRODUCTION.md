# 🔧 Production Deployment Notes

## Critical Issues & Fixes

### Server Crash Loop (Fixed 2026-02-27)

**Problem:**
SupaBrain server crashed repeatedly in production due to auto-reload feature:
- `reload=True` in uvicorn caused watchfiles to monitor for changes
- Every log write triggered reload
- Reload → port conflict → crash → zombie process
- Crash loop made server unstable

**Symptoms:**
- Server process exists but port 8080 unresponsive
- Health check fails (connection refused)
- Zombie uvicorn reloader processes accumulate
- Multiple crashes per day (3+ observed)

**Root Cause:**
`server.py` had `reload=True` intended for development, running in production.

**Solution:**
```python
# server.py line 167
reload=False,  # Production: auto-reload disabled (fixes crash loop)
```

**Verification:**
```bash
# Check server is up
curl -sf http://localhost:8080/health

# Verify no watchfiles subprocess (confirms reload disabled)
ps aux | grep watchfiles  # Should return nothing

# Monitor for stability
tail -f /tmp/supabrain_*.log
```

**Prevention:**
- Always use `reload=False` in production
- Use systemd service for proper process management (see WORKER_README.md)
- Monitor health endpoint via heartbeat checks

---

## Best Practices

### Server Management

**Use systemd service (recommended):**
```bash
# Start
systemctl --user start supabrain.service

# Status
systemctl --user status supabrain.service

# Logs
journalctl --user -u supabrain.service -f
```

**Manual start (development only):**
```bash
cd ~/supabrain/core
source venv/bin/activate
python3 server.py  # Auto-detects environment
```

### Health Monitoring

Add to heartbeat checks (every 15 min):
```bash
curl -sf http://localhost:8080/health || echo "⚠️ SERVER DOWN"
```

Auto-recovery on failure:
```bash
systemctl --user restart supabrain.service
```

### Logs

Production logs location:
- `/tmp/supabrain_*.log` - rotating logs
- `journalctl --user -u supabrain.service` - systemd logs

Monitor for issues:
```bash
tail -f /tmp/supabrain_*.log | grep -i "error\|warn\|fail"
```

---

## Troubleshooting

### Server Won't Start

**Port already in use:**
```bash
# Find process using port 8080
lsof -ti:8080

# Kill it
kill -9 $(lsof -ti:8080)
```

**Zombie processes:**
```bash
# Kill all SupaBrain processes
pkill -9 -f "python3.*server.py"
pkill -9 -f "uvicorn.*supabrain"

# Clean restart
systemctl --user restart supabrain.service
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
systemctl status postgresql

# Verify connection
psql -U bibi -d supabrain -c "SELECT 1"

# Check .env configuration
cat ~/supabrain/core/.env | grep DATABASE
```

### Performance Issues

```bash
# Check memory usage
ps aux | grep python3 | grep server.py

# Check database size
psql -U bibi -d supabrain -c "SELECT pg_size_pretty(pg_database_size('supabrain'))"

# Check slow queries (if any)
tail -f /tmp/supabrain_*.log | grep "slow"
```

---

*Last updated: 2026-02-28*
