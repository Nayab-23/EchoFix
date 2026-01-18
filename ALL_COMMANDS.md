# EchoFix Complete Command Reference

## 🚀 Deployment Commands (Use These!)

### Deploy Everything (First Time or After Teardown)
```bash
./deploy.sh
```

### Stop All Services (Preserves Data)
```bash
./stop.sh
```

### Restart Services (After Config Changes)
```bash
./restart.sh
```

### Check System Status
```bash
./status.sh
```

### View Logs
```bash
./logs.sh           # All services
./logs.sh backend   # Backend only
./logs.sh n8n       # n8n only
```

### Rebuild After Code Changes
```bash
./rebuild.sh
```

### Complete Teardown (⚠️ Deletes Everything)
```bash
./teardown.sh
```

---

## 📋 One-Line Commands Cheat Sheet

```bash
# Quick deploy
./deploy.sh

# Check if everything is running
./status.sh

# View backend logs
./logs.sh backend

# Restart after .env changes
./restart.sh

# Fresh start
./teardown.sh && ./deploy.sh
```

---

## 🐳 Direct Docker Commands (Alternative)

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose stop

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Rebuild
docker-compose build --no-cache
docker-compose up -d

# Remove everything
docker-compose down -v
```

---

## 🔧 Useful Docker Commands

```bash
# Access backend container shell
docker exec -it echofix-backend /bin/bash

# Access n8n container shell
docker exec -it echofix-n8n /bin/sh

# View backend logs only
docker logs -f echofix-backend

# Restart single service
docker-compose restart backend

# Kill everything forcefully
docker-compose kill && docker-compose down -v
```

---

## 📊 Debugging Commands

```bash
# Check backend health
curl http://localhost:8000/health | python3 -m json.tool

# Test n8n
curl -I http://localhost:5678

# Check which containers are running
docker ps

# Check container health status
docker ps --filter "name=echofix" --format "table {{.Names}}\t{{.Status}}"

# View resource usage
docker stats --no-stream

# Check if ports are in use
lsof -i :8000  # Backend
lsof -i :5678  # n8n

# Kill process on port
lsof -ti:8000 | xargs kill -9
```

---

## ⚙️ Configuration Commands

```bash
# Create .env from example
cp backend/.env.example backend/.env

# Edit configuration
nano backend/.env

# View current config (without secrets)
grep -v -E '(SECRET|KEY|PASSWORD)' backend/.env

# Validate .env exists
test -f backend/.env && echo "✅ .env exists" || echo "❌ .env missing"
```

---

## 🧪 Testing Commands

```bash
# Health check
curl http://localhost:8000/health

# Test Reddit ingestion (demo mode)
curl -X POST http://localhost:8000/api/reddit/ingest-seed

# Get insights
curl http://localhost:8000/api/insights | python3 -m json.tool

# Check repo configs
curl http://localhost:8000/api/repo-configs | python3 -m json.tool
```

---

## 📦 Complete Workflow Examples

### First Time Setup
```bash
# 1. Configure
cp backend/.env.example backend/.env
nano backend/.env  # Add API keys or set DEMO_MODE=true

# 2. Deploy
./deploy.sh

# 3. Verify
./status.sh
curl http://localhost:8000/health
```

### After Making Code Changes
```bash
# 1. Edit code
nano backend/app.py

# 2. Rebuild
./rebuild.sh

# 3. Check logs
./logs.sh backend
```

### Clean Restart
```bash
# 1. Teardown
./teardown.sh

# 2. Redeploy
./deploy.sh
```

### Quick Stop and Start
```bash
./stop.sh
# Do something else...
./deploy.sh  # Or: docker-compose up -d
```

---

## 🎯 Demo Mode Setup

```bash
# Edit .env
nano backend/.env

# Set this:
DEMO_MODE=true

# Deploy
./deploy.sh

# No API keys needed!
```

---

## 🔍 Monitoring & Logs

```bash
# Follow all logs
./logs.sh

# Follow backend logs
docker-compose logs -f backend

# Follow n8n logs
docker-compose logs -f n8n

# View last 100 lines
docker-compose logs --tail=100

# Search logs for errors
docker-compose logs | grep -i error

# View logs with timestamps
docker-compose logs -t -f
```

---

## 🚨 Emergency Commands

### Everything is Broken - Nuclear Option
```bash
# Kill everything
docker-compose kill

# Remove all containers and volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Or use the script
./teardown.sh

# Start fresh
./deploy.sh
```

### Port Conflicts
```bash
# Find what's using port 8000
lsof -i :8000

# Kill it
lsof -ti:8000 | xargs kill -9

# Find what's using port 5678
lsof -i :5678

# Kill it
lsof -ti:5678 | xargs kill -9
```

### Container Won't Stop
```bash
# Force kill
docker kill echofix-backend echofix-n8n

# Remove forcefully
docker rm -f echofix-backend echofix-n8n
```

---

## 📈 Performance & Diagnostics

```bash
# View resource usage
docker stats

# View specific container stats
docker stats echofix-backend

# Check disk usage
docker system df

# Clean up unused resources
docker system prune -a

# Check network
docker network ls
docker network inspect echofix-network
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────┐
│  MOST USED COMMANDS                         │
├─────────────────────────────────────────────┤
│  ./deploy.sh        → Start everything      │
│  ./stop.sh          → Stop all              │
│  ./status.sh        → Check health          │
│  ./logs.sh backend  → View backend logs     │
│  ./restart.sh       → Restart after config  │
│  ./rebuild.sh       → Rebuild after code    │
│  ./teardown.sh      → Delete everything     │
└─────────────────────────────────────────────┘
```

---

**Remember**: Use the `./script.sh` commands for simplicity. They handle all the Docker complexity for you!
