import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from ..classes import ResearchState
from ..config import config

logger = logging.getLogger(__name__)

class ComprehensiveDataSynthesizer:
    """
    Synthesizes all gathered data from various agents into a comprehensive, focused analysis.
    This includes company data, competitor analysis, industry trends, client trends, and market intelligence.
    """
    
    def __init__(self) -> None:
        try:
            self.llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0.2,
                api_key=config.OPENAI_API_KEY
            )
            logger.info("ComprehensiveDataSynthesizer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ComprehensiveDataSynthesizer LLM: {e}")
            raise

    async def run(self, state: ResearchState) -> ResearchState:
        """Run the comprehensive data synthesis process."""
        try:
            logger.info("Starting comprehensive data synthesis")
            return await self.synthesize_all_data(state)
        except Exception as e:
            logger.error(f"Error in comprehensive data synthesis: {e}", exc_info=True)
            # Create a fallback synthesis on error
            state['comprehensive_synthesis'] = {
                'error': f"Data synthesis error: {str(e)}",
                'timestamp': datetime.utcnow().isoformat()
            }
            return state

    async def synthesize_all_data(self, state: ResearchState) -> ResearchState:
        """Main method to synthesize all gathered data into actionable insights."""
        company = state.get('company', 'Unknown Company')
        user_role = state.get('user_role', 'Executive')
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')

        logger.info(f"Synthesizing comprehensive data for company: {company}, user_role: {user_role}")

        try:
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message=f"Synthesizing comprehensive data for {company}",
                    result={
                        "step": "Comprehensive Data Synthesizer",
                        "substep": "data_gathering"
                    }
                )

            # Gather all data from state
            synthesis_data = await self._gather_all_data(state)
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="analyzing",
                    message="Analyzing and synthesizing gathered data",
                    result={
                        "step": "Comprehensive Data Synthesizer",
                        "data_sources": len(synthesis_data),
                        "substep": "synthesis"
                    }
                )

            # Synthesize key insights
            key_insights = await self._extract_key_insights(synthesis_data, company, user_role)
            
            # Create competitor analysis summary
            competitor_summary = await self._synthesize_competitor_data(synthesis_data, company, user_role)
            
            # Create trend analysis summary
            trend_summary = await self._synthesize_trend_data(synthesis_data, company, user_role)
            
            # Compile comprehensive synthesis
            comprehensive_synthesis = {
                'company': company,
                'user_role': user_role,
                'timestamp': datetime.utcnow().isoformat(),
                'key_insights': key_insights,
                'competitor_summary': competitor_summary,
                'trend_summary': trend_summary,
                'data_coverage': {
                    'company_data': bool(synthesis_data.get('company_data')),
                    'competitor_data': bool(synthesis_data.get('competitor_data')),
                    'sector_trends': bool(synthesis_data.get('sector_trends')),
                    'client_trends': bool(synthesis_data.get('client_trends')),
                    'industry_data': bool(synthesis_data.get('industry_data')),
                    'market_intelligence': bool(synthesis_data.get('market_intelligence'))
                }
            }

            state['comprehensive_synthesis'] = comprehensive_synthesis

            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="synthesis_complete",
                    message="Comprehensive data synthesis completed",
                    result={
                        "step": "Comprehensive Data Synthesizer",
                        "insights_count": len(key_insights),
                        "competitor_count": len(competitor_summary.get('top_competitors', [])),
                        "trend_categories": len(trend_summary),
                        "substep": "complete"
                    }
                )

            # Update messages
            messages = state.get('messages', [])
            messages.append(AIMessage(content=f"📊 Comprehensive data synthesis completed for {company}"))
            state['messages'] = messages
            
            logger.info(f"Comprehensive synthesis completed for {company}")
            return state
            
        except Exception as e:
            logger.error(f"Critical error in synthesize_all_data: {e}", exc_info=True)
            state['comprehensive_synthesis'] = {
                'error': f"Critical synthesis error: {str(e)}",
                'timestamp': datetime.utcnow().isoformat()
            }
            return state

    async def _gather_all_data(self, state: ResearchState) -> Dict[str, Any]:
        """Gather all relevant data from the state for synthesis."""
        synthesis_data = {}
        
        # Company data
        synthesis_data['company_data'] = {
            'profile': state.get('profile', {}),
            'enriched_company': state.get('curated_company_data', {}),
            'company_url': state.get('company_url', ''),
            'industry': state.get('profile', {}).get('industry', ''),
            'business_model': state.get('profile', {}).get('business_model', ''),
            'target_market': state.get('profile', {}).get('target_market', ''),
            'key_products': state.get('profile', {}).get('key_products', []),
            'revenue_streams': state.get('profile', {}).get('revenue_streams', [])
        }
        
        # Competitor data
        synthesis_data['competitor_data'] = {
            'discovered_competitors': state.get('discovered_competitors', []),
            'competitor_analysis': state.get('competitor_analysis', {}),
            'enriched_competitor': state.get('curated_competitor_data', {}),
            'competitive_positioning': state.get('profile', {}).get('competitive_positioning', '')
        }
        
        # Trend data
        synthesis_data['sector_trends'] = state.get('sector_trends', {})
        synthesis_data['client_trends'] = state.get('client_trends', {})
        
        # Market intelligence
        synthesis_data['market_intelligence'] = {
            'enriched_news': state.get('curated_news_data', {}),
            'enriched_financial': state.get('curated_financial_data', {}),
            'research_results': state.get('research_results', {})
        }
        
        # Industry data
        synthesis_data['industry_data'] = {
            'industry_context': state.get('profile', {}).get('industry_context', ''),
            'market_size': state.get('profile', {}).get('market_size', ''),
            'growth_rate': state.get('profile', {}).get('growth_rate', ''),
            'key_players': state.get('profile', {}).get('key_players', [])
        }
        
        # User profile and interests
        synthesis_data['user_context'] = {
            'user_role': state.get('user_role', ''),
            'inferred_interests': state.get('inferred_interests', []),
            'research_intent': state.get('research_intent', {})
        }
        
        return synthesis_data

    async def _extract_key_insights(self, synthesis_data: Dict[str, Any], 
                                   company: str, user_role: str) -> List[Dict[str, Any]]:
        """Extract the most important insights from all gathered data."""
        
        prompt = f"""
        As a strategic business analyst, analyze the following comprehensive data about {company} 
        and extract the 5-7 most critical insights for someone in a {user_role} role.

        COMPREHENSIVE DATA:
        
        Company Profile:
        {self._format_company_data(synthesis_data.get('company_data', {}))}
        
        Competitor Intelligence:
        {self._format_competitor_data(synthesis_data.get('competitor_data', {}))}
        
        Industry Trends:
        Sector Trends: {self._format_trend_data(synthesis_data.get('sector_trends', {}))}
        Client Trends: {self._format_trend_data(synthesis_data.get('client_trends', {}))}
        
        Market Intelligence:
        {self._format_market_intelligence(synthesis_data.get('market_intelligence', {}))}

        Extract insights that are:
        1. Immediately actionable for a {user_role}
        2. Have significant strategic or competitive impact
        3. Represent opportunities or threats requiring attention
        4. Are supported by the data provided

        Format each insight as:
        - insight_title: Brief, compelling title
        - insight_description: 2-3 sentence explanation
        - impact_level: HIGH/MEDIUM/LOW
        - category: COMPETITIVE/MARKET/OPERATIONAL/STRATEGIC/FINANCIAL
        - recommended_action: Specific next step
        - supporting_data: Key data points that support this insight

        Return exactly 5-7 insights in JSON format.
        """

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
            insights_text = response.content
            
            # Parse the response
            import json
            try:
                insights = json.loads(insights_text)
                if isinstance(insights, list):
                    return insights[:7]  # Ensure max 7 insights
                else:
                    return [insights] if isinstance(insights, dict) else []
            except json.JSONDecodeError:
                # Fallback parsing
                return self._parse_insights_fallback(insights_text)
                
        except Exception as e:
            logger.error(f"Error extracting key insights: {e}")
            return [{
                'insight_title': 'Data Analysis Error',
                'insight_description': f'Unable to extract insights due to processing error: {str(e)}',
                'impact_level': 'LOW',
                'category': 'OPERATIONAL',
                'recommended_action': 'Review data sources and retry analysis',
                'supporting_data': 'Error in data processing'
            }]

    async def _synthesize_competitor_data(self, synthesis_data: Dict[str, Any], 
                                        company: str, user_role: str) -> Dict[str, Any]:
        """Synthesize competitor data into actionable summary."""
        
        competitor_data = synthesis_data.get('competitor_data', {})
        discovered_competitors = competitor_data.get('discovered_competitors', [])
        competitor_analysis = competitor_data.get('competitor_analysis', {})
        
        prompt = f"""
        Analyze the competitor data for {company} and create a focused competitive summary 
        for a {user_role}.

        COMPETITOR DATA:
        Discovered Competitors: {discovered_competitors}
        Detailed Analysis: {competitor_analysis}
        
        Create a summary with:
        1. Top 3-5 most important competitors to monitor
        2. Key competitive threats and their implications
        3. Competitive advantages {company} should leverage
        4. Market positioning gaps or opportunities
        5. Immediate competitive actions to consider

        Focus on actionable intelligence rather than general information.
        Return in JSON format with fields: top_competitors, threats, advantages, opportunities, recommended_actions
        """

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
            result = response.content
            
            import json
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {
                    'top_competitors': discovered_competitors[:5] if discovered_competitors else [],
                    'threats': ['Unable to parse competitive threats'],
                    'advantages': ['Analysis parsing error'],
                    'opportunities': ['Competitive analysis incomplete'],
                    'recommended_actions': ['Retry competitive analysis']
                }
                
        except Exception as e:
            logger.error(f"Error synthesizing competitor data: {e}")
            return {
                'error': f'Competitor synthesis error: {str(e)}',
                'top_competitors': discovered_competitors[:5] if discovered_competitors else []
            }

    async def _synthesize_trend_data(self, synthesis_data: Dict[str, Any], 
                                   company: str, user_role: str) -> Dict[str, Any]:
        """Synthesize trend data from sector and client analysis."""
        
        sector_trends = synthesis_data.get('sector_trends', {})
        client_trends = synthesis_data.get('client_trends', {})
        
        prompt = f"""
        Analyze the trend data for {company} and create actionable trend insights 
        for a {user_role}. For each trend, provide a brief explanation of how it specifically 
        relates to {company} and its business.

        TREND DATA:
        Sector Trends: {sector_trends}
        Client Industry Trends: {client_trends}
        
        Create a summary with:
        1. Top 3-5 sector trends affecting {company} - for each trend include:
           - trend_name: Brief name of the trend
           - trend_description: What the trend is about
           - company_relevance: How this trend specifically affects {company}
           
        2. Top 3-5 client industry trends creating opportunities/threats - for each trend include:
           - trend_name: Brief name of the trend  
           - trend_description: What the trend is about
           - company_relevance: How this trend specifically affects {company}
           
        3. Converging trends that create strategic opportunities for {company}
        4. Trend-based threats requiring immediate attention by {company}

        Return in JSON format with fields: sector_trends, client_trends, converging_opportunities, threats
        """

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
            result = response.content
            
            import json
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {
                    'sector_trends': ['Trend analysis parsing error'],
                    'client_trends': ['Client trend analysis incomplete'],
                    'converging_opportunities': ['Unable to identify convergence'],
                    'threats': ['Trend threat analysis failed']
                }
                
        except Exception as e:
            logger.error(f"Error synthesizing trend data: {e}")
            return {
                'error': f'Trend synthesis error: {str(e)}',
                'raw_sector_trends': sector_trends,
                'raw_client_trends': client_trends
            }

    async def _generate_strategic_recommendations(self, synthesis_data: Dict[str, Any], 
                                                key_insights: List[Dict[str, Any]], 
                                                company: str, user_role: str) -> List[Dict[str, Any]]:
        """Generate strategic recommendations based on all synthesized data."""
        
        prompt = f"""
        Based on the comprehensive analysis for {company}, generate 3-5 strategic recommendations 
        for a {user_role}.

        KEY INSIGHTS:
        {key_insights}
        
        SYNTHESIS DATA SUMMARY:
        - Company Profile: {synthesis_data.get('company_data', {}).get('profile', {})}
        - Competitor Count: {len(synthesis_data.get('competitor_data', {}).get('discovered_competitors', []))}
        - Trend Analysis: Available
        - Market Intelligence: Available
        
        Generate recommendations that are:
        1. Directly actionable within 30-90 days
        2. Based on specific insights from the data
        3. Address the most critical opportunities or threats
        4. Appropriate for the {user_role} role and authority level
        5. Include specific success metrics

        For each recommendation provide:
        - title: Clear, action-oriented title
        - description: 2-3 sentence explanation
        - priority: HIGH/MEDIUM/LOW
        - timeline: Immediate (0-30 days), Short-term (1-3 months), Medium-term (3-6 months)
        - required_resources: What's needed to execute
        - success_metrics: How to measure success
        - risk_level: LOW/MEDIUM/HIGH

        Return in JSON format as an array of recommendation objects.
        """

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
            result = response.content
            
            import json
            try:
                recommendations = json.loads(result)
                return recommendations if isinstance(recommendations, list) else [recommendations]
            except json.JSONDecodeError:
                return [{
                    'title': 'Strategic Analysis Required',
                    'description': 'Complete strategic analysis to identify specific recommendations.',
                    'priority': 'MEDIUM',
                    'timeline': 'Short-term (1-3 months)',
                    'required_resources': 'Strategic planning team',
                    'success_metrics': 'Completion of analysis',
                    'risk_level': 'LOW'
                }]
                
        except Exception as e:
            logger.error(f"Error generating strategic recommendations: {e}")
            return [{
                'title': 'Analysis Error',
                'description': f'Strategic recommendation generation failed: {str(e)}',
                'priority': 'LOW',
                'timeline': 'Immediate (0-30 days)',
                'required_resources': 'Technical review',
                'success_metrics': 'Error resolution',
                'risk_level': 'MEDIUM'
            }]

    def _format_company_data(self, company_data: Dict[str, Any]) -> str:
        """Format company data for LLM analysis."""
        profile = company_data.get('profile', {})
        return f"""
        Industry: {profile.get('industry', 'Unknown')}
        Business Model: {profile.get('business_model', 'Unknown')}
        Target Market: {profile.get('target_market', 'Unknown')}
        Key Products: {', '.join(profile.get('key_products', []))}
        Revenue Streams: {', '.join(profile.get('revenue_streams', []))}
        """

    def _format_competitor_data(self, competitor_data: Dict[str, Any]) -> str:
        """Format competitor data for LLM analysis."""
        competitors = competitor_data.get('discovered_competitors', [])
        analysis = competitor_data.get('competitor_analysis', {})
        
        formatted = f"Discovered Competitors ({len(competitors)}): {', '.join(competitors[:10])}\n"
        if analysis:
            formatted += f"Analysis Available: {len(analysis)} competitor profiles analyzed\n"
        return formatted

    def _format_trend_data(self, trend_data: Dict[str, Any]) -> str:
        """Format trend data for LLM analysis."""
        if not trend_data:
            return "No trend data available"
        
        formatted_trends = []
        for key, value in trend_data.items():
            if isinstance(value, (list, dict)):
                formatted_trends.append(f"{key}: {str(value)[:200]}...")
            else:
                formatted_trends.append(f"{key}: {str(value)}")
        
        return "; ".join(formatted_trends[:5])

    def _format_market_intelligence(self, market_intel: Dict[str, Any]) -> str:
        """Format market intelligence for LLM analysis."""
        news_count = len(market_intel.get('enriched_news', {}))
        financial_count = len(market_intel.get('enriched_financial', {}))
        research_count = len(market_intel.get('research_results', {}))
        
        return f"News Articles: {news_count}, Financial Data: {financial_count}, Research Results: {research_count}"

    def _parse_insights_fallback(self, text: str) -> List[Dict[str, Any]]:
        """Fallback method to parse insights if JSON parsing fails."""
        insights = []
        lines = text.split('\n')
        current_insight = {}
        
        for line in lines:
            line = line.strip()
            if 'insight_title:' in line.lower():
                if current_insight:
                    insights.append(current_insight)
                current_insight = {
                    'insight_title': line.split(':', 1)[1].strip(),
                    'impact_level': 'MEDIUM',
                    'category': 'STRATEGIC'
                }
            elif 'insight_description:' in line.lower() and current_insight:
                current_insight['insight_description'] = line.split(':', 1)[1].strip()
            elif 'recommended_action:' in line.lower() and current_insight:
                current_insight['recommended_action'] = line.split(':', 1)[1].strip()
        
        if current_insight:
            insights.append(current_insight)
        
        return insights[:7]  # Max 7 insights