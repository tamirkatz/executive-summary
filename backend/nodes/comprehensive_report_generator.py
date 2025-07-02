import logging
import os
from typing import Dict, List, Any
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from ..classes.state import ResearchState
from ..agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ComprehensiveReportGenerator(BaseAgent):
    """
    Enhanced agent that generates executive-focused strategic intelligence reports.
    Emphasizes competitive landscape, market data, and cutting-edge industry trends.
    """
    
    def __init__(self):
        super().__init__(agent_type="comprehensive_report_generator")
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
    async def run(self, state: ResearchState) -> ResearchState:
        """
        Generate comprehensive executive intelligence report
        """
        self.log_agent_start(state)
        company = state.get('company', 'the company')
        user_role = state.get('user_role', 'business stakeholder')
        websocket_manager, job_id = self.get_websocket_info(state)
        
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message="📊 Starting enhanced strategic intelligence report generation",
                result={"step": "Enhanced Strategic Intelligence", "substep": "initialization"}
            )
            
            # Get all available data from state
            competitor_discovery = state.get('competitor_discovery', {})
            competitor_analysis = state.get('competitor_analysis', {})
            competitors = state.get('competitors', [])
            sector_trends = state.get('sector_trends', [])
            client_trends = state.get('client_trends', [])
            profile = state.get('profile', {})
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message="🎯 Analyzing competitive intelligence and market dynamics",
                result={"step": "Enhanced Strategic Intelligence", "substep": "competitive_analysis"}
            )
            
            # Generate enhanced strategic intelligence report
            final_report = await self._generate_enhanced_strategic_report(
                company, user_role, competitor_discovery, competitor_analysis, 
                competitors, sector_trends, client_trends, profile
            )
            
            # Update state with the comprehensive report
            state['report'] = final_report
            
            # Add completion message to messages
            completion_msg = f"✅ Generated enhanced strategic intelligence report for {company}"
            messages = state.get('messages', [])
            messages.append(AIMessage(content=completion_msg))
            state['messages'] = messages
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="completed",
                message=completion_msg,
                result={
                    "step": "Enhanced Strategic Intelligence",
                    "substep": "complete",
                    "report": final_report
                }
            )
            
            self.log_agent_complete(state)
            return state
            
        except Exception as e:
            error_msg = f"❌ Enhanced strategic intelligence generation failed: {str(e)}"
            self.logger.error(error_msg)
            await self.send_status_update(
                websocket_manager, job_id,
                status="error",
                message=error_msg,
                result={"step": "Enhanced Strategic Intelligence", "error": str(e)}
            )
            return state

    async def _generate_enhanced_strategic_report(self, company: str, user_role: str,
                                                competitor_discovery: Dict, competitor_analysis: Dict,
                                                competitors: List, sector_trends: List, 
                                                client_trends: List, profile: Dict) -> str:
        """Generate enhanced strategic intelligence report with emphasis on competitive landscape and industry data"""
        
        # Extract company context
        company_context = self._extract_company_context(profile, company)
        
        # Prepare comprehensive data
        competitive_data = self._prepare_competitive_intelligence(
            competitor_discovery, competitor_analysis, competitors
        )
        
        market_data = self._prepare_market_intelligence(sector_trends, client_trends)
        
        system_prompt = f"""
        You are an elite strategic intelligence analyst creating an executive briefing for C-suite leadership.
        Your report must be data-driven, fact-heavy, and focused on competitive dynamics and market realities.
        
        CRITICAL REQUIREMENTS:
        1. COMPETITIVE LANDSCAPE must be the PRIMARY and LONGEST section
        2. Focus on SPECIFIC competitor moves, not generic insights
        3. Include QUANTITATIVE data wherever possible (market sizes, growth rates, valuations)
        
        5. NO generic strategic recommendations - keep them minimal and data-backed
        6. Lead with FACTS and industry developments, not analysis
        
        Structure the report as:
        
        # Strategic Intelligence Report for {company}
        
        ## Company Overview
        {company_context}
        
        ## Executive Summary
        [3-4 sentences highlighting the most critical competitive developments and market dynamics affecting {company}. Focus on immediate competitive threats and market opportunities.]
        
        ## Competitive Landscape Analysis
        [THIS IS THE MAIN SECTION - 60% of the report]
        
        ### Direct Competitors - Strategic Moves
        [For each major competitor, provide:]
        - **Recent Product Launches:** [Specific products/features with dates and market impact]
        - **Funding/Valuation Updates:** [Specific amounts, dates, investors]
        - **Strategic Partnerships:** [New alliances, integrations, M&A activity]
        - **Technology Investments:** [AI capabilities, API developments, infrastructure upgrades]
        - **Market Share Data:** [When available, specific market position changes]
        
        ### Emerging Competitive Threats
        [New entrants, disruptive technologies, non-traditional competitors]
        
        ### Industry Consolidation Activity
        [M&A deals, strategic acquisitions, market concentration trends]
        
        ## Market & Technology Dynamics
        
        [Specific developments in AI-driven commerce, autonomous agents, workflow automation]
        
        ### Market Size & Growth Data
        [Specific market metrics, growth projections, segment analysis]
        
        ## Industry Intelligence Highlights
        [5-8 specific industry developments with sources and dates]
        
        ## Key Market Risks
        [2-3 specific, immediate risks with factual basis]
        
        Make it executive-ready: dense with facts, light on fluff, heavy on competitive intelligence.
        """
        
        user_prompt = f"""
        Create an enhanced strategic intelligence report for {company} using this data:
        
        COMPETITIVE INTELLIGENCE:
        {competitive_data}
        
        MARKET INTELLIGENCE:
        {market_data}
        
        User role: {user_role}
        
        Focus on:
        1. Specific competitor movements and strategic decisions
        2. Quantitative market data and industry metrics
        4. Factual industry developments over generic insights
        5. Minimal strategic recommendations - let the data speak
        
        Make this report 10x more interesting and complete for executives by focusing on:
        - Hard facts and specific competitor intelligence
        - Industry data and market metrics
        - Technological innovations and platform developments
        - Specific dates, amounts, and quantifiable developments
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content

    def _extract_company_context(self, profile: Dict, company: str) -> str:
        """Extract and format company context"""
        context_parts = [f"{company} Business Profile:"]
        
        if profile:
            if profile.get('description'):
                context_parts.append(f"- Description: {profile['description']}")
            if profile.get('core_products'):
                context_parts.append(f"- Core Products: {', '.join(profile['core_products'])}")
            if profile.get('use_cases'):
                context_parts.append(f"- Use Cases: {', '.join(profile['use_cases'])}")
            if profile.get('customer_segments'):
                context_parts.append(f"- Customer Segments: {', '.join(profile['customer_segments'])}")
            if profile.get('known_clients'):
                context_parts.append(f"- Notable Clients: {', '.join(profile['known_clients'][:5])}")
            if profile.get('industry'):
                context_parts.append(f"- Industry: {profile['industry']}")
        
        return "\n".join(context_parts)

    def _prepare_competitive_intelligence(self, competitor_discovery: Dict, 
                                        competitor_analysis: Dict, competitors: List) -> str:
        """Prepare comprehensive competitive intelligence data"""
        intel_parts = []
        
        # Discovered competitors by category
        if competitor_discovery:
            intel_parts.append("DISCOVERED COMPETITORS BY CATEGORY:")
            for category in ["direct", "indirect", "emerging"]:
                cat_competitors = competitor_discovery.get(category, [])
                if cat_competitors:
                    intel_parts.append(f"\n{category.title()} Competitors:")
                    for comp in cat_competitors[:8]:
                        if isinstance(comp, dict):
                            name = comp.get("name", "Unknown")
                            description = comp.get("description", "")
                            intel_parts.append(f"  • {name}: {description}")
                        else:
                            intel_parts.append(f"  • {comp}")
        
        # Competitor news analysis - grouped per competitor to ensure all meaningful launches are captured
        if competitor_analysis and competitor_analysis.get('news_items'):
            intel_parts.append("\n\nCOMPETITOR NEWS & DEVELOPMENTS:")
            news_items = competitor_analysis['news_items']
            
            # Build nested mapping: competitor -> category -> list[items]
            comp_map: Dict[str, Dict[str, List[dict]]] = {}
            for item in news_items:
                comp = item.get('competitor', 'Unknown') or 'Unknown'
                cat = item.get('category', 'other')
                comp_map.setdefault(comp, {}).setdefault(cat, []).append(item)
            
            # For each competitor print categories that have entries
            for comp, cat_dict in comp_map.items():
                intel_parts.append(f"\n{comp}:")
                # Define display order
                ordered_cats = [
                    'product_launch',
                    'funding',
                    'partnership',
                    'm_a',
                    'other'
                ]
                for cat in ordered_cats:
                    items = cat_dict.get(cat, [])
                    if not items:
                        continue  # Skip categories with no items (e.g., no M&A)

                    cat_title = cat.replace('_', ' ').title()
                    intel_parts.append(f"  {cat_title}:")

                    # List up to 5 items, but for product launches allow up to 10 meaningful ones
                    limit = 10 if cat == 'product_launch' else 5
                    for itm in items[:limit]:
                        title = itm.get('title', 'No title')
                        date = itm.get('date', 'Unknown date')
                        impact = itm.get('impact', '')
                        intel_parts.append(f"    • {title} ({date})")
                        if impact:
                            intel_parts.append(f"      Impact: {impact}")
        
        # Basic competitor list
        if competitors:
            intel_parts.append("\n\nADDITIONAL COMPETITORS:")
            for comp in competitors[:10]:
                if isinstance(comp, dict):
                    intel_parts.append(f"  • {comp.get('name', str(comp))}")
                else:
                    intel_parts.append(f"  • {comp}")
        
        return "\n".join(intel_parts) if intel_parts else "No specific competitive intelligence available."

    def _prepare_market_intelligence(self, sector_trends: List, client_trends: List) -> str:
        """Prepare comprehensive market intelligence data"""
        intel_parts = []
        
        if sector_trends:
            intel_parts.append("SECTOR TRENDS & MARKET DYNAMICS:")
            for i, trend in enumerate(sector_trends[:10], 1):
                if isinstance(trend, dict):
                    trend_name = trend.get('trend', trend.get('title', f'Sector Trend {i}'))
                    evidence = trend.get('evidence', '')
                    impact = trend.get('impact', '')
                    confidence = trend.get('confidence', '')
                    date = trend.get('date', '')
                    
                    intel_parts.append(f"\n{i}. {trend_name}")
                    if evidence:
                        intel_parts.append(f"   Evidence: {evidence}")
                    if impact:
                        intel_parts.append(f"   Impact: {impact}")
                    if confidence:
                        intel_parts.append(f"   Confidence: {confidence}")
                    if date:
                        intel_parts.append(f"   Date: {date}")
                else:
                    intel_parts.append(f"{i}. {str(trend)[:500]}")
        
        if client_trends:
            intel_parts.append("\n\nCLIENT/MARKET TRENDS:")
            for i, trend in enumerate(client_trends[:10], 1):
                if isinstance(trend, dict):
                    trend_name = trend.get('trend', trend.get('title', f'Client Trend {i}'))
                    evidence = trend.get('evidence', '')
                    impact = trend.get('impact', '')
                    
                    intel_parts.append(f"\n{i}. {trend_name}")
                    if evidence:
                        intel_parts.append(f"   Evidence: {evidence}")
                    if impact:
                        intel_parts.append(f"   Impact: {impact}")
                else:
                    intel_parts.append(f"{i}. {str(trend)[:500]}")
        
        return "\n".join(intel_parts) if intel_parts else "No specific market intelligence available." 