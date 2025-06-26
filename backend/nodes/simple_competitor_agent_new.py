import os
import logging
import asyncio
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from backend.config import config
from tavily import AsyncTavilyClient
from ..classes import ResearchState
from ..agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class CompetitorInfo(BaseModel):
    """Structure for competitor information"""
    name: str = Field(description="Company name")
    reasoning: str = Field(description="Why this is a competitor")
    confidence: float = Field(description="Confidence score 0-1")


class CompetitorList(BaseModel):
    """Structure for the complete competitor analysis"""
    direct_competitors: List[str] = Field(description="List of direct competitors")
    indirect_competitors: List[str] = Field(description="List of indirect competitors")
    analysis_summary: str = Field(description="Brief analysis of the competitive landscape")


class SimpleCompetitorDiscoveryAgent(BaseAgent):
    """
    Simple, effective competitor discovery agent that uses o3-mini for initial analysis
    and Tavily for validation and enrichment.
    """
    
    def __init__(self):
        super().__init__(agent_type="simple_competitor_discovery_agent")
        
        # Use o3-mini for the core competitor analysis
        self.llm = ChatOpenAI(
            model="o3-mini",
            temperature=0.1,
            api_key=config.OPENAI_API_KEY
        )
        
        self.tavily = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    async def discover_competitors(self, company_info: Dict[str, Any], websocket_manager=None, job_id=None) -> Dict[str, Any]:
        """Main competitor discovery method"""
        
        company_name = company_info.get('company', 'Unknown')
        
        await self.send_status_update(
            websocket_manager, job_id,
            status="processing",
            message=f"🧠 Analyzing competitors for {company_name} using o3-mini",
            result={"step": "Competitor Discovery", "substep": "llm_analysis"}
        )
        
        # Step 1: Get initial competitor list from o3-mini
        initial_competitors = await self._get_initial_competitors_from_llm(company_info)
        
        await self.send_status_update(
            websocket_manager, job_id,
            status="processing",
            message=f"🔍 Found {len(initial_competitors.direct_competitors + initial_competitors.indirect_competitors)} initial competitors, validating with web search",
            result={"step": "Competitor Discovery", "substep": "web_validation"}
        )
        
        # Step 2: Validate and enrich with Tavily
        validated_competitors = await self._validate_and_enrich_with_tavily(
            company_name, 
            initial_competitors, 
            company_info
        )
        
        await self.send_status_update(
            websocket_manager, job_id,
            status="competitor_discovery_complete",
            message=f"✅ Competitor analysis complete: {len(validated_competitors)} validated competitors",
            result={"competitors": validated_competitors}
        )
        
        return {
            "competitors": validated_competitors,
            "analysis_summary": initial_competitors.analysis_summary,
            "methodology": "o3_mini_plus_tavily_validation"
        }

    async def _get_initial_competitors_from_llm(self, company_info: Dict[str, Any]) -> CompetitorList:
        """Use o3-mini to generate the initial competitor analysis"""
        
        # Build comprehensive company context
        company_context = self._build_company_context(company_info)
        
        prompt = f"""You are a world-class business analyst specializing in competitive intelligence. You have access to comprehensive information about a company and need to identify its true competitors.

{company_context}

Your task is to provide a comprehensive competitive analysis. Consider:

1. **Direct Competitors**: Companies offering nearly identical products/services to the same target market
2. **Indirect Competitors**: Companies solving the same customer problem with different approaches
3. **Emerging Competitors**: Newer companies or products that could become threats

Requirements:
- Focus on actual, real companies that exist today
- Prioritize companies that customers would genuinely consider as alternatives
- Consider both established players and emerging startups
- Exclude companies that are too broad or unrelated
- Provide reasoning for each classification

Be thorough but precise. Quality over quantity."""

        try:
            response = await self.llm.with_structured_output(CompetitorList).ainvoke(prompt)
            self.logger.info(f"o3-mini identified {len(response.direct_competitors)} direct and {len(response.indirect_competitors)} indirect competitors")
            return response
        except Exception as e:
            self.logger.error(f"LLM competitor analysis failed: {e}")
            # Return empty structure on failure
            return CompetitorList(
                direct_competitors=[],
                indirect_competitors=[],
                analysis_summary="Analysis failed - using fallback method"
            )

    def _build_company_context(self, company_info: Dict[str, Any]) -> str:
        """Build comprehensive context about the company for the LLM"""
        
        context_parts = []
        
        # Basic company info
        if company_info.get('company'):
            context_parts.append(f"**Company Name:** {company_info['company']}")
        
        if company_info.get('description'):
            context_parts.append(f"**Description:** {company_info['description']}")
        
        if company_info.get('industry'):
            context_parts.append(f"**Industry:** {company_info['industry']}")
        
        if company_info.get('sector'):
            context_parts.append(f"**Sector:** {company_info['sector']}")
        
        # Client and market info
        if company_info.get('clients_industries'):
            context_parts.append(f"**Client Industries:** {', '.join(company_info['clients_industries'])}")
        
        if company_info.get('known_clients'):
            context_parts.append(f"**Notable Clients:** {', '.join(company_info['known_clients'][:5])}")  # Limit to first 5
        
        if company_info.get('partners'):
            context_parts.append(f"**Partners:** {', '.join(company_info['partners'][:5])}")  # Limit to first 5
        
        return "\n".join(context_parts)

    async def _validate_and_enrich_with_tavily(self, company_name: str, initial_competitors: CompetitorList, company_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate the LLM results and find additional competitors using Tavily"""
        
        all_initial = initial_competitors.direct_competitors + initial_competitors.indirect_competitors
        validated_competitors = []
        
        # Validate each competitor and gather additional context
        validation_tasks = []
        for competitor in all_initial:
            validation_tasks.append(self._validate_competitor_with_search(company_name, competitor, company_info))
        
        # Also search for additional competitors
        search_tasks = [
            self._search_for_additional_competitors(company_name, company_info.get('sector', ''), company_info.get('industry', '')),
            self._search_competitor_lists(company_name)
        ]
        
        # Execute all tasks in parallel
        validation_results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Process validation results
        for i, result in enumerate(validation_results):
            if isinstance(result, Exception):
                self.logger.warning(f"Validation failed for {all_initial[i]}: {result}")
                # Add without validation if search fails
                validated_competitors.append({
                    "name": all_initial[i],
                    "description": f"Competitor in {company_info.get('sector', 'same industry')}",
                    "reasoning": f"Identified by AI analysis as competitor to {company_name}",
                    "confidence_score": 0.7,
                    "source": "llm_analysis"
                })
            else:
                validated_competitors.extend(result)
        
        # Process additional search results
        additional_competitors = set()
        for result in search_results:
            if not isinstance(result, Exception) and result:
                additional_competitors.update(result)
        
        # Add new competitors found via search
        existing_names = {comp["name"].lower() for comp in validated_competitors}
        for competitor_name in additional_competitors:
            if competitor_name.lower() not in existing_names and competitor_name.lower() != company_name.lower():
                validated_competitors.append({
                    "name": competitor_name,
                    "description": f"Competitor in {company_info.get('sector', 'same industry')}",
                    "reasoning": f"Found through web search as competitor to {company_name}",
                    "confidence_score": 0.6,
                    "source": "web_search"
                })
        
        # Sort by confidence and limit results
        validated_competitors.sort(key=lambda x: x["confidence_score"], reverse=True)
        return validated_competitors[:15]  # Return top 15 competitors

    async def _validate_competitor_with_search(self, company_name: str, competitor: str, company_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate a single competitor using web search"""
        
        try:
            # Search for the competitor in relation to the company
            query = f'"{competitor}" vs "{company_name}" comparison'
            results = await self.tavily.search(query=query, max_results=3)
            
            if results and results.get("results"):
                # If we find search results, it's likely a valid competitor
                return [{
                    "name": competitor,
                    "description": f"Competitor in {company_info.get('sector', 'same industry')}",
                    "reasoning": f"Validated through web search as competitor to {company_name}",
                    "confidence_score": 0.8,
                    "source": "llm_plus_web_validation"
                }]
            else:
                # No results found, lower confidence
                return [{
                    "name": competitor,
                    "description": f"Potential competitor in {company_info.get('sector', 'same industry')}",
                    "reasoning": f"Identified by AI analysis but not validated by web search",
                    "confidence_score": 0.5,
                    "source": "llm_analysis_only"
                }]
                
        except Exception as e:
            self.logger.warning(f"Search validation failed for {competitor}: {e}")
            return [{
                "name": competitor,
                "description": f"Competitor in {company_info.get('sector', 'same industry')}",
                "reasoning": f"Identified by AI analysis",
                "confidence_score": 0.6,
                "source": "llm_analysis"
            }]

    async def _search_for_additional_competitors(self, company_name: str, sector: str, industry: str) -> Set[str]:
        """Search for additional competitors not found by the LLM"""
        
        competitors = set()
        
        # Search queries designed to find competitor lists
        queries = [
            f'"{company_name}" competitors list {sector}',
            f'alternatives to "{company_name}" {industry}',
            f'companies like "{company_name}" {sector}'
        ]
        
        for query in queries:
            try:
                results = await self.tavily.search(query=query, max_results=5)
                if results and results.get("results"):
                    # Extract company names from the content
                    content = " ".join([r.get("content", "") for r in results["results"]])
                    extracted = await self._extract_company_names_from_text(content, company_name)
                    competitors.update(extracted)
            except Exception as e:
                self.logger.warning(f"Additional competitor search failed for query '{query}': {e}")
        
        return competitors

    async def _search_competitor_lists(self, company_name: str) -> Set[str]:
        """Search for existing competitor analysis or comparison pages"""
        
        competitors = set()
        
        try:
            query = f'"{company_name}" competitor analysis comparison'
            results = await self.tavily.search(query=query, max_results=5, include_answer=True)
            
            if results and results.get("results"):
                content = " ".join([r.get("content", "") for r in results["results"]])
                extracted = await self._extract_company_names_from_text(content, company_name)
                competitors.update(extracted)
                
        except Exception as e:
            self.logger.warning(f"Competitor list search failed: {e}")
        
        return competitors

    async def _extract_company_names_from_text(self, text: str, exclude_company: str) -> Set[str]:
        """Extract company names from text using a simple LLM call"""
        
        if not text.strip():
            return set()
        
        prompt = f"""Extract company names from the following text. Focus on companies that appear to be competitors or alternatives.

Rules:
- Extract only company names, not product names or generic terms
- Exclude "{exclude_company}"
- Return only legitimate company names
- One name per line

Text:
{text[:5000]}

Company names:"""

        try:
            # Use a simpler model for extraction
            simple_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=config.OPENAI_API_KEY)
            response = await simple_llm.ainvoke(prompt)
            
            names = set()
            for line in response.content.split('\n'):
                name = line.strip()
                if name and len(name) > 1 and name.lower() != exclude_company.lower():
                    # Basic validation
                    if not any(invalid in name.lower() for invalid in ['http', 'www', '.com', 'the ', 'and ']):
                        names.add(name)
            
            return names
            
        except Exception as e:
            self.logger.warning(f"Company name extraction failed: {e}")
            return set()

    async def run(self, state: ResearchState) -> ResearchState:
        """Main entry point for the agent."""
        
        websocket_manager, job_id = self.get_websocket_info(state)
        self.log_agent_start(state)

        company_info = state.get('company_info', {})
        
        if not company_info.get('company'):
            error_msg = "No company information available for competitor discovery"
            self.logger.error(error_msg)
            await self.send_error_update(websocket_manager, job_id, error_msg, "Competitor Discovery")
            state['competitors'] = []
            return state

        try:
            # Discover competitors using the simplified method
            result = await self.discover_competitors(
                company_info=company_info,
                websocket_manager=websocket_manager,
                job_id=job_id
            )

            # Update the state with the discovered competitors
            state['competitors'] = result.get('competitors', [])
            
            self.log_agent_complete(state)
            return state
            
        except Exception as e:
            error_msg = f"Competitor discovery failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            await self.send_error_update(websocket_manager, job_id, error_msg, "Competitor Discovery")
            state['competitors'] = []
            return state


# Keep the old class name for compatibility
FocusedCompetitorDiscoveryAgent = SimpleCompetitorDiscoveryAgent 