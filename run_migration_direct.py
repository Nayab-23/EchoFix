#!/usr/bin/env python3
"""
Apply Supabase migration directly via REST API
"""
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

load_dotenv()

from supabase import create_client

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_key:
    print('❌ Supabase credentials not found')
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

print("Applying migration: 00005_add_community_approval.sql")
print("=" * 60)

# Check if columns already exist
try:
    result = supabase.table('insights').select('community_approval_requested').limit(1).execute()
    print("✅ Columns already exist! Migration was previously applied.")
    sys.exit(0)
except Exception as e:
    error_msg = str(e)
    if 'community_approval_requested' in error_msg and 'does not exist' in error_msg:
        print("⚠️  Columns don't exist yet. Need to apply migration.")
        print("\nSince we can't execute raw SQL via Python client, please run this SQL manually:")
        print("\n" + "=" * 60)

        with open('backend/supabase/migrations/00005_add_community_approval.sql', 'r') as f:
            print(f.read())

        print("=" * 60)
        print("\nTo apply manually:")
        print("1. Go to: https://supabase.com/dashboard/project/bkjuzmdzbxffxpeluwsv/sql")
        print("2. Copy/paste the SQL above")
        print("3. Click 'Run'")

        sys.exit(1)
    else:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
