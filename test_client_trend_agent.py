#!/usr/bin/env python3
"""
Test script for ClientTrendAgent

This script demonstrates how the ClientTrendAgent analyzes trends 
in client industries to provide business insights.
"""

import asyncio
import json
import logging
from datetime import datetime

from backend.nodes.client_trend_agent import ClientTrendAgent
from backend.classes.state import ResearchState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_client_trend_agent():
    """Test the ClientTrendAgent with sample company profiles."""
    
    print("🚀 Testing ClientTrendAgent\n")
    
    # Test case 1: Nuvei (Payment processor)
    nuvei_profile = {
        "company": "Nuvei",
        "description": "Nuvei is a payment technology company that provides payment solutions for businesses worldwide, serving ecommerce merchants, gaming operators, and financial institutions.",
        "sector": "Fintech",
        "industry": "Payment Processing",
        "core_products": ["payment gateway", "fraud prevention", "merchant solutions", "cryptocurrency payments"],
        "business_model": "B2B payment processing platform",
        "target_market": "Online merchants, gaming companies, financial institutions"
    }
    
    # Test case 2: Shopify (E-commerce platform)
    shopify_profile = {
        "company": "Shopify",
        "description": "Shopify is a commerce platform that allows anyone to set up an online store and sell their products. It serves small businesses, enterprises, and entrepreneurs.",
        "sector": "E-commerce Technology",
        "industry": "Software as a Service",
        "core_products": ["e-commerce platform", "payment processing", "inventory management", "marketing tools"],
        "business_model": "SaaS subscription with transaction fees",
        "target_market": "Small to medium businesses, entrepreneurs, enterprises"
    }
    
    test_cases = [
        ("Nuvei", nuvei_profile),
        ("Shopify", shopify_profile)
    ]
    
    for company_name, profile in test_cases:
        print(f"\n{'='*50}")
        print(f"Testing {company_name}")
        print(f"{'='*50}")
        
        # Create initial state
        state = ResearchState(
            company=company_name,
            profile=profile,
            messages=[],
            client_trends=[]
        )
        
        try:
            # Initialize and run the ClientTrendAgent
            agent = ClientTrendAgent()
            
            print(f"🎯 Analyzing client industry trends for {company_name}...")
            
            # Run the agent
            result_state = await agent.run(state)
            
            # Display results
            client_trends = result_state.get('client_trends', [])
            
            print(f"\n📈 Found {len(client_trends)} client industry trends:")
            print("-" * 50)
            
            for i, trend in enumerate(client_trends, 1):
                print(f"\n{i}. {trend['trend']}")
                print(f"   Impact: {trend['impact']}")
                print(f"   Source: {trend['source_domain']}")
                print(f"   Confidence: {trend['confidence_score']}")
                print(f"   Date: {trend['date']}")
                
            # Show messages
            messages = result_state.get('messages', [])
            if messages:
                print(f"\n💬 Agent Messages:")
                for msg in messages[-3:]:  # Show last 3 messages
                    print(f"   {msg.content}")
                    
        except Exception as e:
            print(f"❌ Error testing {company_name}: {str(e)}")
            logger.error(f"Test failed for {company_name}", exc_info=True)


async def test_client_industry_identification():
    """Test just the client industry identification functionality."""
    
    print("\n🔍 Testing Client Industry Identification\n")
    
    agent = ClientTrendAgent()
    
    test_profiles = [
        {
            "name": "Stripe",
            "profile": {
                "company": "Stripe",
                "description": "Online payment processing for internet businesses",
                "core_products": ["payment processing", "billing", "connect marketplace"],
                "business_model": "Transaction-based fees"
            }
        },
        {
            "name": "Slack",
            "profile": {
                "company": "Slack",
                "description": "Business communication platform for teams",
                "core_products": ["messaging", "file sharing", "integrations"],
                "business_model": "SaaS subscription"
            }
        }
    ]
    
    for test_case in test_profiles:
        print(f"Company: {test_case['name']}")
        try:
            industries = await agent._identify_client_industries(test_case['profile'])
            print(f"Client Industries: {industries['industries']}")
            print(f"Rationale: {industries['rationale']}")
            print("-" * 40)
        except Exception as e:
            print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    print("ClientTrendAgent Test Suite")
    print("=" * 50)
    
    try:
        # Test client industry identification (faster)
        asyncio.run(test_client_industry_identification())
        
        # Comment out the full test if you want to save API calls
        # asyncio.run(test_client_trend_agent())
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        logger.error("Test suite error", exc_info=True) 