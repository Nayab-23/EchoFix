#!/bin/bash
KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJranV6bWR6YnhmZnhwZWx1d3N2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODY1NjQxNSwiZXhwIjoyMDg0MjMyNDE1fQ.2SXDiiDO_t9xQ_Ootq0apK52FZ0QNH8ehjsL17juED8'

curl -s "https://bkjuzmdzbxffxpeluwsv.supabase.co/rest/v1/repo_configs?select=*" \
  -H "apikey: $KEY" \
  -H "Authorization: Bearer $KEY" | python3 -m json.tool
