#!/usr/bin/env python3
"""
Quick test for base44 competitor discovery to validate improvements
"""

import asyncio
import logging
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.nodes.competitor_discovery_agent import EnhancedCompetitorDiscoveryAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_base44_competitor_discovery():
    """Test competitor discovery for base44"""
    
    # Base44 profile (from the websocket message)
    base44_profile = {
        "company": "base44",
        "role": "ceo",
        "description": "Base44 is a Software-as-a-Service (SaaS) platform that enables users to create fully functioning web applications without the need for coding, utilizing a natural language development approach. The primary target market includes creative professionals, small business owners, and individuals with app ideas who seek to build custom applications quickly and efficiently. Key technologies employed by Base44 include artificial intelligence for app development and integration capabilities with third-party services.",
        "industry": "Software as a Service",
        "sector": "No-Code Development Platform",
        "customer_segments": ["Creative Professionals", "Small Business Owners", "Individuals with App Ideas"],
        "known_clients": [],
        "partners": [],
        "use_cases": ["Building Custom Web Applications", "Rapid Prototyping", "No-Code Development", "Integration with Third-Party Services", "AI-Driven App Development"],
        "core_products": ["No-Code Application Builder", "Natural Language Development Interface", "Integration Tools", "AI Development Features"],
        "synonyms": ["No-Code Platform", "Low-Code Development", "App Builder", "SaaS Development Tool"]
    }
    
    # Expected competitors for no-code platforms
    expected_competitors = {
        "bubble", "webflow", "retool", "glide", "adalo", "appgyver", 
        "mendix", "outsystems", "powerapps", "appsheet", "thunkable",
        "flutterflow", "bravo studio", "draftbit", "build.ai", "zapier"
    }
    
    logger.info("=== TESTING BASE44 COMPETITOR DISCOVERY ===")
    logger.info(f"Target: {base44_profile['company']}")
    logger.info(f"Sector: {base44_profile['sector']}")
    logger.info(f"Expected competitors: {expected_competitors}")
    
    # Initialize agent
    agent = EnhancedCompetitorDiscoveryAgent()
    
    try:
        # Run competitor discovery
        result = await agent.discover_competitors(
            enriched_profile=base44_profile,
            websocket_manager=None,
            job_id=None
        )
        
        competitors = result.get('competitors', [])
        competitor_names = {comp['name'].lower() for comp in competitors}
        
        logger.info(f"=== RESULTS ===")
        logger.info(f"Found {len(competitors)} competitors:")
        for comp in competitors:
            logger.info(f"  - {comp['name']} (confidence: {comp.get('confidence_score', 'N/A')})")
        
        # Calculate accuracy
        matches = competitor_names.intersection(expected_competitors)
        accuracy = len(matches) / len(expected_competitors) * 100 if expected_competitors else 0
        
        logger.info(f"=== ACCURACY ANALYSIS ===")
        logger.info(f"Expected: {len(expected_competitors)} competitors")
        logger.info(f"Found: {len(competitors)} competitors")
        logger.info(f"Matches: {len(matches)} ({matches})")
        logger.info(f"Accuracy: {accuracy:.1f}%")
        
        if accuracy > 20:
            logger.info("✅ SUCCESS: Good accuracy achieved!")
        else:
            logger.warning("⚠️ WARNING: Low accuracy, needs improvement")
            
        return accuracy, len(competitors)
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return 0, 0

if __name__ == "__main__":
    asyncio.run(test_base44_competitor_discovery()) 