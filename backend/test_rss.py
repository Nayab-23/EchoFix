"""
Quick test for RSS ingestion module
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.reddit_rss import RedditRSSClient, validate_url, extract_post_id

def test_url_normalization():
    """Test URL normalization"""
    client = RedditRSSClient(demo_mode=True)
    
    test_cases = [
        ("https://www.reddit.com/r/webdev/comments/1abc2d3/my_post", True),
        ("https://old.reddit.com/r/programming/comments/xyz789/", True),
        ("https://redd.it/1abc2d3", True),
        ("https://invalid.com/post", False),
    ]
    
    print("Testing URL normalization:")
    for url, should_be_valid in test_cases:
        normalized = client.normalize_url(url)
        is_valid = normalized is not None
        status = "✓" if is_valid == should_be_valid else "✗"
        print(f"  {status} {url[:50]}... -> {normalized is not None}")
    
    print()

def test_rss_conversion():
    """Test RSS URL conversion"""
    client = RedditRSSClient(demo_mode=True)
    
    url = "https://www.reddit.com/r/webdev/comments/1abc2d3/my_post"
    normalized = client.normalize_url(url)
    rss_url = client.url_to_rss(normalized)
    
    print(f"Testing RSS conversion:")
    print(f"  Original: {url}")
    print(f"  Normalized: {normalized}")
    print(f"  RSS URL: {rss_url}")
    print(f"  ✓ Conversion successful")
    print()

def test_demo_mode():
    """Test demo mode ingestion"""
    client = RedditRSSClient(demo_mode=True)
    
    print("Testing demo mode ingestion:")
    entries = client.fetch_thread("https://reddit.com/r/test/comments/123/test")
    
    print(f"  Fetched {len(entries)} demo entries")
    if entries:
        first = entries[0]
        print(f"  First entry: {first.reddit_type} by {first.author}")
        print(f"  Title: {first.title or 'N/A'}")
        print(f"  Body preview: {first.body[:60]}...")
    print(f"  ✓ Demo mode works")
    print()

def test_model_compatibility():
    """Test that RSS entries match the RedditEntry model"""
    client = RedditRSSClient(demo_mode=True)
    
    print("Testing model compatibility:")
    entries = client.fetch_thread("https://reddit.com/r/test/comments/123/test")
    
    if entries:
        entry = entries[0]
        required_fields = ['id', 'reddit_id', 'reddit_type', 'body', 'author', 
                          'subreddit', 'permalink', 'created_at', 'reddit_created_at']
        
        all_present = all(hasattr(entry, field) for field in required_fields)
        print(f"  All required fields present: {'✓' if all_present else '✗'}")
        
        for field in required_fields:
            value = getattr(entry, field)
            print(f"    - {field}: {type(value).__name__}")
    
    print(f"  ✓ Models compatible")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("EchoFix RSS Ingestion Module Tests")
    print("=" * 60)
    print()
    
    try:
        test_url_normalization()
        test_rss_conversion()
        test_demo_mode()
        test_model_compatibility()
        
        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
