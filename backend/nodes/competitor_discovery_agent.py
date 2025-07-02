from __future__ import annotations

from typing import Any, Dict

from langchain_core.messages import AIMessage

from ..agents.base_agent import BaseAgent
from .competitor_search_agent import CompetitorSearchAgent
from .competitor_validator_agent import CompetitorValidatorAgent


class EnhancedCompetitorDiscoveryAgent(BaseAgent):
    """High-level orchestrator that discovers competitors in two stages:

    1. `CompetitorSearchAgent` – generate search queries, run Tavily searches, and
       pull a raw list of candidate competitors.
    2. `CompetitorValidatorAgent` – score & rank those candidates, returning a
       curated list of the strongest competitors (max 8).
    """

    def __init__(self, llm_model: str = "gpt-4o") -> None:
        super().__init__(agent_type="competitor_discovery_agent")
        self.search_agent = CompetitorSearchAgent(llm_model)
        self.validator_agent = CompetitorValidatorAgent(llm_model)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run search ➜ validation and return the enriched state."""

        self.log_agent_start(state)

        # --------------------------- Phase 1 – SEARCH ---------------------------
        state = await self.search_agent.run(state)

        # ------------------------ Phase 2 – VALIDATION --------------------------
        state = await self.validator_agent.run(state)

        # ---------------------------- Completion -------------------------------
        company = state.get("company", "Unknown Company")
        competitors = state.get("competitors", [])
        candidate_count = len(state.get("candidate_competitors", []))

        completion_msg = (
            f"✅ Discovered and ranked top {len(competitors)} competitors for {company} "
            f"(selected from {candidate_count} candidates)"
        )
        messages = state.get("messages", [])
        messages.append(AIMessage(content=completion_msg))
        state["messages"] = messages

        self.log_agent_complete(state)
        return state
