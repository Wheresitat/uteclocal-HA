# U-tec Local Gateway Integration

Enhanced U-tec smart lock integration with automatic OAuth token refresh for Home Assistant.

## ✨ Features

- ✅ **Automatic Token Refresh** - Never re-authenticate manually
- ✅ **Lock Control** - Lock/unlock from Home Assistant
- ✅ **Battery Monitoring** - Track battery levels
- ✅ **Status Sensors** - Real-time lock status
- ✅ **Local Control** - No cloud dependency after setup

## 📋 Prerequisites

### 1. Deploy Gateway First

The integration requires a gateway to communicate with U-tec's API:

```bash
git clone https://github.com/YOUR_USERNAME/uteclocal-HA.git
cd uteclocal-HA
./deploy_docker.sh
```

Gateway will run on: `http://localhost:8000`

### 2. Complete OAuth Setup

1. Open `http://localhost:8000`
2. Enter your U-tec API credentials
3. Complete OAuth authorization
4. Verify devices appear

## 🚀 Installation

### Via HACS (Recommended)

1. **Add Custom Repository:**
   - HACS → Integrations → ⋮ → Custom repositories
   - Repository: `https://github.com/YOUR_USERNAME/uteclocal-HA`
   - Category: Integration
   - Click Add

2. **Install Integration:**
   - Search "U-tec Local Gateway"
   - Click Install
   - Restart Home Assistant

3. **Add Integration:**
   - Settings → Devices & Services → Add Integration
   - Search "U-tec Local Gateway"
   - Enter gateway URL: `http://YOUR_GATEWAY_IP:8000`

## 🎯 Configuration

When adding the integration, enter your gateway URL:
- Local: `http://192.168.1.40:8000`
- Same machine: `http://localhost:8000`

## 📱 Entities Created

For each lock:
- `lock.device_name` - Lock control
- `sensor.device_name_battery` - Battery level

## 🔧 Troubleshooting

### No Entities Appear

1. **Check gateway is reachable:**
   ```bash
   curl http://YOUR_GATEWAY_IP:8000/health
   ```

2. **Enable debug logging:**
   ```yaml
   logger:
     logs:
       custom_components.uteclocal: debug
   ```

3. **Check logs:** Settings → System → Logs → Search "uteclocal"

### Gateway Connection Failed

- Verify gateway is running: `docker ps | grep uteclocal`
- Check gateway logs: `docker logs uteclocal-gateway`
- Test URL in browser: `http://YOUR_GATEWAY_IP:8000`

## 📚 Full Documentation

See the [complete README](https://github.com/YOUR_USERNAME/uteclocal-HA) for:
- Detailed setup instructions
- Gateway configuration
- Home Assistant automation examples
- Advanced troubleshooting

## 🆘 Support

- **Issues:** https://github.com/YOUR_USERNAME/uteclocal-HA/issues
- **Discussions:** https://github.com/YOUR_USERNAME/uteclocal-HA/discussions
