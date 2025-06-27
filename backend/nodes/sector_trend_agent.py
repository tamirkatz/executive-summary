from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import urlparse

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from tavily import AsyncTavilyClient
from pydantic import BaseModel, Field

from ..agents.base_agent import BaseAgent
from ..classes.state import ResearchState
from ..config import config
from ..models import TrendInfo

logger = logging.getLogger(__name__)


# Schema models for structured LLM outputs
class SeedList(BaseModel):
    """Schema for seed generation."""
    seeds: List[str] = Field(
        description="Micro-domain or technology keywords (2-4 words each)",
        max_length=5
    )


class TrendData(BaseModel):
    """Schema for individual trend data."""
    trend: str = Field(description="One-sentence description of the trend")
    evidence: str = Field(description="URL or source providing evidence")
    impact: str = Field(description="Why this matters for SaaS/AI builders")
    date: str = Field(description="Date in YYYY-MM format")
    confidence: float = Field(description="Confidence score between 0-1")


class TrendArray(BaseModel):
    """Schema for trend extraction."""
    trends: List[TrendData] = Field(
        description="Array of extracted trends",
        max_length=15
    )


class SectorTrendAgent(BaseAgent):
    """
    Enhanced Sector Trend Agent v3 - Dynamic, company-agnostic seed generation
    
    Features:
    - Dynamic seed generation via GPT-4o structured output
    - Embedding-based relevance filtering
    - Trusted domain filtering
    - Rate-limited concurrent searches
    - WebSocket status updates
    """
    
    def __init__(self, llm_model: str = "gpt-4o"):
        super().__init__(agent_type="sector_trend_agent")
        
        self.llm_model = llm_model
        self.temperature = 0.1
        self.rate_limit = 6  # Tavily concurrent requests
        self.days_back = 180  # Search recency window
        
        if not config.TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY is not configured")
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
            
        self.llm = ChatOpenAI(
            model=self.llm_model,
            temperature=self.temperature,
            api_key=config.OPENAI_API_KEY
        )
        self.embedding = OpenAIEmbeddings(api_key=config.OPENAI_API_KEY)
        self.tavily = AsyncTavilyClient(api_key=config.TAVILY_API_KEY)
        self.sem = asyncio.Semaphore(self.rate_limit)
        
        # Enhanced trusted domains for quality sources
        self.trusted_domains = [
            "techcrunch.com", "crunchbase.com", "forrester.com", "gartner.com",
            "cbinsights.com", "europa.eu", "sec.gov",
            "a16z.com", "future.a16z.com", "sequoiacap.com",
            "huggingface.co", "towardsdatascience.com", "ruder.io",
            "mckinsey.com", "bcg.com", "bain.com", "pwc.com", "deloitte.com"
        ]
    
    async def run(self, state: ResearchState) -> ResearchState:
        """Main execution method for sector trend collection."""
        self.log_agent_start(state)
        company = state.get('company', 'Unknown Company')
        websocket_manager, job_id = self.get_websocket_info(state)
        
        try:
            # Extract profile from state
            profile = state.get("profile", {})
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"📈 Starting sector trend analysis for {company}",
                result={"step": "Sector Trend Analysis", "substep": "initialization"}
            )
            
            # Generate dynamic seeds using LLM
            seeds = await self._generate_sector_seeds(profile)
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🔍 Generated {len(seeds)} specialized keywords for trend discovery",
                result={"step": "Sector Trend Analysis", "substep": "seed_generation", "seeds": seeds}
            )
            
            # Generate targeted queries
            queries = self._generate_queries(profile, seeds)
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🌐 Searching {len(queries)} trend queries across trusted sources",
                result={"step": "Sector Trend Analysis", "substep": "search", "query_count": len(queries)}
            )
            
            # Concurrent search with rate limiting
            docs = await self._search(queries)
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🧠 Analyzing {len(docs)} documents for valuable trend insights",
                result={"step": "Sector Trend Analysis", "substep": "extraction", "docs_count": len(docs)}
            )
            
            # Extract trends using structured LLM output
            raw_trends = await self._llm_extract(profile, docs)
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message="⚖️ Filtering trends by relevance and confidence",
                result={"step": "Sector Trend Analysis", "substep": "filtering"}
            )
            
            # Post-filter using embedding similarity
            filtered_trends = await self._postfilter(profile, raw_trends)
            
            # Update state with trend data
            state['sector_trends'] = [trend.model_dump() for trend in filtered_trends]
            
            # Add completion message
            completion_msg = f"✅ Collected {len(filtered_trends)} high-quality sector trends for {company}"
            messages = state.get('messages', [])
            messages.append(AIMessage(content=completion_msg))
            state['messages'] = messages
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="completed",
                message=completion_msg,
                result={
                    "step": "Sector Trend Analysis",
                    "substep": "complete",
                    "trends_count": len(filtered_trends),
                    "trends": [trend.model_dump() for trend in filtered_trends]
                }
            )
            
            return state
            
        except Exception as e:
            error_msg = f"❌ Sector trend analysis failed: {str(e)}"
            self.logger.error(error_msg)
            await self.send_status_update(
                websocket_manager, job_id,
                status="error",
                message=error_msg,
                result={"step": "Sector Trend Analysis", "error": str(e)}
            )
            return state

    # --------------------------------- PHASE 1: DYNAMIC SEED GENERATION ---------------------------------

    async def _generate_sector_seeds(self, profile: Dict[str, Any]) -> List[str]:
        """LLM proposes up to 5 specialized keywords for trend hunting."""
        
        context = {
            "sector": profile.get("sector", ""),
            "industry": profile.get("industry", ""),
            "core_products": profile.get("core_products", [])[:3],
            "synonyms": profile.get("synonyms", [])[:3],
            "description": profile.get("description", "")[:500]
        }
        
        prompt = (
            "You are an industry analyst. Given the company profile below, identify up to 5 *specialized* "
            "keywords that capture its micro-domain, relevant sub-technologies, or adjacent tooling.\n"
            "Avoid generic buzzwords (e.g., 'AI', 'technology', 'software').\n"
            "Focus on specific technologies, methodologies, or market segments.\n"
            f"PROFILE: {json.dumps(context)}"
        )
        
        try:
            llm_with_schema = self.llm.with_structured_output(SeedList)
            response = await llm_with_schema.ainvoke(prompt)
            seeds = response.seeds
            
            # Validate and clean seeds
            valid_seeds = [s.strip() for s in seeds if len(s.strip()) > 2 and len(s.strip()) < 50]
            return valid_seeds[:5]
            
        except Exception as e:
            self.logger.warning(f"Seed generation failed, using fallback: {e}")
            # Fallback to core products and synonyms
            fallback = profile.get("core_products", []) + profile.get("synonyms", [])
            return [item for item in fallback if item][:5]

    # --------------------------------- PHASE 2: QUERY GENERATION ---------------------------------

    def _generate_queries(self, profile: Dict[str, Any], seeds: List[str]) -> List[str]:
        """Generate targeted trend queries using sector and dynamic seeds."""
        
        sector = profile.get("sector", "technology")
        
        # Base sector queries
        base_queries = [
            f"{sector} market trends 2025",
            f"{sector} industry outlook 2025"
        ]
        
        # Dynamic seed-based queries
        seed_queries = []
        for seed in seeds:
            seed_queries.extend([
                f"{seed} adoption trends 2025",
                f"{seed} funding analysis 2025"
            ])
        
        all_queries = base_queries + seed_queries
        return all_queries[:10]  # Limit to 10 queries

    # --------------------------------- PHASE 3: CONCURRENT SEARCH ---------------------------------

    async def _search(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Execute concurrent searches with rate limiting and deduplication."""
        
        async def _one_search(query: str) -> List[Dict[str, Any]]:
            async with self.sem:
                try:
                    result = await self.tavily.search(
                        query=query,
                        max_results=5,
                        include_answer=True,
                        include_domains=self.trusted_domains,
                        days=self.days_back
                    )
                    return [r for r in result.get("results", []) if self._is_trusted(r["url"])]
                except Exception as e:
                    self.logger.warning(f"Search failed for query '{query}': {e}")
                    return []
        
        # Execute all searches concurrently
        tasks = [_one_search(q) for q in queries]
        results = await asyncio.gather(*tasks)
        
        # Flatten and deduplicate by URL
        seen_urls = set()
        docs = []
        for batch in results:
            for doc in batch:
                url = doc.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    docs.append(doc)
        
        return docs

    def _is_trusted(self, url: str) -> bool:
        """Check if URL is from a trusted domain."""
        domain = urlparse(url).netloc.lower()
        return any(trusted_domain in domain for trusted_domain in self.trusted_domains)

    # --------------------------------- PHASE 4: STRUCTURED EXTRACTION ---------------------------------

    async def _llm_extract(self, profile: Dict[str, Any], docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract trends using structured LLM output."""
        
        if not docs:
            return []
        
        # Prepare content chunks
        chunks = []
        for doc in docs[:25]:  # Limit to prevent token overflow
            content = doc.get("content", "")
            url = doc.get("url", "")
            title = doc.get("title", "")
            
            if content and url:
                chunk = f"URL: {url}\nTITLE: {title}\nCONTENT: {content[:800]}"
                chunks.append(chunk)
        
        joined_content = "\n---\n".join(chunks)
        sector = profile.get("sector", "technology")
        
        prompt = (
            f"You are an industry analyst specializing in {sector} trends. "
            "Extract macro-level trends relevant to companies in this sector from the provided content. "
            "Focus on trends with concrete evidence and strategic impact for SaaS/AI builders. "
            "Include only trends with high confidence and concrete supporting evidence."
        )
        
        try:
            llm_with_schema = self.llm.with_structured_output(TrendArray)
            response = await llm_with_schema.ainvoke(
                f"{prompt}\n\nCONTENT:\n{joined_content}"
            )
            # Convert TrendData objects to dictionaries
            return [trend.model_dump() for trend in response.trends]
            
        except Exception as e:
            self.logger.error(f"Failed to extract trends via structured output: {e}")
            return []

    # --------------------------------- PHASE 5: RELEVANCE FILTERING ---------------------------------

    async def _postfilter(self, profile: Dict[str, Any], raw_trends: List[Dict[str, Any]]) -> List[TrendInfo]:
        """Filter trends using embedding similarity and confidence thresholds."""
        
        if not raw_trends:
            return []
        
        # Get embedding for company description
        description = profile.get("description", profile.get("company", ""))
        if not description:
            # Fallback: use sector and core products
            description = f"{profile.get('sector', '')} {' '.join(profile.get('core_products', []))}"
        
        try:
            desc_vector = await self.embedding.aembed_query(description[:512])
        except Exception as e:
            self.logger.warning(f"Failed to generate embedding: {e}")
            desc_vector = None
        
        processed_trends = []
        
        for trend_data in raw_trends:
            try:
                # Extract required fields with defaults
                trend_text = trend_data.get("trend", "")
                evidence_url = trend_data.get("evidence", "")
                impact_text = trend_data.get("impact", "")
                date_str = trend_data.get("date", datetime.now().strftime('%Y-%m'))
                confidence = float(trend_data.get("confidence", 0.5))
                
                # Validate URL format
                if not evidence_url.startswith(('http://', 'https://')):
                    self.logger.warning(f"Invalid URL format: {evidence_url}")
                    continue
                
                # Skip trends with missing essential data
                if not trend_text or not evidence_url or confidence < 0.6:
                    continue
                
                # Calculate relevance using embedding similarity
                relevance = 0.5  # Default relevance
                if desc_vector:
                    try:
                        trend_vector = await self.embedding.aembed_query(f"{trend_text} {impact_text}"[:512])
                        relevance = self._cosine_similarity(desc_vector, trend_vector)
                    except Exception as e:
                        self.logger.warning(f"Failed to calculate relevance: {e}")
                
                # Apply relevance threshold
                if relevance >= 0.55:
                    trend = TrendInfo(
                        trend=trend_text,
                        evidence=evidence_url,
                        impact=impact_text,
                        date=date_str,
                        source_domain=urlparse(evidence_url).netloc,
                        confidence_score=round(confidence, 2)
                    )
                    
                    # Add relevance score for sorting
                    trend_dict = trend.model_dump()
                    trend_dict["relevance"] = round(relevance, 2)
                    processed_trends.append(TrendInfo(**trend_dict))
                    
            except Exception as e:
                self.logger.warning(f"Failed to process trend: {e}")
                continue
        
        # Sort by combined relevance and confidence score
        processed_trends.sort(
            key=lambda x: (x.confidence_score + getattr(x, 'relevance', 0.5)) / 2,
            reverse=True
        )
        
        return processed_trends[:10]  # Return top 10 trends

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        
        return dot_product / (norm_a * norm_b + 1e-8) 