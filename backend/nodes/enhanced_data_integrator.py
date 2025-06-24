import logging
from typing import Dict, Any
from datetime import datetime

from langchain_core.messages import AIMessage

from ..classes import ResearchState
from ..agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class EnhancedDataIntegrator(BaseAgent):
    """
    Integrates data from enhanced pre-research agents into standard workflow fields
    so the existing workflow nodes can process the enhanced data properly.
    """
    
    def __init__(self):
        super().__init__(agent_type="enhanced_data_integrator")
    
    async def run(self, state: ResearchState) -> Dict[str, Any]:
        """Main execution method for the Enhanced Data Integrator."""
        self.log_agent_start(state)
        company = state.get('company', 'Unknown Company')
        websocket_manager, job_id = self.get_websocket_info(state)
        
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🔗 Integrating enhanced research data for {company}",
                result={
                    "step": "Enhanced Data Integrator",
                    "company": company,
                    "phase": "data_integration"
                }
            )
            
            # Get enhanced data from the three agents
            company_factual_data = state.get('company_factual_data', {})
            industry_intelligence = state.get('industry_intelligence', {})
            enhanced_competitor_data = state.get('enhanced_competitor_data', {})
            
            # Transform and populate standard workflow fields
            await self._integrate_company_data(state, company_factual_data, websocket_manager, job_id)
            await self._integrate_financial_data(state, company_factual_data, websocket_manager, job_id)
            await self._integrate_competitor_data(state, enhanced_competitor_data, websocket_manager, job_id)
            await self._integrate_market_data(state, industry_intelligence, websocket_manager, job_id)
            
            # Mark research as complete so the workflow can proceed
            state['query_collection_complete'] = True
            state['categorized_queries'] = self._create_summary_queries(state)
            state['total_queries'] = len(state['categorized_queries'].get('summary', []))
            
            # Create curated data summaries
            await self._create_curated_summaries(state, websocket_manager, job_id)
            
            # Add completion message
            completion_msg = f"✅ Enhanced data integration complete for {company}. Populated standard workflow fields from enhanced research."
            
            messages = state.get('messages', [])
            messages.append(AIMessage(content=completion_msg))
            state['messages'] = messages
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="completed",
                message=completion_msg,
                result={
                    "step": "Enhanced Data Integrator",
                    "company": company,
                    "integrated_fields": [
                        "company_data", "financial_data", "competitor_data",
                        "curated_company_data", "curated_financial_data", "curated_competitor_data"
                    ]
                }
            )
            
            return state
            
        except Exception as e:
            error_msg = f"Error in Enhanced Data Integrator: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await self.send_error_update(
                websocket_manager, job_id, error_msg, "Enhanced Data Integrator"
            )
            return state
    
    async def _integrate_company_data(self, state: ResearchState, company_factual_data: Dict[str, Any], 
                                    websocket_manager=None, job_id=None):
        """Integrate company factual data into standard company_data field."""
        try:
            company_url = state.get('company_url', '')
            company = state.get('company', 'Unknown Company')
            
            # Create standard company_data structure from enhanced data
            company_data = {}
            
            if company_url:
                # Use website analysis data if available
                website_analysis = company_factual_data.get('website_analysis', {})
                company_data[company_url] = {
                    "content": self._format_company_content(website_analysis, company_factual_data),
                    "title": f"{company} - Company Overview",
                    "url": company_url,
                    "source": "enhanced_website_analysis"
                }
            
            # Add additional company intelligence
            intelligence_summary = company_factual_data.get('intelligence_summary', {})
            if intelligence_summary:
                company_data[f"enhanced_intelligence_{company}"] = {
                    "content": self._format_intelligence_content(intelligence_summary),
                    "title": f"{company} - Enhanced Intelligence",
                    "url": f"enhanced://company_research/{company}",
                    "source": "enhanced_company_research"
                }
            
            state['company_data'] = company_data
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"📊 Integrated company data: {len(company_data)} sources"
            )
            
        except Exception as e:
            logger.error(f"Error integrating company data: {e}")
    
    async def _integrate_financial_data(self, state: ResearchState, company_factual_data: Dict[str, Any],
                                      websocket_manager=None, job_id=None):
        """Integrate financial data from enhanced research."""
        try:
            company = state.get('company', 'Unknown Company')
            
            # Extract financial information from enhanced data
            financial_info = company_factual_data.get('financial_data', {})
            organizational_data = company_factual_data.get('organizational_structure', {})
            
            financial_data = {}
            
            if financial_info or organizational_data:
                financial_data[f"enhanced_financial_{company}"] = {
                    "content": self._format_financial_content(financial_info, organizational_data),
                    "title": f"{company} - Financial & Organizational Data",
                    "url": f"enhanced://financial_research/{company}",
                    "source": "enhanced_financial_research"
                }
            
            state['financial_data'] = financial_data
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"💰 Integrated financial data: {len(financial_data)} sources"
            )
            
        except Exception as e:
            logger.error(f"Error integrating financial data: {e}")
    
    async def _integrate_competitor_data(self, state: ResearchState, enhanced_competitor_data: Dict[str, Any],
                                       websocket_manager=None, job_id=None):
        """Integrate competitor data from enhanced research."""
        try:
            company = state.get('company', 'Unknown Company')
            
            # Extract competitor information
            competitor_profiles = enhanced_competitor_data.get('comprehensive_profiles', {})
            tech_comparisons = enhanced_competitor_data.get('technology_comparisons', {})
            strategic_movements = enhanced_competitor_data.get('strategic_movements', {})
            
            competitor_data = {}
            
            if competitor_profiles:
                competitor_data[f"enhanced_competitors_{company}"] = {
                    "content": self._format_competitor_content(
                        competitor_profiles, tech_comparisons, strategic_movements
                    ),
                    "title": f"{company} - Competitive Intelligence",
                    "url": f"enhanced://competitor_research/{company}",
                    "source": "enhanced_competitor_research"
                }
            
            state['competitor_data'] = competitor_data
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing", 
                message=f"🥊 Integrated competitor data: {len(competitor_profiles)} competitor profiles"
            )
            
        except Exception as e:
            logger.error(f"Error integrating competitor data: {e}")
    
    async def _integrate_market_data(self, state: ResearchState, industry_intelligence: Dict[str, Any],
                                   websocket_manager=None, job_id=None):
        """Integrate market/industry data as news_data."""
        try:
            company = state.get('company', 'Unknown Company')
            
            # Use industry intelligence as market news/trends
            market_analysis = industry_intelligence.get('market_analysis', {})
            tech_landscape = industry_intelligence.get('technology_landscape', {})
            competitive_landscape = industry_intelligence.get('competitive_landscape', {})
            
            news_data = {}
            
            if market_analysis or tech_landscape or competitive_landscape:
                news_data[f"enhanced_market_intelligence_{company}"] = {
                    "content": self._format_market_content(
                        market_analysis, tech_landscape, competitive_landscape
                    ),
                    "title": f"{company} - Market & Industry Intelligence",
                    "url": f"enhanced://industry_research/{company}",
                    "source": "enhanced_industry_research"
                }
            
            state['news_data'] = news_data
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"📈 Integrated market intelligence data"
            )
            
        except Exception as e:
            logger.error(f"Error integrating market data: {e}")
    
    def _create_summary_queries(self, state: ResearchState) -> Dict[str, Any]:
        """Create summary queries for the collector to process."""
        company = state.get('company', 'Unknown Company')
        
        return {
            'summary': [
                f"Enhanced research summary for {company}",
                f"Comprehensive analysis of {company} from enhanced pre-research",
                f"Strategic intelligence overview for {company}"
            ],
            'company': [f"Enhanced company analysis for {company}"],
            'financial': [f"Enhanced financial data for {company}"],
            'competitor': [f"Enhanced competitive intelligence for {company}"],
            'market': [f"Enhanced market intelligence for {company}"]
        }
    
    async def _create_curated_summaries(self, state: ResearchState, websocket_manager=None, job_id=None):
        """Create curated data summaries from integrated data."""
        try:
            # Create curated summaries from the integrated data
            state['curated_company_data'] = state.get('company_data', {})
            state['curated_financial_data'] = state.get('financial_data', {})
            state['curated_competitor_data'] = state.get('competitor_data', {})
            state['curated_news_data'] = state.get('news_data', {})
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message="📋 Created curated data summaries from enhanced research"
            )
            
        except Exception as e:
            logger.error(f"Error creating curated summaries: {e}")
    
    def _format_company_content(self, website_analysis: Dict[str, Any], 
                              company_factual_data: Dict[str, Any]) -> str:
        """Format company content from enhanced data."""
        content_parts = []
        
        # Add main products and business model
        main_products = website_analysis.get('main_products', [])
        if main_products:
            content_parts.append(f"Main Products: {', '.join(main_products)}")
        
        business_model = website_analysis.get('business_model', '')
        if business_model:
            content_parts.append(f"Business Model: {business_model}")
        
        # Add technology stack
        tech_stack = company_factual_data.get('technology_stack', {})
        technologies = tech_stack.get('technologies', [])
        if technologies:
            content_parts.append(f"Technology Stack: {', '.join(technologies)}")
        
        # Add customer information
        customer_segments = company_factual_data.get('customer_segments', {})
        key_customers = customer_segments.get('key_customers', [])
        if key_customers:
            content_parts.append(f"Key Customers: {', '.join(key_customers)}")
        
        return "\n\n".join(content_parts) if content_parts else "Enhanced company research completed."
    
    def _format_intelligence_content(self, intelligence_summary: Dict[str, Any]) -> str:
        """Format intelligence summary content."""
        content_parts = []
        
        reliability_score = intelligence_summary.get('reliability_score', 0)
        content_parts.append(f"Data Reliability Score: {reliability_score:.2f}")
        
        data_sources = intelligence_summary.get('data_sources', [])
        if data_sources:
            content_parts.append(f"Research Sources: {len(data_sources)} verified sources")
        
        last_updated = intelligence_summary.get('last_updated', '')
        if last_updated:
            content_parts.append(f"Last Updated: {last_updated}")
        
        return "\n\n".join(content_parts) if content_parts else "Enhanced intelligence analysis completed."
    
    def _format_financial_content(self, financial_info: Dict[str, Any], 
                                organizational_data: Dict[str, Any]) -> str:
        """Format financial content from enhanced data."""
        content_parts = []
        
        # Add organizational insights
        hiring_trends = organizational_data.get('hiring_trends', [])
        if hiring_trends:
            content_parts.append(f"Recent Hiring Trends: {', '.join(hiring_trends)}")
        
        team_size = organizational_data.get('team_size', '')
        if team_size:
            content_parts.append(f"Team Size: {team_size}")
        
        geographic_presence = organizational_data.get('geographic_presence', [])
        if geographic_presence:
            content_parts.append(f"Geographic Presence: {', '.join(geographic_presence)}")
        
        return "\n\n".join(content_parts) if content_parts else "Enhanced financial research completed."
    
    def _format_competitor_content(self, competitor_profiles: Dict[str, Any],
                                 tech_comparisons: Dict[str, Any], 
                                 strategic_movements: Dict[str, Any]) -> str:
        """Format competitor content from enhanced data."""
        content_parts = []
        
        # Add competitor profiles
        if competitor_profiles:
            content_parts.append(f"Analyzed Competitors: {len(competitor_profiles)} comprehensive profiles")
            competitor_names = list(competitor_profiles.keys())[:5]  # Show first 5
            if competitor_names:
                content_parts.append(f"Key Competitors: {', '.join(competitor_names)}")
        
        # Add technology comparisons
        tech_stacks = tech_comparisons.get('technology_stacks', {})
        if tech_stacks:
            content_parts.append(f"Technology Stack Analysis: {len(tech_stacks)} competitors analyzed")
        
        # Add strategic movements
        recent_funding = strategic_movements.get('recent_funding', {})
        if recent_funding:
            content_parts.append(f"Recent Competitive Funding: {len(recent_funding)} funding events tracked")
        
        return "\n\n".join(content_parts) if content_parts else "Enhanced competitive intelligence completed."
    
    def _format_market_content(self, market_analysis: Dict[str, Any],
                             tech_landscape: Dict[str, Any],
                             competitive_landscape: Dict[str, Any]) -> str:
        """Format market/industry content from enhanced data."""
        content_parts = []
        
        # Add market analysis
        market_size = market_analysis.get('market_size', {})
        if market_size:
            content_parts.append("Market Size Analysis: Comprehensive market sizing completed")
        
        growth_trends = market_analysis.get('growth_trends', [])
        if growth_trends:
            content_parts.append(f"Growth Trends: {len(growth_trends)} trends identified")
        
        # Add technology landscape
        emerging_tech = tech_landscape.get('emerging_technologies', [])
        if emerging_tech:
            content_parts.append(f"Emerging Technologies: {len(emerging_tech)} technologies tracked")
        
        # Add competitive landscape
        market_leaders = competitive_landscape.get('market_leaders', [])
        if market_leaders:
            content_parts.append(f"Market Leaders: {', '.join(market_leaders[:5])}")
        
        return "\n\n".join(content_parts) if content_parts else "Enhanced market intelligence completed."