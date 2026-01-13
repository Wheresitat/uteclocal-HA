# 🎯 Installation for uteclocal-HA Repository

## Repository: https://github.com/Wheresitat/uteclocal-HA

Perfect! Here's how to add the auto-refresh enhancement to this specific repository.

---

## 🔄 Two Approaches

### Approach 1: Fork and Enhance (Recommended)
Create your own fork with the enhancements

### Approach 2: Clone Original + Apply Enhancements
Clone the original and apply enhancements locally

---

## 🌟 Method 1: Fork & Enhance (Best for Contributing Back)

### Step 1: Fork the Repository

1. **Go to:** https://github.com/Wheresitat/uteclocal-HA
2. **Click "Fork"** (top right corner)
3. **Create fork** → You now have: `https://github.com/YOUR_USERNAME/uteclocal-HA`

### Step 2: Add Enhanced Files to Your Fork

**Option A: Via GitHub Web Interface** (Easiest)

1. Go to your fork: `https://github.com/YOUR_USERNAME/uteclocal-HA`
2. Navigate to the files you want to replace:
   - Click on `gateway/main.py` → Click pencil icon (Edit)
   - Copy content from `gateway_main_enhanced.py`
   - Paste and commit
3. Upload new files:
   - Click "Add file" → "Upload files"
   - Upload: `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `*.sh`, `*.md`
   - Commit changes
4. Edit `requirements.txt`:
   - Click on `requirements.txt` → Click pencil icon
   - Add line: `APScheduler==3.10.4`
   - Commit changes

**Option B: Via Git on Your Computer**

```bash
# 1. Clone your fork
git clone https://github.com/YOUR_USERNAME/uteclocal-HA.git
cd uteclocal-HA

# 2. Copy enhanced files
# (Assuming you have them in ~/Downloads)
cp ~/Downloads/gateway_main_enhanced.py gateway/main.py
cp ~/Downloads/Dockerfile ./
cp ~/Downloads/docker-compose.yml ./
cp ~/Downloads/.dockerignore ./
cp ~/Downloads/deploy_docker.sh ./
cp ~/Downloads/test_gateway.sh ./

# 3. Create docs folder and move documentation
mkdir -p docs
cp ~/Downloads/QUICK_START.md docs/
cp ~/Downloads/DOCKER_DEPLOYMENT_GUIDE.md docs/
cp ~/Downloads/IMPLEMENTATION_GUIDE.md docs/
cp ~/Downloads/DOCKER_ARCHITECTURE.md docs/
cp ~/Downloads/VISUAL_GUIDE.md docs/
cp ~/Downloads/FILE_INDEX.md docs/
cp ~/Downloads/GITHUB_*.md docs/

# 4. Update requirements.txt
echo "APScheduler==3.10.4" >> requirements.txt

# 5. Add .gitignore
cp ~/Downloads/gitignore_for_repo.txt .gitignore

# 6. Commit and push
git add .
git commit -m "Add automatic token refresh enhancement

- Enhanced gateway with auto-refresh every 5 minutes
- Background scheduler for token monitoring
- Smart retry logic on API failures
- Updated Docker configuration with volumes
- Added comprehensive documentation
- Added deployment and testing scripts"

git push origin main
```

### Step 3: Install on Your Linux Box

```bash
# Clone YOUR fork (not the original)
git clone https://github.com/YOUR_USERNAME/uteclocal-HA.git
cd uteclocal-HA

# Run the installer
chmod +x deploy_docker.sh
./deploy_docker.sh

# Test
curl http://localhost:8000/health
```

**Done!** ✅

---

## 🚀 Method 2: Clone Original + Apply Patches (Quick & Simple)

If you don't want to fork, just enhance your local copy:

### Step 1: Clone Original Repository

```bash
# On your Linux box
git clone https://github.com/Wheresitat/uteclocal-HA.git
cd uteclocal-HA
```

### Step 2: Download Enhanced Files Directly

You have two options:

**Option A: Copy from your computer to server**

```bash
# On your computer, in the directory with downloaded files:
scp ~/Downloads/gateway_main_enhanced.py user@your-server:~/uteclocal-HA/gateway/main.py
scp ~/Downloads/Dockerfile user@your-server:~/uteclocal-HA/
scp ~/Downloads/docker-compose.yml user@your-server:~/uteclocal-HA/
scp ~/Downloads/.dockerignore user@your-server:~/uteclocal-HA/
scp ~/Downloads/deploy_docker.sh user@your-server:~/uteclocal-HA/
scp ~/Downloads/test_gateway.sh user@your-server:~/uteclocal-HA/
scp ~/Downloads/*.md user@your-server:~/uteclocal-HA/docs/
```

**Option B: Create files directly on server**

```bash
# On your Linux server
cd uteclocal-HA

# You can copy-paste the content of each file
# Or download them using curl/wget if you uploaded them somewhere
```

### Step 3: Update Files

```bash
# On your Linux server
cd uteclocal-HA

# Replace gateway code
cp gateway_main_enhanced.py gateway/main.py

# Update requirements
echo "APScheduler==3.10.4" >> requirements.txt

# Make scripts executable
chmod +x deploy_docker.sh test_gateway.sh

# Run installer
./deploy_docker.sh
```

**Done!** ✅

---

## 📋 Complete Command Reference for uteclocal-HA

### Fork Method (Recommended):

```bash
# === ON YOUR COMPUTER (optional, can do via GitHub web) ===
git clone https://github.com/YOUR_USERNAME/uteclocal-HA.git
cd uteclocal-HA
cp ~/Downloads/gateway_main_enhanced.py gateway/main.py
cp ~/Downloads/{Dockerfile,docker-compose.yml,.dockerignore,*.sh} ./
mkdir -p docs
cp ~/Downloads/*.md docs/
echo "APScheduler==3.10.4" >> requirements.txt
git add .
git commit -m "Add auto-refresh enhancement"
git push origin main

# === ON YOUR LINUX BOX ===
git clone https://github.com/YOUR_USERNAME/uteclocal-HA.git
cd uteclocal-HA
chmod +x deploy_docker.sh
./deploy_docker.sh
```

### Direct Method (Simplest):

```bash
# === ON YOUR LINUX BOX ===
git clone https://github.com/Wheresitat/uteclocal-HA.git
cd uteclocal-HA

# Copy enhanced files here (via scp, or paste content)
# Then:
cp gateway_main_enhanced.py gateway/main.py
echo "APScheduler==3.10.4" >> requirements.txt
chmod +x deploy_docker.sh
./deploy_docker.sh
```

---

## 🎨 What Your Fork Will Look Like

After adding the enhancements, your fork will have:

```
uteclocal-HA/
├── .github/                    # Original CI/CD
├── .gitignore                  # ← NEW (protects secrets)
├── README.md                   # Original (or update it)
├── gateway/
│   ├── __init__.py            # Original
│   └── main.py                # ← ENHANCED (auto-refresh)
├── custom_components/
│   └── uteclocal/             # Original HA integration
├── scripts/                   # Original scripts
├── Dockerfile                 # ← ENHANCED (with healthcheck)
├── docker-compose.yml         # ← ENHANCED (with volumes)
├── .dockerignore              # ← NEW
├── requirements.txt           # ← UPDATED (added APScheduler)
├── const.py                   # Original
├── hacs.json                  # Original
├── deploy_docker.sh           # ← NEW (auto-installer)
├── test_gateway.sh            # ← NEW (testing)
└── docs/                      # ← NEW FOLDER
    ├── QUICK_START.md
    ├── DOCKER_DEPLOYMENT_GUIDE.md
    ├── IMPLEMENTATION_GUIDE.md
    ├── DOCKER_ARCHITECTURE.md
    ├── VISUAL_GUIDE.md
    ├── FILE_INDEX.md
    └── GITHUB_*.md
```

---

## 📝 Updating Your Fork's README

Consider adding this to the README.md:

```markdown
## 🌟 Enhanced Version

This fork includes **automatic OAuth token refresh** to prevent authentication expiration.

### New Features:
- ✅ Automatic token refresh (no more manual re-auth)
- ✅ Background scheduler checks token every 5 minutes  
- ✅ Smart retry logic on API failures
- ✅ Enhanced Docker configuration with persistent volumes
- ✅ Web UI with token status monitoring

### Quick Install:
```bash
git clone https://github.com/YOUR_USERNAME/uteclocal-HA.git
cd uteclocal-HA
./deploy_docker.sh
```

See [documentation](docs/) for details.
```

---

## 🔄 Keeping Your Fork Updated

If the original repository gets updates:

```bash
# Add original repo as upstream
cd uteclocal-HA
git remote add upstream https://github.com/Wheresitat/uteclocal-HA.git

# Fetch and merge updates
git fetch upstream
git merge upstream/main

# Push to your fork
git push origin main

# Rebuild on Linux server
cd uteclocal-HA
git pull
docker compose -p uteclocal up -d --build
```

---

## 🎯 Integration with Home Assistant

The HACS configuration remains the same, but now pointing to your fork:

### If Using HACS:

1. **Settings → HACS → Integrations**
2. **Click menu → Custom repositories**
3. **Add:**
   - URL: `https://github.com/YOUR_USERNAME/uteclocal-HA`
   - Category: Integration
4. **Install** from HACS
5. **Restart** Home Assistant
6. **Add Integration** → "U-tec Local Gateway"
7. **Configure:**
   - Host: `http://localhost:8000` (or your gateway IP)
   - Leave API key blank (handled by gateway)

---

## 🚀 Quick Start Commands

### For Your Specific Repository:

**On Computer (to fork and enhance):**
```bash
# Fork on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/uteclocal-HA.git
cd uteclocal-HA
# Add enhanced files
git push
```

**On Linux Server:**
```bash
# Using your fork:
git clone https://github.com/YOUR_USERNAME/uteclocal-HA.git
cd uteclocal-HA
./deploy_docker.sh

# Or using original + patches:
git clone https://github.com/Wheresitat/uteclocal-HA.git
cd uteclocal-HA
# Copy enhanced files
./deploy_docker.sh
```

---

## 📊 File Mapping for uteclocal-HA

Here's what replaces what:

| Downloaded File | Goes To | Action |
|----------------|---------|--------|
| `gateway_main_enhanced.py` | `gateway/main.py` | **Replace** |
| `requirements_enhanced.txt` | `requirements.txt` | **Merge** (add APScheduler) |
| `Dockerfile` | `Dockerfile` | **Replace** |
| `docker-compose.yml` | `docker-compose.yml` | **Replace** |
| `.dockerignore` | `.dockerignore` | **Create new** |
| `deploy_docker.sh` | `deploy_docker.sh` | **Create new** |
| `test_gateway.sh` | `test_gateway.sh` | **Create new** |
| `*.md` files | `docs/*.md` | **Create new** |
| `gitignore_for_repo.txt` | `.gitignore` | **Create new** |

---

## ✅ Verification Checklist

After installation on Linux:

- [ ] Repository cloned: `ls -la uteclocal-HA/`
- [ ] Enhanced gateway in place: `head -20 uteclocal-HA/gateway/main.py`
- [ ] APScheduler in requirements: `grep APScheduler uteclocal-HA/requirements.txt`
- [ ] Scripts executable: `ls -l uteclocal-HA/*.sh`
- [ ] Docker running: `docker compose -p uteclocal ps`
- [ ] Health check passes: `curl http://localhost:8000/health`
- [ ] Token status shows auto-refresh: `curl http://localhost:8000/api/config | jq .auto_refresh_enabled`
- [ ] Web UI accessible: Open `http://localhost:8000` in browser
- [ ] Home Assistant connects: Check HA integration

---

## 🎊 Summary

**For the uteclocal-HA repository, you have 2 options:**

### Option 1: Fork It (Best for contributing back)
1. Fork `Wheresitat/uteclocal-HA` to your GitHub
2. Add enhanced files to your fork
3. Clone your fork to Linux
4. Run `./deploy_docker.sh`

### Option 2: Clone & Patch (Simplest)
1. Clone `Wheresitat/uteclocal-HA` to Linux
2. Copy enhanced files to the directory
3. Run `./deploy_docker.sh`

**Both work perfectly!** Choose based on whether you want to maintain your own fork or just use it locally.

---

## 🎯 Recommended Approach

**I recommend Option 1 (Fork)** because:
- ✅ You can easily update later with `git pull`
- ✅ Your enhancements are backed up on GitHub
- ✅ You can contribute back to the original project
- ✅ Others can use your enhanced version
- ✅ Clean version control

**Commands for Option 1:**
```bash
# 1. Fork on GitHub
# 2. Then on your Linux box:
git clone https://github.com/YOUR_USERNAME/uteclocal-HA.git
cd uteclocal-HA
# Copy enhanced files here
./deploy_docker.sh
```

**Done!** 🚀
