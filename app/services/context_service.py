from typing import List, Dict, Optional, Tuple
import httpx
import re
import asyncio
from datetime import datetime
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

SERP_URL = "https://serpapi.com/search.json"
YOUTUBE_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_DETAILS_URL = "https://www.googleapis.com/youtube/v3/videos"


class ContextData:
    """Structured context data from research"""
    def __init__(self):
        self.google_results: List[Dict] = []
        self.youtube_results: List[Dict] = []
        self.synthesized_context: str = ""
        self.key_insights: List[str] = []
        self.sources: List[str] = []
        self.research_quality: float = 0.0
        self.timestamp: datetime = datetime.utcnow()


class ContextResearchService:
    """Enhanced context research service with Google Search and YouTube integration"""
    
    def __init__(self):
        self.max_retries = 3
        self.timeout = 15
        
    async def research_post_context(
        self, 
        post_title: str, 
        post_content: str = "", 
        max_google_results: int = 5,
        max_youtube_results: int = 3
    ) -> ContextData:
        """
        Research comprehensive context for a Reddit post
        
        Args:
            post_title: The Reddit post title
            post_content: The Reddit post content/body
            max_google_results: Maximum Google search results to fetch
            max_youtube_results: Maximum YouTube videos to fetch
            
        Returns:
            ContextData object with research results and synthesized context
        """
        context_data = ContextData()
        
        try:
            # Extract search queries from post
            search_queries = self._extract_search_queries(post_title, post_content)
            
            if not search_queries:
                logger.warning("No search queries extracted from post")
                return context_data
            
            # Perform parallel research
            tasks = []
            for query in search_queries[:2]:  # Limit to top 2 queries to avoid rate limits
                tasks.append(self._fetch_google_results(query, max_google_results))
                tasks.append(self._fetch_youtube_results(query, max_youtube_results))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            google_results = []
            youtube_results = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Research task {i} failed: {result}")
                    continue
                    
                if i % 2 == 0:  # Google results
                    google_results.extend(result)
                else:  # YouTube results
                    youtube_results.extend(result)
            
            context_data.google_results = google_results[:max_google_results]
            context_data.youtube_results = youtube_results[:max_youtube_results]
            
            # Synthesize context
            context_data.synthesized_context = self._synthesize_context(
                post_title, post_content, context_data
            )
            
            # Extract key insights
            context_data.key_insights = self._extract_key_insights(context_data)
            
            # Collect sources
            context_data.sources = self._collect_sources(context_data)
            
            # Calculate research quality
            context_data.research_quality = self._calculate_research_quality(context_data)
            
            logger.info(f"Context research completed with quality score: {context_data.research_quality}")
            
        except Exception as e:
            logger.error(f"Context research failed: {e}")
            context_data.synthesized_context = "Context research unavailable due to API limitations."
        
        return context_data
    
    def _extract_search_queries(self, post_title: str, post_content: str = "") -> List[str]:
        """Extract relevant search queries from post title and content"""
        queries = []
        
        # Combine title and content
        full_text = f"{post_title} {post_content}".strip()
        
        # Remove Reddit-specific terms
        reddit_terms = ['reddit', 'upvote', 'downvote', 'karma', 'subreddit', 'op', 'tldr', 'eli5']
        for term in reddit_terms:
            full_text = re.sub(rf'\b{term}\b', '', full_text, flags=re.IGNORECASE)
        
        # Extract main topic (use title as primary query)
        if post_title:
            # Clean up title for search
            clean_title = re.sub(r'[^\w\s]', ' ', post_title)
            clean_title = ' '.join(clean_title.split())  # Remove extra spaces
            if len(clean_title) > 5:
                queries.append(clean_title)
        
        # Extract key phrases (noun phrases, technical terms)
        key_phrases = self._extract_key_phrases(full_text)
        queries.extend(key_phrases[:2])  # Add top 2 key phrases
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for query in queries:
            if query.lower() not in seen and len(query) > 3:
                seen.add(query.lower())
                unique_queries.append(query)
        
        return unique_queries[:3]  # Limit to 3 queries max
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text using simple NLP techniques"""
        phrases = []
        
        # Find quoted phrases
        quoted = re.findall(r'"([^"]+)"', text)
        phrases.extend([q for q in quoted if len(q.split()) <= 4])
        
        # Find capitalized terms (potential proper nouns/brands)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        phrases.extend([c for c in capitalized if len(c.split()) <= 3])
        
        # Find technical terms (words with numbers, hyphens, or mixed case)
        technical = re.findall(r'\b\w*[A-Z]\w*\b|\b\w*\d+\w*\b|\b\w+-\w+\b', text)
        phrases.extend([t for t in technical if 3 <= len(t) <= 20])
        
        return phrases[:5]  # Return top 5 phrases
    
    async def _fetch_google_results(self, query: str, num: int = 5) -> List[Dict]:
        """Fetch Google search results with enhanced error handling"""
        if not settings.serpapi_api_key:
            logger.warning("SerpAPI key not configured")
            return []
        
        params = {
            "q": query,
            "api_key": settings.serpapi_api_key,
            "num": num,
            "hl": "en",
            "gl": "us"
        }
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(SERP_URL, params=params)
                    response.raise_for_status()
                    data = response.json()
                    
                    results = []
                    for result in data.get("organic_results", [])[:num]:
                        results.append({
                            "title": result.get("title", ""),
                            "snippet": result.get("snippet", ""),
                            "url": result.get("link", ""),
                            "source": "google"
                        })
                    
                    return results
                    
            except Exception as e:
                logger.warning(f"Google search attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    return []
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return []
    
    async def _fetch_youtube_results(self, query: str, num: int = 3) -> List[Dict]:
        """Fetch YouTube search results with video details"""
        if not settings.youtube_api_key:
            logger.warning("YouTube API key not configured")
            return []
        
        search_params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": num,
            "key": settings.youtube_api_key,
            "order": "relevance",
            "safeSearch": "moderate"
        }
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    # Search for videos
                    search_response = await client.get(YOUTUBE_URL, params=search_params)
                    search_response.raise_for_status()
                    search_data = search_response.json()
                    
                    items = search_data.get("items", [])
                    if not items:
                        return []
                    
                    # Get video IDs for details
                    video_ids = [item["id"]["videoId"] for item in items]
                    
                    # Fetch video details
                    details_params = {
                        "part": "snippet,statistics,contentDetails",
                        "id": ",".join(video_ids),
                        "key": settings.youtube_api_key
                    }
                    
                    details_response = await client.get(YOUTUBE_DETAILS_URL, params=details_params)
                    details_response.raise_for_status()
                    details_data = details_response.json()
                    
                    results = []
                    for item in details_data.get("items", []):
                        snippet = item.get("snippet", {})
                        stats = item.get("statistics", {})
                        
                        results.append({
                            "title": snippet.get("title", ""),
                            "description": snippet.get("description", "")[:200] + "...",
                            "url": f"https://www.youtube.com/watch?v={item['id']}",
                            "channel": snippet.get("channelTitle", ""),
                            "view_count": stats.get("viewCount", "0"),
                            "like_count": stats.get("likeCount", "0"),
                            "published_at": snippet.get("publishedAt", ""),
                            "source": "youtube"
                        })
                    
                    return results
                    
            except Exception as e:
                logger.warning(f"YouTube search attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    return []
                await asyncio.sleep(2 ** attempt)
        
        return []
    
    def _synthesize_context(self, post_title: str, post_content: str, context_data: ContextData) -> str:
        """Synthesize research results into coherent context"""
        context_parts = []
        
        # Add Google search insights
        if context_data.google_results:
            google_insights = []
            for result in context_data.google_results[:3]:  # Top 3 results
                if result.get("snippet"):
                    google_insights.append(f"• {result['snippet'][:100]}...")
            
            if google_insights:
                context_parts.append("Web Search Insights:\n" + "\n".join(google_insights))
        
        # Add YouTube insights
        if context_data.youtube_results:
            youtube_insights = []
            for result in context_data.youtube_results[:2]:  # Top 2 videos
                if result.get("description"):
                    youtube_insights.append(f"• Video: {result['title']} - {result['description'][:80]}...")
            
            if youtube_insights:
                context_parts.append("Video Content Insights:\n" + "\n".join(youtube_insights))
        
        # Combine context
        if context_parts:
            return "\n\n".join(context_parts)
        else:
            return "Limited context available from research."
    
    def _extract_key_insights(self, context_data: ContextData) -> List[str]:
        """Extract key insights from research results"""
        insights = []
        
        # Extract insights from Google results
        for result in context_data.google_results[:3]:
            snippet = result.get("snippet", "")
            if snippet:
                # Look for key facts, numbers, or important statements
                sentences = snippet.split('. ')
                for sentence in sentences:
                    if any(keyword in sentence.lower() for keyword in 
                          ['important', 'key', 'main', 'primary', 'best', 'top', 'most']):
                        insights.append(sentence.strip())
                        break
        
        # Extract insights from YouTube results
        for result in context_data.youtube_results[:2]:
            title = result.get("title", "")
            if title and any(keyword in title.lower() for keyword in 
                           ['how to', 'guide', 'tutorial', 'tips', 'review']):
                insights.append(f"Video guide available: {title}")
        
        return insights[:5]  # Limit to 5 key insights
    
    def _collect_sources(self, context_data: ContextData) -> List[str]:
        """Collect source URLs from research results"""
        sources = []
        
        for result in context_data.google_results:
            if result.get("url"):
                sources.append(result["url"])
        
        for result in context_data.youtube_results:
            if result.get("url"):
                sources.append(result["url"])
        
        return sources
    
    def _calculate_research_quality(self, context_data: ContextData) -> float:
        """Calculate quality score for research results"""
        score = 0.0
        
        # Google results quality
        google_score = min(len(context_data.google_results) * 20, 60)  # Max 60 points
        score += google_score
        
        # YouTube results quality
        youtube_score = min(len(context_data.youtube_results) * 15, 30)  # Max 30 points
        score += youtube_score
        
        # Context synthesis quality
        if context_data.synthesized_context and len(context_data.synthesized_context) > 50:
            score += 10
        
        return min(score, 100.0)


# Legacy functions for backward compatibility
async def fetch_google_results(query: str, num: int = 5) -> List[Dict]:
    """Legacy function - use ContextResearchService instead"""
    service = ContextResearchService()
    return await service._fetch_google_results(query, num)


async def fetch_youtube_results(query: str, num: int = 5) -> List[Dict]:
    """Legacy function - use ContextResearchService instead"""
    service = ContextResearchService()
    return await service._fetch_youtube_results(query, num)



