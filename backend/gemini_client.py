"""
Gemini API integration for EchoFix.
Handles reasoning, structured outputs, and multimodal analysis.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import base64

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from models import (
    InsightSummary,
    IssueSpec,
    PatchPlan,
    Priority,
    Insight,
    RedditEntry
)

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Client for Google Gemini API.
    Supports structured outputs, function calling, and multimodal analysis.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        demo_mode: bool = False,
        model_name: str = "gemini-2.0-flash-exp"
    ):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key
            demo_mode: If True, use fixtures instead of live API
            model_name: Gemini model to use
        """
        self.demo_mode = demo_mode or os.getenv("DEMO_MODE", "false").lower() == "true"
        self.model_name = model_name
        
        if not self.demo_mode:
            self.api_key = api_key or os.getenv("GEMINI_API_KEY")
            
            if not self.api_key:
                logger.warning("Gemini API key missing, falling back to demo mode")
                self.demo_mode = True
            else:
                try:
                    genai.configure(api_key=self.api_key)
                    
                    # Initialize model with safety settings
                    self.model = genai.GenerativeModel(
                        model_name=self.model_name,
                        safety_settings={
                            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                        }
                    )
                    
                    logger.info(f"Gemini client initialized with {model_name}")
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini client: {e}")
                    self.demo_mode = True
        
        if self.demo_mode:
            logger.info("Running in DEMO MODE - using fixtures")
            self.fixtures_path = Path(__file__).parent / "fixtures"
    
    def analyze_insight(
        self,
        insight: Insight,
        reddit_entries: List[RedditEntry]
    ) -> InsightSummary:
        """
        Analyze an insight to create a summary.
        
        Args:
            insight: Insight object
            reddit_entries: Original Reddit entries for context
        
        Returns:
            InsightSummary object
        """
        if self.demo_mode:
            return self._load_demo_insight_summary(insight.theme)
        
        # Build context from Reddit entries
        context = self._build_context(reddit_entries)
        
        prompt = f"""
You are analyzing user feedback from Reddit to create a structured summary.

**Insight Theme:** {insight.theme}
**Description:** {insight.description}
**Number of Entries:** {insight.entry_count}

**Sample Feedback:**
{context}

Analyze this insight and provide:
1. A clear, concise theme (max 80 chars)
2. Severity/priority level (critical, high, medium, low)
3. Your confidence score (0-1)
4. Description of user impact
5. Count of supporting evidence

Respond in JSON format matching this schema:
{{
    "theme": "string",
    "severity": "critical|high|medium|low",
    "confidence": 0.0-1.0,
    "user_impact": "string",
    "evidence_count": integer
}}
"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )
            
            data = json.loads(response.text)
            
            # Map severity string to Priority enum
            severity_map = {
                "critical": Priority.CRITICAL,
                "high": Priority.HIGH,
                "medium": Priority.MEDIUM,
                "low": Priority.LOW
            }
            data["severity"] = severity_map.get(data["severity"], Priority.MEDIUM)
            
            summary = InsightSummary(**data)
            logger.info(f"Generated insight summary for '{insight.theme}'")
            return summary
            
        except Exception as e:
            logger.error(f"Error analyzing insight: {e}")
            # Return default summary
            return InsightSummary(
                theme=insight.theme,
                severity=Priority.MEDIUM,
                confidence=0.5,
                user_impact="Unknown",
                evidence_count=insight.entry_count
            )
    
    def generate_issue_spec(
        self,
        insight: Insight,
        summary: InsightSummary,
        reddit_entries: List[RedditEntry],
        include_images: bool = False
    ) -> IssueSpec:
        """
        Generate a structured GitHub issue specification.
        
        Args:
            insight: Insight
            summary: Insight summary
            reddit_entries: Original Reddit entries
            include_images: Whether to analyze images (multimodal)
        
        Returns:
            IssueSpec object
        """
        if self.demo_mode:
            return self._load_demo_issue_spec(insight.theme)
        
        context = self._build_context(reddit_entries, include_metadata=True)
        
        # Prepare multimodal content if images present
        content_parts = []
        
        prompt_text = f"""
You are a senior engineer converting user feedback into a structured GitHub issue.

**Theme:** {summary.theme}
**Priority:** {summary.severity}
**User Impact:** {summary.user_impact}
**Evidence Count:** {summary.evidence_count}

**User Feedback:**
{context}

Create a detailed GitHub issue specification with:
1. Clear, actionable title (max 80 chars)
2. Problem statement (what's wrong?)
3. Why it matters (user impact)
4. Steps to reproduce (if it's a bug)
5. Expected behavior
6. Actual behavior (if it's a bug)
7. Suspected root cause
8. Suggested fix steps
9. Acceptance criteria (list of testable conditions)
10. Appropriate GitHub labels
11. Estimated effort (XS, S, M, L, XL)

Respond in JSON format:
{{
    "title": "string",
    "problem_statement": "string",
    "user_impact": "string or null",
    "steps_to_reproduce": "string or null",
    "expected_behavior": "string",
    "actual_behavior": "string or null",
    "suspected_root_cause": "string or null",
    "suggested_fix_steps": "string or null",
    "acceptance_criteria": ["criterion1", "criterion2", ...],
    "labels": ["label1", "label2", ...],
    "priority": "critical|high|medium|low",
    "estimated_effort": "XS|S|M|L|XL"
}}
"""
        
        content_parts.append(prompt_text)
        
        # Add images if available and requested
        if include_images:
            for entry in reddit_entries[:3]:  # Limit to first 3 with images
                if entry.image_urls:
                    for img_url in entry.image_urls[:1]:  # One image per entry
                        content_parts.append(f"Screenshot from user: {img_url}")
        
        try:
            response = self.model.generate_content(
                content_parts,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )
            
            data = json.loads(response.text)
            
            # Map priority string to Priority enum
            priority_map = {
                "critical": Priority.CRITICAL,
                "high": Priority.HIGH,
                "medium": Priority.MEDIUM,
                "low": Priority.LOW
            }
            data["priority"] = priority_map.get(data["priority"], Priority.MEDIUM)
            
            issue_spec = IssueSpec(**data)
            logger.info(f"Generated issue spec: '{issue_spec.title}'")
            return issue_spec
            
        except Exception as e:
            logger.error(f"Error generating issue spec: {e}")
            # Return default issue spec
            return IssueSpec(
                title=summary.theme,
                problem_statement=insight.description,
                user_impact=summary.user_impact,
                steps_to_reproduce=None,
                expected_behavior="System should work as expected",
                actual_behavior=None,
                suspected_root_cause=None,
                suggested_fix_steps=None,
                acceptance_criteria=["Issue is resolved"],
                labels=["bug" if "bug" in insight.description.lower() else "enhancement"],
                priority=summary.severity,
                estimated_effort=None
            )
    
    def generate_patch_plan(
        self,
        issue_spec: IssueSpec,
        repo_context: Optional[Dict[str, Any]] = None
    ) -> PatchPlan:
        """
        Generate a patch plan for code changes.
        
        Args:
            issue_spec: Issue specification
            repo_context: Optional repository context (file structure, tech stack)
        
        Returns:
            PatchPlan object
        """
        if self.demo_mode:
            return self._load_demo_patch_plan()
        
        repo_info = ""
        if repo_context:
            repo_info = f"""
**Repository Context:**
- Primary Language: {repo_context.get('language', 'Unknown')}
- Framework: {repo_context.get('framework', 'Unknown')}
- Key Directories: {', '.join(repo_context.get('directories', []))}
"""
        
        prompt = f"""
You are a senior engineer planning code changes for a GitHub issue.

**Issue Title:** {issue_spec.title}
**Problem:** {issue_spec.problem_statement}
**Expected Behavior:** {issue_spec.expected_behavior}
**Acceptance Criteria:**
{chr(10).join(f'- {criterion}' for criterion in issue_spec.acceptance_criteria)}

{repo_info}

Create a high-level patch plan:
1. One-line summary of the change
2. Files likely to be impacted
3. High-level outline of changes
4. Risk level (low, medium, high)
5. Test plan

Respond in JSON format:
{{
    "summary": "string",
    "files_impacted": ["file1.py", "file2.js", ...],
    "change_outline": "string",
    "risk_level": "low|medium|high",
    "test_plan": "string"
}}
"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )
            
            data = json.loads(response.text)
            patch_plan = PatchPlan(**data)
            
            logger.info(f"Generated patch plan: {patch_plan.summary}")
            return patch_plan
            
        except Exception as e:
            logger.error(f"Error generating patch plan: {e}")
            return PatchPlan(
                summary="Implement fix for issue",
                files_impacted=[],
                change_outline="Changes to be determined",
                risk_level="medium",
                test_plan="Manual testing required"
            )
    
    def classify_feedback_type(self, text: str) -> str:
        """
        Classify feedback type (bug, feature, enhancement, question).
        
        Args:
            text: Feedback text
        
        Returns:
            Classification string
        """
        if self.demo_mode:
            # Simple keyword-based classification for demo
            text_lower = text.lower()
            if any(word in text_lower for word in ["bug", "broken", "error", "crash", "issue"]):
                return "bug"
            elif any(word in text_lower for word in ["feature", "add", "would be nice", "suggestion"]):
                return "feature"
            elif any(word in text_lower for word in ["improve", "better", "enhance"]):
                return "enhancement"
            else:
                return "question"
        
        prompt = f"""
Classify this user feedback into one category:
- bug: Something is broken or not working
- feature: Request for new functionality
- enhancement: Improvement to existing functionality
- question: User asking for help or information

Feedback: {text}

Respond with only one word: bug, feature, enhancement, or question
"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(temperature=0.1)
            )
            
            classification = response.text.strip().lower()
            if classification not in ["bug", "feature", "enhancement", "question"]:
                classification = "feedback"
            
            return classification
            
        except Exception as e:
            logger.error(f"Error classifying feedback: {e}")
            return "feedback"
    
    def extract_image_insights(self, image_url: str, context: str) -> str:
        """
        Extract insights from an image (screenshot, error message, etc.).
        
        Args:
            image_url: URL to the image
            context: Surrounding context
        
        Returns:
            Extracted insights as text
        """
        if self.demo_mode:
            return "Demo mode: Image analysis not available"
        
        prompt = f"""
Analyze this screenshot from a user reporting an issue.

Context: {context}

Extract:
1. Any error messages or codes
2. UI elements that seem problematic
3. Technical details visible
4. What the user was trying to do

Provide a concise technical description.
"""
        
        try:
            # Note: In production, you'd download/process the image
            # For now, we just reference the URL
            response = self.model.generate_content(
                [prompt, f"Image URL: {image_url}"],
                generation_config=genai.GenerationConfig(temperature=0.3)
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return f"Error analyzing image: {str(e)}"
    
    def _build_context(
        self,
        reddit_entries: List[RedditEntry],
        max_entries: int = 10,
        include_metadata: bool = False
    ) -> str:
        """Build context string from Reddit entries."""
        context_parts = []
        
        for i, entry in enumerate(reddit_entries[:max_entries], 1):
            text = entry.title if entry.title else ""
            if entry.body:
                text += f"\n{entry.body}"
            
            context_part = f"[Entry {i}]\n{text}"
            
            if include_metadata:
                context_part += f"\nScore: {entry.score} | Subreddit: r/{entry.subreddit}"
                context_part += f"\nLink: {entry.permalink}"
            
            context_parts.append(context_part)
        
        return "\n\n".join(context_parts)
    
    def _load_demo_insight_summary(self, theme: str) -> InsightSummary:
        """Load demo insight summary."""
        # Default summaries based on theme keywords
        if "login" in theme.lower() or "auth" in theme.lower():
            return InsightSummary(
                theme="Authentication Failures",
                severity=Priority.HIGH,
                confidence=0.85,
                user_impact="Users cannot log in to their accounts",
                evidence_count=15
            )
        elif "dark" in theme.lower() and "mode" in theme.lower():
            return InsightSummary(
                theme="Dark Mode Feature Request",
                severity=Priority.MEDIUM,
                confidence=0.9,
                user_impact="Users want dark mode for better UX",
                evidence_count=42
            )
        else:
            return InsightSummary(
                theme=theme,
                severity=Priority.MEDIUM,
                confidence=0.7,
                user_impact="Impact analysis needed",
                evidence_count=10
            )
    
    def _load_demo_issue_spec(self, theme: str) -> IssueSpec:
        """Load demo issue spec."""
        if "login" in theme.lower():
            return IssueSpec(
                title="Fix authentication failures with invalid credentials",
                problem_statement="Users are reporting that login fails even with correct credentials. Error message is not helpful.",
                user_impact="Users cannot access their accounts, which blocks core workflows.",
                steps_to_reproduce="1. Navigate to login page\n2. Enter valid credentials\n3. Click login\n4. See 'invalid credentials' error",
                expected_behavior="User should be logged in successfully with valid credentials",
                actual_behavior="Login fails with generic error message",
                suspected_root_cause="Auth service rejects valid sessions due to token parsing edge case.",
                suggested_fix_steps="1. Add token validation logging\n2. Fix parsing for expired tokens\n3. Improve error messaging",
                acceptance_criteria=[
                    "Valid credentials allow successful login",
                    "Error messages are specific and helpful",
                    "Session persists after login"
                ],
                labels=["bug", "authentication", "high-priority"],
                priority=Priority.HIGH,
                estimated_effort="M"
            )
        else:
            return IssueSpec(
                title=f"Implement {theme}",
                problem_statement=f"Users are requesting {theme}",
                user_impact="Improves usability and addresses repeated user feedback.",
                steps_to_reproduce=None,
                expected_behavior=f"{theme} should be implemented",
                actual_behavior=None,
                suspected_root_cause=None,
                suggested_fix_steps="1. Add feature flag\n2. Implement UI and API support\n3. Add tests and docs",
                acceptance_criteria=[
                    "Feature is implemented",
                    "Tests pass",
                    "Documentation updated"
                ],
                labels=["enhancement"],
                priority=Priority.MEDIUM,
                estimated_effort="L"
            )
    
    def _load_demo_patch_plan(self) -> PatchPlan:
        """Load demo patch plan."""
        return PatchPlan(
            summary="Update authentication logic to handle edge cases",
            files_impacted=["backend/auth.py", "backend/models.py", "frontend/components/LoginForm.tsx"],
            change_outline="1. Add better error handling in auth endpoint\n2. Update validation logic\n3. Improve error messages in UI\n4. Add logging for debugging",
            risk_level="medium",
            test_plan="1. Unit tests for auth logic\n2. Integration tests for login flow\n3. Manual testing with various credential scenarios"
        )
