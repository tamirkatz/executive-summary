#!/usr/bin/env python3
"""
Single Startup Competitor Discovery Test

Focused test on Tavily to identify and fix accuracy issues efficiently.
"""

import asyncio
import logging
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.nodes.competitor_discovery_agent import EnhancedCompetitorDiscoveryAgent

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'single_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Test case: Tavily (AI search startup)
TAVILY_PROFILE = {
    "company": "Tavily",
    "description": "AI-powered search API for developers and researchers, providing real-time web search with AI-enhanced results",
    "industry": "Technology",
    "sector": "AI Search",
    "core_products": ["Search API", "AI Search Engine", "Research Assistant"],
    "use_cases": ["Developer tools", "Research automation", "AI applications"],
    "customer_segments": ["Developers", "Researchers", "AI companies"],
    "synonyms": ["AI search", "search API", "intelligent search"]
}

EXPECTED_COMPETITORS = {
    "good": ["Perplexity", "SearchGPT", "You.com", "Exa", "Metaphor", "Bing Chat", "Phind", "Kagi"],
    "avoid": ["Google", "Microsoft", "Amazon", "Apple", "Meta", "Facebook", "IBM", "Oracle"]
}

async def test_tavily_competitors():
    """Test competitor discovery for Tavily with detailed analysis"""
    
    logger.info("="*60)
    logger.info("TESTING COMPETITOR DISCOVERY FOR TAVILY")
    logger.info("="*60)
    
    logger.info(f"Profile: {json.dumps(TAVILY_PROFILE, indent=2)}")
    logger.info(f"Expected good competitors: {EXPECTED_COMPETITORS['good']}")
    logger.info(f"Should avoid: {EXPECTED_COMPETITORS['avoid']}")
    
    agent = EnhancedCompetitorDiscoveryAgent()
    
    try:
        logger.info("\n🔍 Starting competitor discovery...")
        result = await agent.discover_competitors(TAVILY_PROFILE)
        
        discovered_competitors = result.get('competitors', [])
        search_queries = result.get('search_queries_used', [])
        
        logger.info(f"\n📊 DISCOVERY RESULTS:")
        logger.info(f"Total competitors found: {len(discovered_competitors)}")
        logger.info(f"Search queries used: {len(search_queries)}")
        
        # Log search queries used
        logger.info(f"\n🔍 SEARCH QUERIES USED:")
        for i, query in enumerate(search_queries, 1):
            logger.info(f"  {i}. {query}")
        
        # Analyze results
        analysis = analyze_tavily_results(discovered_competitors)
        log_detailed_analysis(discovered_competitors, analysis)
        
        return {
            'discovered': discovered_competitors,
            'analysis': analysis,
            'queries': search_queries
        }
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return None

def analyze_tavily_results(discovered: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the accuracy of Tavily competitor discovery"""
    
    discovered_names = []
    for comp in discovered:
        if isinstance(comp, dict):
            discovered_names.append(comp.get('name', ''))
        else:
            discovered_names.append(str(comp))
    
    discovered_names = [name.strip() for name in discovered_names if name.strip()]
    
    logger.info(f"\nANALYZING TAVILY RESULTS:")
    logger.info(f"Discovered names: {discovered_names}")
    
    # Check for good competitors found
    good_found = []
    for good_comp in EXPECTED_COMPETITORS['good']:
        for discovered_name in discovered_names:
            if (good_comp.lower() in discovered_name.lower() or 
                discovered_name.lower() in good_comp.lower()):
                good_found.append(good_comp)
                break
    
    # Check for bad competitors (should avoid)
    bad_found = []
    for bad_comp in EXPECTED_COMPETITORS['avoid']:
        for discovered_name in discovered_names:
            if (bad_comp.lower() in discovered_name.lower() or 
                discovered_name.lower() in bad_comp.lower()):
                bad_found.append(bad_comp)
                break
    
    # Calculate accuracy score
    total_expected = len(EXPECTED_COMPETITORS['good'])
    good_ratio = len(good_found) / total_expected if total_expected > 0 else 0
    bad_penalty = len(bad_found) * 0.2  # Each bad competitor reduces score by 20%
    accuracy_score = max(0, good_ratio - bad_penalty)
    
    # Identify issues
    issues = []
    if len(good_found) < 2:
        issues.append('insufficient_good_competitors')
    if len(bad_found) > 0:
        issues.append('big_tech_contamination')
    if len(discovered_names) < 3:
        issues.append('too_few_total_competitors')
    if accuracy_score < 0.3:
        issues.append('very_low_accuracy')
    
    return {
        'accuracy_score': accuracy_score,
        'good_found': good_found,
        'bad_found': bad_found,
        'total_discovered': len(discovered_names),
        'expected_good': len(EXPECTED_COMPETITORS['good']),
        'issues': issues,
        'discovered_names': discovered_names
    }

def log_detailed_analysis(discovered: List[Dict[str, Any]], analysis: Dict[str, Any]):
    """Log detailed results with insights"""
    
    logger.info(f"\n📊 ACCURACY ANALYSIS FOR TAVILY:")
    logger.info(f"  Accuracy Score: {analysis['accuracy_score']:.2f}/1.0")
    logger.info(f"  Good Competitors Found: {analysis['good_found']} ({len(analysis['good_found'])}/{analysis['expected_good']})")
    logger.info(f"  Bad Competitors Found: {analysis['bad_found']} ({len(analysis['bad_found'])} penalties)")
    logger.info(f"  Total Discovered: {analysis['total_discovered']}")
    logger.info(f"  Issues: {analysis['issues']}")
    
    logger.info(f"\n🎯 DETAILED COMPETITOR LIST:")
    for i, comp in enumerate(discovered, 1):
        if isinstance(comp, dict):
            name = comp.get('name', 'Unknown')
            confidence = comp.get('confidence_score', 0)
            category = comp.get('category', 'unknown')
            reasoning = comp.get('reasoning', 'No reasoning provided')
            
            # Determine if this is good or bad
            is_good = any(good.lower() in name.lower() for good in analysis.get('good_found', []))
            is_bad = any(bad.lower() in name.lower() for bad in analysis.get('bad_found', []))
            
            status = "✅ GOOD" if is_good else "❌ BAD" if is_bad else "❓ UNKNOWN"
            
            logger.info(f"  {i}. {name} [{status}]")
            logger.info(f"     Confidence: {confidence:.2f}, Category: {category}")
            logger.info(f"     Reasoning: {reasoning[:150]}...")
        else:
            logger.info(f"  {i}. {comp} [RAW]")
    
    # Provide improvement suggestions
    logger.info(f"\n💡 IMPROVEMENT SUGGESTIONS:")
    if 'big_tech_contamination' in analysis['issues']:
        logger.info("  - CRITICAL: Filter out big tech companies more aggressively")
    if 'insufficient_good_competitors' in analysis['issues']:
        logger.info("  - Improve search queries to target AI search startups specifically")
    if 'too_few_total_competitors' in analysis['issues']:
        logger.info("  - Increase search coverage and fallback strategies")
    if analysis['accuracy_score'] < 0.3:
        logger.info("  - URGENT: Complete overhaul of competitor identification logic needed")

async def main():
    """Run the Tavily competitor discovery test"""
    
    logger.info("🔬 Initializing Tavily Competitor Discovery Test...")
    
    try:
        results = await test_tavily_competitors()
        
        if results:
            # Save results to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"tavily_test_results_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"\n💾 Results saved to: {results_file}")
            
            # Print final summary
            analysis = results['analysis']
            logger.info(f"\n🏁 TAVILY TEST SUMMARY:")
            logger.info(f"   Accuracy Score: {analysis['accuracy_score']:.1%}")
            logger.info(f"   Good Competitors: {len(analysis['good_found'])}/{analysis['expected_good']}")
            logger.info(f"   Bad Competitors: {len(analysis['bad_found'])} (should be 0)")
            
            if analysis['accuracy_score'] < 0.3:
                logger.error("❌ ACCURACY TOO LOW - MAJOR IMPROVEMENTS NEEDED")
                return False
            elif analysis['accuracy_score'] < 0.6:
                logger.warning("⚠️ ACCURACY SUBOPTIMAL - IMPROVEMENTS NEEDED")
                return False
            else:
                logger.info("✅ ACCURACY ACCEPTABLE")
                return True
        else:
            logger.error("❌ Test failed completely")
            return False
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1) 