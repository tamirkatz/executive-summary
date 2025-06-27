#!/usr/bin/env python3
"""
Test script for the new Comprehensive Data Synthesizer node
This demonstrates how the synthesizer consolidates data from all agents
"""

import asyncio
import logging
from backend.classes.state import ResearchState
from backend.nodes.comprehensive_data_synthesizer import ComprehensiveDataSynthesizer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_mock_state():
    """Create a mock state with sample data from various agents"""
    
    # Mock state with data from various agents
    mock_state = ResearchState(
        company="TechStart AI",
        user_role="CEO",
        
        # Company profile data (from profile enrichment)
        profile={
            'industry': 'Artificial Intelligence',
            'business_model': 'B2B SaaS',
            'target_market': 'Enterprise software companies',
            'key_products': ['AI-powered analytics platform', 'ML model deployment tools'],
            'revenue_streams': ['Subscription fees', 'Professional services', 'API usage'],
            'competitive_positioning': 'Focus on enterprise AI deployment and monitoring'
        },
        
        # Competitor data (from competitor discovery and analysis)
        discovered_competitors=[
            'DataRobot', 'H2O.ai', 'Databricks', 'MLOps.ai', 'Weights & Biases'
        ],
        competitor_analysis={
            'DataRobot': {
                'market_position': 'Leader in AutoML',
                'strengths': ['Comprehensive platform', 'Enterprise focus'],
                'weaknesses': ['High cost', 'Complex setup']
            },
            'H2O.ai': {
                'market_position': 'Open source leader',
                'strengths': ['Strong community', 'Cost-effective'],
                'weaknesses': ['Limited enterprise features']
            }
        },
        
        # Trend data (from sector and client trend agents)
        sector_trends={
            'ai_adoption': 'Rapid growth in enterprise AI adoption',
            'regulatory_changes': 'Increasing AI governance requirements',
            'market_consolidation': 'Major acquisitions in AI space'
        },
        client_trends={
            'enterprise_software_trends': 'Shift towards AI-first solutions',
            'budget_allocation': 'Increased spending on AI/ML initiatives',
            'integration_needs': 'Demand for seamless AI integration'
        },
        
        # Market intelligence (from various research agents)
        curated_news_data={
            'tech_news_1': {
                'title': 'Enterprise AI Spending Reaches $50B',
                'raw_content': 'Companies are increasing AI investments...',
                'evaluation': {'overall_score': 8}
            }
        },
        curated_financial_data={
            'funding_round_1': {
                'title': 'AI Startup Raises $100M Series B',
                'raw_content': 'Competition is heating up in AI space...',
                'evaluation': {'overall_score': 7}
            }
        },
        
        # Research results from various researchers
        research_results={
            'market_analysis': 'AI market growing at 25% CAGR',
            'competitive_landscape': 'Fragmented market with consolidation trends'
        },
        
        # User context (from interest inference and research planning)
        inferred_interests=['competitive intelligence', 'market opportunities', 'strategic planning'],
        research_intent={
            'primary_goal': 'Strategic market positioning',
            'decision_timeframe': 'Q1 2024',
            'key_concerns': ['Competition', 'Market timing', 'Product differentiation']
        }
    )
    
    return mock_state

async def test_comprehensive_synthesis():
    """Test the comprehensive data synthesizer"""
    
    logger.info("🧪 Starting Comprehensive Data Synthesizer test")
    
    try:
        # Initialize the synthesizer
        synthesizer = ComprehensiveDataSynthesizer()
        logger.info("✅ ComprehensiveDataSynthesizer initialized successfully")
        
        # Create mock state with comprehensive data
        state = create_mock_state()
        logger.info("✅ Mock state created with comprehensive data")
        
        # Run the synthesis
        logger.info("🔄 Running comprehensive data synthesis...")
        result_state = await synthesizer.run(state)
        
        # Check results
        if 'comprehensive_synthesis' in result_state:
            synthesis = result_state['comprehensive_synthesis']
            
            logger.info("✅ Comprehensive synthesis completed successfully!")
            logger.info(f"📊 Company: {synthesis.get('company')}")
            logger.info(f"👤 User Role: {synthesis.get('user_role')}")
            
            # Log key insights
            key_insights = synthesis.get('key_insights', [])
            logger.info(f"💡 Key Insights Generated: {len(key_insights)}")
            for i, insight in enumerate(key_insights, 1):
                logger.info(f"   {i}. {insight.get('insight_title', 'No title')} ({insight.get('impact_level', 'Unknown')} impact)")
            
            # Log competitor summary
            competitor_summary = synthesis.get('competitor_summary', {})
            top_competitors = competitor_summary.get('top_competitors', [])
            logger.info(f"🏢 Top Competitors Identified: {len(top_competitors)}")
            
            # Log trend summary
            trend_summary = synthesis.get('trend_summary', {})
            logger.info(f"📈 Trend Analysis: Available")
            
            # Log strategic recommendations
            recommendations = synthesis.get('strategic_recommendations', [])
            logger.info(f"🎯 Strategic Recommendations: {len(recommendations)}")
            for i, rec in enumerate(recommendations, 1):
                logger.info(f"   {i}. {rec.get('title', 'No title')} (Priority: {rec.get('priority', 'Unknown')})")
            
            # Log data coverage
            data_coverage = synthesis.get('data_coverage', {})
            logger.info("📋 Data Coverage:")
            for source, available in data_coverage.items():
                status = "✅" if available else "❌"
                logger.info(f"   {status} {source}")
            
        else:
            logger.error("❌ No comprehensive synthesis found in result state")
            
        logger.info("🎉 Test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_comprehensive_synthesis()) 