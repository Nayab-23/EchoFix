# ⚡ EchoFix QuickStart - Resume Analyzer Demo

> Automatically monitor Reddit feedback and create GitHub issues when posts get 2+ upvotes

## 🎯 One-Command Demo

```bash
./open_demo.sh
```

This opens:
- ✅ Dashboard (http://localhost:3000)
- ✅ n8n Workflow (http://localhost:5678)
- ✅ GitHub Repo
- ✅ Reddit Thread

## 📋 Setup Steps (5 minutes)

### 1. Deploy Services

```bash
./deploy.sh
```

Wait for:
- Backend: http://localhost:8000 ✅
- Frontend: http://localhost:3000 ✅
- n8n: http://localhost:5678 ✅

### 2. Setup n8n Monitoring

```bash
# Login to n8n
open http://localhost:5678

# Credentials:
Email: severin.spagnola@sjsu.edu
Password: c08-832mkdsxgxhmp7-a5b4-
```

**Then:**
1. Click **"+ New workflow"**
2. Click **⋮ menu** → **"Import from File"**
3. Select: `workflows/resume_analyzer_monitor.json`
4. Click **"Save"**
5. Toggle **"Active"** to ON ✅

**Done!** Workflow runs every minute automatically.

### 3. Watch It Work

```bash
# Open dashboard
open http://localhost:3000
```

Watch entries move through pipeline:
- PENDING → READY → PROCESSING → PROCESSED

---

## 🎬 What Gets Monitored

**Reddit Thread:**
https://www.reddit.com/r/Resume_Analyszer/comments/1qfzivr/userfeedback/

**Target Repo:**
https://github.com/Nayab-23/Resume_Analyzer

**What Happens:**
1. Every 60 seconds: Check thread for new comments
2. Comments with 2+ upvotes → Mark as READY
3. READY entries → Auto-process:
   - Generate plan with Gemini AI
   - Create GitHub issue
   - Save plan markdown
4. Track everything in dashboard

---

## ✅ Success Checklist

Before demo:

- ☑ All services running (`./status.sh`)
- ☑ n8n workflow activated
- ☑ Dashboard accessible (http://localhost:3000)
- ☑ Can see Reddit entries in dashboard
- ☑ n8n executions showing in history

---

## 🎉 You're Ready!

```bash
# Start everything
./deploy.sh

# Open demo
./open_demo.sh

# Setup n8n workflow
open http://localhost:5678

# Watch it work!
open http://localhost:3000
```

**See N8N_SETUP.md for detailed workflow instructions!**
