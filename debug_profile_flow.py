#!/usr/bin/env python3
"""
Debug Profile Flow

Simple test to identify exactly where the profile data is lost between
UserProfileEnrichmentAgent and EnhancedCompetitorDiscoveryAgent
"""

import asyncio
import logging
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.nodes.user_profile_enrichment_agent import UserProfileEnrichmentAgent
from backend.nodes.competitor_discovery_agent import EnhancedCompetitorDiscoveryAgent

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def debug_profile_flow():
    """Debug the exact profile data flow"""
    
    print("🔍 DEBUGGING PROFILE DATA FLOW")
    print("=" * 50)
    
    # Step 1: Create input state
    input_state = {
        'company': 'base44',
        'company_url': None,
        'user_role': 'ceo',
        'websocket_manager': None,
        'job_id': None
    }
    
    print(f"Input state: {input_state}")
    
    # Step 2: Run profile enrichment
    print("\n🔧 Running UserProfileEnrichmentAgent...")
    profile_agent = UserProfileEnrichmentAgent()
    
    try:
        research_state = await profile_agent.run(input_state)
        
        print(f"\n✅ Profile enrichment completed")
        print(f"Research state keys: {list(research_state.keys())}")
        
        # Check profile data
        if 'profile' in research_state:
            profile = research_state['profile']
            print(f"\n📊 PROFILE DATA:")
            print(f"  - Keys: {list(profile.keys())}")
            print(f"  - Company: {profile.get('company', 'NOT_FOUND')}")
            print(f"  - Sector: {profile.get('sector', 'NOT_FOUND')}")
            print(f"  - Description length: {len(profile.get('description', ''))}")
            
            # This is what the competitor agent will receive
            print(f"\n🎯 What competitor agent will receive:")
            print(f"  - state.get('profile', {{}}) = {bool(profile)}")
            print(f"  - enriched_profile.get('company') = {profile.get('company', 'NOT_FOUND')}")
            
        else:
            print("❌ NO PROFILE IN RESEARCH STATE!")
            return False
            
    except Exception as e:
        print(f"❌ Profile enrichment failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Run competitor discovery
    print("\n🏆 Running EnhancedCompetitorDiscoveryAgent...")
    competitor_agent = EnhancedCompetitorDiscoveryAgent()
    
    try:
        # This will show us the debug logs we added
        updated_state = await competitor_agent.run(research_state)
        
        competitors = updated_state.get('competitors', [])
        print(f"\n✅ Competitor discovery completed")
        print(f"Found {len(competitors)} competitors")
        
        return len(competitors) > 0
        
    except Exception as e:
        print(f"❌ Competitor discovery failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_profile_flow())
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}") 