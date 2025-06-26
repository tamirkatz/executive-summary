#!/usr/bin/env python3

import asyncio
import sys
import os
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.nodes.company_info_agent import CompanyInfoAgent

# Configure logging to see debug info
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_lovable_company():
    """Test the lovable company to debug the 404 issue"""
    print("🔧 Testing 'lovable' company to debug 404 error")
    print("=" * 60)
    
    try:
        # Initialize the company info agent
        agent = CompanyInfoAgent()
        
        print("🏢 Testing company: 'lovable'")
        print("   No URL provided (simulating the issue)")
        
        # Test with no URL (like in the error case)
        result = await agent.extract_company_info_async(
            company="lovable",
            role="CEO",
            company_url=None  # This is likely the issue - no URL provided
        )
        
        print(f"\n📄 Result:")
        for key, value in result.items():
            print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_lovable_company()) 