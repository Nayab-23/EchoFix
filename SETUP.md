# EchoFix: Complete Setup & Run Guide

## ⚡ Quick Start (5 minutes) - Hackathon Mode

This will get EchoFix running with **Reddit JSON ingestion (no OAuth required!)** and demo fallbacks.

### Option A: Docker (Recommended - Easiest)

```bash
# Setup environment
cd backend
cp .env.example .env
# Edit .env and set:
# - REDDIT_INGEST_MODE=json (default, no OAuth needed!)
# - REDDIT_SEED_THREAD_URLS=<paste your Reddit thread URLs here>
# - DEMO_MODE=true (for demo fallbacks if no API keys)
# - MIN_SCORE=2 (minimum upvotes before processing)
# - ENABLE_PLAN_MD=true
# - ENABLE_PR_AUTOMATION=false
# - PLAN_MD_DIR=backend/artifacts/plans
# - PLAN_MD_PATH_TEMPLATE=docs/echofix_plans/{reddit_entry_id}.md

# Build and run with Docker Compose (from project root)
cd ..
docker-compose up --build

# Or run just the backend
docker-compose up backend
```

Backend is now running on **http://localhost:8000**
n8n (optional) is on **http://localhost:5678**

### Option B: Local Python (Manual Setup)

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and set:
# - REDDIT_INGEST_MODE=json (default, no OAuth needed!)
# - REDDIT_SEED_THREAD_URLS=<paste your Reddit thread URLs here>
# - DEMO_MODE=true (for demo fallbacks if no API keys)
# - ENABLE_PLAN_MD=true
# - ENABLE_PR_AUTOMATION=false
# - PLAN_MD_DIR=backend/artifacts/plans
# - PLAN_MD_PATH_TEMPLATE=docs/echofix_plans/{reddit_entry_id}.md

# Start the server
python app.py
```

Backend is now running on **http://localhost:8000**

### 2. Test JSON Ingestion (Hackathon Mode)

In a new terminal:

```bash
# Option 1: Ingest a specific Reddit thread (no OAuth!)
curl -X POST http://localhost:8000/api/reddit/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://reddit.com/r/webdev/comments/abc123/your_post"}'

# Option 2: Ingest pre-configured seed threads
curl -X POST http://localhost:8000/api/reddit/ingest-seed

# Refresh scores (updates eligibility after upvotes)
curl -X POST http://localhost:8000/api/reddit/refresh-scores

# Auto-process READY entries and capture plan/PR info
curl -X POST http://localhost:8000/api/pipeline/auto-process-ready

# Option 3: Run the full demo test script
chmod +x test_demo.sh
./test_demo.sh
```

Tip: `python backend/scripts/run_one_live.py https://reddit.com/r/...` ingests the URL, refreshes scores, and reports issue/PR/plan outputs in one go.

This will run through the entire pipeline:
- Ingest Reddit data via Reddit JSON (no OAuth!) or fixtures
- Refresh scores and mark entries READY (threshold gating)
- Generate insights
- Analyze with Gemini
- Create GitHub issue

### 3. (Optional) Start n8n

In a new terminal:

```bash
cd workflows

# Start n8n with Docker
docker-compose up -d

# Check logs
docker-compose logs -f n8n
```

n8n is now running on **http://localhost:5678**

Import workflows:
1. Open http://localhost:5678
2. Click "Add Workflow" → "Import from File"
3. Import `scheduled-ingestion.json`
4. Import `approval-workflow.json`
5. Activate both workflows

---

## 🔑 Live Mode Setup (Optional - Post-Hackathon)

### Reddit API (OPTIONAL - only for PRAW mode)
**Note**: JSON mode doesn't require Reddit API credentials! Only set these if you want to use PRAW mode.

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in:
   - Name: EchoFix
   - Type: Script
   - Redirect URI: http://localhost:8000
4. Copy **client ID** and **client secret**
5. Set `REDDIT_INGEST_MODE=praw` in `.env`

#### Gemini API
1. Go to https://ai.google.dev/
2. Get API key from Google AI Studio
3. Enable Gemini API

#### GitHub Token
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Scopes needed: `repo`, `workflow`
4. Copy token

#### Supabase
1. Sign up at https://supabase.com
2. Create new project
3. Get URL and service role key from Settings → API

### 2.5. Run Supabase Schema Migration (Required)

EchoFix needs the database schema before the API endpoints will work.

Option A (fastest): Supabase SQL Editor
1. Open the Supabase dashboard → SQL Editor
2. Copy/paste `backend/supabase/migrations/00001_create_core_schema.sql`
3. Copy/paste `backend/supabase/migrations/00002_add_reddit_entry_status.sql`
4. Copy/paste `backend/supabase/migrations/00003_add_plan_and_pr_columns.sql`
5. Click "Run"

Option B: Supabase CLI (if installed and authenticated)
```bash
npm install -g supabase
supabase login
# Or with a CI/CLI token:
# supabase login --token <your-token>
supabase link --project-ref your-project-id
supabase db push
```

Note: The migration uses Postgres-specific features (UUIDs, JSONB, arrays, RLS), so it must run on Supabase/Postgres.

### 2. Configure Environment

Edit `backend/.env`:

```bash
DEMO_MODE=false
MIN_SCORE=2
SCORE_REFRESH_SECONDS=600

REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=EchoFix/1.0 by your_reddit_username

GEMINI_API_KEY=your_gemini_key_here

GITHUB_TOKEN=your_github_token_here

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

If you are running via Docker, restart the backend so it picks up the new `.env`:
```bash
docker-compose up -d --build backend
```

### 3. Setup Database

In Supabase dashboard:
1. Go to SQL Editor
2. Open `backend/supabase/migrations/00001_create_core_schema.sql`
3. Open `backend/supabase/migrations/00002_add_reddit_entry_status.sql`
4. Copy and paste each file (in order)
5. Click "Run"

Or use Supabase CLI:

```bash
npm install -g supabase
supabase link --project-ref your-project-id
supabase db push
```

### 4. Configure Monitoring

Create a repo config:

```bash
curl -X POST http://localhost:8000/api/repo-configs \
  -H "Content-Type: application/json" \
  -d '{
    "github_owner": "your-username",
    "github_repo": "your-repo",
    "github_branch": "main",
    "subreddits": ["programming", "webdev"],
    "keywords": ["your-app-name", "bug", "issue"],
    "product_names": ["YourAppName"]
  }'
```

### 5. Authenticate GitHub CLI

```bash
gh auth login
```

Follow prompts to authenticate.

### 6. Test Live Mode

```bash
# Ingest live Reddit data
curl -X POST http://localhost:8000/api/reddit/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "subreddits": ["programming"],
    "keywords": ["python"],
    "limit": 10,
    "time_filter": "day"
  }'

# Check collected entries
curl http://localhost:8000/api/reddit/entries | jq '.count'

# Refresh scores (threshold gating)
curl -X POST http://localhost:8000/api/reddit/refresh-scores

# Generate insights
curl -X POST http://localhost:8000/api/insights/generate

# Fetch insights
curl http://localhost:8000/api/insights | jq

# Auto-run end-to-end (refresh → insights → Gemini → GitHub)
curl -X POST http://localhost:8000/api/pipeline/auto-process
```

---

## API Testing with Postman/Insomnia

Import this collection:

```json
{
  "name": "EchoFix API",
  "requests": [
    {
      "name": "Health Check",
      "method": "GET",
      "url": "http://localhost:8000/health"
    },
    {
      "name": "Ingest Reddit",
      "method": "POST",
      "url": "http://localhost:8000/api/reddit/ingest",
      "body": {
        "subreddits": ["webdev"],
        "keywords": ["bug"],
        "limit": 20
      }
    },
    {
      "name": "Get Insights",
      "method": "GET",
      "url": "http://localhost:8000/api/insights"
    },
    {
      "name": "Analyze Insight",
      "method": "POST",
      "url": "http://localhost:8000/api/gemini/analyze/{insight_id}"
    },
    {
      "name": "Create GitHub Issue",
      "method": "POST",
      "url": "http://localhost:8000/api/github/create-issue",
      "body": {
        "insight_id": "{insight_id}"
      }
    }
  ]
}
```

---

## n8n Workflow Testing

### Test Scheduled Ingestion Workflow

1. Open http://localhost:5678
2. Open "Scheduled Reddit Ingestion" workflow
3. Click "Execute Workflow" button (play icon)
4. Watch execution in real-time
5. Check "Execution Log" for results

### Test Approval Workflow

Send webhook request:

```bash
curl -X POST http://localhost:5678/webhook/approve-insight \
  -H "Content-Type: application/json" \
  -d '{
    "insight_id": "paste-insight-id-here",
    "action": "approve",
    "user_id": "00000000-0000-0000-0000-000000000001"
  }'
```

Watch the workflow execute in n8n UI.

---

## Troubleshooting

### Backend won't start

**Error: ModuleNotFoundError**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

**Error: Connection to Supabase failed**
```bash
# Check your .env file
cat .env | grep SUPABASE

# Or use demo mode
DEMO_MODE=true python app.py
```

### Reddit API errors

**Error: Invalid credentials**
```bash
# Verify Reddit credentials in .env
# Make sure redirect URI matches in Reddit app settings
# Try demo mode: DEMO_MODE=true
```

**Error: Rate limit exceeded**
```bash
# Reddit has rate limits (60 requests/minute)
# Wait a minute and try again
# Or reduce limit parameter in request
```

### Gemini API errors

**Error: API key invalid**
```bash
# Get new key from https://ai.google.dev/
# Ensure billing is enabled
# Or use demo mode
```

### n8n can't connect to backend

**Error: ECONNREFUSED**
```bash
# Check backend is running
curl http://localhost:8000/health

# If on Mac/Windows, use: http://host.docker.internal:8000
# If on Linux, use: http://172.17.0.1:8000

# Update workflow HTTP Request nodes with correct URL
```

### GitHub CLI not authenticated

**Error: gh: To get started...**
```bash
# Authenticate gh CLI
gh auth login

# Follow interactive prompts
# Or use demo mode for testing
```

---

## File Structure Reference

```
EchoFix/
├── README.md                           # Main project overview
├── MIGRATION.md                        # Migration notes from Vector
├── IMPLEMENTATION_STATUS.md            # What's been completed
├── test_demo.sh                        # Demo test script
├── backend/
│   ├── app.py                          # Flask API server
│   ├── models.py                       # Pydantic models
│   ├── reddit_client.py                # Reddit ingestion
│   ├── gemini_client.py                # Gemini AI
│   ├── github_client.py                # GitHub operations
│   ├── db.py                           # Database layer
│   ├── services/                       # Local services
│   │   ├── reddit_rss.py               # Legacy RSS ingestion
│   │   └── insight_generator.py        # Insight grouping
│   ├── requirements.txt                # Python deps
│   ├── .env.example                    # Environment template
│   ├── README.md                       # Backend docs
│   ├── fixtures/                       # Demo data
│   │   ├── reddit_search.json
│   │   └── reddit_rss_demo.json
│   └── supabase/
│       └── migrations/
│           └── 00001_create_core_schema.sql
├── workflows/
│   ├── scheduled-ingestion.json        # n8n workflow 1
│   ├── approval-workflow.json          # n8n workflow 2
│   ├── docker-compose.yml              # n8n Docker setup
│   └── README.md                       # Workflow docs
└── docs/
    └── DEMO.md                         # Judge walkthrough
```

---

## 🐳 Docker Commands Reference

### Build and Run

```bash
# Build and start all services (backend + n8n)
docker-compose up --build

# Run in detached mode (background)
docker-compose up -d

# Run only backend
docker-compose up backend

# Rebuild specific service
docker-compose build backend
```

### Management

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f n8n

# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove with volumes (clean slate)
docker-compose down -v
```

### Development

```bash
# Execute commands in running container
docker-compose exec backend python test_rss.py

# Access shell in container
docker-compose exec backend bash

# Check health status
docker-compose ps
```

### Production Deployment

For production deployment, consider:
- Using environment-specific `.env` files
- Setting `DEMO_MODE=false`
- Configuring proper secrets management
- Adding reverse proxy (nginx/traefik)
- Setting up persistent volumes for data

---

## What's Next?

### Immediate (if demoing):
1. ✅ Run `test_demo.sh` to verify everything works
2. ✅ Start n8n and import workflows
3. ✅ Practice the 3-minute demo (see docs/DEMO.md)
4. 📹 Record a backup demo video

### Short-term (if building further):
1. Create a simple frontend dashboard
2. Add more comprehensive tests
3. Deploy to cloud (Vercel + Railway/Render)
4. Add more n8n workflows

### Long-term (post-hackathon):
1. Support more platforms (Twitter, HackerNews)
2. Add email/Slack notifications
3. Implement PR generation with code changes
4. Add analytics dashboard
5. Multi-tenant support

---

## Demo Checklist

Before presenting to judges:

- [ ] Backend running (`python app.py`)
- [ ] `test_demo.sh` completes successfully
- [ ] n8n running and workflows imported
- [ ] GitHub repo visible and accessible
- [ ] Demo script (docs/DEMO.md) reviewed
- [ ] Architecture diagram ready to show
- [ ] Backup demo video recorded
- [ ] Team knows who presents what
- [ ] Laptop charged and display mirrored

---

## Resources

- **EchoFix Repo**: github.com/[your-username]/EchoFix
- **Reddit API Docs**: https://www.reddit.com/dev/api
- **Gemini API Docs**: https://ai.google.dev/docs
- **n8n Docs**: https://docs.n8n.io
- **Supabase Docs**: https://supabase.com/docs

---

## Support

For issues or questions:
1. Check IMPLEMENTATION_STATUS.md for known limitations
2. Check backend logs for errors
3. Try demo mode: `DEMO_MODE=true`
4. Review workflow execution logs in n8n

---

**Good luck at CruzHacks! 🎯**
