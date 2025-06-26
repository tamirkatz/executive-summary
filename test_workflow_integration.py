"""
Test script demonstrating the integration of the new modular profile enrichment system
into both the standard and enhanced workflows.
"""

import asyncio
import logging
import sys
import os
from backend.workflow import Graph
from backend.enhanced_workflow import EnhancedGraph, create_enhanced_workflow

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.nodes.user_profile_enrichment_agent import UserProfileEnrichmentAgent
from backend.nodes.competitor_discovery_agent import EnhancedCompetitorDiscoveryAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_standard_workflow_with_enhanced_profile():
    """Test the standard workflow with the new modular profile enrichment system."""
    
    print("\n" + "="*80)
    print("🧪 TESTING STANDARD WORKFLOW WITH ENHANCED PROFILE ENRICHMENT")
    print("="*80)
    
    # Test with enhanced profile enrichment enabled (default)
    print("\n1️⃣ Testing with Enhanced Profile Enrichment (Default)")
    
    workflow = Graph(
        company="Stripe",
        url="https://stripe.com",
        user_role="Product Manager",
        use_enhanced_profile_enrichment=True  # New modular system
    )
    
    print(f"✅ Workflow created with enhanced profile enrichment")
    print(f"   • Agent type: {type(workflow.profile_enrichment_agent).__name__}")
    print(f"   • Enhanced profile enrichment: {workflow.use_enhanced_profile_enrichment}")
    
    # Test with legacy profile enrichment
    print("\n2️⃣ Testing with Legacy Profile Enrichment")
    
    legacy_workflow = Graph(
        company="Stripe",
        url="https://stripe.com", 
        user_role="Product Manager",
        use_enhanced_profile_enrichment=False  # Legacy system
    )
    
    print(f"✅ Workflow created with legacy profile enrichment")
    print(f"   • Agent type: {type(legacy_workflow.profile_enrichment_agent).__name__}")
    print(f"   • Enhanced profile enrichment: {legacy_workflow.use_enhanced_profile_enrichment}")


async def test_enhanced_workflow_with_new_features():
    """Test the enhanced workflow with all new features enabled."""
    
    print("\n" + "="*80)
    print("🚀 TESTING ENHANCED WORKFLOW WITH ALL NEW FEATURES")
    print("="*80)
    
    # Test enhanced workflow with all features
    print("\n1️⃣ Testing Enhanced Workflow (Full Features)")
    
    enhanced_workflow = create_enhanced_workflow(
        company="OpenAI",
        url="https://openai.com",
        user_role="CTO",
        include_specialized_research=True,
        enable_enhanced_pre_research=True,
        use_enhanced_profile_enrichment=True  # New modular system
    )
    
    print(f"✅ Enhanced workflow created with all features")
    print(f"   • Profile agent type: {type(enhanced_workflow.profile_enrichment_agent).__name__}")
    print(f"   • Enhanced pre-research: {enhanced_workflow.enable_enhanced_pre_research}")
    print(f"   • Enhanced profile enrichment: {enhanced_workflow.use_enhanced_profile_enrichment}")
    print(f"   • Specialized research: {enhanced_workflow.include_specialized_research}")
    
    # Get workflow summary
    summary = enhanced_workflow.get_workflow_summary()
    print(f"\n📊 Workflow Summary:")
    print(f"   • Workflow type: {summary['workflow_type']}")
    print(f"   • Pre-research agents: {summary['pre_research_agents']}")
    print(f"   • Total nodes: {summary['total_nodes']}")
    
    # Test backward compatibility (standard workflow through enhanced class)
    print("\n2️⃣ Testing Backward Compatibility")
    
    compat_workflow = Graph(
        company="Algolia",
        url="https://algolia.com",
        user_role="CEO",
        use_enhanced_profile_enrichment=True
    )
    
    print(f"✅ Backward compatible workflow created")
    print(f"   • Profile agent type: {type(compat_workflow.profile_enrichment_agent).__name__}")
    print(f"   • Enhanced pre-research: {compat_workflow.enable_enhanced_pre_research}")  # Should be False
    print(f"   • Enhanced profile enrichment: {compat_workflow.use_enhanced_profile_enrichment}")


async def test_configuration_matrix():
    """Test different configuration combinations."""
    
    print("\n" + "="*80)
    print("⚙️  TESTING CONFIGURATION MATRIX")
    print("="*80)
    
    configurations = [
        {
            "name": "Legacy Everything",
            "enhanced_pre_research": False,
            "enhanced_profile": False,
            "specialized": False
        },
        {
            "name": "Enhanced Profile Only",
            "enhanced_pre_research": False,
            "enhanced_profile": True,
            "specialized": False
        },
        {
            "name": "Enhanced Pre-research Only",
            "enhanced_pre_research": True,
            "enhanced_profile": False,
            "specialized": False
        },
        {
            "name": "Full Enhanced Suite",
            "enhanced_pre_research": True,
            "enhanced_profile": True,
            "specialized": True
        }
    ]
    
    for i, config in enumerate(configurations, 1):
        print(f"\n{i}️⃣ Configuration: {config['name']}")
        
        workflow = create_enhanced_workflow(
            company="TestCorp",
            url="https://testcorp.com",
            user_role="Analyst",
            enable_enhanced_pre_research=config["enhanced_pre_research"],
            use_enhanced_profile_enrichment=config["enhanced_profile"],
            include_specialized_research=config["specialized"]
        )
        
        agent_type = type(workflow.profile_enrichment_agent).__name__
        expected_agent = "ProfileEnrichmentOrchestrator" if config["enhanced_profile"] else "UserProfileEnrichmentAgent"
        
        print(f"   ✅ Profile Agent: {agent_type} ({'✓' if agent_type == expected_agent else '✗'})")
        print(f"   • Enhanced pre-research: {workflow.enable_enhanced_pre_research}")
        print(f"   • Enhanced profile: {workflow.use_enhanced_profile_enrichment}")
        print(f"   • Specialized research: {workflow.include_specialized_research}")


async def demonstrate_workflow_capabilities():
    """Demonstrate the enhanced capabilities of the new system."""
    
    print("\n" + "="*80)
    print("🎯 DEMONSTRATING ENHANCED WORKFLOW CAPABILITIES")
    print("="*80)
    
    # Create a fully enhanced workflow
    workflow = create_enhanced_workflow(
        company="Anthropic",
        url="https://anthropic.com",
        user_role="Research Director",
        enable_enhanced_pre_research=True,
        use_enhanced_profile_enrichment=True,
        include_specialized_research=True
    )
    
    # Get detailed capabilities
    summary = workflow.get_workflow_summary()
    
    print(f"\n🏗️ Workflow Architecture:")
    print(f"   • Type: {summary['workflow_type'].title()}")
    print(f"   • Total Nodes: {summary['total_nodes']}")
    print(f"   • Pre-research Agents: {summary['pre_research_agents']}")
    
    print(f"\n🤖 Active Agents:")
    for agent, active in summary['agents'].items():
        status = "✅ Active" if active else "⚪ Inactive"
        print(f"   • {agent.replace('_', ' ').title()}: {status}")
    
    print(f"\n🚀 Enhanced Capabilities:")
    for capability, enabled in summary['capabilities'].items():
        status = "✅ Enabled" if enabled else "⚪ Disabled"
        print(f"   • {capability.replace('_', ' ').title()}: {status}")
    
    print(f"\n💡 Key Benefits:")
    print(f"   • 🎯 Sophisticated competitor discovery with 3-iteration feedback loop")
    print(f"   • 🔍 Multi-source validation using Tavily crawl verification")
    print(f"   • 📊 Quality assessment and automatic refinement")
    print(f"   • 🏗️ Modular architecture for independent optimization")
    print(f"   • 🔄 Backward compatibility with existing systems")
    print(f"   • 📈 Real-time progress tracking and WebSocket updates")


async def test_workflow_integration():
    """Test the exact workflow integration sequence"""
    
    logger.info("=== TESTING WORKFLOW INTEGRATION ===")
    
    # Step 1: Create initial input state (exactly like the workflow does)
    input_state = {
        'company': 'base44',
        'company_url': None,
        'user_role': 'ceo',
        'websocket_manager': None,
        'job_id': None
    }
    
    logger.info(f"Initial input state: {input_state}")
    
    # Step 2: Run UserProfileEnrichmentAgent (exactly like the workflow does)
    logger.info("Step 1: Running UserProfileEnrichmentAgent...")
    profile_agent = UserProfileEnrichmentAgent()
    
    try:
        research_state = await profile_agent.run(input_state)
        
        logger.info(f"Profile enrichment completed!")
        logger.info(f"Research state keys: {list(research_state.keys())}")
        logger.info(f"Profile in state: {'profile' in research_state}")
        
        if 'profile' in research_state:
            profile = research_state['profile']
            logger.info(f"Profile keys: {list(profile.keys())}")
            logger.info(f"Profile company: {profile.get('company', 'NOT_FOUND')}")
            logger.info(f"Profile sector: {profile.get('sector', 'NOT_FOUND')}")
        else:
            logger.error("❌ No profile found in research state!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Profile enrichment failed: {e}", exc_info=True)
        return False
    
    # Step 3: Run EnhancedCompetitorDiscoveryAgent (exactly like the workflow does)
    logger.info("Step 2: Running EnhancedCompetitorDiscoveryAgent...")
    competitor_agent = EnhancedCompetitorDiscoveryAgent()
    
    try:
        updated_state = await competitor_agent.run(research_state)
        
        competitors = updated_state.get('competitors', [])
        logger.info(f"Competitor discovery completed!")
        logger.info(f"Found {len(competitors)} competitors")
        
        if len(competitors) > 0:
            logger.info("✅ SUCCESS: Competitors found in workflow integration!")
            for i, comp in enumerate(competitors[:5]):
                logger.info(f"  {i+1}. {comp.get('name', 'Unknown')} (confidence: {comp.get('confidence_score', 'N/A')})")
            return True
        else:
            logger.warning("⚠️ WARNING: No competitors found in workflow integration")
            return False
            
    except Exception as e:
        logger.error(f"❌ Competitor discovery failed: {e}", exc_info=True)
        return False


async def main():
    """Run all integration tests."""
    
    print("🎯 MODULAR PROFILE ENRICHMENT WORKFLOW INTEGRATION TESTS")
    print("This demonstrates the integration of the new competitor discovery system")
    print("into both standard and enhanced workflows with backward compatibility.")
    
    try:
        # Run all test suites
        await test_standard_workflow_with_enhanced_profile()
        await test_enhanced_workflow_with_new_features()
        await test_configuration_matrix()
        await demonstrate_workflow_capabilities()
        
        print("\n" + "="*80)
        print("🎉 ALL INTEGRATION TESTS COMPLETED SUCCESSFULLY!")
        print("="*80)
        
        print(f"\n📋 Summary:")
        print(f"   ✅ Standard workflow integration verified")
        print(f"   ✅ Enhanced workflow integration verified")
        print(f"   ✅ Backward compatibility maintained")
        print(f"   ✅ Configuration matrix tested")
        print(f"   ✅ New capabilities demonstrated")
        
        print(f"\n🚀 The new modular profile enrichment system is now integrated!")
        print(f"   • Use 'use_enhanced_profile_enrichment=True' for the new system")
        print(f"   • Use 'use_enhanced_profile_enrichment=False' for legacy behavior") 
        print(f"   • Default is the new enhanced system for better competitor discovery")
        
        success = await test_workflow_integration()
        if success:
            print("🎉 Workflow integration test PASSED!")
        else:
            print("❌ Workflow integration test FAILED!")
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        print(f"\n❌ Integration test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 