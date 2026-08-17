"""
Enhanced U-tec Gateway with Automatic Token Refresh & Extended Logging
Includes:
- Device Management UI & Status Controls
- Direct Health Check with Expiry Telemetry
- Verbose Logging for Home Assistant API calls & Auto-Renew execution
"""

import json
import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import uuid
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("uteclocal-gateway")

# Configuration file path
DATA_DIR = Path("/data")
DATA_DIR.mkdir(exist_ok=True)
CONFIG_FILE = DATA_DIR / "config.json"
LOG_FILE = DATA_DIR / "gateway.log"

file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

app = FastAPI(title="U-tec Local Gateway with Auto-Refresh")

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
    "token_expires_at": None,
    "status_poll_interval": 60,
    "auto_refresh_enabled": True,
    "refresh_buffer_minutes": 15,
}

latest_devices = []
latest_status = {}
last_status_update = 0

scheduler = AsyncIOScheduler()


class TokenRefreshError(Exception):
    """Custom exception for token refresh failures"""
    pass


def load_config():
    global config_data
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                loaded = json.load(f)
                config_data.update(loaded)
            logger.info("Configuration loaded successfully from /data/config.json")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")


def save_config():
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=2)
        logger.info("Configuration saved to /data/config.json")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")


def get_token_expiration() -> Optional[datetime]:
    if config_data.get("token_expires_at"):
        try:
            return datetime.fromisoformat(config_data["token_expires_at"])
        except (ValueError, TypeError):
            return None
    return None


def set_token_expiration(expires_in: int):
    expiration = datetime.utcnow() + timedelta(seconds=int(expires_in))
    config_data["token_expires_at"] = expiration.isoformat()
    save_config()
    logger.info(f"Token expiration updated. Will expire at (UTC): {expiration}")


def is_token_expired() -> bool:
    expiration = get_token_expiration()
    if not expiration:
        return True
    
    buffer = timedelta(minutes=config_data.get("refresh_buffer_minutes", 15))
    return datetime.utcnow() + buffer >= expiration


async def refresh_access_token() -> bool:
    if not config_data.get("refresh_token"):
        logger.error("[AUTO-RENEW] Failed: No refresh token available in config")
        return False
    
    logger.info("🔄 [AUTO-RENEW] Initiating background OAuth token refresh with U-tec...")
    
    try:
        oauth_url = config_data.get("oauth_base_url", "https://oauth.u-tec.com")
        token_endpoint = f"{oauth_url}/token"
        
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
            
            logger.info(f"🔄 [AUTO-RENEW] U-tec token endpoint response status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                
                if token_data.get("access_token"):
                    config_data["access_token"] = token_data["access_token"]
                
                if token_data.get("refresh_token"):
                    config_data["refresh_token"] = token_data["refresh_token"]
                    logger.info("🔄 [AUTO-RENEW] New refresh token saved")
                
                expires_in = token_data.get("expires_in", 3600)
                set_token_expiration(expires_in)
                
                save_config()
                logger.info("✅ [AUTO-RENEW SUCCESS] Access token renewed successfully!")
                return True
            else:
                logger.error(f"❌ [AUTO-RENEW FAILED] HTTP {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"❌ [AUTO-RENEW ERROR] Exception during token refresh: {e}", exc_info=True)
        return False


async def ensure_valid_token() -> bool:
    if not config_data.get("access_token"):
        logger.warning("[AUTH] No access token configured.")
        return False
    
    if is_token_expired():
        logger.info("[AUTH] Token expired or buffer limit reached. Triggering refresh...")
        return await refresh_access_token()
    
    return True


async def make_authenticated_request(
    method: str,
    url: str,
    headers: Optional[Dict] = None,
    json_data: Optional[Dict] = None,
    max_retries: int = 2
) -> httpx.Response:
    if not await ensure_valid_token():
        raise TokenRefreshError("Unable to obtain valid access token")
    
    request_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config_data['access_token']}",
    }
    
    if headers:
        request_headers.update(headers)
    
    if json_data:
        json_data["accessKey"] = config_data.get("access_key", "")
        json_data["secretKey"] = config_data.get("secret_key", "")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(max_retries + 1):
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=request_headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=request_headers, json=json_data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                if response.status_code == 401 and attempt < max_retries:
                    logger.warning(f"[API 401] Token rejected on attempt {attempt + 1}. Attempting instant refresh...")
                    if await refresh_access_token():
                        request_headers["Authorization"] = f"Bearer {config_data['access_token']}"
                        if json_data:
                            json_data["accessKey"] = config_data.get("access_key", "")
                            json_data["secretKey"] = config_data.get("secret_key", "")
                        continue
                
                return response
                
            except httpx.TimeoutException:
                if attempt < max_retries:
                    logger.warning(f"[API TIMEOUT] Request timed out. Retrying attempt {attempt + 1}...")
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"[API ERROR] Request failed ({e}). Retrying attempt {attempt + 1}...")
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
        
        raise Exception("Max retries exceeded")


async def scheduled_token_check():
    """Background task to check and refresh token if needed"""
    try:
        if not config_data.get("auto_refresh_enabled", True):
            return
        
        expiration = get_token_expiration()
        time_left = (expiration - datetime.utcnow()) if expiration else "Unknown"
        logger.info(f"⏰ [SCHEDULED CHECK] Verification running. Token valid. Time remaining until expiry: {time_left}")
        
        if is_token_expired():
            logger.info("⏰ [SCHEDULED CHECK] Token near expiration. Initiating auto-renew...")
            success = await refresh_access_token()
            if success:
                logger.info("✅ [SCHEDULED CHECK] Auto-renew completed successfully.")
            else:
                logger.error("❌ [SCHEDULED CHECK] Auto-renew failed.")
    except Exception as e:
        logger.error(f"Error in scheduled token check: {e}")


async def poll_device_status():
    global latest_devices, latest_status, last_status_update
    try:
        if not await ensure_valid_token():
            return
        
        api_url = config_data.get("api_base_url", "https://api.u-tec.com")
        action_path = config_data.get("action_path", "/action")
        endpoint = f"{api_url}{action_path}"
        
        discovery_payload = {
            "header": {
                "namespace": "Uhome.Device",
                "name": "Discovery",
                "messageId": str(uuid.uuid4()),
                "payloadVersion": "1"
            },
            "payload": {}
        }
        
        response = await make_authenticated_request("POST", endpoint, json_data=discovery_payload)
        
        if response.status_code == 200:
            result = response.json()
            devices = result.get("payload", {}).get("devices", [])
            latest_devices = devices
            
            if devices:
                device_ids = [{"id": d.get("id")} for d in devices if d.get("id")]
                status_payload = {
                    "header": {
                        "namespace": "Uhome.Device",
                        "name": "Query",
                        "messageId": str(uuid.uuid4()),
                        "payloadVersion": "1"
                    },
                    "payload": {"devices": device_ids}
                }
                
                status_response = await make_authenticated_request("POST", endpoint, json_data=status_payload)
                
                if status_response.status_code == 200:
                    latest_status = status_response.json()
                    last_status_update = int(datetime.utcnow().timestamp())
        
    except Exception as e:
        logger.error(f"Error in background status poll: {e}")


@app.on_event("startup")
async def startup_event():
    load_config()
    
    scheduler.add_job(
        scheduled_token_check,
        IntervalTrigger(minutes=5),
        id='token_refresh',
        replace_existing=True
    )
    
    poll_interval = config_data.get("status_poll_interval", 60)
    scheduler.add_job(
        poll_device_status,
        IntervalTrigger(seconds=poll_interval),
        id='status_poll',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("🚀 Gateway online. Auto-refresh scheduler running (checks every 5 mins).")


@app.on_event("shutdown")
async def shutdown_event():
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
    for key, value in config.dict(exclude_unset=True).items():
        if value is not None:
            config_data[key] = value
    save_config()
    return {"status": "ok", "message": "Configuration updated"}


@app.get("/api/config")
async def get_config():
    safe_config = config_data.copy()
    safe_config["secret_key"] = "***" if safe_config.get("secret_key") else ""
    safe_config["access_token"] = "***" if safe_config.get("access_token") else ""
    safe_config["refresh_token"] = "***" if safe_config.get("refresh_token") else ""
    
    expiration = get_token_expiration()
    safe_config["token_status"] = {
        "has_token": bool(config_data.get("access_token")),
        "has_refresh_token": bool(config_data.get("refresh_token")),
        "expires_at": expiration.isoformat() if expiration else None,
        "is_expired": is_token_expired(),
        "time_until_expiry": str(expiration - datetime.utcnow()) if expiration else None
    }
    return safe_config


@app.get("/api/oauth/authorize-url")
async def get_authorize_url():
    oauth_url = config_data.get("oauth_base_url", "https://oauth.u-tec.com")
    client_id = config_data.get("access_key", "")
    redirect_uri = config_data.get("redirect_uri", "")
    scope = config_data.get("scope", "openapi")
    
    if not client_id or not redirect_uri:
        raise HTTPException(status_code=400, detail="Configure access_key and redirect_uri first.")
    
    auth_url = (
        f"{oauth_url}/authorize?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={quote(redirect_uri, safe='')}&"
        f"scope={quote(scope, safe='')}"
    )
    return {"url": auth_url, "success": True}


@app.post("/api/oauth/exchange")
async def exchange_code(request: Request):
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
                if token_data.get("refresh_token"):
                    config_data["refresh_token"] = token_data.get("refresh_token", "")
                
                expires_in = token_data.get("expires_in", 3600)
                set_token_expiration(expires_in)
                save_config()
                logger.info("🔑 [OAUTH] Initial authorization successful. Tokens stored.")
                return {"status": "ok", "message": "Tokens obtained", "data": token_data}
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        logger.error(f"Token exchange failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/oauth/refresh")
async def manual_refresh_token():
    logger.info("👤 [MANUAL REFRESH] User requested manual token refresh via Web UI.")
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
async def get_devices(request: Request):
    client_ip = request.client.host if request.client else "Unknown"
    logger.info(f"📡 [HA POLL] GET /api/devices from Home Assistant ({client_ip})")
    
    try:
        api_url = config_data.get("api_base_url", "https://api.u-tec.com")
        action_path = config_data.get("action_path", "/action")
        endpoint = f"{api_url}{action_path}"
        
        payload = {
            "header": {
                "namespace": "Uhome.Device",
                "name": "Discovery",
                "messageId": str(uuid.uuid4()),
                "payloadVersion": "1"
            },
            "payload": {}
        }
        
        response = await make_authenticated_request("POST", endpoint, json_data=payload)
        if response.status_code == 200:
            data = response.json()
            device_count = len(data.get("payload", {}).get("devices", []))
            logger.info(f"✅ [HA POLL SUCCESS] Returned {device_count} devices to Home Assistant.")
            return data
        else:
            logger.error(f"❌ [HA POLL FAILED] U-tec API HTTP {response.status_code}: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except TokenRefreshError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/status")
async def query_status(request: Request):
    client_ip = request.client.host if request.client else "Unknown"
    try:
        body = await request.json()
        device_id = body.get("id")
        logger.info(f"📊 [HA POLL] POST /api/status for device {device_id} from {client_ip}")
        
        if not device_id:
            raise HTTPException(status_code=400, detail="Device ID required")
        
        api_url = config_data.get("api_base_url", "https://api.u-tec.com")
        action_path = config_data.get("action_path", "/action")
        endpoint = f"{api_url}{action_path}"
        
        payload = {
            "header": {
                "namespace": "Uhome.Device",
                "name": "Query",
                "messageId": str(uuid.uuid4()),
                "payloadVersion": "1"
            },
            "payload": {
                "devices": [{"id": device_id}]
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
        logger.error(f"Error querying status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/lock")
@app.post("/lock")
async def lock_device(request: Request):
    try:
        body = await request.json()
        device_id = body.get("id")
        logger.info(f"🔒 [HA COMMAND] Lock request received for device {device_id}")
        
        if not device_id:
            raise HTTPException(status_code=400, detail="Device ID required")
        
        api_url = config_data.get("api_base_url", "https://api.u-tec.com")
        action_path = config_data.get("action_path", "/action")
        endpoint = f"{api_url}{action_path}"
        
        payload = {
            "header": {
                "namespace": "Uhome.Device",
                "name": "Command",
                "messageId": str(uuid.uuid4()),
                "payloadVersion": "1"
            },
            "payload": {
                "devices": [
                    {
                        "id": device_id,
                        "command": {
                            "capability": "st.lock",
                            "name": "lock"
                        }
                    }
                ]
            }
        }
        
        response = await make_authenticated_request("POST", endpoint, json_data=payload)
        if response.status_code == 200:
            logger.info(f"✅ [HA COMMAND SUCCESS] Lock command executed for {device_id}")
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        logger.error(f"Error locking device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/unlock")
@app.post("/unlock")
async def unlock_device(request: Request):
    try:
        body = await request.json()
        device_id = body.get("id")
        logger.info(f"🔓 [HA COMMAND] Unlock request received for device {device_id}")
        
        if not device_id:
            raise HTTPException(status_code=400, detail="Device ID required")
        
        api_url = config_data.get("api_base_url", "https://api.u-tec.com")
        action_path = config_data.get("action_path", "/action")
        endpoint = f"{api_url}{action_path}"
        
        payload = {
            "header": {
                "namespace": "Uhome.Device",
                "name": "Command",
                "messageId": str(uuid.uuid4()),
                "payloadVersion": "1"
            },
            "payload": {
                "devices": [
                    {
                        "id": device_id,
                        "command": {
                            "capability": "st.lock",
                            "name": "unlock"
                        }
                    }
                ]
            }
        }
        
        response = await make_authenticated_request("POST", endpoint, json_data=payload)
        if response.status_code == 200:
            logger.info(f"✅ [HA COMMAND SUCCESS] Unlock command executed for {device_id}")
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        logger.error(f"Error unlocking device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint used by Docker & HA"""
    expiration = get_token_expiration()
    expired = is_token_expired()
    time_left = str(expiration - datetime.utcnow()) if expiration else "None"
    
    return {
        "status": "ok",
        "health": "healthy" if not expired else "token_expiring_or_missing",
        "token_valid": not expired,
        "token_expires_at_utc": expiration.isoformat() if expiration else None,
        "time_until_expiry": time_left,
        "auto_refresh_enabled": config_data.get("auto_refresh_enabled", True)
    }


@app.get("/logs")
async def get_logs():
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
    try:
        if LOG_FILE.exists():
            LOG_FILE.unlink()
        return {"status": "ok", "message": "Logs cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Web UI with full Device Control & Diagnostics
@app.get("/", response_class=HTMLResponse)
async def root():
    expiration = get_token_expiration()
    time_left = str(expiration - datetime.utcnow()) if expiration else "Not configured"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>U-tec Local Gateway</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f5f7fa; color: #333; }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            h1 {{ color: #2c3e50; margin-bottom: 5px; }}
            .subtitle {{ color: #7f8c8d; margin-bottom: 25px; }}
            .card {{ background: white; margin: 15px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .status-box {{ padding: 12px; border-radius: 6px; margin: 10px 0; font-weight: 500; }}
            .success {{ background: #d4edda; color: #155724; }}
            .warning {{ background: #fff3cd; color: #856404; }}
            button {{ padding: 10px 18px; border: none; border-radius: 6px; font-size: 14px; font-weight: 500; cursor: pointer; margin: 4px; }}
            .btn-primary {{ background: #3498db; color: white; }}
            .btn-success {{ background: #28a745; color: white; }}
            .btn-secondary {{ background: #6c757d; color: white; }}
            input, textarea {{ width: 100%; padding: 8px 12px; border: 1px solid #ccc; border-radius: 6px; margin: 6px 0; }}
            pre {{ background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 13px; max-height: 250px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 U-tec Local Gateway</h1>
            <p class="subtitle">Home Assistant Local Bridge & OAuth Auto-Renew Controller</p>
            
            <div class="card">
                <h3>📊 Gateway Health & Verification</h3>
                <div class="status-box {'success' if not is_token_expired() else 'warning'}">
                    Token Status: {'✅ Active & Auto-Renewing' if not is_token_expired() else '⚠️ Expired / Authorization Needed'}
                </div>
                <p><strong>Time Remaining until Auto-Renew:</strong> {time_left}</p>
                <button class="btn-secondary" onclick="checkHealth()">❤️ Test /health Endpoint</button>
                <button class="btn-secondary" onclick="manualRefresh()">🔄 Force Manual OAuth Refresh</button>
            </div>
            
            <div class="card">
                <h3>📱 Device Management & Controls</h3>
                <button class="btn-primary" onclick="loadDevices()">🔄 Discover Devices</button>
                <pre id="deviceOutput">Click "Discover Devices" to query U-tec account locks...</pre>
                
                <div style="margin-top: 15px;">
                    <label>Target Lock Device ID:</label>
                    <input type="text" id="targetId" placeholder="Paste Device ID here">
                    <button class="btn-success" onclick="controlLock('lock')">🔒 Test Lock</button>
                    <button class="btn-primary" onclick="controlLock('unlock')">🔓 Test Unlock</button>
                </div>
                <div id="cmdOutput" style="margin-top: 10px;"></div>
            </div>
            
            <div class="card">
                <h3>📜 Live Gateway & Home Assistant Logs</h3>
                <button class="btn-secondary" onclick="fetchLogs()">📄 Refresh Logs</button>
                <button class="btn-secondary" onclick="clearLogs()">🗑️ Clear Logs</button>
                <pre id="logOutput">Click "Refresh Logs" to view Home Assistant API activity...</pre>
            </div>
        </div>
        
        <script>
            async function checkHealth() {{
                const res = await fetch('/health');
                const data = await res.json();
                alert(JSON.stringify(data, null, 2));
            }}
            async function manualRefresh() {{
                const res = await fetch('/api/oauth/refresh', {{ method: 'POST' }});
                const data = await res.json();
                alert(data.message || JSON.stringify(data));
                location.reload();
            }}
            async function loadDevices() {{
                const out = document.getElementById('deviceOutput');
                out.textContent = '⏳ Fetching devices from U-tec...';
                try {{
                    const res = await fetch('/api/devices');
                    const data = await res.json();
                    out.textContent = JSON.stringify(data, null, 2);
                    const devs = data.payload?.devices || [];
                    if (devs.length > 0) document.getElementById('targetId').value = devs[0].id;
                }} catch(e) {{ out.textContent = '❌ Error: ' + e.message; }}
            }}
            async function controlLock(action) {{
                const id = document.getElementById('targetId').value.trim();
                const out = document.getElementById('cmdOutput');
                if(!id) {{ alert('Select or enter a Device ID'); return; }}
                out.textContent = '⏳ Sending command...';
                try {{
                    const res = await fetch('/api/' + action, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ id: id }})
                    }});
                    const data = await res.json();
                    out.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                }} catch(e) {{ out.textContent = '❌ Error: ' + e.message; }}
            }}
            async function fetchLogs() {{
                const res = await fetch('/logs');
                document.getElementById('logOutput').textContent = await res.text();
            }}
            async function clearLogs() {{
                await fetch('/logs/clear', {{ method: 'POST' }});
                document.getElementById('logOutput').textContent = 'Logs cleared.';
            }}
        </script>
    </body>
    </html>
    """
    return html_content


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
