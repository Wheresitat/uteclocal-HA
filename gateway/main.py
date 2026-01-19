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
    # NOTE: Using exact header format from original uteclocal
    request_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config_data['access_token']}",
    }
    
    # Add any additional headers
    if headers:
        request_headers.update(headers)
    
    # Add payload with accessKey and secretKey IN THE BODY, not headers
    if json_data:
        json_data["accessKey"] = config_data.get("access_key", "")
        json_data["secretKey"] = config_data.get("secret_key", "")
    
    logger.info(f"Making {method} request to {url}")
    logger.info(f"Headers: {', '.join(request_headers.keys())}")
    logger.info(f"Payload keys: {list(json_data.keys()) if json_data else 'None'}")
    
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
                logger.info(f"Response headers: {dict(response.headers)}")
                if response.text:
                    logger.info(f"Response body preview: {response.text[:200]}")
                
                # If we get 401, try refreshing token
                if response.status_code == 401 and attempt < max_retries:
                    logger.warning(f"Got 401, attempting token refresh (attempt {attempt + 1})")
                    if await refresh_access_token():
                        # Update token in payload
                        request_headers["Authorization"] = f"Bearer {config_data['access_token']}"
                        if json_data:
                            json_data["accessKey"] = config_data.get("access_key", "")
                            json_data["secretKey"] = config_data.get("secret_key", "")
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


@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint to verify API is working"""
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


@app.get("/api/oauth/authorize-url")
async def get_authorize_url():
    """Generate OAuth authorization URL"""
    from urllib.parse import quote
    
    oauth_url = config_data.get("oauth_base_url", "https://oauth.u-tec.com")
    client_id = config_data.get("access_key", "")
    redirect_uri = config_data.get("redirect_uri", "")
    scope = config_data.get("scope", "openapi")
    
    logger.info(f"Generating auth URL with client_id: {client_id[:10]}..., redirect_uri: {redirect_uri}")
    
    if not client_id:
        raise HTTPException(
            status_code=400,
            detail="Please configure access_key (Client ID) first. Go to section 1 and save your configuration."
        )
    
    if not redirect_uri:
        raise HTTPException(
            status_code=400,
            detail="Please configure redirect_uri first. Go to section 1 and save your configuration."
        )
    
    # URL encode the parameters
    encoded_redirect = quote(redirect_uri, safe='')
    encoded_scope = quote(scope, safe='')
    
    # Build authorization URL
    auth_url = (
        f"{oauth_url}/authorize?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={encoded_redirect}&"
        f"scope={encoded_scope}"
    )
    
    logger.info(f"Generated auth URL: {auth_url}")
    
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
    """Get list of devices using correct U-tec API format"""
    try:
        import uuid
        
        api_url = config_data.get("api_base_url", "https://api.u-tec.com")
        action_path = config_data.get("action_path", "/action")
        endpoint = f"{api_url}{action_path}"
        
        logger.info(f"Fetching devices from: {endpoint}")
        
        # Use correct U-tec API format from documentation
        payload = {
            "header": {
                "namespace": "Uhome.Device",
                "name": "Discovery",
                "messageId": str(uuid.uuid4()),
                "payloadVersion": "1"
            },
            "payload": {}
        }
        
        logger.info(f"Request payload: {json.dumps(payload)}")
        
        response = await make_authenticated_request("POST", endpoint, json_data=payload)
        
        logger.info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("✅ Successfully retrieved devices!")
            return response.json()
        else:
            error_detail = f"API returned {response.status_code}: {response.text}"
            logger.error(error_detail)
            raise HTTPException(status_code=response.status_code, detail=error_detail)
    
    except TokenRefreshError as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(status_code=503, detail=f"Unable to reach U-tec API: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting devices: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/api/status")
async def query_status(request: Request):
    """Query device status using correct U-tec API format"""
    try:
        import uuid
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
    """Lock a device using correct U-tec API format"""
    try:
        import uuid
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
            raise HTTPException(status_code=response.status_code, detail=response.text)
    
    except TokenRefreshError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Error locking device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/unlock")
@app.post("/unlock")
async def unlock_device(request: Request):
    """Unlock a device using correct U-tec API format"""
    try:
        import uuid
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
        <title>U-tec Gateway Setup</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f7fa;
                color: #333;
            }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            h1 {{ color: #2c3e50; margin-bottom: 10px; }}
            .subtitle {{ color: #7f8c8d; margin-bottom: 30px; }}
            .step {{ 
                background: white;
                margin: 20px 0;
                padding: 25px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .step-header {{
                display: flex;
                align-items: center;
                margin-bottom: 15px;
            }}
            .step-number {{
                background: #3498db;
                color: white;
                width: 36px;
                height: 36px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                margin-right: 12px;
                flex-shrink: 0;
            }}
            .step-title {{ font-size: 20px; font-weight: 600; color: #2c3e50; }}
            .step-description {{ 
                color: #7f8c8d;
                margin-bottom: 15px;
                line-height: 1.6;
            }}
            .status {{ 
                padding: 12px 16px;
                border-radius: 6px;
                margin: 15px 0;
                border-left: 4px solid;
            }}
            .status-success {{ background: #d4edda; border-color: #28a745; color: #155724; }}
            .status-error {{ background: #f8d7da; border-color: #dc3545; color: #721c24; }}
            .status-warning {{ background: #fff3cd; border-color: #ffc107; color: #856404; }}
            .status-info {{ background: #d1ecf1; border-color: #17a2b8; color: #0c5460; }}
            button {{
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                font-size: 15px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
                margin: 5px 5px 5px 0;
            }}
            button:hover {{ transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0,0,0,0.15); }}
            .btn-primary {{ background: #3498db; color: white; }}
            .btn-primary:hover {{ background: #2980b9; }}
            .btn-success {{ background: #28a745; color: white; }}
            .btn-success:hover {{ background: #218838; }}
            .btn-secondary {{ background: #6c757d; color: white; }}
            .btn-secondary:hover {{ background: #5a6268; }}
            input, textarea {{
                width: 100%;
                padding: 10px 12px;
                border: 2px solid #e1e8ed;
                border-radius: 6px;
                font-size: 14px;
                margin: 8px 0;
                transition: border-color 0.2s;
            }}
            input:focus, textarea:focus {{
                outline: none;
                border-color: #3498db;
            }}
            textarea {{ 
                font-family: 'Courier New', monospace;
                min-height: 80px;
                resize: vertical;
            }}
            label {{ 
                display: block;
                font-weight: 500;
                margin-top: 12px;
                color: #2c3e50;
            }}
            .url-box {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 6px;
                margin: 15px 0;
                border: 2px solid #e1e8ed;
                word-break: break-all;
            }}
            .url-box a {{
                color: #3498db;
                text-decoration: none;
                font-weight: 500;
            }}
            .url-box a:hover {{ text-decoration: underline; }}
            pre {{
                background: #2c3e50;
                color: #ecf0f1;
                padding: 15px;
                border-radius: 6px;
                overflow-x: auto;
                font-size: 13px;
            }}
            .completed {{ opacity: 0.7; }}
            .completed .step-number {{ background: #28a745; }}
            .hidden {{ display: none; }}
            .token-info {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                margin: 10px 0;
            }}
            .token-item {{
                background: #f8f9fa;
                padding: 10px;
                border-radius: 4px;
            }}
            .token-label {{ font-size: 12px; color: #6c757d; }}
            .token-value {{ font-weight: 600; color: #2c3e50; margin-top: 4px; }}
            @media (max-width: 768px) {{
                .token-info {{ grid-template-columns: 1fr; }}
                button {{ width: 100%; margin: 5px 0; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 U-tec Gateway Setup</h1>
            <p class="subtitle">First-time setup & authentication - Follow these steps in order</p>
            
            <!-- STEP 1: Configuration -->
            <div class="step" id="step1">
                <div class="step-header">
                    <div class="step-number">1</div>
                    <div class="step-title">Enter Your Credentials</div>
                </div>
                <p class="step-description">
                    Enter your U-tec API credentials. These are used to communicate with U-tec's servers.
                </p>
                
                <label>Access Key (Client ID) <span style="color: #e74c3c;">*</span></label>
                <input type="text" id="accessKey" value="{config_data.get('access_key', '')}" 
                       placeholder="Enter your U-tec access key">
                
                <label>Secret Key (Client Secret) <span style="color: #e74c3c;">*</span></label>
                <input type="password" id="secretKey" value="{config_data.get('secret_key', '')}" 
                       placeholder="Enter your U-tec secret key">
                
                <label>Redirect URI <span style="color: #e74c3c;">*</span></label>
                <input type="text" id="redirectUri" value="{config_data.get('redirect_uri', '')}" 
                       placeholder="https://your-redirect-uri.com/callback">
                <small style="color: #6c757d;">This must match what you registered with U-tec</small>
                
                <details style="margin-top: 15px;">
                    <summary style="cursor: pointer; color: #3498db; font-weight: 500;">⚙️ Advanced Settings (usually don't need to change)</summary>
                    <div style="margin-top: 15px;">
                        <label>API Base URL</label>
                        <input type="text" id="apiBaseUrl" value="{config_data.get('api_base_url', 'https://api.u-tec.com')}">
                        
                        <label>OAuth Base URL</label>
                        <input type="text" id="oauthBaseUrl" value="{config_data.get('oauth_base_url', 'https://oauth.u-tec.com')}">
                        
                        <label>Scope</label>
                        <input type="text" id="scope" value="{config_data.get('scope', 'openapi')}">
                    </div>
                </details>
                
                <button class="btn-success" onclick="saveConfig()" style="margin-top: 20px;">
                    💾 Save Configuration & Continue
                </button>
                <div id="configStatus"></div>
            </div>
            
            <!-- STEP 2: Authorization -->
            <div class="step" id="step2">
                <div class="step-header">
                    <div class="step-number">2</div>
                    <div class="step-title">Authorize with U-tec</div>
                </div>
                <p class="step-description">
                    Click the button below to open U-tec's login page. You'll login with your <strong>U-tec account username and password</strong> (not the API keys from step 1).
                </p>
                
                <button class="btn-primary" onclick="startOAuth()">
                    🚀 Open U-tec Login Page
                </button>
                
                <div id="authUrlDisplay"></div>
            </div>
            
            <!-- STEP 3: Get Code -->
            <div class="step" id="step3">
                <div class="step-header">
                    <div class="step-number">3</div>
                    <div class="step-title">Copy the Redirect URL</div>
                </div>
                <p class="step-description">
                    After logging in and approving, U-tec will redirect you to a new page. <strong>Copy the entire URL</strong> from your browser's address bar and paste it below.
                </p>
                
                <div class="status status-info">
                    <strong>💡 Example:</strong> The URL will look something like:<br>
                    <code style="background: white; padding: 2px 6px; border-radius: 3px;">https://your-site.com/callback?code=abc123xyz789...</code>
                </div>
                
                <label>Paste the full redirect URL here:</label>
                <textarea id="redirectUrl" placeholder="Paste the entire URL from your browser's address bar here...

Example: https://your-redirect-uri.com/callback?code=abc123xyz789..."></textarea>
                
                <button class="btn-success" onclick="extractAndExchangeCode()">
                    🔑 Submit Code & Complete Setup
                </button>
                
                <div id="tokenDisplay"></div>
            </div>
            
            <!-- STEP 4: Done! -->
            <div class="step completed hidden" id="step4">
                <div class="step-header">
                    <div class="step-number">✓</div>
                    <div class="step-title">Setup Complete!</div>
                </div>
                
                <div class="status status-success">
                    <strong>🎉 Success!</strong> Your gateway is now authenticated and ready to use.
                </div>
                
                <div class="token-info">
                    <div class="token-item">
                        <div class="token-label">Token Status</div>
                        <div class="token-value" id="tokenStatus">{'✅ Valid' if not is_token_expired() else '❌ Expired'}</div>
                    </div>
                    <div class="token-item">
                        <div class="token-label">Auto-Refresh</div>
                        <div class="token-value">{'✅ Enabled' if config_data.get('auto_refresh_enabled', True) else '❌ Disabled'}</div>
                    </div>
                    <div class="token-item">
                        <div class="token-label">Token Expires</div>
                        <div class="token-value" id="tokenExpiry">{token_info}</div>
                    </div>
                    <div class="token-item">
                        <div class="token-label">Next Refresh</div>
                        <div class="token-value">Automatic</div>
                    </div>
                </div>
                
                <button class="btn-primary" onclick="showDevicesSection()">
                    📱 View My Devices
                </button>
                <button class="btn-secondary" onclick="location.reload()">
                    🔄 Refresh Status
                </button>
            </div>
            
            <!-- Devices Section (hidden until setup complete) -->
            <div class="step hidden" id="devicesSection">
                <div class="step-header">
                    <div class="step-title">📱 Device Management & Testing</div>
                </div>
                
                <h3>List Devices</h3>
                <button class="btn-primary" onclick="getDevices()">🔄 Refresh Device List</button>
                
                <pre id="deviceList" style="margin-top: 15px; max-height: 300px; overflow-y: auto;"></pre>
                
                <div id="deviceControls" class="hidden" style="margin-top: 30px;">
                    <h3>Test Device Control</h3>
                    <p class="step-description">
                        Select a device and send commands to test the connection.
                    </p>
                    
                    <label>Device MAC Address:</label>
                    <input type="text" id="deviceMac" placeholder="XX:XX:XX:XX:XX:XX or select from list above">
                    <small style="color: #6c757d;">Copy the MAC address from your device list above</small>
                    
                    <div style="margin-top: 15px;">
                        <button class="btn-success" onclick="lockDevice()">🔒 Lock Device</button>
                        <button class="btn-primary" onclick="unlockDevice()">🔓 Unlock Device</button>
                        <button class="btn-secondary" onclick="queryDevice()">📊 Query Status</button>
                    </div>
                    
                    <div id="commandResult" style="margin-top: 15px;"></div>
                </div>
            </div>
            
            <!-- Advanced Section -->
            <details style="margin-top: 20px;">
                <summary style="cursor: pointer; font-weight: 600; color: #2c3e50; padding: 15px; background: white; border-radius: 8px;">
                    🔧 Advanced Options
                </summary>
                <div style="background: white; padding: 20px; margin-top: 10px; border-radius: 8px;">
                    <h3>Token Management</h3>
                    <button class="btn-secondary" onclick="refreshToken()">🔄 Manually Refresh Token</button>
                    <button class="btn-secondary" onclick="checkHealth()">❤️ Check Health</button>
                    
                    <h3 style="margin-top: 20px;">Auto-Refresh Settings</h3>
                    <label style="display: inline-flex; align-items: center;">
                        <input type="checkbox" id="autoRefresh" {'checked' if config_data.get('auto_refresh_enabled', True) else ''} 
                               style="width: auto; margin-right: 8px;">
                        Enable automatic token refresh
                    </label>
                    <br>
                    <label style="margin-top: 10px;">
                        Refresh buffer (minutes before expiry):
                        <input type="number" id="refreshBuffer" value="{config_data.get('refresh_buffer_minutes', 5)}" 
                               min="1" max="60" style="width: 100px; display: inline-block; margin-left: 10px;">
                    </label>
                    <br>
                    <button class="btn-success" onclick="updateSettings()" style="margin-top: 10px;">💾 Save Settings</button>
                    
                    <h3 style="margin-top: 20px;">Logs</h3>
                    <button class="btn-secondary" onclick="getLogs()">📄 View Logs</button>
                    <button class="btn-secondary" onclick="clearLogs()">🗑️ Clear Logs</button>
                    <pre id="logs" style="max-height: 300px; overflow-y: auto; margin-top: 10px;"></pre>
                </div>
            </details>
        </div>
        
        <script>
            // Check if setup is complete on load
            window.onload = function() {{
                checkSetupStatus();
            }};
            
            function checkSetupStatus() {{
                fetch('/api/config')
                    .then(r => r.json())
                    .then(data => {{
                        if (data.access_token && data.access_token !== '***') {{
                            document.getElementById('step4').classList.remove('hidden');
                            document.getElementById('step1').classList.add('completed');
                            document.getElementById('step2').classList.add('completed');
                            document.getElementById('step3').classList.add('completed');
                        }}
                    }})
                    .catch(e => console.log('Status check:', e));
            }}
            
            async function saveConfig() {{
                const statusDiv = document.getElementById('configStatus');
                statusDiv.innerHTML = '<div class="status status-info">💾 Saving...</div>';
                
                try {{
                    const config = {{
                        api_base_url: document.getElementById('apiBaseUrl').value,
                        oauth_base_url: document.getElementById('oauthBaseUrl').value,
                        access_key: document.getElementById('accessKey').value.trim(),
                        secret_key: document.getElementById('secretKey').value.trim(),
                        scope: document.getElementById('scope').value,
                        redirect_uri: document.getElementById('redirectUri').value.trim()
                    }};
                    
                    // Validate required fields
                    if (!config.access_key) {{
                        statusDiv.innerHTML = '<div class="status status-error">❌ Please enter your Access Key</div>';
                        return;
                    }}
                    if (!config.secret_key) {{
                        statusDiv.innerHTML = '<div class="status status-error">❌ Please enter your Secret Key</div>';
                        return;
                    }}
                    if (!config.redirect_uri) {{
                        statusDiv.innerHTML = '<div class="status status-error">❌ Please enter your Redirect URI</div>';
                        return;
                    }}
                    
                    const response = await fetch('/api/config', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(config)
                    }});
                    
                    if (response.ok) {{
                        statusDiv.innerHTML = '<div class="status status-success">✅ Configuration saved! Now proceed to Step 2.</div>';
                        document.getElementById('step1').classList.add('completed');
                        setTimeout(() => {{
                            document.getElementById('step2').scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        }}, 1000);
                    }} else {{
                        statusDiv.innerHTML = '<div class="status status-error">❌ Failed to save configuration</div>';
                    }}
                }} catch (error) {{
                    statusDiv.innerHTML = '<div class="status status-error">❌ Error: ' + error.message + '</div>';
                }}
            }}
            
            async function startOAuth() {{
                const display = document.getElementById('authUrlDisplay');
                display.innerHTML = '<div class="status status-info">⏳ Generating authorization URL...</div>';
                
                try {{
                    const response = await fetch('/api/oauth/authorize-url');
                    
                    if (!response.ok) {{
                        const error = await response.json();
                        display.innerHTML = `<div class="status status-error">❌ ${{error.detail || 'Failed to generate URL'}}<br><br>Make sure you saved your configuration in Step 1 first!</div>`;
                        return;
                    }}
                    
                    const data = await response.json();
                    
                    // Show the URL and open it
                    display.innerHTML = `
                        <div class="status status-success">
                            <strong>✅ Opening U-tec login page...</strong>
                            <p>If it doesn't open automatically, <a href="${{data.url}}" target="_blank"><strong>click here</strong></a></p>
                        </div>
                        <div class="url-box">
                            <strong>Authorization URL:</strong><br>
                            <a href="${{data.url}}" target="_blank">${{data.url}}</a>
                        </div>
                        <div class="status status-info" style="margin-top: 15px;">
                            <strong>📝 What to do next:</strong>
                            <ol style="margin: 10px 0 0 20px; padding: 0;">
                                <li>Login with your U-tec account username and password</li>
                                <li>Click "Approve" or "Authorize"</li>
                                <li>Copy the URL from your browser's address bar</li>
                                <li>Paste it in Step 3 below</li>
                            </ol>
                        </div>
                    `;
                    
                    // Open in new tab
                    window.open(data.url, '_blank');
                    
                    // Mark step 2 complete and scroll to step 3
                    document.getElementById('step2').classList.add('completed');
                    setTimeout(() => {{
                        document.getElementById('step3').scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    }}, 2000);
                    
                }} catch (error) {{
                    display.innerHTML = `<div class="status status-error">❌ Error: ${{error.message}}</div>`;
                }}
            }}
            
            async function extractAndExchangeCode() {{
                const displayDiv = document.getElementById('tokenDisplay');
                const redirectUrl = document.getElementById('redirectUrl').value.trim();
                
                if (!redirectUrl) {{
                    displayDiv.innerHTML = '<div class="status status-error">❌ Please paste the redirect URL first!</div>';
                    return;
                }}
                
                displayDiv.innerHTML = '<div class="status status-info">⏳ Extracting code and getting tokens...</div>';
                
                try {{
                    // Extract code from URL
                    const url = new URL(redirectUrl);
                    const code = url.searchParams.get('code');
                    
                    if (!code) {{
                        displayDiv.innerHTML = `
                            <div class="status status-error">
                                ❌ No authorization code found in the URL.<br><br>
                                Make sure you pasted the <strong>complete URL</strong> from your browser's address bar.<br><br>
                                It should look like:<br>
                                <code style="background: white; padding: 4px 8px; border-radius: 3px;">
                                https://your-site.com/callback?code=abc123...
                                </code>
                            </div>
                        `;
                        return;
                    }}
                    
                    // Exchange code for tokens
                    const response = await fetch('/api/oauth/exchange', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ code: code }})
                    }});
                    
                    const data = await response.json();
                    
                    if (response.ok) {{
                        displayDiv.innerHTML = `
                            <div class="status status-success">
                                <strong>🎉 Success! Authentication complete!</strong><br>
                                Your gateway is now connected to U-tec.<br>
                                Tokens will automatically refresh every few hours.
                            </div>
                        `;
                        
                        // Show step 4 and mark step 3 complete
                        document.getElementById('step3').classList.add('completed');
                        document.getElementById('step4').classList.remove('hidden');
                        
                        // Scroll to completion
                        setTimeout(() => {{
                            document.getElementById('step4').scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        }}, 1000);
                        
                        // Refresh status in 2 seconds
                        setTimeout(() => {{
                            checkSetupStatus();
                        }}, 2000);
                    }} else {{
                        displayDiv.innerHTML = `
                            <div class="status status-error">
                                <strong>❌ Token exchange failed</strong><br>
                                ${{data.detail || 'Unknown error'}}<br><br>
                                Try the OAuth process again from Step 2.
                            </div>
                        `;
                    }}
                }} catch (error) {{
                    displayDiv.innerHTML = `
                        <div class="status status-error">
                            <strong>❌ Error:</strong> ${{error.message}}<br><br>
                            Make sure you pasted a valid URL.
                        </div>
                    `;
                }}
            }}
            
            function showDevicesSection() {{
                document.getElementById('devicesSection').classList.remove('hidden');
                document.getElementById('devicesSection').scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                getDevices();
            }}
            
            async function getDevices() {{
                const output = document.getElementById('deviceList');
                output.textContent = '⏳ Loading devices...';
                
                try {{
                    const response = await fetch('/api/devices');
                    
                    if (!response.ok) {{
                        const errorText = await response.text();
                        let errorData;
                        try {{
                            errorData = JSON.parse(errorText);
                        }} catch(e) {{
                            errorData = {{ detail: errorText }};
                        }}
                        throw new Error(errorData.detail || `HTTP ${{response.status}}: ${{response.statusText}}`);
                    }}
                    
                    const data = await response.json();
                    output.textContent = JSON.stringify(data, null, 2);
                    
                    // Try to extract device list and enable controls
                    if (data && data.payload && data.payload.devices) {{
                        document.getElementById('deviceControls').classList.remove('hidden');
                        
                        // Show simplified device list
                        const devices = data.payload.devices;
                        if (devices.length > 0) {{
                            let deviceSummary = '\\n📱 Found ' + devices.length + ' device(s):\\n\\n';
                            devices.forEach((device, index) => {{
                                deviceSummary += `${{index + 1}}. ${{device.name || 'Unnamed Device'}}\\n`;
                                deviceSummary += `   MAC: ${{device.id}}\\n`;
                                deviceSummary += `   Type: ${{device.type || 'Unknown'}}\\n\\n`;
                            }});
                            output.textContent = deviceSummary + '\\nFull JSON:\\n' + JSON.stringify(data, null, 2);
                            
                            // Auto-fill first device MAC
                            if (devices[0] && devices[0].id) {{
                                document.getElementById('deviceMac').value = devices[0].id;
                            }}
                        }}
                    }} else {{
                        document.getElementById('deviceControls').classList.remove('hidden');
                    }}
                }} catch (error) {{
                    output.innerHTML = `<div class="status status-error">
❌ Error loading devices: ${{error.message}}

Possible causes:
1. Authentication token may have expired
2. API endpoint might be incorrect
3. Network connectivity issue

Try:
- Click "Refresh Status" in Step 4
- Check logs in Advanced Options
- Manually refresh token

Full error: ${{error.stack || error.message}}
</div>`;
                }}
            }}
            
            async function lockDevice() {{
                const mac = document.getElementById('deviceMac').value.trim();
                const resultDiv = document.getElementById('commandResult');
                
                if (!mac) {{
                    resultDiv.innerHTML = '<div class="status status-error">❌ Please enter a device MAC address</div>';
                    return;
                }}
                
                resultDiv.innerHTML = '<div class="status status-info">🔒 Sending lock command...</div>';
                
                try {{
                    const response = await fetch('/api/lock', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ id: mac }})
                    }});
                    
                    const data = await response.json();
                    
                    if (response.ok) {{
                        resultDiv.innerHTML = `<div class="status status-success">
✅ Lock command sent successfully!
<pre>${{JSON.stringify(data, null, 2)}}</pre>
</div>`;
                    }} else {{
                        throw new Error(data.detail || 'Lock command failed');
                    }}
                }} catch (error) {{
                    resultDiv.innerHTML = `<div class="status status-error">❌ Error: ${{error.message}}</div>`;
                }}
            }}
            
            async function unlockDevice() {{
                const mac = document.getElementById('deviceMac').value.trim();
                const resultDiv = document.getElementById('commandResult');
                
                if (!mac) {{
                    resultDiv.innerHTML = '<div class="status status-error">❌ Please enter a device MAC address</div>';
                    return;
                }}
                
                resultDiv.innerHTML = '<div class="status status-info">🔓 Sending unlock command...</div>';
                
                try {{
                    const response = await fetch('/api/unlock', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ id: mac }})
                    }});
                    
                    const data = await response.json();
                    
                    if (response.ok) {{
                        resultDiv.innerHTML = `<div class="status status-success">
✅ Unlock command sent successfully!
<pre>${{JSON.stringify(data, null, 2)}}</pre>
</div>`;
                    }} else {{
                        throw new Error(data.detail || 'Unlock command failed');
                    }}
                }} catch (error) {{
                    resultDiv.innerHTML = `<div class="status status-error">❌ Error: ${{error.message}}</div>`;
                }}
            }}
            
            async function queryDevice() {{
                const mac = document.getElementById('deviceMac').value.trim();
                const resultDiv = document.getElementById('commandResult');
                
                if (!mac) {{
                    resultDiv.innerHTML = '<div class="status status-error">❌ Please enter a device MAC address</div>';
                    return;
                }}
                
                resultDiv.innerHTML = '<div class="status status-info">📊 Querying device status...</div>';
                
                try {{
                    const response = await fetch('/api/status', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ id: mac }})
                    }});
                    
                    const data = await response.json();
                    
                    if (response.ok) {{
                        resultDiv.innerHTML = `<div class="status status-success">
✅ Device status retrieved!
<pre>${{JSON.stringify(data, null, 2)}}</pre>
</div>`;
                    }} else {{
                        throw new Error(data.detail || 'Status query failed');
                    }}
                }} catch (error) {{
                    resultDiv.innerHTML = `<div class="status status-error">❌ Error: ${{error.message}}</div>`;
                }}
            }}
            
            async function refreshToken() {{
                try {{
                    const response = await fetch('/api/oauth/refresh', {{ method: 'POST' }});
                    const data = await response.json();
                    alert('✅ ' + (data.message || 'Token refreshed successfully!'));
                    location.reload();
                }} catch (error) {{
                    alert('❌ Error: ' + error.message);
                }}
            }}
            
            async function checkHealth() {{
                try {{
                    const response = await fetch('/health');
                    const data = await response.json();
                    alert(JSON.stringify(data, null, 2));
                }} catch (error) {{
                    alert('❌ Error: ' + error.message);
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
                    
                    if (response.ok) {{
                        alert('✅ Settings saved!');
                        location.reload();
                    }}
                }} catch (error) {{
                    alert('❌ Error: ' + error.message);
                }}
            }}
            
            async function getLogs() {{
                try {{
                    const response = await fetch('/logs');
                    const logs = await response.text();
                    document.getElementById('logs').textContent = logs;
                }} catch (error) {{
                    document.getElementById('logs').textContent = '❌ Error: ' + error.message;
                }}
            }}
            
            async function clearLogs() {{
                if (confirm('Clear all logs?')) {{
                    try {{
                        await fetch('/logs/clear', {{ method: 'POST' }});
                        document.getElementById('logs').textContent = '✅ Logs cleared';
                        alert('✅ Logs cleared');
                    }} catch (error) {{
                        alert('❌ Error: ' + error.message);
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
