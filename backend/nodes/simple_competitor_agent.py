import os
import logging
import asyncio
import json
import re
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from backend.config import config
from tavily import AsyncTavilyClient
from ..classes import ResearchState
from ..agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SimpleCompetitor(BaseModel):
    name: str = Field(description="Competitor company name")
    confidence: float = Field(description="Confidence score 0-1")
    source: str = Field(description="How it was discovered")


class SimpleCompetitorDiscoveryAgent(BaseAgent):
    """
    Simple, robust competitor discovery agent that focuses on reliable results.
    Uses multiple discovery strategies with fallback mechanisms.
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        super().__init__(agent_type="simple_competitor_discovery_agent")
        
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=config.OPENAI_API_KEY
        )
        
        self.tavily = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    async def discover_competitors(self, company: str, description: str, industry: str, 
                                 sector: str, websocket_manager=None, job_id=None) -> List[str]:
        """Discover competitors using multiple robust strategies."""
        
        await self.send_status_update(
            websocket_manager, job_id,
            status="processing",
            message=f"🔍 Discovering competitors for {company}",
            result={"step": "Competitor Discovery", "substep": "multi_strategy"}
        )
        
        all_competitors = set()
        
        # Strategy 1: Direct search patterns
        competitors_1 = await self._strategy_direct_search(company, description, industry, sector)
        all_competitors.update(competitors_1)
        
        # Strategy 2: Industry leaders search  
        competitors_2 = await self._strategy_industry_leaders(industry, sector)
        all_competitors.update(competitors_2)
        
        # Strategy 3: Alternative solutions search
        competitors_3 = await self._strategy_alternative_solutions(description, sector)
        all_competitors.update(competitors_3)
        
        # Filter and validate
        validated_competitors = self._validate_competitors(list(all_competitors), company)
        
        await self.send_status_update(
            websocket_manager, job_id,
            status="competitor_discovery_complete",
            message=f"✅ Found {len(validated_competitors)} competitors",
            result={"competitors": validated_competitors}
        )
        
        return validated_competitors

    async def _strategy_direct_search(self, company: str, description: str, 
                                    industry: str, sector: str) -> Set[str]:
        """Strategy 1: Direct competitor search patterns."""
        
        competitors = set()
        
        # Extract key terms from description
        key_terms = self._extract_key_terms(description)
        
        queries = [
            f"top {sector.lower()} companies {industry.lower()}",
            f"leading {sector.lower()} providers 2024", 
            f"{industry} {sector} vendors comparison",
            f"companies like {company} {sector.lower()}"
        ]
        
        # Add key term specific queries
        for term in key_terms[:2]:  # Use top 2 key terms
            queries.append(f"{term} companies providers platforms")
        
        for query in queries:
            try:
                results = await self.tavily.search(query=query, max_results=5)
                competitors.update(self._extract_companies_from_results(results))
            except Exception as e:
                self.logger.error(f"Direct search failed for '{query}': {e}")
        
        return competitors

    async def _strategy_industry_leaders(self, industry: str, sector: str) -> Set[str]:
        """Strategy 2: Industry leaders and market analysis search."""
        
        competitors = set()
        
        queries = [
            f"{industry} market leaders analysis",
            f"top 10 {sector.lower()} companies",
            f"{industry} competitive landscape 2024",
            f"market share {sector.lower()} {industry.lower()}"
        ]
        
        for query in queries:
            try:
                results = await self.tavily.search(query=query, max_results=5)
                competitors.update(self._extract_companies_from_results(results))
            except Exception as e:
                self.logger.error(f"Industry leaders search failed for '{query}': {e}")
        
        return competitors

    async def _strategy_alternative_solutions(self, description: str, sector: str) -> Set[str]:
        """Strategy 3: Alternative solutions and substitutes search."""
        
        competitors = set()
        
        # Create problem-solution based queries
        if "payment" in description.lower():
            queries = [
                "payment processing solutions businesses",
                "online payment platforms companies",
                "payment gateway providers"
            ]
        elif "api" in description.lower():
            queries = [
                "API platform providers companies",
                "developer tools API services",
                "software API solutions"
            ]
        elif any(term in description.lower() for term in ["software", "platform", "saas"]):
            queries = [
                f"{sector.lower()} software platforms",
                f"business {sector.lower()} solutions",
                f"enterprise {sector.lower()} providers"
            ]
        else:
            queries = [
                f"{sector.lower()} service providers",
                f"business {sector.lower()} companies"
            ]
        
        for query in queries:
            try:
                results = await self.tavily.search(query=query, max_results=5)
                competitors.update(self._extract_companies_from_results(results))
            except Exception as e:
                self.logger.error(f"Alternative solutions search failed for '{query}': {e}")
        
        return competitors

    def _extract_companies_from_results(self, search_results: Dict) -> Set[str]:
        """Extract company names from search results using pattern matching."""
        
        companies = set()
        
        if not search_results.get("results"):
            return companies
        
        # Combine all content
        all_content = " ".join([
            result.get("content", "")
            for result in search_results["results"]
            if result.get("content")
        ])
        
        # Company name patterns
        patterns = [
            # Companies with common suffixes
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Inc|Corp|Corporation|LLC|Ltd|Limited|Company|Co)\b',
            # Companies followed by "is a" or "provides"
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:is\s+a|provides|offers|enables)',
            # Listed companies (e.g., "including Company")
            r'(?:including|such\s+as|like)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            # Companies in competitive context
            r'(?:competitor|rival|alternative)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            # Market leader patterns
            r'(?:leader|leading)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            # Top companies patterns
            r'(?:top|major)\s+(?:companies|players|providers).*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            # Standalone capitalized names (more restrictive)
            r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, all_content, re.IGNORECASE)
            for match in matches:
                name = match.strip()
                if self._is_valid_company_name(name):
                    companies.add(name)
        
        return companies

    def _extract_key_terms(self, description: str) -> List[str]:
        """Extract key business terms from company description."""
        
        key_terms = []
        
        # Technology terms
        tech_terms = ["API", "platform", "software", "SaaS", "cloud", "service", "tool"]
        for term in tech_terms:
            if term.lower() in description.lower():
                key_terms.append(term)
        
        # Business model terms  
        business_terms = ["payment", "processing", "analytics", "data", "infrastructure", "automation"]
        for term in business_terms:
            if term.lower() in description.lower():
                key_terms.append(term)
        
        # Industry terms
        industry_terms = ["fintech", "ecommerce", "retail", "enterprise", "startup", "business"]
        for term in industry_terms:
            if term.lower() in description.lower():
                key_terms.append(term)
        
        return key_terms

    def _is_valid_company_name(self, name: str) -> bool:
        """Validate if a name looks like a real company name."""
        
        if not name or len(name) < 2:
            return False
        
        # Filter out generic terms
        generic_terms = {
            'companies', 'business', 'solution', 'platform', 'service', 'software',
            'system', 'tool', 'provider', 'vendor', 'client', 'customer', 'user',
            'market', 'industry', 'sector', 'company', 'corporation', 'inc', 'ltd'
        }
        
        if name.lower() in generic_terms:
            return False
        
        # Must start with capital letter
        if not name[0].isupper():
            return False
        
        # Must contain only letters, spaces, and common company chars
        if not re.match(r'^[A-Za-z\s\.\-&]+$', name):
            return False
        
        # Filter out single words that are too common
        if len(name.split()) == 1 and name.lower() in {
            'google', 'amazon', 'microsoft', 'apple', 'facebook', 'meta',
            'the', 'and', 'for', 'with', 'this', 'that', 'can', 'will'
        }:
            return False
        
        return True

    def _validate_competitors(self, competitors: List[str], target_company: str) -> List[str]:
        """Final validation and filtering of discovered competitors."""
        
        validated = []
        seen = set()
        
        for competitor in competitors:
            # Skip target company
            if competitor.lower() == target_company.lower():
                continue
            
            # Skip duplicates (case insensitive)
            comp_lower = competitor.lower()
            if comp_lower in seen:
                continue
            
            # Additional validation
            if self._is_valid_company_name(competitor) and len(competitor.strip()) > 2:
                validated.append(competitor.strip())
                seen.add(comp_lower)
        
        # Sort by length (shorter names first, usually more legitimate)
        validated.sort(key=len)
        
        # Return top 15 competitors
        return validated[:15]

    async def run(self, state: ResearchState) -> ResearchState:
        """Main entry point for simple competitor discovery."""
        
        company = state.get('company', 'Unknown Company')
        company_info = state.get('company_info', {})
        
        description = company_info.get('description', '')
        industry = company_info.get('industry', 'Technology')
        sector = company_info.get('sector', 'Software')
        
        websocket_manager, job_id = self.get_websocket_info(state)

        self.log_agent_start(state)

        # Execute simple competitor discovery
        competitors = await self.discover_competitors(
            company=company,
            description=description,
            industry=industry,
            sector=sector,
            websocket_manager=websocket_manager,
            job_id=job_id
        )
        
        self.logger.info(f"🎯 Simple discovery found {len(competitors)} competitors for {company}")
        
        # Update state
        updated_state = state.copy()
        
        if 'company_info' in updated_state:
            updated_state['company_info']['competitors'] = competitors
        else:
            updated_state['company_info'] = {'competitors': competitors}

        self.log_agent_complete(state)
        return updated_state


# Maintain backward compatibility
CompetitorDiscoveryAgent = SimpleCompetitorDiscoveryAgent 