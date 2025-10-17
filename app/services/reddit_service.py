from typing import List, Dict, Set, Optional
import praw
import re
import time
import logging
from datetime import datetime, timedelta
from functools import wraps
import asyncio

from app.core.config import settings


logger = logging.getLogger(__name__)

class RedditAPIError(Exception):
    """Custom exception for Reddit API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, retry_after: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        self.retry_after = retry_after
        super().__init__(self.message)

class RateLimitManager:
    """Manages Reddit API rate limiting with exponential backoff"""
    
    def __init__(self):
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_reset = 0
        self.backoff_delay = 1  # Start with 1 second
        self.max_backoff = 300  # Max 5 minutes
        self.requests_per_minute = 60  # Reddit's default limit
        
    def wait_if_needed(self):
        """Wait if we're approaching rate limits"""
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self.rate_limit_reset > 60:
            self.request_count = 0
            self.rate_limit_reset = current_time
            self.backoff_delay = 1  # Reset backoff on successful period
        
        # If we're approaching the limit, wait
        if self.request_count >= self.requests_per_minute - 5:  # Leave buffer
            wait_time = 60 - (current_time - self.rate_limit_reset)
            if wait_time > 0:
                logger.warning(f"Rate limit approaching, waiting {wait_time:.1f} seconds")
                time.sleep(wait_time)
                self.request_count = 0
                self.rate_limit_reset = time.time()
        
        # Ensure minimum delay between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < 1:  # Minimum 1 second between requests
            time.sleep(1 - time_since_last)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def handle_rate_limit_error(self, retry_after: Optional[int] = None):
        """Handle rate limit error with exponential backoff"""
        if retry_after:
            wait_time = retry_after
        else:
            wait_time = min(self.backoff_delay, self.max_backoff)
            self.backoff_delay *= 2  # Exponential backoff
        
        logger.warning(f"Rate limited, waiting {wait_time} seconds")
        time.sleep(wait_time)

# Global rate limit manager
rate_limiter = RateLimitManager()

def with_reddit_error_handling(func):
    """Decorator to handle Reddit API errors with retry logic"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                rate_limiter.wait_if_needed()
                return func(*args, **kwargs)
                
            except praw.exceptions.RedditAPIException as e:
                retry_count += 1
                logger.error(f"Reddit API error (attempt {retry_count}/{max_retries}): {e}")
                
                # Handle specific error types
                for subexception in e.items:
                    if subexception.error_type == "RATELIMIT":
                        rate_limiter.handle_rate_limit_error()
                        continue
                    elif subexception.error_type in ["SERVER_ERROR", "TIMEOUT"]:
                        if retry_count < max_retries:
                            time.sleep(2 ** retry_count)  # Exponential backoff
                            continue
                
                if retry_count >= max_retries:
                    raise RedditAPIError(f"Reddit API error after {max_retries} retries: {e}")
                    
            except praw.exceptions.ResponseException as e:
                retry_count += 1
                logger.error(f"Reddit response error (attempt {retry_count}/{max_retries}): {e}")
                
                if e.response.status_code == 429:  # Rate limited
                    retry_after = e.response.headers.get('retry-after')
                    rate_limiter.handle_rate_limit_error(int(retry_after) if retry_after else None)
                    continue
                elif e.response.status_code >= 500:  # Server error
                    if retry_count < max_retries:
                        time.sleep(2 ** retry_count)
                        continue
                
                if retry_count >= max_retries:
                    raise RedditAPIError(
                        f"Reddit response error after {max_retries} retries: {e}",
                        status_code=e.response.status_code
                    )
                    
            except Exception as e:
                logger.error(f"Unexpected error accessing Reddit API: {e}")
                raise RedditAPIError(f"Unexpected Reddit API error: {e}")
        
        raise RedditAPIError(f"Failed after {max_retries} retries")
    
    return wrapper

def get_reddit_client():
    """Get Reddit client with proper error handling"""
    if not (settings.reddit_client_id and settings.reddit_client_secret and settings.reddit_user_agent):
        logger.error("Reddit API credentials not configured")
        return None
    
    try:
        reddit = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
            timeout=30,  # 30 second timeout
        )
        
        # Test the connection
        reddit.user.me()
        return reddit
        
    except praw.exceptions.ResponseException as e:
        logger.error(f"Failed to authenticate with Reddit API: {e}")
        raise RedditAPIError(f"Reddit authentication failed: {e}")
    except Exception as e:
        logger.error(f"Failed to create Reddit client: {e}")
        raise RedditAPIError(f"Reddit client creation failed: {e}")


@with_reddit_error_handling
def find_matching_posts(subreddits: List[str], keywords: List[str], seen_ids: Set[str] | None = None) -> List[Dict]:
    """Find Reddit posts matching keywords with enhanced error handling and rate limiting"""
    reddit = get_reddit_client()
    if not reddit:
        logger.warning("Reddit client not available, returning empty results")
        return []
    
    seen_ids = seen_ids or set()
    out: List[Dict] = []

    # Validate inputs
    if not subreddits or not keywords:
        logger.warning("No subreddits or keywords provided")
        return []

    # Prepare keyword matchers: entries wrapped in /.../ are treated as regex
    regex_patterns = []
    plain_keywords = []
    invalid_patterns = []
    
    for kw in keywords:
        if not kw or not isinstance(kw, str):
            continue
            
        kw = kw.strip()
        if not kw:
            continue
            
        if len(kw) >= 3 and kw.startswith('/') and kw.endswith('/'):
            try:
                pattern = re.compile(kw[1:-1], re.IGNORECASE)
                regex_patterns.append(pattern)
                logger.debug(f"Added regex pattern: {kw}")
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{kw}': {e}, treating as plain text")
                invalid_patterns.append(kw)
                plain_keywords.append(kw[1:-1])  # Remove slashes and treat as plain
        else:
            plain_keywords.append(kw.lower())

    if invalid_patterns:
        logger.warning(f"Found {len(invalid_patterns)} invalid regex patterns")

    logger.info(f"Searching {len(subreddits)} subreddits with {len(plain_keywords)} plain keywords and {len(regex_patterns)} regex patterns")

    # Process each subreddit
    for sub in subreddits:
        try:
            logger.debug(f"Scanning subreddit: r/{sub}")
            
            # Validate subreddit exists and is accessible
            subreddit = reddit.subreddit(sub)
            
            # Get new posts with error handling
            posts_processed = 0
            posts_matched = 0
            
            for submission in subreddit.new(limit=50):
                posts_processed += 1
                
                # Skip if already seen
                if submission.id in seen_ids:
                    continue
                
                # Extract post content safely
                try:
                    title = submission.title or ""
                    selftext = submission.selftext or ""
                    author = str(submission.author) if submission.author else "[deleted]"
                    
                    # Handle potential None values
                    score = getattr(submission, 'score', 0) or 0
                    num_comments = getattr(submission, 'num_comments', 0) or 0
                    
                except Exception as e:
                    logger.warning(f"Error extracting data from post {submission.id}: {e}")
                    continue

                # Perform matching
                title_lower = title.lower()
                selftext_lower = selftext.lower()
                
                # Plain text matching
                matched_plain = []
                for k in plain_keywords:
                    if k and (k in title_lower or k in selftext_lower):
                        matched_plain.append(k)
                
                # Regex matching
                matched_regex = []
                for pattern in regex_patterns:
                    try:
                        if pattern.search(title) or pattern.search(selftext):
                            matched_regex.append(f'/{pattern.pattern}/')
                    except Exception as e:
                        logger.warning(f"Error applying regex pattern {pattern.pattern}: {e}")
                
                matched = matched_plain + matched_regex
                
                if matched:
                    posts_matched += 1
                    try:
                        post_data = {
                            "id": submission.id,
                            "subreddit": sub,
                            "title": title,
                            "url": f"https://www.reddit.com{submission.permalink}",
                            "author": author,
                            "content": selftext,
                            "score": score,
                            "num_comments": num_comments,
                            "keywords_matched": ",".join(matched),
                            "created_utc": getattr(submission, 'created_utc', time.time()),
                        }
                        out.append(post_data)
                        logger.debug(f"Matched post: {title[:50]}... in r/{sub}")
                        
                    except Exception as e:
                        logger.error(f"Error processing matched post {submission.id}: {e}")
            
            logger.info(f"r/{sub}: processed {posts_processed} posts, matched {posts_matched}")
            
        except praw.exceptions.Redirect:
            logger.warning(f"Subreddit r/{sub} does not exist or is private")
            continue
        except praw.exceptions.Forbidden:
            logger.warning(f"Access forbidden to subreddit r/{sub}")
            continue
        except Exception as e:
            logger.error(f"Error scanning subreddit r/{sub}: {e}")
            continue

    logger.info(f"Total posts found: {len(out)}")
    return out

def validate_subreddit_access(subreddit_name: str) -> bool:
    """Validate that a subreddit exists and is accessible"""
    try:
        reddit = get_reddit_client()
        if not reddit:
            return False
        
        subreddit = reddit.subreddit(subreddit_name)
        # Try to access the subreddit info
        _ = subreddit.display_name
        return True
        
    except praw.exceptions.Redirect:
        logger.warning(f"Subreddit r/{subreddit_name} does not exist")
        return False
    except praw.exceptions.Forbidden:
        logger.warning(f"Access forbidden to subreddit r/{subreddit_name}")
        return False
    except Exception as e:
        logger.error(f"Error validating subreddit r/{subreddit_name}: {e}")
        return False

def test_reddit_connection() -> Dict[str, any]:
    """Test Reddit API connection and return status"""
    try:
        reddit = get_reddit_client()
        if not reddit:
            return {
                "status": "error",
                "message": "Reddit credentials not configured",
                "authenticated": False
            }
        
        # Test authentication
        user = reddit.user.me()
        
        # Test rate limit info
        rate_limit_info = {
            "requests_remaining": getattr(reddit.auth, 'limits', {}).get('remaining', 'unknown'),
            "requests_used": getattr(reddit.auth, 'limits', {}).get('used', 'unknown'),
            "reset_timestamp": getattr(reddit.auth, 'limits', {}).get('reset_timestamp', 'unknown')
        }
        
        return {
            "status": "success",
            "message": "Reddit API connection successful",
            "authenticated": True,
            "user": str(user) if user else "authenticated",
            "rate_limit": rate_limit_info
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Reddit API connection failed: {str(e)}",
            "authenticated": False
        }

@with_reddit_error_handling
def get_subreddit_guidelines(subreddit_name: str) -> Dict[str, any]:
    """Fetch subreddit rules and guidelines"""
    reddit = get_reddit_client()
    if not reddit:
        logger.warning("Reddit client not available")
        return {"rules": [], "description": "", "error": "Reddit client not configured"}
    
    try:
        subreddit = reddit.subreddit(subreddit_name)
        
        # Get subreddit rules
        rules = []
        try:
            for rule in subreddit.rules:
                rules.append({
                    "short_name": rule.short_name,
                    "description": rule.description,
                    "kind": rule.kind,
                    "violation_reason": rule.violation_reason
                })
        except Exception as e:
            logger.warning(f"Could not fetch rules for r/{subreddit_name}: {e}")
        
        # Get subreddit description/sidebar
        description = ""
        try:
            description = subreddit.description or subreddit.public_description or ""
        except Exception as e:
            logger.warning(f"Could not fetch description for r/{subreddit_name}: {e}")
        
        return {
            "subreddit": subreddit_name,
            "rules": rules,
            "description": description,
            "display_name": subreddit.display_name,
            "subscribers": getattr(subreddit, 'subscribers', 0)
        }
        
    except praw.exceptions.Redirect:
        logger.warning(f"Subreddit r/{subreddit_name} does not exist")
        return {"rules": [], "description": "", "error": "Subreddit not found"}
    except praw.exceptions.Forbidden:
        logger.warning(f"Access forbidden to subreddit r/{subreddit_name}")
        return {"rules": [], "description": "", "error": "Access forbidden"}
    except Exception as e:
        logger.error(f"Error fetching guidelines for r/{subreddit_name}: {e}")
        return {"rules": [], "description": "", "error": str(e)}



