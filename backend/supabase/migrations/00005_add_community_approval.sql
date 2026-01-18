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
