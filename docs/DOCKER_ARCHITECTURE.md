# U-tec Gateway Docker Architecture

## 🏗️ Container Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Docker Host                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         uteclocal-gateway Container                      │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────┐     │  │
│  │  │  FastAPI Gateway (Python 3.11)                 │     │  │
│  │  │  ├─ uvicorn (ASGI server)                      │     │  │
│  │  │  ├─ APScheduler (background jobs)              │     │  │
│  │  │  │  ├─ Token refresh check (every 5 min)       │     │  │
│  │  │  │  └─ Device status poll (configurable)       │     │  │
│  │  │  └─ httpx (API client)                         │     │  │
│  │  └────────────────────────────────────────────────┘     │  │
│  │                                                          │  │
│  │  Port Mapping:  8000:8000                               │  │
│  │                                                          │  │
│  │  Volume Mount:  uteclocal-data → /data                  │  │
│  │                                                          │  │
│  │  Health Check:  curl localhost:8000/health              │  │
│  │                 (every 30 seconds)                       │  │
│  │                                                          │  │
│  │  Restart:       unless-stopped                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Docker Volume: uteclocal-data                    │  │
│  │  /var/lib/docker/volumes/uteclocal_uteclocal-data/      │  │
│  │                                                          │  │
│  │  ├── config.json         (OAuth tokens, settings)       │  │
│  │  │   ├─ access_token                                    │  │
│  │  │   ├─ refresh_token                                   │  │
│  │  │   ├─ token_expires_at                                │  │
│  │  │   ├─ auto_refresh_enabled: true                      │  │
│  │  │   └─ refresh_buffer_minutes: 5                       │  │
│  │  │                                                       │  │
│  │  └── gateway.log         (Rotating logs)                │  │
│  │      └─ Token refresh events, API calls, errors         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
         │                                      │
         │ Port 8000                            │ HTTPS
         ▼                                      ▼
    ┌─────────┐                        ┌────────────────┐
    │  Home   │                        │   U-tec Cloud  │
    │Assistant│                        │   API Server   │
    │Container│                        │ api.u-tec.com  │
    └─────────┘                        └────────────────┘
```

## 🔄 Token Refresh Flow in Docker

```
┌─────────────────────────────────────────────────────────────────┐
│              Container: uteclocal-gateway                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [APScheduler Background Jobs]                                 │
│                                                                 │
│  Job 1: Token Refresh Check (Every 5 minutes)                  │
│  ┌─────────────────────────────────────────────────┐           │
│  │  1. Read /data/config.json                      │           │
│  │  2. Check token_expires_at                      │           │
│  │  3. If expiring soon (< 5 min):                 │           │
│  │     ├─ POST to oauth.u-tec.com/token            │────────┐  │
│  │     │  (grant_type: refresh_token)              │        │  │
│  │     ├─ Receive new access_token                 │        │  │
│  │     ├─ Update /data/config.json                 │        │  │
│  │     └─ Log: "Token refreshed successfully"      │        │  │
│  └─────────────────────────────────────────────────┘        │  │
│         │                                                    │  │
│         │ Data persists in volume                           │  │
│         ▼                                                    │  │
│  [Docker Volume: uteclocal-data]                            │  │
│  /data/config.json ← Updated atomically                     │  │
│                                                              │  │
│  Job 2: Device Status Poll (Every 60s default)              │  │
│  ┌─────────────────────────────────────────────────┐        │  │
│  │  1. Ensure token valid (auto-refresh if needed) │        │  │
│  │  2. POST to api.u-tec.com/action                │────────┤  │
│  │  3. Cache results in memory                     │        │  │
│  │  4. Update last_status_update timestamp         │        │  │
│  └─────────────────────────────────────────────────┘        │  │
│                                                              │  │
│  [FastAPI Endpoints]                                         │  │
│  ┌─────────────────────────────────────────────────┐        │  │
│  │  POST /api/lock (from Home Assistant)           │        │  │
│  │  ├─ Call: ensure_valid_token()                  │        │  │
│  │  │  └─ If expired → refresh automatically       │        │  │
│  │  ├─ Call: make_authenticated_request()          │────────┤  │
│  │  │  └─ If 401 → retry with refreshed token      │        │  │
│  │  └─ Return result to Home Assistant             │        │  │
│  └─────────────────────────────────────────────────┘        │  │
│                                                              │  │
└──────────────────────────────────────────────────────────────┘  │
                                                                  │
                         External Calls                           │
                         ═══════════════                           │
                                                                  │
┌─────────────────────┐         ┌──────────────────────┐        │
│   oauth.u-tec.com   │◄────────┤ Token Refresh        │◄───────┘
│   /token            │         │ POST with            │
│                     │         │ refresh_token        │
└─────────────────────┘         └──────────────────────┘
         │
         │ Returns: new access_token
         │          new refresh_token (optional)
         │          expires_in (seconds)
         │
         ▼
┌─────────────────────┐
│ /data/config.json   │ ← Updated in Docker volume
│ (persists forever)  │    Survives container restarts
└─────────────────────┘
```

## 🏠 Home Assistant Integration

```
┌────────────────────────────────────────────────┐
│        Home Assistant Container/Host           │
│                                                │
│  ┌──────────────────────────────────────┐     │
│  │  U-tec Local Gateway Integration     │     │
│  │  (custom_components/uteclocal)       │     │
│  │                                       │     │
│  │  Config:                              │     │
│  │  └─ Gateway Host: http://uteclocal-   │     │
│  │                   gateway:8000        │     │
│  │    OR                                 │     │
│  │  └─ Gateway Host: http://192.168.1.X  │     │
│  │                   :8000               │     │
│  │                                       │     │
│  │  Creates entities:                    │     │
│  │  ├─ lock.front_door                   │     │
│  │  ├─ sensor.front_door_battery         │     │
│  │  └─ sensor.front_door_status          │     │
│  └──────────────────────────────────────┘     │
│             │                                  │
│             │ HTTP Requests                    │
│             │                                  │
└─────────────┼──────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│      Docker Network: uteclocal-network          │
│                                                 │
│  Container: uteclocal-gateway                  │
│  └─ Responds to lock/unlock commands           │
│  └─ Returns device status                      │
│  └─ Handles token refresh transparently        │
└─────────────────────────────────────────────────┘
```

## 📊 Data Persistence Across Restarts

```
Event Timeline:
═══════════════

T=0     Container starts
        ├─ Reads /data/config.json
        ├─ Loads tokens (if present)
        ├─ Starts schedulers
        └─ Gateway ready

T=5min  First scheduled token check
        ├─ Token still valid
        └─ No action needed

T=60min Home Assistant locks door
        ├─ Token check: valid
        ├─ API call succeeds
        └─ Returns success

T=3hr   Token expiring soon
        ├─ Scheduler detects expiration
        ├─ Refreshes token automatically
        ├─ Saves to /data/config.json
        └─ Log: "Token refreshed successfully"

T=3.5hr Container restart (docker compose restart)
        ├─ Reads /data/config.json
        ├─ Loads FRESH tokens ✅
        ├─ Continues operation
        └─ No re-authentication needed!

T=4hr   Home Assistant unlocks door
        ├─ Token valid (refreshed earlier)
        ├─ API call succeeds
        └─ Everything works!

T=6hr   Another token refresh
        ├─ Automatic refresh
        ├─ Saves to volume
        └─ Continuous operation

INFINITE LOOP - No manual intervention needed! 🎉
```

## 🔒 Security & Isolation

```
┌─────────────────────────────────────────────────┐
│              Docker Security Layers             │
├─────────────────────────────────────────────────┤
│                                                 │
│  [Network Isolation]                            │
│  ├─ Custom bridge network                      │
│  ├─ Only exposed port: 8000                    │
│  └─ No direct access to host network           │
│                                                 │
│  [File System Isolation]                        │
│  ├─ Container has own filesystem                │
│  ├─ Only /data mounted as volume               │
│  └─ Config.json protected by volume perms      │
│                                                 │
│  [Process Isolation]                            │
│  ├─ Runs as non-root inside container          │
│  ├─ Isolated from host processes               │
│  └─ Resource limits configurable               │
│                                                 │
│  [Secrets Management]                           │
│  ├─ Tokens stored in Docker volume             │
│  ├─ Not in image layers                        │
│  ├─ Not in environment variables               │
│  └─ Persisted across rebuilds                  │
│                                                 │
└─────────────────────────────────────────────────┘
```

## 🚀 Deployment Flow

```
Developer's Machine                Docker Host
═══════════════════                ════════════

1. Copy enhanced files
   gateway_main_enhanced.py  ──────────┐
   requirements_enhanced.txt           │
   docker-compose.yml       ──────────┤
   Dockerfile               ──────────┤
   .dockerignore           ──────────┤
                                      │
2. Run deploy script                  │
   ./deploy_docker.sh                 │
                                      ▼
                           ┌──────────────────────┐
                           │ docker compose build │
                           └──────────┬───────────┘
                                      │
                           ┌──────────▼───────────┐
                           │ Build image:         │
                           │ - Python 3.11 base   │
                           │ - Install deps       │
                           │ - Copy gateway code  │
                           └──────────┬───────────┘
                                      │
                           ┌──────────▼───────────┐
                           │ docker compose up -d │
                           └──────────┬───────────┘
                                      │
                           ┌──────────▼────────────┐
                           │ Start container:      │
                           │ - Create volume       │
                           │ - Mount /data         │
                           │ - Expose port 8000    │
                           │ - Start health checks │
                           └──────────┬────────────┘
                                      │
                           ┌──────────▼────────────┐
                           │ Gateway ready!        │
                           │ - Web UI accessible   │
                           │ - API endpoints live  │
                           │ - Scheduler running   │
                           │ ✅ Auto-refresh active│
                           └───────────────────────┘
```

## 📈 Resource Usage

```
Typical Docker Container Stats:
═══════════════════════════════

Container: uteclocal-gateway
├─ CPU:     < 1% (idle)
│           2-5% (during API calls)
│
├─ Memory:  ~50-80 MB (typical)
│           ~100 MB (peak with scheduler)
│
├─ Disk:    ~200 MB (image)
│           ~1-5 MB (volume data)
│
└─ Network: Minimal
            - Token refresh: ~1 KB every few hours
            - Status polls: ~2-5 KB per minute
            - Lock commands: ~1-2 KB per operation

Very lightweight! 🪶
```

## 🎯 Summary

**The Docker implementation provides:**

✅ Complete isolation from host system  
✅ Persistent storage via Docker volumes  
✅ Automatic health monitoring  
✅ Auto-restart on failures  
✅ Easy updates (just rebuild)  
✅ Portable across hosts  
✅ No manual token management needed  
✅ Production-ready deployment  

**Your tokens and config survive:**
- ✅ Container restarts
- ✅ Container rebuilds  
- ✅ Image updates
- ✅ Host reboots
- ✅ Docker daemon restarts

**You'll never need to:**
- ❌ Manually re-authenticate
- ❌ Reload Home Assistant integration
- ❌ Worry about token expiration
- ❌ Monitor authentication status

**It just works!** 🎉
