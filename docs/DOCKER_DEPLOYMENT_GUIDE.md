# Docker Deployment Guide for Enhanced U-tec Gateway

## ✅ Docker Compatibility

The enhanced gateway with automatic token refresh is **fully compatible** with Docker and Docker Compose. All features work seamlessly in containers:

- ✅ Automatic token refresh
- ✅ Background scheduler 
- ✅ Persistent configuration
- ✅ Persistent logs
- ✅ Health checks
- ✅ Container restarts

---

## 📁 File Structure

Your uteclocal directory should look like this:

```
uteclocal/
├── Dockerfile                    # Updated for enhanced gateway
├── docker-compose.yml            # With persistent volume
├── .dockerignore                 # Optimized builds
├── requirements.txt              # With APScheduler
├── const.py                      # Constants file
├── gateway/
│   ├── __init__.py
│   └── main.py                   # Enhanced gateway code
├── custom_components/            # Home Assistant integration
│   └── uteclocal/
└── README.md
```

---

## 🚀 Quick Start (Docker)

### Step 1: Update Your Files

```bash
cd /path/to/uteclocal

# Backup existing files
mkdir -p backup_$(date +%Y%m%d)
cp gateway/main.py backup_$(date +%Y%m%d)/
cp requirements.txt backup_$(date +%Y%m%d)/
cp docker-compose.yml backup_$(date +%Y%m%d)/

# Replace with enhanced versions
cp gateway_main_enhanced.py gateway/main.py
cp requirements_enhanced.txt requirements.txt
cp Dockerfile ./
cp docker-compose.yml ./
cp .dockerignore ./
```

### Step 2: Deploy with Docker Compose

```bash
# Stop existing containers
docker compose -p uteclocal down

# Build and start with new code
docker compose -p uteclocal up -d --build

# Wait for gateway to start (about 10 seconds)
sleep 10

# Check health
curl http://localhost:8000/health
```

### Step 3: Verify

```bash
# Check container is running
docker compose -p uteclocal ps

# Should show:
# NAME                  STATUS          PORTS
# uteclocal-gateway     Up (healthy)    0.0.0.0:8000->8000/tcp

# View logs
docker compose -p uteclocal logs -f gateway

# Access web UI
open http://localhost:8000  # or visit in browser
```

---

## 🔧 Docker-Specific Features

### 1. Persistent Storage

Your tokens and configuration are stored in a Docker **named volume**:

```yaml
volumes:
  uteclocal-data:
    driver: local
```

This means:
- ✅ Config survives container restarts
- ✅ Config survives container rebuilds
- ✅ Config survives host reboots
- ✅ Tokens persist automatically

**Location inside container:** `/data/config.json` and `/data/gateway.log`

### 2. Health Checks

Docker automatically monitors gateway health:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

Check status:
```bash
docker compose -p uteclocal ps
# Shows "healthy" or "unhealthy"
```

### 3. Automatic Restart

Container automatically restarts if it crashes:

```yaml
restart: unless-stopped
```

### 4. Network Isolation

Gateway runs in its own network:

```yaml
networks:
  uteclocal-network:
    driver: bridge
```

---

## 📊 Managing the Docker Container

### View Logs

```bash
# Follow logs in real-time
docker compose -p uteclocal logs -f gateway

# View last 100 lines
docker compose -p uteclocal logs --tail 100 gateway

# Search for token refresh
docker compose -p uteclocal logs gateway | grep "refresh"

# Search for errors
docker compose -p uteclocal logs gateway | grep -i error
```

### Check Container Status

```bash
# List containers
docker compose -p uteclocal ps

# Detailed inspection
docker inspect uteclocal-gateway

# Check resource usage
docker stats uteclocal-gateway
```

### Restart Container

```bash
# Graceful restart (preserves data)
docker compose -p uteclocal restart gateway

# Full restart (stops then starts)
docker compose -p uteclocal down
docker compose -p uteclocal up -d
```

### Rebuild Container

```bash
# After code changes
docker compose -p uteclocal up -d --build

# Force complete rebuild
docker compose -p uteclocal build --no-cache
docker compose -p uteclocal up -d
```

### Access Container Shell

```bash
# Interactive shell
docker exec -it uteclocal-gateway /bin/bash

# Run single command
docker exec uteclocal-gateway ls -la /data

# View config file
docker exec uteclocal-gateway cat /data/config.json
```

---

## 💾 Data Persistence

### Backup Configuration

```bash
# Backup config.json
docker cp uteclocal-gateway:/data/config.json ./config_backup_$(date +%Y%m%d).json

# Backup logs
docker cp uteclocal-gateway:/data/gateway.log ./gateway_backup_$(date +%Y%m%d).log

# Backup entire data directory
docker cp uteclocal-gateway:/data ./data_backup_$(date +%Y%m%d)
```

### Restore Configuration

```bash
# Restore config.json
docker cp ./config_backup.json uteclocal-gateway:/data/config.json

# Restart to apply
docker compose -p uteclocal restart gateway
```

### View Volume Data

```bash
# List volumes
docker volume ls | grep uteclocal

# Inspect volume
docker volume inspect uteclocal_uteclocal-data

# Volume location on host (Linux)
# Usually: /var/lib/docker/volumes/uteclocal_uteclocal-data/_data
```

### Backup Volume (Complete)

```bash
# Create volume backup
docker run --rm \
  -v uteclocal_uteclocal-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/uteclocal-volume-backup.tar.gz /data

# Restore volume backup
docker run --rm \
  -v uteclocal_uteclocal-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/uteclocal-volume-backup.tar.gz -C /
```

---

## 🌐 Networking

### Access from Home Assistant

If Home Assistant is also in Docker:

**Option 1: Same Docker network**
```yaml
# In HA docker-compose.yml, add:
networks:
  - uteclocal-network

# Then use: http://uteclocal-gateway:8000
```

**Option 2: Host network**
```yaml
# In gateway docker-compose.yml:
network_mode: host

# Or in command:
docker run --network host ...

# Then use: http://localhost:8000
```

**Option 3: Docker bridge (default)**
```bash
# Use host's IP address
http://192.168.1.X:8000

# Or use host.docker.internal (Mac/Windows)
http://host.docker.internal:8000
```

### Custom Port

Change the exposed port in `docker-compose.yml`:

```yaml
ports:
  - "8080:8000"  # Changed from 8000:8000
```

Then access at: `http://localhost:8080`

### Multiple Hosts

To allow access from other machines on your network:

```yaml
ports:
  - "0.0.0.0:8000:8000"  # Already default
```

Make sure firewall allows port 8000.

---

## 🔍 Troubleshooting Docker Issues

### Issue: Container won't start

```bash
# Check logs for errors
docker compose -p uteclocal logs gateway

# Common causes:
# 1. Port 8000 already in use
netstat -tuln | grep 8000
# Solution: Change port in docker-compose.yml

# 2. Volume permission issues
docker volume inspect uteclocal_uteclocal-data
# Solution: Recreate volume
docker compose -p uteclocal down -v
docker compose -p uteclocal up -d

# 3. Build errors
docker compose -p uteclocal build --no-cache
```

### Issue: Gateway unhealthy

```bash
# Check health status
docker inspect uteclocal-gateway | grep -A 10 Health

# Check if service is responding
docker exec uteclocal-gateway curl -f http://localhost:8000/health

# Check if Python is running
docker exec uteclocal-gateway ps aux | grep python

# Restart if needed
docker compose -p uteclocal restart gateway
```

### Issue: Config not persisting

```bash
# Verify volume is mounted
docker inspect uteclocal-gateway | grep -A 5 Mounts

# Should show:
# "Destination": "/data"
# "Source": "/var/lib/docker/volumes/uteclocal_uteclocal-data/_data"

# Check files exist in volume
docker exec uteclocal-gateway ls -la /data

# If missing, volume not properly mounted
# Solution: Recreate with volume
docker compose -p uteclocal down
docker compose -p uteclocal up -d
```

### Issue: Can't access from Home Assistant

```bash
# Test from HA container
docker exec homeassistant curl http://uteclocal-gateway:8000/health

# If fails, check network
docker network inspect uteclocal_uteclocal-network

# Verify both containers are on same network
docker inspect homeassistant | grep NetworkMode
docker inspect uteclocal-gateway | grep NetworkMode

# Solution: Add HA to gateway network or vice versa
```

### Issue: High memory/CPU usage

```bash
# Check resource usage
docker stats uteclocal-gateway

# View processes inside container
docker exec uteclocal-gateway ps aux

# Check scheduler jobs
docker exec uteclocal-gateway ps aux | grep python

# If too high:
# 1. Increase poll interval (default 60s)
# 2. Reduce refresh frequency (default 5 min)
# Access config via web UI or API
```

---

## 🔄 Update Workflow

### Regular Updates

```bash
# 1. Pull latest code
git pull origin main

# 2. Rebuild and restart
docker compose -p uteclocal up -d --build

# 3. Verify health
curl http://localhost:8000/health

# Config and tokens are preserved automatically! ✅
```

### Clean Update (if issues)

```bash
# 1. Backup data
docker cp uteclocal-gateway:/data ./data_backup

# 2. Stop and remove containers (but keep volume)
docker compose -p uteclocal down

# 3. Remove old image
docker images | grep uteclocal
docker rmi uteclocal-gateway

# 4. Rebuild from scratch
docker compose -p uteclocal build --no-cache
docker compose -p uteclocal up -d

# 5. Restore data if needed
docker cp ./data_backup/config.json uteclocal-gateway:/data/
```

### Reset Everything (nuclear option)

```bash
# ⚠️  WARNING: This deletes all config and tokens!

# Stop and remove everything including volumes
docker compose -p uteclocal down -v

# Remove images
docker rmi $(docker images | grep uteclocal | awk '{print $3}')

# Start fresh
docker compose -p uteclocal up -d --build

# You'll need to re-do OAuth setup
```

---

## 🧪 Testing Docker Deployment

Run the test script:

```bash
# From host machine
./test_gateway.sh

# Or manually test
curl http://localhost:8000/health
curl http://localhost:8000/api/config
curl http://localhost:8000/api/devices
```

Expected results:
- ✅ Gateway accessible on port 8000
- ✅ Health check returns "ok"
- ✅ Token status shows valid/expired
- ✅ Auto-refresh enabled
- ✅ Config persists after restart

---

## 🐳 Docker Compose Commands Cheat Sheet

```bash
# Start services
docker compose -p uteclocal up -d

# Stop services (preserves data)
docker compose -p uteclocal down

# Stop and remove volumes (⚠️  deletes data)
docker compose -p uteclocal down -v

# Restart services
docker compose -p uteclocal restart

# View logs
docker compose -p uteclocal logs -f

# View logs for specific time
docker compose -p uteclocal logs --since 30m

# Check status
docker compose -p uteclocal ps

# Rebuild
docker compose -p uteclocal build

# Rebuild without cache
docker compose -p uteclocal build --no-cache

# Update and restart
docker compose -p uteclocal up -d --build

# Scale (not useful for gateway, but FYI)
docker compose -p uteclocal up -d --scale gateway=1

# Execute command
docker compose -p uteclocal exec gateway bash

# View processes
docker compose -p uteclocal top
```

---

## 📋 Environment Variables (Optional)

You can add these to `docker-compose.yml`:

```yaml
environment:
  - TZ=America/New_York           # Your timezone
  - LOG_LEVEL=INFO                # DEBUG, INFO, WARNING, ERROR
  - AUTO_REFRESH_ENABLED=true     # Enable auto-refresh
  - REFRESH_BUFFER_MINUTES=5      # Minutes before expiry
  - STATUS_POLL_INTERVAL=60       # Seconds between polls
```

Or use a `.env` file:

```bash
# .env file
TZ=America/New_York
LOG_LEVEL=INFO
AUTO_REFRESH_ENABLED=true
```

Then reference in `docker-compose.yml`:

```yaml
environment:
  - TZ=${TZ}
  - LOG_LEVEL=${LOG_LEVEL}
```

---

## 🎯 Summary: Docker Deployment

The enhanced gateway works perfectly in Docker with:

✅ **Persistent storage** via named volumes  
✅ **Automatic health checks** every 30 seconds  
✅ **Auto-restart** on failure  
✅ **Token refresh** works in containers  
✅ **Background scheduler** runs properly  
✅ **Zero downtime updates** (just rebuild)  
✅ **Easy backup/restore** of config and tokens  

Your existing Docker setup is fully compatible. Just update the files and rebuild!

### Minimal Update Steps:

```bash
cd uteclocal
cp gateway_main_enhanced.py gateway/main.py
echo "APScheduler==3.10.4" >> requirements.txt
docker compose -p uteclocal up -d --build
```

That's it! Your Docker deployment will now have automatic token refresh. 🎉
