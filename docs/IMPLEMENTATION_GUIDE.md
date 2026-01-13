# U-tec Gateway - Automatic Token Refresh Implementation Guide

## Problem Summary
The current U-tec gateway loses connectivity every few days because OAuth access tokens expire and are not automatically refreshed. This requires manual re-authentication through the bridge and reloading the Home Assistant integration.

## Solution Overview
This enhanced gateway implementation includes:

1. **Automatic Token Refresh** - Proactively refreshes tokens before expiration
2. **Retry Logic** - Automatically retries failed requests with token refresh
3. **Token Expiration Monitoring** - Tracks token lifecycle and logs warnings
4. **Background Scheduler** - Checks token status every 5 minutes
5. **Configurable Settings** - Customize refresh timing and behavior

---

## Key Features

### 1. Automatic Token Refresh
- **Proactive refresh**: Tokens are refreshed 5 minutes before expiration (configurable)
- **Background scheduler**: Checks token status every 5 minutes
- **Automatic retry**: If an API call gets 401 Unauthorized, it automatically refreshes the token and retries
- **Persistent storage**: Token expiration times are saved to config.json

### 2. Token Lifecycle Management
```python
# Token expiration is tracked with:
- token_expires_at: ISO format timestamp
- refresh_buffer_minutes: Minutes before expiry to trigger refresh (default: 5)
- auto_refresh_enabled: Global on/off switch (default: True)
```

### 3. Enhanced Error Handling
- Exponential backoff for failed requests
- Maximum retry attempts (configurable)
- Detailed logging for debugging
- Custom TokenRefreshError exception

---

## Installation Instructions

### Option 1: Replace Existing Gateway Files

1. **Backup your current setup** (important!):
   ```bash
   cd uteclocal
   cp gateway/main.py gateway/main.py.backup
   cp requirements.txt requirements.txt.backup
   ```

2. **Replace the main gateway file**:
   ```bash
   # Copy the enhanced main.py
   cp gateway_main_enhanced.py gateway/main.py
   ```

3. **Update requirements.txt**:
   ```bash
   # Add APScheduler to requirements.txt
   echo "APScheduler==3.10.4" >> requirements.txt
   ```

4. **Rebuild and restart the Docker container**:
   ```bash
   docker compose -p uteclocal down
   docker compose -p uteclocal up -d --build
   ```

### Option 2: Manual Update (if you've customized the gateway)

If you've made custom modifications, you can integrate specific features:

1. **Add the APScheduler dependency** to your requirements.txt:
   ```
   APScheduler==3.10.4
   ```

2. **Add these new configuration fields** to your config storage:
   ```python
   "token_expires_at": None,
   "auto_refresh_enabled": True,
   "refresh_buffer_minutes": 5,
   ```

3. **Implement the core functions** (copy from enhanced file):
   - `get_token_expiration()`
   - `set_token_expiration()`
   - `is_token_expired()`
   - `refresh_access_token()`
   - `ensure_valid_token()`
   - `make_authenticated_request()`

4. **Add the scheduler jobs** in startup event:
   ```python
   from apscheduler.schedulers.asyncio import AsyncIOScheduler
   from apscheduler.triggers.interval import IntervalTrigger
   
   scheduler = AsyncIOScheduler()
   
   @app.on_event("startup")
   async def startup_event():
       scheduler.add_job(
           scheduled_token_check,
           IntervalTrigger(minutes=5),
           id='token_refresh'
       )
       scheduler.start()
   ```

---

## Configuration

### Web UI Settings
Access the gateway web UI at `http://localhost:8000/` to configure:

1. **Auto-refresh Toggle**: Enable/disable automatic token refresh
2. **Refresh Buffer**: Set how many minutes before expiration to trigger refresh (1-60 minutes)
3. **Manual Refresh Button**: Force an immediate token refresh

### Environment Variables (Optional)
You can also set these via environment variables:

```yaml
# In docker-compose.yml
environment:
  - AUTO_REFRESH_ENABLED=true
  - REFRESH_BUFFER_MINUTES=5
```

---

## How It Works

### Token Refresh Flow

```
1. Scheduler runs every 5 minutes
   ↓
2. Check if token expires within buffer time (5 min)
   ↓
3. If expiring soon → Call refresh_access_token()
   ↓
4. POST to https://oauth.u-tec.com/token
   - grant_type: refresh_token
   - refresh_token: [stored token]
   - client_id: [access_key]
   - client_secret: [secret_key]
   ↓
5. Receive new access_token (and possibly new refresh_token)
   ↓
6. Update config.json with new tokens and expiration
   ↓
7. Continue normal operation
```

### Automatic Retry on 401

```
1. API call made with current token
   ↓
2. Receives 401 Unauthorized
   ↓
3. Automatically call refresh_access_token()
   ↓
4. Retry original request with new token
   ↓
5. Return response
```

---

## Monitoring & Troubleshooting

### Check Token Status

**Via Web UI:**
- Navigate to `http://localhost:8000/`
- Token status is displayed at the top (Valid/Expired)
- Shows time until expiration

**Via API:**
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "token_valid": true,
  "token_expires_at": "2026-01-15T10:30:00",
  "auto_refresh_enabled": true
}
```

### View Logs

**Via Web UI:**
- Click "View Logs" button
- Shows detailed token refresh attempts and status

**Via Docker:**
```bash
docker compose -p uteclocal logs -f gateway
```

**Via File:**
```bash
docker exec uteclocal-gateway-1 cat /data/gateway.log
```

### Common Log Messages

✅ **Success indicators:**
```
Token will expire at: 2026-01-15 10:30:00
Access token refreshed successfully
Scheduled token refresh successful
```

⚠️ **Warning indicators:**
```
Token expired or expiring soon, attempting refresh...
Got 401, attempting token refresh (attempt 1)
```

❌ **Error indicators:**
```
Token refresh failed: [error details]
No refresh token available
Unable to obtain valid access token
```

---

## Testing the Implementation

### 1. Verify Auto-Refresh is Working

```bash
# Check current token status
curl http://localhost:8000/api/config | jq '.token_status'

# Output should show:
{
  "has_token": true,
  "has_refresh_token": true,
  "expires_at": "2026-01-15T10:30:00",
  "is_expired": false,
  "time_until_expiry": "2:30:00"
}
```

### 2. Test Manual Refresh

```bash
# Force a token refresh
curl -X POST http://localhost:8000/api/oauth/refresh

# Expected response:
{
  "status": "ok",
  "message": "Token refreshed successfully",
  "expires_at": "2026-01-15T12:00:00"
}
```

### 3. Test Lock/Unlock Still Works

```bash
# Replace <device_mac> with your lock's MAC address
curl -X POST http://localhost:8000/api/lock \
  -H "Content-Type: application/json" \
  -d '{"id":"<device_mac>"}'
```

### 4. Simulate Token Expiration (Advanced)

For testing purposes, you can manually set the token expiration to a past date:

```bash
# Access the container
docker exec -it uteclocal-gateway-1 /bin/bash

# Edit config.json and set token_expires_at to a past date
vi /data/config.json

# Wait for next scheduler run (max 5 minutes) or restart gateway
exit
docker compose -p uteclocal restart
```

Watch the logs to see automatic refresh trigger:
```bash
docker compose -p uteclocal logs -f gateway
```

---

## Integration with Home Assistant

### No Changes Required!

The enhanced gateway is 100% backward compatible with your existing Home Assistant integration. The HA integration will:

1. Continue to work without any modifications
2. Benefit from automatic token refresh
3. No longer experience authentication failures
4. Not need to be reloaded every few days

### Verify HA Connection

After deploying the enhanced gateway:

1. **Check HA integration status**:
   - Settings → Devices & Services
   - Find "U-tec Local Gateway"
   - Should show "Connected" or "OK"

2. **Test lock control**:
   - Try locking/unlocking from HA dashboard
   - Should work normally

3. **Monitor for errors**:
   - Check HA logs: Settings → System → Logs
   - Search for "uteclocal" or "u-tec"
   - Should not see authentication errors

---

## Maintenance

### Regular Health Checks

Set up a simple monitoring script (optional):

```bash
#!/bin/bash
# save as check_gateway.sh

GATEWAY="http://localhost:8000"
RESPONSE=$(curl -s ${GATEWAY}/health)
TOKEN_VALID=$(echo $RESPONSE | jq -r '.token_valid')

if [ "$TOKEN_VALID" != "true" ]; then
    echo "WARNING: Gateway token is not valid!"
    # Send notification (email, SMS, etc.)
fi
```

Run via cron:
```bash
# Check every hour
0 * * * * /path/to/check_gateway.sh
```

### Backup Configuration

Your tokens and configuration are stored in Docker volume. To backup:

```bash
# Backup config
docker cp uteclocal-gateway-1:/data/config.json ./config_backup.json

# Backup logs
docker cp uteclocal-gateway-1:/data/gateway.log ./gateway_backup.log
```

### Update Procedure

When updating the gateway code:

```bash
# Pull latest changes
git pull

# Rebuild with new code (preserves /data volume)
docker compose -p uteclocal up -d --build

# Verify health
curl http://localhost:8000/health
```

---

## Advanced Configuration

### Adjust Refresh Timing

If you want more/less aggressive refresh:

```python
# In config or via API:
{
  "refresh_buffer_minutes": 10,  # Refresh 10 minutes early
  "auto_refresh_enabled": true
}
```

### Add Email Notifications on Refresh Failure

Add this to `refresh_access_token()`:

```python
if not success:
    # Send email alert
    send_email(
        to="your@email.com",
        subject="U-tec Gateway: Token Refresh Failed",
        body=f"Token refresh failed at {datetime.now()}"
    )
```

### Increase Retry Attempts

Modify `make_authenticated_request()`:

```python
async def make_authenticated_request(
    method: str,
    url: str,
    headers: Optional[Dict] = None,
    json_data: Optional[Dict] = None,
    max_retries: int = 5  # Increased from 2
) -> httpx.Response:
```

---

## Troubleshooting Guide

### Issue: Token still expires

**Check:**
1. Is auto-refresh enabled? `curl http://localhost:8000/api/config | jq '.auto_refresh_enabled'`
2. Are scheduler jobs running? Check logs for "Scheduled token refresh"
3. Is refresh token present? Check config for `has_refresh_token: true`

**Solution:**
```bash
# Restart gateway to reinitialize scheduler
docker compose -p uteclocal restart gateway
```

### Issue: Refresh fails with "invalid_grant"

**Cause:** Refresh token itself has expired or is invalid

**Solution:**
1. Go through OAuth flow again in web UI
2. Click "Start OAuth" → Approve → Exchange code
3. New refresh token will be stored

### Issue: 401 errors still occur

**Check:**
1. Verify U-tec API hasn't changed their OAuth endpoint
2. Check if access_key and secret_key are still valid
3. Review logs for specific error messages

**Solution:**
```bash
# View detailed logs
docker compose -p uteclocal logs gateway | grep -i "error\|401\|token"
```

### Issue: Scheduler not running

**Check:**
```bash
# Look for scheduler startup message
docker compose -p uteclocal logs gateway | grep "scheduler"
```

**Solution:**
```bash
# Ensure APScheduler is installed
docker exec uteclocal-gateway-1 pip list | grep APScheduler

# If missing, rebuild
docker compose -p uteclocal up -d --build
```

---

## FAQ

**Q: Will this work with multiple locks?**
A: Yes, the token is account-level and works for all locks associated with your U-tec account.

**Q: What happens if the gateway restarts?**
A: Token and expiration info are stored in `/data/config.json` (persisted volume), so they survive restarts.

**Q: Can I disable auto-refresh?**
A: Yes, via web UI or by setting `auto_refresh_enabled: false` in config. Manual refresh will still work.

**Q: How do I know if refresh is working?**
A: Check logs for "Access token refreshed successfully" messages. Also check the health endpoint.

**Q: Will this increase API calls to U-tec?**
A: Minimally. Token refresh only happens once every few hours (when token expires). The scheduler check is local (no API call).

**Q: What if U-tec changes their API?**
A: The gateway logs all API interactions. If something breaks, check logs and update the OAuth endpoints in config.

---

## Support & Contributions

### Reporting Issues

If you encounter problems:

1. **Collect logs**:
   ```bash
   docker compose -p uteclocal logs gateway > gateway_logs.txt
   curl http://localhost:8000/api/config > config_status.txt
   ```

2. **Create GitHub issue** with:
   - Gateway logs
   - Config status (sanitized - remove sensitive data)
   - Home Assistant version
   - Description of issue

### Contributing

Improvements welcome! Focus areas:
- Enhanced error messages
- Additional OAuth providers
- Better UI/UX
- Automated testing

---

## Summary

This enhanced gateway implementation solves the token expiration issue by:

✅ **Automatically refreshing tokens** before they expire
✅ **Monitoring token lifecycle** with detailed logging
✅ **Retrying failed requests** with fresh tokens
✅ **Maintaining backward compatibility** with existing HA integration
✅ **Providing visibility** through web UI and logs

Once deployed, you should **never need to manually re-authenticate** unless:
- You change credentials
- U-tec revokes your API access
- The refresh token itself expires (very rare with proper implementation)

Your Home Assistant integration will continue working seamlessly without the need to reload every few days.
