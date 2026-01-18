# 🎯 EchoFix Demo Setup - Resume Analyzer Monitoring

## Overview

This demo monitors the Resume Analyzer feedback thread on Reddit and automatically creates GitHub issues/PRs when comments get 2+ upvotes.

### Configuration

- **Reddit Thread**: https://www.reddit.com/r/Resume_Analyszer/comments/1qfzivr/userfeedback/
- **Target Repo**: https://github.com/Nayab-23/Resume_Analyzer.git
- **Score Threshold**: 2 upvotes (MIN_SCORE=2)
- **Monitoring Interval**: Every 60 seconds
- **Auto-processing**: Enabled

## Quick Start

### 1. Deploy EchoFix

```bash
./deploy.sh
```

Wait for all services to start:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- n8n: http://localhost:5678

### 2. Run Initial Setup

```bash
./setup_demo.sh
```

This will:
1. Create repo configuration for Resume_Analyzer
2. Ingest all comments from the feedback thread
3. Check scores and mark posts with 2+ upvotes as READY
4. Show current pipeline status

### 3. Start Continuous Monitoring

Choose one of these methods:

#### Method A: Shell Script (Recommended for Testing)

```bash
./start_monitoring.sh
```

This runs in your terminal and shows real-time updates every 60 seconds:
- Ingests new comments
- Refreshes scores
- Auto-processes READY entries (2+ upvotes)
- Shows stats

Press Ctrl+C to stop.

#### Method B: n8n Workflow (Recommended for Production)

1. Open n8n: http://localhost:5678
2. Import workflow: `workflows/resume_analyzer_monitor.json`
3. Activate the workflow
4. It will run automatically every 1 minute

## What Happens Automatically

```
┌─────────────────────────────────────────────────────┐
│  Every 60 seconds:                                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Fetch new comments from Reddit thread          │
│     ↓                                               │
│  2. Check scores for all entries                   │
│     ↓                                               │
│  3. Mark entries with 2+ upvotes as READY          │
│     ↓                                               │
│  4. For each READY entry:                          │
│     • Generate plan with Gemini                    │
│     • Create GitHub issue                          │
│     • Save plan markdown                           │
│     • (Optional) Create PR                         │
│     ↓                                               │
│  5. Mark as PROCESSED                              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Dashboard Features

Open http://localhost:3000 to see:

### Pipeline Status Cards
- **PENDING**: Comments below 2 upvotes
- **READY**: Comments with 2+ upvotes (waiting to process)
- **PROCESSING**: Currently generating plan/issue/PR
- **PROCESSED**: Issue/PR created successfully

### Control Panel
- **Ingest Reddit URL**: Manually add a specific comment
- **Load Demo Data**: Re-ingest the feedback thread
- **Refresh Scores**: Check Reddit for score updates
- **Process Ready**: Manually trigger processing
- **Gen Insights**: Generate insights from processed entries

### Reddit Entries Table
- Filter by status (All/Pending/Ready/Processing/Processed)
- Shows score, author, timestamps
- Links to original Reddit comment
- Links to created GitHub issues/PRs
- Shows plan generation status

## Testing the Demo

### Test 1: Ingest and Process Existing Comments

```bash
# 1. Ingest thread
curl -X POST http://localhost:8000/api/reddit/ingest-seed

# 2. Check scores
curl -X POST http://localhost:8000/api/reddit/refresh-scores

# 3. Process READY entries
curl -X POST http://localhost:8000/api/pipeline/auto-process-ready

# 4. Check results
curl http://localhost:8000/api/stats | jq .
```

### Test 2: Simulate New Comment

1. Post a comment on the Reddit thread: https://www.reddit.com/r/Resume_Analyszer/comments/1qfzivr/userfeedback/
2. Upvote it to get 2+ upvotes
3. Wait 60 seconds for monitoring to detect it
4. Watch the dashboard update automatically
5. See the GitHub issue created at: https://github.com/Nayab-23/Resume_Analyzer/issues

### Test 3: Monitor in Real-Time

```bash
# Terminal 1: Start monitoring
./start_monitoring.sh

# Terminal 2: Watch logs
./logs.sh backend

# Terminal 3: Watch frontend in browser
open http://localhost:3000
```

## Configuration Details

### Backend Environment Variables

Located in `backend/.env`:

```bash
# Score threshold (2+ upvotes triggers processing)
MIN_SCORE=2

# Refresh interval (60 seconds)
SCORE_REFRESH_SECONDS=60

# Target thread
REDDIT_SEED_THREAD_URLS=https://www.reddit.com/r/Resume_Analyszer/comments/1qfzivr/userfeedback/

# Plan generation enabled
ENABLE_PLAN_MD=true

# PR automation disabled (can enable with ENABLE_PR_AUTOMATION=true)
ENABLE_PR_AUTOMATION=false
```

### Repository Configuration

Automatically created by `setup_demo.sh`:

```json
{
  "github_owner": "Nayab-23",
  "github_repo": "Resume_Analyzer",
  "github_branch": "main",
  "subreddits": ["Resume_Analyszer"],
  "keywords": ["bug", "feature", "issue", "problem", "suggestion", "improve"],
  "auto_create_issues": true,
  "auto_create_prs": false,
  "require_approval": false
}
```

## Monitoring Commands

```bash
# View backend logs (shows processing activity)
./logs.sh backend

# View all logs
./logs.sh

# Check service status
./status.sh

# View current stats
curl http://localhost:8000/api/stats | jq .

# View all entries
curl http://localhost:8000/api/reddit/entries | jq .

# View insights
curl http://localhost:8000/api/insights | jq .
```

## Troubleshooting

### No entries being ingested?

```bash
# Check if backend can reach Reddit
curl http://localhost:8000/health

# Try manual ingest
curl -X POST http://localhost:8000/api/reddit/ingest-seed

# Check logs
./logs.sh backend
```

### Entries stuck in PENDING?

```bash
# Manually refresh scores
curl -X POST http://localhost:8000/api/reddit/refresh-scores

# Check MIN_SCORE setting
grep MIN_SCORE backend/.env
```

### READY entries not processing?

```bash
# Manually trigger processing
curl -X POST http://localhost:8000/api/pipeline/auto-process-ready

# Check Gemini API key
grep GEMINI_API_KEY backend/.env

# Check GitHub token
grep GITHUB_TOKEN backend/.env
```

### Monitoring script not running?

```bash
# Make sure backend is healthy
curl http://localhost:8000/health

# Check if port 8000 is accessible
lsof -i :8000

# Restart services
./restart.sh
```

## Demo Flow for Judges

### 1. Show the Problem (30 seconds)
- "We have user feedback scattered across Reddit"
- "Engineers manually check for important issues"
- "GitHub issues get created inconsistently"

### 2. Show EchoFix Solution (1 minute)
- Open dashboard: http://localhost:3000
- Point to the feedback thread being monitored
- Show the pipeline status (PENDING → READY → PROCESSING → PROCESSED)

### 3. Live Demo (2 minutes)

```bash
# Start monitoring
./start_monitoring.sh
```

- Watch terminal show real-time monitoring
- Show dashboard updating
- Filter by READY to see posts with 2+ upvotes
- Click on a PROCESSED entry to show GitHub issue link

### 4. Show the Output (1 minute)
- Open GitHub repo: https://github.com/Nayab-23/Resume_Analyzer
- Show automatically created issues
- Show structured plan markdown
- Highlight Gemini-generated insights

### 5. Show Automation (30 seconds)
- Open n8n: http://localhost:5678
- Show visual workflow
- Explain: "This runs continuously, no human intervention needed"

## Advanced Features

### Enable PR Automation

Edit `backend/.env`:
```bash
ENABLE_PR_AUTOMATION=true
```

Restart:
```bash
./restart.sh
```

Now READY entries will also create PR stubs automatically.

### Change Score Threshold

Edit `backend/.env`:
```bash
MIN_SCORE=5  # Require 5+ upvotes instead of 2
```

### Change Monitoring Frequency

Edit `start_monitoring.sh`:
```bash
POLL_INTERVAL=30  # Check every 30 seconds
```

Or in n8n workflow, change the Schedule Trigger interval.

## Success Metrics

After running for a few minutes, you should see:

- ✅ Multiple entries ingested from Reddit thread
- ✅ Entries with 2+ upvotes marked as READY
- ✅ READY entries auto-processed
- ✅ GitHub issues created with structured plans
- ✅ Dashboard showing real-time status
- ✅ Plan markdown files generated
- ✅ Insights generated from feedback patterns

## Next Steps

1. Deploy EchoFix: `./deploy.sh`
2. Run setup: `./setup_demo.sh`
3. Start monitoring: `./start_monitoring.sh`
4. Watch the magic happen! ✨

Open http://localhost:3000 and watch feedback turn into actionable engineering work!
