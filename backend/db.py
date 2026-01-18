"""
Database operations for EchoFix using Supabase.
All CRUD operations for Reddit entries, insights, and related entities.
"""

from supabase import Client
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
import logging

from models import (
    RedditEntry,
    Insight,
    IssueSpec,
    PatchPlan,
    InsightSummary,
    InsightStatus,
    RedditEntryStatus,
    RepoConfig,
    ExecutionLog,
    LogLevel
)

logger = logging.getLogger(__name__)


# =====================================================
# REDDIT ENTRY OPERATIONS
# =====================================================

def create_reddit_entry(supabase: Client, entry_data: Dict[str, Any]) -> RedditEntry:
    """Create a new Reddit entry."""
    result = supabase.table("reddit_entries").insert(entry_data).execute()
    return RedditEntry(**result.data[0])


def get_reddit_entry(supabase: Client, entry_id: UUID) -> Optional[RedditEntry]:
    """Get a single Reddit entry by ID."""
    result = supabase.table("reddit_entries").select("*").eq("id", str(entry_id)).single().execute()
    return RedditEntry(**result.data) if result.data else None


def get_reddit_entry_by_reddit_id(supabase: Client, reddit_id: str) -> Optional[RedditEntry]:
    """Get a single Reddit entry by reddit_id."""
    result = supabase.table("reddit_entries").select("*").eq("reddit_id", reddit_id).limit(1).execute()
    return RedditEntry(**result.data[0]) if result.data else None


def get_reddit_entries_by_ids(supabase: Client, entry_ids: List[UUID]) -> List[RedditEntry]:
    """Get multiple Reddit entries by IDs."""
    id_strings = [str(id) for id in entry_ids]
    result = supabase.table("reddit_entries").select("*").in_("id", id_strings).execute()
    return [RedditEntry(**entry) for entry in result.data] if result.data else []


def get_reddit_entries_by_insight(supabase: Client, insight_id: UUID) -> List[RedditEntry]:
    """Get all Reddit entries for an insight."""
    result = supabase.table("reddit_entries").select("*").eq("insight_id", str(insight_id)).execute()
    return [RedditEntry(**entry) for entry in result.data] if result.data else []


def get_unprocessed_reddit_entries(supabase: Client, limit: int = 100) -> List[RedditEntry]:
    """Get unprocessed Reddit entries."""
    statuses = [
        RedditEntryStatus.PENDING.value,
        RedditEntryStatus.READY.value,
        RedditEntryStatus.PROCESSING.value,
        RedditEntryStatus.FAILED.value
    ]
    result = supabase.table("reddit_entries").select("*").in_(
        "status", statuses
    ).limit(limit).execute()
    return [RedditEntry(**entry) for entry in result.data] if result.data else []


def check_reddit_entry_exists(supabase: Client, reddit_id: str) -> bool:
    """Check if a Reddit entry already exists by reddit_id."""
    result = supabase.table("reddit_entries").select("id").eq("reddit_id", reddit_id).execute()
    return len(result.data) > 0 if result.data else False


def update_reddit_entry(supabase: Client, entry_id: UUID, updates: Dict[str, Any]) -> RedditEntry:
    """Update a Reddit entry."""
    result = supabase.table("reddit_entries").update(updates).eq("id", str(entry_id)).execute()
    return RedditEntry(**result.data[0])


def get_reddit_entries_by_status(
    supabase: Client,
    status: RedditEntryStatus,
    limit: int = 100
) -> List[RedditEntry]:
    """Get Reddit entries by status."""
    result = supabase.table("reddit_entries").select("*").eq(
        "status", status.value
    ).limit(limit).execute()
    return [RedditEntry(**entry) for entry in result.data] if result.data else []


def get_ready_reddit_entries(supabase: Client, limit: int = 100) -> List[RedditEntry]:
    """Get Reddit entries ready for processing."""
    result = supabase.table("reddit_entries").select("*").eq(
        "status", RedditEntryStatus.READY.value
    ).is_("github_issue_url", "null").limit(limit).execute()
    return [RedditEntry(**entry) for entry in result.data] if result.data else []


def claim_reddit_entry(supabase: Client, entry_id: UUID) -> Optional[RedditEntry]:
    """Claim a READY entry for processing by setting status to PROCESSING."""
    updates = {"status": RedditEntryStatus.PROCESSING.value}
    result = supabase.table("reddit_entries").update(updates).eq(
        "id", str(entry_id)
    ).eq(
        "status", RedditEntryStatus.READY.value
    ).is_(
        "github_issue_url", "null"
    ).execute()
    return RedditEntry(**result.data[0]) if result.data else None


def bulk_update_reddit_entries_processed(supabase: Client, entry_ids: List[UUID]) -> int:
    """Mark multiple Reddit entries as processed."""
    id_strings = [str(id) for id in entry_ids]
    result = supabase.table("reddit_entries").update(
        {
            "processed": True,
            "status": RedditEntryStatus.PROCESSED.value,
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
    ).in_("id", id_strings).execute()
    return len(result.data) if result.data else 0


def mark_reddit_entries_processed_for_insight(
    supabase: Client,
    insight_id: UUID,
    github_issue_url: str,
    plan_md_path: Optional[str] = None,
    plan_md_sha: Optional[str] = None,
    github_pr_url: Optional[str] = None,
    github_pr_number: Optional[int] = None
) -> int:
    """Mark entries linked to an insight as processed."""
    entries = get_reddit_entries_by_insight(supabase, insight_id)
    processed_at = datetime.now(timezone.utc).isoformat()
    updated_count = 0

    for entry in entries:
        updates = {
            "processed": True,
            "status": RedditEntryStatus.PROCESSED.value,
            "processed_at": processed_at,
            "github_issue_url": github_issue_url
        }
        if plan_md_path:
            updates["plan_md_path"] = plan_md_path
        if plan_md_sha:
            updates["plan_md_sha"] = plan_md_sha
        if github_pr_url:
            updates["github_pr_url"] = github_pr_url
        if github_pr_number:
            updates["github_pr_number"] = github_pr_number

        update_reddit_entry(supabase, entry.id, updates)
        updated_count += 1

    return updated_count


# =====================================================
# INSIGHT OPERATIONS
# =====================================================

def create_insight(supabase: Client, insight_data: Dict[str, Any]) -> Insight:
    """Create a new insight."""
    result = supabase.table("insights").insert(insight_data).execute()
    return Insight(**result.data[0])


def get_insight(supabase: Client, insight_id: UUID) -> Optional[Insight]:
    """Get a single insight by ID."""
    result = supabase.table("insights").select("*").eq("id", str(insight_id)).single().execute()
    return Insight(**result.data) if result.data else None


def get_insights_by_status(supabase: Client, status: InsightStatus) -> List[Insight]:
    """Get all insights with a specific status."""
    result = supabase.table("insights").select("*").eq("status", status.value).execute()
    return [Insight(**insight) for insight in result.data] if result.data else []


def get_insights_by_repo(
    supabase: Client,
    repo_config_id: UUID,
    limit: Optional[int] = None
) -> List[Insight]:
    """Get all insights for a repository."""
    query = supabase.table("insights").select("*").eq(
        "repo_config_id", str(repo_config_id)
    ).order("created_at", desc=True)
    
    if limit:
        query = query.limit(limit)
    
    result = query.execute()
    return [Insight(**insight) for insight in result.data] if result.data else []


def update_insight(supabase: Client, insight_id: UUID, updates: Dict[str, Any]) -> Insight:
    """Update an insight."""
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = supabase.table("insights").update(updates).eq("id", str(insight_id)).execute()
    return Insight(**result.data[0])


def update_insight_status(
    supabase: Client,
    insight_id: UUID,
    status: InsightStatus,
    user_id: Optional[UUID] = None
) -> Insight:
    """Update insight status."""
    updates = {
        "status": status.value,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if status == InsightStatus.APPROVED and user_id:
        updates["approved_by"] = str(user_id)
        updates["approved_at"] = datetime.now(timezone.utc).isoformat()
    
    result = supabase.table("insights").update(updates).eq("id", str(insight_id)).execute()
    return Insight(**result.data[0])


def update_insight_github_info(
    supabase: Client,
    insight_id: UUID,
    issue_number: Optional[int] = None,
    issue_url: Optional[str] = None,
    pr_number: Optional[int] = None,
    pr_url: Optional[str] = None
) -> Insight:
    """Update GitHub issue/PR information."""
    updates = {}
    
    if issue_number is not None:
        updates["github_issue_number"] = issue_number
    if issue_url is not None:
        updates["github_issue_url"] = issue_url
    if pr_number is not None:
        updates["github_pr_number"] = pr_number
    if pr_url is not None:
        updates["github_pr_url"] = pr_url
    
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = supabase.table("insights").update(updates).eq("id", str(insight_id)).execute()
        return Insight(**result.data[0])
    
    return get_insight(supabase, insight_id)


def get_insight_with_entries(supabase: Client, insight_id: UUID) -> Optional[Dict[str, Any]]:
    """Get an insight with all related Reddit entries."""
    insight = get_insight(supabase, insight_id)
    if not insight:
        return None
    
    entries = get_reddit_entries_by_insight(supabase, insight_id)
    
    return {
        "insight": insight,
        "entries": entries,
        "entry_count": len(entries)
    }


# =====================================================
# REPO CONFIG OPERATIONS
# =====================================================

def create_repo_config(supabase: Client, config_data: Dict[str, Any]) -> RepoConfig:
    """Create a new repository configuration."""
    result = supabase.table("repo_configs").insert(config_data).execute()
    return RepoConfig(**result.data[0])


def get_repo_config(supabase: Client, config_id: UUID) -> Optional[RepoConfig]:
    """Get a repository configuration by ID."""
    result = supabase.table("repo_configs").select("*").eq("id", str(config_id)).single().execute()
    return RepoConfig(**result.data) if result.data else None


def get_repo_config_by_github(
    supabase: Client,
    github_owner: str,
    github_repo: str
) -> Optional[RepoConfig]:
    """Get a repository configuration by GitHub owner/repo."""
    result = supabase.table("repo_configs").select("*").eq(
        "github_owner", github_owner
    ).eq("github_repo", github_repo).single().execute()
    return RepoConfig(**result.data) if result.data else None


def get_repo_configs_by_user(supabase: Client, user_id: UUID) -> List[RepoConfig]:
    """Get all repository configurations for a user."""
    result = supabase.table("repo_configs").select("*").eq("user_id", str(user_id)).execute()
    return [RepoConfig(**config) for config in result.data] if result.data else []


def update_repo_config(supabase: Client, config_id: UUID, updates: Dict[str, Any]) -> RepoConfig:
    """Update a repository configuration."""
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = supabase.table("repo_configs").update(updates).eq("id", str(config_id)).execute()
    return RepoConfig(**result.data[0])


# =====================================================
# EXECUTION LOG OPERATIONS
# =====================================================

def create_execution_log(supabase: Client, log_data: Dict[str, Any]) -> ExecutionLog:
    """Create a new execution log entry."""
    result = supabase.table("execution_logs").insert(log_data).execute()
    return ExecutionLog(**result.data[0])


def get_execution_logs_by_insight(
    supabase: Client,
    insight_id: UUID,
    limit: Optional[int] = None
) -> List[ExecutionLog]:
    """Get execution logs for an insight."""
    query = supabase.table("execution_logs").select("*").eq(
        "insight_id", str(insight_id)
    ).order("created_at", desc=True)
    
    if limit:
        query = query.limit(limit)
    
    result = query.execute()
    return [ExecutionLog(**log) for log in result.data] if result.data else []


def log_execution_step(
    supabase: Client,
    insight_id: UUID,
    message: str,
    log_level: LogLevel = LogLevel.INFO,
    step_name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ExecutionLog:
    """Helper to log an execution step."""
    log_data = {
        "insight_id": str(insight_id),
        "log_level": log_level.value,
        "message": message,
        "step_name": step_name,
        "metadata": metadata or {}
    }
    return create_execution_log(supabase, log_data)


# =====================================================
# LEGACY MAPPING OPERATIONS
# =====================================================

def create_unwrap_mapping(
    supabase: Client,
    reddit_entry_id: UUID,
    unwrap_entry_id: str
) -> Dict[str, Any]:
    """Create a legacy mapping between Reddit entry and external entry ID."""
    mapping_data = {
        "reddit_entry_id": str(reddit_entry_id),
        "unwrap_entry_id": unwrap_entry_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = supabase.table("unwrap_mappings").insert(mapping_data).execute()
    return result.data[0]


def get_unwrap_entry_id(supabase: Client, reddit_entry_id: UUID) -> Optional[str]:
    """Get legacy external entry ID for a Reddit entry."""
    result = supabase.table("unwrap_mappings").select("unwrap_entry_id").eq(
        "reddit_entry_id", str(reddit_entry_id)
    ).single().execute()
    return result.data["unwrap_entry_id"] if result.data else None


def get_reddit_entry_ids_for_unwrap_group(
    supabase: Client,
    unwrap_group_id: str
) -> List[UUID]:
    """Get Reddit entry IDs for a legacy external group."""
    # This assumes you have a group_mappings table
    result = supabase.table("unwrap_mappings").select("reddit_entry_id").eq(
        "unwrap_group_id", unwrap_group_id
    ).execute()
    
    if result.data:
        return [UUID(item["reddit_entry_id"]) for item in result.data]
    return []


# =====================================================
# ANALYTICS / AGGREGATION OPERATIONS
# =====================================================

def get_insight_statistics(supabase: Client, repo_config_id: UUID) -> Dict[str, Any]:
    """Get statistics for insights in a repository."""
    # Get counts by status
    insights = get_insights_by_repo(supabase, repo_config_id)
    
    status_counts = {}
    for status in InsightStatus:
        status_counts[status.value] = sum(1 for i in insights if i.status == status)
    
    # Get total Reddit entries
    entries_result = supabase.table("reddit_entries").select(
        "id", count="exact"
    ).execute()
    total_entries = entries_result.count if hasattr(entries_result, 'count') else 0
    
    return {
        "total_insights": len(insights),
        "status_counts": status_counts,
        "total_reddit_entries": total_entries,
        "recent_insights": insights[:5]  # Most recent 5
    }


def search_insights(
    supabase: Client,
    repo_config_id: UUID,
    query: str,
    limit: int = 10
) -> List[Insight]:
    """Search insights by theme or description."""
    result = supabase.table("insights").select("*").eq(
        "repo_config_id", str(repo_config_id)
    ).ilike("theme", f"%{query}%").limit(limit).execute()
    
    insights = [Insight(**insight) for insight in result.data] if result.data else []
    
    # Also search in description if no results
    if not insights:
        result = supabase.table("insights").select("*").eq(
            "repo_config_id", str(repo_config_id)
        ).ilike("description", f"%{query}%").limit(limit).execute()
        insights = [Insight(**insight) for insight in result.data] if result.data else []
    
    return insights
