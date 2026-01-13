"""
Enhanced U-tec Gateway with Automatic Token Refresh
This version includes:
- Automatic token refresh before expiration
- Retry logic for failed requests
- Token expiration monitoring
- Background refresh scheduler
"""

import json
import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration file path
DATA_DIR = Path("/data")
DATA_DIR.mkdir(exist_ok=True)
CONFIG_FILE = DATA_DIR / "config.json"
LOG_FILE = DATA_DIR / "gateway.log"

# Add file handler for persistent logs
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

app = FastAPI(title="U-tec Local Gateway with Auto-Refresh")

# Global configuration storage
config_data = {
    "api_base_url": "https://api.u-tec.com",
    "oauth_base_url": "https://oauth.u-tec.com",
    "action_path": "/action",
    "access_key": "",
    "secret_key": "",
    "scope": "openapi",
    "redirect_uri": "",
    "access_token": "",
    "refresh_token": "",
    "token_expires_at": None,  # Store as ISO format string
    "status_poll_interval": 60,
    "auto_refresh_enabled": True,  # New setting
    "refresh_buffer_minutes": 5,  # Refresh token X minutes before expiration
}

# Global state for devices and status
latest_devices = []
latest_status = {}
last_status_update = 0

# Initialize scheduler
scheduler = AsyncIOScheduler()


class TokenRefreshError(Exception):
    """Custom exception for token refresh failures"""
    pass


def load_config():
    """Load configuration from file"""
    global config_data
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                loaded = json.load(f)
                config_data.update(loaded)
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")


def save_config():
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=2)
        logger.info("Configuration saved successfully")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")


def get_token_expiration() -> Optional[datetime]:
    """Get token expiration as datetime object"""
    if config_data.get("token_expires_at"):
        try:
            return datetime.fromisoformat(config_data["token_expires_at"])
        except (ValueError, TypeError):
            return None
    return None


def set_token_expiration(expires_in: int):
    """Set token expiration time from expires_in seconds"""
    expiration = datetime.now() + timedelta(seconds=expires_in)
    config_data["token_expires_at"] = expiration.isoformat()
    save_config()
    logger.info(f"Token will expire at: {expiration}")


def is_token_expired() -> bool:
    """Check if the access token is expired or about to expire"""
    expiration = get_token_expiration()
    if not expiration:
        return True
    
    # Consider token expired if it's within the buffer time
    buffer = timedelta(minutes=config_data.get("refresh_buffer_minutes", 5))
    return datetime.now() + buffer >= expiration


async def refresh_access_token() -> bool:
    """
    Refresh the access token using the refresh token
    Returns True if successful, False otherwise
    """
    if not config_data.get("refresh_token"):
        logger.error("No refresh token available")
        return False
    
    logger.info("Attempting to refresh access token...")
    
    try:
        oauth_url = config_data.get("oauth_base_url", "https://oauth.u-tec.com")
        token_endpoint = f"{oauth_url}/token"
        
        # Prepare refresh token request
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": config_data["refresh_token"],
            "client_id": config_data.get("access_key", ""),
            "client_secret": config_data.get("secret_key", ""),
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                token_endpoint,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            logger.info(f"Token refresh response status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Update tokens
                config_data["access_token"] = token_data.get("access_token", "")
                
                # Some OAuth providers issue new refresh tokens
                if "refresh_token" in token_data:
                    config_data["refresh_token"] = token_data["refresh_token"]
                    logger.info("New refresh token received")
                
                # Set expiration time
                if "expires_in" in token_data:
                    set_token_expiration(token_data["expires_in"])
                else:
                    # Default to 1 hour if not specified
                    set_token_expiration(3600)
                
                save_config()
                logger.info("Access token refreshed successfully")
                return True
            else:
                logger.error(f"Token refresh failed: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return False


async def ensure_valid_token() -> bool:
    """
    Ensure we have a valid access token, refresh if necessary
    Returns True if valid token is available, False otherwise
    """
    if not config_data.get("access_token"):
        logger.warning("No access token available")
        return False
    
    if is_token_expired():
        logger.info("Token expired or expiring soon, attempting refresh...")
        return await refresh_access_token()
    
    return True


async def make_authenticated_request(
    method: str,
    url: str,
    headers: Optional[Dict] = None,
    json_data: Optional[Dict] = None,
    max_retries: int = 2
) -> httpx.Response:
    """
    Make an authenticated API request with automatic token refresh
    """
    if not await ensure_valid_token():
        raise TokenRefreshError("Unable to obtain valid access token")
    
    # Prepare headers with authentication
    request_headers = headers or {}
    request_headers.update({
        "Authorization": f"Bearer {config_data['access_token']}",
        "accessKey": config_data.get("access_key", ""),
        "secretKey": config_data.get("secret_key", ""),
    })
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(max_retries + 1):
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=request_headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=request_headers, json=json_data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # If we get 401, try refreshing token
                if response.status_code == 401 and attempt < max_retries:
                    logger.warning(f"Got 401, attempting token refresh (attempt {attempt + 1})")
                    if await refresh_access_token():
                        # Update headers with new token
                        request_headers["Authorization"] = f"Bearer {config_data['access_token']}"
                        continue
                
                return response
                
            except httpx.TimeoutException:
                if attempt < max_retries:
                    logger.warning(f"Request timeout, retrying... (attempt {attempt + 1})")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Request failed: {e}, retrying... (attempt {attempt + 1})")
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
        
        raise Exception("Max retries exceeded")


# Background task for automatic token refresh
async def scheduled_token_check():
    """Scheduled task to check and refresh token if needed"""
    try:
        if not config_data.get("auto_refresh_enabled", True):
            return
        
        if is_token_expired():
            logger.info("Scheduled token refresh triggered")
            success = await refresh_access_token()
            if success:
                logger.info("Scheduled token refresh successful")
            else:
                logger.error("Scheduled token refresh failed")
    except Exception as e:
        logger.error(f"Error in scheduled token check: {e}")


# Background task for device status polling
async def poll_device_status():
    """Background task to poll device status"""
    global latest_devices, latest_status, last_status_update
    
    try:
        if not await ensure_valid_token():
            logger.warning("Skipping status poll - no valid token")
            return
        
        # Discover devices
        api_url = config_data.get("api_base_url", "https://api.u-tec.com")
        action_path = config_data.get("action_path", "/action")
        endpoint = f"{api_url}{action_path}"
        
        discovery_payload = {
            "action": "Uhome.Device/Query",
            "data": {}
        }
        
        response = await make_authenticated_request("POST", endpoint, json_data=discovery_payload)
        
        if response.status_code == 200:
            result = response.json()
            devices = result.get("payload", {}).get("devices", [])
            latest_devices = devices
            
            # Query status for each device
            if devices:
                device_ids = [{"id": d.get("id")} for d in devices if d.get("id")]
                status_payload = {
                    "action": "Uhome.Device/Query",
                    "data": {"devices": device_ids}
                }
                
                status_response = await make_authenticated_request("POST", endpoint, json_data=status_payload)
                
                if status_response.status_code == 200:
                    latest_status = status_response.json()
                    last_status_update = int(datetime.now().timestamp())
                    logger.info(f"Status poll successful - {len(devices)} devices")
        
    except Exception as e:
        logger.error(f"Error in status poll: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    load_config()
    
    # Start scheduler for token refresh (check every 5 minutes)
    scheduler.add_job(
        scheduled_token_check,
        IntervalTrigger(minutes=5),
        id='token_refresh',
        replace_existing=True
    )
    
    # Start scheduler for status polling
    poll_interval = config_data.get("status_poll_interval", 60)
    scheduler.add_job(
        poll_device_status,
        IntervalTrigger(seconds=poll_interval),
        id='status_poll',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Gateway started with automatic token refresh enabled")
    
    # Log token status
    expiration = get_token_expiration()
    if expiration:
        logger.info(f"Current token expires at: {expiration}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    scheduler.shutdown()
    logger.info("Gateway shutting down")


# ===== API Endpoints =====

class ConfigUpdate(BaseModel):
    api_base_url: Optional[str] = None
    oauth_base_url: Optional[str] = None
    action_path: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    scope: Optional[str] = None
    redirect_uri: Optional[str] = None
    status_poll_interval: Optional[int] = None
    auto_refresh_enabled: Optional[bool] = None
    refresh_buffer_minutes: Optional[int] = None


@app.post("/api/config")
async def update_config(config: ConfigUpdate):
    """Update configuration"""
    for key, value in config.dict(exclude_unset=True).items():
        if value is not None:
            config_data[key] = value
    
    save_config()
    
    # Update polling interval if changed
    if config.status_poll_interval is not None:
        scheduler.reschedule_job(
            'status_poll',
            trigger=IntervalTrigger(seconds=config.status_poll_interval)
        )
    
    return {"status": "ok", "message": "Configuration updated"}


@app.get("/api/config")
async def get_config():
    """Get current configuration (without sensitive data)"""
    safe_config = config_data.copy()
    safe_config["secret_key"] = "***" if safe_config.get("secret_key") else ""
    safe_config["access_token"] = "***" if safe_config.get("access_token") else ""
    safe_config["refresh_token"] = "***" if safe_config.get("refresh_token") else ""
    
    # Add token status info
    expiration = get_token_expiration()
    safe_config["token_status"] = {
        "has_token": bool(config_data.get("access_token")),
        "has_refresh_token": bool(config_data.get("refresh_token")),
        "expires_at": expiration.isoformat() if expiration else None,
        "is_expired": is_token_expired(),
        "time_until_expiry": str(expiration - datetime.now()) if expiration else None
    }
    
    return safe_config


@app.post("/api/oauth/exchange")
async def exchange_code(request: Request):
    """Exchange authorization code for access token"""
    body = await request.json()
    code = body.get("code")
    
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code required")
    
    oauth_url = config_data.get("oauth_base_url", "https://oauth.u-tec.com")
    token_endpoint = f"{oauth_url}/token"
    
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": config_data.get("redirect_uri", ""),
        "client_id": config_data.get("access_key", ""),
        "client_secret": config_data.get("secret_key", ""),
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                token_endpoint,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                config_data["access_token"] = token_data.get("access_token", "")
                config_data["refresh_token"] = token_data.get("refresh_token", "")
                
                # Set expiration
                if "expires_in" in token_data:
                    set_token_expiration(token_data["expires_in"])
                
                save_config()
                logger.info("OAuth tokens obtained successfully")
                return {"status": "ok", "message": "Tokens obtained", "data": token_data}
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
    
    except Exception as e:
        logger.error(f"Token exchange failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/oauth/refresh")
async def manual_refresh_token():
    """Manually trigger token refresh"""
    success = await refresh_access_token()
    if success:
        return {
            "status": "ok",
            "message": "Token refreshed successfully",
            "expires_at": config_data.get("token_expires_at")
        }
    else:
        raise HTTPException(status_code=500, detail="Token refresh failed")


@app.get("/api/devices")
async def get_devices():
    """Get list of devices"""
    try:
        api_url = config_data.get("api_base_url", "https://api.u-tec.com")
        action_path = config_data.get("action_path", "/action")
        endpoint = f"{api_url}{action_path}"
        
        payload = {
            "action": "Uhome.Device/Query",
            "data": {}
        }
        
        response = await make_authenticated_request("POST", endpoint, json_data=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    
    except TokenRefreshError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/status")
async def query_status(request: Request):
    """Query device status"""
    try:
        body = await request.json()
        device_id = body.get("id")
        
        if not device_id:
            raise HTTPException(status_code=400, detail="Device ID required")
        
        api_url = config_data.get("api_base_url", "https://api.u-tec.com")
        action_path = config_data.get("action_path", "/action")
        endpoint = f"{api_url}{action_path}"
        
        payload = {
            "action": "Uhome.Device/Query",
            "data": {"devices": [{"id": device_id}]}
        }
        
        response = await make_authenticated_request("POST", endpoint, json_data=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    
    except TokenRefreshError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Error querying status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/lock")
@app.post("/lock")
async def lock_device(request: Request):
    """Lock a device"""
    try:
        body = await request.json()
        device_id = body.get("id")
        
        if not device_id:
            raise HTTPException(status_code=400, detail="Device ID required")
        
        api_url = config_data.get("api_base_url", "https://api.u-tec.com")
        action_path = config_data.get("action_path", "/action")
        endpoint = f"{api_url}{action_path}"
        
        # Try standard payload first
        payload = {
            "action": "Uhome.Device/Command",
            "data": {
                "id": device_id,
                "capability": "st.lock",
                "command": {
                    "name": "lock"
                }
            }
        }
        
        response = await make_authenticated_request("POST", endpoint, json_data=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            # Try fallback payloads...
            logger.warning("Standard lock command failed, trying fallback...")
            raise HTTPException(status_code=response.status_code, detail=response.text)
    
    except TokenRefreshError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Error locking device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/unlock")
@app.post("/unlock")
async def unlock_device(request: Request):
    """Unlock a device"""
    try:
        body = await request.json()
        device_id = body.get("id")
        
        if not device_id:
            raise HTTPException(status_code=400, detail="Device ID required")
        
        api_url = config_data.get("api_base_url", "https://api.u-tec.com")
        action_path = config_data.get("action_path", "/action")
        endpoint = f"{api_url}{action_path}"
        
        payload = {
            "action": "Uhome.Device/Command",
            "data": {
                "id": device_id,
                "capability": "st.lock",
                "command": {
                    "name": "unlock"
                }
            }
        }
        
        response = await make_authenticated_request("POST", endpoint, json_data=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    
    except TokenRefreshError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Error unlocking device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    expiration = get_token_expiration()
    return {
        "status": "ok",
        "token_valid": not is_token_expired(),
        "token_expires_at": expiration.isoformat() if expiration else None,
        "auto_refresh_enabled": config_data.get("auto_refresh_enabled", True)
    }


@app.get("/api/status/latest")
async def get_latest_status():
    """Get the latest cached status"""
    return {
        "status": latest_status,
        "last_updated": last_status_update
    }


@app.get("/logs")
async def get_logs():
    """Retrieve gateway logs"""
    try:
        if LOG_FILE.exists():
            with open(LOG_FILE, 'r') as f:
                logs = f.read()
            return PlainTextResponse(logs)
        else:
            return PlainTextResponse("No logs available")
    except Exception as e:
        return PlainTextResponse(f"Error reading logs: {e}")


@app.post("/logs/clear")
async def clear_logs():
    """Clear gateway logs"""
    try:
        if LOG_FILE.exists():
            LOG_FILE.unlink()
        return {"status": "ok", "message": "Logs cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Simple HTML UI
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve a simple web UI"""
    expiration = get_token_expiration()
    token_info = ""
    if expiration:
        time_left = expiration - datetime.now()
        token_info = f"Token expires in: {time_left}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>U-tec Gateway with Auto-Refresh</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ccc; }}
            input, button {{ margin: 5px 0; padding: 8px; }}
            button {{ cursor: pointer; background: #007bff; color: white; border: none; }}
            button:hover {{ background: #0056b3; }}
            .status {{ padding: 10px; margin: 10px 0; }}
            .success {{ background: #d4edda; color: #155724; }}
            .warning {{ background: #fff3cd; color: #856404; }}
            .error {{ background: #f8d7da; color: #721c24; }}
        </style>
    </head>
    <body>
        <h1>🔐 U-tec Gateway with Auto-Refresh</h1>
        
        <div class="section">
            <h2>Token Status</h2>
            <div class="status {'success' if not is_token_expired() else 'error'}">
                <strong>Token Status:</strong> {'✅ Valid' if not is_token_expired() else '❌ Expired/Missing'}<br>
                <strong>{token_info}</strong><br>
                <strong>Auto-refresh:</strong> {'✅ Enabled' if config_data.get('auto_refresh_enabled') else '❌ Disabled'}
            </div>
            <button onclick="refreshToken()">🔄 Manually Refresh Token</button>
            <button onclick="checkHealth()">❤️ Check Health</button>
        </div>
        
        <div class="section">
            <h2>Configuration</h2>
            <p>Auto-refresh is enabled by default and will automatically refresh your token 5 minutes before expiration.</p>
            <label><input type="checkbox" id="autoRefresh" {'checked' if config_data.get('auto_refresh_enabled', True) else ''}> Enable automatic token refresh</label><br>
            <label>Refresh buffer (minutes): <input type="number" id="refreshBuffer" value="{config_data.get('refresh_buffer_minutes', 5)}" min="1" max="60"></label><br>
            <button onclick="updateSettings()">💾 Save Settings</button>
        </div>
        
        <div class="section">
            <h2>Devices & Status</h2>
            <button onclick="getDevices()">📱 List Devices</button>
            <button onclick="getStatus()">📊 Get Status</button>
            <pre id="output"></pre>
        </div>
        
        <div class="section">
            <h2>Logs</h2>
            <button onclick="getLogs()">📄 View Logs</button>
            <button onclick="clearLogs()">🗑️ Clear Logs</button>
            <pre id="logs" style="max-height: 300px; overflow-y: auto;"></pre>
        </div>
        
        <script>
            async function refreshToken() {{
                try {{
                    const response = await fetch('/api/oauth/refresh', {{ method: 'POST' }});
                    const data = await response.json();
                    alert(data.message || 'Token refreshed!');
                    location.reload();
                }} catch (error) {{
                    alert('Error: ' + error.message);
                }}
            }}
            
            async function checkHealth() {{
                try {{
                    const response = await fetch('/health');
                    const data = await response.json();
                    alert(JSON.stringify(data, null, 2));
                }} catch (error) {{
                    alert('Error: ' + error.message);
                }}
            }}
            
            async function updateSettings() {{
                try {{
                    const autoRefresh = document.getElementById('autoRefresh').checked;
                    const refreshBuffer = parseInt(document.getElementById('refreshBuffer').value);
                    
                    const response = await fetch('/api/config', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            auto_refresh_enabled: autoRefresh,
                            refresh_buffer_minutes: refreshBuffer
                        }})
                    }});
                    
                    const data = await response.json();
                    alert('Settings saved!');
                    location.reload();
                }} catch (error) {{
                    alert('Error: ' + error.message);
                }}
            }}
            
            async function getDevices() {{
                try {{
                    const response = await fetch('/api/devices');
                    const data = await response.json();
                    document.getElementById('output').textContent = JSON.stringify(data, null, 2);
                }} catch (error) {{
                    document.getElementById('output').textContent = 'Error: ' + error.message;
                }}
            }}
            
            async function getStatus() {{
                try {{
                    const response = await fetch('/api/status/latest');
                    const data = await response.json();
                    document.getElementById('output').textContent = JSON.stringify(data, null, 2);
                }} catch (error) {{
                    document.getElementById('output').textContent = 'Error: ' + error.message;
                }}
            }}
            
            async function getLogs() {{
                try {{
                    const response = await fetch('/logs');
                    const logs = await response.text();
                    document.getElementById('logs').textContent = logs;
                }} catch (error) {{
                    document.getElementById('logs').textContent = 'Error: ' + error.message;
                }}
            }}
            
            async function clearLogs() {{
                if (confirm('Clear all logs?')) {{
                    try {{
                        await fetch('/logs/clear', {{ method: 'POST' }});
                        document.getElementById('logs').textContent = 'Logs cleared';
                    }} catch (error) {{
                        alert('Error: ' + error.message);
                    }}
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html_content


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
