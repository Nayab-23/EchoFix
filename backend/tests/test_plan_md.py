import unittest
from datetime import datetime, timezone
from uuid import uuid4

from models import RedditEntry, IssueSpec, InsightSummary, Priority, RedditEntryStatus
from services.plan_md import build_plan_md, should_create_pr


def _make_entry():
    return RedditEntry(
        id=uuid4(),
        created_at=datetime.now(timezone.utc),
        reddit_id="abc123",
        reddit_type="post",
        title="Sample issue",
        body="The app crashes when uploading",
        author="test_user",
        subreddit="test",
        permalink="https://reddit.com/r/test/comments/abc123/sample",
        score=5,
        num_comments=3,
        image_urls=[],
        video_url=None,
        processed=False,
        status=RedditEntryStatus.PENDING,
        last_score_check_at=None,
        processed_at=None,
        github_issue_url=None,
        plan_md_path=None,
        plan_md_sha=None,
        github_pr_url=None,
        github_pr_number=None,
        unwrap_entry_id=None,
        insight_id=None,
        reddit_created_at=datetime.now(timezone.utc)
    )


class PlanMDTests(unittest.TestCase):
    def test_build_plan_contains_sections(self):
        entry = _make_entry()
        issue_spec = IssueSpec(
            title="Fix crash on upload",
            problem_statement="Uploading files above 5MB crashes",
            user_impact="Users cannot upload resources",
            steps_to_reproduce="1. Go to upload\n2. Select large file\n3. Submit",
            expected_behavior="Large files upload successfully",
            actual_behavior="Request fails with 500",
            acceptance_criteria=["Upload succeeds", "Error logged"],
            labels=["bug"],
            priority=Priority.HIGH,
            estimated_effort="M",
            suspected_root_cause="buffer overflow",
            suggested_fix_steps="1. Increase buffer\n2. Add streaming"
        )
        summary = InsightSummary(
            theme="Uploads",
            severity=Priority.HIGH,
            confidence=0.8,
            user_impact="Critical",
            evidence_count=2
        )
        plan = build_plan_md(entry, issue_spec, summary, [])
        self.assertIn("# Plan", plan)
        self.assertIn("## Proposed Fix Approach", plan)
        self.assertIn("## Acceptance Criteria", plan)

    def test_pr_idempotency(self):
        entry = _make_entry()
        entry.github_pr_url = "https://github.com/org/repo/pull/1"
        self.assertFalse(should_create_pr(entry, enable_pr=True))
        entry.github_pr_url = None
        self.assertTrue(should_create_pr(entry, enable_pr=True))
        self.assertFalse(should_create_pr(entry, enable_pr=False))


if __name__ == "__main__":
    unittest.main()
