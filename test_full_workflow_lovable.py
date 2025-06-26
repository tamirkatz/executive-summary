#!/usr/bin/env python3

import asyncio
import sys
import os
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.workflow import Graph

# Configure logging 
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_full_workflow_lovable():
    """Test the full workflow for lovable company"""
    print("🔧 Testing full workflow for 'lovable' company")
    print("=" * 60)
    
    try:
        # Initialize the workflow
        workflow = Graph()
        
        print("🏢 Testing company: 'lovable'")
        print("   Simulating frontend request (no URL provided)")
        
        # Simulate the exact request that would come from frontend
        input_state = {
            "company": "lovable",
            "company_url": None,  # This is what frontend sends when no URL provided
            "user_role": "CEO"
        }
        
        print(f"📤 Input state: {input_state}")
        
        # Run the full workflow
        result = await workflow.run(input_state)
        
        print(f"\n📄 Workflow completed successfully!")
        print(f"   Company: {result.get('company')}")
        print(f"   Report length: {len(result.get('report', ''))}")
        
        # Check if there's company info
        company_info = result.get('company_info', {})
        if company_info:
            print(f"   Company description: {company_info.get('description', 'N/A')}")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_workflow_lovable()) 