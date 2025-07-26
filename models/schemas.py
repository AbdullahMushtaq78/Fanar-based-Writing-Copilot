"""
Pydantic models for request/response schemas and data structures.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class AgentAction(str, Enum):
    """Available actions for ReAct agent."""
    ISLAMIC_RAG = "islamic_rag"
    WEB_SEARCH = "web_search"
    FINAL_SYNTHESIS = "final_synthesis"


class ReferenceMaterial(BaseModel):
    """Reference material from RAG or web search with enhanced validation."""
    number: Optional[str] = None
    source: str
    content: str
    #url: Optional[str] = None
    #authenticity_score: float = Field(0.0, ge=0.0, le=1.0, description="Relevance/authenticity score")
    is_authentic_source: bool = Field(True, description="Whether source is from authentic Islamic knowledge base")


class QueryRequest(BaseModel):
    """User query request."""
    query: str = Field(..., description="User's question or query")
    language: Optional[str] = Field("en", description="Preferred response language")
    include_references: bool = Field(True, description="Include reference materials")


class RewrittenQuery(BaseModel):
    """Rewritten query for better retrieval."""
    original_query: str
    rewritten_query: str
    improvements: List[str]


class AgentThought(BaseModel):
    """Single thought in ReAct reasoning chain."""
    thought: str
    action: Optional[AgentAction] = None
    action_input: Optional[str] = None
    observation: Optional[str] = None


class ReActTrace(BaseModel):
    """Complete ReAct reasoning trace."""
    thoughts: List[AgentThought]
    final_decision: str


class RAGResult(BaseModel):
    """Enhanced result from Islamic RAG search with quality assessment."""
    content: str
    references: List[ReferenceMaterial]
    sources_used: List[str]
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="Overall confidence in Islamic content quality")


class WebSearchResult(BaseModel):
    """Result from Tavily web search."""
    content: str
    results: List[Dict[str, Any]]
    search_query: str


class FinalAnswer(BaseModel):
    """Final synthesized answer."""
    answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    methodology: str
    references: dict[str, List[str]]


class SystemResponse(BaseModel):
    """Complete system response."""
    final_answer: FinalAnswer
    raw_rag_output: Optional[RAGResult] = None
    raw_web_output: Optional[WebSearchResult] = None
    intermediate_reasoning: Optional[ReActTrace] = None
    rewritten_query: Optional[RewrittenQuery] = None
    processing_time: float


class AgentStatus(BaseModel):
    """Status of individual agent."""
    agent_name: str
    status: str  # "running", "completed", "failed"
    message: Optional[str] = None
    timestamp: float 