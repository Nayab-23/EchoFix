-- Add status/score tracking fields for Reddit entries

ALTER TABLE reddit_entries
  ALTER COLUMN score DROP DEFAULT;

ALTER TABLE reddit_entries
  ADD COLUMN IF NOT EXISTS status TEXT CHECK (status IN (
    'pending',
    'ready',
    'processing',
    'processed',
    'failed',
    'skipped'
  )) DEFAULT 'pending';

ALTER TABLE reddit_entries
  ADD COLUMN IF NOT EXISTS last_score_check_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE reddit_entries
  ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE reddit_entries
  ADD COLUMN IF NOT EXISTS github_issue_url TEXT;

UPDATE reddit_entries
SET status = 'pending'
WHERE status IS NULL;

CREATE INDEX IF NOT EXISTS idx_reddit_entries_status ON reddit_entries(status);
CREATE INDEX IF NOT EXISTS idx_reddit_entries_github_issue_url ON reddit_entries(github_issue_url);
