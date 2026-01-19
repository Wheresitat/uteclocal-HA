# 🎯 HACS Integration Setup

## Current Situation

You're installing via **HACS** (Home Assistant Community Store), which has specific requirements.

---

## 📋 HACS Requirements

For HACS to work properly, your repository needs:

### 1. **hacs.json** in Repository Root

Create `uteclocal-HA/hacs.json`:

```json
{
  "name": "U-tec Local Gateway",
  "content_in_root": false,
  "render_readme": true,
  "domains": ["lock", "sensor"],
  "homeassistant": "2023.1.0"
}
```

**Important:** `"content_in_root": false` tells HACS to look in `custom_components/uteclocal/`

---

### 2. **info.md** (Optional but Recommended)

Create `uteclocal-HA/info.md`:

```markdown
# U-tec Local Gateway Integration

Enhanced U-tec integration with automatic OAuth token refresh.

## Features
- ✅ Automatic token refresh
- ✅ Lock/unlock control
- ✅ Battery sensors
- ✅ No manual re-authentication

## Setup
1. Install this integration via HACS
2. Deploy the gateway (see README)
3. Add integration in Home Assistant
```

---

### 3. **Verify manifest.json**

Your `custom_components/uteclocal/manifest.json` should have:

```json
{
  "domain": "uteclocal",
  "name": "U-tec Local Gateway",
  "codeowners": ["@YOUR_GITHUB_USERNAME"],
  "config_flow": true,
  "dependencies": [],
  "documentation": "https://github.com/YOUR_USERNAME/uteclocal-HA",
  "integration_type": "hub",
  "iot_class": "local_polling",
  "requirements": [],
  "version": "1.5.0"
}
```

---

## 🚀 Repository Structure for HACS

Your current structure is **already correct** for HACS:

```
uteclocal-HA/                          # Repository root
├── hacs.json                          # ← Add this!
├── info.md                            # ← Add this (optional)
├── README.md
├── custom_components/                 # HACS looks here
│   └── uteclocal/                     # Integration files
│       ├── __init__.py
│       ├── config_flow.py
│       ├── lock.py
│       ├── sensor.py
│       ├── manifest.json
│       └── strings.json
├── gateway/                           # Gateway (not installed by HACS)
│   └── main.py
├── docker-compose.yml
└── Dockerfile
```

---

## 📦 How HACS Installs Your Integration

When someone installs via HACS:

1. **HACS reads `hacs.json`**
2. **HACS copies `custom_components/uteclocal/` → `~/.homeassistant/custom_components/uteclocal/`**
3. **User restarts Home Assistant**
4. **Integration appears in Settings → Integrations**

**Note:** HACS **only installs the integration**, NOT the gateway!

---

## 🎯 Two-Part Setup for Users

### Part 1: Deploy Gateway (Manual)

Users must still deploy the gateway separately:

```bash
git clone https://github.com/YOUR_USERNAME/uteclocal-HA.git
cd uteclocal-HA
./deploy_docker.sh
```

**Gateway runs on:** `http://localhost:8000`

---

### Part 2: Install Integration (via HACS)

1. **HACS → Integrations**
2. **Custom repositories → Add:**
   - Repository: `https://github.com/YOUR_USERNAME/uteclocal-HA`
   - Category: Integration
3. **Install "U-tec Local Gateway"**
4. **Restart Home Assistant**
5. **Settings → Add Integration → "U-tec Local Gateway"**
6. **Enter gateway URL:** `http://192.168.1.40:8000`

---

## 🔧 Debugging HACS Installation

### Check HACS Logs

```
Settings → System → Logs
Search: "hacs"
```

Look for:
```
Installing U-tec Local Gateway
Downloaded to: custom_components/uteclocal
```

---

### Verify Files After HACS Install

```bash
ls -la ~/.homeassistant/custom_components/uteclocal/
```

Should show:
```
__init__.py
config_flow.py
lock.py
sensor.py
manifest.json
strings.json
```

---

### Check Integration Loads

```
Settings → System → Logs
Search: "uteclocal"
```

After restart, should see:
```
Setup of domain uteclocal is taking longer than 10 seconds
# OR
Successfully loaded uteclocal
```

---

## 🆘 Common HACS Issues

### Issue 1: "Repository structure is not compliant"

**Problem:** Missing `hacs.json` or wrong structure

**Fix:**
1. Add `hacs.json` to repo root
2. Make sure `content_in_root: false`
3. Ensure files are in `custom_components/uteclocal/`

---

### Issue 2: Integration Not Appearing

**After HACS install:**
1. Check files were copied: `ls ~/.homeassistant/custom_components/uteclocal/`
2. Restart Home Assistant
3. Check logs for errors

---

### Issue 3: "No entities" After Adding Integration

This is your current issue! The integration installed but:
- ❌ No lock entities created
- ❌ No sensor entities created

**Causes:**
1. Gateway not reachable from HA
2. Gateway returns unexpected data format
3. Device type detection failing

**Need to debug with logs!**

---

## 📋 What You Need to Add to Repo

### 1. Create hacs.json

```bash
cd uteclocal-HA
cat > hacs.json << 'EOF'
{
  "name": "U-tec Local Gateway",
  "content_in_root": false,
  "render_readme": true,
  "domains": ["lock", "sensor"],
  "homeassistant": "2023.1.0"
}
EOF
git add hacs.json
git commit -m "Add HACS support"
git push
```

---

### 2. Update manifest.json

```bash
# Edit custom_components/uteclocal/manifest.json
# Add your GitHub username to codeowners
# Update documentation URL
```

---

### 3. Create info.md (Optional)

```bash
cat > info.md << 'EOF'
# U-tec Local Gateway

Automatic OAuth token refresh for U-tec smart locks.

## Prerequisites
- Deploy gateway first (see README)
- Gateway must be accessible from Home Assistant

## Setup
1. Install via HACS
2. Restart Home Assistant
3. Add Integration → U-tec Local Gateway
4. Enter gateway URL
EOF
git add info.md
git commit -m "Add HACS info"
git push
```

---

## 🎊 After Adding HACS Files

Users can then:

1. **Add your repository to HACS:**
   - HACS → Integrations → Custom Repositories
   - URL: `https://github.com/YOUR_USERNAME/uteclocal-HA`
   - Category: Integration

2. **Install via HACS:**
   - Search "U-tec Local Gateway"
   - Click Install
   - Restart HA

3. **Add Integration:**
   - Settings → Devices & Services → Add Integration
   - Search "U-tec Local Gateway"
   - Enter: `http://192.168.1.40:8000`

---

## 🔍 Debug Your Current "No Entities" Issue

Since you installed via HACS and integration shows but no entities:

### 1. Check Integration Files Exist

```bash
ls -la ~/.homeassistant/custom_components/uteclocal/
```

### 2. Check Gateway is Reachable

From Home Assistant machine:
```bash
curl http://192.168.1.40:8000/api/devices
```

### 3. Enable Debug Logging

Add to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.uteclocal: debug
```

Restart and check logs.

---

## 📦 Files to Download

I'll create the HACS configuration files for you:
1. `hacs.json`
2. `info.md`
3. Updated `manifest.json`

Then you can add them to your repository and users can install via HACS properly!

---

**The key issue is: Integration installed via HACS but not creating entities. We need to see the debug logs to understand why!** 🔍
