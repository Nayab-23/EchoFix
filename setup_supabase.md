# Supabase Setup for EchoFix

## Step 1: Get Service Role Key

1. Go to: https://supabase.com/dashboard/project/bkjuzmdzbxffxpeluwsv/settings/api
2. Scroll to **Project API keys**
3. Copy the **`service_role` (secret)** key
4. Update `backend/.env` line 46:
   ```bash
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (paste your key here)
   ```

## Step 2: Run Database Migrations

1. Go to: https://supabase.com/dashboard/project/bkjuzmdzbxffxpeluwsv/editor
2. Click **SQL Editor** (left sidebar)
3. Click **+ New query**
4. Copy and paste the contents of each migration file:

### Migration 1: Core Schema

Copy entire contents of: `backend/supabase/migrations/00001_create_core_schema.sql`
Paste into SQL Editor and click **Run**

### Migration 2: Add Status

Copy entire contents of: `backend/supabase/migrations/00002_add_reddit_entry_status.sql`
Paste into SQL Editor and click **Run**

### Migration 3: Add Plan/PR Columns

Copy entire contents of: `backend/supabase/migrations/00003_add_plan_and_pr_columns.sql`
Paste into SQL Editor and click **Run**

## Step 3: Restart Backend

```bash
./restart.sh
```

## Done!

Your backend should now connect to Supabase successfully.

Test it:
```bash
curl http://localhost:8000/health
```

Should show: `"supabase": true`
