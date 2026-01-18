# 🔄 n8n Workflow Setup - Resume Analyzer Monitoring

## Login Credentials

- **URL**: http://localhost:5678
- **Email**: severin.spagnola@sjsu.edu
- **Password**: c08-832mkdsxgxhmp7-a5b4-

## Quick Setup (5 minutes)

### 1. Access n8n

```bash
open http://localhost:5678
```

Login with the credentials above.

### 2. Create the Workflow

**Method A: Import JSON (Fastest)** ⭐

1. Click **"Workflows"** in the left sidebar
2. Click **"+ New workflow"** button (top right)
3. Click the **⋮** menu (three dots, top right)
4. Select **"Import from File"**
5. Choose: `workflows/resume_analyzer_monitor.json`
6. Click **"Save"** (top right)
7. Toggle **"Active"** switch to ON (top right)

**Method B: Build Manually (5 minutes)**

Follow the steps below if import doesn't work.

---

## Manual Workflow Creation

### Step 1: Create New Workflow

1. Click **"Workflows"** → **"+ New workflow"**
2. Name it: **"Resume Analyzer Monitor"**

### Step 2: Add Schedule Trigger

1. Click **"+ Add first step"**
2. Search for: **"Schedule Trigger"**
3. Configure:
   - **Trigger Interval**: `Minutes`
   - **Minutes Between Triggers**: `1`
4. Click outside to save

### Step 3: Ingest Reddit Comments

1. Click **"+"** after Schedule Trigger
2. Search for: **"HTTP Request"**
3. Configure:
   - **Method**: `POST`
   - **URL**: `http://backend:8000/api/reddit/ingest-seed`
4. Rename node: **"Ingest Thread Comments"**

### Step 4: Refresh Scores

1. Click **"+"** after previous node
2. Add another **"HTTP Request"**
3. Configure:
   - **Method**: `POST`
   - **URL**: `http://backend:8000/api/reddit/refresh-scores`
4. Rename node: **"Refresh Scores"**

### Step 5: Check if READY Entries Exist

1. Click **"+"** after Refresh Scores
2. Search for: **"IF"**
3. Configure:
   - **Condition**: `Number`
   - **Value 1**: `{{ $json.ready_count }}`
   - **Operation**: `Larger`
   - **Value 2**: `0`
4. Rename node: **"Has READY Entries?"**

### Step 6: Auto-Process READY Entries

1. Click **"+"** on the **"true"** output of IF node
2. Add **"HTTP Request"**
3. Configure:
   - **Method**: `POST`
   - **URL**: `http://backend:8000/api/pipeline/auto-process-ready`
4. Rename node: **"Auto-Process READY"**

### Step 7: Get Statistics (Optional)

1. Click **"+"** after Auto-Process
2. Add **"HTTP Request"**
3. Configure:
   - **Method**: `GET`
   - **URL**: `http://backend:8000/api/stats`
4. Rename node: **"Get Stats"**

### Step 8: Activate Workflow

1. Click **"Save"** (top right)
2. Toggle **"Active"** to ON (top right)
3. ✅ **Done!** Workflow runs every minute automatically

---

## What the Workflow Does

```
┌─────────────────────────────────────────────────┐
│  Every 1 Minute (Schedule Trigger)              │
│                                                 │
│  1. Ingest Thread Comments                     │
│     POST /api/reddit/ingest-seed               │
│     → Fetches new comments from:               │
│       r/Resume_Analyszer/userfeedback          │
│                                                 │
│  2. Refresh Scores                             │
│     POST /api/reddit/refresh-scores            │
│     → Checks Reddit for score updates          │
│     → Marks 2+ upvote entries as READY         │
│                                                 │
│  3. Check READY Count                          │
│     IF ready_count > 0                         │
│                                                 │
│  4. Auto-Process (if READY exists)             │
│     POST /api/pipeline/auto-process-ready      │
│     → Generates plan with Gemini               │
│     → Creates GitHub issue                     │
│     → Saves plan markdown                      │
│     → Marks as PROCESSED                       │
│                                                 │
│  5. Get Updated Stats                          │
│     GET /api/stats                             │
│     → Shows current pipeline status            │
└─────────────────────────────────────────────────┘
```

---

## Verify Workflow is Running

### Check Executions

1. In n8n, click your workflow
2. Click **"Executions"** tab (top)
3. You should see new executions every minute
4. Click any execution to see detailed logs

### Check Dashboard

1. Open: http://localhost:3000
2. Watch stats update automatically
3. See entries move from PENDING → READY → PROCESSED

### Check Backend Logs

```bash
./logs.sh backend
```

You should see:
- `Ingesting from seed URLs...`
- `Refreshing scores for X entries...`
- `Processing entry: ...`
- `Created GitHub issue: ...`

---

## Advanced Configuration

### Change Monitoring Frequency

**Every 30 seconds:**
1. Edit workflow
2. Click Schedule Trigger
3. Change to: `Seconds Between Triggers: 30`

**Every 5 minutes:**
1. Change to: `Minutes Between Triggers: 5`

### Add Notifications

**Slack Notification on New Issue:**

1. After "Auto-Process READY" node
2. Add **"Slack"** node
3. Configure:
   - **Message**: `New GitHub issue created from Reddit feedback!`
   - **Channel**: `#echofix-alerts`

**Email Notification:**

1. Add **"Send Email"** node
2. Configure recipient and message

### Add Error Handling

1. Click any node
2. Click **"Settings"** tab
3. Under **"Error Workflow"**:
   - Enable **"Continue On Fail"**
   - Add error handling logic

---

## Troubleshooting

### Workflow Not Running?

1. Check if **"Active"** toggle is ON
2. Check execution history for errors
3. Verify backend is healthy: `curl http://localhost:8000/health`

### "Connection Refused" Errors?

- URL should be `http://backend:8000` (NOT `localhost:8000`)
- n8n runs inside Docker and uses service names

### No READY Entries Being Processed?

1. Check MIN_SCORE in backend/.env (should be 2)
2. Manually test: `curl -X POST http://localhost:8000/api/reddit/refresh-scores`
3. Check if Reddit thread has comments with 2+ upvotes

### Executions Failing Silently?

1. Click failed execution
2. Check error message
3. Common issues:
   - Backend not responding → restart: `./restart.sh`
   - Supabase connection issue → check credentials
   - Rate limiting → increase interval

---

## Demo Tips

### For Hackathon Judges

1. **Open n8n**: http://localhost:5678
2. **Show the visual workflow** - judges love seeing automation!
3. **Run execution manually**: Click "Execute Workflow" button
4. **Show execution history** - proves it's been running
5. **Open dashboard in split screen**: Show n8n + dashboard updating together

### Impressive Demo Flow

```bash
# Terminal 1: Watch backend logs
./logs.sh backend

# Terminal 2: Open dashboard
open http://localhost:3000

# Browser: Open n8n workflow
open http://localhost:5678
```

**Tell judges:**
1. "This workflow monitors Reddit every minute"
2. "When feedback gets 2+ upvotes, it automatically..."
3. "Generates AI-powered plan" (show Gemini API)
4. "Creates GitHub issue" (show GitHub)
5. "All without any human intervention!"

---

## Workflow JSON Preview

Your workflow is saved in: `workflows/resume_analyzer_monitor.json`

If you need to modify it:
1. Export from n8n: **⋮ Menu** → **"Download"**
2. Edit JSON directly
3. Re-import to n8n

---

## Success Checklist

After setup, verify:

- ☑ n8n accessible at http://localhost:5678
- ☑ Can login with credentials
- ☑ Workflow imported/created
- ☑ Workflow activated (Active toggle ON)
- ☑ First execution completed successfully
- ☑ Dashboard showing updated data
- ☑ Backend logs showing activity
- ☑ GitHub issues being created

---

## Next Steps

1. Login to n8n: http://localhost:5678
2. Import workflow: `workflows/resume_analyzer_monitor.json`
3. Activate workflow
4. Watch dashboard: http://localhost:3000
5. See GitHub issues: https://github.com/Nayab-23/Resume_Analyzer/issues

**That's it! Your automated Reddit → Engineering pipeline is running!** 🚀
