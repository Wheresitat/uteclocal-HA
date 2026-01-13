# ⚡ SUPER SIMPLE: uteclocal-HA Installation

## Repository: https://github.com/Wheresitat/uteclocal-HA

---

## 🎯 The Absolute Simplest Way

### On Your Linux Box:

```bash
# 1. Clone the repository
git clone https://github.com/Wheresitat/uteclocal-HA.git
cd uteclocal-HA

# 2. Download this one-line script that does everything
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/uteclocal-HA/main/deploy_docker.sh

# Wait - you need the enhanced files first!
# See below for how to get them there...
```

**Actually, here's the REAL simplest way:**

---

## 📋 Two Super Simple Methods

### Method 1: Fork First (Recommended)

**Step 1:** Go to https://github.com/Wheresitat/uteclocal-HA  
**Step 2:** Click "Fork" (top right)  
**Step 3:** Upload the 13 enhanced files to your fork via GitHub web UI  
**Step 4:** On your Linux box:

```bash
git clone https://github.com/YOUR_USERNAME/uteclocal-HA.git
cd uteclocal-HA
chmod +x deploy_docker.sh
./deploy_docker.sh
```

**Done!** ✅

---

### Method 2: Clone Then Patch (Even Simpler!)

**On Your Linux Box:**

```bash
# Clone the original
git clone https://github.com/Wheresitat/uteclocal-HA.git
cd uteclocal-HA

# Create the enhanced gateway file
cat > gateway/main.py << 'EOF'
# Paste the entire content of gateway_main_enhanced.py here
# (or copy it via scp from your computer)
EOF

# Update requirements
echo "APScheduler==3.10.4" >> requirements.txt

# Create the Dockerfile
cat > Dockerfile << 'EOF'
# Paste Dockerfile content here
EOF

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
# Paste docker-compose.yml content here
EOF

# Create deploy script
cat > deploy_docker.sh << 'EOF'
# Paste deploy_docker.sh content here
EOF

# Make executable and run
chmod +x deploy_docker.sh
./deploy_docker.sh
```

**Done!** ✅

---

## 🚀 EASIEST METHOD: Upload to Your Fork

This is what I recommend:

### Step-by-Step:

1. **Fork the repo on GitHub:**
   - Go to: https://github.com/Wheresitat/uteclocal-HA
   - Click "Fork"
   - You now have: `https://github.com/YOUR_USERNAME/uteclocal-HA`

2. **Upload enhanced files via GitHub:**
   - Go to your fork
   - Click "gateway" folder → "main.py" → Edit button
   - Replace content with `gateway_main_enhanced.py` content
   - Commit
   - Go back to root, click "Add file" → "Upload files"
   - Upload: `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `deploy_docker.sh`, `test_gateway.sh`
   - Commit
   - Edit `requirements.txt`, add `APScheduler==3.10.4`
   - Commit

3. **On your Linux box:**

```bash
git clone https://github.com/YOUR_USERNAME/uteclocal-HA.git
cd uteclocal-HA
./deploy_docker.sh
```

**That's it!** 3 commands! ✅

---

## 📦 What Gets Installed

After running `./deploy_docker.sh`:

```
✅ Enhanced gateway with auto-refresh
✅ Docker container running on port 8000
✅ Background scheduler checking tokens every 5 min
✅ Web UI at http://localhost:8000
✅ Persistent storage for tokens
✅ Automatic recovery from auth failures
✅ Home Assistant integration works unchanged
```

---

## 🔧 Quick Commands

### After Installation:

```bash
# Check if running
docker compose -p uteclocal ps

# View logs
docker compose -p uteclocal logs -f gateway

# Check health
curl http://localhost:8000/health

# Open web UI
# Go to: http://YOUR_SERVER_IP:8000

# Restart if needed
docker compose -p uteclocal restart gateway

# Stop
docker compose -p uteclocal down

# Start again
docker compose -p uteclocal up -d
```

---

## 🎯 Quick Decision Guide

**Do you have the files on your computer?**

├─ **YES** → Copy to Linux server via SCP, then run deploy script
│
└─ **NO** → Upload to GitHub fork first, then clone on Linux

**Which method?**

├─ **Want it on GitHub** → Fork, upload files, clone, deploy
│
└─ **Just want it working** → Clone original, copy files, deploy

**All methods end with:**
```bash
./deploy_docker.sh
```

---

## 📋 File Transfer Options

### Option A: SCP from Computer to Linux

```bash
# From your computer
scp ~/Downloads/gateway_main_enhanced.py user@server:~/uteclocal-HA/gateway/main.py
scp ~/Downloads/Dockerfile user@server:~/uteclocal-HA/
scp ~/Downloads/docker-compose.yml user@server:~/uteclocal-HA/
scp ~/Downloads/.dockerignore user@server:~/uteclocal-HA/
scp ~/Downloads/deploy_docker.sh user@server:~/uteclocal-HA/
scp ~/Downloads/test_gateway.sh user@server:~/uteclocal-HA/

# Then on server
cd uteclocal-HA
echo "APScheduler==3.10.4" >> requirements.txt
./deploy_docker.sh
```

### Option B: Via GitHub (Cleanest)

```bash
# 1. Fork and upload to GitHub
# 2. On Linux:
git clone https://github.com/YOUR_USERNAME/uteclocal-HA.git
cd uteclocal-HA
./deploy_docker.sh
```

### Option C: Copy-Paste Content

```bash
# On Linux server
cd uteclocal-HA

# Edit gateway/main.py
nano gateway/main.py
# Paste content from gateway_main_enhanced.py
# Save (Ctrl+X, Y, Enter)

# Same for other files
nano Dockerfile
nano docker-compose.yml
nano deploy_docker.sh
chmod +x deploy_docker.sh
echo "APScheduler==3.10.4" >> requirements.txt

# Run
./deploy_docker.sh
```

---

## ✅ Success Indicators

After installation, you should see:

```bash
$ docker compose -p uteclocal ps
NAME                  STATUS          PORTS
uteclocal-gateway     Up (healthy)    0.0.0.0:8000->8000/tcp

$ curl http://localhost:8000/health
{
  "status": "ok",
  "token_valid": true,
  "auto_refresh_enabled": true
}
```

---

## 🎊 Summary for uteclocal-HA

**Repository:** https://github.com/Wheresitat/uteclocal-HA

**Simplest Installation:**
1. Fork repo on GitHub
2. Upload 13 enhanced files to your fork
3. Clone to Linux: `git clone https://github.com/YOUR_USERNAME/uteclocal-HA.git`
4. Run: `./deploy_docker.sh`

**Alternative (No Fork):**
1. Clone original: `git clone https://github.com/Wheresitat/uteclocal-HA.git`
2. Copy enhanced files to directory (via scp or paste)
3. Run: `./deploy_docker.sh`

**Both methods work!** Choose based on whether you want your version on GitHub or not.

**Time:** 5-10 minutes total
**Result:** Gateway that never loses authentication! 🎉

---

## 🔗 Quick Links

- **Original Repo:** https://github.com/Wheresitat/uteclocal-HA
- **Your Fork:** https://github.com/YOUR_USERNAME/uteclocal-HA (after forking)
- **Gateway Web UI:** http://localhost:8000 (after installation)
- **Documentation:** See the `.md` files in `docs/` folder

---

## ⚡ Ultra-Quick Reference

```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR_USERNAME/uteclocal-HA.git
cd uteclocal-HA
./deploy_docker.sh

# Or without fork:
git clone https://github.com/Wheresitat/uteclocal-HA.git
cd uteclocal-HA
# Copy files here
./deploy_docker.sh
```

**That's all you need to know!** 🚀
