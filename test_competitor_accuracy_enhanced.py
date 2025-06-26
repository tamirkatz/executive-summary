#!/usr/bin/env python3
"""
Enhanced Competitor Discovery Accuracy Test

Tests the competitor discovery system on multiple real startups to validate
accuracy and identify issues. Includes extensive debug logging.
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
from backend.classes.state import ResearchState

# Configure comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'competitor_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Test cases: Real startups with their expected competitor categories
TEST_STARTUPS = {
    "tavily": {
        "company": "Tavily",
        "description": "AI-powered search API for developers and researchers, providing real-time web search with AI-enhanced results",
        "industry": "Technology",
        "sector": "AI Search",
        "core_products": ["Search API", "AI Search Engine", "Research Assistant"],
        "use_cases": ["Developer tools", "Research automation", "AI applications"],
        "customer_segments": ["Developers", "Researchers", "AI companies"],
        "synonyms": ["AI search", "search API", "intelligent search"],
        "expected_competitors": {
            "good": ["Perplexity", "SearchGPT", "You.com", "Exa", "Metaphor", "Bing Chat", "Phind"],
            "avoid": ["Google", "Microsoft", "Amazon", "Apple", "Meta", "Facebook", "IBM"]
        }
    },
    "lovable": {
        "company": "Lovable", 
        "description": "AI-powered full-stack development platform that builds complete applications from natural language descriptions",
        "industry": "Technology",
        "sector": "AI Development Platform",
        "core_products": ["AI Code Generation", "Full-stack Development", "No-code Platform"],
        "use_cases": ["Rapid prototyping", "MVP development", "AI-assisted coding"],
        "customer_segments": ["Developers", "Startups", "Product managers"],
        "synonyms": ["AI development", "code generation", "AI programming"],
        "expected_competitors": {
            "good": ["Cursor", "v0", "Bolt", "Replit", "GitHub Copilot", "Claude Artifacts", "Windsurf"],
            "avoid": ["Google", "Microsoft", "Amazon", "Oracle", "IBM", "Salesforce"]
        }
    },
    "bubble": {
        "company": "Bubble",
        "description": "Visual programming platform for building web applications without code",
        "industry": "Technology", 
        "sector": "No-code Platform",
        "core_products": ["Visual Programming", "Web App Builder", "Database Management"],
        "use_cases": ["Web app development", "MVP creation", "Business automation"],
        "customer_segments": ["Non-technical founders", "Agencies", "Enterprises"],
        "synonyms": ["no-code", "visual programming", "app builder"],
        "expected_competitors": {
            "good": ["Webflow", "Retool", "Adalo", "Glide", "AppGyver", "OutSystems", "Mendix"],
            "avoid": ["Google", "Microsoft", "Amazon", "Oracle", "IBM", "Salesforce"]
        }
    },
    "supabase": {
        "company": "Supabase",
        "description": "Open source Firebase alternative providing backend-as-a-service with PostgreSQL database",
        "industry": "Technology",
        "sector": "Backend-as-a-Service", 
        "core_products": ["Database", "Authentication", "Storage", "Edge Functions"],
        "use_cases": ["Backend development", "Database hosting", "User authentication"],
        "customer_segments": ["Developers", "Startups", "Indie hackers"],
        "synonyms": ["BaaS", "backend service", "database platform"],
        "expected_competitors": {
            "good": ["Firebase", "PlanetScale", "Neon", "Xata", "Appwrite", "AWS Amplify", "Convex"],
            "avoid": ["Google", "Microsoft", "Amazon", "Oracle", "IBM", "MongoDB"]
        }
    },
    "vercel": {
        "company": "Vercel",
        "description": "Frontend cloud platform for deploying and hosting modern web applications",
        "industry": "Technology",
        "sector": "Frontend Deployment Platform",
        "core_products": ["Static Site Hosting", "Serverless Functions", "Edge Network"],
        "use_cases": ["Website deployment", "JAMstack hosting", "Frontend optimization"],
        "customer_segments": ["Frontend developers", "Web agencies", "Startups"],
        "synonyms": ["deployment platform", "JAMstack", "static hosting"],
        "expected_competitors": {
            "good": ["Netlify", "Railway", "Render", "Fly.io", "Cloudflare Pages", "GitHub Pages"],
            "avoid": ["Google", "Microsoft", "Amazon", "Oracle", "IBM"]
        }
    }
}

class CompetitorAccuracyTester:
    """Comprehensive tester for competitor discovery accuracy"""
    
    def __init__(self):
        self.agent = EnhancedCompetitorDiscoveryAgent()
        self.results = []
        
    async def test_startup(self, startup_name: str, startup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test competitor discovery for a single startup with detailed analysis"""
        
        logger.info(f"\n{'='*60}")
        logger.info(f"TESTING COMPETITOR DISCOVERY FOR: {startup_name.upper()}")
        logger.info(f"{'='*60}")
        
        profile = {k: v for k, v in startup_data.items() if k != 'expected_competitors'}
        expected = startup_data['expected_competitors']
        
        logger.info(f"Profile: {json.dumps(profile, indent=2)}")
        logger.info(f"Expected good competitors: {expected['good']}")
        logger.info(f"Should avoid: {expected['avoid']}")
        
        try:
            # Run competitor discovery
            result = await self.agent.discover_competitors(profile)
            
            discovered_competitors = result.get('competitors', [])
            logger.info(f"\nDISCOVERED {len(discovered_competitors)} COMPETITORS:")
            
            # Analyze results
            analysis = self.analyze_results(discovered_competitors, expected, startup_name)
            
            # Log detailed results
            self.log_detailed_results(discovered_competitors, analysis, startup_name)
            
            return {
                'startup': startup_name,
                'profile': profile,
                'discovered': discovered_competitors,
                'expected': expected,
                'analysis': analysis,
                'queries_used': result.get('search_queries_used', [])
            }
            
        except Exception as e:
            logger.error(f"ERROR testing {startup_name}: {e}", exc_info=True)
            return {
                'startup': startup_name,
                'error': str(e),
                'analysis': {'accuracy_score': 0, 'issues': ['test_failed']}
            }
    
    def analyze_results(self, discovered: List[Dict[str, Any]], expected: Dict[str, List[str]], startup_name: str) -> Dict[str, Any]:
        """Analyze the accuracy of discovered competitors"""
        
        discovered_names = []
        for comp in discovered:
            if isinstance(comp, dict):
                discovered_names.append(comp.get('name', ''))
            else:
                discovered_names.append(str(comp))
        
        discovered_names = [name.strip() for name in discovered_names if name.strip()]
        
        logger.info(f"\nANALYZING RESULTS FOR {startup_name}:")
        logger.info(f"Discovered names: {discovered_names}")
        
        # Check for good competitors found
        good_found = []
        for good_comp in expected['good']:
            for discovered_name in discovered_names:
                if (good_comp.lower() in discovered_name.lower() or 
                    discovered_name.lower() in good_comp.lower()):
                    good_found.append(good_comp)
                    break
        
        # Check for bad competitors (should avoid)
        bad_found = []
        for bad_comp in expected['avoid']:
            for discovered_name in discovered_names:
                if (bad_comp.lower() in discovered_name.lower() or 
                    discovered_name.lower() in bad_comp.lower()):
                    bad_found.append(bad_comp)
                    break
        
        # Calculate accuracy score
        total_expected = len(expected['good'])
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
            'expected_good': len(expected['good']),
            'issues': issues,
            'discovered_names': discovered_names
        }
    
    def log_detailed_results(self, discovered: List[Dict[str, Any]], analysis: Dict[str, Any], startup_name: str):
        """Log detailed results with insights"""
        
        logger.info(f"\n📊 ACCURACY ANALYSIS FOR {startup_name}:")
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
                logger.info(f"     Reasoning: {reasoning[:100]}...")
            else:
                logger.info(f"  {i}. {comp} [RAW]")
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run tests on all startups and generate comprehensive report"""
        
        logger.info(f"\n🚀 STARTING COMPREHENSIVE COMPETITOR DISCOVERY ACCURACY TEST")
        logger.info(f"Testing {len(TEST_STARTUPS)} startups: {list(TEST_STARTUPS.keys())}")
        
        test_results = []
        
        for startup_name, startup_data in TEST_STARTUPS.items():
            result = await self.test_startup(startup_name, startup_data)
            test_results.append(result)
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        # Generate overall report
        report = self.generate_overall_report(test_results)
        
        logger.info(f"\n📋 OVERALL ACCURACY REPORT:")
        logger.info(f"Average Accuracy: {report['average_accuracy']:.2f}/1.0")
        logger.info(f"Tests Passed: {report['tests_passed']}/{report['total_tests']}")
        logger.info(f"Common Issues: {report['common_issues']}")
        
        return {
            'test_results': test_results,
            'overall_report': report
        }
    
    def generate_overall_report(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate an overall accuracy report"""
        
        total_tests = len(test_results)
        successful_tests = [r for r in test_results if 'error' not in r]
        
        if not successful_tests:
            return {
                'average_accuracy': 0,
                'tests_passed': 0,
                'total_tests': total_tests,
                'common_issues': ['all_tests_failed']
            }
        
        # Calculate average accuracy
        accuracies = [r['analysis']['accuracy_score'] for r in successful_tests]
        average_accuracy = sum(accuracies) / len(accuracies)
        
        # Count tests that passed (accuracy > 0.5)
        tests_passed = len([a for a in accuracies if a > 0.5])
        
        # Identify common issues
        all_issues = []
        for result in successful_tests:
            all_issues.extend(result['analysis']['issues'])
        
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        common_issues = [issue for issue, count in issue_counts.items() if count >= 2]
        
        return {
            'average_accuracy': average_accuracy,
            'tests_passed': tests_passed,
            'total_tests': total_tests,
            'common_issues': common_issues,
            'issue_breakdown': issue_counts
        }

async def main():
    """Run the comprehensive competitor discovery accuracy test"""
    
    logger.info("🔬 Initializing Competitor Discovery Accuracy Test...")
    
    tester = CompetitorAccuracyTester()
    
    try:
        results = await tester.run_comprehensive_test()
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"competitor_accuracy_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\n💾 Results saved to: {results_file}")
        
        # Print final summary
        report = results['overall_report']
        logger.info(f"\n🏁 FINAL SUMMARY:")
        logger.info(f"   Average Accuracy: {report['average_accuracy']:.1%}")
        logger.info(f"   Success Rate: {report['tests_passed']}/{report['total_tests']} ({report['tests_passed']/report['total_tests']:.1%})")
        
        if report['average_accuracy'] < 0.3:
            logger.error("❌ ACCURACY TOO LOW - MAJOR IMPROVEMENTS NEEDED")
        elif report['average_accuracy'] < 0.6:
            logger.warning("⚠️ ACCURACY SUBOPTIMAL - IMPROVEMENTS NEEDED")
        else:
            logger.info("✅ ACCURACY ACCEPTABLE")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    asyncio.run(main()) 