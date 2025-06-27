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
        self.rate_limit = 8  # Tavily concurrent requests
        self.days_back = 365  # Search news from last year
        
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
        
        # Trusted sources for competitor intelligence
        self.trusted_sources = [
            "techcrunch.com", "venturebeat.com", "crunchbase.com", "pitchbook.com",
            "bloomberg.com", "reuters.com", "businesswire.com", "prnewswire.com",
            "forbes.com", "cnbc.com", "businessinsider.com", "yahoo.com",
            "theverge.com", "wired.com", "arstechnica.com", "zdnet.com",
            "sec.gov", "marketwatch.com", "fool.com"
        ]
        
        # Industry blog domains for sector-specific insights
        self.industry_blogs = [
            "a16z.com", "future.a16z.com", "sequoiacap.com", "medium.com",
            "substack.com", "techcrunch.com", "venturebeat.com",
            "ben-evans.com", "stratechery.com", "nextbigwhat.com",
            "saastr.com", "firstround.com", "bothsides.substack.com"
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
            
            # Analyze each competitor
            all_competitor_news = []
            for i, competitor in enumerate(competitors[:10]):  # Limit to top 10 competitors
                competitor_name = competitor.get("name", "") if isinstance(competitor, dict) else str(competitor)
                if not competitor_name:
                    continue
                    
                await self.send_status_update(
                    websocket_manager, job_id,
                    status="processing",
                    message=f"📰 Analyzing competitor {i+1}/{min(len(competitors), 10)}: {competitor_name}",
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
                "competitors_analyzed": min(len(competitors), 10),
                "total_news_items": len(all_competitor_news)
            }
            
            # Add completion message
            completion_msg = f"✅ Analyzed {min(len(competitors), 10)} competitors and found {len(all_competitor_news)} relevant news items"
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
                    "competitors_analyzed": min(len(competitors), 10),
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
                # First, try to find the competitor's website
                website_search = await self.tavily.search(
                    query=f'"{competitor_name}" official website',
                    max_results=3
                )
                
                if not website_search.get("results"):
                    return []
                
                # Get the first result as likely official website
                website_url = website_search["results"][0]["url"]
                
                # Crawl the website with specific focus on news sections
                crawl_result = await self.tavily.crawl(
                    url=website_url,
                    max_depth=2,
                    max_breadth=15,
                    limit=30,
                    instructions="""Extract recent news, announcements, press releases, product launches, 
                    funding announcements, partnership news, and strategic updates. Focus on factual 
                    information with dates. Prioritize: 1) Product launches and updates, 2) Funding 
                    and investment news, 3) Partnership announcements, 4) Acquisition news, 
                    5) Executive changes and hiring.""",
                    categories=["News", "Press", "Blog", "About", "Investors"],
                    exclude_paths=["/careers/*", "/support/*", "/legal/*"],
                    extract_depth="advanced"
                )
                
                if crawl_result and crawl_result.get("results"):
                    return [{
                        "source": "website_crawl",
                        "url": website_url,
                        "content": result.get("content", ""),
                        "category": result.get("category", ""),
                        "reliability": 0.9
                    } for result in crawl_result["results"] if result.get("content")]
                
                return []
                
        except Exception as e:
            self.logger.warning(f"Website crawl failed for {competitor_name}: {e}")
            return []

    async def _search_competitor_news(self, competitor_name: str) -> List[Dict[str, Any]]:
        """Search for competitor news across trusted sources."""
        news_queries = [
            f'"{competitor_name}" product launch 2024',
            f'"{competitor_name}" funding round investment 2024',
            f'"{competitor_name}" partnership announcement 2024',
            f'"{competitor_name}" acquisition merger 2024',
            f'"{competitor_name}" strategic announcement 2024',
            f'"{competitor_name}" executive hire CEO CTO 2024'
        ]
        
        news_data = []
        for query in news_queries:
            try:
                async with self.sem:
                    results = await self.tavily.search(
                        query=query,
                        search_depth="advanced",
                        max_results=5,
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
        """Search industry blogs and thought leadership for competitor insights."""
        profile = state.get("profile", {})
        sector = profile.get("sector", "")
        
        blog_queries = [
            f'"{competitor_name}" industry analysis {sector}',
            f'"{competitor_name}" market position competition',
            f'"{competitor_name}" startup ecosystem trends',
            f'site:medium.com "{competitor_name}" strategy',
            f'site:substack.com "{competitor_name}" analysis'
        ]
        
        blog_data = []
        for query in blog_queries:
            try:
                async with self.sem:
                    results = await self.tavily.search(
                        query=query,
                        search_depth="basic",
                        max_results=4,
                        include_domains=self.industry_blogs,
                        days=self.days_back,
                        include_answer=True
                    )
                    
                    if results and results.get("results"):
                        for result in results["results"]:
                            blog_data.append({
                                "source": "industry_blog",
                                "content": result.get("content", ""),
                                "url": result.get("url", ""),
                                "title": result.get("title", ""),
                                "published_date": result.get("published_date", ""),
                                "query": query,
                                "reliability": 0.7
                            })
                            
            except Exception as e:
                self.logger.warning(f"Blog search failed for query '{query}': {e}")
                continue
        
        return blog_data

    async def _extract_competitor_news(self, competitor_name: str, data_sources: List[Dict[str, Any]]) -> List[CompetitorNews]:
        """Extract structured competitor news using LLM analysis."""
        if not data_sources:
            return []
        
        # Prepare content for LLM analysis
        content_blocks = []
        for data in data_sources[:20]:  # Limit to prevent token overflow
            content = data.get("content", "")
            if content and len(content) > 50:  # Filter out very short content
                content_blocks.append({
                    "source": data.get("source", ""),
                    "url": data.get("url", ""),
                    "content": content[:1000],  # Truncate to prevent token overflow
                    "title": data.get("title", ""),
                    "date": data.get("published_date", "")
                })
        
        if not content_blocks:
            return []
        
        prompt = f"""
        You are an expert competitive intelligence analyst. Analyze the provided data sources about "{competitor_name}" 
        and extract significant news items focusing on:

        1. Product launches and major updates
        2. Funding rounds, investments, and M&A activity
        3. Strategic partnerships and integrations
        4. Executive changes and key hires
        5. Market expansion and business model changes

        Focus on factual, strategic information that would be relevant for competitive analysis. 
        Ignore routine marketing content, minor updates, or promotional material.

        Data sources to analyze:
        {json.dumps(content_blocks, indent=2)}

        Extract only significant, factual news items with clear strategic implications.
        """
        
        try:
            llm_with_schema = self.llm.with_structured_output(CompetitorNewsArray)
            response = await llm_with_schema.ainvoke(prompt)
            return response.news_items
            
        except Exception as e:
            self.logger.error(f"LLM extraction failed for {competitor_name}: {e}")
            return [] 