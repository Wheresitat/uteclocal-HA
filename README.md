# 🔐 U-tec Local Gateway with Auto-Refresh

Enhanced U-tec Local Gateway for Home Assistant with automatic OAuth token refresh and complete Home Assistant integration.

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Home Assistant](https://img.shields.io/badge/home%20assistant-compatible-blue.svg)](https://www.home-assistant.io/)
[![HACS](https://img.shields.io/badge/HACS-Compatible-brightgreen.svg)](https://github.com/hacs/integration)

---

## 🌟 Features

### Gateway
- ✅ **Automatic Token Refresh** - Tokens refresh 5 minutes before expiration
- ✅ **Background Scheduler** - Monitors token status every 5 minutes
- ✅ **Smart Retry Logic** - Auto-retries failed API calls with fresh tokens
- ✅ **Persistent Storage** - Tokens survive container restarts/rebuilds
- ✅ **Correct U-tec API Format** - Uses official API structure (header/payload)
- ✅ **Web-Based Setup UI** - Beautiful step-by-step OAuth configuration
- ✅ **Device Control UI** - Test locks directly from web interface

### Home Assistant Integration
- ✅ **Lock Control** - Lock/unlock from Home Assistant
- ✅ **Real-time Status** - Lock state updates every 30 seconds
- ✅ **Battery Monitoring** - Track battery levels (0-100%)
- ✅ **Health Check** - Online/Offline status sensor
- ✅ **HACS Compatible** - Easy installation via HACS
- ✅ **Automatic Updates** - Status refreshes after commands
- ✅ **Device Info** - Proper device registry with manufacturer/model

---

## 🎯 What This Solves

**Problem:** 
- U-tec tokens expire every few days requiring manual re-authentication
- No native Home Assistant integration
- Complex API format requires custom gateway

**Solution:** 
- Set up OAuth once, tokens auto-refresh forever
- Full Home Assistant integration with lock, battery, and status entities
- Gateway handles all API communication

---

## 📋 Prerequisites

- Docker & Docker Compose installed
- U-tec API credentials (Access Key, Secret Key, Redirect URI)
- U-tec account for authentication
- Home Assistant (for integration)

---

## 🚀 Quick Start

### Part 1: Deploy Gateway

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/uteclocal-HA.git
cd uteclocal-HA

# Deploy gateway
chmod +x deploy_docker.sh
./deploy_docker.sh

# Gateway runs on http://localhost:8000
```

### Part 2: Configure OAuth

1. **Open:** `http://localhost:8000` (or `http://YOUR_SERVER_IP:8000`)

2. **Step 1 - Enter Credentials:**
   - Access Key (Client ID from U-tec Developer Portal)
   - Secret Key (Client Secret)
   - Redirect URI (callback URL)
   - Click "💾 Save Configuration & Continue"

3. **Step 2 - Authorize:**
   - Click "🚀 Open U-tec Login Page"
   - Login with U-tec username/password
   - Click "Approve"

4. **Step 3 - Exchange Code:**
   - Copy the redirect URL from browser
   - Paste into Step 3
   - Click "🔑 Submit Code & Complete Setup"

5. **Step 4 - Test:**
   - Click "📱 View My Devices"
   - Your locks appear!

### Part 3: Install Home Assistant Integration

#### Via HACS (Recommended)

1. **HACS → Integrations → Custom Repositories**
2. **Add:** `https://github.com/YOUR_USERNAME/uteclocal-HA`
3. **Category:** Integration
4. **Install** "U-tec Local Gateway"
5. **Restart** Home Assistant

#### Manual Installation

```bash
cd ~/.homeassistant/custom_components/
git clone https://github.com/YOUR_USERNAME/uteclocal-HA.git
cp -r uteclocal-HA/custom_components/uteclocal ./
ha core restart
```

### Part 4: Add Integration to Home Assistant

1. **Settings → Devices & Services → Add Integration**
2. **Search:** "U-tec Local Gateway"
3. **Enter Gateway URL:** `http://192.168.1.40:8000` (or your gateway IP)
4. **Done!** Entities appear immediately

---

## 📱 Home Assistant Entities

For each lock, you get:

### Lock Entity
```
lock.office_door_lock
State: Locked / Unlocked
Actions: Lock, Unlock
Updates: Every 30 seconds + after commands
```

### Battery Sensor
```
sensor.office_door_lock_battery
State: 0-100%
Conversion: 5→100%, 4→80%, 3→60%, 2→40%, 1→20%, 0→0%
Device Class: battery
Icon: Shows charge level
```

### Health Status Sensor
```
sensor.office_door_lock_status
State: Online / Offline
Icon: Changes based on status
Updates: Every 30 seconds
```

---

## 🎨 Example Automations

### Lock at Night
```yaml
automation:
  - alias: "Lock office at night"
    trigger:
      platform: time
      at: "22:00:00"
    condition:
      - condition: state
        entity_id: sensor.office_door_lock_status
        state: "Online"
    action:
      - service: lock.lock
        target:
          entity_id: lock.office_door_lock
```

### Low Battery Alert
```yaml
automation:
  - alias: "Office lock low battery"
    trigger:
      - platform: numeric_state
        entity_id: sensor.office_door_lock_battery
        below: 40
    action:
      - service: notify.mobile_app
        data:
          message: "Office door lock battery at {{ states('sensor.office_door_lock_battery') }}%"
```

### Offline Alert
```yaml
automation:
  - alias: "Office lock offline"
    trigger:
      - platform: state
        entity_id: sensor.office_door_lock_status
        to: "Offline"
        for: "00:05:00"
    action:
      - service: notify.mobile_app
        data:
          message: "Office door lock is offline! Check battery or connection."
```

### Auto-Lock After Opening
```yaml
automation:
  - alias: "Auto-lock after 5 minutes"
    trigger:
      - platform: state
        entity_id: lock.office_door_lock
        to: "unlocked"
        for: "00:05:00"
    action:
      - service: lock.lock
        target:
          entity_id: lock.office_door_lock
      - service: notify.mobile_app
        data:
          message: "Office door auto-locked after 5 minutes"
```

---

## 🔧 Gateway API Endpoints

The gateway provides these endpoints:

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

### Refresh Token Manually
```bash
curl -X POST http://localhost:8000/api/oauth/refresh
```

---

## 🔄 How Auto-Refresh Works

### Background Monitoring
- Checks token every 5 minutes
- Refreshes 5 minutes before expiration
- Logs all refresh attempts

### Automatic Retry
- If API call returns 401 (Unauthorized)
- Gateway automatically refreshes token
- Retries the request with new token

### Persistent Storage
- Tokens stored in Docker volume `/data`
- Survives container restarts and rebuilds
- No manual re-authentication needed

### Example Logs
```
2026-01-19 03:55:23 - Token expires at: 2026-01-26 02:55:23
2026-01-26 02:50:00 - Token expiring soon, refreshing...
2026-01-26 02:50:01 - Token refreshed successfully
2026-01-26 02:50:01 - New token expires at: 2026-02-02 02:50:01
```

---

## 📊 Monitoring

### View Gateway Logs
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

### Home Assistant Logs
```
Settings → System → Logs
Search: "uteclocal"
```

Enable debug logging:
```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.uteclocal: debug
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

**Your config and tokens are preserved!**

### Update Home Assistant Integration

#### Via HACS:
1. HACS → Integrations → U-tec Local Gateway → Redownload
2. Restart Home Assistant

#### Manually:
```bash
cd uteclocal-HA
git pull origin main
cp -r custom_components/uteclocal ~/.homeassistant/custom_components/
ha core restart
```

---

## 🆘 Troubleshooting

### Gateway Issues

#### Token Expired Despite Auto-Refresh

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

#### Container Not Starting

**Check logs:**
```bash
docker compose -p uteclocal logs gateway
```

**Common issues:**
- Port 8000 in use → Change port in `docker-compose.yml`
- Missing dependencies → Rebuild: `docker compose -p uteclocal up -d --build`

#### "HTTP 400" Errors

**Cause:** Using old gateway code

**Solution:**
```bash
cd uteclocal-HA
git pull origin main
cp gateway_main_FINAL_FIXED.py gateway/main.py
docker compose -p uteclocal up -d --build
```

---

### Home Assistant Issues

#### No Entities Appear

**Check integration installed:**
```bash
ls ~/.homeassistant/custom_components/uteclocal/
# Should show: __init__.py, config_flow.py, lock.py, sensor.py, etc.
```

**Check gateway reachable:**
```bash
curl http://YOUR_GATEWAY_IP:8000/api/devices
```

**Enable debug logging:**
```yaml
logger:
  logs:
    custom_components.uteclocal: debug
```

Check logs: Settings → System → Logs → Search "uteclocal"

#### Lock Status Not Updating

**Wait 2-3 seconds** after locking/unlocking for status to refresh.

**Check if API returns correct state:**
```bash
curl -X POST http://localhost:8000/api/status \
  -H "Content-Type: application/json" \
  -d '{"id":"YOUR:MAC:ADDRESS"}' | jq
```

**Verify coordinator updates:**
Check logs for: `Lock states for ... : [... 'value': 'Locked']`

#### Battery Shows "Unknown"

**Check device status includes battery:**
```bash
curl -X POST http://localhost:8000/api/status \
  -H "Content-Type: application/json" \
  -d '{"id":"YOUR:MAC:ADDRESS"}' | jq '.payload.devices[0].states[] | select(.capability == "st.batteryLevel")'
```

Should return battery level (0-5).

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
- Restrict network access to gateway if exposed externally
- Rotate credentials periodically
- Use HTTPS if exposing gateway to internet

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

## 📁 Repository Structure

```
uteclocal-HA/
├── hacs.json                      # HACS configuration
├── info.md                        # HACS info page
├── README.md                      # This file
├── custom_components/             # Home Assistant integration
│   └── uteclocal/
│       ├── __init__.py           # Coordinator
│       ├── config_flow.py        # UI configuration
│       ├── lock.py               # Lock entities
│       ├── sensor.py             # Battery & health sensors
│       ├── manifest.json         # Integration metadata
│       └── strings.json          # UI text
├── gateway/                       # Gateway code
│   ├── __init__.py
│   └── main.py                   # FastAPI gateway
├── docker-compose.yml             # Docker Compose config
├── Dockerfile                     # Docker image
├── requirements.txt               # Python dependencies
├── deploy_docker.sh               # Deployment script
└── .gitignore                     # Protects sensitive files
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

This gateway uses the official U-tec API format with header/payload structure:

#### Device Discovery
```json
{
  "header": {
    "namespace": "Uhome.Device",
    "name": "Discovery",
    "messageId": "uuid-v4",
    "payloadVersion": "1"
  },
  "payload": {},
  "accessKey": "your-access-key",
  "secretKey": "your-secret-key"
}
```

#### Device Command
```json
{
  "header": {
    "namespace": "Uhome.Device",
    "name": "Command",
    "messageId": "uuid-v4",
    "payloadVersion": "1"
  },
  "payload": {
    "devices": [
      {
        "id": "MAC:ADDRESS",
        "command": {
          "capability": "st.lock",
          "name": "lock"
        }
      }
    ]
  },
  "accessKey": "your-access-key",
  "secretKey": "your-secret-key"
}
```

### Status Response Format

```json
{
  "payload": {
    "devices": [
      {
        "id": "MAC:ADDRESS",
        "states": [
          {
            "capability": "st.healthCheck",
            "name": "status",
            "value": "Online"
          },
          {
            "capability": "st.lock",
            "name": "lockState",
            "value": "Locked"
          },
          {
            "capability": "st.batteryLevel",
            "name": "level",
            "value": 5
          }
        ]
      }
    ]
  }
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
- **python-docx** - Document creation (for gateway UI)

---

## 📄 License

Same as original uteclocal project.

---

## 🙏 Credits

- Original uteclocal concept by [Wheresitat](https://github.com/Wheresitat/uteclocal)
- Enhanced with automatic token refresh and complete HA integration
- U-tec API format based on official documentation: https://doc.api.u-tec.com/
- Built for the Home Assistant community

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/YOUR_USERNAME/uteclocal-HA/issues)
- **Discussions:** [GitHub Discussions](https://github.com/YOUR_USERNAME/uteclocal-HA/discussions)
- **Documentation:** https://doc.api.u-tec.com/

---

## ✨ What Makes This Enhanced

### Before (Manual Re-auth Required)
- ❌ Token expires every few days
- ❌ Manual OAuth flow required
- ❌ Home Assistant reload needed
- ❌ Service interruptions
- ❌ Wrong API format
- ❌ No battery/health sensors

### After (Fully Automated)
- ✅ Automatic token refresh
- ✅ One-time OAuth setup
- ✅ Zero maintenance required
- ✅ Continuous operation
- ✅ Correct API format (header/payload)
- ✅ Beautiful web UI for setup and testing
- ✅ Complete HA integration with lock, battery, and health entities
- ✅ Device control interface
- ✅ Comprehensive logging
- ✅ HACS compatible

---

## 🎊 Enjoy Hassle-Free Smart Lock Control!

Set it up once, never touch it again. The gateway and integration handle everything automatically. 🔐✨

**Questions? Open an issue!**  
**Working perfectly? Star the repository! ⭐**

---

**Last Updated:** January 2026  
**API Version:** U-tec API v1 (header/payload format)  
**Gateway Version:** 1.5.0 (Auto-refresh + Correct API Format)  
**Integration Version:** 1.5.0 (Lock + Battery + Health Check)
