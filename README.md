# 🔐 U-tec Gateway with Automatic Token Refresh

Enhanced U-tec Local Gateway for Home Assistant with automatic OAuth token refresh to eliminate manual re-authentication every few days.

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Home Assistant](https://img.shields.io/badge/home%20assistant-compatible-blue.svg)](https://www.home-assistant.io/)

---

## 🌟 Features

- ✅ **Automatic Token Refresh** - Tokens refresh automatically before expiration
- ✅ **Background Scheduler** - Monitors token status every 5 minutes
- ✅ **Smart Retry Logic** - Auto-retries failed API calls with fresh tokens
- ✅ **Persistent Storage** - Tokens survive container restarts
- ✅ **Web-Based Setup UI** - Easy step-by-step configuration
- ✅ **Device Control** - Test locks directly from the web interface
- ✅ **100% HA Compatible** - Works seamlessly with Home Assistant
- ✅ **Comprehensive Logging** - Detailed logs for troubleshooting

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose installed
- U-tec API credentials (Access Key, Secret Key, Redirect URI)
- U-tec account for authentication

### Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/uteclocal-HA.git
cd uteclocal-HA

# Start gateway
chmod +x deploy_docker.sh
./deploy_docker.sh

# Open web interface
open http://localhost:8000
```

---

## 📋 First-Time Setup (Step-by-Step)

### Step 1: Enter Your Credentials

Open `http://localhost:8000` in your browser.

Fill in the following in **Step 1**:

| Field | Value | Where to Get It |
|-------|-------|-----------------|
| **Access Key** | Your U-tec Client ID | U-tec Developer Portal |
| **Secret Key** | Your U-tec Client Secret | U-tec Developer Portal |
| **Redirect URI** | Your registered callback URL | What you set in U-tec Developer Portal |

**Example:**
```
Access Key: abc123xyz789
Secret Key: your-secret-key-here
Redirect URI: http://localhost:8000/callback
```

Click **"💾 Save Configuration & Continue"**

---

### Step 2: Authorize with U-tec

1. Click **"🚀 Open U-tec Login Page"**
2. A new tab opens to: `https://oauth.u-tec.com/login/auth...`
3. **Login** with your U-tec account username and password
4. Click **"Approve"** or **"Authorize"**
5. You'll be redirected to a page (the URL contains a code)

---

### Step 3: Complete Authentication

1. **Copy the entire URL** from your browser's address bar
   - Example: `https://your-site.com/callback?code=abc123xyz...`
2. **Paste** it into the text box in Step 3
3. Click **"🔑 Submit Code & Complete Setup"**
4. ✅ **Success!** Your gateway is now authenticated

---

### Step 4: Test Your Setup

1. Click **"📱 View My Devices"**
2. You should see your U-tec locks listed
3. Try the device controls:
   - **🔒 Lock** - Send lock command
   - **🔓 Unlock** - Send unlock command
   - **📊 Query Status** - Get current device status

---

## 🎯 Using the Gateway

### Web Interface

Access at: `http://localhost:8000`

**Main Sections:**
- **Setup Steps** - Initial configuration and OAuth
- **Device Management** - List devices and send commands
- **Advanced Options** - Token management, settings, logs

---

### API Endpoints

#### **Health Check**
```bash
curl http://localhost:8000/health
```
Returns: Token status, auto-refresh status

#### **List Devices**
```bash
curl http://localhost:8000/api/devices
```
Returns: All your U-tec devices

#### **Lock Device**
```bash
curl -X POST http://localhost:8000/api/lock \
  -H "Content-Type: application/json" \
  -d '{"id":"XX:XX:XX:XX:XX:XX"}'
```

#### **Unlock Device**
```bash
curl -X POST http://localhost:8000/api/unlock \
  -H "Content-Type: application/json" \
  -d '{"id":"XX:XX:XX:XX:XX:XX"}'
```

#### **Query Device Status**
```bash
curl -X POST http://localhost:8000/api/status \
  -H "Content-Type: application/json" \
  -d '{"id":"XX:XX:XX:XX:XX:XX"}'
```

#### **Manually Refresh Token**
```bash
curl -X POST http://localhost:8000/api/oauth/refresh
```

---

## 🏠 Home Assistant Integration

The gateway is fully compatible with Home Assistant's U-tec integration.

### Setup in Home Assistant

1. **Settings** → **Devices & Services**
2. **Add Integration** → Search "U-tec Local Gateway"
3. **Configure:**
   - Host: `http://localhost:8000` (or your gateway IP)
   - Leave API key blank (handled by gateway)
4. **Done!** Locks appear as entities

### Entities Created

- `lock.front_door` - Lock control
- `sensor.front_door_battery` - Battery level
- `sensor.front_door_status` - Lock status

### Automation Example

```yaml
automation:
  - alias: "Lock door at night"
    trigger:
      platform: time
      at: "22:00:00"
    action:
      service: lock.lock
      target:
        entity_id: lock.front_door
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file (optional):

```env
API_BASE_URL=https://api.u-tec.com
OAUTH_BASE_URL=https://oauth.u-tec.com
STATUS_POLL_INTERVAL=60
AUTO_REFRESH_ENABLED=true
REFRESH_BUFFER_MINUTES=5
```

### docker-compose.yml

```yaml
services:
  gateway:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - uteclocal-data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  uteclocal-data:
```

---

## 📊 Monitoring

### View Logs

**Via Web UI:**
- Go to Advanced Options → View Logs

**Via Docker:**
```bash
docker compose -p uteclocal logs -f gateway
```

### Check Status

```bash
# Container status
docker compose -p uteclocal ps

# Health check
curl http://localhost:8000/health | jq

# Token status
curl http://localhost:8000/api/config | jq '.token_status'
```

### Common Log Messages

✅ **Good:**
```
Token refreshed successfully
Gateway started with automatic token refresh enabled
Scheduled token refresh successful
```

❌ **Needs Attention:**
```
Token refresh failed
Error getting devices: 401
Authentication failed
```

---

## 🔄 Updating

### Update Gateway Code

```bash
cd uteclocal-HA

# Pull latest changes
git pull origin main

# Rebuild container
docker compose -p uteclocal up -d --build

# Verify update
curl http://localhost:8000/health
```

### Update Individual File

```bash
# Copy new gateway file
cp gateway_main_enhanced_FINAL.py gateway/main.py

# Rebuild
docker compose -p uteclocal up -d --build
```

**Your config and tokens are preserved!** They're stored in a Docker volume.

---

## 🆘 Troubleshooting

### "HTTP 500: Internal Server Error" when listing devices

**Causes:**
- Token expired or invalid
- Incorrect API endpoints
- Network connectivity issue

**Solutions:**
```bash
# 1. Check logs
docker compose -p uteclocal logs gateway | tail -50

# 2. Manually refresh token
curl -X POST http://localhost:8000/api/oauth/refresh

# 3. Restart gateway
docker compose -p uteclocal restart gateway

# 4. If still failing, re-do OAuth (Steps 1-3 in UI)
```

---

### "Not Found" when clicking OAuth button

**Cause:** Container not updated with new code

**Solution:**
```bash
cd uteclocal-HA
docker compose -p uteclocal up -d --build
```

---

### Tokens still expiring after a few days

**Check auto-refresh is enabled:**
```bash
curl http://localhost:8000/health | jq '.auto_refresh_enabled'
# Should return: true
```

**Check logs for refresh attempts:**
```bash
docker compose -p uteclocal logs gateway | grep -i refresh
```

**Enable if disabled:**
- Open web UI → Advanced Options
- Check "Enable automatic token refresh"
- Save Settings

---

### Device commands not working

**Test connectivity:**
```bash
# 1. List devices first
curl http://localhost:8000/api/devices

# 2. Try querying a specific device
curl -X POST http://localhost:8000/api/status \
  -H "Content-Type: application/json" \
  -d '{"id":"YOUR_DEVICE_MAC"}'

# 3. Check response for errors
```

**Common issues:**
- Wrong device MAC address
- Device offline
- Token needs refresh

---

### Port 8000 already in use

**Change port in docker-compose.yml:**
```yaml
ports:
  - "8080:8000"  # Changed to 8080
```

Then: `docker compose -p uteclocal up -d`

---

## 📁 File Structure

```
uteclocal-HA/
├── gateway/
│   ├── __init__.py
│   └── main.py              # Enhanced gateway code
├── custom_components/
│   └── uteclocal/           # Home Assistant integration
├── docs/                    # Documentation
├── Dockerfile               # Docker image config
├── docker-compose.yml       # Docker Compose setup
├── .dockerignore
├── .gitignore
├── requirements.txt         # Python dependencies (includes APScheduler)
├── deploy_docker.sh         # Automated installer
├── test_gateway.sh          # Testing script
├── const.py                 # Constants
├── hacs.json               # HACS compatibility
└── README.md               # This file
```

---

## 🔐 Security Notes

### What Gets Stored

The gateway stores in `/data/config.json`:
- Access Key & Secret Key (for API requests)
- OAuth tokens (access_token, refresh_token)
- Token expiration time
- Configuration settings

### Best Practices

- ✅ Use Docker volumes for persistent storage
- ✅ Never commit `config.json` to git
- ✅ Use `.gitignore` to exclude sensitive files
- ✅ Rotate credentials periodically
- ✅ Use HTTPS if accessing remotely
- ❌ Don't share your config.json
- ❌ Don't expose port 8000 to internet without authentication

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

Same as original uteclocal project.

---

## 🙏 Credits

- Original uteclocal gateway by [Wheresitat](https://github.com/Wheresitat/uteclocal-HA)
- Enhanced with automatic token refresh
- Built for the Home Assistant community

---

## 📞 Support

- **Issues:** https://github.com/YOUR_USERNAME/uteclocal-HA/issues
- **Discussions:** https://github.com/YOUR_USERNAME/uteclocal-HA/discussions
- **Documentation:** See `/docs` folder

---

## ✨ What Makes This Enhanced

### Before (Original)
- ❌ Manual token refresh every few days
- ❌ Requires Home Assistant reload
- ❌ Basic error handling
- ❌ No web UI for setup
- ❌ Limited logging

### After (Enhanced)
- ✅ Automatic token refresh
- ✅ No manual intervention needed
- ✅ Smart retry logic
- ✅ Beautiful setup UI
- ✅ Device testing interface
- ✅ Comprehensive logging
- ✅ Health monitoring
- ✅ Better error messages

---

## 🎊 Enjoy Hassle-Free Smart Lock Control!

No more authentication errors. No more manual re-authentication. Just reliable, automatic operation. 🔐✨

**Questions?** Open an issue or check the documentation!

**Working great?** Star the repository! ⭐
