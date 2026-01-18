# 🗄️ Run Supabase Migrations (5 minutes)

## Quick Steps

### 1. Open SQL Editor

Go to: https://supabase.com/dashboard/project/bkjuzmdzbxffxpeluwsv/sql/new

### 2. Run Migration 1 - Core Schema

1. Click **"+ New query"**
2. Copy the **entire contents** of this file:
   ```
   backend/supabase/migrations/00001_create_core_schema.sql
   ```
3. Paste into the SQL editor
4. Click **"Run"** (or press Cmd/Ctrl + Enter)
5. ✅ Should show "Success. No rows returned"

### 3. Run Migration 2 - Add Status Column

1. Click **"+ New query"** again
2. Copy contents of:
   ```
   backend/supabase/migrations/00002_add_reddit_entry_status.sql
   ```
3. Paste and click **"Run"**
4. ✅ Success

### 4. Run Migration 3 - Add Plan/PR Columns

1. Click **"+ New query"** again
2. Copy contents of:
   ```
   backend/supabase/migrations/00003_add_plan_and_pr_columns.sql
   ```
3. Paste and click **"Run"**
4. ✅ Success

### 5. Verify Tables Created

In the left sidebar, click **"Table Editor"**

You should see these tables:
- ✅ repo_configs
- ✅ reddit_entries
- ✅ insights

## After Migrations Complete

Restart the backend to connect to Supabase:

```bash
./restart.sh
```

Test the connection:

```bash
curl http://localhost:8000/health
```

Should show:
```json
{
  "status": "healthy",
  "services": {
    "supabase": true
  }
}
```

## Done! 🎉

Your database is now set up and EchoFix can store Reddit entries!

Try ingesting data:

```bash
curl -X POST http://localhost:8000/api/reddit/ingest-seed
```

Check the dashboard:

```bash
open http://localhost:3000
```
