"""
Test file for the Enhanced Three-Agent Pre-Research Workflow.

This file demonstrates usage patterns and validates the implementation
of the enhanced workflow system.
"""

import asyncio
import logging
import json
from typing import Dict, Any

# Configure logging for testing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock WebSocket manager for testing
class MockWebSocketManager:
    """Mock WebSocket manager for testing purposes."""
    
    def __init__(self):
        self.updates = []
    
    async def send_status_update(self, job_id: str, status: str, message: str = None, result: Dict[str, Any] = None):
        """Mock status update method."""
        update = {
            "job_id": job_id,
            "status": status,
            "message": message,
            "result": result,
            "timestamp": asyncio.get_event_loop().time()
        }
        self.updates.append(update)
        logger.info(f"Status Update [{status}]: {message}")
    
    async def broadcast_to_job(self, job_id: str, update: Dict[str, Any]):
        """Mock broadcast method."""
        self.updates.append(update)
        logger.info(f"Broadcast to {job_id}: {update.get('type', 'unknown')}")

async def test_individual_agents():
    """Test individual agents separately."""
    logger.info("🧪 Testing Individual Agents")
    
    try:
        from backend.nodes.company_research_agent import CompanyResearchAgent
        from backend.nodes.industry_research_agent import IndustryResearchAgent
        from backend.nodes.competitors_research_agent import CompetitorsResearchAgent
        
        # Mock state for testing
        test_state = {
            "company": "Stripe",
            "company_url": "https://stripe.com",
            "user_role": "CEO",
            "websocket_manager": MockWebSocketManager(),
            "job_id": "test_job_123",
            "profile": {
                "industry": "Financial Technology",
                "sector": "Payments",
                "competitors": ["PayPal", "Square", "Adyen"]
            }
        }
        
        # Test Company Research Agent
        logger.info("🏢 Testing Company Research Agent")
        company_agent = CompanyResearchAgent()
        enhanced_state = await company_agent.run(test_state.copy())
        
        assert "company_factual_data" in enhanced_state
        logger.info(f"✅ Company Research Agent completed: {len(enhanced_state.get('company_factual_data', {}))} data categories")
        
        # Test Industry Research Agent
        logger.info("🏭 Testing Industry Research Agent")
        industry_agent = IndustryResearchAgent()
        enhanced_state = await industry_agent.run(enhanced_state)
        
        assert "industry_intelligence" in enhanced_state
        logger.info(f"✅ Industry Research Agent completed: {len(enhanced_state.get('industry_intelligence', {}))} intelligence categories")
        
        # Test Competitors Research Agent
        logger.info("🥊 Testing Competitors Research Agent")
        competitors_agent = CompetitorsResearchAgent()
        enhanced_state = await competitors_agent.run(enhanced_state)
        
        assert "enhanced_competitor_data" in enhanced_state
        total_competitors = enhanced_state.get('enhanced_competitor_data', {}).get('total_competitors', 0)
        logger.info(f"✅ Competitors Research Agent completed: {total_competitors} competitors analyzed")
        
        return enhanced_state
        
    except Exception as e:
        logger.error(f"❌ Individual agent test failed: {e}")
        raise

async def test_enhanced_workflow():
    """Test the complete enhanced workflow."""
    logger.info("🚀 Testing Enhanced Workflow")
    
    try:
        from backend.enhanced_workflow import create_enhanced_workflow
        
        # Create mock WebSocket manager
        ws_manager = MockWebSocketManager()
        
        # Create enhanced workflow
        workflow = create_enhanced_workflow(
            company="OpenAI",
            url="https://openai.com",
            user_role="CTO",
            websocket_manager=ws_manager,
            job_id="enhanced_test_456",
            enable_enhanced_pre_research=True,
            include_specialized_research=False
        )
        
        # Get workflow summary
        summary = workflow.get_workflow_summary()
        logger.info(f"📋 Workflow Summary: {json.dumps(summary, indent=2)}")
        
        # Run a few steps of the workflow (full run would require API keys)
        logger.info("🔄 Testing workflow initialization...")
        
        # Test state initialization
        initial_state = workflow.input_state
        assert "company" in initial_state
        assert "enhanced_competitor_data" in initial_state
        assert "company_factual_data" in initial_state
        assert "industry_intelligence" in initial_state
        
        logger.info("✅ Enhanced workflow initialization successful")
        
        # Test progress calculation
        test_state = initial_state.copy()
        test_state["company_factual_data"] = {"intelligence_summary": {"test": "data"}}
        progress = workflow._calculate_enhanced_progress(test_state)
        logger.info(f"📊 Progress calculation test: {progress}%")
        
        # Test phase determination
        phase = workflow._determine_current_phase(test_state)
        logger.info(f"📍 Current phase: {phase}")
        
        # Test metrics extraction
        metrics = workflow._extract_enhanced_metrics(test_state)
        logger.info(f"📈 Extracted metrics: {json.dumps(metrics, indent=2)}")
        
        return workflow
        
    except Exception as e:
        logger.error(f"❌ Enhanced workflow test failed: {e}")
        raise

async def test_backward_compatibility():
    """Test backward compatibility with original workflow."""
    logger.info("🔄 Testing Backward Compatibility")
    
    try:
        from backend.workflow import Graph
        
        # Test original Graph class still works
        original_workflow = Graph(
            company="Tesla",
            url="https://tesla.com", 
            user_role="CEO",
            websocket_manager=MockWebSocketManager(),
            job_id="compat_test_789"
        )
        
        # Verify original functionality is preserved
        assert hasattr(original_workflow, 'input_state')
        assert hasattr(original_workflow, 'workflow')
        assert original_workflow.input_state["company"] == "Tesla"
        
        logger.info("✅ Backward compatibility verified")
        
        return original_workflow
        
    except Exception as e:
        logger.error(f"❌ Backward compatibility test failed: {e}")
        raise

async def test_state_management():
    """Test enhanced state management."""
    logger.info("📊 Testing Enhanced State Management")
    
    try:
        from backend.classes.state import default_research_state, ResearchState
        
        # Test new state fields are present
        assert "company_factual_data" in default_research_state
        assert "industry_intelligence" in default_research_state
        assert "enhanced_competitor_data" in default_research_state
        assert "pre_research_complete" in default_research_state
        
        # Test default structures
        company_data = default_research_state["company_factual_data"]
        assert "website_analysis" in company_data
        assert "financial_data" in company_data
        assert "technology_stack" in company_data
        
        industry_data = default_research_state["industry_intelligence"]
        assert "market_trends" in industry_data
        assert "technology_disruptions" in industry_data
        assert "regulatory_landscape" in industry_data
        
        competitor_data = default_research_state["enhanced_competitor_data"]
        assert "comprehensive_profiles" in competitor_data
        assert "technology_comparisons" in competitor_data
        assert "strategic_movements" in competitor_data
        
        logger.info("✅ Enhanced state management verified")
        
    except Exception as e:
        logger.error(f"❌ State management test failed: {e}")
        raise

async def test_error_handling():
    """Test error handling and graceful degradation."""
    logger.info("🛡️ Testing Error Handling")
    
    try:
        from backend.nodes.company_research_agent import CompanyResearchAgent
        
        # Test with invalid state
        invalid_state = {"invalid": "state"}
        agent = CompanyResearchAgent()
        
        # Should handle gracefully and return state with error info
        result_state = await agent.run(invalid_state)
        
        # Should have error information but not crash
        assert "company_factual_data" in result_state
        logger.info("✅ Error handling verified - graceful degradation works")
        
    except Exception as e:
        logger.error(f"❌ Error handling test failed: {e}")
        raise

async def benchmark_performance():
    """Benchmark performance of enhanced workflow components."""
    logger.info("⚡ Running Performance Benchmarks")
    
    try:
        import time
        from backend.enhanced_workflow import create_enhanced_workflow
        
        # Benchmark workflow creation
        start_time = time.time()
        workflow = create_enhanced_workflow(
            company="Benchmark Test",
            enable_enhanced_pre_research=True
        )
        creation_time = time.time() - start_time
        
        logger.info(f"📊 Workflow creation time: {creation_time:.3f}s")
        
        # Benchmark state operations
        start_time = time.time()
        test_state = workflow.input_state.copy()
        test_state["company_factual_data"] = {"intelligence_summary": {"test": "data"}}
        progress = workflow._calculate_enhanced_progress(test_state)
        phase = workflow._determine_current_phase(test_state)
        metrics = workflow._extract_enhanced_metrics(test_state)
        state_ops_time = time.time() - start_time
        
        logger.info(f"📊 State operations time: {state_ops_time:.3f}s")
        logger.info(f"✅ Performance benchmarks completed")
        
    except Exception as e:
        logger.error(f"❌ Performance benchmark failed: {e}")
        raise

async def main():
    """Run all tests."""
    logger.info("🚀 Starting Enhanced Workflow Test Suite")
    
    try:
        # Test enhanced state management
        await test_state_management()
        
        # Test backward compatibility first
        await test_backward_compatibility()
        
        # Test error handling
        await test_error_handling()
        
        # Test enhanced workflow
        workflow = await test_enhanced_workflow()
        
        # Performance benchmarks
        await benchmark_performance()
        
        # Note: Individual agent tests require API keys, so we'll skip in basic test
        logger.info("ℹ️  Skipping individual agent tests (require API keys)")
        logger.info("ℹ️  To test with real API calls, set TAVILY_API_KEY and OPENAI_API_KEY")
        
        logger.info("🎉 All tests completed successfully!")
        
        # Display summary
        summary = {
            "status": "SUCCESS",
            "tests_run": [
                "Enhanced State Management",
                "Backward Compatibility", 
                "Error Handling",
                "Enhanced Workflow",
                "Performance Benchmarks"
            ],
            "skipped": [
                "Individual Agent Tests (require API keys)"
            ],
            "workflow_features": workflow.get_workflow_summary() if 'workflow' in locals() else {}
        }
        
        logger.info("📋 Test Summary:")
        print(json.dumps(summary, indent=2))
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        raise

# Demo function for real usage (requires API keys)
async def demo_with_api_keys():
    """
    Demo function that shows real usage with API keys.
    Only run this if you have valid TAVILY_API_KEY and OPENAI_API_KEY.
    """
    logger.info("🎬 Running Enhanced Workflow Demo")
    
    # Check for API keys
    import os
    if not os.getenv("TAVILY_API_KEY") or not os.getenv("OPENAI_API_KEY"):
        logger.warning("⚠️  API keys not found. Skipping real demo.")
        return
    
    try:
        from backend.enhanced_workflow import create_enhanced_workflow
        
        # Create WebSocket manager for real-time updates
        ws_manager = MockWebSocketManager()
        
        # Create enhanced workflow for a real company
        workflow = create_enhanced_workflow(
            company="Stripe",
            url="https://stripe.com",
            user_role="VP of Strategy",
            websocket_manager=ws_manager,
            job_id="demo_real_001",
            enable_enhanced_pre_research=True,
            include_specialized_research=False
        )
        
        logger.info("🚀 Running enhanced workflow with real API calls...")
        
        # Run the workflow (this will make real API calls)
        final_state = None
        async for state in workflow.run(thread={"configurable": {"thread_id": "demo_1"}}):
            current_phase = workflow._determine_current_phase(state)
            progress = workflow._calculate_enhanced_progress(state)
            logger.info(f"📍 Phase: {current_phase} | Progress: {progress}%")
            final_state = state
        
        # Display results
        if final_state:
            logger.info("🎉 Demo completed successfully!")
            
            # Show key results
            company_data = final_state.get("company_factual_data", {})
            industry_data = final_state.get("industry_intelligence", {})
            competitor_data = final_state.get("enhanced_competitor_data", {})
            
            logger.info(f"📊 Company Intelligence: {bool(company_data.get('intelligence_summary'))}")
            logger.info(f"📊 Industry Intelligence: {bool(industry_data.get('intelligence_summary'))}")
            logger.info(f"📊 Competitor Intelligence: {competitor_data.get('total_competitors', 0)} competitors")
            
            # Show final report if available
            if final_state.get("report"):
                logger.info("📄 Executive report generated successfully!")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        raise

if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main())
    
    # Uncomment to run real demo with API keys
    # asyncio.run(demo_with_api_keys()) 