"""
Tavily web search service for real-time information retrieval.
"""

import logging
from typing import List, Dict, Any, Optional
from tavily import TavilyClient

from config.settings import settings
from models.schemas import WebSearchResult

logger = logging.getLogger(__name__)


class TavilyService:
    """Service for web search using Tavily API."""
    
    def __init__(self):
        if not settings.tavily_api_key:
            logger.warning("Tavily API key not found. Web search will be disabled.")
            self.client = None
        else:
            self.client = TavilyClient(api_key=settings.tavily_api_key)
    
    def search(self, query: str, max_results: int = 3) -> WebSearchResult:
        """
        Perform web search using Tavily.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            WebSearchResult with search results
        """
        if not self.client:
            raise ValueError("Tavily API key not configured")
        
        try:
            # Perform search
            search_result = self.client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_answer="advanced",
                include_domains=None,
                exclude_domains=None
            )
            
            # Extract content and results
            content = search_result.get("answer", "")
            if not content and search_result.get("results"):
                # Fallback: combine top result contents
                content = "\n".join([
                    result.get("content", "")
                    for result in search_result["results"][:3]
                ])
            
            return WebSearchResult(
                content=content,
                results=search_result.get("results", []),
                search_query=query
            )
            
        except Exception as e:
            logger.error(f"Error in Tavily search: {e}")
            raise
    
    def search_with_context(self, query: str, context: str, max_results: int = 5) -> WebSearchResult:
        """
        Perform contextual web search.
        
        Args:
            query: Search query
            context: Additional context to improve search
            max_results: Maximum number of results
            
        Returns:
            WebSearchResult with search results
        """
        # Enhance query with context
        enhanced_query = f"{query} {context}"
        return self.search(enhanced_query, max_results)
    
    def is_available(self) -> bool:
        """Check if Tavily service is available."""
        return self.client is not None 