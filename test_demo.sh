#!/bin/bash

# EchoFix Demo Test Script
# Tests the complete pipeline in demo mode

set -e  # Exit on error

echo "🎯 EchoFix Demo Test Script"
echo "=============================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"

# Check if backend is running
echo -e "${BLUE}Checking if backend is running...${NC}"
if ! curl -s "$BASE_URL/health" > /dev/null; then
    echo -e "${YELLOW}Backend not running. Please start it first:${NC}"
    echo "  cd backend && python app.py"
    exit 1
fi

echo -e "${GREEN}✓ Backend is running${NC}"
echo ""

# Step 1: Health Check
echo -e "${BLUE}Step 1: Health Check${NC}"
curl -s "$BASE_URL/health" | jq '.'
echo ""

# Step 2: Ingest Reddit Data (JSON mode)
echo -e "${BLUE}Step 2: Ingest Reddit Thread via JSON${NC}"
echo "Using demo mode or test URL..."

# Try JSON ingestion first (works without credentials)
INGEST_RESULT=$(curl -s -X POST "$BASE_URL/api/reddit/ingest-url" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://reddit.com/r/webdev/comments/test123/demo_thread",
    "max_items": 20
  }')

# Check if JSON worked, otherwise fallback to seed or legacy
if echo "$INGEST_RESULT" | jq -e '.success' > /dev/null 2>&1; then
    echo "$INGEST_RESULT" | jq '.success, .imported_count'
    ENTRIES_NEW=$(echo "$INGEST_RESULT" | jq -r '.imported_count')
    echo -e "${GREEN}✓ Ingested $ENTRIES_NEW entries via RSS${NC}"
else
    echo -e "${YELLOW}JSON failed, trying seed ingestion...${NC}"
    INGEST_RESULT=$(curl -s -X POST "$BASE_URL/api/reddit/ingest-seed" || \
                    curl -s -X POST "$BASE_URL/api/reddit/ingest" -H "Content-Type: application/json" \
                    -d '{"subreddits": ["webdev"], "keywords": ["bug"], "limit": 20}')
    
    if echo "$INGEST_RESULT" | jq -e '.success' > /dev/null 2>&1; then
        ENTRIES_NEW=$(echo "$INGEST_RESULT" | jq -r '.total_imported // .entries_new')
        echo -e "${GREEN}✓ Ingested $ENTRIES_NEW entries${NC}"
    else
        echo -e "${YELLOW}⚠ Ingestion failed - check DEMO_MODE or fixtures${NC}"
    fi
fi
echo ""

# Step 3: Refresh Scores (threshold gating)
echo -e "${BLUE}Step 3: Refresh Scores${NC}"
REFRESH_RESULT=$(curl -s -X POST "$BASE_URL/api/reddit/refresh-scores")
echo "$REFRESH_RESULT" | jq '.success, .pending_checked, .ready, .skipped_recent'
echo -e "${GREEN}✓ Refreshed scores for $(echo $REFRESH_RESULT | jq -r '.pending_checked') entries${NC}"
echo ""

# Step 4: Generate Insights
echo -e "${BLUE}Step 4: Generate Insights${NC}"
IMPORT_RESULT=$(curl -s -X POST "$BASE_URL/api/insights/generate")
echo "$IMPORT_RESULT" | jq '.success, .entries_processed, .insights_created, .insights_updated'
echo -e "${GREEN}✓ Processed $(echo $IMPORT_RESULT | jq -r '.entries_processed') entries into insights${NC}"
echo ""

# Step 5: Fetch Insights
echo -e "${BLUE}Step 5: Fetch Insights${NC}"
INSIGHTS_RESULT=$(curl -s "$BASE_URL/api/insights")
echo "$INSIGHTS_RESULT" | jq '.count'
echo ""

# Extract first insight ID
FIRST_INSIGHT_ID=$(echo "$INSIGHTS_RESULT" | jq -r '.insights[0].id')
FIRST_INSIGHT_THEME=$(echo "$INSIGHTS_RESULT" | jq -r '.insights[0].theme')

if [ "$FIRST_INSIGHT_ID" != "null" ]; then
    echo -e "${GREEN}✓ Found insight: \"$FIRST_INSIGHT_THEME\" (ID: $FIRST_INSIGHT_ID)${NC}"
    echo ""
    
    # Step 6: Analyze with Gemini
    echo -e "${BLUE}Step 6: Analyze Insight with Gemini${NC}"
    ANALYSIS_RESULT=$(curl -s -X POST "$BASE_URL/api/gemini/analyze/$FIRST_INSIGHT_ID")
    
    if echo "$ANALYSIS_RESULT" | jq -e '.success' > /dev/null; then
        echo "$ANALYSIS_RESULT" | jq '.issue_spec.title, .issue_spec.priority'
        echo -e "${GREEN}✓ Generated issue spec with Gemini${NC}"
        echo ""
        
        # Step 7: Create GitHub Issue (demo mode)
        echo -e "${BLUE}Step 7: Create GitHub Issue${NC}"
        GITHUB_RESULT=$(curl -s -X POST "$BASE_URL/api/github/create-issue" \
          -H "Content-Type: application/json" \
          -d "{\"insight_id\": \"$FIRST_INSIGHT_ID\"}")
        
        if echo "$GITHUB_RESULT" | jq -e '.success' > /dev/null; then
            ISSUE_URL=$(echo "$GITHUB_RESULT" | jq -r '.issue_url')
            ISSUE_NUMBER=$(echo "$GITHUB_RESULT" | jq -r '.issue_number')
            echo -e "${GREEN}✓ Created GitHub issue #$ISSUE_NUMBER${NC}"
            echo -e "  URL: $ISSUE_URL"
        else
            echo -e "${YELLOW}⚠ GitHub issue creation failed (check if in demo mode)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Gemini analysis failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠ No insights found${NC}"
fi

echo ""
echo "=============================="
echo -e "${GREEN}✓ Demo test completed!${NC}"
echo ""
echo "Next steps:"
echo "  • View all insights: curl $BASE_URL/api/insights | jq"
echo "  • Get statistics: curl $BASE_URL/api/stats | jq"
echo "  • Open n8n: http://localhost:5678 (if running)"
echo ""
