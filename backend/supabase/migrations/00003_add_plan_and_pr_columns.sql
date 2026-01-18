-- Add plan metadata to Reddit entries

ALTER TABLE reddit_entries
  ADD COLUMN IF NOT EXISTS plan_md_path TEXT;

ALTER TABLE reddit_entries
  ADD COLUMN IF NOT EXISTS plan_md_sha TEXT;

ALTER TABLE reddit_entries
  ADD COLUMN IF NOT EXISTS github_pr_url TEXT;

ALTER TABLE reddit_entries
  ADD COLUMN IF NOT EXISTS github_pr_number INTEGER;

CREATE INDEX IF NOT EXISTS idx_reddit_entries_plan_md_path ON reddit_entries(plan_md_path);
CREATE INDEX IF NOT EXISTS idx_reddit_entries_github_pr_url ON reddit_entries(github_pr_url);
