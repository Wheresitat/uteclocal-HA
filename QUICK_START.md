# 📋 STEP-BY-STEP INSTALLATION GUIDE

## What to Do With These Files

Follow these simple steps to install the enhanced gateway with automatic token refresh.

---

## 🎯 Prerequisites

Before you start, make sure you have:
- ✅ The uteclocal repository already installed on your system
- ✅ Docker and Docker Compose installed
- ✅ The gateway currently working (or ready to set up)

---

## 📥 STEP 1: Download All Files

You should have downloaded these 11 files:

**Core Files (REQUIRED):**
1. `gateway_main_enhanced.py`
2. `requirements_enhanced.txt`
3. `Dockerfile`
4. `docker-compose.yml`
5. `.dockerignore`

**Scripts:**
6. `deploy_docker.sh` (automated installer - recommended)

**Documentation (for reference):**
7. `README_ENHANCED.md`
8. `DOCKER_DEPLOYMENT_GUIDE.md`
9. `DOCKER_ARCHITECTURE.md`
10. `IMPLEMENTATION_GUIDE.md`
11. `test_gateway.sh`

---

## 📂 STEP 2: Navigate to Your uteclocal Directory

Open a terminal and go to where you have uteclocal installed:

```bash
cd /path/to/uteclocal
```

For example:
```bash
cd ~/uteclocal
# or
cd /home/username/uteclocal
# or
cd /opt/uteclocal
```

**To find your uteclocal directory:**
```bash
# Search for it
find ~ -name "docker-compose.yml" -path "*/uteclocal/*" 2>/dev/null

# Or if you know you're running the container
docker inspect uteclocal-gateway | grep Source
```

---

## 📋 STEP 3: Copy Files to uteclocal Directory

Copy all the downloaded files into your uteclocal directory.

**If you downloaded to ~/Downloads:**
```bash
cd /path/to/uteclocal

# Copy the files
cp ~/Downloads/gateway_main_enhanced.py ./
cp ~/Downloads/requirements_enhanced.txt ./
cp ~/Downloads/Dockerfile ./
cp ~/Downloads/docker-compose.yml ./
cp ~/Downloads/.dockerignore ./
cp ~/Downloads/deploy_docker.sh ./
cp ~/Downloads/*.md ./
cp ~/Downloads/*.sh ./
```

**Or if files are in a different location:**
```bash
cp /path/to/downloaded/files/* /path/to/uteclocal/
```

Your directory should now look like:
```
uteclocal/
├── gateway_main_enhanced.py        ← NEW
├── requirements_enhanced.txt       ← NEW
├── Dockerfile                      ← NEW or REPLACED
├── docker-compose.yml              ← NEW or REPLACED
├── .dockerignore                   ← NEW
├── deploy_docker.sh                ← NEW
├── test_gateway.sh                 ← NEW
├── *.md files                      ← NEW (documentation)
├── gateway/                        ← EXISTING
│   ├── __init__.py
│   └── main.py
├── custom_components/              ← EXISTING
│   └── uteclocal/
├── requirements.txt                ← EXISTING
└── const.py                        ← EXISTING
```

---

## 🚀 STEP 4: Run the Automated Installer

Now run the deployment script that does everything for you:

```bash
# Make the script executable
chmod +x deploy_docker.sh

# Run it
./deploy_docker.sh
```

**What this script does automatically:**
1. ✅ Backs up your existing files
2. ✅ Backs up your current config from the running container
3. ✅ Replaces `gateway/main.py` with the enhanced version
4. ✅ Updates `requirements.txt` to add APScheduler
5. ✅ Stops the old container
6. ✅ Rebuilds with the new code
7. ✅ Starts the enhanced container
8. ✅ Tests that it's working

**The script will show you progress messages like:**
```
================================================
U-tec Gateway - Docker Deployment
Enhanced with Automatic Token Refresh
================================================

✓ Docker and Docker Compose found
✓ Backup created in backup_20260113_143022
✓ Gateway code updated
✓ Added APScheduler to requirements
✓ Containers stopped
✓ Gateway container started
✓ Gateway is healthy and ready!
✓ Gateway is accessible on http://localhost:8000

✅ Docker Deployment Complete!
```

---

## ✅ STEP 5: Verify It's Working

### Option A: Use the Test Script (Recommended)
```bash
chmod +x test_gateway.sh
./test_gateway.sh
```

This will run a comprehensive test suite and tell you if everything is working.

### Option B: Manual Tests
```bash
# Test 1: Check if gateway is responding
curl http://localhost:8000/health

# Should return:
# {
#   "status": "ok",
#   "token_valid": true,
#   "auto_refresh_enabled": true
# }

# Test 2: Check container is running
docker compose -p uteclocal ps

# Should show:
# NAME                STATUS          PORTS
# uteclocal-gateway   Up (healthy)    0.0.0.0:8000->8000/tcp

# Test 3: Check logs
docker compose -p uteclocal logs -f gateway

# Should show:
# Gateway started with automatic token refresh enabled
# Token will expire at: [timestamp]
```

### Option C: Web UI
Open your browser and go to:
```
http://localhost:8000
```

You should see the gateway web interface with a "Token Status" section showing auto-refresh is enabled.

---

## 🔧 STEP 6: Configure OAuth (If Needed)

If this is a **fresh installation** or your tokens have expired:

1. **Open the web UI:** `http://localhost:8000`

2. **Enter your U-tec API credentials:**
   - API Base URL: `https://api.u-tec.com`
   - OAuth Base URL: `https://oauth.u-tec.com`
   - Action Path: `/action`
   - Access Key: (your key)
   - Secret Key: (your key)
   - Scope: `openapi`
   - Redirect URI: (the one you registered)

3. **Click "Save"** then **"Start OAuth"**

4. **Approve in browser** - You'll be redirected to U-tec's authorization page

5. **Copy the redirect URL** after approving

6. **Paste into "OAuth Callback"** section and click **"Extract Code"**

7. **Click "Exchange Code"** - The gateway will get your tokens

8. **Verify:** Token Status should now show "✅ Valid"

**If you already have tokens configured:** The deployment script backed up and restored your config, so you don't need to do anything!

---

## 🏠 STEP 7: Verify Home Assistant Still Works

Your Home Assistant integration should continue working without any changes:

1. **Go to Home Assistant:** Settings → Devices & Services

2. **Find "U-tec Local Gateway"** - Should show "Connected"

3. **Test lock control:**
   - Try locking/unlocking from HA dashboard
   - Should work normally

4. **No configuration needed!** The integration already points to `http://localhost:8000` and will benefit from auto-refresh automatically.

---

## 🎉 You're Done!

Your gateway now has **automatic token refresh** enabled!

### What happens now:

✅ **Every 5 minutes:** Gateway checks if token is expiring  
✅ **Before expiration:** Automatically refreshes the token  
✅ **On API errors:** Auto-retries with fresh token  
✅ **Your Home Assistant:** Continues working seamlessly  
✅ **You never need to:** Manually re-authenticate again!

---

## 📊 Monitoring (Optional)

### Watch the logs to see auto-refresh in action:
```bash
docker compose -p uteclocal logs -f gateway | grep refresh
```

You'll see messages like:
```
Token will expire at: 2026-01-15 10:30:00
Scheduled token refresh triggered
Access token refreshed successfully
```

### Check token status anytime:
```bash
curl http://localhost:8000/health
```

### View in web UI:
Open `http://localhost:8000` and check the "Token Status" section

---

## ❓ Troubleshooting

### Issue: "deploy_docker.sh: command not found"

**Solution:**
```bash
# Make sure you're in the right directory
pwd
# Should show /path/to/uteclocal

# Make script executable
chmod +x deploy_docker.sh

# Run with explicit path
./deploy_docker.sh
```

### Issue: "docker compose: command not found"

**Solution:**
```bash
# Try with hyphen (older Docker versions)
docker-compose -p uteclocal ps

# Or install Docker Compose
# On Ubuntu/Debian:
sudo apt-get install docker-compose

# On Mac:
brew install docker-compose
```

### Issue: Gateway not accessible at localhost:8000

**Solution:**
```bash
# Check if container is running
docker ps | grep uteclocal

# Check logs for errors
docker compose -p uteclocal logs gateway

# Try restarting
docker compose -p uteclocal restart gateway
```

### Issue: "Port 8000 already in use"

**Solution:**
```bash
# Find what's using port 8000
sudo netstat -tlnp | grep 8000
# or
sudo lsof -i :8000

# Kill the process or change the port
# Edit docker-compose.yml:
# ports:
#   - "8080:8000"  # Changed to 8080

# Then rebuild
docker compose -p uteclocal up -d --build
```

### Issue: Token still expires after a few days

**Solution:**
```bash
# Check if auto-refresh is enabled
curl http://localhost:8000/health | jq '.auto_refresh_enabled'

# Should return: true

# Check logs for refresh attempts
docker compose -p uteclocal logs gateway | grep -i refresh

# If no refresh attempts, check scheduler is running
docker exec uteclocal-gateway ps aux | grep python
```

### Need More Help?

1. **Check the guides:**
   - Read `DOCKER_DEPLOYMENT_GUIDE.md` for detailed Docker info
   - Read `IMPLEMENTATION_GUIDE.md` for troubleshooting

2. **Check logs:**
   ```bash
   docker compose -p uteclocal logs --tail 100 gateway
   ```

3. **Restart from scratch:**
   ```bash
   # Stop everything
   docker compose -p uteclocal down
   
   # Rebuild
   docker compose -p uteclocal up -d --build
   
   # Test
   curl http://localhost:8000/health
   ```

---

## 📝 Quick Reference

### Useful Commands

```bash
# Start gateway
docker compose -p uteclocal up -d

# Stop gateway (preserves config)
docker compose -p uteclocal down

# Restart gateway
docker compose -p uteclocal restart gateway

# View logs
docker compose -p uteclocal logs -f gateway

# Check status
docker compose -p uteclocal ps

# Test health
curl http://localhost:8000/health

# Backup config
docker cp uteclocal-gateway:/data/config.json ./config_backup.json

# Update after changes
docker compose -p uteclocal up -d --build
```

### Important URLs

- **Gateway Web UI:** http://localhost:8000
- **Health Check:** http://localhost:8000/health
- **API Config:** http://localhost:8000/api/config
- **Logs:** http://localhost:8000/logs

---

## 🎊 Summary

**What you did:**
1. Downloaded the enhanced gateway files
2. Copied them to your uteclocal directory
3. Ran the deployment script
4. Verified everything works

**What you got:**
- ✅ Automatic token refresh every few hours
- ✅ No more manual re-authentication needed
- ✅ Home Assistant continues working seamlessly
- ✅ Better logging and monitoring
- ✅ More reliable operation

**Enjoy your hassle-free smart lock control!** 🔐✨
