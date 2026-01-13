# U-tec Gateway - Automatic Token Refresh Solution

## 🔧 Problem Solved

**Before:** Gateway loses authentication every few days, requiring manual OAuth re-authentication and Home Assistant integration reload.

**After:** Gateway automatically refreshes OAuth tokens before expiration, maintaining continuous connectivity indefinitely.

---

## 🎯 What's Included

This package provides an enhanced version of the U-tec Local Gateway with:

### Core Features
- ✅ **Automatic Token Refresh** - Tokens refreshed 5 minutes before expiration
- ✅ **Background Scheduler** - Monitors token status every 5 minutes
- ✅ **Smart Retry Logic** - Auto-retries failed API calls with fresh tokens
- ✅ **Persistent Storage** - Token lifecycle data survives container restarts
- ✅ **Web UI Controls** - View status and manually trigger refresh
- ✅ **Comprehensive Logging** - Detailed logs for monitoring and debugging
- ✅ **Zero HA Changes** - 100% backward compatible with existing integration

### Files Provided
1. **`gateway_main_enhanced.py`** - Enhanced gateway with auto-refresh (replaces `gateway/main.py`)
2. **`requirements_enhanced.txt`** - Updated dependencies with APScheduler
3. **`IMPLEMENTATION_GUIDE.md`** - Detailed installation and troubleshooting guide
4. **`deploy_enhanced_gateway.sh`** - Automated deployment script
5. **`README.md`** - This file

---

## 🚀 Quick Start

### Prerequisites
- Existing uteclocal gateway installation
- Docker and Docker Compose installed
- OAuth credentials already configured (or ready to configure)

### Installation (3 steps)

1. **Download the enhanced files** to your uteclocal directory:
   ```bash
   cd /path/to/uteclocal
   # Copy the provided files here
   ```

2. **Run the deployment script**:
   ```bash
   chmod +x deploy_enhanced_gateway.sh
   ./deploy_enhanced_gateway.sh
   ```

3. **Verify it's working**:
   ```bash
   curl http://localhost:8000/health
   ```
   
   Should return:
   ```json
   {
     "status": "ok",
     "token_valid": true,
     "token_expires_at": "2026-01-15T10:30:00",
     "auto_refresh_enabled": true
   }
   ```

**That's it!** Your gateway will now automatically maintain authentication.

---

## 📊 How It Works

### Token Refresh Cycle

```
┌─────────────────────────────────────────────────┐
│  Background Scheduler (Every 5 minutes)         │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
          ┌───────────────────┐
          │ Check expiration  │
          │ time vs buffer    │
          └─────────┬─────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌──────────────┐        ┌──────────────┐
│ Still valid  │        │ Expiring     │
│ > 5 min left │        │ < 5 min left │
└──────┬───────┘        └──────┬───────┘
       │                       │
       ▼                       ▼
   Continue              Refresh Token
   normally              ──────────────
                         POST /token
                         - grant_type: refresh_token
                         - refresh_token: [saved]
                         ──────────────
                         Receive new tokens
                         Update config.json
                         Continue operation
```

### API Request Flow with Auto-Retry

```
┌────────────────────┐
│ API Request Made   │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Check token valid? │
└─────────┬──────────┘
          │
    ┌─────┴──────┐
    │            │
    ▼            ▼
┌────────┐  ┌─────────────┐
│ Valid  │  │ Expired     │
└────┬───┘  └──────┬──────┘
     │             │
     │             ▼
     │      ┌──────────────┐
     │      │ Refresh token│
     │      └──────┬───────┘
     │             │
     └─────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Make request │
    └──────┬───────┘
           │
      ┌────┴─────┐
      │          │
      ▼          ▼
   ┌──────┐  ┌──────┐
   │ 200  │  │ 401  │
   │ OK   │  │ Fail │
   └──┬───┘  └───┬──┘
      │          │
      │          ▼
      │    ┌─────────────┐
      │    │ Retry once  │
      │    │ with refresh│
      │    └─────┬───────┘
      │          │
      └──────────┴────────→ Return response
```

---

## 🎛️ Configuration

### Web UI (Recommended)

Access `http://localhost:8000/` and configure:

| Setting | Description | Default |
|---------|-------------|---------|
| Auto-refresh | Enable/disable automatic refresh | ✅ Enabled |
| Refresh buffer | Minutes before expiry to trigger refresh | 5 minutes |

### Manual Refresh Button
Force an immediate token refresh via the web UI or:
```bash
curl -X POST http://localhost:8000/api/oauth/refresh
```

---

## 📈 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

**Response indicators:**
- ✅ `"token_valid": true` - Token is valid
- ❌ `"token_valid": false` - Token expired/missing
- ⏰ `"token_expires_at"` - Expiration timestamp
- 🔄 `"auto_refresh_enabled"` - Refresh feature status

### View Logs

**Web UI:**
- Click "View Logs" button on homepage

**Docker:**
```bash
docker compose -p uteclocal logs -f gateway
```

**Log indicators:**
- ✅ `"Access token refreshed successfully"` - Refresh worked
- ⚠️ `"Token expired or expiring soon"` - Refresh triggered
- ❌ `"Token refresh failed"` - Manual intervention may be needed

---

## 🔍 Testing

### Verify Auto-Refresh Setup

```bash
# 1. Check configuration
curl http://localhost:8000/api/config | jq '.token_status'

# 2. Test manual refresh
curl -X POST http://localhost:8000/api/oauth/refresh

# 3. Verify lock control still works
curl -X POST http://localhost:8000/api/lock \
  -H "Content-Type: application/json" \
  -d '{"id":"YOUR_DEVICE_MAC"}'

# 4. Monitor logs for scheduled refresh
docker compose -p uteclocal logs -f gateway | grep "refresh"
```

---

## 🏠 Home Assistant Integration

### No Changes Required! ✨

Your existing Home Assistant integration will:
- ✅ Continue working without modifications
- ✅ Benefit from automatic token refresh
- ✅ Never lose authentication
- ✅ Not require periodic reloading

### Verification Steps

1. **Check integration status:**
   - Settings → Devices & Services
   - Find "U-tec Local Gateway"
   - Status should be "Connected"

2. **Test lock control:**
   - Lock/unlock from HA dashboard
   - Should work normally

3. **Monitor over time:**
   - Check after a few days
   - Should remain connected (no manual re-auth needed)

---

## 🐛 Troubleshooting

### Issue: Token still expires after a few days

**Solution:**
```bash
# Check if auto-refresh is enabled
curl http://localhost:8000/api/config | jq '.auto_refresh_enabled'

# If false, enable it via web UI or:
curl -X POST http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{"auto_refresh_enabled": true}'

# Restart gateway
docker compose -p uteclocal restart gateway
```

### Issue: Refresh fails with "invalid_grant"

**Cause:** Refresh token itself has expired

**Solution:**
1. Go to `http://localhost:8000/`
2. Complete OAuth flow again:
   - Enter credentials
   - Click "Start OAuth"
   - Approve authorization
   - Copy redirect URL
   - Exchange code for new tokens

### Issue: Gateway not starting

**Solution:**
```bash
# Check logs
docker compose -p uteclocal logs gateway

# Common issues:
# 1. Port 8000 already in use
# 2. Missing APScheduler dependency
# 3. Syntax error in main.py

# Rebuild from scratch
docker compose -p uteclocal down
docker compose -p uteclocal up -d --build
```

### Issue: 401 errors persist

**Solution:**
```bash
# View detailed error logs
docker compose -p uteclocal logs gateway | grep -i "401\|error\|token"

# Verify credentials are correct
curl http://localhost:8000/api/config | jq '.access_key, .secret_key'

# Test OAuth endpoint
curl https://oauth.u-tec.com/token \
  -d "grant_type=refresh_token" \
  -d "refresh_token=YOUR_TOKEN" \
  -d "client_id=YOUR_ACCESS_KEY" \
  -d "client_secret=YOUR_SECRET_KEY"
```

---

## 📚 Documentation

- **`IMPLEMENTATION_GUIDE.md`** - Comprehensive setup and troubleshooting guide
- **Gateway Code** - Well-commented Python code with inline documentation
- **Web UI** - Built-in help and status indicators
- **Logs** - Detailed logging for debugging

---

## 🆘 Support

### Common Questions

**Q: Will this increase API usage?**
A: Minimal impact. Token refresh only occurs when tokens are expiring (every few hours).

**Q: What happens during gateway restart?**
A: Token data is persisted in `/data/config.json` volume and survives restarts.

**Q: Can I disable auto-refresh?**
A: Yes, via web UI or config. Manual refresh will still work.

**Q: Does this work with multiple locks?**
A: Yes, tokens are account-level and work for all your U-tec devices.

**Q: What if U-tec changes their API?**
A: Check logs for errors. Update OAuth endpoints in config if needed.

### Getting Help

1. **Check logs first:**
   ```bash
   docker compose -p uteclocal logs gateway | tail -100
   ```

2. **Review Implementation Guide:**
   - See `IMPLEMENTATION_GUIDE.md` for detailed troubleshooting

3. **Create GitHub Issue:**
   - Include sanitized logs and config
   - Describe the problem and steps to reproduce

---

## 🔄 Updates

### Updating the Gateway

```bash
# Pull latest changes from repository
git pull

# Run deployment script
./deploy_enhanced_gateway.sh

# Or manually rebuild
docker compose -p uteclocal up -d --build
```

Configuration and tokens are preserved during updates.

---

## 🎉 Summary

This enhanced gateway solves the authentication expiration problem by:

| Feature | Benefit |
|---------|---------|
| **Automatic Refresh** | No more manual re-authentication every few days |
| **Background Monitoring** | Proactive token management before issues occur |
| **Smart Retries** | Handles transient failures gracefully |
| **Web UI** | Easy monitoring and manual control |
| **Detailed Logging** | Clear visibility into what's happening |
| **Zero HA Changes** | Works with existing Home Assistant setup |

### Expected Results

After deployment, you should **never need to manually re-authenticate** unless:
- ❌ You change your U-tec credentials
- ❌ U-tec revokes your API access
- ❌ Major API changes by U-tec

Otherwise, your gateway will maintain continuous authentication indefinitely! 🎊

---

## 📄 License

This enhancement maintains the same license as the original uteclocal project.

---

## 🙏 Credits

- Original uteclocal gateway by [Wheresitat](https://github.com/Wheresitat/uteclocal)
- Enhanced with automatic token refresh functionality
- Built for the Home Assistant community

---

**Enjoy uninterrupted smart lock control!** 🔐✨
