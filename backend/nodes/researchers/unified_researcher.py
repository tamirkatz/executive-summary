import logging
from typing import Any, Dict, List

from langchain_core.messages import AIMessage

from ...classes import ResearchState
from .base import BaseResearcher

logger = logging.getLogger(__name__)

class UnifiedResearcher(BaseResearcher):
    def __init__(self) -> None:
        super().__init__()
        self.analyst_type = "unified_researcher"

    async def analyze(self, state: ResearchState) -> Dict[str, Any]:
        company = state.get('company', 'Unknown Company')
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')
        
        try:
            # Get categorized queries from collector agent
            categorized_queries = state.get('categorized_queries', {})
            
            if not categorized_queries:
                logger.warning(f"No categorized queries found for {company}")
                # Fallback to generating basic queries if no categorized queries available
                categorized_queries = await self._generate_fallback_queries(state, company)
            
            # Add message to show categorized queries
            queries_msg = "🔍 Categorized queries for unified research:\n"
            for category, queries in categorized_queries.items():
                if queries:
                    queries_msg += f"\n• {category.title()}: {len(queries)} queries"
                    for query in queries[:3]:  # Show first 3 queries per category
                        queries_msg += f"\n  - {query}"
                    if len(queries) > 3:
                        queries_msg += f"\n  ... and {len(queries) - 3} more"
            
            messages = state.get('messages', [])
            messages.append(AIMessage(content=queries_msg))
            state['messages'] = messages

            # Send initial status through WebSocket
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message="Unified research queries prepared",
                    result={
                        "step": "Unified Researcher",
                        "analyst_type": "Unified Researcher",
                        "categories": list(categorized_queries.keys()),
                        "total_queries": sum(len(queries) for queries in categorized_queries.values())
                    }
                )
            
            # Initialize data containers
            financial_data = {}
            news_data = {}
            company_data = {}
            competitor_data = {}  # NEW: Dedicated competitor data collection
            
            # Process site scrape data if available
            if site_scrape := state.get('site_scrape'):
                company_url = state.get('company_url', 'company-website')
                site_doc = {
                    'title': state.get('company', 'Unknown Company'),
                    'raw_content': site_scrape,
                    'query': f'Company information on {company}',
                    'url': company_url,
                    'source': 'site_scrape',
                    'score': 1.0  # High score for site scrape data
                }
                
                # Add to all categories since site scrape is comprehensive
                financial_data[company_url] = site_doc
                news_data[company_url] = site_doc
                company_data[company_url] = site_doc

            # Process queries by category with COMPETITOR PRIORITY
            category_mapping = {
                'financial': financial_data,
                'news': news_data,
                'company': company_data,
                'technology': company_data,  # Technology queries go to company data
                'market': company_data,      # Market queries go to company data
                'competitor': competitor_data,  # ENHANCED: Dedicated competitor data
                'partnership': news_data,    # Partnership queries go to news (often news)
                'regulatory': news_data,     # Regulatory queries go to news (often news)
                'geopolitical': company_data, # Geopolitical queries go to company data
                'risk': company_data,        # Risk queries go to company data
                'opportunity': company_data, # Opportunity queries go to company data
                'general': company_data      # General queries go to company data
            }

            # STEP 1: Process COMPETITOR queries FIRST (highest priority)
            competitor_queries = categorized_queries.get('competitor', [])
            if competitor_queries:
                if websocket_manager and job_id:
                    await websocket_manager.send_status_update(
                        job_id=job_id,
                        status="processing",
                        message=f"🎯 PRIORITY: Processing {len(competitor_queries)} competitor intelligence queries",
                        result={
                            "step": "Unified Researcher",
                            "category": "competitor",
                            "query_count": len(competitor_queries),
                            "priority": "HIGH"
                        }
                    )
                
                # Use specialized competitor search strategy
                self.analyst_type = "competitor_analyst"
                try:
                    competitor_documents = await self.search_documents_competitor_focused(state, competitor_queries)
                    for url, doc in competitor_documents.items():
                        doc['query'] = f"competitor: {doc.get('query', '')}"
                        doc['priority'] = 'high'
                        competitor_data[url] = doc
                        # Also add to news data for broader analysis
                        news_data[url] = doc
                finally:
                    self.analyst_type = "unified_researcher"

            # STEP 2: Process each remaining category
            for category, queries in categorized_queries.items():
                if not queries or category == 'competitor':  # Skip empty or already processed
                    continue
                
                target_data = category_mapping.get(category, company_data)
                
                # Send status update for category processing
                if websocket_manager and job_id:
                    await websocket_manager.send_status_update(
                        job_id=job_id,
                        status="processing",
                        message=f"Processing {category} queries",
                        result={
                            "step": "Unified Researcher",
                            "category": category,
                            "query_count": len(queries)
                        }
                    )
                
                # Set appropriate analyst type for search parameters
                original_analyst_type = self.analyst_type
                if category == 'financial':
                    self.analyst_type = "financial_analyst"
                elif category == 'news':
                    self.analyst_type = "news_analyst"
                elif category == 'partnership':
                    self.analyst_type = "news_analyst"  # Partnerships are often news
                elif category == 'regulatory':
                    self.analyst_type = "news_analyst"  # Regulatory changes are often news
                else:
                    self.analyst_type = "company_analyst"
                
                try:
                    # Search documents for this category
                    documents = await self.search_documents(state, queries)
                    
                    # Add documents to appropriate data container
                    for url, doc in documents.items():
                        doc['query'] = f"{category}: {doc.get('query', '')}"
                        target_data[url] = doc
                finally:
                    # Restore original analyst type
                    self.analyst_type = original_analyst_type

            # Send completion status with competitor focus
            total_competitor_docs = len(competitor_data)
            completion_msg = f"✅ Unified research complete: {total_competitor_docs} competitor docs, {len(financial_data)} financial, {len(news_data)} news, {len(company_data)} company documents"
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message=completion_msg,
                    result={
                        "step": "Unified Researcher",
                        "analyst_type": "Unified Researcher",
                        "competitor_documents": total_competitor_docs,
                        "financial_documents": len(financial_data),
                        "news_documents": len(news_data),
                        "company_documents": len(company_data),
                        "total_documents": total_competitor_docs + len(financial_data) + len(news_data) + len(company_data),
                        "competitor_priority": True
                    }
                )
            
            # Update state with competitor priority
            messages.append(AIMessage(content=completion_msg))
            state['messages'] = messages
            state['financial_data'] = financial_data
            state['news_data'] = news_data
            state['company_data'] = company_data
            state['competitor_data'] = competitor_data  # NEW: Store competitor data separately

            return {
                'message': completion_msg,
                'financial_data': financial_data,
                'news_data': news_data,
                'company_data': company_data,
                'competitor_data': competitor_data,  # NEW: Return competitor data
                'analyst_type': self.analyst_type,
                'categorized_queries': categorized_queries,
                'competitor_focus': True
            }

        except Exception as e:
            error_msg = f"Unified research failed: {str(e)}"
            logger.error(error_msg)
            
            # Send error status
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="error",
                    message=error_msg,
                    result={
                        "analyst_type": "Unified Researcher",
                        "error": str(e)
                    }
                )
            raise  # Re-raise to maintain error flow

    async def _generate_fallback_queries(self, state: ResearchState, company: str) -> Dict[str, List[str]]:
        """Generate fallback queries if no categorized queries are available."""
        logger.info(f"Generating fallback queries for {company}")
        
        # Generate basic queries for each category
        financial_queries = await self.generate_queries(state, f"""
Generate queries on the financial analysis of {company} such as:

- Funding rounds and investors
- Revenue and financial performance
- Valuation and market cap
- Financial partnerships
- Investment activities
""")

        news_queries = await self.generate_queries(state, f"""
Generate queries on the recent news coverage of {company} such as:

- Recent company announcements
- Press releases
- New partnerships
- Media coverage
- Industry news
""")

        company_queries = await self.generate_queries(state, f"""
Generate queries on the company fundamentals of {company} such as:

- Company overview and mission
- Product/service offerings
- Leadership team and structure
- Company history and milestones
- Business model and strategy
""")

        return {
            'financial': financial_queries,
            'news': news_queries,
            'company': company_queries
        }

    async def search_documents_competitor_focused(self, state: ResearchState, queries: List[str]) -> Dict[str, Any]:
        """Specialized search method optimized for competitor intelligence with focus on recent launches and news."""
        competitor_documents = {}
        
        for query in queries[:15]:  # Focus on top 15 competitor queries for quality
            try:
                # Enhanced search parameters for competitor intelligence
                search_params = {
                    "query": query,
                    "search_depth": "advanced",  # Deeper search for competitor intelligence
                    "max_results": 8,            # More results per query for competitor research
                    "include_domains": [
                        "techcrunch.com", "venturebeat.com", "businesswire.com",
                        "prnewswire.com", "bloomberg.com", "reuters.com",
                        "cnbc.com", "forbes.com", "crunchbase.com"
                    ],
                    "topic": "news",             # Focus on news for latest developments
                    "days": 180,                 # Look for news in last 6 months
                    "include_answer": True       # Get comprehensive answers
                }
                
                # Execute Tavily search with competitor-optimized parameters
                result = await self.tavily_client.search(**search_params)
                
                if result and result.get('results'):
                    for item in result['results']:
                        url = item.get('url', '')
                        if url and url not in competitor_documents:
                            # Enhanced document scoring for competitor content
                            score = item.get('score', 0.5)
                            
                            # Boost score for competitor-specific indicators
                            title = item.get('title', '').lower()
                            content = item.get('content', '').lower()
                            
                            # Boost for launch/partnership keywords
                            if any(keyword in title or keyword in content for keyword in [
                                'launch', 'announces', 'partnership', 'integration', 
                                'funding', 'acquisition', 'expand', 'new product',
                                'platform', 'api', 'developer', 'strategic'
                            ]):
                                score += 0.3
                            
                            # Boost for recent dates
                            published_date = item.get('published_date', '')
                            if '2024' in published_date:
                                score += 0.2
                            
                            competitor_documents[url] = {
                                'title': item.get('title', ''),
                                'snippet': item.get('content', ''),
                                'published_date': published_date,
                                'score': min(score, 1.0),  # Cap at 1.0
                                'source': 'competitor_intelligence',
                                'query': query,
                                'url': url,
                                'domain': item.get('url', '').split('/')[2] if '/' in item.get('url', '') else 'unknown'
                            }
                            
            except Exception as e:
                logger.error(f"Error in competitor search for query '{query}': {e}")
                continue
        
        return competitor_documents

    async def run(self, state: ResearchState) -> Dict[str, Any]:
        return await self.analyze(state) 