import asyncio
import json
import logging
from backend.nodes.competitor_discovery_agent import EnhancedCompetitorDiscoveryAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test cases with expected competitor types
TEST_COMPANIES = [
    {
        "company": "base44",
        "description": "Base44 is a Software-as-a-Service (SaaS) platform that enables users to create fully functioning web applications without the need for coding, utilizing a natural language development approach.",
        "industry": "Software as a Service",
        "sector": "No-Code Development Platform",
        "customer_segments": ["Creative Professionals", "Small Business Owners", "Entrepreneurs", "Non-Technical Users"],
        "core_products": ["No-Code Application Builder", "AI Development Tools", "Web Application Hosting"],
        "use_cases": ["Building Custom Web Applications", "No-Code Development", "AI-Driven Application Creation"],
        "synonyms": ["No-Code Platform", "Low-Code Development", "AI-Powered Development"],
        "expected_competitors": ["Bubble", "Webflow", "Retool", "Lovable", "Bolt", "Framer", "Glide"]
    },
    {
        "company": "Tavily",
        "description": "Tavily is an AI-powered search API designed for autonomous agents and RAG applications, providing real-time web search capabilities.",
        "industry": "Artificial Intelligence",
        "sector": "AI Search API",
        "customer_segments": ["AI Developers", "Enterprise", "Researchers", "Startups"],
        "core_products": ["Search API", "Real-time Web Search", "AI Agent Integration"],
        "use_cases": ["AI Agent Search", "RAG Applications", "Real-time Information Retrieval"],
        "synonyms": ["AI Search", "Search API", "Agent Search"],
        "expected_competitors": ["Perplexity", "SearchGPT", "You.com", "Exa", "Metaphor", "SerpAPI"]
    },
    {
        "company": "Cursor",
        "description": "Cursor is an AI-powered code editor that helps developers write code faster with intelligent completions and AI assistance.",
        "industry": "Developer Tools",
        "sector": "AI Code Editor",
        "customer_segments": ["Software Developers", "Engineers", "Startups", "Tech Companies"],
        "core_products": ["AI Code Editor", "Code Completion", "AI Pair Programming"],
        "use_cases": ["AI-Assisted Coding", "Code Generation", "Developer Productivity"],
        "synonyms": ["AI IDE", "Smart Code Editor", "AI Programming Assistant"],
        "expected_competitors": ["GitHub Copilot", "Replit", "CodeWhisperer", "Tabnine", "Codeium"]
    },
    {
        "company": "Linear",
        "description": "Linear is a modern issue tracking and project management tool designed for high-performance teams.",
        "industry": "Productivity Software",
        "sector": "Project Management",
        "customer_segments": ["Engineering Teams", "Startups", "Product Teams", "Tech Companies"],
        "core_products": ["Issue Tracking", "Project Management", "Team Collaboration"],
        "use_cases": ["Bug Tracking", "Sprint Planning", "Team Organization"],
        "synonyms": ["Issue Tracker", "Project Management Tool", "Development Workflow"],
        "expected_competitors": ["Jira", "Asana", "Height", "Shortcut", "ClickUp", "Monday.com"]
    },
    {
        "company": "Vercel",
        "description": "Vercel is a cloud platform for frontend frameworks and static sites, optimized for performance and developer experience.",
        "industry": "Cloud Computing",
        "sector": "Frontend Deployment Platform",
        "customer_segments": ["Frontend Developers", "Startups", "Agencies", "Enterprise"],
        "core_products": ["Static Site Hosting", "Serverless Functions", "Edge Network"],
        "use_cases": ["Frontend Deployment", "Static Site Hosting", "Edge Computing"],
        "synonyms": ["JAMstack Platform", "Frontend Cloud", "Static Hosting"],
        "expected_competitors": ["Netlify", "Cloudflare Pages", "AWS Amplify", "Railway", "Render"]
    }
]

async def test_competitor_discovery():
    """Test the enhanced competitor discovery agent on multiple companies"""
    
    agent = EnhancedCompetitorDiscoveryAgent()
    results = {}
    
    print("🧪 Testing Enhanced Competitor Discovery Agent")
    print("=" * 60)
    
    for test_case in TEST_COMPANIES:
        company_name = test_case["company"]
        expected = set(test_case["expected_competitors"])
        
        print(f"\n🔍 Testing: {company_name}")
        print(f"Sector: {test_case['sector']}")
        print(f"Expected competitors: {', '.join(expected)}")
        print("-" * 40)
        
        try:
            # Test competitor discovery
            result = await agent.discover_competitors(
                enriched_profile=test_case,
                websocket_manager=None,
                job_id=None
            )
            
            discovered = result.get('competitors', [])
            discovered_names = set([comp.get('name', comp) if isinstance(comp, dict) else comp for comp in discovered])
            
            print(f"✅ Discovered: {', '.join(discovered_names)}")
            
            # Calculate accuracy metrics
            correct_matches = expected.intersection(discovered_names)
            precision = len(correct_matches) / len(discovered_names) if discovered_names else 0
            recall = len(correct_matches) / len(expected) if expected else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            # Check for big tech false positives
            big_tech = {'Google', 'Microsoft', 'Amazon', 'Apple', 'Meta', 'Facebook', 'IBM', 'Oracle', 'Teams', 'Slack'}
            false_positives = discovered_names.intersection(big_tech)
            
            results[company_name] = {
                "discovered": list(discovered_names),
                "expected": list(expected),
                "correct_matches": list(correct_matches),
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score,
                "big_tech_false_positives": list(false_positives),
                "total_discovered": len(discovered_names)
            }
            
            print(f"📊 Metrics:")
            print(f"  - Correct matches: {list(correct_matches)}")
            print(f"  - Precision: {precision:.2f}")
            print(f"  - Recall: {recall:.2f}")
            print(f"  - F1 Score: {f1_score:.2f}")
            
            if false_positives:
                print(f"  - ❌ Big Tech False Positives: {list(false_positives)}")
            else:
                print(f"  - ✅ No Big Tech False Positives")
            
        except Exception as e:
            print(f"❌ Error testing {company_name}: {e}")
            results[company_name] = {"error": str(e)}
    
    # Calculate overall metrics
    print("\n" + "=" * 60)
    print("📈 OVERALL RESULTS")
    print("=" * 60)
    
    total_f1 = sum(r.get('f1_score', 0) for r in results.values())
    avg_f1 = total_f1 / len([r for r in results.values() if 'f1_score' in r])
    
    total_precision = sum(r.get('precision', 0) for r in results.values())
    avg_precision = total_precision / len([r for r in results.values() if 'precision' in r])
    
    total_recall = sum(r.get('recall', 0) for r in results.values())
    avg_recall = total_recall / len([r for r in results.values() if 'recall' in r])
    
    total_big_tech_fps = sum(len(r.get('big_tech_false_positives', [])) for r in results.values())
    
    print(f"Average F1 Score: {avg_f1:.2f}")
    print(f"Average Precision: {avg_precision:.2f}")
    print(f"Average Recall: {avg_recall:.2f}")
    print(f"Total Big Tech False Positives: {total_big_tech_fps}")
    
    # Quality assessment
    if avg_f1 > 0.6 and total_big_tech_fps == 0:
        print("✅ EXCELLENT: High accuracy with no false positives")
    elif avg_f1 > 0.4 and total_big_tech_fps <= 2:
        print("✅ GOOD: Decent accuracy with minimal false positives")
    elif avg_f1 > 0.2:
        print("⚠️  NEEDS IMPROVEMENT: Low accuracy")
    else:
        print("❌ POOR: Very low accuracy, major improvements needed")
    
    # Save detailed results
    with open('competitor_discovery_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: competitor_discovery_test_results.json")
    return results

if __name__ == "__main__":
    asyncio.run(test_competitor_discovery()) 