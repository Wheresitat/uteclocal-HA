# 🎯 SIMPLE VISUAL GUIDE - What To Do

## The 5-Minute Installation

```
┌─────────────────────────────────────────────────────────────┐
│                    START HERE                               │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
         ┌────────────────────────────┐
         │ Do you have the uteclocal  │
         │ directory on your computer?│
         └────────┬──────────┬────────┘
                  │          │
            YES   │          │   NO
                  │          │
                  ▼          ▼
         ┌────────────┐  ┌──────────────────────┐
         │  Continue  │  │ Clone the repository │
         │  to Step 1 │  │ git clone ...        │
         └─────┬──────┘  └──────────┬───────────┘
               │                    │
               └────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────────────┐
│                    STEP 1: LOCATE FILES                       │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  You downloaded 11 files from Claude.                        │
│  They are probably in your Downloads folder:                 │
│                                                               │
│  ~/Downloads/                                                 │
│  ├── gateway_main_enhanced.py                                │
│  ├── requirements_enhanced.txt                               │
│  ├── Dockerfile                                              │
│  ├── docker-compose.yml                                      │
│  ├── .dockerignore                                           │
│  ├── deploy_docker.sh          ← YOU'LL USE THIS ONE         │
│  ├── test_gateway.sh                                         │
│  └── *.md files (documentation)                              │
│                                                               │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────┐
│                  STEP 2: OPEN TERMINAL                        │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Open your terminal/command line:                            │
│                                                               │
│  On Mac:     Applications → Terminal                         │
│  On Linux:   Ctrl+Alt+T                                      │
│  On Windows: WSL or PowerShell                               │
│                                                               │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────┐
│           STEP 3: GO TO YOUR UTECLOCAL DIRECTORY              │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Type this command (adjust path for your system):            │
│                                                               │
│  $ cd ~/uteclocal                                             │
│                                                               │
│  OR find it first:                                            │
│  $ find ~ -name "docker-compose.yml" -path "*/uteclocal/*"   │
│                                                               │
│  You should see:                                              │
│  uteclocal/                                                   │
│  ├── gateway/                                                 │
│  ├── custom_components/                                       │
│  ├── docker-compose.yml                                       │
│  └── requirements.txt                                         │
│                                                               │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────┐
│              STEP 4: COPY FILES TO uteclocal                  │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  While in the uteclocal directory, copy all downloaded files: │
│                                                               │
│  $ cp ~/Downloads/gateway_main_enhanced.py ./                 │
│  $ cp ~/Downloads/requirements_enhanced.txt ./                │
│  $ cp ~/Downloads/Dockerfile ./                               │
│  $ cp ~/Downloads/docker-compose.yml ./                       │
│  $ cp ~/Downloads/.dockerignore ./                            │
│  $ cp ~/Downloads/deploy_docker.sh ./                         │
│  $ cp ~/Downloads/*.md ./                                     │
│  $ cp ~/Downloads/*.sh ./                                     │
│                                                               │
│  OR copy everything at once:                                  │
│  $ cp ~/Downloads/{gateway_main_enhanced.py,requirements_*,\  │
│     Dockerfile,docker-compose.yml,.dockerignore,*.sh,*.md} ./ │
│                                                               │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────┐
│          STEP 5: RUN THE AUTOMATIC INSTALLER                  │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Make the script executable and run it:                       │
│                                                               │
│  $ chmod +x deploy_docker.sh                                  │
│  $ ./deploy_docker.sh                                         │
│                                                               │
│  ⏱️  This takes about 1-2 minutes                             │
│                                                               │
│  The script will:                                             │
│  ✅ Backup your existing files                                │
│  ✅ Update gateway code                                       │
│  ✅ Stop old container                                        │
│  ✅ Build new container                                       │
│  ✅ Start enhanced gateway                                    │
│  ✅ Test that it works                                        │
│                                                               │
│  You'll see output like:                                      │
│  ================================================              │
│  U-tec Gateway - Docker Deployment                           │
│  ================================================              │
│  ✓ Docker and Docker Compose found                           │
│  ✓ Backup created                                            │
│  ✓ Gateway code updated                                      │
│  ✓ Containers stopped                                        │
│  ✓ Gateway container started                                 │
│  ✓ Gateway is healthy and ready!                             │
│  ✅ Docker Deployment Complete!                               │
│                                                               │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────┐
│                 STEP 6: TEST IT WORKS                         │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Option 1 - Quick Test:                                       │
│  $ curl http://localhost:8000/health                          │
│                                                               │
│  Should show:                                                 │
│  {                                                            │
│    "status": "ok",                                            │
│    "token_valid": true,                                       │
│    "auto_refresh_enabled": true                               │
│  }                                                            │
│                                                               │
│  Option 2 - Full Test:                                        │
│  $ ./test_gateway.sh                                          │
│                                                               │
│  Option 3 - Web UI:                                           │
│  Open browser → http://localhost:8000                         │
│                                                               │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │ Does it show "healthy"? │
              └──────┬──────────┬───────┘
                     │          │
               YES   │          │   NO
                     │          │
                     ▼          ▼
         ┌────────────────┐  ┌──────────────────────┐
         │ ✅ SUCCESS!    │  │ See troubleshooting  │
         │ You're done!   │  │ in QUICK_START.md    │
         └────────┬───────┘  └──────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  🎉 INSTALLATION COMPLETE!                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Your gateway now has automatic token refresh!             │
│                                                             │
│  What this means:                                           │
│  ✅ Tokens refresh automatically before expiring           │
│  ✅ No more manual re-authentication every few days        │
│  ✅ Home Assistant continues working seamlessly            │
│  ✅ Better logging and monitoring                          │
│                                                             │
│  Next steps:                                                │
│  1. Open web UI: http://localhost:8000                     │
│  2. If needed, complete OAuth setup (one-time)             │
│  3. Verify Home Assistant still works                      │
│  4. Relax! No more auth issues 🎊                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Super Quick Reference Card

### If you just want the commands:

```bash
# 1. Go to uteclocal directory
cd ~/uteclocal

# 2. Copy downloaded files
cp ~/Downloads/{gateway_main_enhanced.py,requirements_enhanced.txt,Dockerfile,docker-compose.yml,.dockerignore,deploy_docker.sh,*.md,test_gateway.sh} ./

# 3. Run installer
chmod +x deploy_docker.sh
./deploy_docker.sh

# 4. Test
curl http://localhost:8000/health

# ✅ Done!
```

---

## 🆘 Common Issues

### "No such file or directory"
→ You're not in the right directory. Use `pwd` to check where you are.

### "Permission denied"
→ Run `chmod +x deploy_docker.sh` first

### "docker: command not found"
→ Install Docker first: https://docs.docker.com/get-docker/

### "Port 8000 already in use"
→ Something else is using port 8000. Kill it or change the port in docker-compose.yml

### Gateway not healthy
→ Wait 30 seconds, check logs: `docker compose -p uteclocal logs gateway`

---

## 🎯 What Each File Does

| File | Purpose | Do You Need It? |
|------|---------|----------------|
| `gateway_main_enhanced.py` | Enhanced gateway code | ✅ Required |
| `requirements_enhanced.txt` | Python dependencies | ✅ Required |
| `Dockerfile` | Docker build instructions | ✅ Required |
| `docker-compose.yml` | Docker orchestration | ✅ Required |
| `.dockerignore` | Build optimization | ✅ Required |
| `deploy_docker.sh` | Automatic installer | ⭐ Recommended |
| `test_gateway.sh` | Testing script | 📋 Optional |
| `QUICK_START.md` | Installation guide | 📖 Reference |
| `DOCKER_DEPLOYMENT_GUIDE.md` | Detailed Docker guide | 📖 Reference |
| `IMPLEMENTATION_GUIDE.md` | Technical details | 📖 Reference |
| `DOCKER_ARCHITECTURE.md` | Architecture diagrams | 📖 Reference |
| `README_ENHANCED.md` | Overview | 📖 Reference |

---

## ⏱️ Time Estimate

- **Copying files:** 30 seconds
- **Running installer:** 1-2 minutes (Docker build)
- **Testing:** 30 seconds
- **Total:** About 3-4 minutes

---

## ❓ Still Confused?

**Just do these 3 things:**

1. Put all downloaded files in your `uteclocal` folder
2. Run `./deploy_docker.sh`
3. Open `http://localhost:8000` in your browser

That's it! The script does everything else for you.

---

## 📞 Need Help?

1. **Read QUICK_START.md** - Step-by-step instructions
2. **Check logs:** `docker compose -p uteclocal logs gateway`
3. **Run test:** `./test_gateway.sh`
4. **Read troubleshooting** in DOCKER_DEPLOYMENT_GUIDE.md

---

**You've got this! 💪**
