#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.nodes.user_profile_enrichment_agent import UserProfileEnrichmentAgent

async def test_enhanced_business_extraction():
    """Test the enhanced business description extraction for Tavily"""
    print("🔧 Testing Enhanced Business Description Extraction")
    print("=" * 60)
    
    try:
        # Initialize the profile enrichment agent
        agent = UserProfileEnrichmentAgent()
        
        print("🌐 Testing Tavily website analysis...")
        print("   URL: https://tavily.com")
        
        # Test the enhanced company info extraction
        business_description = await agent._scrape_company_info("https://tavily.com")
        
        print(f"\n📄 Extracted Business Description:")
        print(f"   Length: {len(business_description)} characters")
        print(f"   Content: {business_description}")
        
        # Analyze the description quality
        print(f"\n🔍 Analysis:")
        keywords_found = []
        
        # Check for AI/search/API keywords
        ai_keywords = ["ai", "artificial intelligence", "search", "api", "crawl", "data", "agent", "llm"]
        travel_keywords = ["travel", "booking", "hotel", "flight", "vacation", "tourism"]
        content_keywords = ["content", "marketing", "brand", "about us", "storytelling"]
        
        description_lower = business_description.lower()
        
        for keyword in ai_keywords:
            if keyword in description_lower:
                keywords_found.append(f"✅ AI/Tech: '{keyword}'")
        
        for keyword in travel_keywords:
            if keyword in description_lower:
                keywords_found.append(f"❌ Travel: '{keyword}'")
        
        for keyword in content_keywords:
            if keyword in description_lower:
                keywords_found.append(f"⚠️  Content: '{keyword}'")
        
        if keywords_found:
            print("   Keywords found:")
            for kw in keywords_found:
                print(f"     {kw}")
        else:
            print("   ⚠️  No relevant keywords found")
        
        # Test full profile enrichment with enhanced extraction
        print(f"\n🧪 Testing Full Profile with Enhanced Extraction:")
        profile = await agent.enrich_profile_async(
            company="Tavily",
            role="CEO", 
            company_url="https://tavily.com"
        )
        
        print(f"\n📊 Profile Results:")
        print(f"   Industry: {profile.get('industry', 'Unknown')}")
        print(f"   Sector: {profile.get('sector', 'Unknown')}")
        print(f"   Description: {profile.get('description', 'Unknown')}")
        print(f"   Competitors: {profile.get('competitors', [])[:5]}...")  # Show first 5
        
        # Evaluate success
        success_indicators = []
        
        # Check if industry is more accurate
        industry = profile.get('industry', '').lower()
        if any(tech_term in industry for tech_term in ['technology', 'ai', 'artificial intelligence', 'software', 'search', 'data', 'api']):
            success_indicators.append("✅ Industry correctly identified as technology-related")
        else:
            success_indicators.append(f"❌ Industry still incorrect: {profile.get('industry', 'Unknown')}")
        
        # Check if description is better
        description = profile.get('description', '').lower()
        if any(tech_term in description for tech_term in ['ai', 'search', 'api', 'data', 'crawl']):
            success_indicators.append("✅ Description mentions relevant technology terms")
        else:
            success_indicators.append("❌ Description still doesn't capture AI/search nature")
        
        # Check competitors
        competitors = profile.get('competitors', [])
        tech_competitors = [c for c in competitors if any(tech in c.lower() for tech in ['algolia', 'elastic', 'google', 'microsoft', 'openai'])]
        travel_competitors = [c for c in competitors if any(travel in c.lower() for travel in ['trip', 'airbnb', 'booking', 'expedia'])]
        
        if tech_competitors and not travel_competitors:
            success_indicators.append(f"✅ Found relevant tech competitors: {tech_competitors}")
        elif travel_competitors:
            success_indicators.append(f"❌ Still finding travel competitors: {travel_competitors}")
        else:
            success_indicators.append("⚠️  No obvious tech or travel competitors found")
        
        print(f"\n📈 Success Analysis:")
        for indicator in success_indicators:
            print(f"   {indicator}")
        
        # Overall assessment
        success_count = len([s for s in success_indicators if s.startswith("✅")])
        total_indicators = len(success_indicators)
        
        if success_count >= total_indicators * 0.7:  # 70% success rate
            print(f"\n🎉 SUCCESS: Enhanced extraction working well ({success_count}/{total_indicators} indicators positive)")
            return True
        else:
            print(f"\n⚠️  PARTIAL: Some improvement but needs work ({success_count}/{total_indicators} indicators positive)")
            return False
        
    except Exception as e:
        print(f"❌ Error testing enhanced extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_enhanced_business_extraction())
    if result:
        print("\n🚀 Enhanced business description extraction is working!")
    else:
        print("\n🔧 Needs further refinement.") 