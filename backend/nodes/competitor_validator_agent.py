from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from tavily import AsyncTavilyClient

from ..agents.base_agent import BaseAgent

# ---------------------------------------------------------------------------
# Pydantic Schemas (LLM structured outputs)
# ---------------------------------------------------------------------------

class CompetitorWithDescription(BaseModel):
    name: str = Field(description="Competitor company name")
    description: str = Field(description="Brief description of what the company does")


class ScoredCompetitor(BaseModel):
    name: str = Field(description="Competitor company name")
    score: float = Field(
        description="Accuracy score from 0-10, where 10 is the most accurate competitor",
        ge=0,
        le=10,
    )
    reasoning: str = Field(description="Brief explanation of the score and why this competitor is relevant")


class ScoredCompetitors(BaseModel):
    competitors: List[ScoredCompetitor] = Field(description="List of competitors with accuracy scores")


# ---------------------------------------------------------------------------
# Agent Definition
# ---------------------------------------------------------------------------


class CompetitorValidatorAgent(BaseAgent):
    """Agent responsible for validating, scoring, and ranking competitor candidates.

    It expects that the search phase already populated `state["candidate_competitors"]`.
    """

    def __init__(self, llm_model: str = "gpt-4o", *, rate_limit: int = 5):
        super().__init__(agent_type="competitor_validator_agent")

        # Environment validation ------------------------------------------------------
        if not os.getenv("TAVILY_API_KEY"):
            raise ValueError("TAVILY_API_KEY is not configured")
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is not configured")

        self.llm_model = llm_model
        self.temperature = 0.3
        self.rate_limit = rate_limit

        self.llm = ChatOpenAI(
            model=self.llm_model,
            temperature=self.temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.tavily = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        self.sem = asyncio.Semaphore(self.rate_limit)

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and rank competitor candidates.

        Expected pre-conditions:
            • state["candidate_competitors"] is a non-empty list.

        Side-effects:
            • state["competitors"] – Final validated list (max 8).
            • state["competitor_validation"] – Metadata / stats.
        """

        self.log_agent_start(state)
        company = state.get("company", "Unknown Company")
        websocket_manager, job_id = self.get_websocket_info(state)

        candidate_names: List[str] = state.get("candidate_competitors", [])
        if not candidate_names:
            self.logger.warning("No candidate competitors found – skipping validation phase")
            return state

        profile = state.get("profile", {})
        company_description = profile.get("description", "")
        core_products = profile.get("core_products", [])

        # ------------------------------------------------------------------
        # Step 1 – Fetch short descriptions for each candidate
        # ------------------------------------------------------------------
        await self.send_status_update(
            websocket_manager,
            job_id,
            status="processing",
            message=f"📋 Getting descriptions for {len(candidate_names)} candidates",
            result={"step": "Competitor Validation", "substep": "fetch_descriptions"},
        )

        competitors_with_desc = await self._get_competitor_descriptions(candidate_names)

        # ------------------------------------------------------------------
        # Step 2 – LLM-based scoring / ranking
        # ------------------------------------------------------------------
        await self.send_status_update(
            websocket_manager,
            job_id,
            status="processing",
            message=f"🤖 Scoring {len(competitors_with_desc)} candidates",
            result={"step": "Competitor Validation", "substep": "llm_scoring"},
        )

        scored_competitors = await self._llm_score_competitors(
            company, company_description, core_products, competitors_with_desc
        )

        # Sort + keep top 8 ------------------------------------------------------------
        sorted_competitors = sorted(scored_competitors, key=lambda x: x.score, reverse=True)
        top_competitors = sorted_competitors[:8]
        validated_names = [c.name for c in top_competitors]

        # ------------------------------------------------------------------
        # Optional post-filter: ensure recent news mention (signal of relevancy)
        # ------------------------------------------------------------------
        current_year = datetime.now().year
        prev_year = current_year - 1
        filtered_names: List[str] = []
        
        async def _check_recent_news(name: str) -> bool:
            """Check if a competitor has recent news mentions with rate limiting."""
            async with self.sem:  # Use semaphore for rate limiting
                try:
                    await asyncio.sleep(0.5)  # Add small delay to avoid overwhelming APIs
                    query = f'"{name}" news {prev_year} OR {current_year}'
                    result = await self.tavily.search(query=query, max_results=3)
                    
                    for item in result.get("results", []):
                        date = item.get("published_date") or item.get("date")
                        if date and (str(prev_year) in date or str(current_year) in date):
                            return True
                    return False
                except Exception as e:
                    self.logger.warning(f"Post-filter failed for {name}: {e}")
                    return False
        
        # Process competitors with rate limiting
        news_check_tasks = [_check_recent_news(name) for name in validated_names]
        news_results = await asyncio.gather(*news_check_tasks, return_exceptions=True)
        
        for name, has_recent in zip(validated_names, news_results):
            if isinstance(has_recent, bool) and has_recent:
                filtered_names.append(name)

        if filtered_names:
            validated_names = filtered_names

        # ------------------------------------------------------------------
        # Persist + notify ---------------------------------------------------
        # ------------------------------------------------------------------
        filtered_out = len(candidate_names) - len(validated_names)
        state["competitors"] = validated_names
        state["competitor_validation"] = {
            "total_candidates": len(candidate_names),
            "final_competitors_selected": len(validated_names),
            "filtered_out": filtered_out,
        }

        await self.send_status_update(
            websocket_manager,
            job_id,
            status="validation_complete",
            message=f"🏆 Selected top {len(validated_names)} competitors (filtered {filtered_out})",
            result={
                "step": "Competitor Validation",
                "substep": "complete",
                "final_competitors": validated_names,
                "filtered_out": filtered_out,
            },
        )

        self.log_agent_complete(state)
        return state

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    async def _get_competitor_descriptions(self, names: List[str]) -> List[CompetitorWithDescription]:
        """Fetch a short company description for each competitor via Tavily."""

        async def _single(name: str) -> CompetitorWithDescription:
            async with self.sem:
                try:
                    query = f'"{name}" company what they do business description'
                    result = await self.tavily.search(query=query, max_results=3, include_answer=True)

                    description = "Unknown company"
                    if result.get("answer"):
                        description = result["answer"][:200]
                    elif result.get("results") and result["results"][0].get("content"):
                        description = result["results"][0]["content"][:200]

                    return CompetitorWithDescription(name=name, description=description)
                except Exception as e:
                    self.logger.warning(f"Failed to get description for {name}: {e}")
                    return CompetitorWithDescription(name=name, description="Unknown company")

        tasks = [_single(n) for n in names]
        return await asyncio.gather(*tasks)

    async def _llm_score_competitors(
        self,
        company: str,
        company_description: str,
        core_products: List[str],
        competitors: List[CompetitorWithDescription],
    ) -> List[ScoredCompetitor]:
        """Use the LLM to assign a 0-10 competitor relevancy score to each company."""

        core_products_text = ", ".join(core_products) if core_products else "N/A"
        comp_list_text = "\n".join([f"- {c.name}: {c.description}" for c in competitors])

        prompt = f"""You are a competitive intelligence expert. Score each candidate company based on how accurate/strong of a competitor they are to the target company.

TARGET COMPANY: {company}
TARGET DESCRIPTION: {company_description}
TARGET CORE PRODUCTS: {core_products_text}

CANDIDATE COMPANIES TO SCORE:
{comp_list_text}

For each candidate company, assign a score from 0-10 based on competitive accuracy:

SCORING CRITERIA:
- 9-10: DIRECT COMPETITOR – Nearly identical target market, very similar products/services.
- 7-8: STRONG COMPETITOR – Overlapping market, similar solutions.
- 5-6: MODERATE – Some overlap.
- 3-4: WEAK – Limited overlap.
- 1-2: TANGENTIAL – Minimal overlap.
- 0: NOT A COMPETITOR – Different industry/business model.

Return only companies with score ≥ 3, with clear reasoning for each score."""

        llm_with_schema = self.llm.with_structured_output(ScoredCompetitors)
        response = await llm_with_schema.ainvoke(prompt)

        valid: List[ScoredCompetitor] = []
        for comp in response.competitors:
            if comp.score >= 3 and comp.name.lower() != company.lower():
                valid.append(comp)

        self.logger.info(
            "LLM scoring complete",
            extra={"candidates": len(competitors), "selected": len(valid)},
        )
        return valid 