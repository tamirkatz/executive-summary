from __future__ import annotations
import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field
from typing import List
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from tavily import AsyncTavilyClient
from langchain_core.messages import AIMessage

from ..agents.base_agent import BaseAgent

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class CompetitorInfo(BaseModel):
    name: str
    description: str
    category: str  # direct / indirect / emerging
    confidence: float
    evidence: str


class DiscoveryResult(BaseModel):
    direct: List[CompetitorInfo]
    indirect: List[CompetitorInfo]
    emerging: List[CompetitorInfo]


class QueryList(BaseModel):
    queries: List[str] = Field(description="List of competitor-oriented search strings", min_length=10, max_length=20)


class CompanyList(BaseModel):
    companies: List[str] = Field(description="List of company names", max_length=50)


class CompetitorClassification(BaseModel):
    category: str = Field(description="Competitor category", pattern="^(direct|indirect|emerging|not_relevant)$")
    reason: str = Field(description="Reason for classification")


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class EnhancedCompetitorDiscoveryAgent(BaseAgent):
    """Enhanced competitor discovery agent that finds and validates competitors."""
    
    def __init__(self, llm_model: str = "gpt-4o"):
        super().__init__(agent_type="competitor_discovery_agent")
        
        self.llm_model = llm_model
        self.temperature = 0.3
        self.rate_limit = 5  # Tavily concurrent requests
        
        if not os.getenv("TAVILY_API_KEY"):
            raise ValueError("TAVILY_API_KEY is not configured")
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is not configured")
            
        self.llm = ChatOpenAI(model=self.llm_model, temperature=self.temperature, api_key=os.getenv("OPENAI_API_KEY"))
        self.embedding = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
        self.tavily = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        self.sem = asyncio.Semaphore(self.rate_limit)

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution method for competitor discovery."""
        self.log_agent_start(state)
        company = state.get('company', 'Unknown Company')
        websocket_manager, job_id = self.get_websocket_info(state)
        
        try:
            # Extract profile from state
            profile = state.get("profile", {})
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🔍 Starting competitor discovery for {company}",
                result={"step": "Competitor Discovery", "substep": "query_generation"}
            )
            
            queries = await self._generate_queries(profile)
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🌐 Searching {len(queries)} competitor queries",
                result={"step": "Competitor Discovery", "substep": "search"}
            )
            
            raw_docs = await self._search_bulk(queries)
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message="🧮 Extracting competitor candidates",
                result={"step": "Competitor Discovery", "substep": "extraction"}
            )
            
            candidates = await self._extract_candidates(profile, raw_docs)
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"⚖️ Validating {len(candidates)} competitor candidates",
                result={"step": "Competitor Discovery", "substep": "validation"}
            )
            
            validated = await self._validate(profile, candidates)
            result = self._bucketise(validated)
            
            # Store results in both formats for compatibility
            state["competitor_discovery"] = result.model_dump()
            
            # Store in the format expected by other agents
            competitors = []
            for comp in result.direct + result.indirect + result.emerging:
                competitors.append({
                    "name": comp.name,
                    "description": comp.description,
                    "type": comp.category,
                    "confidence": comp.confidence,
                    "evidence": comp.evidence
                })
            state["competitors"] = competitors
            
            # Add completion message
            completion_msg = f"✅ Discovered {len(competitors)} competitors for {company}"
            messages = state.get('messages', [])
            messages.append(AIMessage(content=completion_msg))
            state['messages'] = messages
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="completed",
                message=completion_msg,
                result={
                    "step": "Competitor Discovery",
                    "substep": "complete",
                    "competitors_found": len(competitors),
                    "competitors": competitors,
                    "discovery_result": result.model_dump()
                }
            )
            
            return state
            
        except Exception as e:
            error_msg = f"❌ Competitor discovery failed: {str(e)}"
            self.logger.error(error_msg)
            await self.send_status_update(
                websocket_manager, job_id,
                status="error",
                message=error_msg,
                result={"step": "Competitor Discovery", "error": str(e)}
            )
            return state

    # --------------------------------- PHASE 1 ---------------------------------

    async def _generate_queries(self, profile: Dict[str, Any]) -> List[str]:
        """LLM generates 10-20 queries; enforce schema for reliability."""
        prompt = (
            "You are a competitive‑intelligence analyst.\n"
            "Generate laser‑focused search queries (10‑20) to uncover **startup or scale‑up** competitors for the company below.\n"
            "Avoid Big‑Tech names in queries.\n\n"
            f"COMPANY: {profile.get('company', 'Unknown Company')}\n"
            f"SECTOR: {profile.get('sector','')}\n"
            f"CORE_PRODUCTS: {', '.join(profile.get('core_products', []))}\n"
        )

        llm_with_schema = self.llm.with_structured_output(QueryList)
        rsp = await llm_with_schema.ainvoke(prompt)
        return rsp.queries

    # --------------------------------- PHASE 2 ---------------------------------

    async def _search_bulk(self, queries: List[str]) -> List[Dict[str, Any]]:
        async def _one(q: str):
            async with self.sem:
                try:
                    return await self.tavily.search(query=q, max_results=5, include_answer=True)
                except Exception as e:
                    self.logger.warning("Tavily error %s", e)
                    return None

        tasks = [_one(q) for q in queries]
        results = await asyncio.gather(*tasks)
        # flatten + drop None
        docs = [item for res in results if res for item in res.get("results", [])]
        return docs

    # --------------------------------- PHASE 3 ---------------------------------

    async def _extract_candidates(self, profile: Dict[str, Any], docs: List[Dict[str, Any]]) -> Set[str]:
        """Ask LLM to extract candidate company names from aggregated snippets."""
        chunks = [d["content"][:1000] for d in docs if d.get("content")]
        joined = "\n---\n".join(chunks)[:12000]

        prompt = (
            "Identify **startup/scale‑up** companies that directly or indirectly compete with"
            f" {profile.get('company', 'Unknown Company')} (sector: {profile.get('sector','')})."
            "Return only company names, no descriptions."
        )
        llm_with_schema = self.llm.with_structured_output(CompanyList)
        rsp = await llm_with_schema.ainvoke(prompt + "\nTEXT:\n" + joined)
        names = rsp.companies
        # normalise & dedupe
        cleaned = {re.sub(r"[^a-z0-9]+", "", n.lower()): n.strip() for n in names if len(n) < 30}
        return set(cleaned.values())

    # --------------------------------- PHASE 4 ---------------------------------

    async def _validate(self, profile: Dict[str, Any], names: Set[str]) -> List[CompetitorInfo]:
        # Safely get description with fallback
        description = profile.get("description", profile.get("company", ""))
        target_vec = await self.embedding.aembed_query(description[:512])

        async def _score(name: str) -> Optional[CompetitorInfo]:
            """LLM relevance + embedding similarity."""
            # quick info fetch
            try:
                res = await self.tavily.search(query=f"{name} company overview", max_results=2, include_answer=True)
                snippet = res["results"][0]["content"] if res.get("results") else ""
            except Exception:
                snippet = ""

            # embedding sim
            if snippet:
                vec = await self.embedding.aembed_query(snippet[:512])
                sim = self._cosine(target_vec, vec)
            else:
                sim = 0.0

            # LLM classification
            prompt = (
                f"Is {name} a competitor to {profile.get('company', 'Unknown Company')} (sector: {profile.get('sector','')})?"
                " Classify and justify in one line."
            )
            llm_with_schema = self.llm.with_structured_output(CompetitorClassification)
            cls = await llm_with_schema.ainvoke(prompt)

            category = cls.category
            if category == "not_relevant":
                return None

            confidence = (sim + (1.0 if category == "direct" else 0.7)) / 2
            return CompetitorInfo(
                name=name,
                description=snippet[:200] if snippet else "",
                category=category,
                confidence=round(confidence, 2),
                evidence=cls.reason,
            )

        tasks = [_score(n) for n in names]
        items = await asyncio.gather(*tasks)
        return [i for i in items if i and i.confidence >= 0.6]

    # --------------------------------- HELPER ---------------------------------

    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        import math
        dot = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(x*x for x in b))
        return dot / (na*nb + 1e-8)

    def _bucketise(self, comps: List[CompetitorInfo]) -> DiscoveryResult:
        direct = [c for c in comps if c.category == "direct"]
        indirect = [c for c in comps if c.category == "indirect"]
        emerging = [c for c in comps if c.category == "emerging"]
        return DiscoveryResult(direct=direct, indirect=indirect, emerging=emerging)
