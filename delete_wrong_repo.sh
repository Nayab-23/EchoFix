#!/bin/bash
KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJranV6bWR6YnhmZnhwZWx1d3N2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODY1NjQxNSwiZXhwIjoyMDg0MjMyNDE1fQ.2SXDiiDO_t9xQ_Ootq0apK52FZ0QNH8ehjsL17juED8'

echo "Deleting EchoFix repo config..."
curl -X DELETE "https://bkjuzmdzbxffxpeluwsv.supabase.co/rest/v1/repo_configs?id=eq.bfcde0e5-2142-4508-be18-268480639d1b" \
  -H "apikey: $KEY" \
  -H "Authorization: Bearer $KEY"

echo ""
echo "Done! Only Resume_Analyzer repo config remains."
