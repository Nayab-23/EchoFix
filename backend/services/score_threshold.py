"""
Helpers for score threshold gating and idempotent processing.
"""

from datetime import datetime, timezone
from typing import Optional

from models import RedditEntry, RedditEntryStatus


def determine_entry_status(score: Optional[int], min_score: int) -> RedditEntryStatus:
    """Return the entry status based on score and threshold."""
    if score is None:
        return RedditEntryStatus.PENDING
    return RedditEntryStatus.READY if score >= min_score else RedditEntryStatus.PENDING


def should_refresh_score(
    last_check_at: Optional[datetime],
    refresh_seconds: int
) -> bool:
    """Decide whether score should be refreshed based on last check time."""
    if last_check_at is None:
        return True
    elapsed = datetime.now(timezone.utc) - last_check_at
    return elapsed.total_seconds() >= refresh_seconds


def should_process_entry(entry: RedditEntry) -> bool:
    """Return True if the entry is eligible for processing."""
    if entry.github_issue_url:
        return False
    if entry.status in (RedditEntryStatus.PROCESSED, RedditEntryStatus.SKIPPED):
        return False
    return entry.status == RedditEntryStatus.READY
