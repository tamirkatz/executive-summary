import os
import logging
import asyncio
import json
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from backend.config import config
from tavily import AsyncTavilyClient
from ..classes import ResearchState
from ..agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class CompetitorCandidate(BaseModel):
    name: str = Field(description="Competitor company name")
    description: str = Field(description="What the competitor does")
    reasoning: str = Field(description="Why this is considered a competitor")
    confidence_score: float = Field(description="Confidence 0-1 that this is a relevant competitor")
    source_query: str = Field(description="Query that discovered this competitor")
    evidence: List[str] = Field(description="Evidence snippets supporting this as a competitor")
    market_overlap: str = Field(description="How they overlap with target company")


class QueryStrategy(BaseModel):
    query: str = Field(description="The search query to execute")
    reasoning: str = Field(description="Why this query will find relevant competitors")
    expected_type: str = Field(description="Type of competitors this query targets")
    priority: int = Field(description="Priority 1-5, where 5 is highest")


class AutonomousCompetitorDiscoveryAgent(BaseAgent):
    """
    🚀 10x Enhanced Autonomous Competitor Discovery Agent
    
    Uses o3 model with sophisticated reasoning to discover competitors
    through smart query generation and iterative refinement.
    
    Key Features:
    - Autonomous reasoning (no naive "competitors of X" queries)
    - Smart query patterns based on business model analysis
    - Deep validation using additional Tavily searches
    - Confidence scoring and evidence tracking
    """
    
    def __init__(self, model_name: str = "o3-mini"):
        super().__init__(agent_type="autonomous_competitor_discovery_agent")
        
        # Use o3 model for state-of-the-art reasoning
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.1,
            api_key=config.OPENAI_API_KEY
        )
        
        self.tavily = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        
        # Agent state
        self.discovered_candidates: List[CompetitorCandidate] = []
        self.executed_queries: List[QueryStrategy] = []
        self.reasoning_history: List[str] = []
        
        # Configuration
        self.max_iterations = 5
        self.min_competitors_required = 3
        self.confidence_threshold = 0.7

    async def discover_competitors(self, company: str, description: str, industry: str, 
                                 sector: str, websocket_manager=None, job_id=None) -> Dict[str, Any]:
        """🧠 Autonomous competitor discovery with sophisticated reasoning."""
        
        await self.send_status_update(
            websocket_manager, job_id,
            status="processing",
            message=f"🧠 Starting autonomous competitor discovery for {company}",
            result={"step": "Autonomous Competitor Discovery", "substep": "initialization"}
        )
        
        company_profile = {
            "name": company,
            "description": description,
            "industry": industry,
            "sector": sector
        }
        
        self.reasoning_history.append(f"🎯 Target: {company} - {description}")
        
        # Autonomous discovery loop
        for iteration in range(1, self.max_iterations + 1):
            self.logger.info(f"🔄 Discovery iteration {iteration}/{self.max_iterations}")
            
            # Generate smart query strategies
            strategies = await self._generate_smart_queries(company_profile, iteration)
            
            if not strategies:
                break
            
            # Execute queries and extract candidates
            new_candidates = await self._execute_and_extract(strategies, company_profile)
            
            # Validate and score candidates
            validated_candidates = await self._validate_candidates(new_candidates, company_profile)
            
            self.discovered_candidates.extend(validated_candidates)
            
            # Check if we have sufficient results
            high_confidence = [c for c in self.discovered_candidates if c.confidence_score >= self.confidence_threshold]
            
            if len(high_confidence) >= self.min_competitors_required:
                self.logger.info(f"✅ Sufficient results achieved at iteration {iteration}")
                break
        
        # Finalize results
        final_competitors = await self._finalize_results(company_profile)
        
        return {
            "competitors": [c.name for c in final_competitors],
            "detailed_analysis": [c.model_dump() for c in final_competitors],
            "reasoning_history": self.reasoning_history,
            "total_iterations": iteration,
            "avg_confidence": sum(c.confidence_score for c in final_competitors) / max(1, len(final_competitors))
        }

    async def _generate_smart_queries(self, company_profile: Dict, iteration: int) -> List[QueryStrategy]:
        """Generate intelligent query strategies avoiding naive patterns."""
        
        strategy_prompt = f"""You are an autonomous business intelligence agent generating smart competitor discovery queries.

TARGET COMPANY:
Name: {company_profile['name']}
Description: {company_profile['description']}
Industry: {company_profile['industry']}
Sector: {company_profile['sector']}

ITERATION: {iteration}/5

🚫 FORBIDDEN (naive queries):
- "competitors of [company]"
- "[company] vs competitors"
- "alternatives to [company]"

✅ SMART PATTERNS:
- "companies providing [specific service] to [target market]"
- "[technology] solutions for [use case] in [industry]"
- "vendors helping [customer type] with [specific problem]"
- "platforms for [workflow] used by [industry vertical]"

Generate 2-3 sophisticated queries as JSON:
[
  {{
    "query": "smart search query",
    "reasoning": "why this finds relevant competitors",
    "expected_type": "type of competitors targeted",
    "priority": 1-5
  }}
]

Strategies:"""

        try:
            result = await self.llm.ainvoke(strategy_prompt)
            strategies_data = json.loads(result.content.strip())
            
            strategies = []
            for data in strategies_data:
                strategy = QueryStrategy(**data)
                strategies.append(strategy)
            
            return sorted(strategies, key=lambda x: x.priority, reverse=True)
            
        except Exception as e:
            self.logger.error(f"Strategy generation failed: {e}")
            return []

    async def _execute_and_extract(self, strategies: List[QueryStrategy], 
                                  company_profile: Dict) -> List[CompetitorCandidate]:
        """Execute queries and extract competitor candidates."""
        
        all_candidates = []
        
        for strategy in strategies:
            try:
                # Execute Tavily search
                search_results = await self.tavily.search(
                    query=strategy.query,
                    max_results=8,
                    include_answer=True,
                    search_depth="advanced"
                )
                
                # Extract candidates using reasoning
                candidates = await self._extract_with_reasoning(
                    search_results, strategy, company_profile
                )
                
                all_candidates.extend(candidates)
                self.executed_queries.append(strategy)
                
            except Exception as e:
                self.logger.error(f"Query execution failed: {e}")
        
        return all_candidates

    async def _extract_with_reasoning(self, search_results: Dict, strategy: QueryStrategy,
                                     company_profile: Dict) -> List[CompetitorCandidate]:
        """Extract competitors using sophisticated reasoning."""
        
        if not search_results.get("results"):
            return []
        
        content = " ".join([
            result.get("content", "")
            for result in search_results["results"]
            if result.get("content")
        ])
        
        extraction_prompt = f"""Extract competitor companies using sophisticated analysis.

TARGET: {company_profile['name']} - {company_profile['description']}
SEARCH STRATEGY: {strategy.reasoning}
CONTENT: {content[:2000]}...

Analyze for companies that:
1. Solve similar problems for similar customers
2. Operate in the same market segment
3. Would be considered alternatives by customers

Return as JSON:
[
  {{
    "name": "Company Name",
    "description": "What they do",
    "reasoning": "Why they compete",
    "confidence_score": 0.0-1.0,
    "evidence": ["supporting quote 1", "supporting quote 2"],
    "market_overlap": "how they compete"
  }}
]

Competitors:"""

        try:
            result = await self.llm.ainvoke(extraction_prompt)
            competitors_data = json.loads(result.content.strip())
            
            candidates = []
            for comp_data in competitors_data:
                candidate = CompetitorCandidate(
                    name=comp_data["name"],
                    description=comp_data.get("description", ""),
                    reasoning=comp_data.get("reasoning", ""),
                    confidence_score=comp_data.get("confidence_score", 0.5),
                    source_query=strategy.query,
                    evidence=comp_data.get("evidence", []),
                    market_overlap=comp_data.get("market_overlap", "")
                )
                candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            self.logger.error(f"Extraction failed: {e}")
            return []

    async def _validate_candidates(self, candidates: List[CompetitorCandidate],
                                  company_profile: Dict) -> List[CompetitorCandidate]:
        """Validate candidates through additional research."""
        
        validated = []
        
        for candidate in candidates:
            # Skip if invalid name
            if not self._is_valid_name(candidate.name):
                continue
            
            # Deep validation
            enhanced = await self._deep_validate(candidate, company_profile)
            
            if enhanced and enhanced.confidence_score >= 0.6:
                validated.append(enhanced)
        
        return validated

    async def _deep_validate(self, candidate: CompetitorCandidate,
                           company_profile: Dict) -> Optional[CompetitorCandidate]:
        """Perform deep validation using additional Tavily search."""
        
        try:
            # Validation search
            validation_query = f'"{candidate.name}" company business model products services'
            
            validation_results = await self.tavily.search(
                query=validation_query,
                max_results=3,
                include_answer=True
            )
            
            if not validation_results.get("results"):
                return candidate
            
            candidate_info = " ".join([
                result.get("content", "")
                for result in validation_results["results"]
            ])
            
            # Assess competitive similarity
            similarity_prompt = f"""Assess competitive similarity.

TARGET: {company_profile['name']} - {company_profile['description']}
CANDIDATE: {candidate.name}
RESEARCH: {candidate_info[:1500]}

Analyze:
1. Business model similarity
2. Target market overlap  
3. Product/service similarity
4. Competitive threat level

Return JSON:
{{
  "confidence_score": 0.0-1.0,
  "enhanced_description": "refined description",
  "competitive_analysis": "detailed analysis",
  "is_valid_competitor": true/false
}}

Assessment:"""

            result = await self.llm.ainvoke(similarity_prompt)
            assessment = json.loads(result.content.strip())
            
            if assessment.get("is_valid_competitor", False):
                candidate.confidence_score = assessment.get("confidence_score", candidate.confidence_score)
                candidate.description = assessment.get("enhanced_description", candidate.description)
                candidate.reasoning = assessment.get("competitive_analysis", candidate.reasoning)
                return candidate
            
            return None
                
        except Exception as e:
            self.logger.error(f"Deep validation failed for {candidate.name}: {e}")
            return candidate

    async def _finalize_results(self, company_profile: Dict) -> List[CompetitorCandidate]:
        """Finalize and rank competitor list."""
        
        # Remove duplicates and rank by confidence
        seen_names = set()
        unique_candidates = []
        
        # Sort by confidence
        self.discovered_candidates.sort(key=lambda x: x.confidence_score, reverse=True)
        
        for candidate in self.discovered_candidates:
            name_lower = candidate.name.lower()
            if name_lower not in seen_names:
                seen_names.add(name_lower)
                unique_candidates.append(candidate)
        
        # Take top 10
        final_list = unique_candidates[:10]
        
        self.reasoning_history.append(f"🎯 Final: {len(final_list)} competitors selected")
        
        return final_list

    def _is_valid_name(self, name: str) -> bool:
        """Validate competitor name."""
        if not name or len(name) < 2:
            return False
        
        invalid_terms = {
            'companies', 'startups', 'businesses', 'solutions', 'platforms',
            'tools', 'services', 'software', 'systems', 'providers'
        }
        
        return name.lower() not in invalid_terms

    async def run(self, state: ResearchState) -> ResearchState:
        """Main entry point for autonomous competitor discovery."""
        company = state.get('company', 'Unknown Company')
        company_info = state.get('company_info', {})
        
        description = company_info.get('description', '')
        industry = company_info.get('industry', 'Unknown')
        sector = company_info.get('sector', 'Unknown')
        
        websocket_manager, job_id = self.get_websocket_info(state)

        self.log_agent_start(state)

        # Execute autonomous discovery
        discovery_result = await self.discover_competitors(
            company=company,
            description=description,
            industry=industry,
            sector=sector,
            websocket_manager=websocket_manager,
            job_id=job_id
        )
        
        competitors = discovery_result.get('competitors', [])
        self.logger.info(f"🎯 Autonomous discovery found {len(competitors)} competitors for {company}")
        
        # Update state
        updated_state = state.copy()
        
        if 'company_info' in updated_state:
            updated_state['company_info']['competitors'] = competitors
        else:
            updated_state['company_info'] = {'competitors': competitors}
        
        updated_state['autonomous_competitor_discovery'] = discovery_result

        self.log_agent_complete(state)
        return updated_state


# Maintain backward compatibility
CompetitorDiscoveryAgent = AutonomousCompetitorDiscoveryAgent 