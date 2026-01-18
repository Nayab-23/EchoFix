# EchoFix RSS Quick Reference (Legacy)

Note: EchoFix now defaults to Reddit JSON ingestion for upvote scores. RSS remains as a legacy option.

## 🚀 Quick Start Commands

### 1. Ingest a Specific Reddit Thread (Paste Any URL!)
```bash
curl -X POST http://localhost:8000/api/reddit/ingest-url \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://reddit.com/r/webdev/comments/1abc2d3/my_app_crashes",
    "max_items": 50
  }'
```

**Response:**
```json
{
  "success": true,
  "url": "https://reddit.com/r/webdev/comments/1abc2d3/my_app_crashes",
  "run_id": "uuid-here",
  "imported_count": 12,
  "entries": [...]
}
```

---

### 2. Ingest Pre-Configured Seed Threads
```bash
# First, set in backend/.env:
# REDDIT_SEED_THREAD_URLS=https://reddit.com/r/webdev/comments/...,https://...

curl -X POST http://localhost:8000/api/reddit/ingest-seed
```

**Response:**
```json
{
  "success": true,
  "threads_processed": 3,
  "total_imported": 45,
  "results": [
    {"url": "...", "success": true, "imported": 12},
    {"url": "...", "success": true, "imported": 18},
    {"url": "...", "success": true, "imported": 15}
  ]
}
```

---

### 3. Complete End-to-End Pipeline
```bash
# Step 1: Ingest
curl -X POST http://localhost:8000/api/reddit/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://reddit.com/r/programming/comments/xyz/perf_issues"}'

# Step 2: Refresh scores (RSS has no scores)
curl -X POST http://localhost:8000/api/reddit/refresh-scores

# Step 3: Generate insights (only READY entries are processed)
curl -X POST http://localhost:8000/api/insights/generate

# Step 4: Fetch Insights
curl http://localhost:8000/api/insights

# Step 5: Analyze with Gemini (get insight_id from step 4)
curl -X POST http://localhost:8000/api/gemini/analyze/<insight-id>

# Step 6: Create GitHub Issue
curl -X POST http://localhost:8000/api/github/create-issue \
  -H "Content-Type: application/json" \
  -d '{"insight_id": "<insight-id>"}'
```

---

## 🎛️ Configuration

### Environment Variables (backend/.env)
```bash
# Ingestion Mode
REDDIT_INGEST_MODE=rss_url  # rss_url (default), praw, or fixtures

# Seed URLs (comma-separated)
REDDIT_SEED_THREAD_URLS=https://reddit.com/r/webdev/comments/abc/...,https://...

# RSS Settings
REDDIT_USER_AGENT=EchoFix/1.0 CruzHacks2026
REDDIT_RSS_BASE_DOMAIN=old.reddit.com
REDDIT_RSS_TIMEOUT=10

# Score threshold gating
MIN_SCORE=2
SCORE_REFRESH_SECONDS=600

# Demo Mode (uses fixtures if true)
DEMO_MODE=false
```

---

## 🧪 Testing

### Run RSS Module Tests
```bash
cd backend
python test_rss.py
```

### Run Full Demo Pipeline
```bash
chmod +x test_demo.sh
./test_demo.sh
```

---

## 📋 Supported Reddit URL Formats

All of these work:
- `https://reddit.com/r/webdev/comments/1abc2d3/my_post`
- `https://www.reddit.com/r/webdev/comments/1abc2d3/my_post`
- `https://old.reddit.com/r/webdev/comments/1abc2d3/my_post`
- `https://np.reddit.com/r/webdev/comments/1abc2d3/my_post`
- `https://new.reddit.com/r/webdev/comments/1abc2d3/my_post`
- `https://redd.it/1abc2d3` (shortlinks)

---

## 🐛 Troubleshooting

### "No entries found or invalid URL"
- Check URL format (must be a Reddit thread URL)
- Try normalizing: use `https://old.reddit.com/r/.../comments/...`
- Verify network connectivity

### "No repository configured"
- Create a repo config first:
```bash
curl -X POST http://localhost:8000/api/repo-configs \
  -H "Content-Type: application/json" \
  -d '{
    "repo_owner": "your-org",
    "repo_name": "your-repo",
    "github_token": "ghp_..."
  }'
```

### Demo Mode Not Working
- Check `backend/fixtures/reddit_rss_demo.json` exists
- Verify `DEMO_MODE=true` in `.env`
- Look for fixture loading errors in logs

### Duplicate Entries
- Deduplication is automatic by `reddit_id`
- Re-running ingestion on the same URL will skip duplicates
- Check database for existing entries: `GET /api/reddit/entries`

---

## 🎯 Demo Tips

1. **Pre-load seed URLs** in `.env` for one-click demos
2. **Use real threads** with active discussions for impressive demos
3. **Show evidence links** in generated GitHub issues (judges love traceability)
4. **Highlight speed**: "From Reddit URL to GitHub issue in 30 seconds"
5. **Emphasize no OAuth**: "Works immediately, no API approval needed"

---

## 🔗 Related Documentation

- [README.md](../README.md) - Project overview
- [SETUP.md](../SETUP.md) - Complete setup guide
- [docs/DEMO.md](../docs/DEMO.md) - Judge demo script
- [RSS_IMPLEMENTATION.md](../RSS_IMPLEMENTATION.md) - Implementation details
- [workflows/README.md](../workflows/README.md) - n8n workflow setup
