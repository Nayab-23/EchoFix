#!/bin/bash

# Update repo config to point to the correct test repository

SUPABASE_URL="https://bkjuzmdzbxffxpeluwsv.supabase.co"
SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJranV6bWR6YnhmZnhwZWx1d3N2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODY1NjQxNSwiZXhwIjoyMDg0MjMyNDE1fQ.2SXDiiDO_t9xQ_Ootq0apK52FZ0QNH8ehjsL17juED8"

echo "Updating repo config to Nayab-23/Resume_Analyzer..."

# Update the repo config
curl -X PATCH "${SUPABASE_URL}/rest/v1/repo_configs?id=neq.00000000-0000-0000-0000-000000000000" \
  -H "apikey: ${SERVICE_ROLE_KEY}" \
  -H "Authorization: Bearer ${SERVICE_ROLE_KEY}" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=representation" \
  -d '{
    "github_owner": "Nayab-23",
    "github_repo": "Resume_Analyzer",
    "github_branch": "main"
  }'

echo ""
echo "Done! Repo config updated."
