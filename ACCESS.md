# 📍 EchoFix Access Guide

## Quick Answer

After running `./deploy.sh`, access your services here:

| Service | URL | Purpose |
|---------|-----|---------|
| **Dashboard** | http://localhost:3000 | Main UI - View feedback, insights, stats |
| **n8n** | http://localhost:5678 | Workflow automation and orchestration |
| **Backend API** | http://localhost:8000 | REST API endpoints |

---

## 🎨 Frontend Dashboard (Port 3000)

**URL**: http://localhost:3000

### What You'll See:
- 📊 **Stats Cards**: Total insights, Reddit entries, pending/ready counts
- 📝 **Feedback Table**: All ingested feedback with platform icons
- 💡 **Insights Section**: Generated insights with GitHub issue links
- 🟢 **Health Indicator**: Backend connectivity status

### Features:
- Real-time updates (refreshes every 5 seconds)
- Platform badges (🔴 Reddit, 💜 GitHub, 🟠 HackerNews)
- Status indicators (pending, ready, processed)
- Click-through links to original posts
- Direct link to n8n in header

---

## 🔄 n8n Workflow Automation (Port 5678)

**URL**: http://localhost:5678

### What You'll See:
- Visual workflow editor
- Execution history
- Workflow templates
- Trigger configuration

### Use Cases:
- Create multi-platform ingestion workflows
- Schedule automated polling
- Set up webhooks
- Monitor pipeline execution

---

## 🔌 Backend API (Port 8000)

**URL**: http://localhost:8000

### Health Check:
```bash
curl http://localhost:8000/health
```

### Key Endpoints:

**Feedback Ingestion:**
```bash
# Ingest from Reddit
POST /api/reddit/ingest

# Ingest seed data
POST /api/reddit/ingest-seed
```

**Insights:**
```bash
# Get all insights
GET /api/insights

# Generate new insights
POST /api/insights/generate
```

**Statistics:**
```bash
# Get dashboard stats
GET /api/stats
```

---

## 🚀 Quick Start Workflow

1. **Deploy Everything:**
   ```bash
   ./deploy.sh
   ```

2. **Access Dashboard:**
   ```bash
   open http://localhost:3000
   ```

3. **Ingest Data:**
   ```bash
   curl -X POST http://localhost:8000/api/reddit/ingest-seed
   ```

4. **Watch Dashboard Update!**
   - Refresh http://localhost:3000
   - See new entries appear in table
   - Watch stats update

5. **Open n8n:**
   ```bash
   open http://localhost:5678
   ```

---

## 🔍 Verification

### Check if Everything is Running:
```bash
./status.sh
```

### Test Each Service:
```bash
# Frontend
curl -I http://localhost:3000

# Backend
curl http://localhost:8000/health

# n8n
curl -I http://localhost:5678
```

---

## 🛠️ Troubleshooting

### Can't Access Dashboard (Port 3000)?

**Check if frontend is running:**
```bash
docker ps | grep frontend
```

**View logs:**
```bash
./logs.sh frontend
```

**Restart:**
```bash
docker-compose restart frontend
```

### Can't Access n8n (Port 5678)?

**Check if n8n is running:**
```bash
docker ps | grep n8n
```

**View logs:**
```bash
./logs.sh n8n
```

### Can't Access Backend (Port 8000)?

**Check health:**
```bash
./status.sh
```

**View logs:**
```bash
./logs.sh backend
```

---

## 📱 For Hackathon Demo

### Best Demo Flow:

1. **Start with Dashboard** (http://localhost:3000)
   - Show clean, modern UI
   - Point out real-time stats

2. **Ingest Data Live:**
   ```bash
   curl -X POST http://localhost:8000/api/reddit/ingest-seed
   ```
   - Refresh dashboard
   - Watch table populate

3. **Show n8n** (http://localhost:5678)
   - Visual workflow
   - Multi-platform automation
   - "This orchestrates everything"

4. **Back to Dashboard**
   - Show generated insights
   - Click GitHub issue links
   - Demonstrate end-to-end flow

---

## 🎯 Port Summary

| Port | Service | Access |
|------|---------|--------|
| 3000 | Frontend Dashboard | Browser |
| 5678 | n8n | Browser |
| 8000 | Backend API | cURL / Dashboard |

---

## 💡 Pro Tips

1. **Bookmark these URLs** in your browser
2. **Keep Dashboard open** during development
3. **Use n8n** to impress judges (visual workflows)
4. **Monitor backend health** with `/health` endpoint
5. **Check logs** if something doesn't update: `./logs.sh`

---

## 🎉 Summary

**Your main dashboard**: http://localhost:3000

This is what you show to judges and users. It's a beautiful, real-time interface showing all your feedback aggregation and prioritization in action!

n8n (port 5678) is your automation engine - use it to create workflows.

Backend (port 8000) is your API - the dashboard uses it automatically.

---

**Next Steps:**
1. Run `./deploy.sh`
2. Open http://localhost:3000
3. Start demoing!
