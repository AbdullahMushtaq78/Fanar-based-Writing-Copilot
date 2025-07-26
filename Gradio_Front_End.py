"""
Gradio-based UI for the Islamic Knowledge System.
"""

import gradio as gr
import sys
import os
from typing import Tuple, Optional
import logging
import time

# Add the Backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator import IslamicKnowledgeOrchestrator
from models.schemas import QueryRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the orchestrator
orchestrator = IslamicKnowledgeOrchestrator(use_thinking_mode=False)

def process_query(query: str, thinking_mode: bool = False) -> Tuple[str, str, str, str, str, float]:
    """
    Process a query through the orchestrator and return formatted results.
    
    Args:
        query: User's query
        thinking_mode: Whether to use thinking mode
        
    Returns:
        Tuple of (final_answer_html, rag_content, web_content, query_info, references, processing_time)
    """
    if not query.strip():
        return "Please enter a query.", "", "", "", "", 0.0
    
    try:
        # Create query request
        request = QueryRequest(query=query.strip())
        
        # Process through orchestrator
        response = orchestrator.process_query(request, use_thinking_mode=thinking_mode)
        
        final_answer_html = response.final_answer.answer
        
        # Print final answer to CLI for verification
        print("\n" + "="*80)
        print("FINAL ANSWER OUTPUT:")
        print("="*80)
        print(response.final_answer.answer)
        print("="*80 + "\n")
        
        # Format RAG content
        rag_content = ""
        if response.raw_rag_output:
            rag_content = f"""
            **RAG Search Results:**
            
            **Content:** {response.raw_rag_output.content}
            
            **Confidence Score:** {response.raw_rag_output.confidence_score:.2f}
            
            **Sources Used:** {', '.join(response.raw_rag_output.sources_used)}
            
            **References:**
            """
            for ref in response.raw_rag_output.references:
                rag_content += f"- **{ref.source}**: {ref.content[:200]}...\n"
        
        # Format web search content
        web_content = ""
        if response.raw_web_output:
            web_content = f"""
            **Web Search Results:**
            
            **Search Query:** {response.raw_web_output.search_query}
            
            **Content:** {response.raw_web_output.content}
            
            **Results:**
            """
            for result in response.raw_web_output.results[:3]:  # Show first 3 results
                title = result.get('title', 'No title')
                url = result.get('url', 'No URL')
                content = result.get('content', 'No content')[:200]
                web_content += f"- **{title}** ({url}): {content}...\n"
        
        # Format query information
        query_info = f"""
        **Original Query:** {query}
        
        **Processing Time:** {response.processing_time:.2f} seconds
        
        **Final Answer Confidence:** {response.final_answer.confidence:.2f}
        
        **Methodology:** {response.final_answer.methodology}
        """
        
        if response.rewritten_query:
            query_info += f"""
            
            **Rewritten Query:** {response.rewritten_query.rewritten_query}
            
            **Improvements:** {', '.join(response.rewritten_query.improvements)}
            """
        
        # Format references
        references = ""
        if response.final_answer.references:
            references = "**References:**\n\n"
            for ref_type, ref_list in response.final_answer.references.items():
                if ref_list:
                    references += f"**{ref_type}:**\n"
                    for i, ref in enumerate(ref_list, 1):
                        references += f"{i}. {ref}\n"
                    references += "\n"
        
        return (
            final_answer_html,
            rag_content,
            web_content,
            query_info,
            references,
            response.processing_time
        )
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        error_message = f"""
        **Error:** {str(e)}
        """
        return error_message, "", "", "", "", 0.0

def get_system_info() -> str:
    """Get system information for display."""
    try:
        info = orchestrator.get_system_info()
        health = orchestrator.health_check()
        
        info_text = f"""
        # System Information
        
        **System:** {info['system']}
        **Version:** {info['version']}
        **Status:** {health['status']}
        
        ## Agents
        {', '.join(info['agents'])}
        
        ## Services
        {', '.join(info['services'])}
        
        ## Service Health
        - **Fanar:** {health['services']['fanar']}
        - **Tavily:** {health['services']['tavily']}
        
        ## Configuration
        - **Thinking Mode:** {'Enabled' if info['configuration']['thinking_mode_enabled'] else 'Disabled'}
        - **Agent Type:** {info['configuration']['agent_type']}
        
        ## Models
        - **Fanar Simple:** {info['models']['fanar_simple']}
        - **Fanar RAG:** {info['models']['fanar_rag']}
        """
        
        return info_text
    
    except Exception as e:
        return f"**Error retrieving system info:** {str(e)}"

def create_interface():
    """Create the Gradio interface."""
    
    # Custom CSS for better styling
    custom_css = """
    .gradio-container {
        max-width: 1200px !important;
        margin: auto !important;
    }
    .main-header {
        text-align: center;
        color: #2c3e50;
        margin-bottom: 20px;
    }
    .response-section {
        margin-top: 20px;
        padding: 15px;
        border-radius: 8px;
        background-color: #f8f9fa;
    }
    .error-message {
        color: #dc3545;
        padding: 10px;
        border: 1px solid #dc3545;
        border-radius: 5px;
        background-color: #f8d7da;
    }
    """
    
    with gr.Blocks(css=custom_css, title="Islamic Knowledge System", theme=gr.themes.Soft()) as interface:
        
        # Header
        gr.Markdown("""
        # 🕌 Islamic Knowledge System
        ## Multi-Agent AI System for Islamic Queries
        
        Ask questions about Islamic knowledge, and our system will search through authentic sources and provide comprehensive answers.
        """, elem_classes="main-header")
        
        with gr.Row():
            with gr.Column(scale=2):
                # Input section
                with gr.Group():
                    gr.Markdown("### 📝 Enter Your Query")
                    query_input = gr.Textbox(
                        label="Your Question",
                        placeholder="e.g., What are the five pillars of Islam?",
                        lines=3,
                        max_lines=5
                    )
                    
                    with gr.Row():
                        thinking_mode = gr.Checkbox(
                            label="Enable Thinking Mode",
                            value=False,
                            info="Show detailed reasoning process"
                        )
                        submit_btn = gr.Button("Submit Query", variant="primary", size="lg")
                
                # Main response section
                with gr.Group():
                    gr.Markdown("### 🎯 Final Answer")
                    final_answer = gr.Markdown(
                        label="Answer",
                        value="Your answer will appear here..."
                    )
            
            with gr.Column(scale=1):
                # System info sidebar
                with gr.Group():
                    gr.Markdown("### ⚙️ System Status")
                    system_info = gr.Markdown(get_system_info())
                    refresh_btn = gr.Button("Refresh Status", size="sm")
        
        # Additional information tabs
        with gr.Row():
            with gr.Tabs():
                with gr.Tab("📚 RAG Results"):
                    rag_output = gr.Markdown(
                        value="RAG results will appear here after processing a query.",
                        height=300
                    )
                
                with gr.Tab("🌐 Web Search"):
                    web_output = gr.Markdown(
                        value="Web search results will appear here after processing a query.",
                        height=300
                    )
                
                with gr.Tab("📋 Query Details"):
                    query_details = gr.Markdown(
                        value="Query processing details will appear here after processing a query.",
                        height=300
                    )
                
                with gr.Tab("📖 References"):
                    references_output = gr.Markdown(
                        value="References will appear here after processing a query.",
                        height=300
                    )
        
        # Processing time display
        with gr.Row():
            processing_time = gr.Markdown("⏱️ Processing time will be shown here")
        
        # Event handlers
        def update_all_outputs(query, thinking):
            final_html, rag, web, details, refs, proc_time = process_query(query, thinking)
            time_display = f"⏱️ **Processing Time:** {proc_time:.2f} seconds"
            return final_html, rag, web, details, refs, time_display
        
        submit_btn.click(
            fn=update_all_outputs,
            inputs=[query_input, thinking_mode],
            outputs=[final_answer, rag_output, web_output, query_details, references_output, processing_time]
        )
        
        # Enter key support
        query_input.submit(
            fn=update_all_outputs,
            inputs=[query_input, thinking_mode],
            outputs=[final_answer, rag_output, web_output, query_details, references_output, processing_time]
        )
        
        # Refresh system info
        refresh_btn.click(
            fn=get_system_info,
            outputs=system_info
        )
        
        # Example queries
        gr.Markdown("""
        ### 💡 Example Queries
        - What are the five pillars of Islam?
        - Explain the concept of Tawhid in Islamic theology
        - What is the importance of Salah in Islam?
        - How should a Muslim prepare for Hajj?
        - What are the different types of charity in Islam?
        """)
    
    return interface

def main():
    """Main function to launch the Gradio interface."""
    try:
        logger.info("Starting Islamic Knowledge System UI...")
        
        # Create and launch the interface
        interface = create_interface()
        
        # Launch with specific configuration
        interface.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            debug=False,
            show_error=True,
            inbrowser=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start UI: {e}")
        raise

if __name__ == "__main__":
    main()
