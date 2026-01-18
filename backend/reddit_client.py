"""
Reddit ingestion client for EchoFix.
Supports live mode (PRAW) and demo mode (fixtures).
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from uuid import uuid4

import praw
from praw.models import Submission, Comment

from models import RedditEntry

logger = logging.getLogger(__name__)


class RedditClient:
    """
    Reddit data ingestion client.
    Supports both live API calls and demo mode with fixtures.
    """
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_agent: Optional[str] = None,
        demo_mode: bool = False
    ):
        """
        Initialize Reddit client.
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: Reddit API user agent
            demo_mode: If True, use fixtures instead of live API
        """
        self.demo_mode = demo_mode or os.getenv("DEMO_MODE", "false").lower() == "true"
        
        if not self.demo_mode:
            self.client_id = client_id or os.getenv("REDDIT_CLIENT_ID")
            self.client_secret = client_secret or os.getenv("REDDIT_CLIENT_SECRET")
            self.user_agent = user_agent or os.getenv("REDDIT_USER_AGENT", "EchoFix/1.0")
            
            if not all([self.client_id, self.client_secret]):
                logger.warning("Reddit credentials missing, falling back to demo mode")
                self.demo_mode = True
            else:
                try:
                    self.reddit = praw.Reddit(
                        client_id=self.client_id,
                        client_secret=self.client_secret,
                        user_agent=self.user_agent
                    )
                    logger.info("Reddit client initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize Reddit client: {e}")
                    self.demo_mode = True
        
        if self.demo_mode:
            logger.info("Running in DEMO MODE - using fixtures")
            self.fixtures_path = Path(__file__).parent / "fixtures"
    
    def search_subreddits(
        self,
        subreddits: List[str],
        keywords: List[str],
        limit: int = 100,
        time_filter: str = "day"
    ) -> List[RedditEntry]:
        """
        Search multiple subreddits for keywords.
        
        Args:
            subreddits: List of subreddit names (without r/)
            keywords: List of keywords to search
            limit: Max results per subreddit
            time_filter: Time filter (hour, day, week, month, year, all)
        
        Returns:
            List of RedditEntry objects
        """
        if self.demo_mode:
            return self._load_demo_entries("reddit_search.json", limit)
        
        entries = []
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Search for each keyword
                for keyword in keywords:
                    submissions = subreddit.search(
                        keyword,
                        time_filter=time_filter,
                        limit=limit
                    )
                    
                    for submission in submissions:
                        entry = self._submission_to_entry(submission)
                        entries.append(entry)
                        
                        # Also collect top comments
                        submission.comments.replace_more(limit=0)
                        for comment in submission.comments[:5]:  # Top 5 comments
                            comment_entry = self._comment_to_entry(comment, submission)
                            entries.append(comment_entry)
                
            except Exception as e:
                logger.error(f"Error searching r/{subreddit_name}: {e}")
        
        logger.info(f"Collected {len(entries)} entries from subreddit search")
        return entries
    
    def monitor_subreddit_new(
        self,
        subreddit_name: str,
        limit: int = 50
    ) -> List[RedditEntry]:
        """
        Get latest posts from a subreddit.
        
        Args:
            subreddit_name: Subreddit name (without r/)
            limit: Max number of posts
        
        Returns:
            List of RedditEntry objects
        """
        if self.demo_mode:
            return self._load_demo_entries("reddit_new.json", limit)
        
        entries = []
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            for submission in subreddit.new(limit=limit):
                entry = self._submission_to_entry(submission)
                entries.append(entry)
                
                # Collect top comments
                submission.comments.replace_more(limit=0)
                for comment in submission.comments[:5]:
                    comment_entry = self._comment_to_entry(comment, submission)
                    entries.append(comment_entry)
            
            logger.info(f"Collected {len(entries)} entries from r/{subreddit_name}")
        except Exception as e:
            logger.error(f"Error monitoring r/{subreddit_name}: {e}")
        
        return entries
    
    def get_post_with_comments(
        self,
        post_id: str
    ) -> List[RedditEntry]:
        """
        Get a specific post and all its comments.
        
        Args:
            post_id: Reddit post ID
        
        Returns:
            List of RedditEntry objects (post + comments)
        """
        if self.demo_mode:
            return self._load_demo_entries("reddit_post.json")
        
        entries = []
        try:
            submission = self.reddit.submission(id=post_id)
            
            # Add the post
            entry = self._submission_to_entry(submission)
            entries.append(entry)
            
            # Add all comments
            submission.comments.replace_more(limit=None)
            for comment in submission.comments.list():
                comment_entry = self._comment_to_entry(comment, submission)
                entries.append(comment_entry)
            
            logger.info(f"Collected post + {len(entries)-1} comments")
        except Exception as e:
            logger.error(f"Error fetching post {post_id}: {e}")
        
        return entries
    
    def track_product_mentions(
        self,
        product_names: List[str],
        subreddits: List[str] = ["programming", "technology", "webdev"],
        limit: int = 100,
        time_filter: str = "week"
    ) -> List[RedditEntry]:
        """
        Track mentions of product names across subreddits.
        
        Args:
            product_names: List of product names to track
            subreddits: Subreddits to monitor
            limit: Max results per product per subreddit
            time_filter: Time filter
        
        Returns:
            List of RedditEntry objects
        """
        all_entries = []
        
        for product in product_names:
            entries = self.search_subreddits(
                subreddits=subreddits,
                keywords=[product],
                limit=limit,
                time_filter=time_filter
            )
            all_entries.extend(entries)
        
        # Deduplicate by reddit_id
        seen_ids = set()
        unique_entries = []
        for entry in all_entries:
            if entry.reddit_id not in seen_ids:
                seen_ids.add(entry.reddit_id)
                unique_entries.append(entry)
        
        logger.info(f"Tracked {len(unique_entries)} unique mentions")
        return unique_entries

    def fetch_entry_score(self, reddit_id: str, reddit_type: str) -> Optional[int]:
        """Fetch score for a post or comment using PRAW when available."""
        if self.demo_mode:
            return None

        try:
            if reddit_type == "comment":
                comment = self.reddit.comment(id=reddit_id)
                return comment.score
            submission = self.reddit.submission(id=reddit_id)
            return submission.score
        except Exception as e:
            logger.warning("Failed to fetch score via PRAW for %s: %s", reddit_id, e)
            return None
    
    def _submission_to_entry(self, submission: Submission) -> RedditEntry:
        """Convert PRAW Submission to RedditEntry."""
        # Extract image URLs
        image_urls = []
        video_url = None
        
        if hasattr(submission, 'preview') and 'images' in submission.preview:
            for img in submission.preview['images']:
                if 'source' in img:
                    image_urls.append(img['source']['url'])
        
        if hasattr(submission, 'is_video') and submission.is_video:
            if hasattr(submission, 'media') and submission.media:
                video_url = submission.media.get('reddit_video', {}).get('fallback_url')
        
        return RedditEntry(
            id=uuid4(),
            created_at=datetime.now(timezone.utc),
            reddit_id=submission.id,
            reddit_type="post",
            title=submission.title,
            body=submission.selftext or "",
            author=str(submission.author) if submission.author else "[deleted]",
            subreddit=str(submission.subreddit),
            permalink=f"https://reddit.com{submission.permalink}",
            score=submission.score,
            num_comments=submission.num_comments,
            image_urls=image_urls,
            video_url=video_url,
            reddit_created_at=datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
        )
    
    def _comment_to_entry(self, comment: Comment, submission: Submission) -> RedditEntry:
        """Convert PRAW Comment to RedditEntry."""
        return RedditEntry(
            id=uuid4(),
            created_at=datetime.now(timezone.utc),
            reddit_id=comment.id,
            reddit_type="comment",
            title=None,
            body=comment.body,
            author=str(comment.author) if comment.author else "[deleted]",
            subreddit=str(submission.subreddit),
            permalink=f"https://reddit.com{comment.permalink}",
            score=comment.score,
            num_comments=0,
            reddit_created_at=datetime.fromtimestamp(comment.created_utc, tz=timezone.utc)
        )
    
    def _load_demo_entries(self, fixture_name: str, limit: Optional[int] = None) -> List[RedditEntry]:
        """Load entries from demo fixtures."""
        fixture_path = self.fixtures_path / fixture_name
        
        if not fixture_path.exists():
            logger.warning(f"Fixture {fixture_name} not found, returning empty list")
            return []
        
        try:
            with open(fixture_path, 'r') as f:
                data = json.load(f)
            
            entries = [RedditEntry(**item) for item in (data[:limit] if limit else data)]
            logger.info(f"Loaded {len(entries)} entries from {fixture_name}")
            return entries
        except Exception as e:
            logger.error(f"Error loading fixture {fixture_name}: {e}")
            return []
    
    def post_comment(self, parent_id: str, text: str) -> str:
        """
        Post a comment as a reply to a Reddit post/comment.

        Args:
            parent_id: Reddit ID of parent (comment or submission)
            text: Comment text to post

        Returns:
            Comment ID of the posted comment
        """
        if self.demo_mode:
            # In demo mode, generate a fake comment ID
            demo_id = f"demo_{uuid4().hex[:7]}"
            logger.info(f"DEMO: Would post comment to {parent_id}: {text[:100]}...")
            return demo_id

        try:
            # Get the parent thing (comment or submission)
            if parent_id.startswith('t3_'):
                parent = self.reddit.submission(id=parent_id.replace('t3_', ''))
            elif parent_id.startswith('t1_'):
                parent = self.reddit.comment(id=parent_id.replace('t1_', ''))
            else:
                # Try without prefix
                try:
                    parent = self.reddit.comment(id=parent_id)
                except:
                    parent = self.reddit.submission(id=parent_id)

            # Post the comment
            comment = parent.reply(text)
            logger.info(f"Posted comment {comment.id} to {parent_id}")
            return comment.id

        except Exception as e:
            logger.error(f"Failed to post comment: {e}")
            raise

    def create_demo_fixtures(entries: List[RedditEntry], filename: str):
        """
        Helper to create demo fixtures from live data.
        Run this once with live credentials to generate fixtures.
        """
        fixtures_path = Path(__file__).parent / "fixtures"
        fixtures_path.mkdir(exist_ok=True)

        filepath = fixtures_path / filename

        data = [entry.model_dump(mode='json') for entry in entries]

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Created fixture: {filepath} with {len(entries)} entries")
