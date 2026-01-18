#!/bin/bash

# Run Supabase Migrations
# This script applies all database migrations to your Supabase instance

set -e

SUPABASE_URL="https://bkjuzmdzbxffxpeluwsv.supabase.co"
SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJranV6bWR6YnhmZnhwZWx1d3N2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODY1NjQxNSwiZXhwIjoyMDg0MjMyNDE1fQ.2SXDiiDO_t9xQ_Ootq0apK52FZ0QNH8ehjsL17juED8"

echo "🗄️  Running EchoFix Database Migrations"
echo "======================================"
echo ""

# Function to run SQL file
run_migration() {
    local file=$1
    local name=$(basename "$file")

    echo "📝 Running: $name"

    # Read the SQL file and send to Supabase
    RESPONSE=$(curl -s -X POST \
        "${SUPABASE_URL}/rest/v1/rpc/exec_sql" \
        -H "apikey: ${SERVICE_ROLE_KEY}" \
        -H "Authorization: Bearer ${SERVICE_ROLE_KEY}" \
        -H "Content-Type: application/json" \
        -d "{\"query\": $(cat "$file" | jq -Rs .)}")

    if echo "$RESPONSE" | grep -q "error"; then
        echo "❌ Error running $name"
        echo "$RESPONSE"
    else
        echo "✅ $name completed"
    fi
    echo ""
}

# Check if migrations directory exists
if [ ! -d "backend/supabase/migrations" ]; then
    echo "❌ Error: backend/supabase/migrations directory not found"
    exit 1
fi

# Run migrations in order
echo "Running migrations..."
echo ""

for migration in backend/supabase/migrations/*.sql; do
    run_migration "$migration"
done

echo ""
echo "✅ All migrations completed!"
echo ""
echo "🔄 Now restart the backend:"
echo "   ./restart.sh"
echo ""
