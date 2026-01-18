# EchoFix Demo Script for Judges (2-3 minutes)

**Tagline**: Reddit feedback → local insights → Gemini reasoning → n8n automation → GitHub issues

## The Problem

Developers get scattered feedback across Reddit threads. It's:
- **Noisy**: Hundreds of posts/comments to sift through
- **Unstructured**: "It's broken" isn't actionable
- **Manual**: Copy-pasting into GitHub issues wastes hours
- **Disconnected**: No loop-back to users who gave feedback

## Our Solution: EchoFix

A **Reddit-first feedback-to-shipping pipeline** that automatically:
1. Collects feedback from Reddit threads (no OAuth required!)
2. Groups feedback into themes with a local insight engine
3. Uses **Gemini** to convert insights into structured issue specs
4. Uses **n8n** to orchestrate approval and GitHub automation

---

## Demo Flow (Live or Recorded)

### Setup (show briefly)
"We can ingest any Reddit thread instantly—just paste the URL. No API approval needed!"

**Show**: Architecture diagram (30 seconds)

---

### Step 1: Reddit Ingestion via JSON (15 seconds)

**Show terminal**:
```bash
# Paste any Reddit thread URL - works immediately!
curl -X POST http://localhost:8000/api/reddit/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://reddit.com/r/webdev/comments/1abc2d3/my_app_crashes"}'
```

**Explain**:
"We just ingested this Reddit thread via JSON—no OAuth, no waiting for API approval. EchoFix collected the post and 15 top comments..."

**Show**: JSON response with Reddit entries

**Highlight**:
- Post Title: "My app keeps crashing when users upload large files"
- Top Comment: "You need to increase MAX_CONTENT_LENGTH..."
- Score: 42 upvotes
- Evidence links preserved

**CruzHacks Connection**: "Perfect for hackathons—start demoing in 5 minutes, not 5 days waiting for API approval."

---

### Step 2: Insight Generation (20 seconds)

**Show terminal**:
```bash
curl -X POST http://localhost:8000/api/reddit/refresh-scores
curl -X POST http://localhost:8000/api/insights/generate
curl http://localhost:8000/api/insights
```

**Explain**:
"EchoFix refreshes scores to capture new upvotes and groups READY entries into 3 themes..."

**Show**: Insights response

**Highlight**:
- **Theme 1**: "File Upload Issues" (15 entries, rising trend)
- **Theme 2**: "Dark Mode Requests" (42 entries, stable)
- **Theme 3**: "API Performance" (8 entries)

**CruzHacks Connection**: "This is where the local insight engine turns noise into signal."

---

### Step 3: Gemini Analysis (25 seconds)

**Show terminal**:
```bash
curl -X POST http://localhost:8000/api/gemini/analyze/<insight-id>
```

**Explain**:
"Gemini takes the 'File Upload Issues' insight and generates a structured GitHub issue spec..."

**Show**: Gemini response (IssueSpec)

**Highlight** (split screen: raw insight vs structured output):
- **Title**: "Fix file upload crashes for files >50MB"
- **Problem Statement**: Clear technical description citing Flask MAX_CONTENT_LENGTH
- **Steps to Reproduce**: 4-step process
- **Acceptance Criteria**: 3 testable conditions
- **Labels**: ["bug", "file-upload", "high-priority"]
- **Priority**: HIGH
- **Evidence**: Links to Reddit thread & top comments

**CruzHacks Connection**: "Gemini's structured outputs make this production-ready. No human editing needed."

---

### Step 4: n8n Orchestration (30 seconds)

**Show**: n8n UI (workflow canvas)

**Explain**:
"n8n orchestrates the entire flow. Here are two workflows running..."

**Show Workflow 1: Scheduled Ingestion** (quick pan):
- Cron trigger (every 6 hours)
- → Ingest Reddit
- → Generate insights

**Show Workflow 2: Approval to GitHub** (focus here):
- Webhook trigger (from dashboard)
- → Check if approved
- → Analyze with Gemini
- → Create GitHub issue
- → Log success

**Demo**: Click "Test workflow" → show execution log → show success

**CruzHacks Connection**: "n8n makes everything observable and repeatable. This is the automation spine."

---

### Step 5: GitHub Issue Created (20 seconds)

**Show**: GitHub repository

**Explain**:
"When a human approves in the dashboard, n8n triggers the pipeline..."

**Show**: 
1. New issue #127 just created
2. Click on issue to show:
   - Title matches Gemini output
   - Body has problem statement, acceptance criteria
   - Labels applied automatically
   - **Evidence section** with links to all 15 Reddit threads

**Highlight**: "Users who gave feedback can see their issue was heard."

---

### Step 6: Dashboard (20 seconds)

**Show**: EchoFix dashboard (quick tour)

**Sections**:
1. **Recent Reddit Activity**: 47 entries today
2. **Insights**: 3 themes identified
   - Authentication Issues (Priority: HIGH, 🔴 Rising)
   - Dark Mode Requests (Priority: MEDIUM)
3. **Insight Detail View**:
   - Evidence: Links to Reddit threads
   - Gemini-generated IssueSpec
   - **Approve** button → triggers n8n workflow
4. **Activity Log**: Shows GitHub issue #127 created

**Explain**: "Judges can test this themselves—everything runs in demo mode without API keys."

---

### Demo Mode (10 seconds)

**Show terminal**:
```bash
DEMO_MODE=true python app.py
```

**Explain**:
"Set DEMO_MODE=true and the entire pipeline runs end-to-end with fixtures. No Reddit/Gemini credentials needed. Perfect for testing or judging."

---

## CruzHacks Track Alignment Summary (10 seconds)

**n8n Track**:
- Two production workflows (scheduled + approval)
- Orchestrates entire pipeline
- Webhooks, HTTP requests, conditional logic

**Gemini Track**:
- Structured outputs (IssueSpec with strict JSON schema)
- Multimodal analysis (processes Reddit images/screenshots)
- Reasoning over unstructured feedback

---

## Closing (5 seconds)

"EchoFix proves that with the right tools—local insights, Gemini for reasoning, and n8n for automation—we can close the feedback loop at scale."

**Call to action**: "Try it yourself: github.com/[your-username]/EchoFix"

---

## Backup Slides (if needed)

### Live Demo Fails?
Show pre-recorded screen recording (3 minutes max).

### Questions?
- **"How does deduplication work?"**: Reddit ID check before inserting.
- **"What about spam?"**: Gemini can filter, or add moderation step in n8n.
- **"Can it handle other platforms?"**: Yes! Just swap Reddit client for Twitter/HackerNews/etc.
- **"What about security?"**: No auto-merge; always requires approval; sandbox for code changes.

---

## Judging Criteria - How We Excel

### Innovation
- First Reddit-to-GitHub pipeline with full AI orchestration
- Demo mode for reproducibility

### Technical Complexity
- 3 API integrations (Reddit, Gemini, GitHub)
- n8n workflow orchestration
- Supabase backend with JSONB storage for flexible schemas

### Usefulness
- Solves real problem for indie devs and open-source maintainers
- Reduces feedback triage time by 90%

### Track Alignment
- **n8n**: Visible in every step of automation
- **Gemini**: Powers all reasoning and structured outputs

### Presentation
- Clear 3-minute flow
- Live demo + demo mode fallback
- Visual architecture diagram

---

## Demo Checklist

- [ ] Backend running (`python app.py`)
- [ ] n8n running (`docker-compose up`)
- [ ] Demo fixtures loaded
- [ ] GitHub repo visible in browser
- [ ] n8n workflows imported and active
- [ ] Dashboard accessible
- [ ] Terminal ready for curl commands
- [ ] Architecture diagram open
- [ ] Pre-recorded video as backup

---

**Total Time**: 2-3 minutes
**Tone**: Confident, technical, judge-friendly
**Energy**: High but controlled—let the demo speak
