-- EchoFix Database Schema
-- Reddit-first feedback pipeline with local insights and Gemini integration

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search

-- =====================================================
-- TABLE: repo_configs
-- Repository configurations for monitoring
-- =====================================================
CREATE TABLE repo_configs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,

  -- Repository details
  github_owner TEXT NOT NULL,
  github_repo TEXT NOT NULL,
  github_branch TEXT DEFAULT 'main' NOT NULL,

  -- Reddit monitoring
  subreddits TEXT[] DEFAULT '{}', -- e.g., ['webdev', 'programming']
  keywords TEXT[] DEFAULT '{}', -- Keywords to search
  product_names TEXT[] DEFAULT '{}', -- Product names to track

  -- Automation settings
  auto_create_issues BOOLEAN DEFAULT false,
  auto_create_prs BOOLEAN DEFAULT false,
  require_approval BOOLEAN DEFAULT true,

  -- User who configured this repo
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,

  UNIQUE(github_owner, github_repo)
);

-- =====================================================
-- TABLE: reddit_entries
-- Reddit posts and comments collected
-- =====================================================
CREATE TABLE reddit_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,

  -- Reddit metadata
  reddit_id TEXT UNIQUE NOT NULL,
  reddit_type TEXT CHECK (reddit_type IN ('post', 'comment')) NOT NULL,
  title TEXT,
  body TEXT NOT NULL,
  author TEXT NOT NULL,
  subreddit TEXT NOT NULL,
  permalink TEXT NOT NULL,

  -- Engagement metrics
  score INTEGER DEFAULT 0,
  num_comments INTEGER DEFAULT 0,

  -- Media
  image_urls TEXT[] DEFAULT '{}',
  video_url TEXT,

  -- Processing status
  processed BOOLEAN DEFAULT false,
  unwrap_entry_id TEXT, -- Legacy external insight entry ID (unused)
  insight_id UUID, -- Will add FK constraint after insights table

  -- Timestamps
  reddit_created_at TIMESTAMP WITH TIME ZONE NOT NULL,

  -- Repo context
  repo_config_id UUID REFERENCES repo_configs(id) ON DELETE CASCADE
);

-- =====================================================
-- TABLE: insights
-- Core entity: combines insights + Gemini analysis
-- =====================================================
CREATE TABLE insights (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,

  -- Insight data
  theme TEXT NOT NULL,
  description TEXT NOT NULL,
  entry_count INTEGER DEFAULT 0,
  unwrap_groups TEXT[] DEFAULT '{}', -- Legacy external group IDs (unused)

  -- Gemini analysis (stored as JSONB for flexibility)
  summary JSONB, -- InsightSummary
  issue_spec JSONB, -- IssueSpec
  patch_plan JSONB, -- PatchPlan (optional)

  -- Status workflow
  status TEXT CHECK (status IN (
    'pending',
    'analyzing',
    'ready',
    'approved',
    'in_progress',
    'completed',
    'closed'
  )) DEFAULT 'pending',

  -- Priority (from Gemini analysis)
  priority TEXT CHECK (priority IN ('critical', 'high', 'medium', 'low')),

  -- GitHub integration
  github_issue_number INTEGER,
  github_issue_url TEXT,
  github_pr_number INTEGER,
  github_pr_url TEXT,

  -- Approval tracking
  approved_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  approved_at TIMESTAMP WITH TIME ZONE,

  -- Foreign keys
  repo_config_id UUID REFERENCES repo_configs(id) ON DELETE CASCADE NOT NULL
);

-- =====================================================
-- TABLE: execution_logs
-- Logs from workflow execution (ingestion, analysis, GitHub actions)
-- =====================================================
CREATE TABLE execution_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,

  -- Log details
  log_level TEXT CHECK (log_level IN ('info', 'warning', 'error', 'debug')) DEFAULT 'info',
  message TEXT NOT NULL,
  metadata JSONB DEFAULT '{}',

  -- Execution context
  step_name TEXT, -- e.g., "reddit_ingestion", "gemini_analysis", "github_issue_created"

  -- Foreign keys
  insight_id UUID REFERENCES insights(id) ON DELETE CASCADE NOT NULL
);

-- =====================================================
-- TABLE: unwrap_mappings
-- Legacy mapping between Reddit entries and external insight entries/groups
-- =====================================================
CREATE TABLE unwrap_mappings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()) NOT NULL,

  -- Mappings
  reddit_entry_id UUID REFERENCES reddit_entries(id) ON DELETE CASCADE NOT NULL,
  unwrap_entry_id TEXT NOT NULL,
  unwrap_group_id TEXT, -- Optional group ID

  UNIQUE(reddit_entry_id, unwrap_entry_id)
);

-- =====================================================
-- FOREIGN KEY CONSTRAINTS
-- Add circular foreign keys after all tables are created
-- =====================================================

ALTER TABLE reddit_entries
  ADD CONSTRAINT fk_reddit_entries_insight
  FOREIGN KEY (insight_id)
  REFERENCES insights(id)
  ON DELETE SET NULL;

-- =====================================================
-- INDEXES
-- For performance on common queries
-- =====================================================

-- Reddit entries indexes
CREATE INDEX idx_reddit_entries_reddit_id ON reddit_entries(reddit_id);
CREATE INDEX idx_reddit_entries_processed ON reddit_entries(processed);
CREATE INDEX idx_reddit_entries_insight_id ON reddit_entries(insight_id);
CREATE INDEX idx_reddit_entries_subreddit ON reddit_entries(subreddit);
CREATE INDEX idx_reddit_entries_created_at ON reddit_entries(reddit_created_at DESC);

-- Insights indexes
CREATE INDEX idx_insights_status ON insights(status);
CREATE INDEX idx_insights_priority ON insights(priority);
CREATE INDEX idx_insights_repo_config ON insights(repo_config_id);
CREATE INDEX idx_insights_created_at ON insights(created_at DESC);
CREATE INDEX idx_insights_theme ON insights USING gin(theme gin_trgm_ops); -- Text search

-- Execution logs indexes
CREATE INDEX idx_execution_logs_insight ON execution_logs(insight_id);
CREATE INDEX idx_execution_logs_level ON execution_logs(log_level);
CREATE INDEX idx_execution_logs_created_at ON execution_logs(created_at DESC);

-- Legacy mappings indexes
CREATE INDEX idx_unwrap_mappings_reddit_entry ON unwrap_mappings(reddit_entry_id);
CREATE INDEX idx_unwrap_mappings_unwrap_entry ON unwrap_mappings(unwrap_entry_id);
CREATE INDEX idx_unwrap_mappings_group ON unwrap_mappings(unwrap_group_id);

-- =====================================================
-- FUNCTIONS & TRIGGERS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = TIMEZONE('utc', NOW());
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_repo_configs_updated_at
  BEFORE UPDATE ON repo_configs
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_insights_updated_at
  BEFORE UPDATE ON insights
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- ROW LEVEL SECURITY (RLS)
-- Enable RLS for multi-tenant support
-- =====================================================

ALTER TABLE repo_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE reddit_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE execution_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE unwrap_mappings ENABLE ROW LEVEL SECURITY;

-- Policies for repo_configs (users can only see their own)
CREATE POLICY "Users can view their own repo configs"
  ON repo_configs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own repo configs"
  ON repo_configs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own repo configs"
  ON repo_configs FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own repo configs"
  ON repo_configs FOR DELETE
  USING (auth.uid() = user_id);

-- Policies for insights (via repo_configs)
CREATE POLICY "Users can view insights for their repos"
  ON insights FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM repo_configs
      WHERE repo_configs.id = insights.repo_config_id
      AND repo_configs.user_id = auth.uid()
    )
  );

-- Similar policies for other tables...
-- (For MVP, you can also allow service role to bypass RLS)

-- =====================================================
-- DEMO DATA (Optional, for testing)
-- =====================================================

-- You can add sample repo_config, reddit_entries, insights here for demo mode
-- Or load via backend scripts

COMMENT ON TABLE repo_configs IS 'Repository configurations for Reddit monitoring';
COMMENT ON TABLE reddit_entries IS 'Reddit posts and comments collected for analysis';
COMMENT ON TABLE insights IS 'Core entity combining insights and Gemini analysis';
COMMENT ON TABLE execution_logs IS 'Logs from workflow execution steps';
COMMENT ON TABLE unwrap_mappings IS 'Legacy mappings between Reddit entries and external insight system';
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
