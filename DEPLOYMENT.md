# EchoFix Deployment Guide

Complete guide for deploying and managing EchoFix locally with Docker.

## Quick Start

### First-Time Setup

1. **Clone the repository** (if not already done):
   ```bash
   cd /Users/severinspagnola/Desktop/EchoFix
   ```

2. **Configure environment variables**:
   ```bash
   # The deploy script will create backend/.env from backend/.env.example
   # Edit it with your API keys:
   nano backend/.env
   ```

   Required variables (if not in DEMO_MODE):
   - `GEMINI_API_KEY` - Get from https://ai.google.dev/
   - `GITHUB_TOKEN` - Get from https://github.com/settings/tokens
   - `SUPABASE_URL` - Get from https://supabase.com/dashboard
   - `SUPABASE_SERVICE_ROLE_KEY` - Get from Supabase project settings

   Optional: Set `DEMO_MODE=true` to run without real API keys.

3. **Deploy everything**:
   ```bash
   ./deploy.sh
   ```

   This will:
   - Build Docker images
   - Start backend API (port 8000)
   - Start n8n workflow automation (port 5678)
   - Run health checks
   - Display service URLs

4. **Verify deployment**:
   ```bash
   ./status.sh
   ```

## Service URLs

Once deployed, access these URLs:

- **Backend API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **n8n Workflows**: http://localhost:5678

## Management Commands

All commands are simple shell scripts in the root directory:

### 🚀 Deploy/Start
```bash
./deploy.sh
```
First-time deployment or start after teardown. Builds images, starts services, runs health checks.

### 🛑 Stop Services
```bash
./stop.sh
```
Gracefully stop all services. **Data is preserved** (n8n workflows, volumes).

### 🔄 Restart Services
```bash
./restart.sh
```
Stop and start services. Use after configuration changes in `backend/.env`.

### 📊 View Status
```bash
./status.sh
```
Shows:
- Container status
- Health check results
- Resource usage (CPU, memory)
- Quick command reference

### 📋 View Logs
```bash
# All services
./logs.sh

# Backend only
./logs.sh backend

# n8n only
./logs.sh n8n
```
Follow logs in real-time. Press `Ctrl+C` to exit.

### 🔨 Rebuild After Code Changes
```bash
./rebuild.sh
```
Rebuild Docker images (no cache) and restart. Use after modifying Python code.

### 🗑️ Complete Teardown
```bash
./teardown.sh
```
**⚠️ WARNING**: Removes everything:
- Stops containers
- Deletes volumes (n8n data lost)
- Removes Docker images

You'll need to run `./deploy.sh` again to redeploy.

## Common Workflows

### Making Code Changes

1. Edit Python files in `backend/`
2. Rebuild and restart:
   ```bash
   ./rebuild.sh
   ```
3. Check logs for errors:
   ```bash
   ./logs.sh backend
   ```

### Changing Environment Variables

1. Edit `backend/.env`
2. Restart services:
   ```bash
   ./restart.sh
   ```

### Debugging Issues

1. Check status:
   ```bash
   ./status.sh
   ```

2. View logs:
   ```bash
   ./logs.sh backend
   ```

3. Check backend health directly:
   ```bash
   curl http://localhost:8000/health | python3 -m json.tool
   ```

4. Access container shell:
   ```bash
   docker exec -it echofix-backend /bin/bash
   ```

### Fresh Start

If things are broken and you want to start clean:

```bash
# Complete teardown
./teardown.sh

# Redeploy from scratch
./deploy.sh
```

## Docker Compose Commands

You can also use `docker-compose` directly:

```bash
# Start in foreground (see logs directly)
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose stop

# View logs
docker-compose logs -f

# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# Remove everything
docker-compose down -v
```

## Troubleshooting

### Backend Won't Start

**Check logs**:
```bash
./logs.sh backend
```

**Common issues**:
- Missing API keys in `backend/.env`
- Port 8000 already in use
- Supabase credentials invalid

**Solution**:
1. Verify `backend/.env` has correct values
2. Kill any process using port 8000:
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```
3. Restart:
   ```bash
   ./restart.sh
   ```

### n8n Won't Start

**Check logs**:
```bash
./logs.sh n8n
```

**Common issues**:
- Port 5678 already in use
- Backend dependency not healthy

**Solution**:
1. Ensure backend is healthy first:
   ```bash
   ./status.sh
   ```
2. Kill any process using port 5678:
   ```bash
   lsof -ti:5678 | xargs kill -9
   ```
3. Restart:
   ```bash
   ./restart.sh
   ```

### "Permission Denied" on Scripts

```bash
chmod +x *.sh
```

### Docker Not Running

Start Docker Desktop, then run:
```bash
./deploy.sh
```

### Clean Slate Needed

```bash
./teardown.sh
rm backend/.env
./deploy.sh
```

## Production Deployment

For production (AWS, GCP, etc.), you'll need:

1. **Set environment variables** via platform secrets (not `.env` file)
2. **Update `docker-compose.yml`**:
   - Remove port mappings (use reverse proxy)
   - Add restart policies
   - Configure logging drivers
3. **Use managed services**:
   - Supabase Cloud (already configured)
   - Managed n8n (n8n.cloud) or self-hosted
4. **Add SSL/TLS** with Nginx or Traefik
5. **Set up monitoring** with Prometheus/Grafana

## Architecture

```
┌─────────────────────────────────────┐
│         Docker Compose              │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │   Backend    │  │     n8n     │ │
│  │  (Flask API) │  │ (Workflows) │ │
│  │   Port 8000  │  │  Port 5678  │ │
│  └──────┬───────┘  └──────┬──────┘ │
│         │                 │         │
│         └─────────┬───────┘         │
│                   │                 │
│         ┌─────────▼─────────┐       │
│         │  echofix-network  │       │
│         │  (Bridge Network) │       │
│         └───────────────────┘       │
│                                     │
│  ┌─────────────────────────────┐   │
│  │     n8n_data (Volume)       │   │
│  │  Persists n8n workflows     │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
         │              │
         ▼              ▼
   Supabase Cloud    GitHub API
   (PostgreSQL)    Gemini API
                   Reddit API
```

## Quick Reference Card

```
┌─────────────────────────────────────────────────┐
│           ECHOFIX DEPLOYMENT COMMANDS           │
├─────────────────────────────────────────────────┤
│  🚀 Start:      ./deploy.sh                     │
│  🛑 Stop:       ./stop.sh                       │
│  🔄 Restart:    ./restart.sh                    │
│  📊 Status:     ./status.sh                     │
│  📋 Logs:       ./logs.sh [backend|n8n]         │
│  🔨 Rebuild:    ./rebuild.sh                    │
│  🗑️ Teardown:   ./teardown.sh                   │
├─────────────────────────────────────────────────┤
│  Service URLs:                                  │
│    Backend:  http://localhost:8000              │
│    n8n:      http://localhost:5678              │
├─────────────────────────────────────────────────┤
│  Config:     backend/.env                       │
│  Logs:       docker-compose logs -f             │
│  Shell:      docker exec -it echofix-backend sh │
└─────────────────────────────────────────────────┘
```

## Next Steps

After deployment:

1. **Access n8n**: Open http://localhost:5678
2. **Import workflows**: Import from `workflows/` directory
3. **Test API**:
   ```bash
   curl http://localhost:8000/health
   ```
4. **Read API docs**: See `backend/README.md`
5. **Configure repo**: Create a repo config via API or dashboard

---

**Need help?** Check logs with `./logs.sh` or view status with `./status.sh`
