from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from tavily import AsyncTavilyClient

from ..agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


# Schema models for structured LLM outputs
class CompetitorNews(BaseModel):
    """Schema for competitor news item."""
    competitor: str = Field(description="Name of the competitor")
    title: str = Field(description="News title/headline")
    category: str = Field(description="News category: product_launch, funding, m_a, partnership, or other")
    summary: str = Field(description="Brief summary of the news")
    impact: str = Field(description="Strategic impact or significance")
    date: str = Field(description="Date in YYYY-MM-DD format")
    source: str = Field(description="Source URL or publication")
    confidence: float = Field(description="Confidence score between 0-1")


class CompetitorNewsArray(BaseModel):
    """Schema for competitor news extraction."""
    news_items: List[CompetitorNews] = Field(
        description="Array of competitor news items",
        max_length=50
    )


class CompetitorAnalystAgent(BaseAgent):
    """
    Competitor Analyst Agent - Analyzes news about competitors including product launches, 
    funding, M&A, and partnerships using Tavily crawl and industry blog searches.
    """
    
    def __init__(self, llm_model: str = "gpt-4o"):
        super().__init__(agent_type="competitor_analyst_agent")
        
        self.llm_model = llm_model
        self.temperature = 0.1
        self.rate_limit = 12  # Increased concurrent requests for faster processing
        self.days_back = 180  # Reduced to 6 months for more focused recent news
        
        if not os.getenv("TAVILY_API_KEY"):
            raise ValueError("TAVILY_API_KEY is not configured")
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is not configured")
            
        self.llm = ChatOpenAI(
            model=self.llm_model,
            temperature=self.temperature,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.tavily = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        self.sem = asyncio.Semaphore(self.rate_limit)
        
        # Focused trusted sources for faster processing
        self.trusted_sources = [
            "techcrunch.com", "venturebeat.com", "crunchbase.com", 
            "businesswire.com", "prnewswire.com", "reuters.com"
        ]

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution method for competitor analysis."""
        self.log_agent_start(state)
        company = state.get('company', 'Unknown Company')
        websocket_manager, job_id = self.get_websocket_info(state)
        
        try:
            # Extract competitors from state
            competitors = state.get("competitors", [])
            if not competitors:
                # Fallback to competitor_discovery data
                competitor_discovery = state.get("competitor_discovery", {})
                competitors = []
                for category in ["direct", "indirect", "emerging"]:
                    for comp in competitor_discovery.get(category, []):
                        competitors.append({
                            "name": comp.get("name", ""),
                            "category": comp.get("category", category)
                        })
            
            if not competitors:
                self.logger.warning("No competitors found in state")
                return state
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🔍 Starting competitor analysis for {len(competitors)} competitors",
                result={"step": "Competitor Analysis", "substep": "initialization", "competitors_count": len(competitors)}
            )
            
            # Analyze each competitor (process all competitors provided after user review)
            total_competitors_to_analyze = len(competitors)
            all_competitor_news = []

            # Limit can be applied for extremely large lists, but we default to analysing all to preserve
            # user-added competitors. To maintain reasonable runtimes we cap at 12, prioritising the first
            # 12 items. Adjust the cap via an environment variable if needed.

            max_competitors_env = os.getenv("MAX_COMPETITOR_ANALYSIS")
            try:
                max_competitors = int(max_competitors_env) if max_competitors_env else 12
            except ValueError:
                max_competitors = 12

            competitors_to_process = competitors[:max_competitors]

            for i, competitor in enumerate(competitors_to_process):
                competitor_name = competitor.get("name", "") if isinstance(competitor, dict) else str(competitor)
                if not competitor_name:
                    continue
                    
                await self.send_status_update(
                    websocket_manager, job_id,
                    status="processing",
                    message=f"📰 Analyzing competitor {i+1}/{min(total_competitors_to_analyze, max_competitors)}: {competitor_name}",
                    result={"step": "Competitor Analysis", "substep": "individual_analysis", "current_competitor": competitor_name}
                )
                
                competitor_news = await self._analyze_single_competitor(competitor_name, state)
                all_competitor_news.extend(competitor_news)
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🧠 Processing {len(all_competitor_news)} competitor news items",
                result={"step": "Competitor Analysis", "substep": "news_processing"}
            )
            
            # Store results in state
            state["competitor_analysis"] = {
                "news_items": [news.model_dump() for news in all_competitor_news],
                "analysis_date": datetime.now().isoformat(),
                "competitors_analyzed": len(competitors_to_process),
                "total_news_items": len(all_competitor_news)
            }
            
            # Add completion message
            completion_msg = f"✅ Analyzed {len(competitors_to_process)} competitors and found {len(all_competitor_news)} relevant news items"
            messages = state.get('messages', [])
            messages.append(AIMessage(content=completion_msg))
            state['messages'] = messages
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="completed",
                message=completion_msg,
                result={
                    "step": "Competitor Analysis",
                    "substep": "complete",
                    "competitors_analyzed": len(competitors_to_process),
                    "news_items_found": len(all_competitor_news),
                    "analysis": state["competitor_analysis"]
                }
            )
            
            return state
            
        except Exception as e:
            error_msg = f"❌ Competitor analysis failed: {str(e)}"
            self.logger.error(error_msg)
            await self.send_status_update(
                websocket_manager, job_id,
                status="error",
                message=error_msg,
                result={"step": "Competitor Analysis", "error": str(e)}
            )
            return state

    async def _analyze_single_competitor(self, competitor_name: str, state: Dict[str, Any]) -> List[CompetitorNews]:
        """Analyze a single competitor for news and strategic movements."""
        try:
            # Step 1: Website crawling
            website_data = await self._crawl_competitor_website(competitor_name)
            
            # Step 2: News search
            news_data = await self._search_competitor_news(competitor_name)
            
            # Step 3: Industry blog search
            blog_data = await self._search_industry_blogs(competitor_name, state)
            
            # Combine all data sources
            all_data = website_data + news_data + blog_data
            
            if not all_data:
                return []
            
            # Extract structured news using LLM
            competitor_news = await self._extract_competitor_news(competitor_name, all_data)
            return competitor_news
            
        except Exception as e:
            self.logger.error(f"Error analyzing competitor {competitor_name}: {e}")
            return []

    async def _crawl_competitor_website(self, competitor_name: str) -> List[Dict[str, Any]]:
        """Crawl competitor website for recent news and announcements."""
        try:
            async with self.sem:
                # Quick search for competitor website
                website_search = await self.tavily.search(
                    query=f'"{competitor_name}" official website',
                    max_results=2
                )
                
                if not website_search.get("results"):
                    return []
                
                # Get the first result as likely official website
                website_url = website_search["results"][0]["url"]
                
                # Fast, focused crawl - minimal depth and breadth
                crawl_result = await self.tavily.crawl(
                    url=website_url,
                    max_depth=1,  # Reduced from 2
                    max_breadth=5,  # Reduced from 15
                    limit=8,  # Reduced from 30
                    instructions="""Focus ONLY on: 1) Recent product launches, 2) M&A announcements, 
                    3) Partnership deals. Extract only factual information with dates from the last 6 months.""",
                    categories=["News", "Press"],  # Reduced categories
                    exclude_paths=["/careers/*", "/support/*", "/legal/*", "/blog/*"],
                    extract_depth="basic"  # Reduced from advanced
                )
                
                if crawl_result and crawl_result.get("results"):
                    return [{
                        "source": "website_crawl",
                        "url": website_url,
                        "content": result.get("content", ""),
                        "category": result.get("category", ""),
                        "reliability": 0.9
                    } for result in crawl_result["results"][:5] if result.get("content")]  # Limit results
                
                return []
                
        except Exception as e:
            self.logger.warning(f"Website crawl failed for {competitor_name}: {e}")
            return []

    async def _search_competitor_news(self, competitor_name: str) -> List[Dict[str, Any]]:
        """Search for competitor news focusing on product launches, M&A, and partnerships."""
        # Focused queries for only the three key areas
        current_year = datetime.now().year
        news_queries = [
            f'"{competitor_name}" product launch new product {current_year}',
            f'"{competitor_name}" acquisition merger M&A {current_year}',
            f'"{competitor_name}" partnership deal collaboration {current_year}'
        ]
        
        news_data = []
        for query in news_queries:
            try:
                async with self.sem:
                    results = await self.tavily.search(
                        query=query,
                        search_depth="basic",  # Reduced from advanced
                        max_results=3,  # Reduced from 5
                        include_domains=self.trusted_sources,
                        topic="news",
                        days=self.days_back,
                        include_answer=True
                    )
                    
                    if results and results.get("results"):
                        for result in results["results"]:
                            news_data.append({
                                "source": "news_search",
                                "content": result.get("content", ""),
                                "url": result.get("url", ""),
                                "title": result.get("title", ""),
                                "published_date": result.get("published_date", ""),
                                "query": query,
                                "reliability": 0.8
                            })
                            
            except Exception as e:
                self.logger.warning(f"News search failed for query '{query}': {e}")
                continue
        
        return news_data

    async def _search_industry_blogs(self, competitor_name: str, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Quick search of industry sources for competitor insights."""
        # Single focused query for speed
        try:
            async with self.sem:
                results = await self.tavily.search(
                    query=f'"{competitor_name}" product launch OR acquisition OR partnership',
                    search_depth="basic",
                    max_results=3,  # Reduced significantly
                    include_domains=["medium.com", "techcrunch.com"],  # Reduced domains
                    days=self.days_back,
                    include_answer=True
                )
                
                blog_data = []
                if results and results.get("results"):
                    for result in results["results"]:
                        blog_data.append({
                            "source": "industry_blog",
                            "content": result.get("content", ""),
                            "url": result.get("url", ""),
                            "title": result.get("title", ""),
                            "published_date": result.get("published_date", ""),
                            "reliability": 0.7
                        })
                
                return blog_data
                        
        except Exception as e:
            self.logger.warning(f"Blog search failed for {competitor_name}: {e}")
            return []

    async def _extract_competitor_news(self, competitor_name: str, data_sources: List[Dict[str, Any]]) -> List[CompetitorNews]:
        """Extract structured competitor news using focused LLM analysis."""
        if not data_sources:
            return []
        
        # Prepare content for LLM analysis - reduced limit for speed
        content_blocks = []
        for data in data_sources[:10]:  # Reduced from 20
            content = data.get("content", "")
            if content and len(content) > 50:
                content_blocks.append({
                    "source": data.get("source", ""),
                    "url": data.get("url", ""),
                    "content": content[:600],  # Reduced from 1000
                    "title": data.get("title", ""),
                    "date": data.get("published_date", "")
                })
        
        if not content_blocks:
            return []
        
        # Shorter, focused prompt
        prompt = f"""
        Analyze the data about "{competitor_name}" and extract ONLY significant news in these 3 categories:
        1. Product launches and major product updates
        2. M&A activity (acquisitions, mergers, being acquired)
        3. Strategic partnerships and collaborations

        Ignore: routine updates, marketing content, minor announcements, hiring news.

        Data sources:
        {json.dumps(content_blocks, indent=2)}

        Extract only factual, strategic news items with clear business impact.
        """
        
        try:
            llm_with_schema = self.llm.with_structured_output(CompetitorNewsArray)
            response = await llm_with_schema.ainvoke(prompt)
            return response.news_items
            
        except Exception as e:
            self.logger.error(f"LLM extraction failed for {competitor_name}: {e}")
            return [] 