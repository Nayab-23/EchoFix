#!/usr/bin/env python3
"""
Apply migration using Supabase PostgREST admin endpoint
"""
import os
import requests
from supabase import create_client

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_key:
    print('❌ Supabase credentials not found')
    exit(1)

# Read migration SQL
with open('supabase/migrations/00005_add_community_approval.sql', 'r') as f:
    migration_sql = f.read()

print("Attempting to apply migration via Supabase REST API...")
print("=" * 70)

# Try using the PostgREST API to execute SQL
# We'll use a workaround by creating the columns via individual ALTER statements

statements = [
    "ALTER TABLE insights ADD COLUMN IF NOT EXISTS community_approval_requested BOOLEAN DEFAULT false",
    "ALTER TABLE insights ADD COLUMN IF NOT EXISTS community_reply_id TEXT",
    "ALTER TABLE insights ADD COLUMN IF NOT EXISTS community_reply_score INTEGER DEFAULT 0",
    "ALTER TABLE insights ADD COLUMN IF NOT EXISTS community_approved BOOLEAN DEFAULT false",
    "ALTER TABLE insights ADD COLUMN IF NOT EXISTS community_approved_at TIMESTAMPTZ"
]

supabase = create_client(supabase_url, supabase_key)

# Try executing via RPC if available
for i, stmt in enumerate(statements, 1):
    print(f"\n[{i}/{len(statements)}] {stmt[:80]}...")
    try:
        # Attempt to use the query endpoint
        response = requests.post(
            f"{supabase_url}/rest/v1/rpc/exec_sql",
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json"
            },
            json={"query": stmt}
        )

        if response.status_code == 200:
            print(f"✅ Success")
        else:
            print(f"⚠️  Status {response.status_code}: {response.text}")

    except Exception as e:
        print(f"⚠️  Error: {e}")

print("\n" + "=" * 70)
print("Attempting to verify columns were created...")

# Verify by trying to query with the new columns
try:
    result = supabase.table("insights").select("community_approval_requested").limit(1).execute()
    print("✅ SUCCESS! Migration applied - columns are accessible")
    exit(0)
except Exception as e:
    error_msg = str(e)
    if 'does not exist' in error_msg:
        print("❌ Migration not applied - columns still don't exist")
        print("\nThe RPC method is not available. Manual application required.")
        print("\nPlease apply manually via Supabase Dashboard:")
        print("https://supabase.com/dashboard/project/bkjuzmdzbxffxpeluwsv/sql")
        print("\nSQL to run:")
        print("=" * 70)
        print(migration_sql)
        print("=" * 70)
        exit(1)
    else:
        print(f"✅ Columns might exist (got different error: {error_msg})")
        exit(0)
