#!/bin/bash

# EchoFix Continuous Monitoring Script
# Monitors Reddit thread and auto-processes READY entries

API_URL="http://localhost:8000"
POLL_INTERVAL=60  # seconds

echo "🔄 EchoFix Continuous Monitoring"
echo "================================"
echo ""
echo "📍 Monitoring: https://www.reddit.com/r/Resume_Analyszer/comments/1qfzivr/userfeedback/"
echo "⏱️  Poll interval: ${POLL_INTERVAL}s"
echo "🎯 Auto-processing posts with 2+ upvotes"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""

# Counter for iterations
ITERATION=0

while true; do
  ITERATION=$((ITERATION + 1))
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "⏰ [$TIMESTAMP] Iteration #$ITERATION"
  echo ""

  # Step 1: Ingest latest comments from the thread
  echo "1️⃣  Fetching latest comments from thread..."
  INGEST_RESULT=$(curl -s -X POST "$API_URL/api/reddit/ingest-seed" 2>/dev/null)
  echo "$INGEST_RESULT" | jq -r '.message // .error // "Ingestion complete"'

  # Step 2: Refresh scores to check for new READY entries
  echo ""
  echo "2️⃣  Refreshing scores (checking for 2+ upvotes)..."
  REFRESH_RESULT=$(curl -s -X POST "$API_URL/api/reddit/refresh-scores" 2>/dev/null)
  READY_COUNT=$(echo "$REFRESH_RESULT" | jq -r '.ready_count // 0')
  echo "   → Found $READY_COUNT READY entries"

  # Step 3: Auto-process READY entries
  if [ "$READY_COUNT" -gt 0 ]; then
    echo ""
    echo "3️⃣  🚀 Processing $READY_COUNT READY entries..."
    PROCESS_RESULT=$(curl -s -X POST "$API_URL/api/pipeline/auto-process-ready" 2>/dev/null)
    echo "$PROCESS_RESULT" | jq -r '.message // .processed // "Processing complete"'

    # Show what was created
    PROCESSED=$(echo "$PROCESS_RESULT" | jq -r '.processed // 0')
    if [ "$PROCESSED" -gt 0 ]; then
      echo ""
      echo "   ✅ $PROCESSED entries processed!"
      echo "   📊 Check dashboard: http://localhost:3000"
    fi
  else
    echo "   ℹ️  No READY entries to process"
  fi

  # Step 4: Show current stats
  echo ""
  echo "4️⃣  Current Status:"
  STATS=$(curl -s "$API_URL/api/stats" 2>/dev/null)
  echo "$STATS" | jq -r '
    if .entries then
      "   Total Entries: \(.entries.total // 0)
   PENDING: \(.entries.pending // 0)
   READY: \(.entries.ready // 0)
   PROCESSING: \(.entries.processing // 0)
   PROCESSED: \(.entries.processed // 0)
   Insights: \(.insights.total // 0)"
    else
      "   Stats unavailable"
    end
  ' || echo "   Stats unavailable"

  echo ""
  echo "⏳ Next check in ${POLL_INTERVAL}s..."
  echo ""

  # Wait before next iteration
  sleep $POLL_INTERVAL
done
