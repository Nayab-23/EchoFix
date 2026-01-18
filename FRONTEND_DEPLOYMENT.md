# 🎨 EchoFix Frontend Dashboard

## 📍 Access Your Dashboard

Once deployed, access at:
- **Frontend Dashboard**: http://localhost:3000
- **n8n Workflows**: http://localhost:5678
- **Backend API**: http://localhost:8000

---

## 🚀 Quick Deploy (All Services)

```bash
./deploy.sh
```

This now deploys:
- ✅ Backend (port 8000)
- ✅ Frontend Dashboard (port 3000) **NEW!**
- ✅ n8n (port 5678)

---

## 🎨 Deploy Frontend Only

If you already have backend running:

```bash
./deploy-frontend.sh
```

---

## 🔧 Development Mode (Local, No Docker)

For faster development iteration:

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Run Development Server
```bash
npm run dev
```

Frontend will be available at http://localhost:3000 with hot reload!

---

## 🎯 What You'll See

### Dashboard Features

**Stats Cards:**
- Total Insights
- Reddit Entries
- Pending Items
- Ready Items

**Feedback Table:**
- Platform icons (Reddit 🔴, GitHub 💜, HN 🟠)
- Entry titles and authors
- Engagement scores
- Status badges
- Links to original posts

**Insights Section:**
- Generated insights
- Entry counts
- Status tracking
- Links to GitHub issues

---

## 📋 Service Architecture

```
┌─────────────────────────────────────────┐
│         Your Browser                    │
│                                         │
│  http://localhost:3000 (Frontend)      │
│  http://localhost:5678 (n8n)           │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│       Docker Compose Stack              │
│                                         │
│  ┌──────────┐  ┌──────────┐  ┌───────┐ │
│  │ Frontend │  │  Backend │  │  n8n  │ │
│  │ Next.js  │◄─┤  Flask   │◄─┤Workflows│
│  │ Port 3000│  │ Port 8000│  │Port 5678│
│  └──────────┘  └──────────┘  └───────┘ │
│                     │                   │
│                     ▼                   │
│             Supabase, Gemini, GitHub    │
└─────────────────────────────────────────┘
```

---

## 🔄 Bring Up & Down (Updated)

### Bring Down
```bash
# Stop all services (keeps data)
./stop.sh

# Complete teardown
./teardown.sh
```

### Bring Up
```bash
# Deploy everything
./deploy.sh

# Or deploy frontend separately
./deploy-frontend.sh
```

---

## 📊 View Logs

```bash
# All services
./logs.sh

# Frontend only
./logs.sh frontend
docker-compose logs -f frontend

# Backend only
./logs.sh backend

# n8n only
./logs.sh n8n
```

---

## 🛠️ Troubleshooting

### Frontend Won't Start

**Check logs:**
```bash
docker-compose logs frontend
```

**Common issues:**
- Backend not running
- Port 3000 already in use
- Docker out of memory

**Solutions:**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Restart
docker-compose restart frontend

# Rebuild
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Can't Connect to Backend

**Check environment:**
```bash
cat frontend/.env.local
```

Should show:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Verify backend is healthy:**
```bash
./status.sh
curl http://localhost:8000/health
```

### Frontend Shows No Data

**Trigger data ingestion:**
```bash
# Ingest from Reddit (demo mode)
curl -X POST http://localhost:8000/api/reddit/ingest-seed

# Generate insights
curl -X POST http://localhost:8000/api/insights/generate

# Refresh frontend page
```

---

## 🎯 Demo Workflow

For hackathon judges:

1. **Open Dashboard**
   ```bash
   open http://localhost:3000
   ```

2. **Show Stats** - Real-time updates

3. **Ingest Feedback**
   ```bash
   curl -X POST http://localhost:8000/api/reddit/ingest-seed
   ```

4. **Watch Dashboard Update** - Shows new entries in table

5. **Show n8n Workflow**
   ```bash
   open http://localhost:5678
   ```

6. **Create Insights**
   ```bash
   curl -X POST http://localhost:8000/api/pipeline/auto-process
   ```

7. **Dashboard Shows GitHub Issues** - Links appear

---

## 🔧 Customization

### Change API URL

Edit `frontend/.env.local`:
```bash
NEXT_PUBLIC_API_URL=https://your-backend.com
```

Then rebuild:
```bash
docker-compose build frontend
docker-compose up -d frontend
```

### Modify Styling

Edit `frontend/app/globals.css` or component files, then:
```bash
docker-compose restart frontend
```

For development (hot reload):
```bash
cd frontend
npm run dev
```

---

## ✅ Success Checklist

After deployment:

- ☑ http://localhost:3000 loads dashboard
- ☑ Stats cards show data
- ☑ Feedback table populates
- ☑ Health indicator shows "Healthy"
- ☑ n8n link works from header

---

## 💡 Pro Tips

1. **Use development mode** for UI changes (faster iteration)
2. **View browser console** for debugging (F12)
3. **Refresh data** by triggering backend endpoints
4. **Check Docker logs** if page is blank
5. **Ensure backend is healthy** before accessing frontend

---

## 🎉 You're Ready!

```bash
# Deploy everything
./deploy.sh

# Access dashboard
open http://localhost:3000
```

**Your complete stack:**
- Dashboard: http://localhost:3000 ← **Your main UI**
- n8n: http://localhost:5678 ← Workflow automation
- API: http://localhost:8000 ← Backend

---

For detailed deployment commands, see [BRING_UP_DOWN.md](BRING_UP_DOWN.md)
