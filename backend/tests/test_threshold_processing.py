import unittest
from datetime import datetime, timezone
from uuid import uuid4

from models import RedditEntry, RedditEntryStatus
from services.reddit_json_client import RedditJSONClient
from services.score_threshold import (
    determine_entry_status,
    should_process_entry
)


def _make_entry(status: RedditEntryStatus, score=None, github_issue_url=None):
    return RedditEntry(
        id=uuid4(),
        created_at=datetime.now(timezone.utc),
        reddit_id="abc123",
        reddit_type="post",
        title="Test",
        body="Body",
        author="user",
        subreddit="test",
        permalink="https://reddit.com/r/test/comments/abc123/test",
        score=score,
        num_comments=0,
        image_urls=[],
        video_url=None,
        processed=False,
        status=status,
        last_score_check_at=None,
        processed_at=None,
        github_issue_url=github_issue_url,
        unwrap_entry_id=None,
        insight_id=None,
        reddit_created_at=datetime.now(timezone.utc)
    )


class ThresholdProcessingTests(unittest.TestCase):
    def test_score_below_threshold_stays_pending(self):
        status = determine_entry_status(score=1, min_score=2)
        self.assertEqual(status, RedditEntryStatus.PENDING)
        entry = _make_entry(RedditEntryStatus.PENDING, score=1)
        self.assertFalse(should_process_entry(entry))

    def test_score_meets_threshold_triggers_once(self):
        status = determine_entry_status(score=2, min_score=2)
        self.assertEqual(status, RedditEntryStatus.READY)
        entry = _make_entry(RedditEntryStatus.READY, score=2)
        self.assertTrue(should_process_entry(entry))

        already_linked = _make_entry(
            RedditEntryStatus.READY,
            score=3,
            github_issue_url="https://github.com/org/repo/issues/2"
        )
        self.assertFalse(should_process_entry(already_linked))

        processed_entry = _make_entry(
            RedditEntryStatus.PROCESSED,
            score=2,
            github_issue_url="https://github.com/org/repo/issues/1"
        )
        self.assertFalse(should_process_entry(processed_entry))

    def test_null_score_then_enrichment_flips_ready(self):
        status_pending = determine_entry_status(score=None, min_score=2)
        self.assertEqual(status_pending, RedditEntryStatus.PENDING)
        client = RedditJSONClient(user_agent="EchoFixTest/1.0")
        payload = [
            {"data": {"children": [{"data": {"id": "abc123", "score": 5}}]}},
            {"data": {"children": []}}
        ]
        score = client._extract_score(payload, "abc123")
        self.assertEqual(score, 5)
        status_ready = determine_entry_status(score=score, min_score=2)
        self.assertEqual(status_ready, RedditEntryStatus.READY)


if __name__ == "__main__":
    unittest.main()
