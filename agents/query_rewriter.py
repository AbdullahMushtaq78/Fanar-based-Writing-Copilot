"""
Query Rewriter Agent for improving user queries.
"""

import logging
import re
from typing import List, Tuple

from services.fanar_service import FanarService
from models.schemas import RewrittenQuery
from prompts.query_rewriter import QUERY_REWRITER_PROMPT

logger = logging.getLogger(__name__)


class QueryRewriterAgent:
    """Agent responsible for rewriting user queries to improve retrieval and search quality."""
    
    def __init__(self, fanar_service: FanarService):
        self.fanar_service = fanar_service
    
    def rewrite_query(self, original_query: str) -> RewrittenQuery:
        """
        Rewrite the user's query for better retrieval.
        
        Args:
            original_query: Original user query
            
        Returns:
            RewrittenQuery with improved version and improvements list
        """
        try:
            # Prepare prompt
            prompt = QUERY_REWRITER_PROMPT.format(original_query=original_query)
            
            messages = [{"role": "user", "content": prompt}]
            
            # Get response from Fanar
            response = self.fanar_service.simple_chat(messages)
            
            # Parse response
            rewritten_query, improvements = self._parse_response(response, original_query)
            
            return RewrittenQuery(
                original_query=original_query,
                rewritten_query=rewritten_query,
                improvements=improvements
            )
            
        except Exception as e:
            logger.error(f"Error in query rewriting: {e}")
            # Fallback: return original query with enhancement
            return RewrittenQuery(
                original_query=original_query,
                rewritten_query=self._simple_enhance_query(original_query),
                improvements=["Added basic Islamic context (fallback)"]
            )
    
    def _parse_response(self, response: str, original_query: str) -> Tuple[str, List[str]]:
        """Parse the rewriter response to extract query and improvements."""
        try:
            lines = response.strip().split('\n')
            rewritten_query = original_query  # fallback
            improvements = []
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for sections
                if line.startswith("1. Rewritten Query:") or "Rewritten Query:" in line:
                    current_section = "query"
                    # Extract query from same line if present
                    if ":" in line:
                        query_part = line.split(":", 1)[1].strip()
                        if query_part and not query_part.startswith("["):
                            rewritten_query = query_part
                elif line.startswith("2. Improvements Made:") or "Improvements Made:" in line:
                    current_section = "improvements"
                elif current_section == "query" and line:
                    # Continue reading query
                    if not line.startswith("[") and not line.startswith("2."):
                        rewritten_query = line
                elif current_section == "improvements" and line:
                    # Extract improvements
                    if line.startswith("-") or line.startswith("•") or line.startswith("*"):
                        improvements.append(line[1:].strip())
                    elif not line.startswith("["):
                        improvements.append(line)
            
            # Clean up the rewritten query
            rewritten_query = rewritten_query.strip()
            if rewritten_query.startswith("[") and rewritten_query.endswith("]"):
                rewritten_query = original_query  # fallback if bracketed placeholder
            
            # Ensure we have at least one improvement
            if not improvements:
                improvements = ["Query processed for Islamic context"]
            
            return rewritten_query, improvements
            
        except Exception as e:
            logger.error(f"Error parsing rewriter response: {e}")
            return original_query, ["Error in parsing (using original query)"]
    
    def _simple_enhance_query(self, query: str) -> str:
        """Simple fallback enhancement of the query."""
        # Basic enhancement: add Islamic context if not present
        islamic_terms = ["islam", "islamic", "quran", "hadith", "prophet", "allah", "muhammad"]
        query_lower = query.lower()
        
        has_islamic_context = any(term in query_lower for term in islamic_terms)
        
        if not has_islamic_context:
            return f"{query} in Islamic perspective according to Quran and Sunnah"
        
        return query 