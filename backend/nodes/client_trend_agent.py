from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
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
class ClientIndustryList(BaseModel):
    """Schema for client industry identification."""
    industries: List[str] = Field(
        description="Primary industries where the company's clients operate",
        max_length=6
    )
    rationale: str = Field(
        description="Brief explanation of why these are the main client industries"
    )


class ClientTrendData(BaseModel):
    """Schema for individual client industry trend data."""
    trend: str = Field(description="One-sentence description of the client industry trend")
    evidence: str = Field(description="URL or source providing evidence")
    impact: str = Field(description="Why this client trend matters for the company's business")
    client_industry: str = Field(description="Which client industry this trend affects")
    date: str = Field(description="Date in YYYY-MM format")
    confidence: float = Field(description="Confidence score between 0-1")
    disruption_score: float = Field(description="AI-assessed disruption potential score between 0-1, considering company relevance")
    business_relevance: str = Field(description="Specific explanation of how this trend could impact the company's business strategy")


class ClientTrendArray(BaseModel):
    """Schema for client trend extraction."""
    trends: List[ClientTrendData] = Field(
        description="Array of extracted client industry trends",
        max_length=15
    )


class TrendRelevanceReview(BaseModel):
    """Schema for AI review of trend relevance."""
    relevant_trends: List[int] = Field(
        description="Indices of trends that are genuinely interesting and relevant for the company"
    )
    reasoning: str = Field(
        description="Brief explanation of the filtering criteria applied"
    )


class ClientTrendAgent(BaseAgent):
    """
    Enhanced Client Trend Agent v2 - Disruptive & Future-Shaping Trend Discovery
    
    This agent focuses on identifying DISRUPTIVE and FUTURE-SHAPING trends in client
    industries by leveraging comprehensive data from earlier workflow stages including
    competitor intelligence, known clients, and partnership networks.
    
    Enhanced Features:
    - Leverages competitor data and ecosystem intelligence
    - Uses known clients and partners for contextualized search
    - Focuses specifically on disruptive/transformative trends
    - Multi-layer AI review for trend impact assessment
    - Strategic opportunity identification
    - Future market shift prediction
    """
    
    def __init__(self, llm_model: str = "gpt-4o"):
        super().__init__(agent_type="client_trend_agent")
        
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
        
        # Enhanced trusted domains focusing on disruptive trends and innovation
        self.trusted_domains = [
            # Innovation & Disruption Focus
            "techcrunch.com", "crunchbase.com", "venturebeat.com", "theinformation.com",
            "stratechery.com", "a16z.com", "future.a16z.com", "sequoiacap.com",
            "cbinsights.com", "pitchbook.com", "bloomberg.com", "reuters.com",
            
            # Research & Analysis
            "forrester.com", "gartner.com", "mckinsey.com", "bcg.com", "bain.com", 
            "pwc.com", "deloitte.com", "accenture.com", "kpmg.com",
            
            # Industry-Specific Innovation
            "retaildive.com", "emarketer.com", "statista.com", "mobilemarketingwatch.com",
            "digiday.com", "marketingland.com", "adage.com", "campaignlive.com",
            
            # AI & Technology Disruption
            "huggingface.co", "towardsdatascience.com", "ruder.io", "openai.com",
            "anthropic.com", "deepmind.com", "nvidia.com", "arxiv.org",
            
            # Government & Regulatory (disruption drivers)
            "europa.eu", "sec.gov", "ftc.gov", "whitehouse.gov"
        ]
    
    async def run(self, state: ResearchState) -> ResearchState:
        """Main execution method for client trend collection."""
        self.log_agent_start(state)
        company = state.get('company', 'Unknown Company')
        websocket_manager, job_id = self.get_websocket_info(state)
        
        try:
            # Extract comprehensive data from all previous workflow stages
            profile = state.get("profile", {})
            competitor_data = state.get("competitor_data", {})
            sector_trends = state.get("sector_trends", [])
            
            # Extract ecosystem intelligence
            competitors = competitor_data.get("competitors", [])
            ecosystem_context = {
                "profile": profile,
                "competitors": competitors[:10],  # Top 10 competitors for context
                "sector_trends_count": len(sector_trends)
            }
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🎯 Starting DISRUPTIVE client trend analysis for {company} (leveraging {len(competitors)} competitors + {len(sector_trends)} sector trends)",
                result={"step": "Client Trend Analysis", "substep": "initialization", "ecosystem_data": ecosystem_context}
            )
            
            # Identify client industries using LLM
            client_industries = await self._identify_client_industries(profile)
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🏭 Identified {len(client_industries['industries'])} client industries: {', '.join(client_industries['industries'])}",
                result={"step": "Client Trend Analysis", "substep": "industry_identification", "industries": client_industries}
            )
            
            # Generate DISRUPTIVE client industry queries using ecosystem intelligence
            queries = self._generate_disruptive_client_queries(
                client_industries['industries'], 
                profile, 
                competitors,
                sector_trends
            )
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🔍 Searching {len(queries)} client industry trend queries",
                result={"step": "Client Trend Analysis", "substep": "search", "query_count": len(queries)}
            )
            
            # Concurrent search with rate limiting
            docs = await self._search(queries)
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"📊 Analyzing {len(docs)} documents for client industry trends",
                result={"step": "Client Trend Analysis", "substep": "extraction", "docs_count": len(docs)}
            )
            
            # Extract DISRUPTIVE trends using enhanced ecosystem intelligence
            raw_trends = await self._llm_extract_disruptive_client_trends(
                profile, client_industries, docs, competitors, sector_trends
            )
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message="🧠 AI reviewing trends for business relevance",
                result={"step": "Client Trend Analysis", "substep": "ai_review"}
            )
            
            # AI review for relevance
            reviewed_trends = await self._ai_review_trends(profile, raw_trends)
            
            # Final filtering using embedding similarity
            filtered_trends = await self._postfilter_client_trends(profile, reviewed_trends)
            
            # Update state with client trend data
            state['client_trends'] = [trend.model_dump() for trend in filtered_trends]
            
            # Add completion message
            completion_msg = f"✅ Collected {len(filtered_trends)} relevant client industry trends for {company}"
            messages = state.get('messages', [])
            messages.append(AIMessage(content=completion_msg))
            state['messages'] = messages
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="completed",
                message=completion_msg,
                result={
                    "step": "Client Trend Analysis",
                    "substep": "complete",
                    "trends_count": len(filtered_trends),
                    "client_industries": client_industries['industries'],
                    "trends": [trend.model_dump() for trend in filtered_trends]
                }
            )
            
            return state
            
        except Exception as e:
            error_msg = f"❌ Client trend analysis failed: {str(e)}"
            self.logger.error(error_msg)
            await self.send_status_update(
                websocket_manager, job_id,
                status="error",
                message=error_msg,
                result={"step": "Client Trend Analysis", "error": str(e)}
            )
            return state

    # --------------------------------- PHASE 1: CLIENT INDUSTRY IDENTIFICATION ---------------------------------

    async def _identify_client_industries(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced client industry identification using ALL available workflow data."""
        
        context = {
            "company": profile.get("company", ""),
            "description": profile.get("description", ""),
            "sector": profile.get("sector", ""),
            "industry": profile.get("industry", ""),
            "core_products": profile.get("core_products", []),
            "customer_segments": profile.get("customer_segments", []),
            "known_clients": profile.get("known_clients", []),
            "partners": profile.get("partners", []),
            "use_cases": profile.get("use_cases", []),
            "business_model": profile.get("business_model", ""),
            "synonyms": profile.get("synonyms", [])
        }
        
        prompt = (
            "You are a strategic business analyst specializing in identifying DISRUPTIVE client industry trends. "
            "Analyze the comprehensive company profile below and identify the PRIMARY INDUSTRIES where this company's "
            "clients operate, considering their known clients, partners, and use cases.\n\n"
            
            "ENHANCED ANALYSIS APPROACH:\n"
            "1. Known Clients: If specific clients are mentioned, analyze what industries they operate in\n"
            "2. Partners: Partner companies often indicate adjacent client industries\n"
            "3. Use Cases: Specific use cases reveal target industry applications\n"
            "4. Customer Segments: Direct indicators of client types\n\n"
            
            "EXAMPLES OF THOROUGH ANALYSIS:\n"
            "- Payment processor (Nuvei): ecommerce, gaming, fintech, SaaS, digital marketplaces\n"
            "- Search API (Tavily): AI development, enterprise software, research institutions, media\n"
            "- No-code platform (Bubble): creative agencies, startups, SMBs, consulting firms\n"
            "- Developer tools: enterprise software, fintech, healthtech, edtech, proptech\n\n"
            
            "Focus on industries where DISRUPTION is happening or likely to happen. Prioritize industries "
            "undergoing digital transformation, regulatory changes, or technological shifts.\n\n"
            f"COMPREHENSIVE COMPANY PROFILE: {json.dumps(context, indent=2)}"
        )
        
        try:
            llm_with_schema = self.llm.with_structured_output(ClientIndustryList)
            response = await llm_with_schema.ainvoke(prompt)
            
            return {
                "industries": response.industries,
                "rationale": response.rationale
            }
            
        except Exception as e:
            self.logger.warning(f"Client industry identification failed, using fallback: {e}")
            # Fallback based on sector and industry
            sector = profile.get("sector", "").lower()
            industry = profile.get("industry", "").lower()
            
            fallback_industries = []
            if "payment" in sector or "fintech" in sector:
                fallback_industries = ["ecommerce", "gaming", "fintech", "SaaS"]
            elif "software" in sector or "saas" in sector:
                fallback_industries = ["startups", "enterprise", "healthcare", "education"]
            elif "marketing" in sector:
                fallback_industries = ["retail", "ecommerce", "hospitality", "real estate"]
            else:
                fallback_industries = ["technology", "business services", "retail"]
            
            return {
                "industries": fallback_industries[:4],
                "rationale": f"Fallback based on company sector: {sector}"
            }

    # --------------------------------- PHASE 2: CLIENT QUERY GENERATION ---------------------------------

    def _generate_disruptive_client_queries(self, client_industries: List[str], profile: Dict[str, Any], 
                                           competitors: List[str], sector_trends: List[Dict[str, Any]]) -> List[str]:
        """Generate DISRUPTIVE and FUTURE-SHAPING queries using ecosystem intelligence."""
        
        queries = []
        
        # Extract intelligence for context
        known_clients = profile.get("known_clients", [])[:5]
        partners = profile.get("partners", [])[:5] 
        company_sector = profile.get("sector", "")
        current_year = datetime.now().year
        
        for industry in client_industries:
            # DISRUPTIVE TECHNOLOGY TRENDS
            disruptive_queries = [
                f"{industry} AI disruption {current_year} market transformation",
                f"{industry} emerging technologies disrupting business models",
                f"{industry} automation replacing traditional processes",
                f"{industry} new technology adoption trends {current_year}",
                f"{industry} regulatory changes disrupting markets {current_year}"
            ]
            
            # FUTURE-SHAPING BUSINESS MODEL SHIFTS
            business_model_queries = [
                f"{industry} subscription economy transformation trends",
                f"{industry} platform business models disrupting incumbents",
                f"{industry} direct-to-consumer DTC revolution trends",
                f"{industry} marketplace economy disruption {current_year}",
                f"{industry} API economy platform strategies"
            ]
            
            # CONSUMER BEHAVIOR REVOLUTIONS
            behavior_queries = [
                f"{industry} generation Z consumer behavior shifts",
                f"{industry} remote work changing business demands",
                f"{industry} sustainability ESG driving market changes",
                f"{industry} personalization AI customer expectations"
            ]
            
            queries.extend(disruptive_queries + business_model_queries + behavior_queries)
        
        # COMPETITOR-INFORMED QUERIES (using competitor intelligence)
        if competitors:
            for competitor in competitors[:3]:  # Top 3 competitors
                competitor_queries = [
                    f"{competitor} disrupting {' '.join(client_industries[:2])} market analysis",
                    f"{competitor} vs traditional {client_industries[0] if client_industries else 'industry'} business models"
                ]
                queries.extend(competitor_queries)
        
        # KNOWN CLIENT INDUSTRY QUERIES (if specific clients are known)
        if known_clients:
            for client in known_clients[:3]:
                client_queries = [
                    f"{client} industry transformation trends driving change",
                    f"{client} market disruption challenges {current_year}"
                ]
                queries.extend(client_queries)
        
        # CROSS-SECTOR DISRUPTION (using company's own sector for cross-pollination)
        if company_sector and client_industries:
            for client_industry in client_industries[:2]:
                cross_sector_queries = [
                    f"{company_sector} solutions disrupting {client_industry} traditional workflows",
                    f"{client_industry} adopting {company_sector} innovations trends"
                ]
                queries.extend(cross_sector_queries)
        
        # Remove duplicates and limit
        unique_queries = list(dict.fromkeys(queries))  # Preserve order while removing duplicates
        return unique_queries[:20]  # Increased limit for comprehensive coverage

    # --------------------------------- PHASE 3: CONCURRENT SEARCH ---------------------------------

    async def _search(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Execute concurrent searches with rate limiting and deduplication."""
        
        async def _one_search(query: str) -> List[Dict[str, Any]]:
            async with self.sem:
                try:
                    result = await self.tavily.search(
                        query=query,
                        max_results=4,
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

    # --------------------------------- PHASE 4: STRUCTURED CLIENT TREND EXTRACTION ---------------------------------

    async def _llm_extract_disruptive_client_trends(self, profile: Dict[str, Any], client_industries: Dict[str, Any], 
                                                  docs: List[Dict[str, Any]], competitors: List[str], 
                                                  sector_trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract DISRUPTIVE client industry trends using comprehensive ecosystem intelligence."""
        
        if not docs:
            return []
        
        # Prepare content chunks for analysis
        chunks = []
        for doc in docs[:25]:  # Process top 25 documents
            content = doc.get("content", "")
            url = doc.get("url", "")
            title = doc.get("title", "")
            
            if content and url:
                chunk = f"URL: {url}\nTITLE: {title}\nCONTENT: {content[:800]}"
                chunks.append(chunk)
        
        joined_content = "\n---\n".join(chunks)
        company_name = profile.get("company", "the company")
        industries_list = ", ".join(client_industries['industries'])
        known_clients = profile.get("known_clients", [])
        partners = profile.get("partners", [])
        competitors_context = competitors[:5] if competitors else []
        
        # Enhanced context with ecosystem intelligence
        ecosystem_context = f"""
COMPANY: {company_name}
CLIENT INDUSTRIES: {industries_list}
KNOWN CLIENTS: {', '.join(known_clients) if known_clients else 'None specified'}
PARTNERS: {', '.join(partners) if partners else 'None specified'}  
COMPETITORS: {', '.join(competitors_context) if competitors_context else 'None available'}
SECTOR TRENDS AVAILABLE: {len(sector_trends)} trends identified
"""
        
        prompt = (
                         f"You are analyzing trends in {company_name}'s client industries to identify those with genuine "
             f"disruptive potential and business relevance.\n\n"
             
             f"COMPANY & ECOSYSTEM CONTEXT:\n{ecosystem_context}\n"
             
             "ANALYSIS FRAMEWORK:\n"
             "For each trend you extract, you must:\n\n"
             
             "1. ASSESS DISRUPTION POTENTIAL (0-1 scale):\n"
             "   - 0.9-1.0: Fundamental paradigm shift (e.g., entire industry business models changing)\n"
             "   - 0.7-0.9: Major market restructuring (e.g., new dominant players emerging)\n"
             "   - 0.5-0.7: Significant operational changes (e.g., new technologies changing workflows)\n"
             "   - 0.3-0.5: Moderate evolution (e.g., incremental improvements with some impact)\n"
             "   - 0.0-0.3: Minor changes (e.g., typical industry evolution)\n\n"
             
             "2. EVALUATE BUSINESS RELEVANCE TO THIS SPECIFIC COMPANY:\n"
             "   - How does this trend specifically impact their products/services?\n"
             "   - What opportunities or threats does it create for their business model?\n"
             "   - How might it affect their known clients, partners, or competitive position?\n"
             "   - Is this actionable for the company within 1-3 years?\n\n"
             
             "3. PRIORITIZE TRENDS THAT:\n"
             "   - Create new market opportunities for the company\n"
             "   - Change how their clients operate or make decisions\n"
             "   - Affect their competitive landscape\n"
             "   - Have concrete evidence (not speculation)\n"
             "   - Show clear adoption momentum or investment\n\n"
             
             "AVOID:\n"
             "- Generic industry trends without specific business impact\n"
             "- Well-known, already-adopted technologies\n"
             "- Vague predictions without evidence\n"
             "- Trends that don't connect to the company's business model\n\n"
             
             "Extract only the most impactful trends with clear business relevance and disruption potential."
        )
        
        try:
            llm_with_schema = self.llm.with_structured_output(ClientTrendArray)
            response = await llm_with_schema.ainvoke(
                f"{prompt}\n\nCONTENT:\n{joined_content}"
            )
            # Convert ClientTrendData objects to dictionaries
            return [trend.model_dump() for trend in response.trends]
            
        except Exception as e:
            self.logger.error(f"Failed to extract disruptive client trends via structured output: {e}")
            return []

    # --------------------------------- PHASE 5: AI RELEVANCE REVIEW ---------------------------------

    async def _ai_review_trends(self, profile: Dict[str, Any], raw_trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use AI to review and filter trends for genuine business relevance."""
        
        if not raw_trends:
            return []
        
        company_context = {
            "company": profile.get("company", ""),
            "description": profile.get("description", ""),
            "core_products": profile.get("core_products", []),
            "business_model": profile.get("business_model", "")
        }
        
        # Prepare trends for review (with indices and AI scores)
        trends_text = []
        for i, trend in enumerate(raw_trends):
            trend_summary = (
                f"[{i}] TREND: {trend.get('trend', '')}\n"
                f"IMPACT: {trend.get('impact', '')}\n"
                f"CLIENT INDUSTRY: {trend.get('client_industry', '')}\n"
                f"DISRUPTION SCORE: {trend.get('disruption_score', 0)}\n"
                f"BUSINESS RELEVANCE: {trend.get('business_relevance', '')}\n"
                f"CONFIDENCE: {trend.get('confidence', 0)}"
            )
            trends_text.append(trend_summary)
        
        prompt = (
            f"You are a STRATEGIC DISRUPTION ADVISOR reviewing client industry trends for TRANSFORMATIVE potential "
            f"for {company_context['company']}.\n\n"
            f"COMPANY CONTEXT: {json.dumps(company_context)}\n\n"
            
                         "REVIEW CRITERIA:\n\n"
             
             "SELECT trends that have:\n\n"
             
             "1. HIGH DISRUPTION SCORE (≥0.7) AND strong business relevance:\n"
             "   - Clear connection to the company's products/services\n"
             "   - Concrete business opportunities or threats\n"
             "   - Evidence of real market momentum\n\n"
             
             "2. MODERATE DISRUPTION SCORE (0.5-0.7) BUT exceptional company relevance:\n"
             "   - Directly affects known clients, partners, or competitors\n"
             "   - Creates clear actionable opportunities\n"
             "   - Has specific timeline or adoption evidence\n\n"
             
             "3. COMPANY-SPECIFIC STRATEGIC VALUE:\n"
             "   - Validates or challenges current business strategy\n"
             "   - Could influence product roadmap decisions\n"
             "   - Affects competitive positioning\n"
             "   - Creates urgency for client action\n\n"
             
             "REJECT trends that:\n"
             "- Have low disruption scores (<0.5) regardless of relevance\n"
             "- Lack specific business relevance explanations\n"
             "- Are generic industry observations\n"
             "- Have no clear connection to company ecosystem\n\n"
             
             "Focus on quality over quantity - only select genuinely impactful trends.\n\n"
            
            f"TRENDS TO REVIEW:\n{chr(10).join(trends_text)}"
        )
        
        try:
            llm_with_schema = self.llm.with_structured_output(TrendRelevanceReview)
            response = await llm_with_schema.ainvoke(prompt)
            
            # Filter trends based on AI review
            relevant_trends = []
            for index in response.relevant_trends:
                if 0 <= index < len(raw_trends):
                    relevant_trends.append(raw_trends[index])
            
            self.logger.info(f"AI review: {len(relevant_trends)}/{len(raw_trends)} trends deemed relevant. Reasoning: {response.reasoning}")
            return relevant_trends
            
        except Exception as e:
            self.logger.warning(f"AI review failed, returning all trends: {e}")
            return raw_trends

    # --------------------------------- PHASE 6: FINAL FILTERING ---------------------------------

    async def _postfilter_client_trends(self, profile: Dict[str, Any], reviewed_trends: List[Dict[str, Any]]) -> List[TrendInfo]:
        """Final filtering using embedding similarity and confidence thresholds."""
        
        if not reviewed_trends:
            return []
        
        # Get embedding for company description + business context
        business_context = f"{profile.get('description', '')} {profile.get('business_model', '')} {' '.join(profile.get('core_products', []))}"
        
        try:
            context_vector = await self.embedding.aembed_query(business_context[:512])
        except Exception as e:
            self.logger.warning(f"Failed to generate embedding: {e}")
            context_vector = None
        
        processed_trends = []
        
        for trend_data in reviewed_trends:
            try:
                # Extract required fields with defaults
                trend_text = trend_data.get("trend", "")
                evidence_url = trend_data.get("evidence", "")
                impact_text = trend_data.get("impact", "")
                client_industry = trend_data.get("client_industry", "")
                date_str = trend_data.get("date", datetime.now().strftime('%Y-%m'))
                confidence = float(trend_data.get("confidence", 0.5))
                disruption_score = float(trend_data.get("disruption_score", 0.5))
                business_relevance = trend_data.get("business_relevance", "")
                
                # Validate URL format
                if not evidence_url.startswith(('http://', 'https://')):
                    self.logger.warning(f"Invalid URL format: {evidence_url}")
                    continue
                
                # Skip trends with missing essential data, low confidence, or low disruption potential
                if not trend_text or not evidence_url or confidence < 0.5 or disruption_score < 0.4:
                    continue
                
                # Create enhanced impact description with business relevance
                enhanced_impact = f"[{client_industry}] {impact_text}"
                if business_relevance:
                    enhanced_impact += f" | Business Impact: {business_relevance}"
                
                trend = TrendInfo(
                    trend=trend_text,
                    evidence=evidence_url,
                    impact=enhanced_impact,
                    date=date_str,
                    source_domain=urlparse(evidence_url).netloc,
                    confidence_score=round(confidence, 2)
                )
                
                # Add AI-generated scores for sorting
                trend_dict = trend.model_dump()
                trend_dict["disruption_score"] = round(disruption_score, 2)
                trend_dict["business_relevance_score"] = len(business_relevance) / 100.0  # Simple relevance based on detail
                processed_trends.append(TrendInfo(**trend_dict))
                    
            except Exception as e:
                self.logger.warning(f"Failed to process client trend: {e}")
                continue
        
        # Sort by combined disruption score and confidence (prioritizing disruption potential)
        processed_trends.sort(
            key=lambda x: (getattr(x, 'disruption_score', 0.5) * 0.6 + x.confidence_score * 0.4),
            reverse=True
        )
        
        return processed_trends[:8]  # Return top 8 most disruptive client trends

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        
        return dot_product / (norm_a * norm_b + 1e-8) 