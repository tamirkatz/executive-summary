import logging
import os
from typing import Any, Dict, List
from datetime import datetime

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from ..classes import ResearchState
from ..config import config

logger = logging.getLogger(__name__)

class ExecutiveReportComposer:
    """Composes executive-style reports from synthesized insights."""
    
    def __init__(self) -> None:
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.2,
            api_key=config.OPENAI_API_KEY
        )
        
        # Executive report sections based on user role and content
        self.section_templates = {
            "executive_summary": {
                "title": "🧠 Executive Summary (1-minute read)",
                "description": "Top 3 takeaways, recommended actions, and business relevance",
                "tags": ["strategic_impact", "executive_decision", "business_relevance"]
            },
            "company_performance": {
                "title": "📊 Company Performance & Signals",
                "description": "Product/engineering highlights, customer trends, hiring & talent, investor/board mentions",
                "tags": ["product_launch", "customer_trend", "hiring", "investor_mention", "performance"]
            },
            "market_trends": {
                "title": "🌍 Market & Industry Trends",
                "description": "Emerging technologies, shifts in buyer behavior, macro trends",
                "tags": ["trend", "market_signal", "regulatory_change", "technology", "buyer_behavior"]
            },
            "competitor_moves": {
                "title": "🔥 Competitor & Adjacent Player Moves",
                "description": "Competitor launches/pivots, partnerships/M&A, funding announcements, hiring trends",
                "tags": ["strategic_move", "competitive_advantage", "partnership", "funding", "acquisition"]
            },
            "opportunities_threats": {
                "title": "🕵️‍♂️ Emerging Opportunities & Threats",
                "description": "High-potential partnerships, new GTM angles, market saturation signals, customer complaints",
                "tags": ["opportunity", "threat", "partnership", "market_saturation", "customer_feedback"]
            },
            "strategic_recommendations": {
                "title": "📌 Strategic Recommendations",
                "description": "3-5 AI-synthesized strategic suggestions with specific actions",
                "tags": ["strategic_move", "opportunity", "financial_impact", "recommendation"]
            },
            "appendix": {
                "title": "🧾 Appendix",
                "description": "Sources, links, long-form insights, graphs, screenshots",
                "tags": ["source", "link", "detailed_insight"]
            }
        }

    async def run(self, state: ResearchState) -> ResearchState:
        """Run the executive report composition process."""
        try:
            return await self.compose_executive_report(state)
        except Exception as e:
            logger.error(f"Error in executive report composition: {e}")
            # Create a fallback report on error
            state['report'] = f"Executive Report Generation Error: {str(e)}"
            return state

    async def compose_executive_report(self, state: ResearchState) -> ResearchState:
        """Main method to compose the executive report from synthesized insights."""
        company = state.get('company', 'Unknown Company')
        user_role = state.get('user_role', 'Executive')
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')

        if websocket_manager and job_id:
            await websocket_manager.send_status_update(
                job_id=job_id,
                status="processing",
                message=f"Composing executive report for {company}",
                result={
                    "step": "Executive Report Composer",
                    "substep": "initialization"
                }
            )

        msg = [f"📋 Composing executive report for {company}:"]

        # Get synthesized insights
        strategic_insights = state.get('strategic_insights', {})
        if not strategic_insights or not strategic_insights.get('prioritized_insights'):
            msg.append("\n⚠️ No synthesized insights available - creating basic report")
            basic_report = await self.create_basic_report(state)
            state['report'] = basic_report
            messages = state.get('messages', [])
            messages.append(AIMessage(content="\n".join(msg)))
            state['messages'] = messages
            return state

        insights = strategic_insights.get('prioritized_insights', [])
        executive_summary = strategic_insights.get('executive_summary', '')
        
        msg.append(f"\n• Processing {len(insights)} strategic insights")
        msg.append(f"• Executive summary available: {'Yes' if executive_summary else 'No'}")

        if websocket_manager and job_id:
            await websocket_manager.send_status_update(
                job_id=job_id,
                status="organizing",
                message="Organizing insights into report sections",
                result={
                    "step": "Executive Report Composer",
                    "total_insights": len(insights)
                }
            )

        # Organize insights into sections
        organized_sections = await self.organize_insights_into_sections(insights, user_role)
        msg.append(f"• Organized into {len(organized_sections)} sections")

        # Generate the executive report
        if websocket_manager and job_id:
            await websocket_manager.send_status_update(
                job_id=job_id,
                status="composing",
                message="Composing final executive report",
                result={
                    "step": "Executive Report Composer",
                    "sections": len(organized_sections)
                }
            )

        final_report = await self.generate_executive_report(
            company, user_role, executive_summary, organized_sections, state
        )
        
        if final_report:
            state['report'] = final_report
            msg.append(f"✅ Executive report completed ({len(final_report)} characters)")
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="report_complete",
                    message="Executive report completed successfully",
                    result={
                        "step": "Executive Report Composer",
                        "report_length": len(final_report),
                        "company": company,
                        "is_final": True,
                        "status": "completed"
                    }
                )
        else:
            msg.append("❌ Failed to generate executive report")

        # Update messages
        messages = state.get('messages', [])
        messages.append(AIMessage(content="\n".join(msg)))
        state['messages'] = messages
        
        return state

    async def organize_insights_into_sections(self, insights: List[Dict[str, Any]], 
                                           user_role: str) -> Dict[str, List[Dict[str, Any]]]:
        """Organize insights into report sections based on tags and relevance."""
        sections = {}
        
        # Group insights by their tags
        for insight in insights:
            tags = insight.get('tags', [])
            category = insight.get('category', 'unknown')
            
            # Determine best section for this insight
            best_section = self.determine_best_section(tags, category, user_role)
            
            if best_section not in sections:
                sections[best_section] = []
            sections[best_section].append(insight)

        # Sort insights within each section by relevance score
        for section_key, section_insights in sections.items():
            sections[section_key] = sorted(
                section_insights, 
                key=lambda x: x.get('relevance_score', 0), 
                reverse=True
            )

        return sections

    def determine_best_section(self, tags: List[str], category: str, user_role: str) -> str:
        """Determine the best section for an insight based on its tags and context."""
        # Priority mapping for different tags
        tag_section_map = {
            # Executive Summary
            'strategic_impact': 'executive_summary',
            'executive_decision': 'executive_summary',
            'business_relevance': 'executive_summary',
            
            # Company Performance
            'product_launch': 'company_performance',
            'customer_trend': 'company_performance',
            'hiring': 'company_performance',
            'investor_mention': 'company_performance',
            'performance': 'company_performance',
            
            # Market Trends
            'trend': 'market_trends',
            'market_signal': 'market_trends',
            'regulatory_change': 'market_trends',
            'technology': 'market_trends',
            'buyer_behavior': 'market_trends',
            
            # Competitor Moves
            'strategic_move': 'competitor_moves',
            'competitive_advantage': 'competitor_moves',
            'partnership': 'competitor_moves',
            'funding': 'competitor_moves',
            'acquisition': 'competitor_moves',
            
            # Opportunities & Threats
            'opportunity': 'opportunities_threats',
            'threat': 'opportunities_threats',
            'market_saturation': 'opportunities_threats',
            'customer_feedback': 'opportunities_threats',
            
            # Strategic Recommendations
            'financial_impact': 'strategic_recommendations',
            'recommendation': 'strategic_recommendations',
            
            # Appendix
            'source': 'appendix',
            'link': 'appendix',
            'detailed_insight': 'appendix'
        }
        
        # Check tags for best match
        for tag in tags:
            if tag in tag_section_map:
                return tag_section_map[tag]
        
        # Fallback based on category
        if category == 'news':
            return 'market_trends'
        elif category == 'financial':
            return 'strategic_recommendations'
        elif category == 'product':
            return 'company_performance'
        elif category == 'competitor':
            return 'competitor_moves'
        else:
            return 'strategic_recommendations'  # Default section

    async def generate_executive_report(self, company: str, user_role: str, 
                                      executive_summary: str, sections: Dict[str, List[Dict[str, Any]]], 
                                      state: ResearchState) -> str:
        """Generate the final executive report."""
        
        # Prepare sections content
        sections_content = []
        for section_key, insights in sections.items():
            if insights:  # Only include sections with content
                section_info = self.section_templates.get(section_key, {
                    "title": section_key.replace('_', ' ').title(),
                    "description": ""
                })
                
                sections_content.append({
                    "key": section_key,
                    "title": section_info["title"],
                    "insights": insights[:5]  # Limit to top 5 insights per section for readability
                })

        # Get additional context from state
        company_context = self.extract_company_context(state)
        
        # Create the executive report prompt
        prompt = f"""
You are an expert executive report writer creating a strategic briefing for a {user_role} at {company}.

CONTEXT:
{company_context}

EXECUTIVE SUMMARY:
{executive_summary}

ORGANIZED INSIGHTS:
{self.format_sections_for_prompt(sections_content)}

Create a compelling, scannable executive report following this EXACT format:

# 🧠 Executive Summary (1-minute read)
**Top 3 Takeaways** – Summary of the most impactful insights.
**Recommended Actions** – What the {user_role} should do or delegate.
**Business Relevance** – Why this matters now.

# 📊 Company Performance & Signals
(If connected to internal metrics or relevant public signals)

**Product / Engineering Highlights**
- New product launches, outages, releases (if public)

**Customer Trends**
- New logos, churn risk signals, major feedback

**Hiring & Talent**
- Key hires, exits, headcount growth (public signals or LinkedIn data)

**Investor/Board Mentions**
- Press or online mentions of investors or related moves

# 🌍 Market & Industry Trends
**Emerging Technologies**
- New tools, protocols, or platforms rising in usage or hype

**Shifts in Buyer Behavior**
- New procurement patterns, budget cuts, interest in certain features

**Macro Trends**
- Regulation, economic shifts, funding climate (e.g. AI, cybersecurity)

# 🔥 Competitor & Adjacent Player Moves
**Competitor Launches / Pivots**

**Partnerships / M&A**

**Funding Announcements**

**Hiring Trends / Talent War Signals**

Optionally, highlight with:
✅ Why this matters
⚠️ Threat level or opportunity level
💡 Suggested response or positioning

# 🕵️‍♂️ Emerging Opportunities & Threats
- High-potential partnerships
- New GTM angles
- Signals of market saturation or category decline
- Customer complaints in competitor ecosystems

# 📌 Strategic Recommendations
3–5 AI-synthesized strategic suggestions

E.g., "Explore partnerships in [category] with [relevant_copmany], due to [trend]."
"Start positioning around [keyword] to capture interest from [market]."
"Consider internal review of [tech stack/hiring pipeline], given [insight]."

# 🧾 Appendix (Optional)
Sources, links, long-form insights, graphs, screenshots

Focus on insights most relevant to {company}'s strategic position and {user_role}'s decision-making needs.
Avoid generic industry information - keep everything company-specific and actionable.
Use the organized insights provided to populate each section appropriately.
"""

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
            report = response.content
            
            # Add header and footer
            final_report = self.format_final_report(report, company, user_role)
            return final_report
            
        except Exception as e:
            logger.error(f"Error generating executive report: {e}")
            return f"Error generating executive report: {str(e)}"

    def extract_company_context(self, state: ResearchState) -> str:
        """Extract comprehensive company context from the research state."""
        context_pieces = []
        
        company = state.get('company', '')
        if company:
            context_pieces.append(f"Company: {company}")
            
        # Add detailed profile information
        if profile := state.get('profile', {}):
            if industry := profile.get('industry'):
                context_pieces.append(f"Industry: {industry}")
            if sector := profile.get('sector'):
                context_pieces.append(f"Sector: {sector}")
            if description := profile.get('description'):
                context_pieces.append(f"Business Description: {description}")
            if competitors := profile.get('competitors'):
                context_pieces.append(f"Key Competitors: {', '.join(competitors[:5])}")
            if clients := profile.get('known_clients'):
                context_pieces.append(f"Notable Clients: {', '.join(clients[:5])}")
            if partners := profile.get('partners'):
                context_pieces.append(f"Strategic Partners: {', '.join(partners[:5])}")
            if client_industries := profile.get('clients_industries'):
                context_pieces.append(f"Client Industries: {', '.join(client_industries[:5])}")
        
        # Add user interests context
        if user_interests := state.get('user_interests', {}):
            if strategic_interests := user_interests.get('strategic_interests'):
                context_pieces.append(f"Strategic Focus Areas: {', '.join(strategic_interests[:5])}")
            if tech_interests := user_interests.get('technology_interests'):
                context_pieces.append(f"Technology Interests: {', '.join(tech_interests[:5])}")
        
        return "\n".join(context_pieces) if context_pieces else "Limited company context available"

    def format_sections_for_prompt(self, sections_content: List[Dict[str, Any]]) -> str:
        """Format organized sections for the LLM prompt."""
        formatted = []
        for section in sections_content:
            formatted.append(f"\n{section['title'].upper()}:")
            for insight in section['insights']:
                formatted.append(f"• {insight.get('summary', '')} (Score: {insight.get('relevance_score', 0)})")
                if implication := insight.get('implication'):
                    formatted.append(f"  → {implication}")
        return "\n".join(formatted)

    def format_section_templates(self) -> str:
        """Format available section templates for the prompt."""
        formatted = []
        for key, template in self.section_templates.items():
            formatted.append(f"• {template['title']}: {template['description']}")
        return "\n".join(formatted)

    def format_final_report(self, report: str, company: str, user_role: str) -> str:
        """Add header and footer to the final report."""
        timestamp = datetime.now().strftime("%B %d, %Y")
        
        header = f"""# Executive Strategic Brief: {company}
**Prepared for:** {user_role}  
**Date:** {timestamp}  
**Report Type:** Strategic Intelligence Briefing

"""
        
        footer = f"""

---

**Report prepared by Company Research Agent**  
*This report synthesizes strategic intelligence from multiple sources and provides actionable insights tailored for executive decision-making.*

**Disclaimer:** This report is based on publicly available information and AI analysis. Verify critical information before making strategic decisions.
"""
        
        return header + report + footer

    async def create_basic_report(self, state: ResearchState) -> str:
        """Create a basic report when no insights are available."""
        company = state.get('company', 'Unknown Company')
        user_role = state.get('user_role', 'Executive')
        
        # Try to use any available briefings as fallback
        briefings = []
        for key in ['company_briefing', 'financial_briefing', 'news_briefing']:
            if content := state.get(key):
                briefings.append(content)
        
        if briefings:
            basic_content = "\n\n".join(briefings)
            prompt = f"""
Create a brief executive summary for {user_role} at {company} based on the following research:

{basic_content}

Format as a professional executive brief with key highlights and strategic implications.
Keep it concise and actionable.
"""
            try:
                response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
                return self.format_final_report(response.content, company, user_role)
            except Exception as e:
                logger.error(f"Error creating basic report: {e}")
        
        # Final fallback
        return self.format_final_report(
            f"# Executive Brief: {company}\n\nInsufficient data available to generate comprehensive strategic insights. Please ensure data collection and enrichment processes completed successfully.",
            company, user_role
        )