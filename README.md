# EchoFix 🎯

**Reddit-First Feedback-to-Shipping Pipeline for CruzHacks 2026**

EchoFix transforms Reddit feedback into actionable engineering artifacts and automated workflows. Built to showcase the power of **n8n** (orchestration) and **Gemini** (reasoning) with a local insight engine.

## 🚀 What It Does

1. **Collect**: Ingests Reddit threads via Reddit JSON (no OAuth required!) or PRAW
2. **Understand**: Groups feedback into themes with a local insight engine
3. **Reason**: Leverages Gemini to transform insights into structured issue specs with acceptance criteria
4. **Automate**: Orchestrates the entire pipeline with n8n workflows
5. **Ship**: Creates GitHub issues (and optionally PRs) with approval gates

## ✨ Hackathon Mode (No Reddit OAuth!)

**Perfect for hackathons with tight timelines:**
- **JSON-based ingestion**: Paste any Reddit thread URL, no API approval needed
- **Bring-Your-Own-Thread**: Demo with real Reddit content instantly
- **Works offline**: Full demo mode with fixtures if network is down
- **Zero OAuth friction**: Get started in < 5 minutes

## 🏆 CruzHacks Track Alignment

### n8n Track
- **Workflow Orchestration**: End-to-end automation from ingestion to GitHub
- **Scheduled Runs**: Automatic Reddit monitoring on cron
- **Approval Gates**: Human-in-the-loop approval via webhooks
- **GitHub Automation**: Issue/PR creation with labels and assignments

### Gemini Track
- **Structured Outputs**: Strict JSON schemas for issue specs and patch plans
- **Function Calling**: Tool-ready actions (create_issue, request_more_info)
- **Multimodal**: Processes images/screenshots from Reddit for bug reports
- **Reasoning**: Transforms unstructured feedback into engineering artifacts

## 📋 Architecture

```
┌─────────────┐
│   Reddit    │  JSON ingestion (no OAuth!) or PRAW
│   Threads   │  Paste URLs → fetch via JSON
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Insight    │  Local theme grouping
│  Engine     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Gemini    │  Insight → IssueSpec (structured JSON)
│  (Reasoning)│  Multimodal, function calling, guardrails
└──────┬──────┘
       │
       ▼
┌─────────────┐
│     n8n     │  Orchestrates workflows, approval gates
│(Automation) │  Triggers GitHub actions
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   GitHub    │  Issues created with evidence links
│             │  Optional: PRs with patch plans
└─────────────┘
       │
       ▼
┌─────────────┐
│  Dashboard  │  Review insights, approve actions
│  (Next.js)  │  Reddit evidence, Gemini outputs
└─────────────┘
```

## 🎬 Demo Mode

EchoFix supports **full demo mode** for environments without API keys:
- Uses pre-saved Reddit fixtures (JSON)
- Gemini responses from fixtures
- Full pipeline still runs end-to-end

Set `DEMO_MODE=true` in your `.env` file.

## 🛠️ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (for n8n)
- Supabase account (or local instance)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your credentials (or use DEMO_MODE=true)

# Run migrations
python migrate.py

# Start backend
python app.py
# Server runs on http://localhost:8000
```

### 2. Frontend Setup

```bash
cd webapp

# Install dependencies
npm install  # or pnpm install

# Setup environment
cp .env.example .env.local
# Edit with your Supabase credentials

# Start dev server
npm run dev
# Dashboard runs on http://localhost:3000
```

### 3. n8n Setup

```bash
cd workflows

# Start n8n with Docker
docker-compose up -d

# Access n8n at http://localhost:5678
# Import workflows from workflows/*.json
```

### 4. Run Demo

```bash
# Option 1: Use seed threads (configured in .env)
# Set REDDIT_SEED_THREAD_URLS in backend/.env, then:
curl -X POST http://localhost:8000/api/reddit/ingest-seed

# Option 2: Ingest a specific Reddit thread (paste any URL!)
curl -X POST http://localhost:8000/api/reddit/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://reddit.com/r/webdev/comments/abc123/my_post"}'

# Visit http://localhost:3000 to see results
```

## 📂 Project Structure

```
EchoFix/
├── backend/
│   ├── app.py              # Flask API server
│   ├── models.py           # Pydantic models
│   ├── db.py               # Database operations
│   ├── reddit_client.py    # Reddit PRAW (optional)
│   ├── services/
│   │   ├── reddit_rss.py   # Legacy RSS ingestion
│   │   └── insight_generator.py  # Local insight grouping
│   ├── gemini_client.py    # Gemini integration
│   ├── github_client.py    # GitHub operations
│   ├── sandbox.py          # Code sandbox (optional)
│   ├── requirements.txt
│   ├── .env.example
│   ├── fixtures/           # Demo mode data
│   │   ├── reddit_search.json
│   │   ├── reddit_rss_demo.json
│   └── supabase/
│       └── migrations/     # Database schema
├── webapp/
│   ├── app/                # Next.js app directory
│   ├── components/         # React components
│   ├── lib/                # Utilities
│   ├── package.json
│   └── .env.example
├── workflows/
│   ├── docker-compose.yml  # n8n setup
│   ├── scheduled-ingestion.json
│   ├── approval-workflow.json
│   └── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── DEMO.md             # Judge walkthrough
├── MIGRATION.md            # Migration notes from Vector
└── README.md               # This file
```

## 🔐 Environment Variables

### Backend (.env)
```bash
# Core
DEMO_MODE=false

# Reddit Ingestion Mode (hackathon-friendly!)
REDDIT_INGEST_MODE=json  # json (no OAuth!), praw (requires OAuth), rss_url (legacy), or fixtures
# Plan artifacts
ENABLE_PLAN_MD=true
ENABLE_PR_AUTOMATION=false
PLAN_MD_DIR=backend/artifacts/plans
PLAN_MD_PATH_TEMPLATE=docs/echofix_plans/{reddit_entry_id}.md
REDDIT_SEED_THREAD_URLS=https://reddit.com/r/webdev/comments/...,https://reddit.com/r/programming/comments/...

# Reddit JSON (no credentials needed!)
REDDIT_USER_AGENT=EchoFix/1.0 CruzHacks2026

# Score threshold gating
MIN_SCORE=2
SCORE_REFRESH_SECONDS=600

# Reddit API (OPTIONAL - only for PRAW mode)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_secret

# Gemini
GEMINI_API_KEY=your_gemini_key

# GitHub
GITHUB_TOKEN=your_github_token

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_key
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### n8n (docker-compose.yml)
```bash
N8N_ENCRYPTION_KEY=random_encryption_key
N8N_WEBHOOK_BASE_URL=http://localhost:5678
ECHOFIX_BACKEND_URL=http://host.docker.internal:8000
```

## 📊 API Endpoints

### Reddit Ingestion (JSON Mode - No OAuth!)
- `POST /api/reddit/ingest-url` - Ingest specific Reddit thread URL
- `POST /api/reddit/ingest-seed` - Ingest pre-configured seed threads
- `POST /api/reddit/ingest` - Legacy PRAW ingestion (optional)
- `POST /api/reddit/refresh-scores` - Refresh scores and mark entries READY once `MIN_SCORE` is met
- `GET /api/reddit/entries` - List collected entries
- `POST /api/pipeline/auto-process-ready` - Refresh & process READY entries, returns plan/PR links

### Insight Generation
- `POST /api/insights/generate` - Generate insights from READY entries (score threshold met)
- `GET /api/insights` - List insights

### Auto Pipeline
- `POST /api/pipeline/auto-process` - Refresh scores, generate insights, run Gemini, and create GitHub issues
- `POST /api/pipeline/auto-process-ready` - Ready-focused auto-run that reports issue/PR/plan artifacts

### Gemini Processing
- `POST /api/gemini/analyze` - Analyze insight with Gemini
- `POST /api/gemini/issue-spec` - Generate issue specification
- `POST /api/gemini/patch-plan` - Generate patch plan (optional)

### GitHub Actions
- `POST /api/github/create-issue` - Create GitHub issue
- `POST /api/github/create-pr` - Create pull request (with approval)

### Workflow Triggers (for n8n)
- `POST /api/workflows/trigger` - Generic workflow trigger
- `POST /api/workflows/approve` - Approval webhook

## 🎨 Dashboard Features

- **Reddit Feed**: Recent posts/comments with filtering
- **Insights Panel**: Local themes with trend indicators
- **Evidence View**: Links to original Reddit threads
- **Issue Specs**: Gemini-generated structured outputs
- **Approval UI**: One-click approve → n8n → GitHub
- **Demo Mode Indicator**: Clear visual when in demo mode

## 🧰 Demo Utilities

- `python backend/scripts/run_one_live.py <reddit_thread_url>` — ingest a live thread, refresh scores, and print issue/PR/plan outputs when the backend is running.

## 🔒 Security

- **No Auto-Merge**: All PRs require explicit approval
- **Approval Gates**: Human review before GitHub actions
- **Sandbox Isolation**: Code generation in isolated environment
- **Token Scoping**: Minimal GitHub permissions required
- **Rate Limiting**: Respects Reddit API limits

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd webapp
npm test

# E2E demo flow
./scripts/test-demo.sh
```

## 📚 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [Demo Script for Judges](docs/DEMO.md)
- [Migration Notes](MIGRATION.md)

## 🤝 Contributing

This is a hackathon project, but improvements welcome:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- Built on the foundation of **Vector** (X/Grok pipeline)
- Orchestrated by **n8n** for workflow automation
- Reasoning by **Gemini** for structured outputs
- Data from **Reddit** community feedback

## 🎯 CruzHacks 2026

**Team**: [Your Team Name]
**Tracks**: n8n, Gemini
**Demo**: [Link to demo video]

---

Made with ❤️ for CruzHacks 2026
