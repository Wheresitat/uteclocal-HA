# 🔐 U-tec Gateway with Automatic Token Refresh

Enhanced U-tec Local Gateway for Home Assistant with automatic OAuth token refresh and correct U-tec API integration.

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Home Assistant](https://img.shields.io/badge/home%20assistant-compatible-blue.svg)](https://www.home-assistant.io/)

---

## 🌟 What This Solves

**Problem:** U-tec tokens expire every few days, requiring manual re-authentication and Home Assistant reloads.

**Solution:** Automatic token refresh monitors expiration and refreshes tokens in the background - **set it up once, never touch it again!**

---

## ✨ Features

- ✅ **Automatic Token Refresh** - Tokens refresh 5 minutes before expiration
- ✅ **Background Scheduler** - Monitors token status every 5 minutes
- ✅ **Smart Retry Logic** - Auto-retries failed API calls with fresh tokens
- ✅ **Persistent Storage** - Tokens survive container restarts/rebuilds
- ✅ **Correct U-tec API Format** - Uses official API structure (header/payload)
- ✅ **Web-Based Setup UI** - Beautiful step-by-step OAuth configuration
- ✅ **Device Control UI** - Test locks directly from web interface
- ✅ **Home Assistant Ready** - Full integration support
- ✅ **Comprehensive Logging** - Detailed logs for troubleshooting

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose installed
- U-tec API credentials (Access Key, Secret Key, Redirect URI)
- U-tec account for authentication

### Installation

```bash
# Clone or download this repository
cd uteclocal-HA

# Make deploy script executable
chmod +x deploy_docker.sh

# Deploy gateway
./deploy_docker.sh

# Open web interface
open http://localhost:8000
```

---

## 📋 First-Time Setup (5 Minutes)

### Step 1: Configure API Credentials

Open `http://localhost:8000` (or `http://YOUR_SERVER_IP:8000`)

Fill in **Step 1** with your U-tec credentials:

| Field | Value | Where to Get It |
|-------|-------|-----------------|
| **Access Key** | Your Client ID | U-tec Developer Portal |
| **Secret Key** | Your Client Secret | U-tec Developer Portal |
| **Redirect URI** | Your callback URL | What you registered with U-tec |

**Click "💾 Save Configuration & Continue"**

---

### Step 2: Complete OAuth Authorization

1. **Click "🚀 Open U-tec Login Page"**
2. A new tab opens to U-tec's authorization page
3. **Login** with your U-tec account username and password
4. **Click "Approve"** to authorize access
5. You'll be redirected to a page with a code in the URL

---

### Step 3: Exchange Code for Tokens

1. **Copy the entire URL** from your browser's address bar after authorization
   - Example: `https://your-site.com/callback?code=abc123xyz...`
2. **Paste** it into the text box in Step 3
3. **Click "🔑 Submit Code & Complete Setup"**
4. ✅ **Success!** Authentication complete

---

### Step 4: Test Your Devices

1. **Click "📱 View My Devices"**
2. Your U-tec locks will be listed
3. **Test the controls:**
   - 🔒 Lock Device
   - 🔓 Unlock Device
   - 📊 Query Status

---

## 🏠 Home Assistant Integration

### Method 1: REST Integration (Simplest)

Add to `configuration.yaml`:

```yaml
# Lock/Unlock Commands
rest_command:
  lock_front_door:
    url: http://192.168.1.40:8000/api/lock
    method: POST
    content_type: 'application/json'
    payload: '{"id":"XX:XX:XX:XX:XX:XX"}'
  
  unlock_front_door:
    url: http://192.168.1.40:8000/api/unlock
    method: POST
    content_type: 'application/json'
    payload: '{"id":"XX:XX:XX:XX:XX:XX"}'

# Status Sensor
sensor:
  - platform: rest
    name: "Front Door Lock Status"
    resource: http://192.168.1.40:8000/api/status
    method: POST
    headers:
      Content-Type: application/json
    payload: '{"id":"XX:XX:XX:XX:XX:XX"}'
    value_template: >
      {{ value_json.payload.devices[0].capabilities['st.lock'].state.value }}
    scan_interval: 30

# Template Lock Entity
lock:
  - platform: template
    name: "Front Door"
    value_template: "{{ states('sensor.front_door_lock_status') == 'locked' }}"
    lock:
      service: rest_command.lock_front_door
    unlock:
      service: rest_command.unlock_front_door
```

Replace `XX:XX:XX:XX:XX:XX` with your actual device MAC address.

**Restart Home Assistant**, then you'll have:
- `lock.front_door` - Lock control
- `sensor.front_door_lock_status` - Current status

---

### Method 2: Custom Integration (If Available)

Check if a custom integration exists:

```bash
# Look in the repository
ls custom_components/uteclocal/
```

If present, copy to Home Assistant:

```bash
cp -r custom_components/uteclocal ~/.homeassistant/custom_components/
```

Then restart Home Assistant and add via UI:
- Settings → Devices & Services → Add Integration
- Search for "U-tec Local Gateway"
- Configure with gateway URL: `http://192.168.1.40:8000`

---

## 🔧 Gateway API Endpoints

The gateway provides these endpoints for Home Assistant:

### List All Devices
```bash
curl http://localhost:8000/api/devices
```

### Lock Device
```bash
curl -X POST http://localhost:8000/api/lock \
  -H "Content-Type: application/json" \
  -d '{"id":"XX:XX:XX:XX:XX:XX"}'
```

### Unlock Device
```bash
curl -X POST http://localhost:8000/api/unlock \
  -H "Content-Type: application/json" \
  -d '{"id":"XX:XX:XX:XX:XX:XX"}'
```

### Query Device Status
```bash
curl -X POST http://localhost:8000/api/status \
  -H "Content-Type: application/json" \
  -d '{"id":"XX:XX:XX:XX:XX:XX"}'
```

### Health Check
```bash
curl http://localhost:8000/health
```

Returns:
```json
{
  "status": "ok",
  "token_valid": true,
  "auto_refresh_enabled": true,
  "token_expires_at": "2026-01-26T02:55:23...",
  "scheduler_running": true
}
```

---

## 🔄 How Auto-Refresh Works

### Background Monitoring
- **Checks token every 5 minutes**
- **Refreshes 5 minutes before expiration**
- **Logs all refresh attempts**

### Automatic Retry
- If API call returns **401 (Unauthorized)**
- Gateway automatically refreshes token
- Retries the request with new token

### Persistent Storage
- Tokens stored in Docker volume `/data`
- Survives container restarts and rebuilds
- No manual re-authentication needed

### Example Logs
```
2026-01-19 03:55:23 - Token will expire at: 2026-01-26 02:55:23
2026-01-26 02:50:00 - Token expiring soon, attempting refresh...
2026-01-26 02:50:01 - Token refreshed successfully
2026-01-26 02:50:01 - New token expires at: 2026-02-02 02:50:01
```

---

## 📊 Monitoring

### View Logs
```bash
# All logs
docker compose -p uteclocal logs gateway -f

# Only refresh events
docker compose -p uteclocal logs gateway | grep -i refresh

# Last 50 lines
docker compose -p uteclocal logs gateway | tail -50
```

### Check Status
```bash
# Container status
docker compose -p uteclocal ps

# Health check
curl http://localhost:8000/health | jq

# Token expiration
curl http://localhost:8000/api/config | jq '.token_expires_at'
```

### Web UI
- Open `http://localhost:8000`
- View token status in Step 4
- Check logs in Advanced Options
- Monitor device responses

---

## 🔄 Updating

### Update Gateway Code

```bash
cd uteclocal-HA

# Pull latest changes (if using git)
git pull origin main

# Or copy new gateway file
cp gateway_main_FINAL_FIXED.py gateway/main.py

# Rebuild container
docker compose -p uteclocal up -d --build

# Verify update
curl http://localhost:8000/health
```

**Your config and tokens are preserved!** They're stored in a Docker volume.

---

## 🆘 Troubleshooting

### "HTTP 400" or Commands Not Working

**Cause:** Using old gateway code with incorrect API format

**Solution:**
```bash
# Make sure you have the latest version
cp gateway_main_FINAL_FIXED.py gateway/main.py
docker compose -p uteclocal up -d --build
```

### Token Expired Despite Auto-Refresh

**Check if auto-refresh is enabled:**
```bash
curl http://localhost:8000/health | jq '.auto_refresh_enabled'
# Should return: true
```

**Check logs for refresh attempts:**
```bash
docker compose -p uteclocal logs gateway | grep "refresh"
```

**Manually trigger refresh:**
```bash
curl -X POST http://localhost:8000/api/oauth/refresh
```

### Container Not Starting

**Check logs:**
```bash
docker compose -p uteclocal logs gateway
```

**Common issues:**
- Port 8000 already in use → Change port in `docker-compose.yml`
- Missing dependencies → Rebuild: `docker compose -p uteclocal up -d --build`

### Home Assistant Can't Connect

**Test gateway is accessible:**
```bash
curl http://YOUR_GATEWAY_IP:8000/health
```

**Check Home Assistant logs:**
```
Settings → System → Logs
Search for: "uteclocal" or "rest_command"
```

**Verify MAC address format:**
- Must be: `XX:XX:XX:XX:XX:XX` (uppercase, colons)
- Get from gateway device list

---

## 🔐 Security Best Practices

### What Gets Stored

In Docker volume `/data/config.json`:
- Access Key & Secret Key (for API requests)
- OAuth access_token & refresh_token
- Token expiration timestamp
- Gateway configuration

### Recommendations

✅ **DO:**
- Use `.gitignore` to exclude `config.json`
- Use Docker volumes for persistent storage
- Restrict network access to gateway if exposed
- Rotate credentials periodically

❌ **DON'T:**
- Commit `config.json` to version control
- Share your tokens or credentials
- Expose port 8000 to internet without authentication
- Delete the Docker volume (will lose tokens)

### Backup Configuration

```bash
# Backup tokens
docker exec uteclocal-gateway cat /data/config.json > config_backup.json

# Restore if needed
docker cp config_backup.json uteclocal-gateway:/data/config.json
docker compose -p uteclocal restart gateway
```

---

## 📁 File Structure

```
uteclocal-HA/
├── gateway/
│   ├── __init__.py
│   └── main.py              # Enhanced gateway with auto-refresh
├── custom_components/       # Home Assistant integration (if present)
│   └── uteclocal/
├── docs/                    # Documentation
├── Dockerfile               # Docker image configuration
├── docker-compose.yml       # Docker Compose setup
├── .dockerignore
├── .gitignore              # Protects config.json
├── requirements.txt        # Python dependencies (includes APScheduler)
├── deploy_docker.sh        # Automated installer
├── test_gateway.sh         # Testing script
└── README.md              # This file
```

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Test thoroughly with actual U-tec devices
4. Follow U-tec API documentation: https://doc.api.u-tec.com/
5. Submit a pull request

---

## 📚 Technical Details

### U-tec API Format

This gateway uses the official U-tec API format:

```json
{
  "header": {
    "namespace": "Uhome.Device",
    "name": "Discovery|Query|Command",
    "messageId": "uuid-v4",
    "payloadVersion": "1"
  },
  "payload": {
    // Command-specific data
  },
  "accessKey": "your-access-key",
  "secretKey": "your-secret-key"
}
```

### Token Refresh Flow

1. Background scheduler runs every 5 minutes
2. Checks: `token_expires_at - now() < 5 minutes`
3. If true, POST to `/token` endpoint with `refresh_token`
4. Receives new `access_token` and `refresh_token`
5. Updates config and saves to persistent storage
6. Logs success/failure

### Dependencies

- **FastAPI** - Web framework
- **httpx** - Async HTTP client
- **APScheduler** - Background task scheduler
- **pydantic** - Data validation
- **uvicorn** - ASGI server

---

## 📄 License

Same as original uteclocal project.

---

## 🙏 Credits

- Original uteclocal concept by [Wheresitat](https://github.com/Wheresitat/uteclocal)
- Enhanced with automatic token refresh
- U-tec API format based on official documentation: https://doc.api.u-tec.com/
- Built for the Home Assistant community

---

## 📞 Support

- **Issues:** Create an issue in this repository
- **Discussions:** Use GitHub Discussions
- **Documentation:** https://doc.api.u-tec.com/

---

## ✨ What Makes This Enhanced

### Before (Manual Re-auth Required)
- ❌ Token expires every few days
- ❌ Manual OAuth flow required
- ❌ Home Assistant reload needed
- ❌ Service interruptions
- ❌ Wrong API format (action/data structure)

### After (Fully Automated)
- ✅ Automatic token refresh
- ✅ One-time OAuth setup
- ✅ Zero maintenance required
- ✅ Continuous operation
- ✅ Correct API format (header/payload structure)
- ✅ Beautiful web UI for setup and testing
- ✅ Device control interface
- ✅ Comprehensive logging

---

## 🎊 Enjoy Hassle-Free Smart Lock Control!

Set it up once, never touch it again. The gateway handles everything automatically. 🔐✨

**Questions? Open an issue!**  
**Working perfectly? Star the repository! ⭐**

---

**Last Updated:** January 2026  
**API Version:** U-tec API v1 (header/payload format)  
**Gateway Version:** 1.5.0 (Auto-refresh + Correct API Format)
