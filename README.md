# U-tec Local Gateway - Enhanced with Auto-Refresh

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Home Assistant](https://img.shields.io/badge/home%20assistant-compatible-blue.svg)](https://www.home-assistant.io/)

Enhanced U-tec Local Gateway with **automatic OAuth token refresh** for Home Assistant integration.

## 🌟 What's New

This version adds automatic token refresh to prevent authentication expiration every few days:

- ✅ **Automatic token refresh** - No more manual re-authentication
- ✅ **Background scheduler** - Checks token status every 5 minutes
- ✅ **Smart retry logic** - Auto-retries failed API calls with fresh tokens
- ✅ **Persistent storage** - Tokens survive container restarts
- ✅ **Web UI controls** - Monitor status and manually trigger refresh
- ✅ **100% backward compatible** - Works with existing Home Assistant integration

## 🚀 Quick Start

```bash
# Clone this repository
git clone https://github.com/YOUR_USERNAME/uteclocal-HA.git
cd uteclocal-HA

# Run the automated installer
chmod +x deploy_docker.sh
./deploy_docker.sh

# Open web UI
http://localhost:8000
```

That's it! Your gateway now has automatic token refresh enabled.

## 📋 What This Solves

**Problem:** The U-tec gateway loses authentication every few days, requiring manual OAuth re-authentication and Home Assistant integration reload.

**Solution:** Automatic token refresh monitors token expiration and refreshes tokens proactively before they expire.

## 🔧 Requirements

- Docker & Docker Compose
- Home Assistant (optional, for lock integration)
- U-tec account with API credentials

## 📖 Documentation

- [Quick Start Guide](docs/QUICK_START.md) - Step-by-step installation
- [Docker Deployment Guide](docs/DOCKER_DEPLOYMENT_GUIDE.md) - Docker-specific details
- [Implementation Guide](docs/IMPLEMENTATION_GUIDE.md) - Technical details
- [Architecture Overview](docs/DOCKER_ARCHITECTURE.md) - How it works
- [Visual Guide](docs/VISUAL_GUIDE.md) - Diagrams and flowcharts

## 🏗️ Repository Structure

```
uteclocal-HA/
├── gateway/
│   ├── __init__.py
│   └── main.py              # Enhanced gateway with auto-refresh
├── custom_components/
│   └── uteclocal/           # Home Assistant integration
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
├── Dockerfile               # Docker image configuration
├── docker-compose.yml       # Docker Compose setup
├── requirements.txt         # Python dependencies
├── deploy_docker.sh         # Automated installer
├── test_gateway.sh          # Testing script
└── README.md               # This file
```

## 🎯 Features

### Automatic Token Management
- Proactive refresh 5 minutes before expiration
- Background scheduler monitors token lifecycle
- Automatic retry on 401 authentication errors
- Detailed logging of all refresh attempts

### Enhanced Reliability
- Persistent token storage in Docker volumes
- Survives container restarts and rebuilds
- Smart fallback mechanisms for API calls
- Health monitoring and auto-recovery

### Better UX
- Web-based configuration UI
- Real-time token status display
- Manual refresh button for testing
- Comprehensive logs viewer

## 🏠 Home Assistant Integration

No changes needed! Your existing Home Assistant integration continues working:

1. **Add Integration:** Settings → Devices & Services → "U-tec Local Gateway"
2. **Configure:**
   - Host: `http://localhost:8000` (or your gateway IP)
   - Leave API key blank (handled by gateway)
3. **Use:** Locks appear as `lock.*` entities with battery sensors

## 📊 How It Works

```
Every 5 minutes:
  ├─ Check token expiration time
  ├─ If expiring within 5 minutes:
  │  ├─ POST to oauth.u-tec.com/token
  │  ├─ Receive new access_token & refresh_token
  │  ├─ Save to persistent storage
  │  └─ Log success
  └─ Continue monitoring

On API request:
  ├─ Check token validity
  ├─ If expired → Auto-refresh
  ├─ If 401 error → Auto-refresh and retry
  └─ Return response
```

## 🔄 Updating

```bash
# Pull latest changes
cd uteclocal-HA
git pull origin main

# Rebuild and restart
docker compose -p uteclocal up -d --build
```

Your config and tokens are preserved!

## 🆘 Troubleshooting

**Gateway not accessible:**
```bash
# Check container status
docker compose -p uteclocal ps

# View logs
docker compose -p uteclocal logs -f gateway

# Restart
docker compose -p uteclocal restart gateway
```

**Token still expires:**
```bash
# Check auto-refresh is enabled
curl http://localhost:8000/health | jq '.auto_refresh_enabled'

# Should return: true
```

See [troubleshooting guide](docs/QUICK_START.md#troubleshooting) for more help.

## 🔒 Security

- Never commit `config.json` or token files
- Use `.gitignore` to exclude sensitive data
- Tokens stored in Docker volumes only
- OAuth credentials configured via web UI

## 📝 Configuration

Access web UI at `http://localhost:8000` to configure:

- API endpoints (U-tec cloud URLs)
- OAuth credentials (access key, secret key)
- Refresh settings (buffer time, auto-refresh toggle)
- View token status and expiration

## 🧪 Testing

```bash
# Run comprehensive tests
./test_gateway.sh

# Quick health check
curl http://localhost:8000/health

# Check token status
curl http://localhost:8000/api/config | jq '.token_status'
```

## 📈 Monitoring

```bash
# View logs
docker compose -p uteclocal logs -f gateway | grep refresh

# Check container health
docker compose -p uteclocal ps

# Access web UI
open http://localhost:8000
```

## 🙏 Credits

- Original gateway by [Wheresitat](https://github.com/Wheresitat)
- Enhanced with automatic token refresh
- Built for the Home Assistant community

## 📄 License

Same as original project

## 🌟 Support

If this helps you, please:
- ⭐ Star this repository
- 📢 Share with others having token issues
- 🐛 Report bugs via Issues
- 💡 Suggest improvements

---

**Enjoy uninterrupted smart lock control!** 🔐✨
