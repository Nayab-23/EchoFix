#!/bin/bash
# Copy migration SQL to clipboard and open Supabase dashboard

echo "📋 Copying migration SQL to clipboard..."
cat backend/supabase/migrations/00005_add_community_approval.sql | pbcopy

echo "✅ Migration SQL copied to clipboard!"
echo ""
echo "📝 Next steps:"
echo "1. Opening Supabase SQL Editor in your browser..."
echo "2. The SQL is already in your clipboard - just paste (Cmd+V)"
echo "3. Click 'Run' to apply the migration"
echo ""
echo "Dashboard URL: https://supabase.com/dashboard/project/bkjuzmdzbxffxpeluwsv/sql"

# Open the SQL editor in browser
open "https://supabase.com/dashboard/project/bkjuzmdzbxffxpeluwsv/sql"

echo ""
echo "🔐 If login is required:"
echo "   - Ask your friend for the login credentials"
echo "   - Or have them apply the migration themselves"
echo ""
echo "Migration SQL (also in clipboard):"
echo "======================================"
cat backend/supabase/migrations/00005_add_community_approval.sql
