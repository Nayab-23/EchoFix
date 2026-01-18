"""
GitHub integration for EchoFix.
Handles issue and PR creation using gh CLI.
"""

import subprocess
import json
import logging
import os
import base64
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)


@dataclass
class GitHubIssue:
    """GitHub issue data."""
    number: int
    title: str
    url: str
    state: str


@dataclass
class PullRequest:
    """Pull request data."""
    number: int
    url: str
    state: str


class GitHubClient:
    """
    Client for GitHub operations using gh CLI.
    Supports demo mode for testing without credentials.
    """
    
    def __init__(self, demo_mode: bool = False):
        """
        Initialize GitHub client.
        
        Args:
            demo_mode: If True, mock GitHub operations
        """
        self.demo_mode = demo_mode or os.getenv("DEMO_MODE", "false").lower() == "true"
        
        if not self.demo_mode:
            if not self._check_gh_cli():
                logger.warning("gh CLI not available, falling back to demo mode")
                self.demo_mode = True
            elif not self._check_gh_auth():
                logger.warning("gh CLI not authenticated, falling back to demo mode")
                self.demo_mode = True

        self.token = os.getenv("GITHUB_TOKEN")
        self.rest_session = requests.Session()
        if self.token:
            self.rest_session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3+json"
            })
        
        if self.demo_mode:
            logger.info("Running in DEMO MODE - GitHub operations will be mocked")
    
    def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> GitHubIssue:
        """
        Create a GitHub issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue body (markdown)
            labels: Optional list of labels
            assignees: Optional list of assignees
        
        Returns:
            GitHubIssue object
        """
        if self.demo_mode:
            return self._mock_create_issue(owner, repo, title)
        
        try:
            # Build command
            cmd = [
                "gh", "issue", "create",
                "--repo", f"{owner}/{repo}",
                "--title", title,
                "--body", body
            ]
            
            if labels:
                cmd.extend(["--label", ",".join(labels)])
            
            if assignees:
                cmd.extend(["--assignee", ",".join(assignees)])
            
            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to create issue: {result.stderr}")
                raise Exception(f"GitHub issue creation failed: {result.stderr}")
            
            # Parse issue URL from output
            issue_url = result.stdout.strip()
            
            # Extract issue number from URL
            # URL format: https://github.com/owner/repo/issues/123
            issue_number = int(issue_url.split("/")[-1])
            
            logger.info(f"Created GitHub issue #{issue_number}: {issue_url}")
            
            return GitHubIssue(
                number=issue_number,
                title=title,
                url=issue_url,
                state="open"
            )
            
        except Exception as e:
            logger.error(f"Error creating GitHub issue: {e}")
            raise
    
    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main"
    ) -> PullRequest:
        """
        Create a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            body: PR body (markdown)
            head_branch: Branch with changes
            base_branch: Target branch (default: main)
        
        Returns:
            PullRequest object
        """
        if self.demo_mode:
            return self._mock_create_pr(owner, repo, title, head_branch)
        
        try:
            cmd = [
                "gh", "pr", "create",
                "--repo", f"{owner}/{repo}",
                "--title", title,
                "--body", body,
                "--base", base_branch,
                "--head", head_branch
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to create PR: {result.stderr}")
                raise Exception(f"GitHub PR creation failed: {result.stderr}")
            
            pr_url = result.stdout.strip()
            pr_number = int(pr_url.split("/")[-1])
            
            logger.info(f"Created GitHub PR #{pr_number}: {pr_url}")
            
            return PullRequest(
                number=pr_number,
                url=pr_url,
                state="open"
            )
            
        except Exception as e:
            logger.error(f"Error creating GitHub PR: {e}")
            raise

    # ------------------------------------------------------------------
    # REST helpers for plan artifacts / PR stubs (requires GITHUB_TOKEN)
    # ------------------------------------------------------------------

    GITHUB_API_BASE = "https://api.github.com"

    def _ensure_rest_ready(self):
        if self.demo_mode:
            raise RuntimeError("REST GitHub calls disabled in demo mode")
        if not self.token:
            raise RuntimeError("GITHUB_TOKEN must be set for REST operations")

    def _rest_url(self, path: str) -> str:
        return f"{self.GITHUB_API_BASE}{path}"

    def _rest_request(self, method: str, path: str, **kwargs) -> requests.Response:
        self._ensure_rest_ready()
        url = self._rest_url(path)
        response = self.rest_session.request(method, url, **kwargs)
        if response.status_code >= 400:
            logger.error("GitHub REST %s %s failed: %s", method, url, response.text)
            response.raise_for_status()
        return response

    def get_branch_sha(self, owner: str, repo: str, branch: str) -> Optional[str]:
        try:
            response = self._rest_request("GET", f"/repos/{owner}/{repo}/git/ref/heads/{branch}")
            return response.json()["object"]["sha"]
        except requests.HTTPError as exc:
            if exc.response.status_code == 404:
                return None
            raise

    def create_branch(self, owner: str, repo: str, branch_name: str, base_branch: str) -> Optional[str]:
        existing = self.get_branch_sha(owner, repo, branch_name)
        if existing:
            logger.info("Branch %s already exists", branch_name)
            return existing

        base_sha = self.get_branch_sha(owner, repo, base_branch)
        if not base_sha:
            raise RuntimeError(f"Base branch {base_branch} not found")

        payload = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha
        }
        response = self._rest_request("POST", f"/repos/{owner}/{repo}/git/refs", json=payload)
        return response.json()["object"]["sha"]

    def get_file_sha(self, owner: str, repo: str, path: str, ref: str) -> Optional[str]:
        try:
            response = self._rest_request("GET", f"/repos/{owner}/{repo}/contents/{path}", params={"ref": ref})
            return response.json().get("sha")
        except requests.HTTPError as exc:
            if exc.response.status_code == 404:
                return None
            raise

    def upsert_file(
        self,
        owner: str,
        repo: str,
        path: str,
        branch: str,
        content_bytes: bytes,
        message: str,
        sha: Optional[str] = None
    ) -> str:
        payload = {
            "message": message,
            "content": base64.b64encode(content_bytes).decode(),
            "branch": branch
        }
        if sha:
            payload["sha"] = sha
        response = self._rest_request("PUT", f"/repos/{owner}/{repo}/contents/{path}", json=payload)
        return response.json()["content"]["sha"]

    def create_pull_request_stub(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str
    ) -> PullRequest:
        if self.demo_mode:
            return self._mock_create_pr(owner, repo, title, head_branch)
        payload = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch
        }
        response = self._rest_request("POST", f"/repos/{owner}/{repo}/pulls", json=payload)
        data = response.json()
        return PullRequest(
            number=data["number"],
            url=data["html_url"],
            state=data["state"]
        )
    
    def add_issue_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        comment: str
    ) -> bool:
        """
        Add a comment to an issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            comment: Comment text
        
        Returns:
            True if successful
        """
        if self.demo_mode:
            logger.info(f"DEMO: Would add comment to issue #{issue_number}")
            return True
        
        try:
            cmd = [
                "gh", "issue", "comment", str(issue_number),
                "--repo", f"{owner}/{repo}",
                "--body", comment
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to add comment: {result.stderr}")
                return False
            
            logger.info(f"Added comment to issue #{issue_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            return False
    
    def update_issue_labels(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        labels: List[str]
    ) -> bool:
        """
        Update issue labels.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            labels: List of labels
        
        Returns:
            True if successful
        """
        if self.demo_mode:
            logger.info(f"DEMO: Would update labels for issue #{issue_number}")
            return True
        
        try:
            cmd = [
                "gh", "issue", "edit", str(issue_number),
                "--repo", f"{owner}/{repo}",
                "--add-label", ",".join(labels)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to update labels: {result.stderr}")
                return False
            
            logger.info(f"Updated labels for issue #{issue_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating labels: {e}")
            return False
    
    def _check_gh_cli(self) -> bool:
        """Check if gh CLI is installed."""
        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _check_gh_auth(self) -> bool:
        """Check if gh CLI is authenticated."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
    
    def _mock_create_issue(self, owner: str, repo: str, title: str) -> GitHubIssue:
        """Mock issue creation for demo mode."""
        import random
        issue_number = random.randint(100, 999)
        issue_url = f"https://github.com/{owner}/{repo}/issues/{issue_number}"
        
        logger.info(f"DEMO: Created mock issue #{issue_number}: {title}")
        
        return GitHubIssue(
            number=issue_number,
            title=title,
            url=issue_url,
            state="open"
        )
    
    def _mock_create_pr(
        self,
        owner: str,
        repo: str,
        title: str,
        head_branch: str
    ) -> PullRequest:
        """Mock PR creation for demo mode."""
        import random
        pr_number = random.randint(10, 99)
        pr_url = f"https://github.com/{owner}/{repo}/pull/{pr_number}"
        
        logger.info(f"DEMO: Created mock PR #{pr_number}: {title}")
        
        return PullRequest(
            number=pr_number,
            url=pr_url,
            state="open"
        )


def format_issue_body_from_spec(
    issue_spec: Dict[str, Any],
    reddit_entries: List[Dict[str, Any]]
) -> str:
    """
    Format a GitHub issue body from an IssueSpec and Reddit entries.
    
    Args:
        issue_spec: IssueSpec dict from Gemini
        reddit_entries: List of Reddit entry dicts
    
    Returns:
        Formatted markdown string
    """
    body_parts = []
    
    # Problem statement
    body_parts.append("## Problem Statement")
    body_parts.append(issue_spec.get("problem_statement", ""))
    body_parts.append("")
    
    # Steps to reproduce (if present)
    if issue_spec.get("steps_to_reproduce"):
        body_parts.append("## Steps to Reproduce")
        body_parts.append(issue_spec["steps_to_reproduce"])
        body_parts.append("")

    # User impact (why it matters)
    if issue_spec.get("user_impact"):
        body_parts.append("## Why It Matters")
        body_parts.append(issue_spec["user_impact"])
        body_parts.append("")

    # Expected behavior
    body_parts.append("## Expected Behavior")
    body_parts.append(issue_spec.get("expected_behavior", ""))
    body_parts.append("")

    # Actual behavior (if present)
    if issue_spec.get("actual_behavior"):
        body_parts.append("## Actual Behavior")
        body_parts.append(issue_spec["actual_behavior"])
        body_parts.append("")

    # Suspected root cause (if present)
    if issue_spec.get("suspected_root_cause"):
        body_parts.append("## Suspected Root Cause")
        body_parts.append(issue_spec["suspected_root_cause"])
        body_parts.append("")

    # Suggested fix steps (if present)
    if issue_spec.get("suggested_fix_steps"):
        body_parts.append("## Suggested Fix Steps")
        body_parts.append(issue_spec["suggested_fix_steps"])
        body_parts.append("")
    
    # Acceptance criteria
    body_parts.append("## Acceptance Criteria")
    for criterion in issue_spec.get("acceptance_criteria", []):
        body_parts.append(f"- [ ] {criterion}")
    body_parts.append("")
    
    # User feedback evidence
    body_parts.append("## User Feedback")
    body_parts.append(f"Based on {len(reddit_entries)} Reddit posts/comments:")
    body_parts.append("")
    
    for i, entry in enumerate(reddit_entries[:5], 1):  # Show top 5
        permalink = entry.get("permalink", "")
        score = entry.get("score", 0)
        body_parts.append(f"{i}. [{score} upvotes]({permalink})")
    
    if len(reddit_entries) > 5:
        body_parts.append(f"\n...and {len(reddit_entries) - 5} more")
    
    body_parts.append("")
    body_parts.append("---")
    body_parts.append("*Generated by EchoFix from Reddit feedback*")
    
    return "\n".join(body_parts)
