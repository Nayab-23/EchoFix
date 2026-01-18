"""
Local insight generation for EchoFix.
Groups Reddit entries into simple themes without external services.
"""

import logging
from typing import List, Dict, Tuple, Any
from uuid import UUID

from models import RedditEntry, InsightStatus, RedditEntryStatus
import db

logger = logging.getLogger(__name__)


THEME_RULES = [
    {
        "theme": "Authentication Issues",
        "keywords": ["auth", "login", "log in", "sign in", "signin", "password", "2fa", "mfa", "oauth"],
        "description": "Users report login and authentication failures."
    },
    {
        "theme": "File Upload Issues",
        "keywords": ["upload", "file", "attachment", "import", "csv"],
        "description": "Users report problems uploading or importing files."
    },
    {
        "theme": "Dark Mode Requests",
        "keywords": ["dark mode", "dark theme", "night mode"],
        "description": "Users request a dark mode option."
    },
    {
        "theme": "Performance Issues",
        "keywords": ["slow", "lag", "performance", "timeout", "loading", "freeze"],
        "description": "Users report slowness or performance regressions."
    },
    {
        "theme": "UI/UX Issues",
        "keywords": ["ui", "ux", "layout", "button", "design", "navigation"],
        "description": "Users report usability or interface issues."
    }
]


def _classify_entry(entry: RedditEntry) -> Tuple[str, str]:
    """Assign a theme and description based on simple keyword matching."""
    text = f"{entry.title or ''}\n{entry.body}".lower()

    for rule in THEME_RULES:
        if any(keyword in text for keyword in rule["keywords"]):
            return rule["theme"], rule["description"]

    return "General Feedback", "Mixed feedback without a dominant theme yet."


def generate_insights_from_entries(
    supabase: Any,
    repo_config_id: UUID,
    entries: List[RedditEntry]
) -> Dict[str, Any]:
    """Create one insight per entry for specific, actionable feedback."""
    insights = []
    created_count = 0
    processed_count = 0

    for entry in entries:
        # Skip removed/deleted Reddit entries
        body_text = entry.body.strip()
        if body_text in ['[removed]', '[deleted]', '']:
            logger.info(f"Skipping removed/deleted entry: {entry.id}")
            continue

        # Use the actual comment text as the insight title for specificity
        # Truncate to first sentence or 100 chars
        first_sentence = body_text.split('.')[0] if '.' in body_text else body_text
        title = first_sentence[:100] + ('...' if len(first_sentence) > 100 else '')

        # Create one insight per entry for maximum specificity
        insight_data = {
            "theme": title,
            "description": body_text[:200] + ('...' if len(body_text) > 200 else ''),
            "entry_count": 1,
            "unwrap_groups": [],
            "repo_config_id": str(repo_config_id),
            "status": InsightStatus.PENDING.value
        }
        insight = db.create_insight(supabase, insight_data)
        created_count += 1

        # Link entry to insight
        db.update_reddit_entry(supabase, entry.id, {
            "insight_id": str(insight.id),
            "status": RedditEntryStatus.PROCESSING.value
        })
        processed_count += 1

        insights.append(insight)

    return {
        "entries_processed": processed_count,
        "insights_created": created_count,
        "insights_updated": 0,
        "insights": [i.model_dump(mode="json") for i in insights]
    }
