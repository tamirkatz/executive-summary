"""
Demo script showing the new modular profile enrichment system.

This demonstrates how the ProfileEnrichmentOrchestrator coordinates:
1. CompanyInfoAgent - extracts basic company information
2. CompetitorDiscoveryAgent - sophisticated competitor discovery with evaluation loop
3. CompetitorEvaluatorAgent - quality assessment and feedback

The system uses a feedback loop that can run up to 3 iterations to ensure 
high-quality competitor discovery.
"""

import asyncio
import logging
from backend.nodes import ProfileEnrichmentOrchestrator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_profile_enrichment():
    """Demonstrate the new profile enrichment system."""
    
    # Create sample input state
    input_state = {
        'company': 'Algolia',
        'company_url': 'https://www.algolia.com',
        'user_role': 'CTO',
        'websocket_manager': None,  # In real usage, this would be the websocket manager
        'job_id': 'demo_job_123'
    }
    
    print("🚀 Starting Profile Enrichment Demo")
    print(f"Company: {input_state['company']}")
    print(f"Role: {input_state['user_role']}")
    print("=" * 60)
    
    # Initialize the orchestrator
    orchestrator = ProfileEnrichmentOrchestrator()
    
    try:
        # Run the complete profile enrichment process
        result_state = await orchestrator.run(input_state)
        
        print("\n✅ Profile Enrichment Completed!")
        print("=" * 60)
        
        # Display company info results
        company_info = result_state.get('company_info', {})
        print(f"\n📊 Company Information:")
        print(f"  • Company: {company_info.get('company', 'N/A')}")
        print(f"  • Industry: {company_info.get('industry', 'N/A')}")
        print(f"  • Sector: {company_info.get('sector', 'N/A')}")
        print(f"  • Description: {company_info.get('description', 'N/A')[:100]}...")
        
        # Display competitor results
        competitors = company_info.get('competitors', [])
        print(f"\n🏆 Competitors Found ({len(competitors)}):")
        for i, competitor in enumerate(competitors, 1):
            print(f"  {i}. {competitor}")
        
        # Display evaluation results
        evaluation = result_state.get('competitor_evaluation', {})
        if evaluation:
            print(f"\n📈 Quality Assessment:")
            print(f"  • Overall Score: {evaluation.get('overall_score', 0):.2f}")
            print(f"  • Quality Passed: {evaluation.get('pass_threshold', False)}")
            print(f"  • Issues Found: {len(evaluation.get('issues_found', []))}")
            
            if evaluation.get('issues_found'):
                print(f"  • Issues: {', '.join(evaluation['issues_found'])}")
        
        # Display discovery metadata
        discovery_result = result_state.get('competitor_discovery_result', {})
        if discovery_result:
            print(f"\n🔍 Discovery Metadata:")
            print(f"  • Total Iterations: {discovery_result.get('total_iterations', 0)}")
            print(f"  • Queries Used: {discovery_result.get('queries_used', 0)}")
        
        print("\n" + "=" * 60)
        print("Demo completed successfully! 🎉")
        
        return result_state
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        return None


async def demo_individual_agents():
    """Demonstrate individual agents working separately."""
    
    print("\n🔧 Individual Agent Demo")
    print("=" * 60)
    
    from backend.nodes import CompanyInfoAgent, CompetitorDiscoveryAgent, CompetitorEvaluatorAgent
    
    # Sample state
    input_state = {
        'company': 'Stripe',
        'company_url': 'https://stripe.com',
        'user_role': 'CEO',
        'websocket_manager': None,
        'job_id': 'demo_individual'
    }
    
    # Step 1: Company Info Agent
    print("\n1️⃣ Running CompanyInfoAgent...")
    company_agent = CompanyInfoAgent()
    research_state = await company_agent.run(input_state)
    
    company_info = research_state.get('company_info', {})
    print(f"   ✅ Extracted info for {company_info.get('company', 'Unknown')}")
    print(f"   • Industry: {company_info.get('industry', 'N/A')}")
    print(f"   • Description: {company_info.get('description', 'N/A')[:80]}...")
    
    # Step 2: Competitor Discovery Agent
    print("\n2️⃣ Running CompetitorDiscoveryAgent...")
    competitor_agent = CompetitorDiscoveryAgent()
    research_state = await competitor_agent.run(research_state)
    
    competitors = research_state.get('company_info', {}).get('competitors', [])
    print(f"   ✅ Found {len(competitors)} competitors")
    print(f"   • Top 3: {', '.join(competitors[:3])}")
    
    # Step 3: Competitor Evaluator Agent
    print("\n3️⃣ Running CompetitorEvaluatorAgent...")
    evaluator_agent = CompetitorEvaluatorAgent()
    research_state = await evaluator_agent.run(research_state)
    
    evaluation = research_state.get('competitor_evaluation', {})
    print(f"   ✅ Evaluation completed")
    print(f"   • Score: {evaluation.get('overall_score', 0):.2f}")
    print(f"   • Quality Check: {'PASSED' if evaluation.get('pass_threshold') else 'FAILED'}")
    
    print("\n✨ Individual agent demo completed!")


if __name__ == "__main__":
    print("🎯 Profile Enrichment System Demo")
    print("This demonstrates the new modular approach to profile enrichment.")
    print()
    
    # Run the orchestrated demo
    asyncio.run(demo_profile_enrichment())
    
    # Run the individual agents demo
    asyncio.run(demo_individual_agents()) 