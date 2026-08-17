"""
Enhanced U-tec Gateway with Automatic Token Refresh
This version includes:
- Robust refresh_token preservation (prevents token dropping)
- UTC-based expiration calculations to prevent timezone drift
- Retried requests and error handling
- Background refresh scheduler
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
    "token_expires_at": None,  # Store as ISO format string (UTC)
    "status_poll_interval": 60,
    "auto_refresh_enabled": True,
    "refresh_buffer_minutes": 15,  # Increased default buffer to 15 mins for safety
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
    """Get token expiration as datetime object (UTC)"""
    if config_data.get("token_expires_at"):
        try:
            return datetime.fromisoformat(config_data["token_expires_at"])
        except (ValueError, TypeError):
            return None
    return None


def set_token_expiration(expires_in: int):
    """Set token expiration time using UTC timestamp to prevent drift."""
    expiration = datetime.utcnow() + timedelta(seconds=int(expires_in))
    config_data["token_expires_at"] = expiration.isoformat()
    save_config()
    logger.info(f"Token will expire at (UTC): {expiration}")


def is_token_expired() -> bool:
    """Check if the access token is expired or about to expire using UTC."""
    expiration = get_token_expiration()
    if not expiration:
        return True
    
    buffer = timedelta(minutes=config_data.get("refresh_buffer_minutes", 15))
    return datetime.utcnow() + buffer >= expiration


async def refresh_access_token() -> bool:
    """
    Refresh access token safely without dropping existing refresh tokens.
    """
    if not config_data.get("refresh_token"):
        logger.error("No refresh token available in configuration")
        return False
    
    logger.info("Attempting to refresh access token...")
    
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
            
            logger.info(f"Token refresh response status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Update access token
                if token_data.get("access_token"):
                    config_data["access_token"] = token_data["access_token"]
                
                # Only overwrite refresh_token if a valid non-empty string is explicitly returned
                if token_data.get("refresh_token"):
                    config_data["refresh_token"] = token_data["refresh_token"]
                    logger.info("New refresh token received and updated")
                
                # Set expiration time (defaults to 3600 seconds if missing)
                expires_in = token_data.get("expires_in", 3600)
                set_token_expiration(expires_in)
                
                save_config()
                logger.info("Access token refreshed successfully")
                return True
            else:
                logger.error(f"Token refresh failed (HTTP {response.status_code}): {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error refreshing token: {e}", exc_info=True)
        return False


async def ensure_valid_token() -> bool:
    """
    Ensure we have a valid access token, refresh if necessary
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
    
    request_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config_data['access_token']}",
    }
    
    if headers:
        request_headers.update(headers)
    
    if json_data:
        json_data["accessKey"] = config_data.get("access_key", "")
        json_data["secretKey"] = config_data.get("secret_key", "")
    
    logger.info(f"Making {method} request to {url}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(max_retries + 1):
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=request_headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=request_headers, json=json_data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                logger.info(f"Response status: {response.status_code}")
                
                # If we get 401, attempt token refresh and retry request
                if response.status_code == 401 and attempt < max_retries:
                    logger.warning(f"Got 401, attempting token refresh (attempt {attempt + 1})")
                    if await refresh_access_token():
                        request_headers["Authorization"] = f"Bearer {config_data['access_token']}"
                        if json_data:
                            json_data["accessKey"] = config_data.get("access_key", "")
                            json_data["secretKey"] = config_data.get("secret_key", "")
                        continue
                
                return response
                
            except httpx.TimeoutException:
                if attempt < max_retries:
                    logger.warning(f"Request timeout, retrying... (attempt {attempt + 1})")
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Request failed: {e}, retrying... (attempt {attempt + 1})")
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
        
        raise Exception("Max retries exceeded")


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


async def poll_device_status():
    """Background task to poll device status"""
    global latest_devices, latest_status, last_status_update
    
    try:
        if not await ensure_valid_token():
            logger.warning("Skipping status poll - no valid token")
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
                    logger.info(f"Status poll successful - {len(devices)} devices")
        
    except Exception as e:
        logger.error(f"Error in status poll: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
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
    logger.info("Gateway started with automatic token refresh enabled")
    
    expiration = get_token_expiration()
    if expiration:
        logger.info(f"Current token expires at (UTC): {expiration}")


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
    
    if config.status_poll_interval is not None:
        scheduler.reschedule_job(
            'status_poll',
            trigger=IntervalTrigger(seconds=config.status_poll_interval)
        )
    
    return {"status": "ok", "message": "Configuration updated"}


@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {
        "status": "ok",
        "message": "API is working",
        "config_loaded": bool(config_data.get("access_key")),
        "has_tokens": bool(config_data.get("access_token"))
    }


@app.get("/api/config")
async def get_config():
    """Get current configuration (without sensitive data)"""
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
    """Generate OAuth authorization URL"""
    oauth_url = config_data.get("oauth_base_url", "https://oauth.u-tec.com")
    client_id = config_data.get("access_key", "")
    redirect_uri = config_data.get("redirect_uri", "")
    scope = config_data.get("scope", "openapi")
    
    if not client_id or not redirect_uri:
        raise HTTPException(
            status_code=400,
            detail="Please configure access_key and redirect_uri first."
        )
    
    encoded_redirect = quote(redirect_uri, safe='')
    encoded_scope = quote(scope, safe='')
    
    auth_url = (
        f"{oauth_url}/authorize?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={encoded_redirect}&"
        f"scope={encoded_scope}"
    )
    
    return {"url": auth_url, "success": True}


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
                if token_data.get("refresh_token"):
                    config_data["refresh_token"] = token_data.get("refresh_token", "")
                
                expires_in = token_data.get("expires_in", 3600)
                set_token_expiration(expires_in)
                
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
    """Get list of devices using correct U-tec API format"""
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
    """Query device status using correct U-tec API format"""
    try:
        body = await request.json()
        device_id = body.get("id")
        
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
    """Lock a device"""
    try:
        body = await request.json()
        device_id = body.get("id")
        
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
            return response.json()
        else:
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


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve a simple web UI"""
    expiration = get_token_expiration()
    token_info = ""
    if expiration:
        time_left = expiration - datetime.utcnow()
        token_info = f"Token expires in: {time_left}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>U-tec Gateway Setup</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f5f7fa; color: #333; }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            h1 {{ color: #2c3e50; margin-bottom: 10px; }}
            .subtitle {{ color: #7f8c8d; margin-bottom: 30px; }}
            .step {{ background: white; margin: 20px 0; padding: 25px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .step-header {{ display: flex; align-items: center; margin-bottom: 15px; }}
            .step-number {{ background: #3498db; color: white; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 12px; flex-shrink: 0; }}
            .step-title {{ font-size: 20px; font-weight: 600; color: #2c3e50; }}
            .step-description {{ color: #7f8c8d; margin-bottom: 15px; line-height: 1.6; }}
            .status {{ padding: 12px 16px; border-radius: 6px; margin: 15px 0; border-left: 4px solid; }}
            .status-success {{ background: #d4edda; border-color: #28a745; color: #155724; }}
            .status-error {{ background: #f8d7da; border-color: #dc3545; color: #721c24; }}
            .status-info {{ background: #d1ecf1; border-color: #17a2b8; color: #0c5460; }}
            button {{ padding: 12px 24px; border: none; border-radius: 6px; font-size: 15px; font-weight: 500; cursor: pointer; transition: all 0.2s; margin: 5px 5px 5px 0; }}
            button:hover {{ transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0,0,0,0.15); }}
            .btn-primary {{ background: #3498db; color: white; }}
            .btn-success {{ background: #28a745; color: white; }}
            .btn-secondary {{ background: #6c757d; color: white; }}
            input, textarea {{ width: 100%; padding: 10px 12px; border: 2px solid #e1e8ed; border-radius: 6px; font-size: 14px; margin: 8px 0; }}
            pre {{ background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 13px; }}
            .completed {{ opacity: 0.7; }}
            .completed .step-number {{ background: #28a745; }}
            .hidden {{ display: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 U-tec Gateway Setup</h1>
            <p class="subtitle">First-time setup & authentication</p>
            
            <div class="step" id="step1">
                <div class="step-header">
                    <div class="step-number">1</div>
                    <div class="step-title">Enter Your Credentials</div>
                </div>
                <label>Access Key (Client ID)</label>
                <input type="text" id="accessKey" value="{config_data.get('access_key', '')}">
                
                <label>Secret Key (Client Secret)</label>
                <input type="password" id="secretKey" value="{config_data.get('secret_key', '')}">
                
                <label>Redirect URI</label>
                <input type="text" id="redirectUri" value="{config_data.get('redirect_uri', '')}">
                
                <button class="btn-success" onclick="saveConfig()">💾 Save Configuration</button>
                <div id="configStatus"></div>
            </div>
            
            <div class="step" id="step2">
                <div class="step-header">
                    <div class="step-number">2</div>
                    <div class="step-title">Authorize with U-tec</div>
                </div>
                <button class="btn-primary" onclick="startOAuth()">🚀 Open U-tec Login Page</button>
                <div id="authUrlDisplay"></div>
            </div>
            
            <div class="step" id="step3">
                <div class="step-header">
                    <div class="step-number">3</div>
                    <div class="step-title">Copy the Redirect URL</div>
                </div>
                <textarea id="redirectUrl" placeholder="Paste the entire URL from browser address bar..."></textarea>
                <button class="btn-success" onclick="extractAndExchangeCode()">🔑 Submit Code</button>
                <div id="tokenDisplay"></div>
            </div>
            
            <div class="step completed hidden" id="step4">
                <div class="step-header">
                    <div class="step-number">✓</div>
                    <div class="step-title">Setup Complete!</div>
                </div>
                <div class="status status-success">
                    <strong>🎉 Success!</strong> Gateway authenticated.
                </div>
            </div>
        </div>
        <script>
            async function saveConfig() {{
                const config = {{
                    access_key: document.getElementById('accessKey').value.trim(),
                    secret_key: document.getElementById('secretKey').value.trim(),
                    redirect_uri: document.getElementById('redirectUri').value.trim()
                }};
                await fetch('/api/config', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(config)
                }});
                alert('Saved!');
            }}
            async function startOAuth() {{
                const res = await fetch('/api/oauth/authorize-url');
                const data = await res.json();
                if(data.url) window.open(data.url, '_blank');
            }}
            async function extractAndExchangeCode() {{
                const redirectUrl = document.getElementById('redirectUrl').value.trim();
                const url = new URL(redirectUrl);
                const code = url.searchParams.get('code');
                const res = await fetch('/api/oauth/exchange', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ code }})
                }});
                if(res.ok) alert('Authentication complete!');
            }}
        </script>
    </body>
    </html>
    """
    return html_content


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
