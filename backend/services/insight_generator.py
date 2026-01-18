"""
Local insight generation for EchoFix.
Groups Reddit entries into simple themes without external services.
"""

from typing import List, Dict, Tuple, Any
from uuid import UUID

from models import RedditEntry, InsightStatus, RedditEntryStatus
import db


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
    """Create or update insights and attach entries to them."""
    grouped: Dict[str, Dict[str, Any]] = {}

    for entry in entries:
        theme, description = _classify_entry(entry)
        group = grouped.setdefault(
            theme,
            {"description": description, "entries": []}
        )
        group["entries"].append(entry)

    insights = []
    created_count = 0
    updated_count = 0
    processed_count = 0

    for theme, group in grouped.items():
        existing = db.search_insights(supabase, repo_config_id, theme, limit=1)

        if existing:
            insight = existing[0]
            new_count = len(group["entries"])
            insight = db.update_insight(supabase, insight.id, {
                "description": group["description"],
                "entry_count": (insight.entry_count or 0) + new_count
            })
            updated_count += 1
        else:
            insight_data = {
                "theme": theme,
                "description": group["description"],
                "entry_count": len(group["entries"]),
                "unwrap_groups": [],
                "repo_config_id": str(repo_config_id),
                "status": InsightStatus.PENDING.value
            }
            insight = db.create_insight(supabase, insight_data)
            created_count += 1

        for entry in group["entries"]:
            db.update_reddit_entry(supabase, entry.id, {
                "insight_id": str(insight.id),
                "status": RedditEntryStatus.PROCESSING.value
            })
            processed_count += 1

        insights.append(insight)

    return {
        "entries_processed": processed_count,
        "insights_created": created_count,
        "insights_updated": updated_count,
        "insights": [i.model_dump(mode="json") for i in insights]
    }
