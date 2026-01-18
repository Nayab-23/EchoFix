# EchoFix Backend

Flask API server for the Reddit-first feedback-to-shipping pipeline.

## Quick Start

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env - at minimum, set DEMO_MODE=true for testing

# Run server
python app.py
```

Server runs on http://localhost:8000

## Demo Mode

For quick testing without API credentials:

```bash
# In .env
DEMO_MODE=true
```

Demo mode uses pre-saved fixtures for:
- Reddit data (`fixtures/reddit_search.json`)
- Gemini responses (generated defaults)
- GitHub operations (mocked with fake URLs)

The entire pipeline still runs end-to-end!

## API Endpoints

### Health
- `GET /health` - Health check with service status

### Reddit Ingestion
- `POST /api/reddit/ingest` - Trigger Reddit data collection
- `POST /api/reddit/refresh-scores` - Refresh scores and mark entries READY once `MIN_SCORE` is met
- `GET /api/reddit/entries` - List collected entries

### Insight Generation
- `POST /api/insights/generate` - Generate insights from READY entries (score threshold met)

### Auto Pipeline
- `POST /api/pipeline/auto-process` - Refresh scores, generate insights, run Gemini, and create GitHub issues

### Gemini Analysis
- `POST /api/gemini/analyze/<insight_id>` - Analyze insight with Gemini

### Insights Management
- `GET /api/insights` - List all insights
- `GET /api/insights/<insight_id>` - Get specific insight with entries
- `PUT /api/insights/<insight_id>/status` - Update insight status

### GitHub Actions
- `POST /api/github/create-issue` - Create GitHub issue from insight

### Workflow Triggers (for n8n)
- `POST /api/workflows/trigger` - Generic workflow trigger
- `POST /api/workflows/approve` - Approval webhook

### Config & Stats
- `GET /api/repo-configs` - List repo configurations
- `POST /api/repo-configs` - Create repo configuration
- `GET /api/stats` - Dashboard statistics

## Database Setup

If using local Supabase or need to run migrations:

```bash
# Install Supabase CLI
npm install -g supabase

# Init project
supabase init

# Link to your project
supabase link --project-ref your-project-id

# Run migrations
supabase db push
```

Or manually execute `supabase/migrations/00001_create_core_schema.sql` and
`supabase/migrations/00002_add_reddit_entry_status.sql` in your Supabase SQL editor.

## Environment Variables

See `.env.example` for all variables. Key ones:

```bash
DEMO_MODE=true  # Set to false for live mode
MIN_SCORE=2     # Minimum upvotes before processing
SCORE_REFRESH_SECONDS=600
ENABLE_PLAN_MD=true
ENABLE_PR_AUTOMATION=false
PLAN_MD_DIR=backend/artifacts/plans
PLAN_MD_PATH_TEMPLATE=docs/echofix_plans/{reddit_entry_id}.md

# Required for live mode:
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
GEMINI_API_KEY=...
GITHUB_TOKEN=...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
```

## Testing the Flow

### 1. Ingest Reddit Data
```bash
curl -X POST http://localhost:8000/api/reddit/ingest \\
  -H "Content-Type: application/json" \\
  -d '{
    "subreddits": ["webdev"],
    "keywords": ["bug", "issue"],
    "limit": 20
  }'
```

### 2. Refresh Scores (updates eligibility after upvotes)
```bash
curl -X POST http://localhost:8000/api/reddit/refresh-scores
```

### 2.5 Auto-process READY entries (plan + PR output)
```bash
curl -X POST http://localhost:8000/api/pipeline/auto-process-ready
```

### 3. Generate Insights
```bash
curl -X POST http://localhost:8000/api/insights/generate
```

### 4. Fetch Insights
```bash
curl http://localhost:8000/api/insights
```

### 5. Analyze with Gemini
```bash
curl -X POST http://localhost:8000/api/gemini/analyze/<insight-id>
```

### 6. Create GitHub Issue
```bash
curl -X POST http://localhost:8000/api/github/create-issue \\
  -H "Content-Type: application/json" \\
  -d '{"insight_id": "<insight-id>"}'
```

### Bonus: Run the live runner
```bash
python scripts/run_one_live.py https://reddit.com/r/webdev/comments/<thread_id>
```

## Architecture

```
┌─────────────────┐
│  Reddit Client  │  Collects posts/comments from subreddits
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Supabase DB   │  Stores reddit_entries, insights, logs
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Insight Engine  │  Groups entries into themes
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Gemini Client   │  Analyzes insights → IssueSpec (structured JSON)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GitHub Client   │  Creates issues/PRs via gh CLI
└─────────────────┘
```

## File Structure

```
backend/
├── app.py                 # Flask API server
├── models.py              # Pydantic models
├── db.py                  # Database operations
├── reddit_client.py       # Reddit ingestion
├── gemini_client.py       # Gemini integration
├── github_client.py       # GitHub operations
├── services/
│   └── insight_generator.py  # Local insight grouping
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── fixtures/              # Demo mode data
│   ├── reddit_search.json
│   └── reddit_rss_demo.json
└── supabase/
    └── migrations/        # Database schema
        └── 00001_create_core_schema.sql
```

## Logging

Logs are printed to console. In production, configure proper logging:

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('echofix.log'),
        logging.StreamHandler()
    ]
)
```

## Troubleshooting

**Import errors**:
- Ensure you're in the virtual environment
- Run `pip install -r requirements.txt` again

**Supabase connection errors**:
- Check `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
- Verify network connectivity
- Check Supabase dashboard for API status

**Reddit API errors**:
- Verify credentials in .env
- Check Reddit API rate limits
- Use DEMO_MODE=true to bypass

**Gemini API errors**:
- Check API key validity
- Verify quota/billing
- Use DEMO_MODE=true to bypass

**GitHub CLI errors**:
- Run `gh auth login` to authenticate
- Ensure `gh` is in PATH
- Use DEMO_MODE=true to bypass

## Production Deployment

For production:

1. Set `DEMO_MODE=false`
2. Use proper secrets management (not .env files)
3. Enable CORS properly for your frontend domain
4. Add rate limiting (flask-limiter)
5. Add authentication/authorization
6. Use production WSGI server (gunicorn):
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```
7. Set up monitoring and logging
8. Configure database connection pooling
9. Add health check endpoint monitoring

## Contributing

This is a hackathon project, but improvements welcome:
- Add tests (pytest)
- Add rate limiting
- Improve error handling
- Add caching layer
- Optimize database queries
