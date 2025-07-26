"""
Main orchestrator for the multi-agent Islamic knowledge system.
Uses Tool Usage Agent with XML-styled tag invocations.
"""

import logging
import time
from typing import Dict, Any, Optional

from services.fanar_service import FanarService
from services.tavily_service import TavilyService
from agents.query_rewriter import QueryRewriterAgent
from agents.tool_usage_agent import ToolUsageAgent
from agents.synthesis_agent import SynthesisAgent
from models.schemas import QueryRequest, SystemResponse
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IslamicKnowledgeOrchestrator:
    """Main orchestrator for the multi-agent system using Tool Usage Agent."""
    
    def __init__(self, use_thinking_mode: bool = True):
        """Initialize all services and agents."""
        # Initialize services
        self.fanar_service = FanarService()
        self.tavily_service = TavilyService()
        
        # Initialize agents
        self.query_rewriter = QueryRewriterAgent(self.fanar_service)
        self.tool_usage_agent = ToolUsageAgent(self.fanar_service, self.tavily_service, use_thinking_mode)
        self.synthesis_agent = SynthesisAgent(self.fanar_service, use_thinking_mode)
        
        self.use_thinking_mode = use_thinking_mode
        
        logger.info(f"Islamic Knowledge Orchestrator initialized (thinking mode: {'enabled' if use_thinking_mode else 'disabled'})")
    
    def process_query(self, request: QueryRequest, use_thinking_mode: Optional[bool] = None) -> SystemResponse:
        """
        Process a user query through the complete multi-agent pipeline.
        
        Args:
            request: User query request
            use_thinking_mode: Override default thinking mode for this query
            
        Returns:
            SystemResponse with final answer and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing query: {request.query[:50]}...")
            
            # Step 1: Query Rewriting
            logger.info("Step 1: Rewriting query")
            rewritten_query_result = self.query_rewriter.rewrite_query(request.query)
            
            # Step 2: Tool Usage Agent Processing
            logger.info("Step 2: Tool Usage agent processing")
            agent_result = self.tool_usage_agent.process_query(
                rewritten_query_result.rewritten_query, 
                use_thinking_mode
            )
            
            # Step 3: Final Synthesis
            logger.info("Step 3: Final synthesis")
            if agent_result.get("success"):
                # Use new approach with tool results
                final_answer = self.synthesis_agent.synthesize_answer(
                    original_query=request.query,
                    tool_results=agent_result.get("tool_results", []) if agent_result.get("tool_results") else [],
                    rag_result=agent_result.get("rag_result") if agent_result.get("rag_result") else None,
                    web_result=agent_result.get("web_result") if agent_result.get("web_result") else None,
                    use_thinking_mode=use_thinking_mode
                )
            else:
                # Fallback in case of failure
                final_answer = self.synthesis_agent._create_fallback_answer(
                    request.query, 
                    agent_result.get("error", "Unknown error")
                )
            
            # Calculate processing time
            processing_time = time.time() - start_time
           
            
            # Replace reference tags in final answer
            final_answer.answer = self._replace_reference_tags(
                final_answer.answer,
                final_answer.references
            )
            # Create response
            response = SystemResponse(
                final_answer=final_answer,
                raw_rag_output=agent_result.get("rag_result"),
                raw_web_output=agent_result.get("web_result"),
                intermediate_reasoning=None,  # Tool Usage Agent doesn't use traditional reasoning traces
                rewritten_query=rewritten_query_result,
                processing_time=processing_time
            )
            
            logger.info(f"Query processed successfully in {processing_time:.2f}s using Tool Usage Agent")
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            processing_time = time.time() - start_time
            
            # Return error response
            fallback_answer = self.synthesis_agent._create_fallback_answer(
                request.query, str(e)
            )
            
            return SystemResponse(
                final_answer=fallback_answer,
                processing_time=processing_time
            )
    def _replace_reference_tags(self, text: str, references) -> str:
        """
        Replace RAG and Internet reference tags with markdown formatted links.
        
        Args:
            text: Text containing reference tags
            references: Dictionary with RAG and InternetSearch reference lists
            
        Returns:
            Text with tags replaced by markdown links
        """
        # Replace RAG references
        for i, ref in enumerate(references.get("RAG", []), 1):
            pattern = f"<RAG id={i}>"
            replacement = f"[{ref}]"
            text = text.replace(pattern, replacement)
            text = text.replace("</RAG>", "")
        
        # Replace Internet references  
        for i, ref in enumerate(references.get("InternetSearch", []), 1):
            pattern = f"<Internet id={i}>"
            replacement = f"[{ref}]"
            text = text.replace(pattern, replacement)
            text = text.replace("</Internet>", "")
        
        return text
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of all services.
        
        Returns:
            Dictionary with service status
        """
        health = {
            "status": "healthy",
            "services": {
                "fanar": "unknown",
                "tavily": "unknown"
            },
            "timestamp": time.time()
        }
        
        try:
            # Test Fanar service
            test_response = self.fanar_service.simple_chat([
                {"role": "user", "content": "Test message"}
            ])
            health["services"]["fanar"] = "healthy" if test_response else "unhealthy"
        except Exception as e:
            logger.error(f"Fanar health check failed: {e}")
            health["services"]["fanar"] = "unhealthy"
        
        try:
            # Test Tavily service
            health["services"]["tavily"] = "healthy" if self.tavily_service.is_available() else "unavailable"
        except Exception as e:
            logger.error(f"Tavily health check failed: {e}")
            health["services"]["tavily"] = "unhealthy"
        
        # Overall status
        if any(status == "unhealthy" for status in health["services"].values()):
            health["status"] = "degraded"
        elif health["services"]["fanar"] != "healthy":
            health["status"] = "unhealthy"
        
        return health
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information and configuration."""
        return {
            "system": "Fanar-based Islamic Writing Multi-Agent System",
            "version": "1.0.0",
            "agents": [
                "QueryRewriterAgent",
                "ToolUsageAgent", 
                "SynthesisAgent"
            ],
            "services": [
                "FanarService",
                "TavilyService"
            ],
            "models": {
                "fanar_simple": settings.fanar_simple_model,
                "fanar_rag": settings.fanar_rag_model,
            },
            "preferred_sources": settings.preferred_sources,
            "configuration": {
                "thinking_mode_enabled": self.use_thinking_mode,
                "agent_type": "tool_usage",
                "tool_usage_agent_thinking_mode": self.tool_usage_agent.get_thinking_mode(),
                "synthesis_agent_thinking_mode": self.synthesis_agent.get_thinking_mode()
            }
        }
    
    def set_thinking_mode(self, use_thinking_mode: bool):
        """Set thinking mode for the orchestrator and all agents."""
        self.use_thinking_mode = use_thinking_mode
        self.tool_usage_agent.set_thinking_mode(use_thinking_mode)
        self.synthesis_agent.set_thinking_mode(use_thinking_mode)
        logger.info(f"Orchestrator thinking mode set to: {'enabled' if use_thinking_mode else 'disabled'}")
    
    def get_thinking_mode(self) -> bool:
        """Get current thinking mode setting."""
        return self.use_thinking_mode


# Global orchestrator instance with thinking mode enabled by default
orchestrator = IslamicKnowledgeOrchestrator(use_thinking_mode=False) 