#!/bin/bash

# EchoFix Demo Setup Script
# Sets up monitoring for Resume_Analyzer feedback thread

set -e

API_URL="http://localhost:8000"

echo "🎯 EchoFix Demo Setup"
echo "===================="
echo ""
echo "📍 Target Thread: https://www.reddit.com/r/Resume_Analyszer/comments/1qfzivr/userfeedback/"
echo "📦 Target Repo: https://github.com/Nayab-23/Resume_Analyzer.git"
echo "⚡ Score Threshold: 2 upvotes"
echo ""

# Step 1: Create repo config
echo "1️⃣  Creating repository configuration..."
curl -X POST "$API_URL/api/repos/config" \
  -H "Content-Type: application/json" \
  -d '{
    "github_owner": "Nayab-23",
    "github_repo": "Resume_Analyzer",
    "github_branch": "main",
    "subreddits": ["Resume_Analyszer"],
    "keywords": ["bug", "feature", "issue", "problem", "suggestion", "improve"],
    "product_names": ["Resume Analyzer"],
    "auto_create_issues": true,
    "auto_create_prs": false,
    "require_approval": false
  }' 2>/dev/null | jq . || echo "⚠️  Repo config may already exist"

echo ""

# Step 2: Ingest the seed thread
echo "2️⃣  Ingesting feedback thread and all comments..."
curl -X POST "$API_URL/api/reddit/ingest-seed" 2>/dev/null | jq .

echo ""

# Step 3: Refresh scores to see which are READY
echo "3️⃣  Checking scores (will mark posts with 2+ upvotes as READY)..."
sleep 2
curl -X POST "$API_URL/api/reddit/refresh-scores" 2>/dev/null | jq .

echo ""

# Step 4: Get current stats
echo "4️⃣  Current pipeline status:"
curl -s "$API_URL/api/stats" 2>/dev/null | jq .

echo ""
echo "✅ Demo setup complete!"
echo ""
echo "📊 View Dashboard: http://localhost:3000"
echo "🔄 n8n Workflows: http://localhost:5678"
echo ""
echo "🔄 To start continuous monitoring, run:"
echo "   ./start_monitoring.sh"
echo ""
