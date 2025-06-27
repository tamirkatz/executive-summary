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

class FullDataTestComprehensiveReportGenerator:
    """Test the comprehensive report generator with complete research data from WebSocket messages"""
    
    def __init__(self):
        self.report_generator = ComprehensiveReportGenerator()
    
    def create_full_test_state(self) -> ResearchState:
        """Create a test state with the complete actual data from the research workflow"""
        
        # Complete profile data from WebSocket message
        profile_data = {
            "company": "Nuvei",
            "role": "CEO",
            "description": "Nuvei is a Canadian fintech company that provides a comprehensive suite of B2B payment solutions, enabling businesses to accept various payment methods, including credit cards, bank transfers, and alternative payment options across more than 200 markets. Their primary business model is a combination of SaaS and API services, offering modular technology for transaction processing, risk management, and fraud prevention. Nuvei targets businesses in diverse sectors, including eCommerce and iGaming, by facilitating seamless payment integration and providing data-driven insights for improved operational efficiency.",
            "industry": "Financial Technology",
            "sector": "Payment Processing",
            "customer_segments": ["E-commerce", "iGaming", "Retail", "Travel", "Hospitality", "Subscription Services", "B2B Services", "Marketplaces", "Software as a Service (SaaS)", "Financial Services"],
            "known_clients": ["Shopify", "DraftKings", "888 Holdings", "Loto-Québec", "SaaS companies", "Various online retailers", "Gaming platforms", "Travel agencies", "Subscription services", "Marketplaces"],
            "partners": ["Shopify", "Magento", "WooCommerce", "Salesforce", "PayPal", "Visa", "Mastercard", "American Express", "Discover", "Various banks"],
            "use_cases": ["Payment processing", "Fraud prevention", "Risk management", "Transaction analytics", "Seamless payment integration", "Multi-currency transactions", "Alternative payment methods", "Subscription billing", "Data-driven insights", "Operational efficiency"],
            "core_products": ["Payment Gateway", "Fraud Detection Tools", "Risk Management Solutions", "Transaction Processing APIs", "Modular Payment Solutions", "Reporting and Analytics Tools", "Mobile Payment Solutions", "E-commerce Payment Solutions", "iGaming Payment Solutions", "Alternative Payment Options"],
            "synonyms": ["Payment Solutions", "Fintech Services", "Transaction Processing", "B2B Payments", "Payment Integration", "SaaS Payment Solutions", "API Payment Services", "Fraud Prevention Tools", "Risk Management Systems", "E-commerce Payments"]
        }
        
        # Complete competitor discovery data
        competitor_discovery_data = {
            "direct": [
                {
                    "name": "FIS Global",
                    "description": "FIS offers more than 500 solutions and processes over $75b of transactions around the planet. FIS is a Fortune 500® company and is a member of Standard & Poor's 500® Index. For a better understanding",
                    "type": "direct",
                    "confidence": 0.89,
                    "evidence": "FIS Global operates in the payment processing sector, offering similar financial technology solutions as Nuvei, making them direct competitors."
                },
                {
                    "name": "Square",
                    "description": "About Square That one opportunity helped grow Square from a single product to a whole suite for people to run every side of their businesses, including hardware, software, and so much more. Square Han",
                    "type": "direct",
                    "confidence": 0.87,
                    "evidence": "Square and Nuvei both operate in the payment processing sector, offering similar services for facilitating transactions."
                },
                {
                    "name": "Stripe",
                    "description": "Stripe, Inc. Stripe, Inc. In May that year, Stripe introduced Payment Links, a no-code product allowing businesses to create a link to a checkout page and begin accepting payments on social platforms",
                    "type": "direct",
                    "confidence": 0.89,
                    "evidence": "Both Stripe and Nuvei operate in the payment processing sector, offering similar services such as payment gateway solutions and merchant services."
                },
                {
                    "name": "Adyen",
                    "description": "Adyen - Wikipedia **Adyen** is a Dutch payment company with the status of an acquiring bank that allows businesses to accept e-commerce, mobile, and point-of-sale payments. Adyen offers merchants onli",
                    "type": "direct",
                    "confidence": 0.9,
                    "evidence": "Adyen and Nuvei both operate in the payment processing sector, offering similar services such as payment gateway solutions, making them direct competitors."
                },
                {
                    "name": "Flutterwave",
                    "description": "Flutterwave, a San Francisco-based payments technology company with operations in Africa, today announced that it has closed a $35m Series B. By Tommy Williams Former Contributor Jan 13, 2020",
                    "type": "direct",
                    "confidence": 0.89,
                    "evidence": "Both Flutterwave and Nuvei operate in the payment processing industry, offering similar services such as payment solutions for businesses, making them direct competitors."
                }
            ],
            "indirect": [],
            "emerging": [
                {
                    "name": "FamPay",
                    "description": "FamPay has 5 employees across 3 locations and $42.7 m in total funding,. See insights on FamPay including office locations, competitors, revenue, financials, executives, subsidiaries and more at Craft",
                    "type": "emerging",
                    "confidence": 0.72,
                    "evidence": "FamPay is an emerging competitor to Nuvei as it targets the digital payment sector, focusing on a younger demographic with innovative payment solutions, which could influence future market dynamics."
                }
            ]
        }
        
        # Complete competitor analysis data from WebSocket
        competitor_analysis_data = {
            "news_items": [
                {
                    "competitor": "FIS Global",
                    "title": "Global Payments shares plunge 17% after company announces $24 billion Worldpay deal",
                    "category": "m_a",
                    "summary": "FIS Global announced a $24.25 billion deal to sell Worldpay to Global Payments. This transaction involves a three-way reshuffling of assets where Global Payments will sell its issuer solutions unit to FIS for $13.5 billion while acquiring Worldpay from FIS and GTCR.",
                    "impact": "This deal allows FIS to focus on its core business of serving financial institutions with issuer and banking infrastructure, streamlining its operations and enhancing its position as a leading fintech provider.",
                    "date": "2025-04-17",
                    "source": "CNBC",
                    "confidence": 0.9
                },
                {
                    "competitor": "FIS Global",
                    "title": "How FIS CEO Stephanie Ferris Led A $24 Billion Fintech Deal",
                    "category": "m_a",
                    "summary": "FIS Global's CEO Stephanie Ferris orchestrated a $24.25 billion deal to sell Worldpay to Global Payments, marking a significant fintech transaction. The deal involves FIS acquiring Global Payments' Issuer Solutions business for $13.5 billion.",
                    "impact": "The transaction is strategically significant as it allows FIS to streamline its business and focus on its core competencies, enhancing its global reach and specialization in financial services technology.",
                    "date": "2025-05-09",
                    "source": "Forbes",
                    "confidence": 0.9
                },
                {
                    "competitor": "Stripe",
                    "title": "Stripe's valuation climbs to $91.5 billion in secondary stock offer",
                    "category": "funding",
                    "summary": "Stripe's valuation increased to $91.5 billion through a secondary stock sale, nearing its previous peak valuation of $95 billion. The company reported a total payment volume of $1.4 trillion in 2024, marking a 38% increase from the previous year.",
                    "impact": "The valuation boost and significant increase in payment volume highlight Stripe's strong market position and growth trajectory, potentially enhancing its attractiveness to investors and partners.",
                    "date": "2025-02-27",
                    "source": "CNBC",
                    "confidence": 0.9
                },
                {
                    "competitor": "Stripe",
                    "title": "Stripe closes $1.1 billion Bridge deal, prepares for aggressive stablecoin push",
                    "category": "m_a",
                    "summary": "Stripe completed a $1.1 billion acquisition of Bridge, a stablecoin platform, marking its largest acquisition to date. This move is part of Stripe's strategy to expand its capabilities in stablecoin payments.",
                    "impact": "The acquisition positions Stripe to capitalize on the growing stablecoin market, potentially increasing its competitive edge in the fintech sector.",
                    "date": "2025-02-04",
                    "source": "CNBC",
                    "confidence": 0.9
                },
                {
                    "competitor": "Stripe",
                    "title": "Stripe Says Stablecoins Payments Made in More Than 70 Countries After Relaunch",
                    "category": "product_launch",
                    "summary": "Stripe relaunched its stablecoin payment services, now available in over 70 countries, after previously ending the service in 2018.",
                    "impact": "This relaunch signifies Stripe's strategic move to re-enter the crypto payments market, potentially expanding its global reach and service offerings.",
                    "date": "2024-10-10",
                    "source": "Bloomberg",
                    "confidence": 0.85
                },
                {
                    "competitor": "Stripe",
                    "title": "Klarna scores global payment deal with Stripe to expand reach ahead of blockbuster U.S. IPO",
                    "category": "partnership",
                    "summary": "Klarna entered a major distribution partnership with Stripe, allowing it to offer buy now, pay later plans to merchants using Stripe's payment tools in 26 countries.",
                    "impact": "This partnership enhances Stripe's service offerings and market reach, while supporting Klarna's expansion efforts ahead of its IPO.",
                    "date": "2025-01-14",
                    "source": "CNBC",
                    "confidence": 0.9
                },
                {
                    "competitor": "Adyen",
                    "title": "Klarna partners with fellow fintech Adyen to bring buy now, pay later into physical stores",
                    "category": "partnership",
                    "summary": "Klarna will be included as an option across more than 450,000 Adyen payment terminals in brick-and-mortar locations. The partnership will initially launch in Europe, North America, and Australia with a wider rollout planned later.",
                    "impact": "This partnership enhances Adyen's in-store payment offerings and expands its reach in the BNPL market, potentially increasing its market share and customer base.",
                    "date": "2024-09-26",
                    "source": "CNBC",
                    "confidence": 0.9
                }
            ],
            "analysis_date": "2025-06-27T11:55:56.965806",
            "competitors_analyzed": 6,
            "total_news_items": 21
        }
        
        # Complete sector trends data
        sector_trends_data = [
            {
                "trend": "Global cashless payment volumes are set to increase by more than 80% from 2020 to 2025.",
                "evidence": "https://www.pwc.com/gx/en/financial-services/fs-2025/pwc-future-of-payments.pdf",
                "impact": "This trend highlights the growing importance of digital payment solutions, presenting opportunities for SaaS/AI builders to innovate in payment processing technologies and enhance digital transaction security.",
                "date": "2023-10",
                "source_domain": "www.pwc.com",
                "confidence_score": 0.9
            },
            {
                "trend": "Increased focus on fraud mitigation and risk management in payment services.",
                "evidence": "https://www.mckinsey.com/capabilities/risk-and-resilience/our-insights/the-future-of-the-payments-industry-how-managing-risk-can-drive-growth",
                "impact": "SaaS/AI builders can leverage this trend by developing advanced fraud detection and risk management solutions, ensuring compliance and enhancing the security of payment systems.",
                "date": "2023-10",
                "source_domain": "www.mckinsey.com",
                "confidence_score": 0.9
            },
            {
                "trend": "Payments industry must focus on personalizing product design and insights delivered.",
                "evidence": "https://www.deloitte.com/us/en/Industries/financial-services/articles/infocus-payments-trends.html",
                "impact": "This trend suggests a strategic opportunity for SaaS/AI builders to create personalized payment solutions that cater to individual consumer preferences, enhancing user experience and customer loyalty.",
                "date": "2023-10",
                "source_domain": "www.deloitte.com",
                "confidence_score": 0.88
            },
            {
                "trend": "Emergence of real-time cross-border payment networks in Southeast Asia.",
                "evidence": "https://www.pwc.com/sg/en/financial-services/fintech/payments-2025-and-beyond.html",
                "impact": "This presents a significant opportunity for SaaS/AI companies to develop platforms that facilitate seamless cross-border transactions, tapping into the rapidly growing Southeast Asian market.",
                "date": "2023-10",
                "source_domain": "www.pwc.com",
                "confidence_score": 0.87
            },
            {
                "trend": "Alternative payment rails will flourish outside the US.",
                "evidence": "https://www.forrester.com/report/predictions-2025-payments/RES181544",
                "impact": "SaaS/AI companies can capitalize on this trend by developing solutions that integrate with these alternative payment systems, expanding their market reach and offering more diverse payment options.",
                "date": "2023-10",
                "source_domain": "www.forrester.com",
                "confidence_score": 0.85
            }
        ]
        
        # Complete client trends data
        client_trends_data = [
            {
                "trend": "AI-driven automation is reshaping retail business models and value chains.",
                "evidence": "https://www.mckinsey.com/industries/retail/our-insights/automation-in-retail-an-executive-overview-for-getting-ready",
                "impact": "[Retail] This trend is crucial for Nuvei as it could lead to increased demand for seamless payment solutions integrated with AI-driven retail systems. | Business Impact: Nuvei can capitalize on this trend by developing advanced payment solutions that integrate with AI-driven retail systems, offering enhanced customer experiences and operational efficiencies.",
                "date": "2025-06",
                "source_domain": "www.mckinsey.com",
                "confidence_score": 0.9
            },
            {
                "trend": "AI is becoming the cornerstone of consumer markets, transitioning from isolated deployments.",
                "evidence": "https://www.pwc.com/gx/en/industries/consumer-markets.html",
                "impact": "[Retail] AI's integration into consumer markets can drive demand for advanced payment solutions that leverage AI for fraud detection and personalized customer experiences. | Business Impact: Nuvei can invest in AI technologies to enhance its payment solutions, offering clients improved security and personalized services.",
                "date": "2025-06",
                "source_domain": "www.pwc.com",
                "confidence_score": 0.9
            },
            {
                "trend": "Subscription models are transforming e-commerce and retail sectors.",
                "evidence": "https://www.mckinsey.com/capabilities/growth-marketing-and-sales/our-insights/sign-up-now-creating-consumer-and-business-value-with-subscriptions",
                "impact": "[eCommerce] This trend opens new revenue streams for Nuvei by facilitating recurring payment solutions for subscription-based services. | Business Impact: Nuvei can enhance its payment processing services to support subscription models, providing clients with reliable and efficient recurring billing solutions.",
                "date": "2025-06",
                "source_domain": "www.mckinsey.com",
                "confidence_score": 0.85
            },
            {
                "trend": "Cryptocurrency adoption is increasing in e-commerce.",
                "evidence": "https://venturebeat.com/virtual/why-this-winter-wont-stop-the-growing-crypto-e-commerce-adoption/",
                "impact": "[eCommerce] As more e-commerce platforms adopt cryptocurrency, Nuvei can expand its payment processing capabilities to include crypto transactions, attracting a broader client base. | Business Impact: Nuvei should consider integrating cryptocurrency payment options to stay competitive and meet the evolving needs of e-commerce clients.",
                "date": "2025-06",
                "source_domain": "venturebeat.com",
                "confidence_score": 0.8
            }
        ]
        
        # Create the state with all competitors
        competitors_list = [comp for comp in competitor_discovery_data['direct'] + competitor_discovery_data['emerging']]
        
        # Create the state
        state = ResearchState()
        state.update({
            'company': 'Nuvei',
            'user_role': 'CEO',
            'profile': profile_data,
            'competitor_discovery': competitor_discovery_data,
            'competitor_analysis': competitor_analysis_data,
            'competitors': competitors_list,
            'sector_trends': sector_trends_data,
            'client_trends': client_trends_data,
            'messages': []
        })
        
        return state
    
    async def test_and_display_full_report(self):
        """Test and display the complete comprehensive report"""
        logger.info("🧪 Testing Comprehensive Report Generator with FULL DATA")
        
        # Create test state with complete real data
        test_state = self.create_full_test_state()
        
        logger.info(f"📊 Complete test state prepared with:")
        logger.info(f"  - Company: {test_state.get('company')}")
        logger.info(f"  - Profile segments: {len(test_state.get('profile', {}).get('customer_segments', []))}")
        logger.info(f"  - Known clients: {len(test_state.get('profile', {}).get('known_clients', []))}")
        logger.info(f"  - Partners: {len(test_state.get('profile', {}).get('partners', []))}")
        logger.info(f"  - Core products: {len(test_state.get('profile', {}).get('core_products', []))}")
        logger.info(f"  - Direct competitors: {len(test_state.get('competitor_discovery', {}).get('direct', []))}")
        logger.info(f"  - Emerging competitors: {len(test_state.get('competitor_discovery', {}).get('emerging', []))}")
        logger.info(f"  - Competitor news items: {len(test_state.get('competitor_analysis', {}).get('news_items', []))}")
        logger.info(f"  - Sector trends: {len(test_state.get('sector_trends', []))}")
        logger.info(f"  - Client trends: {len(test_state.get('client_trends', []))}")
        
        try:
            # Run the comprehensive report generator
            logger.info("🚀 Running comprehensive report generator with full data...")
            result_state = await self.report_generator.run(test_state)
            
            # Check if report was generated
            report = result_state.get('report')
            if report:
                logger.info(f"✅ Full report generated successfully!")
                logger.info(f"📄 Report length: {len(report)} characters")
                
                # Save to file for better viewing
                with open('generated_comprehensive_report.md', 'w', encoding='utf-8') as f:
                    f.write(report)
                logger.info("💾 Report saved to 'generated_comprehensive_report.md'")
                
                # Print the complete report with proper formatting
                print("\n" + "="*100)
                print("COMPLETE COMPREHENSIVE STRATEGIC INTELLIGENCE REPORT FOR NUVEI")
                print("="*100)
                print(report)
                print("="*100)
                
                # Analyze report structure
                sections = [line for line in report.split('\n') if line.startswith('#')]
                logger.info(f"📋 Report structure ({len(sections)} sections):")
                for section in sections:
                    logger.info(f"  • {section}")
                
                return True, report
            else:
                logger.error("❌ No report found in result state")
                logger.error(f"Available state keys: {list(result_state.keys())}")
                return False, None
                
        except Exception as e:
            logger.error(f"❌ Error during comprehensive report generation: {e}")
            import traceback
            traceback.print_exc()
            return False, None

async def main():
    """Main test function"""
    tester = FullDataTestComprehensiveReportGenerator()
    
    logger.info("🔬 Starting COMPLETE Comprehensive Report Generator Test")
    success, report = await tester.test_and_display_full_report()
    
    if success:
        print(f"\n🎯 TEST PASSED: Complete Comprehensive Report Generated Successfully!")
        print(f"📊 Report contains {len(report)} characters")
        print(f"💾 Full report saved to 'generated_comprehensive_report.md'")
    else:
        print("\n❌ TEST FAILED: Issues found with Comprehensive Report Generator")
    
    return success

if __name__ == "__main__":
    asyncio.run(main()) 