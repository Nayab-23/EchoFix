# EchoFix Migration Plan

## Summary of Vector Architecture

**Vector** is an X (Twitter)-first feedback-to-PR pipeline with:
- **Backend (Flask)**: Grok embeddings, tweet clustering, plan generation, PR orchestration
- **Frontend (Next.js)**: Dashboard for viewing projects, approving plans
- **X API Integration**: Monitors mentions, DMs users, posts updates
- **Grok Integration**: Embeddings, clustering, code generation (Grok Fast Code)
- **Supabase**: PostgreSQL + pgvector for storing tweets, projects, plans, logs
- **Local Agent (coder.py)**: Watches for approved plans, creates sandbox, generates code, opens PRs
- **GitHub Integration**: Issue/PR creation via `gh` CLI

## EchoFix Architecture (Target)

**Reddit-first feedback pipeline with CruzHacks track alignment:**

1. **Reddit Ingestion** (replaces X API)
   - Monitor subreddits, keywords, product mentions
   - Collect posts/comments with metadata
   - Support live + demo modes

2. **Unwrap Integration** (insights engine)
   - GraphQL API client
   - Batch import Reddit entries
   - Fetch grouped insights/themes
   - Store entry-to-Reddit mapping

3. **Gemini Integration** (replaces Grok)
   - Classification, summarization, structured outputs
   - Multimodal support (images from Reddit)
   - Function calling for actionable outputs
   - Deterministic demo mode

4. **n8n Orchestration** (automation spine)
   - Scheduled ingestion workflows
   - Approval workflows
   - GitHub automation
   - Webhook triggers from dashboard

5. **Dashboard** (adapted from Vector)
   - Reddit ingestion status
   - Unwrap insights/themes
   - Issue specs with evidence
   - Approval buttons → n8n

6. **GitHub Actions** (adapted from Vector)
   - Issue creation
   - PR creation (optional)
   - Safe, approval-gated

## Migration Steps

### Phase 1: Project Structure Setup
- [x] Create MIGRATION.md
- [ ] Copy Vector baseline to EchoFix
- [ ] Rename branding (Vector → EchoFix)
- [ ] Update directory structure
- [ ] Create .env.example files

### Phase 2: Backend Core Migration
- [ ] Port db.py with schema updates (Reddit-focused)
- [ ] Port models.py and update types
- [ ] Create new Reddit client module
- [ ] Create Unwrap client module
- [ ] Create Gemini client module (replace grok.py)
- [ ] Update app.py with new endpoints
- [ ] Port sandbox.py and github_client.py
- [ ] Update requirements.txt

### Phase 3: Database Schema
- [ ] Create EchoFix migrations
- [ ] Reddit entries table (not tweets)
- [ ] Unwrap mappings table
- [ ] Projects → Insights table
- [ ] Plans → IssueSpecs table
- [ ] Add demo_mode flag to configs

### Phase 4: Reddit Integration
- [ ] Implement Reddit client (PRAW)
- [ ] Subreddit monitoring
- [ ] Keyword search
- [ ] Comment collection
- [ ] Deduplication logic
- [ ] Demo fixtures (JSON files)
- [ ] Demo mode switch

### Phase 5: Unwrap Integration
- [ ] Implement Unwrap GraphQL client
- [ ] Batch entry import
- [ ] Fetch entries/groups/taxonomy
- [ ] Store mappings
- [ ] Demo/mock mode
- [ ] Backend endpoints

### Phase 6: Gemini Integration
- [ ] Implement Gemini client
- [ ] Classification/summarization
- [ ] Structured outputs (IssueSpec, PatchPlan)
- [ ] Function calling
- [ ] Multimodal support
- [ ] Temperature/guardrails
- [ ] Demo mode with fixtures

### Phase 7: n8n Workflows
- [ ] Create /workflows directory
- [ ] Scheduled ingestion workflow
- [ ] Approval workflow
- [ ] GitHub automation workflow
- [ ] Webhook endpoints in backend
- [ ] Docker compose for n8n
- [ ] Setup documentation

### Phase 8: Frontend Migration
- [ ] Port Next.js dashboard
- [ ] Update branding/UI
- [ ] Reddit entries view
- [ ] Unwrap insights view
- [ ] Issue spec review
- [ ] Approval buttons
- [ ] n8n trigger integration
- [ ] Demo mode indicators

### Phase 9: Documentation
- [ ] Main README.md
- [ ] DEMO.md walkthrough
- [ ] .env.example files
- [ ] Architecture diagram
- [ ] Setup instructions
- [ ] Track alignment doc
- [ ] API documentation

### Phase 10: Testing & Demo Mode
- [ ] End-to-end demo flow
- [ ] Demo fixtures verification
- [ ] Error handling
- [ ] Mock switches
- [ ] Local run verification
- [ ] Documentation review

## Key Differences from Vector

1. **Data Source**: Reddit API (PRAW) instead of X API
2. **Insights Engine**: Unwrap GraphQL instead of internal clustering
3. **LLM**: Gemini (Google) instead of Grok (xAI)
4. **Orchestration**: n8n front-and-center instead of background agent
5. **Focus**: CruzHacks tracks (Unwrap prize, n8n automation, Gemini reasoning)
6. **Demo Mode**: Comprehensive fallback for all external APIs

## Environment Variables Needed

### Backend
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`
- `UNWRAP_ACCESS_KEY`
- `GEMINI_API_KEY`
- `GITHUB_TOKEN`
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- `DEMO_MODE=true/false`

### n8n
- `N8N_ENCRYPTION_KEY`
- `N8N_WEBHOOK_BASE_URL`
- `ECHOFIX_BACKEND_URL`

### Frontend
- `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_API_BASE_URL`

## Success Criteria
- ✅ Demo mode runs end-to-end without external API keys
- ✅ Live mode works with proper credentials
- ✅ n8n workflows importable and functional
- ✅ Dashboard shows Reddit → Unwrap → Gemini → GitHub flow
- ✅ Documentation clear for judges/teammates
- ✅ Clear CruzHacks track alignment
