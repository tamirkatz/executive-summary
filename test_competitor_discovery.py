import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.append('backend')

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from backend.nodes.competitor_discovery_agent import AutonomousCompetitorDiscoveryAgent

async def test_competitor_discovery():
    """Test the autonomous competitor discovery agent."""
    
    # Initialize the agent
    agent = AutonomousCompetitorDiscoveryAgent()
    
    # Test company profile
    test_company = "Stripe"
    test_description = "Stripe is a technology company that builds economic infrastructure for the internet. Businesses of every size—from new startups to Fortune 500s—use our software to accept payments and grow their revenue globally."
    test_industry = "Financial Technology"
    test_sector = "Payments"
    test_client_industries = ["E-commerce", "SaaS", "Marketplaces"]
    test_known_clients = ["Shopify", "Uber", "Amazon"]
    
    print(f"🧪 Testing competitor discovery for: {test_company}")
    print(f"📋 Description: {test_description}")
    print(f"🏢 Industry/Sector: {test_industry}/{test_sector}")
    print("=" * 80)
    
    try:
        # Run the discovery
        result = await agent.discover_competitors(
            company=test_company,
            description=test_description,
            industry=test_industry,
            sector=test_sector,
            client_industries=test_client_industries,
            known_clients=test_known_clients
        )
        
        print(f"\n🎯 DISCOVERY RESULTS:")
        print(f"Competitors found: {len(result.get('competitors', []))}")
        print(f"Average confidence: {result.get('discovery_metadata', {}).get('avg_confidence', 0):.2f}")
        print(f"Total iterations: {result.get('discovery_metadata', {}).get('total_iterations', 0)}")
        
        print(f"\n📊 COMPETITORS:")
        for i, competitor in enumerate(result.get('competitors', []), 1):
            print(f"{i}. {competitor}")
        
        print(f"\n📈 DETAILED ANALYSIS:")
        for analysis in result.get('detailed_analysis', []):
            print(f"\n🏢 {analysis.get('name', 'Unknown')}")
            print(f"   📋 Description: {analysis.get('description', 'N/A')}")
            print(f"   🎯 Confidence: {analysis.get('confidence_score', 0):.2f}")
            print(f"   💡 Reasoning: {analysis.get('reasoning', 'N/A')[:100]}...")
            print(f"   🔗 Market Overlap: {analysis.get('market_overlap', 'N/A')[:100]}...")
        
        print(f"\n🧠 REASONING HISTORY:")
        for i, reasoning in enumerate(result.get('discovery_metadata', {}).get('reasoning_history', []), 1):
            print(f"{i}. {reasoning}")
        
        print(f"\n📊 QUALITY METRICS:")
        quality = result.get('quality_metrics', {})
        print(f"High confidence count: {quality.get('high_confidence_count', 0)}")
        print(f"Medium confidence count: {quality.get('medium_confidence_count', 0)}")
        print(f"Evidence strength: {quality.get('evidence_strength', 0):.2f}")
        print(f"Query diversity: {quality.get('query_diversity', 0)}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_simple_discovery():
    """Test with a simpler approach to debug issues."""
    
    agent = AutonomousCompetitorDiscoveryAgent()
    
    print("🔍 Testing query strategy generation...")
    
    company_profile = {
        "name": "Stripe",
        "description": "Payment processing platform for online businesses",
        "industry": "Financial Technology", 
        "sector": "Payments",
        "client_industries": ["E-commerce", "SaaS"],
        "known_clients": ["Shopify", "Uber"]
    }
    
    try:
        # Test strategy generation
        strategies = await agent._generate_autonomous_query_strategies(
            company_profile, iteration=1
        )
        
        print(f"Generated {len(strategies)} strategies:")
        for i, strategy in enumerate(strategies, 1):
            print(f"{i}. Query: {strategy.query}")
            print(f"   Reasoning: {strategy.reasoning}")
            print(f"   Type: {strategy.expected_type}")
            print(f"   Priority: {strategy.priority}")
            print()
        
        if strategies:
            print("🔍 Testing query execution...")
            candidates = await agent._execute_query_strategies(
                strategies[:1], company_profile  # Test just first strategy
            )
            
            print(f"Found {len(candidates)} candidates:")
            for candidate in candidates:
                print(f"- {candidate.name}: {candidate.confidence_score:.2f}")
                print(f"  {candidate.description[:100]}...")
                print()
        
    except Exception as e:
        logger.error(f"❌ Simple test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Competitor Discovery Agent Tests")
    print("=" * 60)
    
    # Check if API keys are available
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment")
        sys.exit(1)
    
    if not os.getenv("TAVILY_API_KEY"):
        print("❌ TAVILY_API_KEY not found in environment")
        sys.exit(1)
    
    print("✅ API keys found")
    
    # Run tests
    asyncio.run(test_simple_discovery())
    print("\n" + "=" * 60)
    asyncio.run(test_competitor_discovery()) 