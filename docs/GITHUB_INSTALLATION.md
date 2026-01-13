# 🔄 GitHub Installation Method

## Yes! You Can Clone and Run From GitHub

This is actually the **cleanest** way to install the enhanced gateway.

---

## 📋 Two Approaches

### Approach 1: Add to Your Existing uteclocal Fork (Recommended)
Create your own fork of the uteclocal repository and add these files to it.

### Approach 2: Separate Repository
Create a new repository just for the enhanced files and merge them into uteclocal.

---

## 🎯 Method 1: Fork & Enhance (Recommended)

### Step 1: Create Your Own Fork

1. **Go to the original repo:** https://github.com/Wheresitat/uteclocal
2. **Click "Fork"** (top right)
3. **Name it:** `uteclocal-enhanced` (or keep original name)
4. **Create fork**

### Step 2: Add Enhanced Files to Your Fork

**Option A: Via GitHub Web Interface**
1. Go to your fork on GitHub
2. Click "Add file" → "Upload files"
3. Upload all 13 files (drag & drop)
4. Commit with message: "Add automatic token refresh enhancement"

**Option B: Via Git Locally**
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/uteclocal-enhanced.git
cd uteclocal-enhanced

# Copy the enhanced files here
cp ~/Downloads/gateway_main_enhanced.py ./
cp ~/Downloads/requirements_enhanced.txt ./
cp ~/Downloads/Dockerfile ./
cp ~/Downloads/docker-compose.yml ./
cp ~/Downloads/.dockerignore ./
cp ~/Downloads/*.sh ./
cp ~/Downloads/*.md ./

# Replace gateway/main.py with enhanced version
cp gateway_main_enhanced.py gateway/main.py

# Merge requirements
cat requirements_enhanced.txt >> requirements.txt
sort -u requirements.txt -o requirements.txt

# Commit and push
git add .
git commit -m "Add automatic token refresh enhancement"
git push origin main
```

### Step 3: Clone to Your Linux Box

```bash
# On your Linux server
cd ~  # or wherever you want it
git clone https://github.com/YOUR_USERNAME/uteclocal-enhanced.git
cd uteclocal-enhanced

# Run the installer
chmod +x deploy_docker.sh
./deploy_docker.sh
```

**Done!** ✅

---

## 🎯 Method 2: Separate Repo (Alternative)

### Step 1: Create New Repository

1. **Go to GitHub:** https://github.com/new
2. **Name:** `uteclocal-auto-refresh` (or any name)
3. **Description:** "Enhanced U-tec gateway with automatic token refresh"
4. **Public or Private:** Your choice
5. **Add README:** Yes
6. **Create repository**

### Step 2: Upload Files

```bash
# On your local machine
mkdir uteclocal-auto-refresh
cd uteclocal-auto-refresh

# Initialize git
git init
git branch -M main

# Copy all enhanced files
cp ~/Downloads/* ./

# Create a simple README
cat > README.md << 'EOF'
# U-tec Gateway Auto-Refresh Enhancement

Enhanced version of the U-tec Local Gateway with automatic OAuth token refresh.

## Installation

```bash
# Clone the original uteclocal
git clone https://github.com/Wheresitat/uteclocal.git
cd uteclocal

# Clone this enhancement repo
cd ..
git clone https://github.com/YOUR_USERNAME/uteclocal-auto-refresh.git

# Copy enhanced files to uteclocal
cp uteclocal-auto-refresh/gateway_main_enhanced.py uteclocal/gateway/main.py
cp uteclocal-auto-refresh/requirements_enhanced.txt uteclocal/requirements.txt
cp uteclocal-auto-refresh/Dockerfile uteclocal/
cp uteclocal-auto-refresh/docker-compose.yml uteclocal/
cp uteclocal-auto-refresh/.dockerignore uteclocal/
cp uteclocal-auto-refresh/*.sh uteclocal/

# Run installer
cd uteclocal
chmod +x deploy_docker.sh
./deploy_docker.sh
```

See documentation files for details.
EOF

# Commit and push
git add .
git commit -m "Initial commit: Auto-refresh enhancement for U-tec gateway"
git remote add origin https://github.com/YOUR_USERNAME/uteclocal-auto-refresh.git
git push -u origin main
```

### Step 3: Install on Linux Box

```bash
# On your Linux server
# Clone original uteclocal
git clone https://github.com/Wheresitat/uteclocal.git
cd uteclocal

# Clone your enhancement repo alongside
cd ..
git clone https://github.com/YOUR_USERNAME/uteclocal-auto-refresh.git

# Copy enhanced files over
cp uteclocal-auto-refresh/gateway_main_enhanced.py uteclocal/gateway/main.py
cp uteclocal-auto-refresh/requirements_enhanced.txt uteclocal/requirements.txt
cp uteclocal-auto-refresh/Dockerfile uteclocal/
cp uteclocal-auto-refresh/docker-compose.yml uteclocal/
cp uteclocal-auto-refresh/.dockerignore uteclocal/
cp uteclocal-auto-refresh/*.sh uteclocal/

# Run installer
cd uteclocal
chmod +x deploy_docker.sh
./deploy_docker.sh
```

---

## 🚀 Quick GitHub to Linux Installation

### If You Just Want Commands:

```bash
# === ON YOUR LINUX BOX ===

# Option A: If you forked and added files to your fork
git clone https://github.com/YOUR_USERNAME/uteclocal-enhanced.git
cd uteclocal-enhanced
chmod +x deploy_docker.sh
./deploy_docker.sh

# Option B: If you have separate repos
git clone https://github.com/Wheresitat/uteclocal.git
git clone https://github.com/YOUR_USERNAME/uteclocal-auto-refresh.git
cp uteclocal-auto-refresh/* uteclocal/
cd uteclocal
chmod +x deploy_docker.sh
./deploy_docker.sh

# Test it works
curl http://localhost:8000/health
```

---

## 📁 Recommended GitHub Repository Structure

If you're creating your own fork/repo, organize it like this:

```
your-repo/
├── README.md                        # Your custom README
├── gateway/
│   ├── __init__.py                 # Original
│   └── main.py                     # ← Enhanced version
├── custom_components/               # Original HA integration
│   └── uteclocal/
├── requirements.txt                 # ← With APScheduler added
├── Dockerfile                       # ← Enhanced version
├── docker-compose.yml              # ← With volumes
├── .dockerignore                   # ← New
├── deploy_docker.sh                # ← Installation script
├── test_gateway.sh                 # ← Testing script
├── const.py                        # Original
├── docs/                           # ← NEW FOLDER
│   ├── QUICK_START.md
│   ├── DOCKER_DEPLOYMENT_GUIDE.md
│   ├── IMPLEMENTATION_GUIDE.md
│   ├── DOCKER_ARCHITECTURE.md
│   ├── VISUAL_GUIDE.md
│   └── FILE_INDEX.md
└── scripts/                        # Original scripts
    └── ...
```

---

## 🎨 Create a Nice README for Your GitHub Repo

Here's a template:

```markdown
# U-tec Local Gateway - Enhanced with Auto-Refresh

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Home Assistant](https://img.shields.io/badge/home%20assistant-compatible-blue.svg)](https://www.home-assistant.io/)

Enhanced version of the [U-tec Local Gateway](https://github.com/Wheresitat/uteclocal) with **automatic OAuth token refresh**.

## 🌟 What's Enhanced

This fork adds automatic token refresh functionality to prevent authentication expiration:

- ✅ **Automatic token refresh** - No more manual re-authentication every few days
- ✅ **Background scheduler** - Checks token status every 5 minutes
- ✅ **Smart retry logic** - Auto-retries failed API calls with fresh tokens
- ✅ **Persistent storage** - Tokens survive container restarts
- ✅ **Web UI controls** - Monitor status and manually trigger refresh
- ✅ **100% backward compatible** - Works with existing Home Assistant integration

## 🚀 Quick Start

```bash
# Clone this repository
git clone https://github.com/YOUR_USERNAME/uteclocal-enhanced.git
cd uteclocal-enhanced

# Run the automated installer
chmod +x deploy_docker.sh
./deploy_docker.sh

# Open web UI
http://localhost:8000
```

## 📖 Documentation

- [Quick Start Guide](docs/QUICK_START.md)
- [Docker Deployment Guide](docs/DOCKER_DEPLOYMENT_GUIDE.md)
- [Implementation Details](docs/IMPLEMENTATION_GUIDE.md)
- [Architecture Overview](docs/DOCKER_ARCHITECTURE.md)

## 🔧 Requirements

- Docker & Docker Compose
- Home Assistant (optional, for lock integration)
- U-tec account with API credentials

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

## 📦 What's Different from Original

| Feature | Original | Enhanced |
|---------|----------|----------|
| Token refresh | Manual | Automatic ✅ |
| Token monitoring | None | Background scheduler ✅ |
| Retry logic | Basic | Smart with auto-refresh ✅ |
| Web UI | Basic | Enhanced with status ✅ |
| Persistence | Config only | Tokens + expiration ✅ |
| Logging | Basic | Comprehensive ✅ |

## 🏠 Home Assistant Integration

No changes needed! Your existing Home Assistant integration continues working:

```yaml
# In Home Assistant configuration
host: http://localhost:8000  # or your gateway IP
```

Locks will appear as:
- `lock.front_door` (lock/unlock control)
- `sensor.front_door_battery` (battery level)
- `sensor.front_door_status` (lock status)

## 🔄 Updates

```bash
# Pull latest changes
cd uteclocal-enhanced
git pull origin main

# Rebuild and restart
docker compose -p uteclocal up -d --build
```

Your config and tokens are preserved!

## 🆘 Troubleshooting

See the [comprehensive troubleshooting guide](docs/QUICK_START.md#troubleshooting).

**Quick checks:**
```bash
# Health check
curl http://localhost:8000/health

# View logs
docker compose -p uteclocal logs -f gateway

# Run tests
./test_gateway.sh
```

## 🙏 Credits

- Original gateway by [Wheresitat](https://github.com/Wheresitat/uteclocal)
- Enhanced with automatic token refresh
- Built for the Home Assistant community

## 📄 License

Same as original project

## ⭐ Star This Repo

If this enhancement helps you, please star the repository!
```

---

## 🎯 Benefits of GitHub Approach

### ✅ Advantages

1. **Version Control** - Track all changes
2. **Easy Updates** - Just `git pull`
3. **Sharing** - Others can benefit
4. **Backup** - Code is safe in the cloud
5. **Collaboration** - Others can contribute
6. **Documentation** - README shows up nicely
7. **Clean Install** - One command to clone and run

### 📊 Workflow

```
Your Computer                GitHub                  Linux Server
═════════════                ══════                  ════════════

Download files    →    Upload to repo         →     Clone repo
    ↓                        ↓                           ↓
Test locally           Version control             Run installer
    ↓                        ↓                           ↓
Commit changes    ←    Push updates           ←    Git pull
                            ↓
                    Share with others
```

---

## 🔐 Private vs Public Repository

### Make it Private if:
- You'll store API credentials in repo (don't do this!)
- You want to keep it personal
- You're testing before sharing

### Make it Public if:
- You want to help the community
- You want others to contribute
- You follow best practices (no secrets in code)

**Recommendation:** Public repo, but NEVER commit:
- API keys
- Secret keys  
- OAuth tokens
- config.json with credentials

These should only be in the Docker volume, never in git!

---

## 📝 .gitignore for Your Repo

Add this `.gitignore` file:

```gitignore
# Sensitive data - NEVER commit these
config.json
data/
*.key
*.pem
.env
secrets.yaml

# Python
__pycache__/
*.py[cod]
*.so
.Python
*.egg-info/
dist/
build/

# Docker
docker-compose.override.yml

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Backups
backup_*/
*.backup
```

---

## 🚀 Complete GitHub Workflow Example

### On Your Computer:

```bash
# 1. Create and setup repo
mkdir uteclocal-enhanced
cd uteclocal-enhanced

# 2. Copy all downloaded files
cp ~/Downloads/* ./

# 3. Setup git
git init
git add .
git commit -m "Enhanced U-tec gateway with auto-refresh"

# 4. Push to GitHub (create repo first on GitHub)
git remote add origin https://github.com/YOUR_USERNAME/uteclocal-enhanced.git
git push -u origin main
```

### On Your Linux Server:

```bash
# 1. Clone from GitHub
git clone https://github.com/YOUR_USERNAME/uteclocal-enhanced.git
cd uteclocal-enhanced

# 2. Run installer
chmod +x deploy_docker.sh
./deploy_docker.sh

# 3. Done!
```

### Future Updates:

**On your computer:**
```bash
# Make changes
git add .
git commit -m "Update configuration"
git push origin main
```

**On your Linux server:**
```bash
cd uteclocal-enhanced
git pull origin main
docker compose -p uteclocal up -d --build
```

---

## ✅ Summary

**Yes, you can absolutely use GitHub!**

**Simplest approach:**
1. Upload all 13 files to a GitHub repository
2. Clone it to your Linux box
3. Run `./deploy_docker.sh`
4. Done!

**Benefits:**
- Clean installation process
- Easy updates with `git pull`
- Version control for your changes
- Share with others easily
- Professional deployment workflow

**This is actually the BEST way to do it!** 🎉
