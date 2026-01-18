"""
Plan-of-attack generator for READY Reddit entries.
"""

import os
import re
from collections import Counter
from datetime import datetime, timezone
from typing import List, Optional

from models import RedditEntry, IssueSpec, Insight, InsightSummary


def _extract_keywords(text: str, limit: int = 5) -> List[str]:
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    counts = Counter(words)
    return [word for word, _ in counts.most_common(limit)]


def build_plan_md(
    entry: RedditEntry,
    issue_spec: IssueSpec,
    summary: InsightSummary,
    reddit_entries: Optional[List[RedditEntry]] = None
) -> str:
    """
    Generate a markdown plan for a Reddit entry.
    """
    reddit_entries = reddit_entries or []
    keywords = _extract_keywords(" ".join([
        entry.title or "",
        entry.body,
        issue_spec.problem_statement,
        issue_spec.expected_behavior
    ]))

    evidence_lines = []
    evidence_lines.append(f"- Score: **{entry.score or 0}** upvotes")
    evidence_lines.append(f"- Author: {entry.author}")
    evidence_lines.append(f"- Subreddit: {entry.subreddit}")
    evidence_lines.append(f"- Link: {entry.permalink}")

    for extra in reddit_entries[:2]:
        evidence_lines.append(f"- Related comment: [{extra.permalink}]({extra.permalink}) ({extra.score or 0} upvotes)")

    fix_steps = issue_spec.suggested_fix_steps.split("\n") if issue_spec.suggested_fix_steps else []
    if not fix_steps:
        fix_steps = issue_spec.acceptance_criteria or []

    plan_lines = [
        f"# Plan: {issue_spec.title}",
        "",
        f"_Generated for Reddit entry `{entry.reddit_id}` on {datetime.now(timezone.utc).isoformat()}_",
        "",
        "## Overview",
        f"- **Problem**: {issue_spec.problem_statement}",
        f"- **Why it matters**: {issue_spec.user_impact or summary.user_impact or 'User impact TBD.'}",
        "",
        "## Evidence",
        *evidence_lines,
        "",
        "## Observed Signals",
        f"- Keywords: {', '.join(keywords) or 'N/A'}",
        f"- Acceptance criteria: {len(issue_spec.acceptance_criteria)} items",
        "",
        "## Proposed Fix Approach",
    ]

    if fix_steps:
        plan_lines.extend([f"1. {step}" for step in fix_steps])
    else:
        plan_lines.append("1. Analyze logs & reproduce locally.")

    plan_lines.extend([
        "",
        "## Acceptance Criteria",
        *[f"- {criterion}" for criterion in issue_spec.acceptance_criteria],
        "",
        "## Risks & Edge Cases",
        f"- {issue_spec.suspected_root_cause or 'Risk details pending.'}",
        "",
        "## Owner Suggestions",
        f"- Suggested component: {summary.theme}",
        f"- Suggested priority: {issue_spec.priority.value}",
    ])

    return "\n".join(plan_lines)


def save_plan_md(content: str, plan_dir: str, reddit_entry_id: str) -> str:
    os.makedirs(plan_dir, exist_ok=True)
    path = os.path.join(plan_dir, f"{reddit_entry_id}.md")
    with open(path, "w", encoding="utf-8") as fp:
        fp.write(content)
    return path


def should_create_pr(entry: RedditEntry, enable_pr: bool) -> bool:
    if not enable_pr:
        return False
    return not bool(entry.github_pr_url)
