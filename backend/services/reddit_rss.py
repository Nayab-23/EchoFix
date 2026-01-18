"""
Reddit RSS ingestion service for EchoFix.
Fetches Reddit thread RSS feeds without requiring OAuth approval.
"""

import os
import re
import logging
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin
from uuid import uuid4
import xml.etree.ElementTree as ET

import requests

from models import RedditEntry

logger = logging.getLogger(__name__)


class RedditRSSClient:
    """
    Reddit RSS feed ingestion client.
    Fetches Reddit threads via RSS without OAuth.
    """
    
    # Regex patterns for Reddit URLs
    REDDIT_URL_PATTERN = re.compile(
        r'^https?://(?:www\.|old\.|np\.|new\.)?reddit\.com/r/([^/]+)/comments/([a-z0-9]+)(?:/([^/]+))?',
        re.IGNORECASE
    )
    REDD_IT_PATTERN = re.compile(r'^https?://redd\.it/([a-z0-9]+)', re.IGNORECASE)
    
    def __init__(self, demo_mode: bool = False):
        """
        Initialize RSS client.
        
        Args:
            demo_mode: If True, use fixtures instead of live requests
        """
        self.demo_mode = demo_mode or os.getenv("DEMO_MODE", "false").lower() == "true"
        self.user_agent = os.getenv("REDDIT_USER_AGENT", "EchoFix/1.0 (Hackathon Demo)")
        self.base_domain = os.getenv("REDDIT_RSS_BASE_DOMAIN", "old.reddit.com")
        self.timeout = int(os.getenv("REDDIT_RSS_TIMEOUT", "10"))
        
        logger.info(f"RedditRSSClient initialized - Demo Mode: {self.demo_mode}")
    
    def normalize_url(self, url: str) -> Optional[str]:
        """
        Normalize Reddit URL to canonical form.
        
        Args:
            url: Reddit URL (any format)
        
        Returns:
            Normalized URL or None if invalid
        """
        url = url.strip()
        
        # Handle redd.it shortlinks
        redd_match = self.REDD_IT_PATTERN.match(url)
        if redd_match:
            post_id = redd_match.group(1)
            # Convert to full URL (we'll need to fetch redirect to get subreddit)
            return f"https://{self.base_domain}/comments/{post_id}"
        
        # Handle standard Reddit URLs
        reddit_match = self.REDDIT_URL_PATTERN.match(url)
        if reddit_match:
            subreddit = reddit_match.group(1)
            post_id = reddit_match.group(2)
            slug = reddit_match.group(3) or ""
            
            if slug:
                return f"https://{self.base_domain}/r/{subreddit}/comments/{post_id}/{slug}"
            else:
                return f"https://{self.base_domain}/r/{subreddit}/comments/{post_id}"
        
        logger.warning(f"Invalid Reddit URL format: {url}")
        return None
    
    def url_to_rss(self, url: str) -> Optional[str]:
        """
        Convert Reddit thread URL to RSS feed URL.
        
        Args:
            url: Normalized Reddit URL
        
        Returns:
            RSS feed URL or None
        """
        if not url:
            return None
        
        # Simply append .rss to the URL
        rss_url = f"{url}.rss"
        logger.info(f"RSS URL: {rss_url}")
        return rss_url
    
    def fetch_thread(
        self,
        url: str,
        max_items: Optional[int] = None
    ) -> List[RedditEntry]:
        """
        Fetch a Reddit thread via RSS.
        
        Args:
            url: Reddit thread URL (any format)
            max_items: Maximum items to return
        
        Returns:
            List of RedditEntry objects (post + comments)
        """
        if self.demo_mode:
            return self._load_demo_entries(max_items)
        
        # Normalize URL
        normalized_url = self.normalize_url(url)
        if not normalized_url:
            logger.error(f"Could not normalize URL: {url}")
            return []
        
        # Convert to RSS
        rss_url = self.url_to_rss(normalized_url)
        if not rss_url:
            return []
        
        # Fetch RSS feed
        try:
            headers = {
                'User-Agent': self.user_agent
            }
            
            logger.info(f"Fetching RSS from: {rss_url}")
            response = requests.get(rss_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse RSS
            entries = self._parse_rss(response.content, normalized_url)
            
            if max_items:
                entries = entries[:max_items]
            
            logger.info(f"Fetched {len(entries)} items from {url}")
            return entries
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch RSS from {rss_url}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error processing RSS feed: {e}")
            return []
    
    def fetch_multiple_threads(
        self,
        urls: List[str],
        max_items_per_thread: Optional[int] = None
    ) -> List[RedditEntry]:
        """
        Fetch multiple Reddit threads.
        
        Args:
            urls: List of Reddit thread URLs
            max_items_per_thread: Max items per thread
        
        Returns:
            Combined list of RedditEntry objects
        """
        all_entries = []
        
        for url in urls:
            entries = self.fetch_thread(url, max_items=max_items_per_thread)
            all_entries.extend(entries)
        
        logger.info(f"Fetched {len(all_entries)} total entries from {len(urls)} threads")
        return all_entries
    
    def _parse_rss(self, xml_content: bytes, thread_url: str) -> List[RedditEntry]:
        """
        Parse Reddit RSS feed XML.
        
        Args:
            xml_content: RSS XML content
            thread_url: Original thread URL
        
        Returns:
            List of RedditEntry objects
        """
        entries = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Reddit RSS uses Atom format
            # Namespace handling
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'content': 'http://purl.org/rss/1.0/modules/content/'
            }
            
            # Try Atom feed first (Reddit's format)
            atom_entries = root.findall('.//atom:entry', ns)
            
            if atom_entries:
                for item in atom_entries:
                    entry = self._parse_atom_entry(item, ns, thread_url)
                    if entry:
                        entries.append(entry)
            else:
                # Fallback to RSS 2.0
                rss_items = root.findall('.//item')
                for item in rss_items:
                    entry = self._parse_rss_item(item, thread_url)
                    if entry:
                        entries.append(entry)
            
            logger.info(f"Parsed {len(entries)} entries from RSS feed")
            
        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
        except Exception as e:
            logger.error(f"Error parsing RSS: {e}")
        
        return entries
    
    def _parse_atom_entry(
        self,
        item: ET.Element,
        ns: Dict[str, str],
        thread_url: str
    ) -> Optional[RedditEntry]:
        """Parse a single Atom entry (Reddit format)."""
        try:
            # Extract fields
            title_elem = item.find('atom:title', ns)
            title = title_elem.text if title_elem is not None else None
            
            # Content
            content_elem = item.find('atom:content', ns)
            body = ""
            if content_elem is not None:
                body = content_elem.text or ""
                # Strip HTML tags (basic)
                body = re.sub(r'<[^>]+>', '', body)
                body = body.strip()
            
            # Link (permalink)
            link_elem = item.find('atom:link[@href]', ns)
            permalink = link_elem.get('href') if link_elem is not None else thread_url
            
            # Author
            author_elem = item.find('atom:author/atom:name', ns)
            author = author_elem.text if author_elem is not None else "[unknown]"
            
            # Published date
            published_elem = item.find('atom:published', ns) or item.find('atom:updated', ns)
            created_at = datetime.now(timezone.utc)
            if published_elem is not None:
                try:
                    created_at = datetime.fromisoformat(published_elem.text.replace('Z', '+00:00'))
                except:
                    pass
            
            # ID (use link hash)
            link_hash = hashlib.md5(permalink.encode()).hexdigest()[:16]
            
            # Extract reddit_id from permalink
            reddit_id = self._extract_reddit_id(permalink)
            
            # Determine type (post vs comment)
            reddit_type = "comment" if "/comments/" in permalink and permalink.count('/') > 6 else "post"
            
            # Extract subreddit from URL
            subreddit = self._extract_subreddit(permalink)
            
            return RedditEntry(
                id=uuid4(),
                created_at=datetime.now(timezone.utc),
                reddit_id=reddit_id,
                reddit_type=reddit_type,
                title=title,
                body=body,
                author=author,
                subreddit=subreddit,
                permalink=permalink,
                score=None,  # RSS doesn't include scores
                num_comments=0,
                reddit_created_at=created_at
            )
            
        except Exception as e:
            logger.error(f"Error parsing Atom entry: {e}")
            return None
    
    def _parse_rss_item(
        self,
        item: ET.Element,
        thread_url: str
    ) -> Optional[RedditEntry]:
        """Parse a single RSS 2.0 item."""
        try:
            title_elem = item.find('title')
            title = title_elem.text if title_elem is not None else None
            
            description_elem = item.find('description')
            body = description_elem.text if description_elem is not None else ""
            body = re.sub(r'<[^>]+>', '', body).strip()
            
            link_elem = item.find('link')
            permalink = link_elem.text if link_elem is not None else thread_url
            
            author_elem = item.find('author')
            author = author_elem.text if author_elem is not None else "[unknown]"
            
            pubdate_elem = item.find('pubDate')
            created_at = datetime.now(timezone.utc)
            if pubdate_elem is not None:
                try:
                    from email.utils import parsedate_to_datetime
                    created_at = parsedate_to_datetime(pubdate_elem.text)
                except:
                    pass
            
            link_hash = hashlib.md5(permalink.encode()).hexdigest()[:16]
            reddit_id = self._extract_reddit_id(permalink)
            reddit_type = "comment" if "/comments/" in permalink and permalink.count('/') > 6 else "post"
            subreddit = self._extract_subreddit(permalink)
            
            return RedditEntry(
                id=uuid4(),
                created_at=datetime.now(timezone.utc),
                reddit_id=reddit_id,
                reddit_type=reddit_type,
                title=title,
                body=body,
                author=author,
                subreddit=subreddit,
                permalink=permalink,
                score=None,
                num_comments=0,
                reddit_created_at=created_at
            )
            
        except Exception as e:
            logger.error(f"Error parsing RSS item: {e}")
            return None
    
    def _extract_reddit_id(self, permalink: str) -> str:
        """Extract Reddit ID from permalink."""
        # Try to extract post/comment ID from URL
        parts = permalink.split('/')
        if 'comments' in parts:
            idx = parts.index('comments')
            if len(parts) > idx + 1:
                return parts[idx + 1]
        
        # Fallback: use hash of permalink
        return hashlib.md5(permalink.encode()).hexdigest()[:8]
    
    def _extract_subreddit(self, permalink: str) -> str:
        """Extract subreddit name from permalink."""
        match = re.search(r'/r/([^/]+)/', permalink)
        if match:
            return match.group(1)
        return "unknown"
    
    def _load_demo_entries(self, max_items: Optional[int] = None) -> List[RedditEntry]:
        """Load demo entries from fixtures."""
        from pathlib import Path
        import json
        
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "reddit_rss_demo.json"
        
        if not fixtures_path.exists():
            logger.warning(f"Demo fixture not found at {fixtures_path}, returning empty list")
            return []
        
        try:
            with open(fixtures_path, 'r') as f:
                data = json.load(f)
            
            entries = [RedditEntry(**item) for item in data]
            
            if max_items:
                entries = entries[:max_items]
            
            logger.info(f"Loaded {len(entries)} demo entries from fixture")
            return entries
            
        except Exception as e:
            logger.error(f"Error loading demo fixture: {e}")
            return []


# Utility functions for testing
def validate_url(url: str) -> bool:
    """Validate if a URL is a valid Reddit thread URL."""
    client = RedditRSSClient(demo_mode=True)
    return client.normalize_url(url) is not None


def extract_post_id(url: str) -> Optional[str]:
    """Extract post ID from Reddit URL."""
    client = RedditRSSClient(demo_mode=True)
    normalized = client.normalize_url(url)
    if normalized:
        return client._extract_reddit_id(normalized)
    return None
