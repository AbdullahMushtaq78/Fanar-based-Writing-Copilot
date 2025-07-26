"""
Test script for the system.
"""

import asyncio
import json
from models.schemas import QueryRequest
from orchestrator import orchestrator


async def test_query(query: str, use_thinking_mode: bool = False):
    """Test a single query through the system."""
    mode_text = f" ({'thinking' if use_thinking_mode else 'simple'} mode)" if use_thinking_mode is not None else ""
    print(f"\n{'='*50}")
    print(f"Testing Query{mode_text}: {query}")
    print(f"{'='*50}")
    
    try:
        # Create request
        request = QueryRequest(query=query)
        
        # Process query
        response = orchestrator.process_query(request, use_thinking_mode)
        
        # Print results
        print(f"\n📝 Original Query: {response.rewritten_query.original_query}")
        print(f"✏️  Rewritten Query: {response.rewritten_query.rewritten_query}")
        print(f"📈 Improvements: {', '.join(response.rewritten_query.improvements)}")
        
        print(f"\n🎯 Final Answer:")
        print(f"📚 {response.final_answer.answer}")
        
        print(f"\n⏱️  Processing Time: {response.processing_time:.2f} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_thinking_mode_settings():
    """Test thinking mode configuration."""
    print(f"\n{'='*50}")
    print("Testing Thinking Mode Configuration")
    print(f"{'='*50}")
    
    try:
        # Test getting current mode
        current_mode = orchestrator.get_thinking_mode()
        tool_usage_mode = orchestrator.tool_usage_agent.get_thinking_mode()
        synthesis_mode = orchestrator.synthesis_agent.get_thinking_mode()
        print(f"Current orchestrator thinking mode: {current_mode}")
        print(f"Current Tool Usage agent thinking mode: {tool_usage_mode}")
        print(f"Current Synthesis agent thinking mode: {synthesis_mode}")
        
        # Test setting to simple mode
        print("\n🔄 Setting to simple mode...")
        orchestrator.set_thinking_mode(False)
        new_mode = orchestrator.get_thinking_mode()
        new_tool_usage_mode = orchestrator.tool_usage_agent.get_thinking_mode()
        new_synthesis_mode = orchestrator.synthesis_agent.get_thinking_mode()
        print(f"New orchestrator thinking mode: {new_mode}")
        print(f"New Tool Usage agent thinking mode: {new_tool_usage_mode}")
        print(f"New Synthesis agent thinking mode: {new_synthesis_mode}")
        
        # Test setting back to thinking mode
        print("\n🔄 Setting back to thinking mode...")
        orchestrator.set_thinking_mode(True)
        final_mode = orchestrator.get_thinking_mode()
        final_tool_usage_mode = orchestrator.tool_usage_agent.get_thinking_mode()
        final_synthesis_mode = orchestrator.synthesis_agent.get_thinking_mode()
        print(f"Final orchestrator thinking mode: {final_mode}")
        print(f"Final Tool Usage agent thinking mode: {final_tool_usage_mode}")
        print(f"Final Synthesis agent thinking mode: {final_synthesis_mode}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing thinking mode: {e}")
        return False


async def test_health():
    """Test system health."""
    print(f"\n{'='*50}")
    print("Testing System Health")
    print(f"{'='*50}")
    
    try:
        health = orchestrator.health_check()
        print(f"Overall Status: {health['status']}")
        print(f"Services:")
        for service, status in health['services'].items():
            emoji = "✅" if status == "healthy" else "⚠️" if status == "unavailable" else "❌"
            print(f"  {emoji} {service}: {status}")
        
        return health['status'] in ["healthy", "degraded"]
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


async def test_system_info():
    """Test system info endpoint."""
    print(f"\n{'='*50}")
    print("System Information")
    print(f"{'='*50}")
    
    try:
        info = orchestrator.get_system_info()
        print(f"System: {info['system']}")
        print(f"Version: {info['version']}")
        print(f"Agents: {', '.join(info['agents'])}")
        print(f"Services: {', '.join(info['services'])}")
        print(f"Islamic Sources: {', '.join(info['preferred_sources'])}")
        
        # Print configuration
        config = info.get('configuration', {})
        print(f"\nConfiguration:")
        print(f"  Thinking mode enabled: {config.get('thinking_mode_enabled', 'unknown')}")
        print(f"  Tool Usage agent thinking mode: {config.get('tool_usage_agent_thinking_mode', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ System info failed: {e}")
        return False


async def test_queries():
    """Test multiple queries with both thinking and simple modes to trigger different RAG/web combinations."""
    print(f"\n{'='*50}")
    print("Testing Multiple Queries")
    print(f"{'='*50}")
    
    
    test_queries = [

        "What is the Islamic ruling on cryptocurrency trading and digital assets in 2025 according to contemporary scholars?",
        "How should Muslims pray during the solar eclipse in 2024 according to Islamic guidelines and current astronomical data?",
       
       
        """What is the latest ruling regarding the use of:
        1) AI-generated voice in adhan?
        2) Cryptocurrency in Islam, 2019 ownwards?
        3) Is there a saying from Prophet Muhammad (PBUH) about the friendship with the Jews?
        """,

        "What are the specific conditions that invalidate prayer (salah) in Islam?",
        
        "What are the detailed Hanafi and Shafi'i positions on breaking fast during Ramadan due to illness?",
        "What are the complete requirements and conditions for performing Hajj pilgrimage according to different madhabs?",
        
    ]
    
    successful_tests = 0
    total_tests = len(test_queries) * 2  # Each query tested in both modes
    
    try:
        for i, query_text in enumerate(test_queries, 1):
            print(f"\n{'='*60}")
            print(f"Query {i}/{len(test_queries)}: {query_text}")
            print(f"{'='*60}")
            
            await test_query(query_text, use_thinking_mode=False)
         
    except Exception as e:
        print(f"❌ Error in queries: {e}")
        return False


async def main():
    """Run simplified tests focusing on mode comparison."""
    print("\n Checking System Health...")
    health_ok = await test_health()
    if not health_ok:
        print("⚠️  System health issues detected, but continuing tests...")
    
    # Test system info
    print("\nGetting System Information...")
    await test_system_info()
    
    print("\n🎯 Running Main Tests: Multiple Queries...")
    await test_queries()
    
    

if __name__ == "__main__":
    asyncio.run(main()) 