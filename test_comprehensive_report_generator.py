#!/usr/bin/env python3

import asyncio
import json
import logging
from typing import Dict, Any
from backend.nodes.comprehensive_report_generator import ComprehensiveReportGenerator
from backend.classes.state import ResearchState

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestComprehensiveReportGenerator:
    """Test the comprehensive report generator with real research data"""
    
    def __init__(self):
        self.report_generator = ComprehensiveReportGenerator()
    
    def create_test_state(self) -> ResearchState:
        """Create a test state with the actual data from the research workflow"""
        
        # Profile data from the research
        profile_data = {
            "company": "Nuvei",
            "role": "CEO",
            "description": "Nuvei is a Canadian fintech company that provides a comprehensive suite of B2B payment solutions, enabling businesses to accept various payment methods, including credit cards, bank transfers, and alternative payment options across more than 200 markets.",
            "industry": "Financial Technology",
            "sector": "Payment Processing",
            "customer_segments": ["E-commerce", "iGaming", "Retail", "Travel", "Hospitality", "Subscription Services"],
            "known_clients": ["Shopify", "DraftKings", "888 Holdings", "Loto-Québec"],
            "partners": ["Shopify", "Magento", "WooCommerce", "Salesforce", "PayPal"],
            "use_cases": ["Payment processing", "Fraud prevention", "Risk management", "Transaction analytics"],
            "core_products": ["Payment Gateway", "Fraud Detection Tools", "Risk Management Solutions"]
        }
        
        # Competitor discovery data
        competitor_discovery_data = {
            "direct": [
                {"name": "FIS Global", "description": "FIS offers more than 500 solutions", "confidence": 0.89},
                {"name": "Stripe", "description": "Payment processing platform", "confidence": 0.89},
                {"name": "Adyen", "description": "Dutch payment company", "confidence": 0.9}
            ],
            "indirect": [],
            "emerging": [{"name": "FamPay", "description": "Digital payment startup", "confidence": 0.72}]
        }
        
        # Competitor analysis data with news items
        competitor_analysis_data = {
            "news_items": [
                {
                    "competitor": "FIS Global",
                    "title": "Global Payments shares plunge 17% after company announces $24 billion Worldpay deal",
                    "summary": "FIS Global announced a $24.25 billion deal to sell Worldpay to Global Payments.",
                    "impact": "This deal allows FIS to focus on its core business.",
                    "date": "2025-04-17"
                },
                {
                    "competitor": "Stripe",
                    "title": "Stripe closes $1.1 billion Bridge deal, prepares for aggressive stablecoin push",
                    "summary": "Stripe completed a $1.1 billion acquisition of Bridge, a stablecoin platform.",
                    "impact": "The acquisition positions Stripe to capitalize on the growing stablecoin market.",
                    "date": "2025-02-04"
                }
            ]
        }
        
        # Sector trends data
        sector_trends_data = [
            {
                "trend": "Global cashless payment volumes are set to increase by more than 80% from 2020 to 2025.",
                "impact": "Growing importance of digital payment solutions.",
                "confidence_score": 0.9
            },
            {
                "trend": "Increased focus on fraud mitigation and risk management in payment services.",
                "impact": "Advanced fraud detection solutions are in demand.",
                "confidence_score": 0.9
            }
        ]
        
        # Client trends data
        client_trends_data = [
            {
                "trend": "AI-driven automation is reshaping retail business models and value chains.",
                "impact": "Increased demand for seamless payment solutions integrated with AI-driven retail systems.",
                "confidence_score": 0.9
            },
            {
                "trend": "Subscription models are transforming e-commerce and retail sectors.",
                "impact": "New revenue streams for recurring payment solutions.",
                "confidence_score": 0.85
            }
        ]
        
        # Create the state
        state = ResearchState()
        state.update({
            'company': 'Nuvei',
            'user_role': 'CEO',
            'profile': profile_data,
            'competitor_discovery': competitor_discovery_data,
            'competitor_analysis': competitor_analysis_data,
            'competitors': [comp for comp in competitor_discovery_data['direct'] + competitor_discovery_data['emerging']],
            'sector_trends': sector_trends_data,
            'client_trends': client_trends_data,
            'messages': []
        })
        
        return state
    
    async def test_report_generation(self):
        """Test the comprehensive report generator with the research data"""
        logger.info("🧪 Testing Comprehensive Report Generator")
        
        # Create test state with real data
        test_state = self.create_test_state()
        
        logger.info(f"📊 Test state prepared with:")
        logger.info(f"  - Company: {test_state.get('company')}")
        logger.info(f"  - Competitors: {len(test_state.get('competitors', []))}")
        logger.info(f"  - Sector trends: {len(test_state.get('sector_trends', []))}")
        logger.info(f"  - Client trends: {len(test_state.get('client_trends', []))}")
        
        try:
            # Run the comprehensive report generator
            logger.info("🚀 Running comprehensive report generator...")
            result_state = await self.report_generator.run(test_state)
            
            # Check if report was generated
            report = result_state.get('report')
            if report:
                logger.info(f"✅ Report generated successfully!")
                logger.info(f"📄 Report length: {len(report)} characters")
                
                # Print report sections
                print("\n" + "="*80)
                print("GENERATED COMPREHENSIVE REPORT")
                print("="*80)
                print(report)
                print("="*80)
                
                return True, report
            else:
                logger.error("❌ No report found in result state")
                return False, None
                
        except Exception as e:
            logger.error(f"❌ Error during report generation: {e}")
            import traceback
            traceback.print_exc()
            return False, None

async def main():
    """Main test function"""
    tester = TestComprehensiveReportGenerator()
    
    logger.info("🔬 Starting Comprehensive Report Generator Test")
    success, report = await tester.test_report_generation()
    
    if success:
        print("\n🎯 TEST PASSED: Comprehensive Report Generator works correctly!")
    else:
        print("\n❌ TEST FAILED: Issues found with Comprehensive Report Generator")
    
    return success

if __name__ == "__main__":
    asyncio.run(main()) 