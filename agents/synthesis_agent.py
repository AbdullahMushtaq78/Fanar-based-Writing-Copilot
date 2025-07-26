"""
Final Synthesis Agent for creating comprehensive Islamic answers.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple

from services.fanar_service import FanarService
from models.schemas import (
    FinalAnswer, RAGResult, WebSearchResult, ReActTrace, ReferenceMaterial
)
from prompts.final_synthesis import FINAL_SYNTHESIS_PROMPT

logger = logging.getLogger(__name__)


class SynthesisAgent:
    """Agent for creating final comprehensive answers using Fanar."""
    
    def __init__(self, fanar_service: FanarService, use_thinking_mode: bool = True):
        self.fanar_service = fanar_service
        self.use_thinking_mode = use_thinking_mode
    
    def synthesize_answer(
        self, 
        original_query: str,
        rag_result: Optional[RAGResult] = None,
        web_result: Optional[WebSearchResult] = None,
        reasoning_trace: Optional[ReActTrace] = None,
        tool_results: Optional[List[Dict]] = None,
        use_thinking_mode: Optional[bool] = None
    ) -> FinalAnswer:
        """
        Create final synthesized answer.
        
        Args:
            original_query: Original user query
            rag_result: Results from Islamic RAG
            web_result: Results from web search
            reasoning_trace: ReAct reasoning trace (legacy)
            tool_results: Tool results from Tool Usage Agent (new)
            use_thinking_mode: Override default thinking mode for this synthesis
            
        Returns:
            FinalAnswer with comprehensive response
        """
        # Use provided mode or fall back to instance default
        thinking_mode = use_thinking_mode if use_thinking_mode is not None else self.use_thinking_mode
        
        try:
            content, data_sources = self._prepare_synthesis_input_from_tool_results(original_query, tool_results)
           
            if thinking_mode:
                response = self.fanar_service.thinking_chat(FINAL_SYNTHESIS_PROMPT.format(user_query=original_query, sources=content), max_tokens=2000)
            else:
                messages = [{"role": "user", "content": FINAL_SYNTHESIS_PROMPT.format(user_query=original_query, sources=content)}]
                response = self.fanar_service.simple_chat(messages)
            
            return FinalAnswer(
                answer=response,
                confidence=0.0,
                methodology="",
                references=data_sources
            )
            
        except Exception as e:
            logger.error(f"Error in synthesis: {e}")
            # Fallback answer
            return self._create_fallback_answer(original_query, str(e))
    
    def _prepare_synthesis_input_from_tool_results(self, query: str, tool_results: List[Dict]) -> str:
        """Prepare structured input for synthesis from Tool Usage Agent results."""
        synthesis_parts = []
        sources = {
            "RAG": [],
            "InternetSearch": []
        }
        for result_data in tool_results:
            tool = result_data['tool']
            query_used = result_data['query']
            result = result_data['result']
            
            if tool == 'RAG' and isinstance(result, RAGResult):
                synthesis_parts.append(f"""
## Islamic Sources Information
**Query Used:** {query_used}
**Content:** {result.content}
""")
                sources["RAG"].extend(result.sources_used)
                if result.references:
                    synthesis_parts.append("**Detailed References and Sources:**")
                    for i, ref in enumerate(result.references, 1):
                        synthesis_parts.append(f"<RAG id={i}>{ref.source}: {ref.content[:100]}...</RAG>")
                    synthesis_parts.append("")
            
            elif tool == 'InternetSearch' and isinstance(result, WebSearchResult):
                synthesis_parts.append(f"""
## Contemporary (Internet Search) Information
**Search Query:** {query_used}
**Direct Search Answer:** {result.content}
""")
                
                if result.results:
                    synthesis_parts.append("**Web Search Results:**")
                    for i, web_result in enumerate(result.results, 1):
                        title = web_result.get("title", "Unknown")
                        url = web_result.get("url", "")
                        snippet = web_result.get("content", "")[:100]
                        synthesis_parts.append(f"<Internet id={i}>{title} ({url}): {snippet}...</Internet>")
                        sources["InternetSearch"].append(url)
                    synthesis_parts.append("")
        
        return "\n".join(synthesis_parts), sources
    
    def _format_rag_content(self, rag_result: RAGResult) -> str:
        """Format RAG content for synthesis."""
        content = f"**Islamic Sources Content:**\n{rag_result.content}\n\n"
        
        if rag_result.references:
            content += "**References from Islamic Sources:**\n"
            for i, ref in enumerate(rag_result.references, 1):
                content += f"[{i}] {ref.source}: {ref.content[:200]}...\n"
            content += "\n"
        
        return content
    
    def _format_web_content(self, web_result: WebSearchResult) -> str:
        """Format web search content for synthesis."""
        if not web_result.content:
            return ""
        
        content = f"**Web Search Content:**\n{web_result.content}\n\n"
        
        if web_result.results:
            content += "**Web Search Results:**\n"
            for i, result in enumerate(web_result.results[:3], 1):
                title = result.get("title", "Unknown")
                url = result.get("url", "")
                snippet = result.get("content", "")[:150]
                content += f"[{i}] {title} ({url}): {snippet}...\n"
            content += "\n"
        
        return content
    
    def _format_reasoning_trace(self, trace: ReActTrace) -> str:
        """Format reasoning trace for synthesis."""
        content = "**Reasoning Process:**\n"
        
        for i, thought in enumerate(trace.thoughts, 1):
            content += f"Step {i}: {thought.thought}\n"
            if thought.action:
                content += f"Action: {thought.action}\n"
            if thought.observation:
                content += f"Result: {thought.observation[:100]}...\n"
            content += "\n"
        
        content += f"Final Decision: {trace.final_decision}\n\n"
        return content
    
   
    
    def _create_fallback_answer(self, query: str, error: str) -> FinalAnswer:
        """Create fallback answer when synthesis fails."""
        return FinalAnswer(
            answer=f"I apologize, but I encountered an error while processing your query: {error}",
            confidence=0.0,
            methodology="Error fallback",
            references = { "RAG": [], "InternetSearch": [] }
        )
    
    def set_thinking_mode(self, use_thinking_mode: bool):
        """Set thinking mode for the agent."""
        self.use_thinking_mode = use_thinking_mode
    
    def get_thinking_mode(self) -> bool:
        """Get current thinking mode setting."""
        return self.use_thinking_mode 