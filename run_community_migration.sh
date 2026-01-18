#!/bin/bash

# Run the community approval migration via Supabase SQL editor
# You'll need to run this SQL manually in the Supabase dashboard

echo "Please run this SQL in your Supabase SQL Editor:"
echo "https://supabase.com/dashboard/project/bkjuzmdzbxffxpeluwsv/sql"
echo ""
echo "===== SQL TO RUN ====="
cat backend/supabase/migrations/00005_add_community_approval.sql
echo ""
echo "======================"
