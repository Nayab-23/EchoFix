"""
Pydantic models for EchoFix backend.
Used for request/response validation and type safety.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


# =====================================================
# ENUMS
# =====================================================

class InsightType(str, Enum):
    """Types of insights extracted from Reddit."""
    BUG = "bug"
    FEATURE = "feature"
    ENHANCEMENT = "enhancement"
    QUESTION = "question"
    FEEDBACK = "feedback"


class InsightStatus(str, Enum):
    """Status workflow for insights."""
    PENDING = "pending"          # New insight, not reviewed
    ANALYZING = "analyzing"      # Gemini analyzing
    READY = "ready"              # Ready for action
    APPROVED = "approved"        # Human approved
    IN_PROGRESS = "in_progress"  # Being worked on
    COMPLETED = "completed"      # Issue/PR created
    CLOSED = "closed"            # No action needed


class Priority(str, Enum):
    """Priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class LogLevel(str, Enum):
    """Log levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


class RedditEntryStatus(str, Enum):
    """Processing status for Reddit entries."""
    PENDING = "pending"
    READY = "ready"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    SKIPPED = "skipped"


# =====================================================
# REDDIT MODELS
# =====================================================

class RedditEntry(BaseModel):
    """Reddit post or comment."""
    id: UUID
    created_at: datetime
    
    # Reddit metadata
    reddit_id: str
    reddit_type: str  # "post" or "comment"
    title: Optional[str] = None
    body: str
    author: str
    subreddit: str
    permalink: str
    
    # Engagement
    score: Optional[int] = None
    num_comments: int = 0
    
    # Media
    image_urls: List[str] = []
    video_url: Optional[str] = None
    
    # Processing
    processed: bool = False
    status: RedditEntryStatus = RedditEntryStatus.PENDING
    last_score_check_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    github_issue_url: Optional[str] = None
    plan_md_path: Optional[str] = None
    plan_md_sha: Optional[str] = None
    github_pr_url: Optional[str] = None
    github_pr_number: Optional[int] = None
    unwrap_entry_id: Optional[str] = None
    insight_id: Optional[UUID] = None
    
    # Timestamps
    reddit_created_at: datetime


class RedditIngestionRequest(BaseModel):
    """Request to ingest Reddit data."""
    subreddits: List[str] = []
    keywords: List[str] = []
    product_names: List[str] = []
    limit: int = 100
    time_filter: str = "day"  # hour, day, week, month, year


class RedditIngestionResponse(BaseModel):
    """Response from Reddit ingestion."""
    success: bool
    entries_collected: int
    entries_new: int
    entries_duplicate: int
    entries: List[RedditEntry]


class RedditURLIngestRequest(BaseModel):
    """Request to ingest a specific Reddit thread URL."""
    url: str
    max_items: Optional[int] = None


class RedditURLIngestResponse(BaseModel):
    """Response from URL-based ingestion."""
    success: bool
    url: str
    run_id: str
    imported_count: int
    entries: List[RedditEntry]


class RedditSeedIngestResponse(BaseModel):
    """Response from seed thread ingestion."""
    success: bool
    threads_processed: int
    total_imported: int
    results: List[Dict[str, Any]]


# =====================================================
# GEMINI MODELS
# =====================================================

class InsightSummary(BaseModel):
    """Summary of an insight by Gemini."""
    theme: str = Field(description="Clear, concise theme (max 80 chars)")
    severity: Priority = Field(description="Priority level")
    confidence: float = Field(description="Confidence score 0-1")
    user_impact: str = Field(description="Impact on users")
    evidence_count: int = Field(description="Number of supporting entries")


class IssueSpec(BaseModel):
    """Structured issue specification from Gemini."""
    title: str = Field(description="Clear, actionable title (max 80 chars)")
    problem_statement: str = Field(description="What's the problem?")
    steps_to_reproduce: Optional[str] = Field(default=None, description="How to reproduce (for bugs)")
    user_impact: Optional[str] = Field(default=None, description="Why it matters to users")
    expected_behavior: str = Field(description="What should happen?")
    actual_behavior: Optional[str] = Field(default=None, description="What actually happens? (for bugs)")
    suspected_root_cause: Optional[str] = Field(default=None, description="Suspected root cause")
    suggested_fix_steps: Optional[str] = Field(default=None, description="Suggested fix steps")
    acceptance_criteria: List[str] = Field(description="List of acceptance criteria")
    labels: List[str] = Field(description="GitHub labels")
    priority: Priority = Field(description="Priority level")
    estimated_effort: Optional[str] = Field(default=None, description="T-shirt size: XS, S, M, L, XL")


class PatchPlan(BaseModel):
    """Plan for code changes from Gemini."""
    summary: str = Field(description="One-line summary")
    files_impacted: List[str] = Field(description="Files likely to change")
    change_outline: str = Field(description="High-level change description")
    risk_level: str = Field(description="low, medium, high")
    test_plan: str = Field(description="How to test changes")


class GeminiAnalyzeRequest(BaseModel):
    """Request to analyze insight with Gemini."""
    insight_id: UUID
    include_images: bool = False


class GeminiAnalyzeResponse(BaseModel):
    """Response from Gemini analysis."""
    success: bool
    insight_summary: Optional[InsightSummary] = None
    issue_spec: Optional[IssueSpec] = None
    patch_plan: Optional[PatchPlan] = None
    error: Optional[str] = None


# =====================================================
# INSIGHT MODELS (Core EchoFix entity)
# =====================================================

class Insight(BaseModel):
    """Central insight entity - combines local grouping + Gemini."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    # Insight data
    theme: str
    description: str
    entry_count: int
    unwrap_groups: List[str] = []  # Group IDs
    
    # Gemini analysis
    summary: Optional[InsightSummary] = None
    issue_spec: Optional[IssueSpec] = None
    patch_plan: Optional[PatchPlan] = None
    
    # Status
    status: InsightStatus = InsightStatus.PENDING
    priority: Optional[Priority] = None
    
    # GitHub integration
    github_issue_number: Optional[int] = None
    github_issue_url: Optional[str] = None
    github_pr_number: Optional[int] = None
    github_pr_url: Optional[str] = None

    # Community approval
    community_approval_requested: Optional[bool] = False
    community_reply_id: Optional[str] = None
    community_reply_score: Optional[int] = 0
    community_approved: Optional[bool] = False
    community_approved_at: Optional[datetime] = None

    # Metadata
    repo_config_id: UUID
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None


class CreateInsightRequest(BaseModel):
    """Request to create an insight."""
    theme: str
    description: str
    unwrap_groups: List[str]
    repo_config_id: UUID


class UpdateInsightStatusRequest(BaseModel):
    """Request to update insight status."""
    status: InsightStatus
    user_id: Optional[UUID] = None


# =====================================================
# GITHUB MODELS
# =====================================================

class CreateGitHubIssueRequest(BaseModel):
    """Request to create GitHub issue."""
    insight_id: UUID
    title: str
    body: str
    labels: List[str] = []
    assignees: List[str] = []


class CreateGitHubIssueResponse(BaseModel):
    """Response from GitHub issue creation."""
    success: bool
    issue_number: Optional[int] = None
    issue_url: Optional[str] = None
    error: Optional[str] = None


class CreateGitHubPRRequest(BaseModel):
    """Request to create GitHub PR."""
    insight_id: UUID
    title: str
    body: str
    branch_name: str
    base_branch: str = "main"


# =====================================================
# REPO CONFIG MODELS
# =====================================================

class RepoConfig(BaseModel):
    """Repository configuration."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    # Repository
    github_owner: str
    github_repo: str
    github_branch: str = "main"
    
    # Reddit monitoring
    subreddits: List[str] = []
    keywords: List[str] = []
    product_names: List[str] = []
    
    # Automation settings
    auto_create_issues: bool = False
    auto_create_prs: bool = False
    require_approval: bool = True
    
    # User
    user_id: Optional[UUID] = None


class CreateRepoConfigRequest(BaseModel):
    """Request to create repo config."""
    github_owner: str
    github_repo: str
    github_branch: str = "main"
    subreddits: List[str] = []
    keywords: List[str] = []
    product_names: List[str] = []


# =====================================================
# WORKFLOW MODELS (n8n integration)
# =====================================================

class WorkflowTriggerRequest(BaseModel):
    """Request to trigger n8n workflow."""
    workflow_name: str
    payload: Dict[str, Any] = {}


class WorkflowApprovalRequest(BaseModel):
    """Request for workflow approval."""
    insight_id: UUID
    action: str  # "approve", "reject", "request_more_info"
    comment: Optional[str] = None
    user_id: UUID


# =====================================================
# LOG MODELS
# =====================================================

class ExecutionLog(BaseModel):
    """Execution log entry."""
    id: UUID
    created_at: datetime
    
    log_level: LogLevel
    message: str
    metadata: Dict[str, Any] = {}
    step_name: Optional[str] = None
    
    insight_id: UUID


class CreateExecutionLogRequest(BaseModel):
    """Request to create log entry."""
    insight_id: UUID
    log_level: LogLevel
    message: str
    metadata: Dict[str, Any] = {}
    step_name: Optional[str] = None


# =====================================================
# RESPONSE MODELS
# =====================================================

class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    demo_mode: bool
    services: Dict[str, bool]


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    details: Optional[str] = None
    code: Optional[str] = None
