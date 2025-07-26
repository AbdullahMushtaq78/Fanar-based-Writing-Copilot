"""
Fanar API service for handling different modes of the Fanar LLM.
"""

import requests
from openai import OpenAI
from typing import List, Dict, Any, Optional, Tuple
import logging

from config.settings import settings
from models.schemas import RAGResult, ReferenceMaterial

logger = logging.getLogger(__name__)


class FanarService:
    """Service for interacting with Fanar API in different modes."""
    
    def __init__(self):
        self.api_key = settings.fanar_api_key
        self.base_url = settings.fanar_base_url
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
    
    def simple_chat(self, messages: List[Dict[str, str]], max_tokens: int = None) -> str:
        """
        Simple chat using Fanar model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens for response
            
        Returns:
            Generated response content
        """
        try:
            response = self.client.chat.completions.create(
                model=settings.fanar_simple_model,
                messages=messages,
                max_tokens=max_tokens or settings.max_tokens_default
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in simple chat: {e}")
            raise
    
    def thinking_chat(self, user_input: str, max_tokens: int = None) -> str:
        """
        Thinking mode chat with CoT reasoning.
        
        Args:
            user_input: User's input message
            max_tokens: Maximum tokens for response
            
        Returns:
            Final response after thinking process
        """
        try:
            # Step 1: Initial thinking request
            messages = [{"role": "thinking_user", "content": user_input}]
            
            response = self._make_request(
                messages=messages,
                max_tokens=max_tokens or settings.max_tokens_thinking
            )
            
            output = response["choices"][0]["message"]["content"]
            finish_reason = response["choices"][0]["finish_reason"]
            
            # Step 2: Check if thinking continuation needed
            has_think_tag = "</think>" in output
            hit_length_limit = finish_reason == "length"
            
            if has_think_tag or hit_length_limit:
                # Extract thinking output
                thinking_output = output.split("</think>")[0] if has_think_tag else output
                
                # Modify role and add thinking message
                for msg in reversed(messages):
                    if msg["role"] == "thinking_user":
                        msg["role"] = "user"
                        break
                
                messages.append({"role": "thinking", "content": thinking_output})
                
                # Final response
                final_response = self._make_request(
                    messages=messages,
                    max_tokens=settings.max_tokens_default
                )
                
                return final_response["choices"][0]["message"]["content"]
            else:
                return output
                
        except Exception as e:
            logger.error(f"Error in thinking chat: {e}")
            raise
    
    def islamic_rag(self, query: str, sources: List[str] = None) -> RAGResult:
        """
        Islamic RAG search using Fanar's RAG model - Direct HTTP implementation.
        
        Args:
            query: Search query
            sources: List of preferred sources (optional)
            
        Returns:
            RAGResult with content and references
        """
        try:
            # Enhanced query preprocessing for Islamic context
            # processed_query = self._preprocess_islamic_query(query)
            
            # # Enhanced source selection based on query type
            # optimal_sources = sources or self._select_optimal_sources(query)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": settings.fanar_rag_model,
                "messages": [{"role": "user", "content": query}],
                "max_tokens": settings.max_tokens_rag,
                #"preferred_sources": settings.preferred_sources
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            # Extract content and references using the working pattern
            content = response_data["choices"][0]["message"]["content"]
            references_data = response_data["choices"][0]["message"].get("references", [])
            
            # Enhanced reference parsing with Islamic source validation
            references = self._parse_enhanced_references(references_data)
            sources_used = list(set([ref.source for ref in references]))
            
            
            return RAGResult(
                content=content,
                references=references,
                sources_used=sources_used,
                confidence_score=0.0
            )
            
        except Exception as e:
            logger.error(f"Error in Enhanced Islamic RAG: {e}")
            raise
    
    def _preprocess_islamic_query(self, query: str) -> str:
        """
        Preprocess query to optimize for Islamic knowledge retrieval.
        """
        # Add Islamic context keywords for better retrieval
        islamic_keywords = {
            'prayer': 'salah prayer Islamic',
            'fasting': 'sawm fasting Ramadan Islamic',
            'pilgrimage': 'hajj pilgrimage Islamic',
            'charity': 'zakat charity Islamic',
            'halal': 'halal permissible Islamic ruling',
            'haram': 'haram forbidden Islamic ruling'
        }
        
        query_lower = query.lower()
        for keyword, enhanced in islamic_keywords.items():
            if keyword in query_lower and 'islamic' not in query_lower:
                query = f"Islamic {query}"
                break
        
        return query
    
    def _select_optimal_sources(self, query: str) -> List[str]:
        """
        Select optimal Islamic sources based on query type.
        """
        query_lower = query.lower()
        
        # Jurisprudence and rulings
        if any(word in query_lower for word in ['halal', 'haram', 'ruling', 'fatwa', 'permissible', 'forbidden']):
            return ["islamqa", "islamweb", "dorar", "shamela", "sunnah"]
        
        # Quranic topics
        elif any(word in query_lower for word in ['quran', 'verse', 'surah', 'tafsir', 'interpretation']):
            return ["quran", "tafsir", "shamela", "islamweb", "dorar"]
        
        # Hadith and Sunnah
        elif any(word in query_lower for word in ['hadith', 'sunnah', 'prophet', 'muhammad']):
            return ["sunnah", "shamela", "dorar", "islamqa", "islamweb"]
        
        # Worship and practices
        elif any(word in query_lower for word in ['prayer', 'salah', 'fasting', 'hajj', 'zakat']):
            return ["islamqa", "sunnah", "islamweb", "dorar", "shamela"]
        
        # Default comprehensive sources
        return settings.preferred_sources
    
    def _parse_enhanced_references(self, references: List[Dict]) -> List[ReferenceMaterial]:
        """Enhanced parsing of references from RAG response with Islamic source validation."""
        parsed_refs = []
        for ref in references:
            # Enhanced reference parsing with Islamic source validation
            source = ref.get("source", "Unknown source")
            content = ref.get("content", "")
            
            # Validate Islamic source authenticity
            is_authentic = self._validate_islamic_source(source)
            
            parsed_refs.append(
                ReferenceMaterial(
                    number=str(ref.get("number")),
                    source=source,
                    content=content,
                    is_authentic_source=is_authentic
                )
            )
        return parsed_refs
    
    def _validate_islamic_source(self, source: str) -> bool:
        """Validate if source is from authentic Islamic knowledge base."""
        authentic_sources = {
            "islamqa", "islamweb", "sunnah", "quran", "tafsir", 
            "dorar", "shamela", "islamonline", "dar-alifta",
            "al-islam", "islamicity", "muslim"
        }
        return any(auth_source in source.lower() for auth_source in authentic_sources)
    
    def _assess_islamic_content_quality(self, content: str, references: List[ReferenceMaterial]) -> float:
        """Assess the quality and authenticity of Islamic content retrieved."""
        quality_score = 0.0
        
        # Reference quality (40% of score)
        if references:
            authentic_refs = sum(1 for ref in references if ref.is_authentic_source)
            ref_quality = authentic_refs / len(references)
            quality_score += ref_quality * 0.4
        
        # Content indicators (30% of score)
        islamic_indicators = ['quran', 'hadith', 'prophet', 'allah', 'islamic', 'muslim', 'sunnah']
        content_lower = content.lower()
        indicator_count = sum(1 for indicator in islamic_indicators if indicator in content_lower)
        content_quality = min(indicator_count / len(islamic_indicators), 1.0)
        quality_score += content_quality * 0.3
        
        # Citation presence (30% of score)
        citation_indicators = ['according to', 'narrated by', 'reported by', 'mentioned in']
        citation_count = sum(1 for citation in citation_indicators if citation in content_lower)
        citation_quality = min(citation_count / len(citation_indicators), 1.0)
        quality_score += citation_quality * 0.3
        
        return min(quality_score, 1.0)
    
    def _make_request(self, messages: List[Dict], max_tokens: int) -> Dict[str, Any]:
        """Make request using requests library for thinking mode."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": settings.fanar_simple_model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    def _make_request_raw(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make raw request for RAG mode."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    def _parse_references(self, references: List[Dict]) -> List[ReferenceMaterial]:
        """Parse references from RAG response."""
        parsed_refs = []
        for ref in references:
            parsed_refs.append(
                ReferenceMaterial(
                    number=ref.get("number"),
                    source=ref.get("source", "Unknown source"),
                    content=ref.get("content", ""),
                    url=ref.get("url")
                )
            )
        return parsed_refs 