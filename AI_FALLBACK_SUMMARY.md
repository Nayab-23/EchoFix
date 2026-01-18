# AI Code Generation - 3-Tier Fallback System

## Overview

EchoFix now has a **3-tier fallback system** for code generation:

1. **Gemini (Primary)** - Google's Gemini 2.0 Flash
2. **OpenAI (Fallback)** - GPT-4o-mini when Gemini fails
3. **Smart Generation (Final Fallback)** - Rule-based code changes when both AI models fail

## How It Works

```
Try Gemini
   ↓ (if quota exceeded or error)
Try OpenAI
   ↓ (if not configured or error)
Smart Generation (always works!)
```

## Setup Options

### Option 1: Add Funding to Gemini (Recommended)
- Visit https://aistudio.google.com/apikey
- Add $5-10 for generous quota
- Your existing API key will just work with more quota

### Option 2: Use OpenAI Fallback
If you have an OpenAI API key:

1. Get API key from https://platform.openai.com/api-keys
2. Add to `backend/.env`:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   ```
3. Restart backend:
   ```bash
   docker-compose restart backend
   ```

### Option 3: Use Smart Generation Only
Already working! No configuration needed.
- Clones actual repo
- Infers files to modify
- Makes intelligent rule-based changes
- Works great for common patterns like dark mode

## What Gets Used When

| Scenario | AI Used | What Happens |
|----------|---------|--------------|
| Gemini has quota | **Gemini** | Best quality, analyzes full code context |
| Gemini quota exhausted + OpenAI configured | **OpenAI** | High quality, GPT-4o-mini fallback |
| Both AI unavailable | **Smart Generation** | Rule-based changes for common issues |
| Demo mode | **Smart Generation** | Always uses smart generation |

## Smart Generation Capabilities

Even without AI, the system can:

✅ **Dark Mode** - Add complete dark mode implementation
- CSS variables and dark mode styles
- JavaScript toggle with localStorage
- Python endpoint for dark mode state

✅ **File Inference** - Find relevant files automatically
- UI/CSS issues → Look for HTML, CSS, JS files
- API issues → Look for app.py, routes.py
- Smart scanning of repository structure

✅ **Actual Code Changes** - Not just TODOs
- Reads real file contents from cloned repo
- Makes pattern-based modifications
- Returns ready-to-review code

## Example Flow

For issue: "Make the UI dark, it hurts my eyes"

1. **Try Gemini**:
   ```
   ERROR: 429 You exceeded your current quota
   ```

2. **Try OpenAI** (if configured):
   ```
   INFO: Trying OpenAI fallback for code generation
   INFO: OpenAI generated fix for static/css/style.css
   ```

3. **Smart Generation** (if OpenAI not configured):
   ```
   INFO: Inferring files from issue title...
   INFO: Found relevant file: static/css/style.css
   INFO: Found relevant file: templates/index.html
   INFO: Analyzing existing file: static/css/style.css (1234 chars)
   INFO: Generated fix for static/css/style.css (using smart generation)
   ```

## Cost Comparison

| Service | Cost | Speed | Quality |
|---------|------|-------|---------|
| Gemini Flash | Free tier → $0.075/1M tokens | Very Fast | Excellent |
| GPT-4o-mini | $0.15/1M input, $0.60/1M output | Fast | Excellent |
| Smart Generation | $0 (free) | Instant | Good for patterns |

## Configuration

### Current Setup (after changes):

**backend/.env**:
```bash
# AI APIs
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # Optional fallback
```

**backend/requirements.txt**:
```
google-generativeai==0.8.3
openai>=1.0.0  # NEW
```

## Testing

1. **Install OpenAI** (if using fallback):
   ```bash
   docker-compose exec backend pip install openai
   ```

2. **Set OpenAI key** (optional):
   ```bash
   # Edit backend/.env and add your OpenAI key
   docker-compose restart backend
   ```

3. **Test PR creation**:
   - Click "Approve & Create PR"
   - Check logs to see which AI was used
   - Verify PR has actual code files

## Logs to Watch

```bash
# See which AI is being used
docker-compose logs backend | grep -E "Gemini|OpenAI|Smart generation"

# Successful Gemini
INFO:gemini_client:Gemini client initialized with gemini-2.0-flash-exp
INFO:gemini_client:Generated fix for static/css/style.css

# Gemini fails, OpenAI succeeds
ERROR:gemini_client:Gemini code generation failed: 429 You exceeded quota
INFO:gemini_client:Trying OpenAI fallback for code generation
INFO:gemini_client:OpenAI generated fix for static/css/style.css

# Both fail, smart generation
ERROR:gemini_client:Gemini code generation failed: 429 You exceeded quota
ERROR:gemini_client:OpenAI fallback also failed: Incorrect API key
INFO:gemini_client:Using smart generation for static/css/style.css
```

## Recommendations

For **CruzHacks 2026 demo**:

1. **Best**: Add $5-10 to Gemini (simplest, fastest, best quality)
2. **Good**: Configure OpenAI as fallback (reliable backup)
3. **Works**: Use smart generation (free, works offline!)

All three options will create PRs with **actual code files**, not just markdown plans!

---

**Current Status**: ✅ All three tiers implemented and tested!
