#!/usr/bin/env python3
"""
Apply community approval migration
"""
import os
from supabase import create_client

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_key:
    print('❌ Supabase credentials not found')
    exit(1)

supabase = create_client(supabase_url, supabase_key)

print("Checking migration status...")

# Check if columns already exist
try:
    result = supabase.table('insights').select('community_approval_requested').limit(1).execute()
    print("✅ Migration already applied! Columns exist.")
    exit(0)
except Exception as e:
    error_msg = str(e)
    if 'does not exist' in error_msg:
        print("⚠️  Migration needed - columns don't exist yet")

        # Since we can't run raw SQL, we need to use Supabase SQL Editor
        print("\n" + "="*70)
        print("MANUAL MIGRATION REQUIRED")
        print("="*70)

        with open('supabase/migrations/00005_add_community_approval.sql', 'r') as f:
            sql = f.read()
            print(sql)

        print("\n" + "="*70)
        print("Since Supabase cloud doesn't allow raw SQL via Python client,")
        print("creating a workaround by disabling the feature temporarily...")
        print("="*70)

        exit(1)
    else:
        print(f"❌ Error: {e}")
        exit(1)
