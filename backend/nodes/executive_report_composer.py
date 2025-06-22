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
    """Composes market-focused executive reports with news headlines from enriched data."""
    
    def __init__(self) -> None:
        try:
            self.llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0.2,
                api_key=config.OPENAI_API_KEY
            )
            logger.info("ExecutiveReportComposer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ExecutiveReportComposer LLM: {e}")
            raise

    async def run(self, state: ResearchState) -> ResearchState:
        """Run the executive report composition process."""
        try:
            logger.info("Starting market-focused executive report composition")
            return await self.compose_market_report(state)
        except Exception as e:
            logger.error(f"Error in executive report composition: {e}", exc_info=True)
            # Create a fallback report on error
            state['report'] = f"Executive Report Generation Error: {str(e)}"
            return state

    async def compose_market_report(self, state: ResearchState) -> ResearchState:
        """Main method to compose market-focused executive report from enriched data."""
        company = state.get('company', 'Unknown Company')
        user_role = state.get('user_role', 'Executive')
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')

        logger.info(f"Composing market report for company: {company}, user_role: {user_role}")

        try:
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message=f"Composing market report for {company}",
                    result={
                        "step": "Executive Report Composer",
                        "substep": "initialization"
                    }
                )

            msg = [f"📋 Composing market report for {company}:"]

            # Get enriched data from all categories with COMPETITOR PRIORITY
            enriched_competitor = state.get('curated_competitor_data', {})
            enriched_news = state.get('curated_news_data', {})
            enriched_financial = state.get('curated_financial_data', {})
            enriched_company = state.get('curated_company_data', {})
            
            logger.info(f"Enriched data available - Competitor: {len(enriched_competitor)}, News: {len(enriched_news)}, Financial: {len(enriched_financial)}, Company: {len(enriched_company)}")
            
            if not any([enriched_competitor, enriched_news, enriched_financial, enriched_company]):
                logger.warning("No enriched data available - creating basic report")
                msg.append("\n⚠️ No enriched data available - creating basic report")
                
                try:
                    basic_report = await self.create_basic_report(state)
                    state['report'] = basic_report
                    logger.info("Basic report created successfully")
                except Exception as e:
                    logger.error(f"Failed to create basic report: {e}", exc_info=True)
                    state['report'] = f"Failed to generate report: {str(e)}"
                    
                messages = state.get('messages', [])
                messages.append(AIMessage(content="\n".join(msg)))
                state['messages'] = messages
                return state

            msg.append(f"\n• Processing enriched data - Competitor: {len(enriched_competitor)}, News: {len(enriched_news)}, Financial: {len(enriched_financial)}, Company: {len(enriched_company)}")

            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="analyzing",
                    message="Analyzing enriched market data with competitor priority",
                    result={
                        "step": "Executive Report Composer",
                        "competitor_count": len(enriched_competitor),
                        "news_count": len(enriched_news),
                        "financial_count": len(enriched_financial),
                        "company_count": len(enriched_company)
                    }
                )

            # Extract market intelligence with COMPETITOR FOCUS
            try:
                market_intelligence = await self.extract_competitor_focused_intelligence(
                    enriched_competitor, enriched_news, enriched_financial, enriched_company, state
                )
                logger.info("Competitor-focused market intelligence extracted successfully")
                msg.append(f"• Competitor-focused intelligence extracted from {len(market_intelligence)} relevant items")
            except Exception as e:
                logger.error(f"Failed to extract market intelligence: {e}", exc_info=True)
                market_intelligence = []
                msg.append(f"• Error extracting market intelligence: {str(e)}")

            # Generate the COMPETITOR-FOCUSED executive report
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="composing",
                    message="Composing competitor-focused market report",
                    result={
                        "step": "Executive Report Composer",
                        "intelligence_items": len(market_intelligence),
                        "competitor_focus": True
                    }
                )

            try:
                final_report = await self.generate_competitor_focused_report(
                    company, user_role, market_intelligence, state
                )
                logger.info("Competitor-focused headlines report generated successfully")
            except Exception as e:
                logger.error(f"Failed to generate competitor-focused report: {e}", exc_info=True)
                final_report = None
            
            if final_report:
                state['report'] = final_report
                logger.info(f"Final report completed with {len(final_report)} characters")
                msg.append(f"✅ Market report completed ({len(final_report)} characters)")
                
                if websocket_manager and job_id:
                    await websocket_manager.send_status_update(
                        job_id=job_id,
                        status="report_complete",
                        message="Market report completed successfully",
                        result={
                            "step": "Executive Report Composer",
                            "report_length": len(final_report),
                            "company": company,
                            "is_final": True,
                            "status": "completed"
                        }
                    )
            else:
                logger.error("Failed to generate executive report - creating fallback")
                try:
                    fallback_report = await self.create_basic_report(state)
                    state['report'] = fallback_report
                    msg.append("⚠️ Using fallback report due to generation error")
                except Exception as e:
                    logger.error(f"Fallback report also failed: {e}", exc_info=True)
                    state['report'] = f"Report generation failed: Unable to create report"
                    msg.append("❌ Failed to generate executive report")

            # Update messages
            messages = state.get('messages', [])
            messages.append(AIMessage(content="\n".join(msg)))
            state['messages'] = messages
            
            return state
            
        except Exception as e:
            logger.error(f"Critical error in compose_market_report: {e}", exc_info=True)
            state['report'] = f"Critical error in report composition: {str(e)}"
            messages = state.get('messages', [])
            messages.append(AIMessage(content=f"❌ Critical error in report composition: {str(e)}"))
            state['messages'] = messages
            return state

    async def extract_market_intelligence(self, enriched_news: Dict, enriched_financial: Dict, 
                                         enriched_company: Dict, state: ResearchState) -> List[Dict[str, Any]]:
        """Extract market intelligence from enriched data with focus on headlines and market impact."""
        
        # Get company profile for context
        profile = state.get('profile', {})
        company = state.get('company', 'Unknown Company')
        competitors = profile.get('competitors', [])
        partners = profile.get('partners', [])
        industry = profile.get('industry', '')
        
        market_intelligence = []
        
        # Process all enriched data sources
        all_data_sources = [
            ('news', enriched_news),
            ('financial', enriched_financial), 
            ('company', enriched_company)
        ]
        
        for source_type, data_source in all_data_sources:
            for url, doc_data in data_source.items():
                if not doc_data.get('raw_content'):
                    continue
                    
                # Extract key information from each document
                intelligence_item = {
                    'url': url,
                    'source_type': source_type,
                    'title': doc_data.get('title', ''),
                    'snippet': doc_data.get('snippet', ''),
                    'raw_content': doc_data.get('raw_content', ''),
                    'published_date': doc_data.get('published_date'),
                    'score': doc_data.get('score', 0)
                }
                
                market_intelligence.append(intelligence_item)
        
        # Sort by score and recency
        market_intelligence.sort(key=lambda x: (x.get('score', 0), x.get('published_date', '')), reverse=True)
        
        # Limit to top 20 items for processing
        return market_intelligence[:20]

    async def generate_market_headlines_report(self, company: str, user_role: str, 
                                             market_intelligence: List[Dict[str, Any]], 
                                             state: ResearchState) -> str:
        """Generate the final market headlines report."""
        
        # Get company context
        profile = state.get('profile', {})
        industry = profile.get('industry', 'Unknown Industry')
        competitors = profile.get('competitors', [])[:5]  # Top 5 competitors
        partners = profile.get('partners', [])[:5]  # Top 5 partners
        
        # Prepare market intelligence content for LLM
        intelligence_content = ""
        for i, item in enumerate(market_intelligence, 1):
            intelligence_content += f"{i}. **{item.get('title', 'No Title')}**\n"
            intelligence_content += f"   Source: {item.get('url', 'Unknown')}\n" 
            intelligence_content += f"   Snippet: {item.get('snippet', 'No snippet')}\n"
            if item.get('raw_content'):
                # Use first 500 chars of raw content
                content_preview = item['raw_content'][:500] + "..." if len(item['raw_content']) > 500 else item['raw_content']
                intelligence_content += f"   Content: {content_preview}\n"
            intelligence_content += "\n"

        # Create the market headlines report prompt
        prompt = f"""
You are creating a market intelligence briefing for a {user_role} at {company}. 

COMPANY CONTEXT:
- Company: {company}
- Industry: {industry}
- Key Competitors: {', '.join(competitors) if competitors else 'Not specified'}
- Strategic Partners: {', '.join(partners) if partners else 'Not specified'}

MARKET INTELLIGENCE DATA:
{intelligence_content}

Create a market report focusing on HEADLINES and MARKET DEVELOPMENTS that impact {company}'s business environment. Format the report with clear headlines similar to these examples:

Example Headlines:
- "Stripe exposes MCP server for merchants to connect with code agents easily"
- "EU regulator forces Apple to have the option for another application store"

Create a report with the following structure:

# 📊 Market Intelligence Report: {company}

## 🔥 Key Market Headlines
[List 5-8 most impactful headlines from the market intelligence, focusing on:]
- Industry developments that affect {company}'s market
- Competitor moves and strategic announcements  
- Regulatory changes impacting the sector
- Technology trends relevant to the business
- Partnership and funding news in the ecosystem
- New market opportunities or threats

**Format each headline as:**
**Headline:** [Clear, impactful headline]
**Impact:** [Brief explanation of relevance to {company}]

## 🏢 Industry Landscape Changes
[Summarize major shifts in the {industry} industry that {company} should monitor]

## 🎯 Competitive Intelligence  
[Highlight competitor moves, new entrants, or market positioning changes]

## 🚀 Emerging Opportunities
[Identify new markets, technologies, or partnerships {company} could consider]

## ⚠️ Market Risks & Challenges
[Flag potential threats or regulatory challenges]

## 📈 Strategic Implications
[Provide 3-5 actionable insights for {company} based on market developments]

Focus on external market signals, news, and developments rather than internal company analysis.
Make headlines clear, specific, and impactful.
Ensure all information is sourced from the provided market intelligence data.
"""

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
            report = response.content
            
            # Add header and footer
            final_report = self.format_final_report(report, company, user_role)
            return final_report
            
        except Exception as e:
            logger.error(f"Error generating market headlines report: {e}")
            return f"Error generating market headlines report: {str(e)}"

    def format_final_report(self, report: str, company: str, user_role: str) -> str:
        """Add header and footer to the final report."""
        timestamp = datetime.now().strftime("%B %d, %Y")
        
        header = f"""# Market Intelligence Briefing: {company}
**Prepared for:** {user_role}  
**Date:** {timestamp}  
**Report Type:** Market Headlines & Intelligence

"""
        
        footer = f"""

---

**Report prepared by Company Research Agent**  
*This market intelligence briefing synthesizes recent developments, headlines, and market signals relevant to {company}'s business environment.*

**Disclaimer:** This report is based on publicly available information and AI analysis. Verify critical information before making strategic decisions.
"""
        
        return header + report + footer

    async def create_basic_report(self, state: ResearchState) -> str:
        """Create a basic report when no enriched data is available."""
        company = state.get('company', 'Unknown Company')
        user_role = state.get('user_role', 'Executive')
        
        logger.info(f"Creating basic market report for {company}")
        
        # Get company profile for context
        profile = state.get('profile', {})
        industry = profile.get('industry', 'Unknown Industry')
        competitors = profile.get('competitors', [])[:3]
        
        basic_content = f"""# Market Intelligence Report: {company}

## Overview
Market intelligence research was initiated for {company} in the {industry} sector, but detailed market data extraction encountered limitations.

## Company Profile
- **Industry:** {industry}
- **Key Competitors:** {', '.join(competitors) if competitors else 'To be determined'}

## Market Research Status
The automated market intelligence gathering process was initiated but faced challenges in:
- Accessing real-time market data sources
- Extracting detailed content from news and financial sources
- Processing competitive intelligence feeds

## Recommended Next Steps
1. **Manual Market Monitoring:** Set up Google Alerts for {company} and key competitors
2. **Industry News Tracking:** Subscribe to {industry} trade publications and news feeds
3. **Competitive Intelligence:** Monitor competitor websites and press releases directly
4. **Regulatory Monitoring:** Track relevant regulatory changes in the {industry} sector

## Strategic Considerations
- Monitor {company}'s competitive positioning in the {industry} market
- Track technology trends and platform changes affecting the sector
- Assess partnership opportunities and market expansion possibilities
- Stay informed of regulatory developments that could impact operations

*This report represents the available information at the time of analysis. For critical business decisions, supplement with additional research and verification.*
"""
        
        return self.format_final_report(basic_content, company, user_role)

    async def extract_competitor_focused_intelligence(self, enriched_competitor: Dict, enriched_news: Dict, 
                                                     enriched_financial: Dict, enriched_company: Dict, 
                                                     state: ResearchState) -> List[Dict[str, Any]]:
        """Extract market intelligence with ENHANCED COMPETITOR FOCUS and better data quality."""
        
        # Get company profile for context
        profile = state.get('profile', {})
        company = state.get('company', 'Unknown Company')
        competitors = profile.get('competitors', [])
        partners = profile.get('partners', [])
        industry = profile.get('industry', '')
        
        market_intelligence = []
        
        # PRIORITY 1: Process competitor data first with enhanced scoring
        competitor_intel = []
        if enriched_competitor:
            for url, doc_data in enriched_competitor.items():
                if not doc_data.get('raw_content'):
                    continue
                    
                # Enhanced scoring for competitor relevance
                title = doc_data.get('title', '').lower()
                content = doc_data.get('raw_content', '').lower()
                score = doc_data.get('score', 0.5)
                
                # Boost score for specific competitor mentions
                for competitor in competitors[:5]:  # Top 5 competitors
                    if competitor.lower() in title or competitor.lower() in content:
                        score += 0.4  # Significant boost for direct competitor mentions
                        break
                
                # Boost for competitive keywords
                competitive_keywords = [
                    'announces', 'launches', 'partnership', 'integration', 'funding', 
                    'acquisition', 'expands', 'new product', 'platform', 'api', 
                    'strategic', 'market share', 'competitive', 'rival', 'vs', 'comparison'
                ]
                
                keyword_matches = sum(1 for keyword in competitive_keywords if keyword in title or keyword in content)
                score += min(keyword_matches * 0.1, 0.3)  # Boost up to 0.3 for keyword matches
                
                # Boost for recent dates
                published_date = doc_data.get('published_date', '')
                if '2024' in published_date:
                    score += 0.2
                elif '2023' in published_date:
                    score += 0.1
                
                intelligence_item = {
                    'url': url,
                    'source_type': 'competitor',
                    'title': doc_data.get('title', ''),
                    'snippet': doc_data.get('snippet', ''),
                    'raw_content': doc_data.get('raw_content', ''),
                    'published_date': published_date,
                    'score': min(score, 1.0),  # Cap at 1.0
                    'priority': 'high',
                    'is_competitor_focused': True
                }
                
                competitor_intel.append(intelligence_item)
        
        # PRIORITY 2: Process news data with competitor focus
        news_intel = []
        if enriched_news:
            for url, doc_data in enriched_news.items():
                if not doc_data.get('raw_content'):
                    continue
                    
                title = doc_data.get('title', '').lower()
                content = doc_data.get('raw_content', '').lower()
                score = doc_data.get('score', 0.3)
                
                # Check if news mentions competitors
                competitor_mentions = []
                for competitor in competitors[:5]:
                    if competitor.lower() in title or competitor.lower() in content:
                        competitor_mentions.append(competitor)
                        score += 0.3
                
                # Only include news that mentions competitors or has high competitive relevance
                if competitor_mentions or any(keyword in title or keyword in content for keyword in [
                    'competitive', 'market leader', 'rivalry', 'vs', 'compared to', 'against'
                ]):
                    intelligence_item = {
                        'url': url,
                        'source_type': 'news',
                        'title': doc_data.get('title', ''),
                        'snippet': doc_data.get('snippet', ''),
                        'raw_content': doc_data.get('raw_content', ''),
                        'published_date': doc_data.get('published_date', ''),
                        'score': min(score, 1.0),
                        'priority': 'medium' if competitor_mentions else 'low',
                        'competitor_mentions': competitor_mentions,
                        'is_competitor_focused': bool(competitor_mentions)
                    }
                    news_intel.append(intelligence_item)
        
        # PRIORITY 3: Process financial and company data with competitor context
        other_intel = []
        for source_type, data_source in [('financial', enriched_financial), ('company', enriched_company)]:
            if not data_source:
                continue
                
            for url, doc_data in data_source.items():
                if not doc_data.get('raw_content'):
                    continue
                    
                title = doc_data.get('title', '').lower()
                content = doc_data.get('raw_content', '').lower()
                score = doc_data.get('score', 0.2)
                
                # Only include if it has competitive relevance
                if any(competitor.lower() in title or competitor.lower() in content for competitor in competitors[:5]) or \
                   any(keyword in title or keyword in content for keyword in [
                       'market position', 'competitive advantage', 'market share', 'industry leader'
                   ]):
                    intelligence_item = {
                        'url': url,
                        'source_type': source_type,
                        'title': doc_data.get('title', ''),
                        'snippet': doc_data.get('snippet', ''),
                        'raw_content': doc_data.get('raw_content', ''),
                        'published_date': doc_data.get('published_date', ''),
                        'score': score,
                        'priority': 'low',
                        'is_competitor_focused': True
                    }
                    other_intel.append(intelligence_item)
        
        # Combine all intelligence with competitor data prioritized
        market_intelligence = competitor_intel + news_intel + other_intel
        
        # Sort by priority and score
        def sort_key(item):
            priority_weights = {'high': 3, 'medium': 2, 'low': 1}
            return (priority_weights.get(item.get('priority', 'low'), 1), item.get('score', 0))
        
        market_intelligence.sort(key=sort_key, reverse=True)
        
        # Limit to top 25 items but ensure at least 15 are competitor-focused
        competitor_focused = [item for item in market_intelligence if item.get('is_competitor_focused', False)]
        non_competitor = [item for item in market_intelligence if not item.get('is_competitor_focused', False)]
        
        final_intelligence = competitor_focused[:20] + non_competitor[:5]  # Ensure competitor focus
        
        logger.info(f"Extracted {len(final_intelligence)} intelligence items ({len([i for i in final_intelligence if i.get('is_competitor_focused')])} competitor-focused)")
        return final_intelligence

    async def generate_competitor_focused_report(self, company: str, user_role: str, 
                                                 market_intelligence: List[Dict[str, Any]], 
                                                 state: ResearchState) -> str:
        """Generate the ENHANCED COMPETITOR-FOCUSED executive report with competitive intelligence as the main focus."""
        
        # Get company context
        profile = state.get('profile', {})
        industry = profile.get('industry', 'Unknown Industry')
        competitors = profile.get('competitors', [])[:8]  # Top 8 competitors for comprehensive analysis
        partners = profile.get('partners', [])[:5]  # Top 5 partners
        
        # Separate competitor-focused vs general intelligence
        competitor_focused_intel = [item for item in market_intelligence if item.get('is_competitor_focused', False)]
        general_intel = [item for item in market_intelligence if not item.get('is_competitor_focused', False)]
        
        # Prepare detailed competitor intelligence content for LLM
        competitor_content = ""
        if competitor_focused_intel:
            competitor_content += "COMPETITOR-FOCUSED INTELLIGENCE:\n"
            for i, item in enumerate(competitor_focused_intel[:15], 1):  # Focus on top 15 competitor items
                competitor_content += f"{i}. **{item.get('title', 'No Title')}**\n"
                competitor_content += f"   Source: {item.get('url', 'Unknown')}\n"
                competitor_content += f"   Published: {item.get('published_date', 'Unknown date')}\n"
                competitor_content += f"   Snippet: {item.get('snippet', 'No snippet')}\n"
                if item.get('raw_content'):
                    # Use more content for competitor intelligence (750 chars)
                    content_preview = item['raw_content'][:750] + "..." if len(item['raw_content']) > 750 else item['raw_content']
                    competitor_content += f"   Full Content: {content_preview}\n"
                if item.get('competitor_mentions'):
                    competitor_content += f"   Competitors Mentioned: {', '.join(item['competitor_mentions'])}\n"
                competitor_content += f"   Priority: {item.get('priority', 'unknown')}\n\n"
        
        # Prepare general market intelligence
        general_content = ""
        if general_intel:
            general_content += "GENERAL MARKET INTELLIGENCE:\n"
            for i, item in enumerate(general_intel[:8], 1):  # Limit general intel
                general_content += f"{i}. **{item.get('title', 'No Title')}**\n"
                general_content += f"   Source: {item.get('url', 'Unknown')}\n"
                general_content += f"   Snippet: {item.get('snippet', 'No snippet')}\n"
                if item.get('raw_content'):
                    content_preview = item['raw_content'][:400] + "..." if len(item['raw_content']) > 400 else item['raw_content']
                    general_content += f"   Content: {content_preview}\n"
                general_content += "\n"

        # Create the ENHANCED COMPETITOR-FOCUSED executive report prompt
        prompt = f"""
You are creating a COMPETITOR-FOCUSED market intelligence briefing for a {user_role} at {company}. 

This report should be structured with COMPETITIVE INTELLIGENCE as the PRIMARY and MOST PROMINENT section - this is what CEOs read first and care about most.

COMPANY CONTEXT:
- Company: {company}
- Industry: {industry}
- Key Competitors: {', '.join(competitors) if competitors else 'Not specified'}
- Strategic Partners: {', '.join(partners) if partners else 'Not specified'}

INTELLIGENCE DATA:
{competitor_content}

{general_content}

Create a report with the following structure, prioritizing competitive intelligence:

# 🚀 Competitive Intelligence Briefing: {company}

## 🎯 EXECUTIVE SUMMARY - COMPETITIVE LANDSCAPE
[2-3 sentence executive summary focusing on the most critical competitive developments that {company} leadership needs to know immediately]

## 🔥 COMPETITIVE INTELLIGENCE - MAIN COMPETITORS
[This is the MAIN section - provide detailed analysis of what each key competitor is doing. For each major competitor mentioned in the data, provide:]

### {competitors[0] if competitors else 'Primary Competitor'}
- **Latest Moves:** [Specific recent actions, launches, partnerships]
- **Strategic Direction:** [What they're focusing on based on the intelligence]  
- **Market Impact:** [How this affects {company}'s position]
- **Threat Level:** [High/Medium/Low and why]

### {competitors[1] if len(competitors) > 1 else 'Secondary Competitor'}
[Same format as above]

[Continue for other major competitors found in the intelligence...]

## 📊 COMPETITIVE MARKET HEADLINES
[List 5-8 most impactful competitive headlines from the intelligence data:]

**Format each headline as:**
• **[Clear, impactful headline about competitor move]**
  - **Competitor:** [Which competitor]
  - **Impact on {company}:** [Direct relevance and implications]
  - **Source:** [Brief source reference]

## ⚡ IMMEDIATE COMPETITIVE THREATS & OPPORTUNITIES  
[Based on the competitive intelligence, identify:]
- **Immediate Threats:** [What competitors are doing that could hurt {company}]
- **Market Opportunities:** [Gaps or weaknesses in competitor strategies {company} could exploit]
- **Partnership Opportunities:** [Potential strategic moves based on competitor activities]

## 🏢 BROADER INDUSTRY DEVELOPMENTS
[Secondary section - broader industry trends and developments not directly competitor-focused]

## 📈 STRATEGIC RECOMMENDATIONS
[Provide 3-5 specific, actionable recommendations for {company} based on competitive intelligence:]
1. [Specific action based on competitor analysis]
2. [Specific action based on competitive threats]
3. [Specific action based on market opportunities]
4. [Specific action based on competitive positioning]
5. [Specific action for competitive advantage]

CRITICAL REQUIREMENTS:
- Focus primarily on what COMPETITORS are doing - their launches, partnerships, funding, strategic moves
- Make competitive intelligence the longest and most detailed section
- Provide specific, actionable insights about each major competitor
- Connect every insight back to implications for {company}
- Use the actual data provided - don't make up information
- Prioritize recent developments (2024 content)
- Make headlines specific and impactful, not generic
"""

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
            report = response.content
            
            # Add header and footer with competitive focus
            final_report = self.format_competitive_report(report, company, user_role, len(competitor_focused_intel))
            return final_report
            
        except Exception as e:
            logger.error(f"Error generating enhanced competitor-focused report: {e}")
            return f"Error generating enhanced competitor-focused report: {str(e)}"

    def format_competitive_report(self, report: str, company: str, user_role: str, competitor_intel_count: int) -> str:
        """Add header and footer to the competitive intelligence report."""
        timestamp = datetime.now().strftime("%B %d, %Y")
        
        header = f"""# 🎯 Competitive Intelligence Briefing: {company}
**Prepared for:** {user_role}  
**Date:** {timestamp}  
**Report Type:** Competitive Intelligence & Market Analysis  
**Competitor Intelligence Sources:** {competitor_intel_count} focused data points

---

"""
        
        footer = f"""

---

## 📋 Intelligence Summary
- **Focus:** Competitive landscape analysis with emphasis on main competitors
- **Data Sources:** {competitor_intel_count} competitor-focused intelligence items
- **Coverage:** Recent developments, strategic moves, and market positioning
- **Next Steps:** Monitor competitor activities and implement strategic recommendations

**Report prepared by Company Research Agent - Competitive Intelligence Module**  
*This competitive intelligence briefing prioritizes competitor activities and strategic moves relevant to {company}'s market position.*

**Disclaimer:** This competitive analysis is based on publicly available information and AI analysis. Verify critical competitive intelligence before making strategic decisions.
"""
        
        return header + report + footer