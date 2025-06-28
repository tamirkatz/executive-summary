#!/usr/bin/env python3

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.nodes.competitor_analyst_agent import CompetitorAnalystAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class MockWebSocketManager:
    async def send_status_update(self, job_id: str, message: dict):
        timestamp = datetime.now().isoformat()
        print(f"🔍 Status Update [{timestamp}]: {json.dumps(message, indent=2)}")


async def test_unipaas_competitor_analysis():
    print("=" * 80)
    print("🧪 TESTING UNIPAAS COMPETITOR ANALYST AGENT")
    print("=" * 80)
    try:
        agent = CompetitorAnalystAgent()
        print(f"✅ Agent initialized successfully")
        print(f"📅 Date range: {agent.three_months_ago.strftime('%Y-%m-%d')} to {agent.current_date.strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    competitors = ["Unipaas"]
    test_state = {
        "company": "Unipaas",
        "competitors": [{"name": comp, "category": "direct"} for comp in competitors],
        "profile": {
            "sector": "fintech",
            "industry": "payment processing",
            "business_model": "B2B payment solutions",
            "description": "Payment orchestration platform"
        },
        "job_id": "test_unipaas_analysis",
        "websocket_manager": MockWebSocketManager(),
        "messages": []
    }
    print(f"\n🏢 Testing Company: {test_state['company']}")
    print(f"🎯 Competitors: {', '.join(competitors)}")
    print(f"🏷️ Sector: {test_state['profile']['sector']}")
    start_time = datetime.now()
    print(f"\n⏰ Analysis started at: {start_time.strftime('%H:%M:%S')}")
    try:
        result_state = await agent.run(test_state)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"\n⏱️ Analysis completed in {duration:.1f} seconds")
        print("=" * 80)
        competitor_analysis = result_state.get("competitor_analysis", {})
        strategic_news = competitor_analysis.get("strategic_news", [])
        print(f"📊 RESULTS SUMMARY:")
        print(f"   • Competitors analyzed: {competitor_analysis.get('competitors_analyzed', 0)}")
        print(f"   • Strategic moves found: {len(strategic_news)}")
        print(f"   • Analysis date: {competitor_analysis.get('analysis_date', 'N/A')}")
        print(f"   • Time period: {competitor_analysis.get('time_period_days', 0)} days")
        if strategic_news:
            print(f"\n📰 RECENT STRATEGIC MOVES:")
            for i, news in enumerate(strategic_news, 1):
                print(f"\n   {i}. {news.get('competitor', 'Unknown')} - {news.get('category', 'Unknown').upper()}")
                print(f"      📋 {news.get('title', 'No title')}")
                print(f"      📅 {news.get('date', 'No date')}")
                print(f"      💰 {news.get('financial_details', 'No financial details')}")
                print(f"      🎯 Impact: {news.get('strategic_impact', 'No impact analysis')[:100]}...")
                print(f"      🔗 {news.get('source', 'No source')}")
                print(f"      📊 Confidence: {news.get('confidence', 0):.2f} | Relevance: {news.get('relevance_score', 0):.2f}")
        else:
            print(f"\n⚠️  No recent strategic moves found.")
        print(f"\n⚡ PERFORMANCE ANALYSIS:")
        if duration > 120:
            print(f"   ⚠️  Analysis took {duration:.1f}s - consider optimization")
        elif duration > 60:
            print(f"   ⚡ Analysis took {duration:.1f}s - acceptable performance")
        else:
            print(f"   🚀 Analysis took {duration:.1f}s - excellent performance")
        recent_count = 0
        old_count = 0
        current_year = datetime.now().year
        for news in strategic_news:
            news_date = news.get('date', '')
            if str(current_year) in news_date or str(current_year - 1) in news_date:
                recent_count += 1
            elif any(str(year) in news_date for year in range(2020, current_year - 1)):
                old_count += 1
        print(f"\n📅 DATE VALIDATION:")
        print(f"   ✅ Recent news (2024-2025): {recent_count}")
        print(f"   ❌ Old news (2020-2023): {old_count}")
        print(f"   ❓ Undated news: {len(strategic_news) - recent_count - old_count}")
        if old_count > 0:
            print(f"   ⚠️  WARNING: Found {old_count} old news items - date filtering needs improvement")
        output_file = f"unipaas_competitor_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            serializable_result = json.loads(json.dumps(competitor_analysis, default=str))
            json.dump(serializable_result, f, indent=2)
        print(f"\n💾 Detailed results saved to: {output_file}")
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"\n❌ Analysis failed after {duration:.1f}s: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    required_vars = ["OPENAI_API_KEY", "TAVILY_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment")
        sys.exit(1)
    asyncio.run(test_unipaas_competitor_analysis()) 