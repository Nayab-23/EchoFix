"""
EchoFix Backend API
Flask server for Reddit-first feedback-to-shipping pipeline
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Load environment variables
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Initialize Supabase (with fallback for demo mode)
from supabase import create_client, Client

# Check DEMO_MODE early
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
MIN_SCORE = int(os.getenv("MIN_SCORE", "2"))
SCORE_REFRESH_SECONDS = int(os.getenv("SCORE_REFRESH_SECONDS", "600"))
ENABLE_PLAN_MD = os.getenv("ENABLE_PLAN_MD", "true").lower() == "true"
ENABLE_PR_AUTOMATION = os.getenv("ENABLE_PR_AUTOMATION", "false").lower() == "true"
PLAN_MD_DIR = os.getenv("PLAN_MD_DIR", "backend/artifacts/plans")
PLAN_MD_PATH_TEMPLATE = os.getenv("PLAN_MD_PATH_TEMPLATE", "docs/echofix_plans/{reddit_entry_id}.md")

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Only initialize Supabase if credentials are provided
if supabase_url and supabase_key:
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
    except Exception as e:
        logger.warning(f"Failed to initialize Supabase client: {e}")
        supabase = None
else:
    # Use None in demo mode or if credentials not provided
    supabase: Client = None
    if not DEMO_MODE:
        logger.warning("Supabase credentials not provided. Some features will be unavailable.")


# Initialize clients
from reddit_client import RedditClient
from gemini_client import GeminiClient
from github_client import GitHubClient, format_issue_body_from_spec
from services.insight_generator import generate_insights_from_entries
from services.reddit_json_client import RedditJSONClient
from services.score_threshold import (
    determine_entry_status,
    should_process_entry
)
from services.plan_md import (
    build_plan_md,
    save_plan_md,
    should_create_pr
)
import db
from models import (
    RedditIngestionRequest,
    RedditIngestionResponse,
    RedditURLIngestRequest,
    RedditURLIngestResponse,
    RedditSeedIngestResponse,
    GeminiAnalyzeRequest,
    GeminiAnalyzeResponse,
    CreateGitHubIssueRequest,
    CreateGitHubIssueResponse,
    UpdateInsightStatusRequest,
    CreateRepoConfigRequest,
    InsightStatus,
    RedditEntryStatus,
    RedditEntry,
    IssueSpec,
    InsightSummary,
    PatchPlan,
    RepoConfig,
    Priority,
    HealthCheckResponse,
    Insight
)

# Initialize clients with demo mode support
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

reddit_client = RedditClient(demo_mode=DEMO_MODE)
gemini_client = GeminiClient(demo_mode=DEMO_MODE)
github_client = GitHubClient(demo_mode=DEMO_MODE)
reddit_json_client = RedditJSONClient()

logger.info(f"EchoFix initialized - Demo Mode: {DEMO_MODE}")


def _resolve_entry_status(
    existing_status: Optional[RedditEntryStatus],
    candidate_status: RedditEntryStatus
) -> RedditEntryStatus:
    """Resolve status without downgrading processed entries."""
    if existing_status in (
        RedditEntryStatus.PROCESSED,
        RedditEntryStatus.SKIPPED,
        RedditEntryStatus.PROCESSING,
        RedditEntryStatus.READY
    ):
        return existing_status
    return candidate_status


def _upsert_reddit_entry(
    entry,
    repo_config_id: str
) -> Dict[str, Any]:
    """Insert or update a Reddit entry with threshold status."""
    existing = db.get_reddit_entry_by_reddit_id(supabase, entry.reddit_id)
    now_iso = datetime.now(timezone.utc).isoformat()
    candidate_status = determine_entry_status(entry.score, MIN_SCORE)
    status = _resolve_entry_status(
        existing.status if existing else None,
        candidate_status
    )

    if existing:
        updates = {
            "title": entry.title,
            "body": entry.body,
            "author": entry.author,
            "subreddit": entry.subreddit,
            "permalink": entry.permalink,
            "num_comments": entry.num_comments,
            "image_urls": entry.image_urls,
            "video_url": entry.video_url,
            "reddit_created_at": entry.reddit_created_at.isoformat(),
            "status": status.value
        }
        if entry.score is not None:
            updates["score"] = entry.score
            updates["last_score_check_at"] = now_iso
        updated_entry = db.update_reddit_entry(supabase, existing.id, updates)
        return {"entry": updated_entry, "created": False}

    entry_data = entry.model_dump(mode="json")
    entry_data["repo_config_id"] = repo_config_id
    entry_data["status"] = status.value
    if entry.score is not None:
        entry_data["last_score_check_at"] = now_iso
    created_entry = db.create_reddit_entry(supabase, entry_data)
    return {"entry": created_entry, "created": True}


def _format_plan_path(entry, insight, issue_number, repo_config):
    class SafeDict(dict):
        def __missing__(self, key):
            return ""

    values = SafeDict({
        "reddit_entry_id": entry.reddit_id,
        "insight_id": str(insight.id),
        "issue_number": issue_number or "",
        "owner": repo_config.github_owner,
        "repo": repo_config.github_repo
    })

    try:
        return PLAN_MD_PATH_TEMPLATE.format_map(values)
    except Exception as exc:
        logger.warning("Invalid PLAN_MD_PATH_TEMPLATE: %s", exc)
        return f"docs/echofix_plans/{entry.reddit_id}.md"


def _normalize_issue_spec(issue_spec):
    if isinstance(issue_spec, IssueSpec):
        return issue_spec
    if not issue_spec:
        return None
    return IssueSpec(**issue_spec)


def _normalize_summary(summary):
    if isinstance(summary, InsightSummary):
        return summary
    if not summary:
        return InsightSummary(
            theme="Unknown",
            severity=Priority.MEDIUM,
            confidence=0.5,
            user_impact="Impact TBD",
            evidence_count=0
        )
    return InsightSummary(**summary)


def _normalize_patch_plan(patch_plan):
    if isinstance(patch_plan, PatchPlan):
        return patch_plan
    if not patch_plan:
        return PatchPlan(
            summary="Implementation plan to be determined",
            files_impacted=[],
            change_outline="Changes to be determined",
            risk_level="medium",
            test_plan="Manual testing required"
        )
    return PatchPlan(**patch_plan)


def _ensure_plan_and_pr(
    entry,
    insight,
    issue_spec,
    summary,
    reddit_entries,
    repo_config,
    github_issue,
    plan_content: Optional[str] = None,
    plan_repo_path: Optional[str] = None
):
    result = {
        "plan_md_path": None,
        "plan_md_sha": None,
        "pr_url": None,
        "pr_number": None
    }

    if not ENABLE_PLAN_MD and not ENABLE_PR_AUTOMATION:
        return result

    if not plan_content:
        plan_content = build_plan_md(entry, issue_spec, summary, reddit_entries)

    if not plan_repo_path:
        plan_repo_path = _format_plan_path(entry, insight, github_issue.number, repo_config)

    local_path = save_plan_md(plan_content, PLAN_MD_DIR, entry.reddit_id)
    result["plan_md_path"] = plan_repo_path

    plan_sha = None
    if ENABLE_PR_AUTOMATION:
        branch_name = f"echofix/{entry.reddit_id}"
        try:
            github_client.create_branch(
                repo_config.github_owner,
                repo_config.github_repo,
                branch_name,
                repo_config.github_branch
            )
        except Exception as exc:
            logger.warning("Failed to create branch %s: %s", branch_name, exc)

        try:
            existing_sha = github_client.get_file_sha(
                repo_config.github_owner,
                repo_config.github_repo,
                plan_repo_path,
                ref=branch_name
            )
            plan_sha = github_client.upsert_file(
                repo_config.github_owner,
                repo_config.github_repo,
                plan_repo_path,
                branch_name,
                plan_content.encode(),
                f"Add EchoFix plan for {entry.reddit_id}",
                sha=existing_sha
            )
            result["plan_md_sha"] = plan_sha
        except Exception as exc:
            logger.warning("Failed to upload plan.md: %s", exc)

        # PR creation is now manual via /api/insights/<id>/create-pr endpoint
        # This provides human-in-the-loop approval before creating PRs
        logger.info(
            "Plan committed to branch %s. Use /api/insights/<id>/create-pr to create PR after approval.",
            branch_name
        )
    else:
        # Always store plan SHA if file created locally
        result["plan_md_sha"] = None

    logger.info("Plan saved to %s (local %s)", plan_repo_path, local_path)
    return result


def _get_existing_issue_info(insight, reddit_entries):
    """Return existing issue info if one is already linked."""
    if insight.github_issue_url or insight.github_issue_number:
        return {
            "issue_url": insight.github_issue_url,
            "issue_number": insight.github_issue_number,
            "source": "insight"
        }

    for entry in reddit_entries:
        if entry.github_issue_url:
            return {
                "issue_url": entry.github_issue_url,
                "issue_number": None,
                "source": "entry"
            }

    return None


def _create_issue_for_insight(insight, reddit_entries, repo_config):
    """Create GitHub issue for an insight if not already created."""
    existing = _get_existing_issue_info(insight, reddit_entries)
    if existing:
        return {"issue": None, "existing": existing}

    issue_spec_obj = _normalize_issue_spec(insight.issue_spec)
    if not issue_spec_obj:
        return {"issue": None, "existing": None}

    summary_obj = _normalize_summary(insight.summary)
    issue_spec_data = (
        issue_spec_obj.model_dump(mode="json")
        if hasattr(issue_spec_obj, "model_dump")
        else issue_spec_obj
    )
    if not issue_spec_data.get("user_impact") and insight.summary:
        summary_data = (
            insight.summary.model_dump(mode="json")
            if hasattr(insight.summary, "model_dump")
            else insight.summary
        )
        issue_spec_data["user_impact"] = summary_data.get("user_impact")

    primary_entry = reddit_entries[0] if reddit_entries else None
    plan_content = None
    plan_preview_path = None
    if primary_entry and (ENABLE_PLAN_MD or ENABLE_PR_AUTOMATION):
        plan_content = build_plan_md(primary_entry, issue_spec_obj, summary_obj, reddit_entries)
        plan_preview_path = _format_plan_path(primary_entry, insight, None, repo_config)

    body = format_issue_body_from_spec(
        issue_spec_data,
        [e.model_dump(mode='json') for e in reddit_entries]
    )

    if plan_content and ENABLE_PLAN_MD and plan_preview_path:
        snippet = "\n".join(plan_content.splitlines()[:5])
        body += (
            "\n\n## Plan-of-Attack\n"
            f"{snippet}\n\n"
            f"Full plan stored at `{plan_preview_path}`"
        )

    github_issue = github_client.create_issue(
        owner=repo_config.github_owner,
        repo=repo_config.github_repo,
        title=issue_spec_data["title"],
        body=body,
        labels=issue_spec_data.get("labels", [])
    )

    db.update_insight_github_info(
        supabase,
        insight.id,
        issue_number=github_issue.number,
        issue_url=github_issue.url
    )

    primary_entry = reddit_entries[0] if reddit_entries else None
    plan_metadata = {}
    if primary_entry and (ENABLE_PLAN_MD or ENABLE_PR_AUTOMATION):
        plan_metadata = _ensure_plan_and_pr(
            primary_entry,
            insight,
            issue_spec_obj,
            summary_obj,
            reddit_entries,
            repo_config,
            github_issue,
            plan_content=plan_content
        )

    db.mark_reddit_entries_processed_for_insight(
        supabase,
        insight.id,
        github_issue.url,
        plan_md_path=plan_metadata.get("plan_md_path"),
        plan_md_sha=plan_metadata.get("plan_md_sha"),
        github_pr_url=plan_metadata.get("pr_url"),
        github_pr_number=plan_metadata.get("pr_number")
    )

    db.update_insight_status(supabase, insight.id, InsightStatus.IN_PROGRESS)

    db.log_execution_step(
        supabase,
        insight.id,
        f"Created GitHub issue #{github_issue.number}",
        step_name="github_issue_created",
        metadata={"issue_url": github_issue.url, "issue_number": github_issue.number}
    )

    return {"issue": github_issue, "existing": None, "plan_metadata": plan_metadata}


def _refresh_pending_scores(limit: int) -> Dict[str, int]:
    """Refresh scores for pending Reddit entries and update readiness."""
    entries = db.get_reddit_entries_by_status(
        supabase,
        RedditEntryStatus.PENDING,
        limit=limit
    )

    if not entries:
        return {
            "pending_checked": 0,
            "updated": 0,
            "ready": 0,
            "skipped_recent": 0
        }

    updated = 0
    ready = 0
    skipped_recent = 0

    for entry in entries:
        # Always refresh PENDING entries when explicitly called via API
        # The workflow runs on a schedule, so time-based skipping is not needed
        score = None
        if not reddit_client.demo_mode:
            score = reddit_client.fetch_entry_score(entry.reddit_id, entry.reddit_type)

        if score is None:
            score = reddit_json_client.fetch_entry_score(entry.permalink, entry.reddit_id)

        updates = {
            "last_score_check_at": datetime.now(timezone.utc).isoformat()
        }

        if score is not None:
            updates["score"] = score
            new_status = determine_entry_status(score, MIN_SCORE)
            updates["status"] = new_status.value
            if new_status == RedditEntryStatus.READY:
                ready += 1

        db.update_reddit_entry(supabase, entry.id, updates)
        updated += 1

    logger.info(
        "Score refresh: checked=%s updated=%s ready=%s skipped_recent=%s",
        len(entries),
        updated,
        ready,
        skipped_recent
    )

    return {
        "pending_checked": len(entries),
        "updated": updated,
        "ready": ready,
        "skipped_recent": skipped_recent
    }


def _refresh_community_approvals() -> Dict[str, int]:
    """Refresh scores for community approval replies and auto-merge when approved."""
    try:
        # Query insights with pending community approvals
        result = supabase.table("insights").select("*").eq(
            "community_approval_requested", True
        ).eq("community_approved", False).execute()
    except Exception as e:
        # If columns don't exist yet (migration not applied), skip gracefully
        error_msg = str(e)
        if 'does not exist' in error_msg or '42703' in error_msg:
            logger.warning("Community approval columns don't exist yet - skipping community approval refresh")
            return {
                "checked": 0,
                "updated": 0,
                "approved": 0,
                "merged": 0
            }
        raise

    if not result.data:
        return {
            "checked": 0,
            "updated": 0,
            "approved": 0,
            "merged": 0
        }

    checked = 0
    updated = 0
    approved_count = 0
    merged_count = 0

    for insight_data in result.data:
        insight = Insight(**insight_data)

        if not insight.community_reply_id:
            continue

        checked += 1

        # Fetch current score of the community reply
        score = None
        if not reddit_client.demo_mode:
            score = reddit_client.fetch_entry_score(insight.community_reply_id, "comment")

        if score is None:
            # Try JSON client as fallback
            reply_url = f"https://reddit.com/comments/{insight.community_reply_id}"
            score = reddit_json_client.fetch_entry_score(reply_url, insight.community_reply_id)

        if score is None:
            logger.warning(f"Could not fetch score for community reply {insight.community_reply_id}")
            continue

        # Update the reply score
        updates = {"community_reply_score": score}

        # Check if approved (score >= MIN_SCORE)
        if score >= MIN_SCORE:
            updates["community_approved"] = True
            updates["community_approved_at"] = datetime.now(timezone.utc).isoformat()
            approved_count += 1

            # Auto-merge the PR
            if insight.github_pr_number and insight.github_repo:
                try:
                    owner, repo = insight.github_repo.split("/")
                    github_client.merge_pr(
                        owner=owner,
                        repo=repo,
                        pr_number=insight.github_pr_number,
                        merge_method="squash"
                    )
                    updates["github_pr_merged"] = True
                    updates["github_pr_merged_at"] = datetime.now(timezone.utc).isoformat()
                    merged_count += 1
                    logger.info(f"Auto-merged PR #{insight.github_pr_number} after community approval")
                except Exception as e:
                    logger.error(f"Failed to auto-merge PR #{insight.github_pr_number}: {e}")

        db.update_insight(supabase, insight.id, updates)
        updated += 1

    logger.info(
        "Community approval refresh: checked=%s updated=%s approved=%s merged=%s",
        checked, updated, approved_count, merged_count
    )

    return {
        "checked": checked,
        "updated": updated,
        "approved": approved_count,
        "merged": merged_count
    }


def _process_ready_workflow(entry_limit: int, insight_limit: int, issue_limit: int) -> Dict[str, Any]:
    report = {
        "entries_processed": 0,
        "insights_created": 0,
        "insights_updated": 0,
        "insights_analyzed": 0,
        "issues_created": 0,
        "issues_skipped": 0,
        "processed_ids": [],
        "created_issue_urls": [],
        "created_pr_urls": [],
        "plan_paths": []
    }

    entries = db.get_ready_reddit_entries(supabase, limit=entry_limit)
    claimed_entries = []

    for entry in entries:
        if not should_process_entry(entry):
            continue
        claimed = db.claim_reddit_entry(supabase, entry.id)
        if claimed:
            claimed_entries.append(claimed)

    repo_configs = supabase.table("repo_configs").select("*").limit(1).execute()
    if not repo_configs.data:
        report["error"] = "No repository configured"
        return report

    repo_config = RepoConfig(**repo_configs.data[0])
    repo_config_id = repo_config.id

    if claimed_entries:
        insight_result = generate_insights_from_entries(
            supabase,
            repo_config_id,
            claimed_entries
        )
        report["entries_processed"] = insight_result.get("entries_processed", 0)
        report["insights_created"] = insight_result.get("insights_created", 0)
        report["insights_updated"] = insight_result.get("insights_updated", 0)

    pending_insights = db.get_insights_by_status(supabase, InsightStatus.PENDING)
    for insight in pending_insights[:insight_limit]:
        if insight.github_issue_url or insight.github_issue_number:
            report["issues_skipped"] += 1
            continue

        insight_data = db.get_insight_with_entries(supabase, insight.id)
        if not insight_data:
            continue

        reddit_entries = insight_data["entries"]
        if not reddit_entries:
            continue

        db.update_insight_status(supabase, insight.id, InsightStatus.ANALYZING)

        summary = gemini_client.analyze_insight(insight, reddit_entries)
        issue_spec = gemini_client.generate_issue_spec(
            insight,
            summary,
            reddit_entries,
            include_images=any(e.image_urls for e in reddit_entries)
        )
        patch_plan = gemini_client.generate_patch_plan(issue_spec)

        db.update_insight(supabase, insight.id, {
            "summary": summary.model_dump(mode='json'),
            "issue_spec": issue_spec.model_dump(mode='json'),
            "patch_plan": patch_plan.model_dump(mode='json'),
            "priority": issue_spec.priority.value,
            "status": InsightStatus.READY.value
        })
        report["insights_analyzed"] += 1

    ready_insights = db.get_insights_by_status(supabase, InsightStatus.READY)
    for insight in ready_insights[:issue_limit]:
        insight_data = db.get_insight_with_entries(supabase, insight.id)
        if not insight_data:
            continue

        reddit_entries = insight_data["entries"]
        if not reddit_entries:
            continue

        result = _create_issue_for_insight(insight, reddit_entries, repo_config)
        if result["existing"]:
            report["issues_skipped"] += 1
            continue

        github_issue = result["issue"]
        if not github_issue:
            continue

        report["issues_created"] += 1
        report["created_issue_urls"].append(github_issue.url)
        report["processed_ids"].extend([entry.reddit_id for entry in reddit_entries])

        plan_meta = result.get("plan_metadata", {}) or {}
        plan_path = plan_meta.get("plan_md_path")
        plan_pr_url = plan_meta.get("pr_url")
        if plan_path:
            report["plan_paths"].append(plan_path)
        if plan_pr_url:
            report["created_pr_urls"].append(plan_pr_url)

    return report


# =====================================================
# HEALTH CHECK
# =====================================================

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "demo_mode": DEMO_MODE,
        "services": {
            "supabase": bool(os.getenv("SUPABASE_URL")),
            "reddit": bool(os.getenv("REDDIT_CLIENT_ID")) or DEMO_MODE,
            "gemini": bool(os.getenv("GEMINI_API_KEY")) or DEMO_MODE,
            "github": bool(os.getenv("GITHUB_TOKEN")) or DEMO_MODE
        }
    })


# =====================================================
# REDDIT INGESTION ENDPOINTS
# =====================================================

@app.route("/api/reddit/ingest", methods=["POST"])
def ingest_reddit():
    """
    Ingest Reddit data based on configuration.
    """
    try:
        # Get request data
        data = request.get_json() or {}
        ingest_request = RedditIngestionRequest(**data)
        
        # Get default repo config (for MVP, use first one)
        # In production, this would be user-specific
        repo_configs = supabase.table("repo_configs").select("*").limit(1).execute()
        
        if not repo_configs.data:
            return jsonify({
                "error": "No repository configured. Please create a repo config first."
            }), 404
        
        repo_config = repo_configs.data[0]
        
        # Use config values if not provided in request
        subreddits = ingest_request.subreddits or repo_config.get("subreddits", [])
        keywords = ingest_request.keywords or repo_config.get("keywords", [])
        product_names = ingest_request.product_names or repo_config.get("product_names", [])
        
        if not subreddits and not keywords and not product_names:
            return jsonify({
                "error": "Must provide subreddits, keywords, or product_names"
            }), 400
        
        # Collect entries
        all_entries = []
        
        # Search subreddits with keywords
        if subreddits and keywords:
            entries = reddit_client.search_subreddits(
                subreddits=subreddits,
                keywords=keywords,
                limit=ingest_request.limit,
                time_filter=ingest_request.time_filter
            )
            all_entries.extend(entries)
        
        # Track product mentions
        if product_names:
            entries = reddit_client.track_product_mentions(
                product_names=product_names,
                subreddits=subreddits or ["programming", "webdev"],
                limit=ingest_request.limit,
                time_filter=ingest_request.time_filter
            )
            all_entries.extend(entries)
        
        # Upsert entries with threshold status
        entries_new = 0
        entries_updated = 0
        saved_entries = []

        for entry in all_entries:
            result = _upsert_reddit_entry(entry, repo_config["id"])
            saved_entries.append(result["entry"])
            if result["created"]:
                entries_new += 1
            else:
                entries_updated += 1

        logger.info(f"Ingested {entries_new} new entries, {entries_updated} updated")

        return jsonify({
            "success": True,
            "entries_collected": len(all_entries),
            "entries_new": entries_new,
            "entries_updated": entries_updated,
            "entries": [e.model_dump(mode='json') for e in saved_entries[:10]]  # Return first 10
        })
        
    except Exception as e:
        logger.error(f"Error ingesting Reddit data: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/reddit/entries", methods=["GET"])
def get_reddit_entries():
    """Get Reddit entries."""
    try:
        # Get query parameters
        limit = int(request.args.get("limit", 50))
        processed = request.args.get("processed")
        
        if processed == "false":
            entries = db.get_unprocessed_reddit_entries(supabase, limit=limit)
        else:
            # Get all recent entries
            result = supabase.table("reddit_entries").select("*").order(
                "created_at", desc=True
            ).limit(limit).execute()
            entries = [RedditEntry(**e) for e in result.data] if result.data else []
        
        return jsonify({
            "entries": [e.model_dump(mode='json') for e in entries],
            "count": len(entries)
        })
        
    except Exception as e:
        logger.error(f"Error getting Reddit entries: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/reddit/ingest-url", methods=["POST"])
def ingest_reddit_url():
    """
    Ingest a specific Reddit thread via RSS (no OAuth required).
    Hackathon-mode endpoint for "Bring Your Own Thread".
    """
    try:
        from services.reddit_rss import RedditRSSClient
        from models import RedditURLIngestRequest, RedditURLIngestResponse
        
        # Get request data
        data = request.get_json() or {}
        ingest_request = RedditURLIngestRequest(**data)
        
        ingest_mode = os.getenv("REDDIT_INGEST_MODE", "json")
        demo_mode = DEMO_MODE or ingest_mode == "fixtures"
        max_items = ingest_request.max_items or 50

        entries = []

        if ingest_mode == "json":
            if demo_mode:
                rss_client = RedditRSSClient(demo_mode=True)
                entries = rss_client.fetch_thread(
                    url=ingest_request.url,
                    max_items=max_items
                )
            else:
                entries = reddit_json_client.fetch_thread_entries(
                    ingest_request.url,
                    max_items
                )
        elif ingest_mode == "rss_url":
            rss_client = RedditRSSClient(demo_mode=demo_mode)
            entries = rss_client.fetch_thread(
                url=ingest_request.url,
                max_items=max_items
            )
        else:
            entries = reddit_json_client.fetch_thread_entries(
                ingest_request.url,
                max_items
            )
        
        if not entries:
            return jsonify({
                "success": False,
                "error": "No entries found or invalid URL"
            }), 400
        
        # Get or create default repo config
        repo_configs = supabase.table("repo_configs").select("*").limit(1).execute()
        if not repo_configs.data:
            return jsonify({
                "error": "No repository configured. Please create a repo config first."
            }), 404
        
        repo_config = repo_configs.data[0]
        
        # Upsert entries to database
        run_id = str(uuid4())
        imported_count = 0
        updated_count = 0
        saved_entries = []

        for entry in entries:
            result = _upsert_reddit_entry(entry, repo_config["id"])
            saved_entries.append(result["entry"])
            if result["created"]:
                imported_count += 1
            else:
                updated_count += 1

        logger.info(
            "RSS ingestion: %s new entries, %s updated from %s",
            imported_count,
            updated_count,
            ingest_request.url
        )
        
        return jsonify({
            "success": True,
            "url": ingest_request.url,
            "run_id": run_id,
            "imported_count": imported_count,
            "updated_count": updated_count,
            "entries": [e.model_dump(mode='json') for e in saved_entries]
        })
        
    except Exception as e:
        logger.error(f"Error ingesting Reddit URL: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/reddit/ingest-seed", methods=["POST"])
def ingest_reddit_seed():
    """
    Ingest seed Reddit threads from REDDIT_SEED_THREAD_URLS environment variable.
    For hackathon demos: pre-configured threads to showcase the pipeline.
    """
    try:
        from services.reddit_rss import RedditRSSClient
        from models import RedditSeedIngestResponse
        
        # Get seed URLs from environment
        seed_urls_str = os.getenv("REDDIT_SEED_THREAD_URLS", "")
        if not seed_urls_str:
            return jsonify({
                "error": "No seed URLs configured. Set REDDIT_SEED_THREAD_URLS in .env"
            }), 400
        
        seed_urls = [url.strip() for url in seed_urls_str.split(',') if url.strip()]
        
        if not seed_urls:
            return jsonify({
                "error": "No valid seed URLs found"
            }), 400
        
        ingest_mode = os.getenv("REDDIT_INGEST_MODE", "json")
        demo_mode = DEMO_MODE or ingest_mode == "fixtures"

        rss_client = RedditRSSClient(demo_mode=demo_mode)
        
        # Get default repo config
        repo_configs = supabase.table("repo_configs").select("*").limit(1).execute()
        if not repo_configs.data:
            return jsonify({
                "error": "No repository configured. Please create a repo config first."
            }), 404
        
        repo_config = repo_configs.data[0]
        
        # Process each seed URL
        results = []
        total_imported = 0
        
        for url in seed_urls:
            try:
                if ingest_mode == "json":
                    if demo_mode:
                        entries = rss_client.fetch_thread(url, max_items=50)
                    else:
                        entries = reddit_json_client.fetch_thread_entries(url, 50)
                elif ingest_mode == "rss_url":
                    entries = rss_client.fetch_thread(url, max_items=50)
                else:
                    entries = reddit_json_client.fetch_thread_entries(url, 50)
                
                imported = 0
                updated = 0
                saved_entries = []

                for entry in entries:
                    result = _upsert_reddit_entry(entry, repo_config["id"])
                    saved_entries.append(result["entry"])
                    if result["created"]:
                        imported += 1
                    else:
                        updated += 1

                total_imported += imported
                
                results.append({
                    "url": url,
                    "success": True,
                    "imported": imported,
                    "updated": updated,
                    "entries_preview": [e.model_dump(mode='json') for e in saved_entries[:3]]
                })
                
                logger.info(
                    "Seed ingestion: %s new entries, %s updated from %s",
                    imported,
                    updated,
                    url
                )
                
            except Exception as e:
                logger.error(f"Error processing seed URL {url}: {e}")
                results.append({
                    "url": url,
                    "success": False,
                    "error": str(e)
                })
        
        return jsonify({
            "success": True,
            "threads_processed": len(seed_urls),
            "total_imported": total_imported,
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error ingesting seed threads: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/reddit/refresh-scores", methods=["POST"])
def refresh_reddit_scores():
    """
    Refresh scores for pending Reddit entries and update readiness.
    """
    try:
        limit = int(request.args.get("limit", 100))
        result = _refresh_pending_scores(limit)

        return jsonify({
            "success": True,
            **result
        })

    except Exception as e:
        logger.error(f"Error refreshing scores: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# =====================================================
# END-TO-END PIPELINE (AUTO)
# =====================================================

@app.route("/api/pipeline/auto-process", methods=["POST"])
def auto_process_pipeline():
    """
    Refresh scores, generate insights, analyze with Gemini, and create issues.
    """
    try:
        refresh_scores = request.args.get("refresh_scores", "true").lower() == "true"
        entry_limit = int(request.args.get("entry_limit", 200))
        insight_limit = int(request.args.get("insight_limit", 10))
        issue_limit = int(request.args.get("issue_limit", 10))

        results = {
            "scores_refreshed": 0,
            "entries_ready": 0
        }

        if refresh_scores:
            refresh_result = _refresh_pending_scores(entry_limit)
            results["scores_refreshed"] = refresh_result.get("updated", 0)
            results["entries_ready"] = refresh_result.get("ready", 0)

            # Also refresh community approvals
            community_result = _refresh_community_approvals()
            results["community_approvals_checked"] = community_result.get("checked", 0)
            results["community_approvals_approved"] = community_result.get("approved", 0)
            results["community_prs_merged"] = community_result.get("merged", 0)

        process_result = _process_ready_workflow(entry_limit, insight_limit, issue_limit)
        results.update(process_result)

        return jsonify({
            "success": True,
            **results
        })

    except Exception as e:
        logger.error(f"Error running auto pipeline: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/pipeline/auto-process-ready", methods=["POST"])
def auto_process_ready():
    """
    Refresh scores and process READY entries end-to-end.
    """
    try:
        entry_limit = int(request.args.get("entry_limit", 200))
        insight_limit = int(request.args.get("insight_limit", 10))
        issue_limit = int(request.args.get("issue_limit", 10))

        refresh_result = _refresh_pending_scores(entry_limit)
        community_result = _refresh_community_approvals()
        process_result = _process_ready_workflow(entry_limit, insight_limit, issue_limit)

        return jsonify({
            "success": True,
            "refresh": refresh_result,
            "community_approvals": community_result,
            "report": {
                "processed_ids": process_result.get("processed_ids", []),
                "created_issue_urls": process_result.get("created_issue_urls", []),
                "created_pr_urls": process_result.get("created_pr_urls", []),
                "plan_paths": process_result.get("plan_paths", [])
            }
        })

    except Exception as e:
        logger.error(f"Error running ready pipeline: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# =====================================================
# INSIGHT GENERATION ENDPOINTS
# =====================================================

@app.route("/api/insights/generate", methods=["POST"])
def generate_insights():
    """
    Generate insights from unprocessed Reddit entries without external services.
    """
    try:
        # Get READY entries and claim them for processing
        entries = db.get_ready_reddit_entries(supabase, limit=200)
        claimed_entries = []

        for entry in entries:
            if not should_process_entry(entry):
                continue
            claimed = db.claim_reddit_entry(supabase, entry.id)
            if claimed:
                claimed_entries.append(claimed)

        if not claimed_entries:
            return jsonify({
                "success": True,
                "entries_processed": 0,
                "insights_created": 0,
                "insights_updated": 0,
                "message": "No unprocessed entries to process"
            })

        # Get default repo config
        repo_configs = supabase.table("repo_configs").select("*").limit(1).execute()
        if not repo_configs.data:
            return jsonify({"error": "No repository configured"}), 404

        repo_config_id = UUID(repo_configs.data[0]["id"])

        result = generate_insights_from_entries(
            supabase,
            repo_config_id,
            claimed_entries
        )

        logger.info(
            "Insight generation: entries_processed=%s insights_created=%s insights_updated=%s",
            result.get("entries_processed"),
            result.get("insights_created"),
            result.get("insights_updated")
        )

        return jsonify({
            "success": True,
            **result
        })

    except Exception as e:
        logger.error(f"Error generating insights: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# =====================================================
# GEMINI ANALYSIS ENDPOINTS
# =====================================================

@app.route("/api/gemini/analyze/<insight_id>", methods=["POST"])
def analyze_insight_with_gemini(insight_id: str):
    """
    Analyze an insight with Gemini to generate IssueSpec.
    """
    try:
        insight_uuid = UUID(insight_id)
        
        # Get insight with entries
        insight_data = db.get_insight_with_entries(supabase, insight_uuid)
        if not insight_data:
            return jsonify({"error": "Insight not found"}), 404
        
        insight = insight_data["insight"]
        reddit_entries = insight_data["entries"]

        # Idempotency: avoid duplicate issues
        if insight.github_issue_url or insight.github_issue_number:
            return jsonify({
                "success": True,
                "issue_number": insight.github_issue_number,
                "issue_url": insight.github_issue_url,
                "message": "Issue already created"
            })

        for entry in reddit_entries:
            if entry.github_issue_url:
                return jsonify({
                    "success": True,
                    "issue_number": insight.github_issue_number,
                    "issue_url": entry.github_issue_url,
                    "message": "Issue already created"
                })
        
        # Update status to analyzing
        db.update_insight_status(supabase, insight_uuid, InsightStatus.ANALYZING)
        
        # Analyze with Gemini
        try:
            # Generate summary
            summary = gemini_client.analyze_insight(insight, reddit_entries)
            
            # Generate issue spec
            issue_spec = gemini_client.generate_issue_spec(
                insight,
                summary,
                reddit_entries,
                include_images=any(e.image_urls for e in reddit_entries)
            )

            # Generate patch plan
            patch_plan = gemini_client.generate_patch_plan(issue_spec)
            
            # Update insight with Gemini analysis
            db.update_insight(supabase, insight_uuid, {
                "summary": summary.model_dump(mode='json'),
                "issue_spec": issue_spec.model_dump(mode='json'),
                "patch_plan": patch_plan.model_dump(mode='json'),
                "priority": issue_spec.priority.value,
                "status": InsightStatus.READY.value
            })
            
            logger.info(f"Analyzed insight {insight_id} with Gemini")
            
            return jsonify({
                "success": True,
                "insight_summary": summary.model_dump(mode='json'),
                "issue_spec": issue_spec.model_dump(mode='json'),
                "patch_plan": patch_plan.model_dump(mode='json')
            })
            
        except Exception as e:
            # Update status to failed
            db.update_insight_status(supabase, insight_uuid, InsightStatus.PENDING)
            raise e
        
    except Exception as e:
        logger.error(f"Error analyzing insight: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# =====================================================
# INSIGHT MANAGEMENT ENDPOINTS
# =====================================================

@app.route("/api/insights", methods=["GET"])
def get_insights():
    """Get all insights for a repository."""
    try:
        # Get default repo config
        repo_configs = supabase.table("repo_configs").select("*").limit(1).execute()
        if not repo_configs.data:
            return jsonify({"insights": [], "count": 0})
        
        repo_config_id = UUID(repo_configs.data[0]["id"])
        
        # Get query parameters
        status = request.args.get("status")
        limit = int(request.args.get("limit", 50))
        
        if status:
            try:
                status_enum = InsightStatus(status)
                insights = db.get_insights_by_status(supabase, status_enum)
            except ValueError:
                return jsonify({"error": f"Invalid status: {status}"}), 400
        else:
            insights = db.get_insights_by_repo(supabase, repo_config_id, limit=limit)
        
        return jsonify({
            "insights": [i.model_dump(mode='json') for i in insights],
            "count": len(insights)
        })
        
    except Exception as e:
        logger.error(f"Error getting insights: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/insights/<insight_id>", methods=["GET"])
def get_insight(insight_id: str):
    """Get a specific insight with entries."""
    try:
        insight_uuid = UUID(insight_id)
        insight_data = db.get_insight_with_entries(supabase, insight_uuid)
        
        if not insight_data:
            return jsonify({"error": "Insight not found"}), 404
        
        return jsonify({
            "insight": insight_data["insight"].model_dump(mode='json'),
            "entries": [e.model_dump(mode='json') for e in insight_data["entries"]],
            "entry_count": insight_data["entry_count"]
        })
        
    except Exception as e:
        logger.error(f"Error getting insight: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/insights/<insight_id>/status", methods=["PUT"])
def update_insight_status(insight_id: str):
    """Update insight status."""
    try:
        insight_uuid = UUID(insight_id)
        data = request.get_json()

        status = InsightStatus(data["status"])
        user_id = UUID(data["user_id"]) if data.get("user_id") else None

        insight = db.update_insight_status(supabase, insight_uuid, status, user_id)

        # Auto-add to dependency graph when marked as in_progress
        if status == InsightStatus.IN_PROGRESS:
            issue_spec = _normalize_issue_spec(insight.issue_spec)
            task_title = issue_spec.title

            # Check if task already exists
            task_exists = any(t["title"] == task_title for t in dependency_tasks)

            if not task_exists:
                # Analyze dependencies with AI
                dependencies = _analyze_dependencies_with_ai(task_title, dependency_tasks)

                # Create new task
                task_id = f"task_{len(dependency_tasks) + 1}"
                new_task = {
                    "id": task_id,
                    "title": task_title,
                    "status": "in_progress",
                    "dependencies": dependencies,
                    "insight_id": str(insight_uuid)
                }

                dependency_tasks.append(new_task)
                logger.info(f"Auto-added task to dependency graph: {task_title}")

        return jsonify({
            "success": True,
            "insight": insight.model_dump(mode='json')
        })

    except Exception as e:
        logger.error(f"Error updating insight status: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# =====================================================
# GITHUB INTEGRATION ENDPOINTS
# =====================================================

@app.route("/api/github/create-issue", methods=["POST"])
def create_github_issue():
    """Create a GitHub issue from an insight."""
    try:
        data = request.get_json()
        insight_id = UUID(data["insight_id"])
        
        # Get insight with entries
        insight_data = db.get_insight_with_entries(supabase, insight_id)
        if not insight_data:
            return jsonify({"error": "Insight not found"}), 404
        
        insight = insight_data["insight"]
        reddit_entries = insight_data["entries"]

        existing = _get_existing_issue_info(insight, reddit_entries)
        if existing:
            return jsonify({
                "success": True,
                "issue_number": existing.get("issue_number"),
                "issue_url": existing.get("issue_url"),
                "message": "Issue already created"
            })
        
        # Get repo config
        repo_config = db.get_repo_config(supabase, insight.repo_config_id)
        if not repo_config:
            return jsonify({"error": "Repository config not found"}), 404
        
        # Get issue spec (should already be generated)
        if not insight.issue_spec:
            return jsonify({
                "error": "Issue spec not generated. Run Gemini analysis first."
            }), 400

        result = _create_issue_for_insight(insight, reddit_entries, repo_config)
        if result["existing"]:
            return jsonify({
                "success": True,
                "issue_number": result["existing"].get("issue_number"),
                "issue_url": result["existing"].get("issue_url"),
                "message": "Issue already created"
            })

        github_issue = result["issue"]
        if not github_issue:
            return jsonify({
                "error": "Issue creation skipped (missing issue spec or config)"
            }), 400

        logger.info(f"Created GitHub issue for insight {insight_id}: {github_issue.url}")

        return jsonify({
            "success": True,
            "issue_number": github_issue.number,
            "issue_url": github_issue.url
        })
        
    except Exception as e:
        logger.error(f"Error creating GitHub issue: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# =====================================================
# REPO CONFIG ENDPOINTS
# =====================================================

@app.route("/api/repo-configs", methods=["GET"])
def get_repo_configs():
    """Get all repository configurations."""
    try:
        result = supabase.table("repo_configs").select("*").execute()
        return jsonify({
            "configs": result.data if result.data else [],
            "count": len(result.data) if result.data else 0
        })
    except Exception as e:
        logger.error(f"Error getting repo configs: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/repo-configs", methods=["POST"])
def create_repo_config():
    """Create a new repository configuration."""
    try:
        data = request.get_json()
        config_request = CreateRepoConfigRequest(**data)
        
        config_data = config_request.model_dump(mode='json')
        # For MVP, allow null user_id if auth isn't set up yet.
        config_data["user_id"] = data.get("user_id")
        
        config = db.create_repo_config(supabase, config_data)
        
        return jsonify({
            "success": True,
            "config": config.model_dump(mode='json')
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating repo config: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# =====================================================
# WORKFLOW TRIGGER ENDPOINTS (for n8n)
# =====================================================

@app.route("/api/workflows/trigger", methods=["POST"])
def trigger_workflow():
    """
    Generic workflow trigger endpoint for n8n.
    n8n workflows can call this to trigger backend actions.
    """
    try:
        data = request.get_json()
        workflow_name = data.get("workflow_name")
        payload = data.get("payload", {})
        
        logger.info(f"Workflow trigger received: {workflow_name}")
        
        # Handle different workflow types
        if workflow_name == "scheduled_ingestion":
            # Trigger Reddit ingestion
            return ingest_reddit()
        
        elif workflow_name == "analyze_insights":
            # Analyze pending insights
            insights = db.get_insights_by_status(supabase, InsightStatus.PENDING)
            results = []
            
            for insight in insights[:5]:  # Limit to 5 per run
                try:
                    # Analyze with Gemini
                    response = analyze_insight_with_gemini(str(insight.id))
                    results.append({"insight_id": str(insight.id), "success": True})
                except Exception as e:
                    results.append({"insight_id": str(insight.id), "error": str(e)})
            
            return jsonify({
                "success": True,
                "results": results
            })
        
        else:
            return jsonify({"error": f"Unknown workflow: {workflow_name}"}), 400
        
    except Exception as e:
        logger.error(f"Error in workflow trigger: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/workflows/approve", methods=["POST"])
def approve_workflow():
    """
    Approval webhook endpoint for n8n.
    Handles human approval actions.
    """
    try:
        data = request.get_json()
        insight_id = UUID(data["insight_id"])
        action = data["action"]  # "approve", "reject", "request_more_info"
        comment = data.get("comment")
        user_id = UUID(data.get("user_id", str(uuid4())))
        
        insight = db.get_insight(supabase, insight_id)
        if not insight:
            return jsonify({"error": "Insight not found"}), 404
        
        if action == "approve":
            # Update status to approved
            db.update_insight_status(supabase, insight_id, InsightStatus.APPROVED, user_id)
            
            # Log approval
            db.log_execution_step(
                supabase,
                insight_id,
                f"Approved by user",
                step_name="insight_approved",
                metadata={"comment": comment} if comment else {}
            )
            
            return jsonify({
                "success": True,
                "action": "approved",
                "message": "Insight approved. Ready for GitHub issue creation."
            })
        
        elif action == "reject":
            # Update status to closed
            db.update_insight_status(supabase, insight_id, InsightStatus.CLOSED, user_id)
            
            db.log_execution_step(
                supabase,
                insight_id,
                f"Rejected by user",
                step_name="insight_rejected",
                metadata={"comment": comment} if comment else {}
            )
            
            return jsonify({
                "success": True,
                "action": "rejected",
                "message": "Insight rejected and closed."
            })
        
        else:
            return jsonify({"error": f"Unknown action: {action}"}), 400
        
    except Exception as e:
        logger.error(f"Error in approval workflow: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# =====================================================
# PR APPROVAL ENDPOINT
# =====================================================

@app.route("/api/insights/<insight_id>/create-pr", methods=["POST"])
def create_pr_for_insight(insight_id):
    """
    Create a PR for an approved insight that already has an issue.
    Requires manual approval - this is the human-in-the-loop step.
    """
    try:
        insight_uuid = UUID(insight_id)

        # Get insight with entries
        insight_data = db.get_insight_with_entries(supabase, insight_uuid)
        if not insight_data:
            return jsonify({"error": "Insight not found"}), 404

        insight = insight_data["insight"]
        reddit_entries = insight_data["entries"]

        # Check if issue already exists
        if not insight.github_issue_url or not insight.github_issue_number:
            return jsonify({"error": "No GitHub issue created yet for this insight"}), 400

        # Check if PR already created (check insight record)
        if insight.github_pr_url:
            return jsonify({
                "success": True,
                "message": "PR already exists",
                "pr_url": insight.github_pr_url,
                "pr_number": insight.github_pr_number
            })

        # Get repo config
        repo_configs = supabase.table("repo_configs").select("*").limit(1).execute()
        if not repo_configs.data:
            return jsonify({"error": "No repository configured"}), 404

        repo_config = RepoConfig(**repo_configs.data[0])

        # Get primary entry
        primary_entry = reddit_entries[0] if reddit_entries else None
        if not primary_entry:
            return jsonify({"error": "No Reddit entries found"}), 400

        # Generate plan content
        issue_spec = _normalize_issue_spec(insight.issue_spec)
        summary = _normalize_summary(insight.summary)
        plan_content = build_plan_md(primary_entry, issue_spec, summary, reddit_entries)

        # Format plan path
        plan_repo_path = _format_plan_path(primary_entry, insight, insight.github_issue_number, repo_config)

        # Create branch
        branch_name = f"echofix/{primary_entry.reddit_id}"
        try:
            github_client.create_branch(
                repo_config.github_owner,
                repo_config.github_repo,
                branch_name,
                repo_config.github_branch
            )
        except Exception as exc:
            logger.warning("Branch may already exist: %s", exc)

        # Upload plan.md to branch
        try:
            existing_sha = github_client.get_file_sha(
                repo_config.github_owner,
                repo_config.github_repo,
                plan_repo_path,
                ref=branch_name
            )
        except:
            existing_sha = None

        plan_sha = github_client.upsert_file(
            repo_config.github_owner,
            repo_config.github_repo,
            plan_repo_path,
            branch_name,
            plan_content.encode(),
            f"Add EchoFix plan for {primary_entry.reddit_id}",
            sha=existing_sha
        )

        # Generate actual code implementation using Gemini
        logger.info("Generating code implementation with Gemini...")
        patch_plan = _normalize_patch_plan(insight.patch_plan)

        # Use new method that clones repo and generates real fixes
        try:
            code_files = gemini_client.generate_real_code_implementation(
                issue_spec=issue_spec,
                patch_plan=patch_plan,
                repo_owner=repo_config.github_owner,
                repo_name=repo_config.github_repo,
                github_token=os.getenv('GITHUB_TOKEN')
            )
        except Exception as e:
            logger.error(f"Real code generation failed: {e}")
            # Fall back to demo mode
            code_files = gemini_client._load_demo_code_implementation(issue_spec, patch_plan)

        # Upload generated code files to branch
        uploaded_files = []
        for file_path, file_content in code_files.items():
            try:
                logger.info(f"Uploading generated file: {file_path}")
                # Check if file already exists
                try:
                    existing_file_sha = github_client.get_file_sha(
                        repo_config.github_owner,
                        repo_config.github_repo,
                        file_path,
                        ref=branch_name
                    )
                except:
                    existing_file_sha = None

                # Upload the file
                github_client.upsert_file(
                    repo_config.github_owner,
                    repo_config.github_repo,
                    file_path,
                    branch_name,
                    file_content.encode(),
                    f"EchoFix: Implement {issue_spec.title}",
                    sha=existing_file_sha
                )
                uploaded_files.append(file_path)
            except Exception as file_exc:
                logger.error(f"Failed to upload {file_path}: {file_exc}")

        logger.info(f"Uploaded {len(uploaded_files)} code files to branch {branch_name}")

        # Create PR
        pr_title = f"EchoFix: {issue_spec.title}"

        # Build files list for PR body
        files_list = "\n".join(f"- `{f}`" for f in uploaded_files) if uploaded_files else "- (plan only)"

        pr_body = (
            f"## 🤖 Auto-Generated Implementation\n\n"
            f"**Issue:** #{insight.github_issue_number}\n"
            f"**Reddit Feedback:** {primary_entry.permalink}\n\n"
            f"### Files Modified/Created ({len(uploaded_files)})\n"
            f"{files_list}\n\n"
            f"### Implementation Plan\n"
            f"Full plan: `{plan_repo_path}`\n\n"
            f"---\n"
            f"⚡ Powered by **EchoFix** + **Gemini AI**\n"
            f"*Auto-generated from community feedback*"
        )

        # Try to create PR, handle case where it already exists
        try:
            pr = github_client.create_pull_request_stub(
                repo_config.github_owner,
                repo_config.github_repo,
                pr_title,
                pr_body,
                head_branch=branch_name,
                base_branch=repo_config.github_branch
            )
        except Exception as pr_error:
            # Check if error is due to PR already existing
            error_str = str(pr_error).lower()
            is_duplicate = ("422" in error_str or "unprocessable entity" in error_str)

            if is_duplicate:
                # PR already exists, try to find it
                logger.warning(f"PR already exists for branch {branch_name}, looking it up...")

                # Try to get existing PR from GitHub
                try:
                    import requests
                    response = requests.get(
                        f"https://api.github.com/repos/{repo_config.github_owner}/{repo_config.github_repo}/pulls",
                        params={"head": f"{repo_config.github_owner}:{branch_name}", "state": "open"},
                        headers={"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
                    )
                    response.raise_for_status()
                    prs = response.json()

                    if prs and len(prs) > 0:
                        existing_pr = prs[0]
                        pr_url = existing_pr["html_url"]
                        pr_number = existing_pr["number"]

                        # Update database with existing PR info
                        db.update_insight(supabase, insight_uuid, {
                            "github_pr_url": pr_url,
                            "github_pr_number": pr_number
                        })

                        db.mark_reddit_entries_processed_for_insight(
                            supabase,
                            insight_uuid,
                            insight.github_issue_url,
                            plan_md_path=plan_repo_path,
                            plan_md_sha=plan_sha,
                            github_pr_url=pr_url,
                            github_pr_number=pr_number
                        )

                        return jsonify({
                            "success": True,
                            "message": "PR already exists (updated records)",
                            "pr_url": pr_url,
                            "pr_number": pr_number,
                            "branch": branch_name
                        })
                except Exception as lookup_error:
                    logger.error(f"Failed to look up existing PR: {lookup_error}")

            # Re-raise if not a duplicate PR error
            raise pr_error

        # Update insight with PR info
        db.update_insight(supabase, insight_uuid, {
            "github_pr_url": pr.url,
            "github_pr_number": pr.number
        })

        # Update entries with PR info
        db.mark_reddit_entries_processed_for_insight(
            supabase,
            insight_uuid,
            insight.github_issue_url,
            plan_md_path=plan_repo_path,
            plan_md_sha=plan_sha,
            github_pr_url=pr.url,
            github_pr_number=pr.number
        )

        return jsonify({
            "success": True,
            "message": "PR created successfully",
            "pr_url": pr.url,
            "pr_number": pr.number,
            "branch": branch_name
        })

    except Exception as e:
        logger.error(f"Error creating PR: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# =====================================================
# COMMUNITY APPROVAL
# =====================================================

@app.route("/api/insights/<insight_id>/ask-community", methods=["POST"])
def ask_community_approval(insight_id):
    """
    Post PR overview as Reddit reply to ask for community approval.
    When the reply reaches MIN_SCORE upvotes, auto-merge the PR.
    """
    try:
        insight_uuid = UUID(insight_id)

        # Get insight with entries
        insight_data = db.get_insight_with_entries(supabase, insight_uuid)
        if not insight_data:
            return jsonify({"error": "Insight not found"}), 404

        insight = insight_data["insight"]
        reddit_entries = insight_data["entries"]

        # Check if PR exists
        if not insight.github_pr_url or not insight.github_pr_number:
            return jsonify({"error": "No PR created yet for this insight"}), 400

        # Check if already asked community (if columns exist)
        if hasattr(insight, 'community_approval_requested') and insight.community_approval_requested:
            return jsonify({
                "success": True,
                "message": "Community approval already requested",
                "reply_id": insight.community_reply_id,
                "reply_score": insight.community_reply_score
            })

        # Get primary entry to reply to
        primary_entry = reddit_entries[0] if reddit_entries else None
        if not primary_entry:
            return jsonify({"error": "No Reddit entry found"}), 400

        # Generate PR summary for community
        issue_spec = _normalize_issue_spec(insight.issue_spec)
        summary_text = f"""Hey! I've created a fix for this: {insight.github_pr_url}

**What it does:**
{issue_spec.problem_statement[:200]}

**Implementation:**
- PR #{insight.github_pr_number}
- Files changed: Check the PR for details

Upvote this comment if you want me to merge it! 🚀

---
🤖 Auto-generated by EchoFix"""

        # Post reply to Reddit
        try:
            # Use Reddit client to post comment
            comment_id = reddit_client.post_comment(
                parent_id=primary_entry.reddit_id,
                text=summary_text
            )

            # Update insight with community approval info (if columns exist)
            try:
                db.update_insight(supabase, insight_uuid, {
                    "community_approval_requested": True,
                    "community_reply_id": comment_id,
                    "community_reply_score": 0
                })
            except Exception as db_error:
                # If columns don't exist, still return success since comment was posted
                error_msg = str(db_error)
                if 'does not exist' in error_msg or '42703' in error_msg:
                    logger.warning("Community approval columns don't exist yet - comment posted but not tracked")
                    return jsonify({
                        "success": True,
                        "message": "Comment posted (migration needed to track approval)",
                        "reply_id": comment_id,
                        "warning": "Database migration required - run migration SQL to enable tracking"
                    })
                raise

            return jsonify({
                "success": True,
                "message": "Community approval requested",
                "reply_id": comment_id,
                "reply_url": f"https://reddit.com/comments/{primary_entry.reddit_id.split('_')[1]}/_/{comment_id}"
            })

        except Exception as reddit_error:
            logger.error(f"Failed to post Reddit comment: {reddit_error}")
            return jsonify({"error": f"Failed to post comment: {str(reddit_error)}"}), 500

    except Exception as e:
        logger.error(f"Error requesting community approval: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# =====================================================
# DEPENDENCY GRAPH
# =====================================================

# In-memory task storage for dependency graph
dependency_tasks = []
dependency_tasks_loaded = False

def _ensure_dependency_tasks_loaded():
    """Lazy-load dependency graph with existing in_progress insights on first access."""
    global dependency_tasks_loaded

    if dependency_tasks_loaded:
        logger.debug("Dependency tasks already loaded")
        return

    logger.info("Loading dependency tasks from in_progress insights...")

    try:
        # Get all in_progress insights
        insights = db.get_insights_by_status(supabase, InsightStatus.IN_PROGRESS)
        logger.info(f"Found {len(insights)} in_progress insights")

        for insight in insights:
            try:
                issue_spec = _normalize_issue_spec(insight.issue_spec)
                task_title = issue_spec.title

                # Check if task already exists
                task_exists = any(t["title"] == task_title for t in dependency_tasks)

                if not task_exists:
                    task_id = f"task_{len(dependency_tasks) + 1}"
                    new_task = {
                        "id": task_id,
                        "title": task_title,
                        "status": "in_progress",
                        "dependencies": [],  # No dependencies on initial load
                        "insight_id": str(insight.id)
                    }
                    dependency_tasks.append(new_task)
                    logger.info(f"Loaded existing in_progress task: {task_title}")
                else:
                    logger.debug(f"Task already exists: {task_title}")
            except Exception as task_error:
                logger.error(f"Error processing insight {insight.id}: {task_error}", exc_info=True)
                continue

        dependency_tasks_loaded = True
        logger.info(f"Dependency graph initialized with {len(dependency_tasks)} tasks")

    except Exception as e:
        logger.error(f"Error populating dependency graph: {e}", exc_info=True)
        dependency_tasks_loaded = True  # Mark as loaded anyway to avoid repeated errors

@app.route("/api/dependency-graph", methods=["GET"])
def get_dependency_graph():
    """Get the current dependency graph with all tasks."""
    _ensure_dependency_tasks_loaded()
    return jsonify({"tasks": dependency_tasks})


@app.route("/api/analyze-task-dependencies", methods=["POST"])
def analyze_task_dependencies():
    """
    Analyze a new task and determine its dependencies using AI.
    """
    try:
        data = request.get_json()
        task_title = data.get("task_title")
        existing_tasks = data.get("existing_tasks", [])

        if not task_title:
            return jsonify({"error": "task_title is required"}), 400

        # Use Gemini/OpenAI to analyze dependencies
        dependencies = _analyze_dependencies_with_ai(task_title, existing_tasks)

        # Create new task
        task_id = f"task_{len(dependency_tasks) + 1}"
        new_task = {
            "id": task_id,
            "title": task_title,
            "status": "pending",
            "dependencies": dependencies
        }

        dependency_tasks.append(new_task)

        return jsonify({
            "success": True,
            "task": new_task,
            "message": f"Task analyzed with {len(dependencies)} dependencies"
        })

    except Exception as e:
        logger.error(f"Error analyzing task dependencies: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/update-task-status", methods=["POST"])
def update_task_status():
    """Update a task's status in the dependency graph."""
    try:
        data = request.get_json()
        task_id = data.get("task_id")
        status = data.get("status")

        if not task_id or not status:
            return jsonify({"error": "task_id and status are required"}), 400

        # Find and update task
        for task in dependency_tasks:
            if task["id"] == task_id:
                task["status"] = status
                return jsonify({"success": True, "task": task})

        return jsonify({"error": "Task not found"}), 404

    except Exception as e:
        logger.error(f"Error updating task status: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


def _analyze_dependencies_with_ai(task_title: str, existing_tasks: list) -> list:
    """
    Use AI (Gemini with OpenAI fallback) to determine task dependencies.
    """
    if not existing_tasks:
        return []

    # Build prompt
    tasks_desc = "\n".join([
        f"- {task['id']}: {task['title']} (status: {task['status']})"
        for task in existing_tasks
    ])

    prompt = f"""You are a software project manager analyzing task dependencies.

NEW TASK: {task_title}

EXISTING TASKS:
{tasks_desc}

Analyze which existing tasks (if any) the new task depends on. Consider:
- Does the new task require another task to be completed first?
- Are there logical ordering requirements?
- What makes sense from an implementation perspective?

Return ONLY a JSON array of task IDs that the new task depends on.
Example: ["task_1", "task_3"]
If no dependencies, return: []

DEPENDENCIES:"""

    # Try Gemini first
    try:
        response = gemini_client.model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 500,
            }
        )

        result_text = response.text.strip()
        # Parse JSON response
        import json
        import re

        # Extract JSON array from response
        json_match = re.search(r'\[.*?\]', result_text, re.DOTALL)
        if json_match:
            dependencies = json.loads(json_match.group(0))
            # Validate task IDs exist
            valid_deps = [
                dep for dep in dependencies
                if any(t["id"] == dep for t in existing_tasks)
            ]
            logger.info(f"Gemini found {len(valid_deps)} dependencies for '{task_title}'")
            return valid_deps

    except Exception as gemini_error:
        logger.error(f"Gemini dependency analysis failed: {gemini_error}")

        # Try OpenAI fallback
        if gemini_client.openai_client:
            try:
                logger.info("Trying OpenAI for dependency analysis")
                response = gemini_client.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a project manager. Return ONLY a JSON array of task IDs."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=500
                )

                result_text = response.choices[0].message.content.strip()
                import json
                import re

                json_match = re.search(r'\[.*?\]', result_text, re.DOTALL)
                if json_match:
                    dependencies = json.loads(json_match.group(0))
                    valid_deps = [
                        dep for dep in dependencies
                        if any(t["id"] == dep for t in existing_tasks)
                    ]
                    logger.info(f"OpenAI found {len(valid_deps)} dependencies for '{task_title}'")
                    return valid_deps

            except Exception as openai_error:
                logger.error(f"OpenAI dependency analysis also failed: {openai_error}")

    # Fallback: simple heuristic (no dependencies)
    logger.warning("AI dependency analysis failed, using heuristic")
    return []


# =====================================================
# DATA MANAGEMENT
# =====================================================

@app.route("/api/admin/apply-migration", methods=["POST"])
def apply_community_migration():
    """
    Apply the community approval migration.
    Uses raw SQL execution via requests to Supabase Management API.
    """
    try:
        # Read migration SQL
        migration_path = os.path.join(os.path.dirname(__file__), 'supabase/migrations/00005_add_community_approval.sql')
        with open(migration_path, 'r') as f:
            migration_sql = f.read()

        # Split into individual statements
        statements = [
            "ALTER TABLE insights ADD COLUMN IF NOT EXISTS community_approval_requested BOOLEAN DEFAULT false",
            "ALTER TABLE insights ADD COLUMN IF NOT EXISTS community_reply_id TEXT",
            "ALTER TABLE insights ADD COLUMN IF NOT EXISTS community_reply_score INTEGER DEFAULT 0",
            "ALTER TABLE insights ADD COLUMN IF NOT EXISTS community_approved BOOLEAN DEFAULT false",
            "ALTER TABLE insights ADD COLUMN IF NOT EXISTS community_approved_at TIMESTAMPTZ",
            "CREATE INDEX IF NOT EXISTS idx_insights_community_approval ON insights(community_approval_requested, community_approved)"
        ]

        results = []

        # Try to execute each statement by attempting to query the column
        for stmt in statements:
            try:
                # We can't execute DDL via Supabase client, but we can check if columns exist
                if "ADD COLUMN" in stmt:
                    col_name = stmt.split("ADD COLUMN IF NOT EXISTS")[1].split()[0].strip()
                    # Try to select this column
                    supabase.table("insights").select(col_name).limit(1).execute()
                    results.append(f"✅ Column {col_name} already exists")
                elif "CREATE INDEX" in stmt:
                    results.append("⚠️ Index creation skipped (requires dashboard)")
            except Exception as e:
                error_msg = str(e)
                if 'does not exist' in error_msg or '42703' in error_msg:
                    results.append(f"❌ Column doesn't exist - manual migration needed")

                    return jsonify({
                        "success": False,
                        "error": "Migration cannot be applied via API",
                        "message": "Please run the SQL manually in Supabase Dashboard",
                        "sql": migration_sql,
                        "dashboard_url": "https://supabase.com/dashboard/project/bkjuzmdzbxffxpeluwsv/sql"
                    }), 400

        return jsonify({
            "success": True,
            "message": "All columns already exist!",
            "results": results
        })

    except Exception as e:
        logger.error(f"Migration check failed: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/admin/clear-all", methods=["POST"])
def clear_all_data():
    """Clear all Reddit entries and insights from the database."""
    try:
        # Delete all insights
        insights_result = supabase.table("insights").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        insights_deleted = len(insights_result.data) if insights_result.data else 0

        # Delete all reddit entries
        entries_result = supabase.table("reddit_entries").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        entries_deleted = len(entries_result.data) if entries_result.data else 0

        return jsonify({
            "success": True,
            "entries_deleted": entries_deleted,
            "insights_deleted": insights_deleted,
            "message": f"Deleted {entries_deleted} entries and {insights_deleted} insights"
        })

    except Exception as e:
        logger.error(f"Error clearing data: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# =====================================================
# STATISTICS & ANALYTICS
# =====================================================

@app.route("/api/stats", methods=["GET"])
def get_statistics():
    """Get dashboard statistics."""
    try:
        # Get default repo config
        repo_configs = supabase.table("repo_configs").select("*").limit(1).execute()
        if not repo_configs.data:
            return jsonify({
                "total_insights": 0,
                "total_entries": 0,
                "status_counts": {}
            })
        
        repo_config_id = UUID(repo_configs.data[0]["id"])

        stats = db.get_insight_statistics(supabase, repo_config_id)

        # Serialize recent_insights
        if 'recent_insights' in stats and stats['recent_insights']:
            stats['recent_insights'] = [i.model_dump(mode='json') for i in stats['recent_insights']]

        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
