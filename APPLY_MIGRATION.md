# Apply Community Approval Migration

The community approval feature is now fully implemented in the backend and frontend, but the database migration needs to be applied manually.

## Quick Fix

Run this SQL in your Supabase SQL Editor:
https://supabase.com/dashboard/project/bkjuzmdzbxffxpeluwsv/sql

```sql
-- Add community approval fields to insights table
ALTER TABLE insights
  ADD COLUMN IF NOT EXISTS community_approval_requested BOOLEAN DEFAULT false,
  ADD COLUMN IF NOT EXISTS community_reply_id TEXT,
  ADD COLUMN IF NOT EXISTS community_reply_score INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS community_approved BOOLEAN DEFAULT false,
  ADD COLUMN IF NOT EXISTS community_approved_at TIMESTAMPTZ;

-- Add index for querying community approvals
CREATE INDEX IF NOT EXISTS idx_insights_community_approval
  ON insights(community_approval_requested, community_approved);

COMMENT ON COLUMN insights.community_approval_requested IS 'Whether community approval was requested via Reddit reply';
COMMENT ON COLUMN insights.community_reply_id IS 'Reddit comment ID of the community approval request';
COMMENT ON COLUMN insights.community_reply_score IS 'Current upvote score of the community approval reply';
COMMENT ON COLUMN insights.community_approved IS 'Whether the community has approved (reply reached MIN_SCORE)';
COMMENT ON COLUMN insights.community_approved_at IS 'Timestamp when community approval was achieved';
```

## What This Enables

Once applied, the community approval feature will:

1. ✅ Track when you request community approval
2. ✅ Store the Reddit reply ID where you asked for approval
3. ✅ Monitor upvotes on that reply automatically (every 15 seconds)
4. ✅ Auto-merge the PR when the reply reaches MIN_SCORE (1 upvote in demo mode)

## Current Status (Without Migration)

The system is designed to work gracefully without the migration:

- ✅ "Ask Community" button appears in the UI
- ✅ Button will post Reddit comment successfully
- ⚠️ Vote tracking and auto-merge won't work until migration is applied
- ⚠️ Auto-process will skip community approval checks (no errors)

## How to Apply

1. Go to Supabase Dashboard: https://supabase.com/dashboard/project/bkjuzmdzbxffxpeluwsv/sql
2. Copy the SQL above
3. Paste it into the SQL Editor
4. Click "Run" or press Cmd+Enter
5. Verify it ran successfully (should see "Success" message)
6. Restart the backend: `docker-compose restart backend`

Done! The feature will now work end-to-end.
