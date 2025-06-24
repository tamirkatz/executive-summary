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

from backend.nodes.simple_competitor_agent import SimpleCompetitorDiscoveryAgent

async def test_simple_competitor_discovery():
    """Test the simple competitor discovery agent."""
    
    # Initialize the agent
    agent = SimpleCompetitorDiscoveryAgent()
    
    # Test companies
    test_cases = [
        {
            "company": "Stripe",
            "description": "Payment processing platform for online businesses and developers",
            "industry": "Financial Technology",
            "sector": "Payments"
        },
        {
            "company": "Shopify", 
            "description": "E-commerce platform enabling businesses to create online stores",
            "industry": "E-commerce",
            "sector": "Retail Technology"
        },
        {
            "company": "Slack",
            "description": "Business communication platform for team collaboration", 
            "industry": "Software",
            "sector": "Communication"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'='*80}")
        print(f"🧪 Testing: {test_case['company']}")
        print(f"📋 Description: {test_case['description']}")
        print(f"🏢 Industry/Sector: {test_case['industry']}/{test_case['sector']}")
        print("="*80)
        
        try:
            # Run discovery
            competitors = await agent.discover_competitors(
                company=test_case['company'],
                description=test_case['description'], 
                industry=test_case['industry'],
                sector=test_case['sector']
            )
            
            print(f"\n🎯 RESULTS:")
            print(f"Found {len(competitors)} competitors:")
            
            for i, competitor in enumerate(competitors, 1):
                print(f"{i:2}. {competitor}")
            
            if not competitors:
                print("❌ No competitors found!")
            else:
                print(f"\n✅ Successfully found {len(competitors)} competitors")
                
        except Exception as e:
            logger.error(f"❌ Test failed for {test_case['company']}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Simple Competitor Discovery Tests")
    
    # Check API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found")
        sys.exit(1)
    
    if not os.getenv("TAVILY_API_KEY"):
        print("❌ TAVILY_API_KEY not found")
        sys.exit(1)
    
    print("✅ API keys found")
    
    # Run test
    asyncio.run(test_simple_competitor_discovery()) 