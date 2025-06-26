import asyncio
import logging
from backend.nodes.competitor_discovery_agent import EnhancedCompetitorDiscoveryAgent

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_competitor_discovery():
    """Debug the competitor discovery process step by step"""
    
    # Test with Tavily case (should find Perplexity, SearchGPT, You.com, Exa)
    test_profile = {
        "company": "Tavily",
        "description": "Tavily is an AI-powered search API designed for autonomous agents and RAG applications, providing real-time web search capabilities.",
        "industry": "Artificial Intelligence",
        "sector": "AI Search API",
        "customer_segments": ["AI Developers", "Enterprise", "Researchers"],
        "core_products": ["Search API", "Real-time Web Search", "AI Agent Integration"],
        "use_cases": ["AI Agent Search", "RAG Applications", "Real-time Information Retrieval"],
        "synonyms": ["AI Search", "Search API", "Agent Search"]
    }
    
    agent = EnhancedCompetitorDiscoveryAgent()
    
    print("🔍 Debug Test: Tavily AI Search API")
    print("=" * 50)
    
    # Step 1: Test query generation
    print("\n📝 Step 1: Query Generation")
    try:
        queries = await agent._generate_targeted_queries(test_profile)
        print(f"Generated {len(queries)} queries:")
        for i, q in enumerate(queries[:5], 1):
            print(f"  {i}. {q['query']} ({q['type']})")
        
        if len(queries) == 0:
            print("❌ NO QUERIES GENERATED - This is the problem!")
            return
            
    except Exception as e:
        print(f"❌ Query generation failed: {e}")
        return
    
    # Step 2: Test search execution (just one query)
    print(f"\n🔍 Step 2: Search Execution (testing first query)")
    try:
        test_query = queries[0]
        search_results = await agent._single_targeted_search(test_query, "Tavily")
        print(f"Search results for '{test_query['query']}':")
        print(f"  - Found {len(search_results)} results")
        
        if search_results:
            for i, result in enumerate(search_results[:2], 1):
                content_preview = result.get('content', '')[:100] + "..." if result.get('content') else "No content"
                print(f"  {i}. {result.get('title', 'No title')}")
                print(f"     {content_preview}")
        
    except Exception as e:
        print(f"❌ Search execution failed: {e}")
        return
    
    # Step 3: Test competitor extraction from one result
    print(f"\n🏢 Step 3: Competitor Extraction")
    try:
        if search_results:
            # Show the actual content being analyzed
            print(f"\n🔍 Content being analyzed:")
            for i, result in enumerate(search_results[:2], 1):
                content = result.get('content', '')[:300]
                print(f"  Result {i}: {content}...")
            
            competitors = await agent._extract_companies_from_result_batch(
                search_results[:2], test_profile, "Tavily", test_query['type']
            )
            print(f"Extracted competitors: {list(competitors)}")
            
            if len(competitors) == 0:
                print("❌ NO COMPETITORS EXTRACTED - This might be the problem!")
                
                # Let's manually test with known competitors in content
                print("\n🧪 Testing extraction with manual content containing known competitors...")
                manual_content = """
                Best AI search APIs for RAG applications include Perplexity AI, SearchGPT, You.com, 
                Exa (formerly Metaphor), and SerpAPI. These platforms offer real-time web search 
                capabilities similar to Tavily. Perplexity provides conversational search, while 
                SearchGPT offers OpenAI-powered search. You.com focuses on private search, and 
                Exa specializes in semantic search for AI applications.
                """
                
                # Test extraction on this manual content
                manual_results = [{
                    'content': manual_content,
                    'title': 'Test content with known competitors',
                    'query_type': 'test',
                    'query_context': 'Manual test',
                    'original_query': 'test'
                }]
                
                manual_competitors = await agent._extract_companies_from_result_batch(
                    manual_results, test_profile, "Tavily", "test"
                )
                print(f"Manual test extracted: {list(manual_competitors)}")
                
                if len(manual_competitors) == 0:
                    print("❌ Even manual extraction failed - the extraction logic is broken!")
                else:
                    print("✅ Manual extraction worked - the search results don't contain competitors")
            
        else:
            print("❌ No search results to extract from")
            
    except Exception as e:
        print(f"❌ Competitor extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Test validation (if we have competitors)
    if 'competitors' in locals() and competitors:
        print(f"\n✅ Step 4: Competitor Validation")
        try:
            first_competitor = list(competitors)[0]
            validation = await agent._validate_single_competitor(
                first_competitor, test_profile, "Tavily"
            )
            
            if validation:
                print(f"Validation result for '{first_competitor}':")
                print(f"  - Category: {validation.get('category')}")
                print(f"  - Confidence: {validation.get('confidence_score')}")
                print(f"  - Reasoning: {validation.get('reasoning', 'No reasoning')}")
            else:
                print(f"❌ '{first_competitor}' was rejected during validation")
            
        except Exception as e:
            print(f"❌ Competitor validation failed: {e}")
    
    print(f"\n🏁 Debug complete")

if __name__ == "__main__":
    asyncio.run(debug_competitor_discovery()) 