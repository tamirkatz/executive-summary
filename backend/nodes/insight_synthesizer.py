import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from ..classes import ResearchState
from ..config import config

logger = logging.getLogger(__name__)

class InsightSynthesizer:
    """Synthesizes insights from enriched data across all categories."""
    
    def __init__(self) -> None:
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=config.OPENAI_API_KEY
        )
        self.insight_tags = [
            "opportunity", "threat", "strategic_move", "market_signal", 
            "competitive_advantage", "risk", "trend", "regulatory_change",
            "financial_impact", "innovation", "partnership", "expansion"
        ]


    def _format_documents_for_analysis(self, documents: List[Dict[str, Any]]) -> str:
        """Format documents for LLM analysis."""
        formatted = []
        for i, doc in enumerate(documents[:10], 1):  # Limit to top 10 documents
            formatted.append(f"{i}. {doc['title']}\n   {doc['content'][:500]}...\n   URL: {doc['url']}\n")
        return "\n".join(formatted)

    def _parse_insights_response(self, response_text: str, category: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured insights."""
        insights = []
        try:
            import json
            # Try to parse as JSON first
            parsed = json.loads(response_text)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        insight = {
                            'summary': item.get('summary', ''),
                            'implication': item.get('implication', ''),
                            'relevance_score': int(item.get('relevance_score', 5)),
                            'tags': item.get('tags', []),
                            'source_urls': item.get('source_urls', []),
                            'category': category,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        insights.append(insight)
        except json.JSONDecodeError:
            # Fallback to text parsing if JSON parsing fails
            insights = self._parse_text_insights(response_text, category)
        
        return insights

    def _parse_text_insights(self, text: str, category: str) -> List[Dict[str, Any]]:
        """Fallback text parsing for insights."""
        insights = []
        lines = text.split('\n')
        current_insight = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('summary:') or line.startswith('Summary:'):
                if current_insight:
                    insights.append(current_insight)
                current_insight = {
                    'summary': line.split(':', 1)[1].strip(),
                    'category': category,
                    'timestamp': datetime.utcnow().isoformat(),
                    'relevance_score': 7,  # Default score
                    'tags': [],
                    'source_urls': []
                }
            elif line.startswith('implication:') or line.startswith('Implication:'):
                if current_insight:
                    current_insight['implication'] = line.split(':', 1)[1].strip()
            elif line.startswith('relevance_score:') or line.startswith('Relevance Score:'):
                if current_insight:
                    try:
                        score = int(line.split(':', 1)[1].strip())
                        current_insight['relevance_score'] = max(1, min(10, score))
                    except ValueError:
                        current_insight['relevance_score'] = 7
        
        if current_insight:
            insights.append(current_insight)
        
        return insights

    async def prioritize_insights(self, all_insights: List[Dict[str, Any]], 
                                company: str, user_role: str) -> Dict[str, Any]:
        """Prioritize and structure insights across all categories."""
        if not all_insights:
            return {"prioritized_insights": [], "summary": "No insights generated"}

        # Group insights by category
        insights_by_category = {}
        for insight in all_insights:
            category = insight.get('category', 'unknown')
            if category not in insights_by_category:
                insights_by_category[category] = []
            insights_by_category[category].append(insight)

        # Sort all insights by relevance score
        top_insights = sorted(all_insights, key=lambda x: x.get('relevance_score', 0), reverse=True)

        # Create executive summary
        summary_prompt = f"""
Based on the following strategic insights for {company}, create an executive summary 
for someone in a {user_role} role. Focus on the top 3-5 most critical points:

TOP INSIGHTS:
{self._format_insights_for_summary(top_insights[:10])}

Provide:
1. A 2-3 sentence executive summary
2. Top 3 immediate priorities/actions
3. Key risks to monitor
4. Key opportunities to pursue

Keep it concise and actionable.
"""

        try:
            summary_response = await self.llm.ainvoke([{"role": "user", "content": summary_prompt}])
            executive_summary = summary_response.content
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            executive_summary = "Unable to generate executive summary due to processing error."

        return {
            "prioritized_insights": top_insights[:15],  # Top 15 insights
            "insights_by_category": insights_by_category,
            "executive_summary": executive_summary,
            "total_insights": len(all_insights),
            "categories_analyzed": list(insights_by_category.keys()),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }

    def _format_insights_for_summary(self, insights: List[Dict[str, Any]]) -> str:
        """Format insights for executive summary generation."""
        formatted = []
        for i, insight in enumerate(insights, 1):
            tags = ', '.join(insight.get('tags', []))
            formatted.append(
                f"{i}. [{insight.get('category', 'unknown').upper()}] "
                f"{insight.get('summary', '')} "
                f"(Score: {insight.get('relevance_score', 0)}, Tags: {tags})"
            )
        return "\n".join(formatted)

    async def extract_insights_from_content(self, category: str, documents: Dict[str, Any], 
                                          company: str, user_role: str, industry: str = "Unknown") -> List[Dict[str, Any]]:
        """Extract insights from a specific category of documents."""
        if not documents:
            return []

        # Prepare content for analysis
        content_summaries = []
        for url, doc in documents.items():
            if doc.get('raw_content'):
                summary = {
                    'title': doc.get('title', 'No title'),
                    'url': url,
                    'content': doc.get('raw_content', '')[:2000],  # Truncate for efficiency
                    'score': doc.get('evaluation', {}).get('overall_score', 0)
                }
                content_summaries.append(summary)

        if not content_summaries:
            return []

        # Create context-aware prompt
        prompt = f"""
You are an expert strategic business analyst with deep domain expertise in {industry}. 
Your analysis should provide executive-level insights for {company}, specifically relevant to someone in a {user_role} role.

Analyze the following {category} documents and extract high-value strategic insights:

DOCUMENTS:
{self._format_documents_for_analysis(content_summaries)}

ANALYSIS FRAMEWORK:
For a {user_role} at {company} in the {industry} industry, extract insights that are:

1. **Strategic Impact**: How does this affect {company}'s competitive position, market opportunities, or strategic direction?
2. **Operational Implications**: What specific actions or decisions should {company} consider?
3. **Competitive Intelligence**: How does this relate to competitor moves or market dynamics?
4. **Industry Context**: What broader industry trends or regulatory changes are at play?
5. **Financial Impact**: What are the potential revenue, cost, or valuation implications?

SPECIFIC FOCUS AREAS for {industry}:
- Market consolidation and M&A activity
- Regulatory changes and compliance requirements  
- Technology disruption and innovation trends
- Partnership and ecosystem developments
- Customer behavior and demand shifts
- Competitive positioning and differentiation

Extract 3-5 most important insights that are:
- Directly actionable for {company}
- Strategically significant (not operational details)
- Backed by specific evidence from the documents
- Relevant to current market conditions and {user_role} decision-making

For each insight, provide:
- summary: A strategic insight statement (1-2 sentences) that explains the key finding and its significance
- implication: Specific strategic implications for {company} - what this means for their business, competitive position, or strategic decisions
- relevance_score: 1-10 (10 being critical strategic importance to {company})
- tags: Choose 1-2 most relevant tags from: {', '.join(self.insight_tags)}
- source_urls: URLs that support this insight
- category: {category}

QUALITY STANDARDS:
- Avoid generic industry information - focus on {company}-specific implications
- Provide specific, actionable strategic guidance
- Connect insights to broader business strategy and competitive dynamics
- Use evidence from documents to support conclusions

Respond with insights in this exact format:
INSIGHT 1:
Summary: [strategic insight statement]
Implication: [specific implications for {company}]  
Relevance Score: [1-10]
Tags: [tag1], [tag2]
URLs: [url1], [url2]
"""

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
            insights_text = response.content
            
            # Parse the response to extract structured insights
            insights = self._parse_insights_response(insights_text, category)
            
            # Filter and rank insights
            filtered_insights = [
                insight for insight in insights 
                if insight.get('relevance_score', 0) >= 6
            ]
            
            return sorted(filtered_insights, key=lambda x: x.get('relevance_score', 0), reverse=True)

        except Exception as e:
            logger.error(f"Error extracting insights from {category}: {e}")
            return []

    def _format_documents_for_analysis(self, documents: List[Dict[str, Any]]) -> str:
        """Format documents for LLM analysis."""
        formatted = []
        for i, doc in enumerate(documents[:10], 1):  # Limit to top 10 documents
            formatted.append(f"{i}. {doc['title']}\n   {doc['content'][:500]}...\n   URL: {doc['url']}\n")
        return "\n".join(formatted)

    def _parse_insights_response(self, response_text: str, category: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured insights."""
        insights = []
        lines = response_text.split('\n')
        current_insight = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('INSIGHT'):
                if current_insight:
                    insights.append(current_insight)
                current_insight = {
                    'category': category,
                    'timestamp': datetime.utcnow().isoformat(),
                    'relevance_score': 7,  # Default score
                    'tags': [],
                    'source_urls': []
                }
            elif line.startswith('Summary:'):
                if current_insight:
                    current_insight['summary'] = line.split(':', 1)[1].strip()
            elif line.startswith('Implication:'):
                if current_insight:
                    current_insight['implication'] = line.split(':', 1)[1].strip()
            elif line.startswith('Relevance Score:'):
                if current_insight:
                    try:
                        score = int(line.split(':', 1)[1].strip())
                        current_insight['relevance_score'] = max(1, min(10, score))
                    except ValueError:
                        current_insight['relevance_score'] = 7
            elif line.startswith('Tags:'):
                if current_insight:
                    tags_text = line.split(':', 1)[1].strip()
                    current_insight['tags'] = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
            elif line.startswith('URLs:'):
                if current_insight:
                    urls_text = line.split(':', 1)[1].strip()
                    current_insight['source_urls'] = [url.strip() for url in urls_text.split(',') if url.strip()]
        
        if current_insight:
            insights.append(current_insight)
        
        return insights

    async def prioritize_insights(self, all_insights: List[Dict[str, Any]], 
                                company: str, user_role: str) -> Dict[str, Any]:
        """Prioritize and structure insights across all categories."""
        if not all_insights:
            return {"prioritized_insights": [], "summary": "No insights generated"}

        # Group insights by category
        insights_by_category = {}
        for insight in all_insights:
            category = insight.get('category', 'unknown')
            if category not in insights_by_category:
                insights_by_category[category] = []
            insights_by_category[category].append(insight)

        # Sort all insights by relevance score
        top_insights = sorted(all_insights, key=lambda x: x.get('relevance_score', 0), reverse=True)

        # Create executive summary
        summary_prompt = f"""
You are a strategic advisor creating an executive briefing for a {user_role} at {company}.
Based on the following strategic insights, create a compelling executive summary that drives decision-making:

TOP INSIGHTS:
{self._format_insights_for_summary(top_insights[:10])}

Create an executive summary with:

**Strategic Context**: What's happening in the market/industry that {company} needs to know about right now?

**Critical Implications**: What are the 3 most important strategic implications for {company}? Focus on:
- Competitive positioning changes
- Market opportunities or threats
- Strategic partnerships or M&A possibilities
- Technology or regulatory shifts
- Financial/operational impacts

**Immediate Actions**: What should the {user_role} do or delegate in the next 30-60 days? Be specific:
- Strategic decisions to make
- Partnerships to explore
- Competitive responses needed
- Market positioning adjustments

**Why This Matters Now**: What makes these insights time-sensitive? What happens if {company} doesn't act?

Requirements:
- Be specific to {company}'s situation, not generic industry advice
- Include company names, specific technologies, or market segments where relevant
- Focus on strategic decisions at the {user_role} level
- Make it actionable with clear next steps
- Keep it executive-level (strategic, not operational)

Write in a confident, forward-looking tone that helps the {user_role} make informed strategic decisions.
"""

        try:
            summary_response = await self.llm.ainvoke([{"role": "user", "content": summary_prompt}])
            executive_summary = summary_response.content
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            executive_summary = "Unable to generate executive summary due to processing error."

        return {
            "prioritized_insights": top_insights[:15],  # Top 15 insights
            "insights_by_category": insights_by_category,
            "executive_summary": executive_summary,
            "total_insights": len(all_insights),
            "categories_analyzed": list(insights_by_category.keys()),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }

    def _format_insights_for_summary(self, insights: List[Dict[str, Any]]) -> str:
        """Format insights for executive summary generation."""
        formatted = []
        for i, insight in enumerate(insights, 1):
            tags = ', '.join(insight.get('tags', []))
            formatted.append(
                f"{i}. [{insight.get('category', 'unknown').upper()}] "
                f"{insight.get('summary', '')} "
                f"(Score: {insight.get('relevance_score', 0)}, Tags: {tags})"
            )
        return "\n".join(formatted)

    async def run(self, state: ResearchState) -> ResearchState:
        """Run the insight synthesis process."""
        try:
            return await self.synthesize_insights(state)
        except Exception as e:
            logger.error(f"Error in insight synthesis process: {e}")
            # Return state with empty insights on error
            state['strategic_insights'] = {
                "prioritized_insights": [],
                "insights_by_category": {},
                "executive_summary": f"Error during insight synthesis: {str(e)}",
                "total_insights": 0,
                "categories_analyzed": [],
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            return state

    async def synthesize_insights(self, state: ResearchState) -> ResearchState:
        """Main method to synthesize insights from all enriched data."""
        company = state.get('company', 'Unknown Company')
        user_role = state.get('user_role', 'Business Analyst')
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')

        if websocket_manager and job_id:
            await websocket_manager.send_status_update(
                job_id=job_id,
                status="processing",
                message=f"Starting insight synthesis for {company}",
                result={
                    "step": "Insight Synthesis",
                    "substep": "initialization"
                }
            )

        msg = [f"🧠 Synthesizing strategic insights for {company}:"]

        # Define data categories to analyze
        data_categories = {
            'curated_financial_data': 'financial',
            'curated_news_data': 'news', 
            'curated_company_data': 'company'
        }

        # Process insights for each category
        all_insights = []
        for state_field, category in data_categories.items():
            documents = state.get(state_field, {})
            if documents:
                msg.append(f"\n• Analyzing {len(documents)} {category} documents...")
                if websocket_manager and job_id:
                    await websocket_manager.send_status_update(
                        job_id=job_id,
                        status="category_analysis",
                        message=f"Analyzing {category} documents for insights",
                        result={
                            "step": "Insight Synthesis",
                            "category": category,
                            "document_count": len(documents)
                        }
                    )
                
                # Get industry from state if available
                profile = state.get('profile', {})
                industry = profile.get('industry', 'Unknown Industry')
                
                insights = await self.extract_insights_from_content(category, documents, company, user_role, industry)
                if insights:
                    all_insights.extend(insights)
                    msg.append(f"  ✓ Extracted {len(insights)} insights from {category} data")
                else:
                    msg.append(f"  ⚠️ No significant insights found in {category} data")

        # Create final structured insights
        if all_insights:
            structured_insights = await self.prioritize_insights(all_insights, company, user_role)
            state['strategic_insights'] = structured_insights
            msg.append(f"\n🎯 Generated {len(structured_insights['prioritized_insights'])} prioritized insights")
        else:
            msg.append("\n⚠️ No significant insights could be extracted from the data")
            state['strategic_insights'] = {
                "prioritized_insights": [],
                "insights_by_category": {},
                "executive_summary": "Insufficient data to generate meaningful insights.",
                "total_insights": 0,
                "categories_analyzed": [],
                "analysis_timestamp": datetime.utcnow().isoformat()
            }

        # Update messages
        messages = state.get('messages', [])
        messages.append(AIMessage(content="\n".join(msg)))
        state['messages'] = messages
        
        return state 