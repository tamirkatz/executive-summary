import asyncio
import logging
import os
from backend.nodes.user_profile_enrichment_agent import UserProfileEnrichmentAgent
from backend.nodes.competitor_discovery_agent import EnhancedCompetitorDiscoveryAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_profile_enrichment():
    """Test profile enrichment and state handling."""
    print("🧪 Testing profile enrichment and state handling...")
    
    try:
        # Create test input state
        input_state = {
            'company': 'TestCorp',
            'user_role': 'CEO',
            'company_url': None,
            'websocket_manager': None,
            'job_id': None
        }
        
        # Initialize user profile enrichment agent
        profile_agent = UserProfileEnrichmentAgent()
        
        print("📊 Testing user profile enrichment...")
        
        # Run the profile enrichment
        research_state = await profile_agent.run(input_state)
        
        print(f"✅ Profile enrichment completed successfully!")
        print(f"Profile keys: {list(research_state.get('profile', {}).keys())}")
        print(f"State keys: {list(research_state.keys())}")
        
        # Check that all expected fields exist
        expected_fields = ['known_clients', 'use_cases', 'core_products', 'synonyms', 'customer_segments']
        missing_fields = []
        
        for field in expected_fields:
            if field not in research_state:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing fields in state: {missing_fields}")
            return False
        else:
            print(f"✅ All expected fields present in state")
        
        # Test competitor discovery with the enriched state
        print("🎯 Testing competitor discovery with enriched state...")
        
        competitor_agent = EnhancedCompetitorDiscoveryAgent()
        
        # Run competitor discovery
        updated_state = await competitor_agent.run(research_state)
        
        print(f"✅ Competitor discovery completed successfully!")
        print(f"Company info keys: {list(updated_state.get('company_info', {}).keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        logger.exception("Test failed")
        return False

async def test_profile_access():
    """Test direct profile field access patterns."""
    print("\n🔍 Testing profile field access patterns...")
    
    # Create a mock profile with all fields
    profile = {
        'company': 'TestCorp',
        'role': 'CEO',
        'description': 'A test company',
        'industry': 'Technology',
        'sector': 'Software',
        'customer_segments': ['B2B', 'Enterprise'],
        'known_clients': ['Client1', 'Client2'],
        'partners': ['Partner1', 'Partner2'],
        'use_cases': ['Use Case 1', 'Use Case 2'],
        'core_products': ['Product 1', 'Product 2'],
        'synonyms': ['Synonym 1', 'Synonym 2']
    }
    
    # Test all the access patterns used in the code
    try:
        # Test patterns from focused_competitor_agent.py
        description = profile.get('description', '')
        industry = profile.get('industry', 'Technology')
        sector = profile.get('sector', 'Software')
        clients_industries = profile.get('customer_segments', [])  # Fixed field name
        known_clients = profile.get('known_clients', [])
        partners = profile.get('partners', [])
        
        print(f"✅ Successfully accessed all profile fields:")
        print(f"  - description: {description}")
        print(f"  - industry: {industry}")
        print(f"  - sector: {sector}")
        print(f"  - customer_segments: {clients_industries}")
        print(f"  - known_clients: {known_clients}")
        print(f"  - partners: {partners}")
        
        return True
        
    except KeyError as e:
        print(f"❌ KeyError accessing profile field: {e}")
        return False
    except Exception as e:
        print(f"❌ Error accessing profile fields: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting profile enrichment fix tests...\n")
    
    # Test 1: Profile field access patterns
    test1_result = await test_profile_access()
    
    # Test 2: Full profile enrichment workflow
    test2_result = await test_profile_enrichment()
    
    print(f"\n📋 Test Results:")
    print(f"  Profile Access Test: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"  Full Workflow Test: {'✅ PASSED' if test2_result else '❌ FAILED'}")
    
    if test1_result and test2_result:
        print(f"\n🎉 All tests passed! The KeyError fix is working correctly.")
        return True
    else:
        print(f"\n❌ Some tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    asyncio.run(main()) 