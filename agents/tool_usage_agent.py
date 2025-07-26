"""
Tool Usage Agent - Uses XML-styled tags for tool invocation
"""

import logging
import re
from typing import List, Dict, Any, Optional

from services.fanar_service import FanarService
from services.tavily_service import TavilyService
from models.schemas import (
    AgentAction, AgentThought, ReActTrace, RAGResult, WebSearchResult
)
from prompts.tool_usage_agent import TOOL_USAGE_PROMPT

logger = logging.getLogger(__name__)


class ToolUsageAgent:
    """Tool Usage Agent with XML-styled tag invocation."""
    
    def __init__(self, fanar_service: FanarService, tavily_service: TavilyService, use_thinking_mode: bool = True):
        self.fanar_service = fanar_service
        self.tavily_service = tavily_service
        self.use_thinking_mode = use_thinking_mode
        
    def process_query(self, query: str, use_thinking_mode: Optional[bool] = None) -> Dict[str, Any]:
        """Process query using XML-styled tool invocation."""
        thinking_mode = use_thinking_mode if use_thinking_mode is not None else self.use_thinking_mode
        
        try:
            # Step 1: Get tool invocations from agent
            tool_invocations = self._get_tool_invocations(query, thinking_mode)
            logger.info(f"Generated tool invocations: {tool_invocations}")
            
            if not tool_invocations:
                logger.warning("No tool invocations generated")
                return self._create_error_result("No tool invocations generated", query)
            
            # Step 2: Parse and execute tools
            rag_result = None
            web_result = None
            tool_results = []
            
            for invocation in tool_invocations:
                if invocation['tool'] == 'RAG':
                    rag_result = self._execute_rag(invocation['query'])
                    if rag_result:
                        tool_results.append({
                            'tool': 'RAG',
                            'query': invocation['query'],
                            'result': rag_result
                        })
                elif invocation['tool'] == 'InternetSearch':
                    web_result = self._execute_web_search(invocation['query'])
                    if web_result:
                        tool_results.append({
                            'tool': 'InternetSearch',
                            'query': invocation['query'],
                            'result': web_result
                        })
            
            # Return tool execution results without synthesis
            return {
                'success': True,
                'tool_invocations': tool_invocations,
                'tool_results': tool_results,
                'rag_result': rag_result,
                'web_result': web_result,
                'thinking_mode': thinking_mode
            }
            
        except Exception as e:
            logger.error(f"Error in tool usage processing: {e}")
            return self._create_error_result(str(e), query)
    
    def _get_tool_invocations(self, query: str, thinking_mode: bool) -> List[Dict[str, str]]:
        """Get tool invocations using the XML-styled prompt."""
        try:
            prompt = TOOL_USAGE_PROMPT.format(query=query)
            
            if thinking_mode:
                response = self.fanar_service.thinking_chat(prompt)
            else:
                messages = [{"role": "user", "content": prompt}]
                response = self.fanar_service.simple_chat(messages)
            
            logger.info(f"Agent response: {response}")
            
            # Parse XML-styled tool invocations
            return self._parse_tool_invocations(response)
            
        except Exception as e:
            logger.error(f"Error getting tool invocations: {e}")
            return []
    
    def _parse_tool_invocations(self, response: str) -> List[Dict[str, str]]:
        """Parse XML-styled tool invocations from response."""
        invocations = []
        
        try:
            # Parse RAG invocations
            rag_pattern = r'<RAG><query>(.*?)</query></RAG>'
            rag_matches = re.findall(rag_pattern, response, re.DOTALL)
            for match in rag_matches:
                invocations.append({
                    'tool': 'RAG',
                    'query': match.strip()
                })
            
            # Parse InternetSearch invocations
            search_pattern = r'<InternetSearch><search_query>(.*?)</search_query></InternetSearch>'
            search_matches = re.findall(search_pattern, response, re.DOTALL)
            for match in search_matches:
                invocations.append({
                    'tool': 'InternetSearch',
                    'query': match.strip()
                })
            
            logger.info(f"Parsed {len(invocations)} tool invocations")
            return invocations
            
        except Exception as e:
            logger.error(f"Error parsing tool invocations: {e}")
            return []
    
    def _execute_rag(self, query: str) -> Optional[RAGResult]:
        """Execute Islamic RAG search."""
        try:
            logger.info(f"Executing RAG search with query: {query}")
            result = self.fanar_service.islamic_rag(query)
            logger.info(f"RAG search completed with confidence: {result.confidence_score:.2f}")
            return result
        except Exception as e:
            logger.error(f"Error in RAG execution: {e}")
            return None
    
    def _execute_web_search(self, query: str) -> Optional[WebSearchResult]:
        """Execute web search using Tavily."""
        try:
            if not self.tavily_service.is_available():
                logger.warning("Web search service not available")
                return None
            
            logger.info(f"Executing web search with query: {query}")
            result = self.tavily_service.search(query)
            logger.info("Web search completed successfully")
            return result
        except Exception as e:
            logger.error(f"Error in web search execution: {e}")
            return None
    
    
    def _create_error_result(self, error: str, query: str) -> Dict[str, Any]:
        """Create error result structure."""
        return {
            'success': False,
            'error': error,
            'query': query,
            'tool_invocations': [],
            'tool_results': [],
            'rag_result': None,
            'web_result': None,
            'thinking_mode': self.use_thinking_mode
        }
    
    def set_thinking_mode(self, use_thinking_mode: bool):
        """Set thinking mode for the agent."""
        self.use_thinking_mode = use_thinking_mode
    
    def get_thinking_mode(self) -> bool:
        """Get current thinking mode setting."""
        return self.use_thinking_mode 