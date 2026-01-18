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
import subprocess
import tempfile
import shutil

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

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not installed. Run: pip install openai")


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
        Initialize Gemini client with OpenAI fallback.

        Args:
            api_key: Gemini API key
            demo_mode: If True, use fixtures instead of live API
            model_name: Gemini model to use
        """
        self.demo_mode = demo_mode or os.getenv("DEMO_MODE", "false").lower() == "true"
        self.model_name = model_name
        self.openai_client = None

        if not self.demo_mode:
            self.api_key = api_key or os.getenv("GEMINI_API_KEY")

            if not self.api_key:
                logger.warning("Gemini API key missing, trying OpenAI fallback")
                self._init_openai_fallback()
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
                    # Also init OpenAI as fallback
                    self._init_openai_fallback()
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini client: {e}")
                    self._init_openai_fallback()

    def _init_openai_fallback(self):
        """Initialize OpenAI as fallback when Gemini fails."""
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI not available - falling back to smart generation")
            return

        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                self.openai_client = OpenAI(api_key=openai_key)
                logger.info("OpenAI fallback initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI fallback: {e}")
        else:
            logger.warning("OPENAI_API_KEY not set - smart generation only")
        
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

    def generate_code_implementation(
        self,
        issue_spec: IssueSpec,
        patch_plan: PatchPlan,
        repo_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate actual code implementation for the issue.

        Args:
            issue_spec: Issue specification
            patch_plan: Patch plan with file impacts
            repo_context: Optional repository context (file contents, tech stack)

        Returns:
            Dictionary mapping file paths to file contents
        """
        if self.demo_mode:
            return self._load_demo_code_implementation(issue_spec, patch_plan)

        repo_info = ""
        if repo_context:
            repo_info = f"""
**Repository Context:**
- Primary Language: {repo_context.get('language', 'Unknown')}
- Framework: {repo_context.get('framework', 'Unknown')}
- Key Directories: {', '.join(repo_context.get('directories', []))}
"""

        # Build file context if available
        file_context = ""
        if repo_context and 'file_contents' in repo_context:
            file_context = "\n\n**Existing File Contents:**\n"
            for file_path, content in repo_context['file_contents'].items():
                file_context += f"\n--- {file_path} ---\n{content[:1000]}\n"

        prompt = f"""
You are a senior engineer implementing code changes for a GitHub issue.

**Issue Title:** {issue_spec.title}
**Problem:** {issue_spec.problem_statement}
**Expected Behavior:** {issue_spec.expected_behavior}
**Acceptance Criteria:**
{chr(10).join(f'- {criterion}' for criterion in issue_spec.acceptance_criteria)}

**Patch Plan:**
Summary: {patch_plan.summary}
Files to modify: {', '.join(patch_plan.files_impacted)}
Change outline: {patch_plan.change_outline}

{repo_info}
{file_context}

Generate complete, production-ready code for ALL files that need to be created or modified.
For features like dark mode, add mode, settings, etc., provide working implementations.

Respond in JSON format:
{{
    "files": {{
        "path/to/file1.ext": "complete file contents",
        "path/to/file2.ext": "complete file contents"
    }},
    "implementation_notes": "Brief explanation of what was implemented"
}}

IMPORTANT:
- Provide COMPLETE file contents, not just snippets
- Include all necessary imports and dependencies
- Follow best practices for the language/framework
- Make the code production-ready
- For CSS/styling, use complete stylesheets
- For React components, include full component code
"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )

            data = json.loads(response.text)
            files = data.get('files', {})

            logger.info(f"Generated code implementation for {len(files)} files")
            return files

        except Exception as e:
            logger.error(f"Error generating code implementation: {e}")
            # Return empty implementation on error
            return {}

    def _load_demo_code_implementation(
        self,
        issue_spec: IssueSpec,
        patch_plan: PatchPlan
    ) -> Dict[str, str]:
        """Load demo code implementation based on issue type."""

        # Check if it's a dark mode request
        if "dark" in issue_spec.title.lower() and "mode" in issue_spec.title.lower():
            return {
                "styles/darkmode.css": """/* Dark Mode Styles */
:root {
    --bg-light: #ffffff;
    --bg-dark: #1a1a1a;
    --text-light: #333333;
    --text-dark: #f0f0f0;
}

body {
    background-color: var(--bg-light);
    color: var(--text-light);
    transition: background-color 0.3s ease, color 0.3s ease;
}

body.dark-mode {
    background-color: var(--bg-dark);
    color: var(--text-dark);
}

.dark-mode-toggle {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 10px 20px;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
}

.dark-mode-toggle:hover {
    background: #0056b3;
}
""",
                "scripts/darkmode.js": """// Dark Mode Toggle Script
(function() {
    const DARK_MODE_KEY = 'darkMode';

    function toggleDarkMode() {
        const isDark = document.body.classList.toggle('dark-mode');
        localStorage.setItem(DARK_MODE_KEY, isDark);
        updateToggleButton(isDark);
    }

    function updateToggleButton(isDark) {
        const button = document.getElementById('dark-mode-toggle');
        if (button) {
            button.textContent = isDark ? '☀️ Light Mode' : '🌙 Dark Mode';
        }
    }

    // Load saved preference
    function loadDarkModePreference() {
        const isDark = localStorage.getItem(DARK_MODE_KEY) === 'true';
        if (isDark) {
            document.body.classList.add('dark-mode');
        }
        updateToggleButton(isDark);
    }

    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {
        loadDarkModePreference();

        // Add toggle button
        const button = document.createElement('button');
        button.id = 'dark-mode-toggle';
        button.className = 'dark-mode-toggle';
        button.onclick = toggleDarkMode;
        document.body.appendChild(button);

        updateToggleButton(document.body.classList.contains('dark-mode'));
    });
})();
""",
                "index.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume Analyzer - Now with Dark Mode!</title>
    <link rel="stylesheet" href="styles/darkmode.css">
    <script src="scripts/darkmode.js"></script>
</head>
<body>
    <h1>Resume Analyzer</h1>
    <p>Dark mode is now available! Click the button in the top-right corner to toggle.</p>
    <!-- Rest of your content -->
</body>
</html>
"""
            }

        # Generic implementation for other issues
        # Generate actual code files based on the patch plan
        code_files = {}

        # Add implementation for each file mentioned in the patch plan
        for file_path in patch_plan.files_impacted:
            # Determine file extension
            if file_path.endswith('.py'):
                # Generate Python code
                code_files[file_path] = f"""# {issue_spec.title}
# Auto-generated implementation

{patch_plan.change_outline}

# TODO: Implement the following changes:
# {chr(10).join(f'# - {c}' for c in issue_spec.acceptance_criteria)}

def fix_{issue_spec.title.lower().replace(' ', '_').replace('-', '_')}():
    \"\"\"
    {issue_spec.problem_statement}

    Changes:
    {patch_plan.summary}
    \"\"\"
    # Implementation goes here
    pass

if __name__ == "__main__":
    fix_{issue_spec.title.lower().replace(' ', '_').replace('-', '_')}()
    print("Fix applied successfully!")
"""
            elif file_path.endswith('.js') or file_path.endswith('.jsx'):
                # Generate JavaScript/React code
                code_files[file_path] = f"""// {issue_spec.title}
// Auto-generated implementation

/*
 * {issue_spec.problem_statement}
 *
 * Changes:
 * {patch_plan.summary}
 */

// TODO: Implement the following:
{chr(10).join(f'// - {c}' for c in issue_spec.acceptance_criteria)}

export function fix{issue_spec.title.replace(' ', '').replace('-', '')}() {{
    // Implementation goes here
    console.log('Fix applied successfully!');
}}
"""
            elif file_path.endswith('.html'):
                # Generate HTML
                code_files[file_path] = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{issue_spec.title}</title>
</head>
<body>
    <!-- {issue_spec.problem_statement} -->

    <!-- Changes: {patch_plan.summary} -->

    <!-- TODO: Implement -->
    <h1>{issue_spec.title}</h1>
    <p>Implementation placeholder</p>
</body>
</html>
"""
            elif file_path.endswith('.css'):
                # Generate CSS
                code_files[file_path] = f"""/* {issue_spec.title} */
/* Auto-generated implementation */

/*
 * {issue_spec.problem_statement}
 *
 * Changes:
 * {patch_plan.summary}
 */

/* TODO: Implement the required styles */
.fix-placeholder {{
    /* Add styles here */
}}
"""
            else:
                # Generic text file
                code_files[file_path] = f"""# {issue_spec.title}

{issue_spec.problem_statement}

## Changes
{patch_plan.summary}

## Implementation
{patch_plan.change_outline}

## TODO
{chr(10).join(f'- {c}' for c in issue_spec.acceptance_criteria)}
"""

        # Also add an IMPLEMENTATION.md for reference
        code_files["IMPLEMENTATION.md"] = f"""# Implementation for: {issue_spec.title}

## Summary
{patch_plan.summary}

## Changes Made

{patch_plan.change_outline}

## Files Modified
{chr(10).join(f'- {f}' for f in patch_plan.files_impacted)}

## Test Plan
{patch_plan.test_plan}

## Acceptance Criteria
{chr(10).join(f'- {c}' for c in issue_spec.acceptance_criteria)}

## Notes
This is an auto-generated implementation. Please review and test thoroughly before merging.
"""

        return code_files

    def generate_real_code_implementation(
        self,
        issue_spec: IssueSpec,
        patch_plan: PatchPlan,
        repo_owner: str,
        repo_name: str,
        github_token: str
    ) -> Dict[str, str]:
        """
        Clone the repository, analyze actual code, and generate real fixes.

        Args:
            issue_spec: The issue specification
            patch_plan: The patch plan with files to modify
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            github_token: GitHub access token

        Returns:
            Dictionary mapping file paths to their new content
        """
        logger.info(f"Generating real code implementation for: {issue_spec.title}")

        # Create temporary directory for repo
        temp_dir = tempfile.mkdtemp(prefix="echofix_repo_")
        repo_url = f"https://{github_token}@github.com/{repo_owner}/{repo_name}.git"

        try:
            # Clone the repository
            logger.info(f"Cloning {repo_owner}/{repo_name} to {temp_dir}")
            subprocess.run(
                ["git", "clone", "--depth=1", repo_url, temp_dir],
                check=True,
                capture_output=True,
                timeout=60
            )

            code_files = {}

            # Log the files we're trying to fix
            logger.info(f"Files to fix from patch plan: {patch_plan.files_impacted}")

            if not patch_plan.files_impacted:
                logger.warning("No files in patch plan! Inferring files from issue title...")
                # Infer files based on issue title/problem
                inferred_files = self._infer_files_from_issue(issue_spec, temp_dir)
                if not inferred_files:
                    logger.warning("Could not infer files. Using demo implementation.")
                    return self._load_demo_code_implementation(issue_spec, patch_plan)
                patch_plan.files_impacted = inferred_files
                logger.info(f"Inferred files: {inferred_files}")

            # For each file in the patch plan, read it and generate fixes
            for file_path in patch_plan.files_impacted:
                full_path = os.path.join(temp_dir, file_path)

                # Check if file exists
                if os.path.exists(full_path):
                    # Read existing file content
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        original_content = f.read()

                    logger.info(f"Analyzing existing file: {file_path} ({len(original_content)} chars)")

                    # Use Gemini to generate the fixed version
                    try:
                        fixed_content = self._generate_code_fix(
                            file_path=file_path,
                            original_content=original_content,
                            issue_spec=issue_spec,
                            patch_plan=patch_plan
                        )

                        if fixed_content and fixed_content != original_content:
                            code_files[file_path] = fixed_content
                            logger.info(f"Generated fix for {file_path}")
                        else:
                            logger.warning(f"No changes generated for {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to generate fix for {file_path}: {e}")
                        # Fall back to adding a comment
                        code_files[file_path] = self._add_todo_comment(original_content, issue_spec, file_path)
                else:
                    # File doesn't exist, create new file
                    logger.info(f"Creating new file: {file_path}")
                    code_files[file_path] = self._generate_new_file(file_path, issue_spec, patch_plan)

            return code_files

        except subprocess.TimeoutExpired:
            logger.error("Git clone timed out")
            # Fall back to demo implementation
            return self._load_demo_code_implementation(issue_spec, patch_plan)
        except subprocess.CalledProcessError as e:
            logger.error(f"Git clone failed: {e.stderr.decode() if e.stderr else str(e)}")
            # Fall back to demo implementation
            return self._load_demo_code_implementation(issue_spec, patch_plan)
        except Exception as e:
            logger.error(f"Error generating real code: {e}", exc_info=True)
            # Fall back to demo implementation
            return self._load_demo_code_implementation(issue_spec, patch_plan)
        finally:
            # Clean up temp directory
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

    def _generate_code_fix(
        self,
        file_path: str,
        original_content: str,
        issue_spec: IssueSpec,
        patch_plan: PatchPlan
    ) -> str:
        """Use Gemini to generate a fixed version of the file."""

        if self.demo_mode:
            return self._make_smart_changes_without_gemini(file_path, original_content, issue_spec)

        prompt = f"""You are a senior software engineer fixing a bug/implementing a feature.

ISSUE: {issue_spec.title}
PROBLEM: {issue_spec.problem_statement}

PATCH PLAN:
{patch_plan.change_outline}

CURRENT FILE ({file_path}):
```
{original_content[:8000]}
```

Generate the COMPLETE fixed version of this file that implements the required changes.
Only output the fixed file content, no explanations or markdown code blocks.
Make minimal changes - only fix what's needed for this issue.

FIXED FILE CONTENT:"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 8192,
                }
            )

            fixed_content = response.text.strip()

            # Remove markdown code blocks if Gemini added them
            if fixed_content.startswith("```"):
                lines = fixed_content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                fixed_content = "\n".join(lines)

            return fixed_content

        except Exception as e:
            logger.error(f"Gemini code generation failed: {e}")

            # Try OpenAI fallback
            if self.openai_client:
                logger.info("Trying OpenAI fallback for code generation")
                try:
                    return self._generate_code_fix_with_openai(file_path, original_content, issue_spec, patch_plan)
                except Exception as openai_error:
                    logger.error(f"OpenAI fallback also failed: {openai_error}")

            # Final fallback: Use smart changes without any AI
            return self._make_smart_changes_without_gemini(file_path, original_content, issue_spec)

    def _add_todo_comment(self, original_content: str, issue_spec: IssueSpec, file_path: str) -> str:
        """Add a TODO comment to the file."""
        if file_path.endswith('.py'):
            comment = f"# TODO: {issue_spec.title}\n# {issue_spec.problem_statement}\n\n"
        elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
            comment = f"// TODO: {issue_spec.title}\n// {issue_spec.problem_statement}\n\n"
        elif file_path.endswith(('.html', '.xml')):
            comment = f"<!-- TODO: {issue_spec.title} -->\n<!-- {issue_spec.problem_statement} -->\n\n"
        elif file_path.endswith('.css'):
            comment = f"/* TODO: {issue_spec.title} */\n/* {issue_spec.problem_statement} */\n\n"
        else:
            comment = f"# TODO: {issue_spec.title}\n# {issue_spec.problem_statement}\n\n"

        return comment + original_content

    def _generate_new_file(self, file_path: str, issue_spec: IssueSpec, patch_plan: PatchPlan) -> str:
        """Generate a new file from scratch."""

        if self.demo_mode:
            return f"# New file: {file_path}\n# TODO: Implement {issue_spec.title}\n"

        prompt = f"""You are a senior software engineer creating a new file.

ISSUE: {issue_spec.title}
PROBLEM: {issue_spec.problem_statement}

PATCH PLAN:
{patch_plan.change_outline}

Create a new file at: {file_path}

Generate the COMPLETE content for this new file.
Only output the file content, no explanations or markdown code blocks.

FILE CONTENT:"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 4096,
                }
            )

            content = response.text.strip()

            # Remove markdown code blocks if Gemini added them
            if content.startswith("```"):
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                content = "\n".join(lines)

            return content

        except Exception as e:
            logger.error(f"Gemini new file generation failed: {e}")
            return f"# New file: {file_path}\n# TODO: Implement {issue_spec.title}\n"

    def _infer_files_from_issue(self, issue_spec: IssueSpec, repo_path: str) -> List[str]:
        """Infer which files to modify based on the issue without using Gemini."""
        files = []
        title_lower = issue_spec.title.lower()
        problem_lower = issue_spec.problem_statement.lower()

        # Check if it's a UI/CSS/dark mode issue
        if any(keyword in title_lower or keyword in problem_lower for keyword in ['ui', 'dark', 'theme', 'css', 'style', 'color']):
            # Look for CSS, HTML, and JS files
            potential_files = [
                'static/css/style.css',
                'static/css/main.css',
                'static/css/app.css',
                'css/style.css',
                'css/main.css',
                'templates/index.html',
                'templates/base.html',
                'index.html',
                'static/js/app.js',
                'static/js/main.js',
                'app.py',  # Might need to add dark mode toggle endpoint
            ]

            for file_path in potential_files:
                full_path = os.path.join(repo_path, file_path)
                if os.path.exists(full_path):
                    files.append(file_path)
                    logger.info(f"Found relevant file: {file_path}")

        # Check for backend/API issues
        elif any(keyword in title_lower or keyword in problem_lower for keyword in ['api', 'endpoint', 'backend', 'server', 'route']):
            potential_files = [
                'app.py',
                'main.py',
                'server.py',
                'api/routes.py',
                'routes.py',
            ]
            for file_path in potential_files:
                full_path = os.path.join(repo_path, file_path)
                if os.path.exists(full_path):
                    files.append(file_path)

        # Default: find main Python/HTML files
        if not files:
            for root, dirs, filenames in os.walk(repo_path):
                # Skip hidden dirs and common excludes
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__']]

                for filename in filenames:
                    if filename in ['app.py', 'main.py', 'index.html', 'style.css']:
                        rel_path = os.path.relpath(os.path.join(root, filename), repo_path)
                        files.append(rel_path)
                        if len(files) >= 3:  # Limit to 3 files
                            break
                if len(files) >= 3:
                    break

        return files

    def _make_smart_changes_without_gemini(self, file_path: str, original_content: str, issue_spec: IssueSpec) -> str:
        """Make intelligent changes to files without using Gemini API."""
        title_lower = issue_spec.title.lower()

        # Dark mode implementation
        if 'dark' in title_lower and 'mode' in title_lower:
            if file_path.endswith('.css'):
                # Add dark mode CSS
                dark_mode_css = """
/* Dark Mode Styles - Auto-generated by EchoFix */
:root {
    --bg-light: #ffffff;
    --bg-dark: #1e1e1e;
    --text-light: #333333;
    --text-dark: #e0e0e0;
}

body.dark-mode {
    background-color: var(--bg-dark) !important;
    color: var(--text-dark) !important;
}

body.dark-mode h1,
body.dark-mode h2,
body.dark-mode h3,
body.dark-mode p {
    color: var(--text-dark) !important;
}

.dark-mode-toggle {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 10px 20px;
    background: #4CAF50;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    z-index: 1000;
}

.dark-mode-toggle:hover {
    background: #45a049;
}
"""
                return original_content + "\n" + dark_mode_css

            elif file_path.endswith('.html'):
                # Add dark mode toggle button and script
                if '<body' in original_content:
                    script = """
<script>
// Dark Mode Toggle - Auto-generated by EchoFix
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDark);
    updateToggleButton(isDark);
}

function updateToggleButton(isDark) {
    const btn = document.getElementById('darkModeToggle');
    if (btn) btn.textContent = isDark ? '☀️ Light Mode' : '🌙 Dark Mode';
}

document.addEventListener('DOMContentLoaded', function() {
    // Load saved preference
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
    }

    // Create toggle button if it doesn't exist
    if (!document.getElementById('darkModeToggle')) {
        const btn = document.createElement('button');
        btn.id = 'darkModeToggle';
        btn.className = 'dark-mode-toggle';
        btn.onclick = toggleDarkMode;
        document.body.appendChild(btn);
        updateToggleButton(document.body.classList.contains('dark-mode'));
    }
});
</script>
"""
                    # Insert before </body>
                    if '</body>' in original_content:
                        return original_content.replace('</body>', script + '\n</body>')
                    else:
                        return original_content + script

            elif file_path.endswith('.py'):
                # Add dark mode toggle endpoint
                endpoint_code = """

# Dark Mode Toggle Endpoint - Auto-generated by EchoFix
@app.route('/api/dark-mode', methods=['POST'])
def toggle_dark_mode():
    \"\"\"Toggle dark mode preference for user session.\"\"\"
    data = request.get_json()
    dark_mode = data.get('dark_mode', False)
    session['dark_mode'] = dark_mode
    return jsonify({'success': True, 'dark_mode': dark_mode})
"""
                # Add at the end
                return original_content + endpoint_code

        # Default: just add a TODO comment
        return self._add_todo_comment(original_content, issue_spec, file_path)

    def _generate_code_fix_with_openai(
        self,
        file_path: str,
        original_content: str,
        issue_spec: IssueSpec,
        patch_plan: PatchPlan
    ) -> str:
        """Use OpenAI to generate a fixed version of the file."""

        prompt = f"""You are a senior software engineer fixing a bug/implementing a feature.

ISSUE: {issue_spec.title}
PROBLEM: {issue_spec.problem_statement}

PATCH PLAN:
{patch_plan.change_outline}

CURRENT FILE ({file_path}):
```
{original_content[:8000]}
```

Generate the COMPLETE fixed version of this file that implements the required changes.
Only output the fixed file content, no explanations or markdown code blocks.
Make minimal changes - only fix what's needed for this issue.

FIXED FILE CONTENT:"""

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cheap
            messages=[
                {"role": "system", "content": "You are a senior software engineer. Output only the fixed code, no explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=8192
        )

        fixed_content = response.choices[0].message.content.strip()

        # Remove markdown code blocks if OpenAI added them
        if fixed_content.startswith("```"):
            lines = fixed_content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            fixed_content = "\n".join(lines)

        return fixed_content
