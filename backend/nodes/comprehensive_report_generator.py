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
    Agent that generates a comprehensive report from competitor analysis and trend data.
    Creates summaries for competitor news and trend analysis with company relevance.
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
        Generate comprehensive report from collected data
        """
        self.log_agent_start(state)
        company = state.get('company', 'the company')
        user_role = state.get('user_role', 'business stakeholder')
        websocket_manager, job_id = self.get_websocket_info(state)
        
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message="📊 Starting comprehensive report generation",
                result={"step": "Comprehensive Report Generation", "substep": "initialization"}
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
                message="🔍 Analyzing competitor intelligence data",
                result={"step": "Comprehensive Report Generation", "substep": "competitor_analysis"}
            )
            
            # Generate competitor news analysis
            competitor_report = await self._generate_competitor_news_analysis(
                company, user_role, competitor_discovery, competitor_analysis, competitors, profile
            )
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message="📈 Analyzing market and sector trends",
                result={"step": "Comprehensive Report Generation", "substep": "trend_analysis"}
            )
            
            # Generate trend analysis report
            trend_report = await self._generate_trend_analysis_report(
                company, user_role, sector_trends, client_trends, profile
            )
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message="📋 Generating final strategic report",
                result={"step": "Comprehensive Report Generation", "substep": "final_report"}
            )
            
            # Combine into final report
            final_report = await self._generate_final_report(
                company, user_role, competitor_report, trend_report, profile
            )
            
            # Update state with the comprehensive report
            state['report'] = final_report
            state['competitor_briefing'] = competitor_report
            
            # Add completion message to messages
            completion_msg = f"✅ Generated comprehensive strategic intelligence report for {company}"
            messages = state.get('messages', [])
            messages.append(AIMessage(content=completion_msg))
            state['messages'] = messages
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="completed",
                message=completion_msg,
                result={
                    "step": "Comprehensive Report Generation",
                    "substep": "complete",
                    "report": final_report
                }
            )
            
            self.log_agent_complete(state)
            return state
            
        except Exception as e:
            error_msg = f"❌ Error in comprehensive report generation: {str(e)}"
            self.logger.error(error_msg)
            await self.send_error_update(
                websocket_manager, job_id,
                error_msg=error_msg,
                step="Comprehensive Report Generation"
            )
            return state
    
    async def _generate_competitor_news_analysis(self, company: str, user_role: str, 
                                               competitor_discovery: Dict, competitor_analysis: Dict, 
                                               competitors: List, profile: Dict) -> str:
        """Generate competitor news analysis with summaries, value, and comparisons"""
        
        # Extract company context from profile
        company_context = ""
        if profile:
            core_products = profile.get('core_products', [])
            use_cases = profile.get('use_cases', [])
            customer_segments = profile.get('customer_segments', [])
            
            if core_products:
                company_context += f"\n{company} Core Products: {', '.join(core_products)}"
            if use_cases:
                company_context += f"\n{company} Use Cases: {', '.join(use_cases)}"
            if customer_segments:
                company_context += f"\n{company} Customer Segments: {', '.join(customer_segments)}"
        
        system_prompt = f"""
        You are an expert business analyst specializing in competitive intelligence.
        
        Your task is to analyze competitor news and developments for {company}.
        
        Company Context: {company_context}
        
        For each significant piece of competitor news or development:
        1. Create a SHORT SUMMARY (2-3 sentences max)
        2. Identify the VALUE/IMPACT for the industry
        3. Compare it to what exists at {company} or suggest implications for {company}
        
        Focus on the most INTERESTING and RELEVANT news that could impact {company}'s strategy.
        
        Structure your response as:
        ## Competitor News Analysis
        
        ### [Competitor Name]
        **News/Development:** [Brief title]
        **Summary:** [2-3 sentence summary]
        **Value/Impact:** [What this means for the industry]
        **Comparison to {company}:** [How this relates to or differs from {company}'s approach]
        
        Only include the most significant and actionable insights.
        """
        
        # Prepare comprehensive competitor data for analysis
        competitor_info = ""
        
        # Add discovered competitors
        if competitor_discovery:
            for category in ["direct", "indirect", "emerging"]:
                cat_competitors = competitor_discovery.get(category, [])
                if cat_competitors:
                    competitor_info += f"\n{category.title()} Competitors: "
                    competitor_info += ", ".join([comp.get("name", str(comp)) if isinstance(comp, dict) else str(comp) for comp in cat_competitors[:5]])
                    competitor_info += "\n"
        
        # Add basic competitor list
        if competitors:
            competitor_names = [comp.get("name", str(comp)) if isinstance(comp, dict) else str(comp) for comp in competitors[:10]]
            competitor_info += f"\nKey Competitors: {', '.join(competitor_names)}\n"
        
        # Add detailed competitor analysis data (news items, etc.)
        if competitor_analysis:
            news_items = competitor_analysis.get('news_items', [])
            if news_items:
                competitor_info += f"\nCompetitor News Analysis ({len(news_items)} items):\n"
                for item in news_items[:10]:  # Limit to top 10 news items
                    competitor_info += f"- {item.get('competitor', 'Unknown')}: {item.get('title', 'No title')} - {item.get('summary', 'No summary')[:200]}\n"
        
        if not competitor_info.strip():
            competitor_info = "No specific competitor data available for analysis."
        
        user_prompt = f"""
        Analyze the following competitor information for {company}:
        
        {competitor_info}
        
        User role context: {user_role}
        
        Generate a focused competitor news analysis following the specified format.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_trend_analysis_report(self, company: str, user_role: str,
                                            sector_trends: List, client_trends: List, profile: Dict) -> str:
        """Generate trend analysis report with descriptions, summaries, and company relevance"""
        
        # Extract company context from profile
        company_context = ""
        if profile:
            core_products = profile.get('core_products', [])
            use_cases = profile.get('use_cases', [])
            customer_segments = profile.get('customer_segments', [])
            known_clients = profile.get('known_clients', [])
            
            if core_products:
                company_context += f"\n{company} Core Products: {', '.join(core_products)}"
            if use_cases:
                company_context += f"\n{company} Use Cases: {', '.join(use_cases)}"
            if customer_segments:
                company_context += f"\n{company} Customer Segments: {', '.join(customer_segments)}"
            if known_clients:
                company_context += f"\n{company} Known Clients: {', '.join(known_clients[:5])}"
        
        system_prompt = f"""
        You are an expert market research analyst specializing in trend analysis.
        
        Your task is to analyze sector and client trends for {company}.
        
        Company Context: {company_context}
        
        For each trend:
        1. Provide a clear DESCRIPTION of the trend
        2. Create a SHORT SUMMARY of its current state and trajectory
        3. Explain HOW IT RELATES to {company} specifically given their products, use cases, and customer segments
        
        Structure your response as:
        ## Trend Analysis Report
        
        ### Sector Trends
        **Trend:** [Trend name/title]
        **Description:** [What this trend is about]
        **Summary:** [Current state and trajectory in 2-3 sentences]
        **Company Relevance:** [How this specifically impacts or relates to {company}]
        
        ### Client/Market Trends
        **Trend:** [Trend name/title]
        **Description:** [What this trend is about]
        **Summary:** [Current state and trajectory in 2-3 sentences]
        **Company Relevance:** [How this specifically impacts or relates to {company}]
        
        Focus on actionable insights and clear connections to {company}'s business.
        """
        
        # Prepare comprehensive trend data for analysis
        trend_info = ""
        
        if sector_trends:
            trend_info += "SECTOR TRENDS:\n"
            for i, trend in enumerate(sector_trends[:8], 1):  # Include more trends
                if isinstance(trend, dict):
                    trend_title = trend.get('title', trend.get('name', f'Trend {i}'))
                    trend_description = trend.get('description', trend.get('summary', str(trend)[:300]))
                    trend_info += f"{i}. {trend_title}: {trend_description}\n"
                else:
                    trend_info += f"{i}. {str(trend)[:400]}\n"
            trend_info += "\n"
        
        if client_trends:
            trend_info += "CLIENT/MARKET TRENDS:\n"
            for i, trend in enumerate(client_trends[:8], 1):  # Include more trends
                if isinstance(trend, dict):
                    trend_title = trend.get('title', trend.get('name', f'Client Trend {i}'))
                    trend_description = trend.get('description', trend.get('summary', str(trend)[:300]))
                    trend_info += f"{i}. {trend_title}: {trend_description}\n"
                else:
                    trend_info += f"{i}. {str(trend)[:400]}\n"
            trend_info += "\n"
        
        if not trend_info.strip():
            trend_info = "No specific trend data available for analysis."
        
        user_prompt = f"""
        Analyze the following trend information for {company}:
        
        {trend_info}
        
        User role context: {user_role}
        
        Generate a focused trend analysis report following the specified format.
        Focus on trends that are most relevant to {company}'s business model and customer base.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_final_report(self, company: str, user_role: str,
                                   competitor_report: str, trend_report: str, profile: Dict) -> str:
        """Generate final comprehensive report combining all analyses"""
        
        # Extract company context from profile
        company_context = ""
        if profile:
            core_products = profile.get('core_products', [])
            use_cases = profile.get('use_cases', [])
            customer_segments = profile.get('customer_segments', [])
            known_clients = profile.get('known_clients', [])
            
            company_context += f"\n{company} Business Profile:"
            if core_products:
                company_context += f"\n- Core Products: {', '.join(core_products)}"
            if use_cases:
                company_context += f"\n- Use Cases: {', '.join(use_cases)}"
            if customer_segments:
                company_context += f"\n- Customer Segments: {', '.join(customer_segments)}"
            if known_clients:
                company_context += f"\n- Notable Clients: {', '.join(known_clients[:5])}"
        
        system_prompt = f"""
        You are an executive business consultant creating a comprehensive strategic intelligence report.
        
        Combine the competitor analysis and trend analysis into a cohesive executive summary
        that provides actionable insights for {company}.
        
        Company Context: {company_context}
        
        Structure the final report as:
        # Strategic Intelligence Report for {company}
        
        ## Executive Summary
        [Key takeaways and strategic implications in 3-4 sentences that tie together competitive landscape and market trends]
        
        ## Competitive Landscape Analysis
        [Include the competitor analysis with focus on the most strategic insights]
        
        ## Market & Sector Trends Analysis
        [Include the trend analysis with emphasis on business impact]
        
        ## Strategic Recommendations
        [5-7 specific, actionable bullet points that {company} should consider based on the competitive and trend analysis]
        
        ## Key Opportunities & Risks
        [Highlight 2-3 key opportunities and 2-3 key risks identified from the analysis]
        
        Keep it executive-ready: strategic, actionable, and focused on business impact.
        """
        
        user_prompt = f"""
        Create a final comprehensive strategic intelligence report for {company} by combining these analyses:
        
        COMPETITOR ANALYSIS:
        {competitor_report}
        
        TREND ANALYSIS:
        {trend_report}
        
        User role context: {user_role}
        
        Generate an executive-ready strategic intelligence report that provides clear, actionable insights 
        for {company}'s leadership team. Focus on the most interesting and strategic findings.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content 