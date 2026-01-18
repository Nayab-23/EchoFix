# EchoFix - Bring Up & Bring Down Commands

## 🛑 BRING EVERYTHING DOWN

### Option 1: Graceful Stop (Keeps Data)
```bash
./stop.sh
```
**What this does:**
- Stops all running containers
- Preserves n8n workflows and data
- Keeps Docker images
- You can start again without losing anything

### Option 2: Complete Teardown (Deletes Everything)
```bash
./teardown.sh
```
**⚠️ WARNING: This deletes:**
- All containers
- All volumes (n8n data will be lost!)
- All Docker images
- Everything must be rebuilt with `./deploy.sh`

---

## 🚀 BRING EVERYTHING BACK UP

### After `./stop.sh` (Quick Restart)
```bash
./deploy.sh
```
**What this does:**
- Starts stopped containers
- Uses existing images and data
- Fast startup (no rebuild needed)

### After `./teardown.sh` (Fresh Start)
```bash
./deploy.sh
```
**What this does:**
- Rebuilds all Docker images
- Creates new containers
- Initializes fresh volumes
- Slower but completely clean

### Quick Restart (Alternative)
```bash
./restart.sh
```
**What this does:**
- Stops and immediately restarts
- Same as `./stop.sh` + `./deploy.sh`
- Useful after changing `backend/.env`

---

## 📋 TYPICAL WORKFLOWS

### Daily Development (Preserving Work)

**End of day:**
```bash
./stop.sh
```

**Next morning:**
```bash
./deploy.sh
```

Your n8n workflows and all data are preserved!

---

### After Code Changes

**Stop, rebuild, and restart:**
```bash
./rebuild.sh
```

This is equivalent to:
```bash
./stop.sh
docker-compose build --no-cache
./deploy.sh
```

---

### Complete Fresh Start (Nuclear Option)

**Remove everything and start clean:**
```bash
./teardown.sh
./deploy.sh
```

---

### After Configuration Changes

**Restart with new config:**
```bash
nano backend/.env  # Edit configuration
./restart.sh        # Apply changes
```

---

## 🎯 ONE-LINE COMMANDS

### Quick Reference

```bash
# Stop (keeps data)
./stop.sh

# Start
./deploy.sh

# Restart
./restart.sh

# Complete removal
./teardown.sh

# Fresh deploy after teardown
./teardown.sh && ./deploy.sh
```

---

## 📊 CHECK STATUS

Before bringing up or down, check current status:

```bash
./status.sh
```

This shows:
- Which containers are running
- Health status
- Resource usage

---

## 🐳 DIRECT DOCKER COMMANDS (Alternative)

If you prefer Docker Compose directly:

### Bring Down
```bash
# Stop (keeps data)
docker-compose stop

# Remove containers (keeps volumes)
docker-compose down

# Remove everything including volumes
docker-compose down -v
```

### Bring Up
```bash
# Start (in background)
docker-compose up -d

# Start (see logs)
docker-compose up
```

---

## ⚡ QUICK COMMANDS SUMMARY

| Goal | Command | Data Preserved? |
|------|---------|-----------------|
| Stop services | `./stop.sh` | ✅ Yes |
| Start services | `./deploy.sh` | ✅ Yes |
| Restart services | `./restart.sh` | ✅ Yes |
| Rebuild & restart | `./rebuild.sh` | ✅ Yes |
| Complete removal | `./teardown.sh` | ❌ No |
| Fresh start | `./teardown.sh && ./deploy.sh` | ❌ No |

---

## 💡 PRO TIPS

1. **Use `./stop.sh` for daily work** - It's fast and preserves everything
2. **Use `./teardown.sh` only when you need a clean slate**
3. **Always check `./status.sh` first** - Know what's running
4. **Backup important n8n workflows** - Before using `./teardown.sh`
5. **Use `./restart.sh`** - After changing `backend/.env`

---

## 🚨 EMERGENCY COMMANDS

### Force Kill Everything
```bash
docker-compose kill
docker-compose down -v
```

### If Containers Won't Stop
```bash
docker kill echofix-backend echofix-n8n
docker rm -f echofix-backend echofix-n8n
```

### If Ports Are Stuck
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 5678
lsof -ti:5678 | xargs kill -9
```

---

## ✅ VERIFICATION

After bringing up, verify everything is running:

```bash
# Check status
./status.sh

# Test backend
curl http://localhost:8000/health

# Test n8n
curl -I http://localhost:5678

# View logs
./logs.sh
```

---

**Remember:**
- `./stop.sh` → Graceful stop, keeps data
- `./teardown.sh` → Nuclear option, deletes everything
- `./deploy.sh` → Bring everything back up
- `./status.sh` → Check what's running

**That's it!** 🎉
