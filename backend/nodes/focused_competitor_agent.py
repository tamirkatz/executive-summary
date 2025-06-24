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


class FocusedCompetitorDiscoveryAgent(BaseAgent):
    """
    Focused competitor discovery agent that uses precise, targeted searches
    and robust validation to find real competitors.
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        super().__init__(agent_type="focused_competitor_discovery_agent")
        
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=config.OPENAI_API_KEY
        )
        
        self.tavily = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    async def discover_competitors(self, company: str, description: str, industry: str, 
                                 sector: str, websocket_manager=None, job_id=None) -> List[str]:
        """Discover competitors using focused, validated searches."""
        
        await self.send_status_update(
            websocket_manager, job_id,
            status="processing",
            message=f"🎯 Focused competitor discovery for {company}",
            result={"step": "Focused Competitor Discovery", "substep": "targeted_search"}
        )
        
        all_competitors = set()
        
        # Use targeted search with specific competitor-finding queries
        competitors = await self._targeted_competitor_search(company, description, industry, sector)
        all_competitors.update(competitors)
        
        # Use LLM to generate high-quality competitors based on industry knowledge
        llm_competitors = await self._llm_competitor_generation(company, description, industry, sector)
        all_competitors.update(llm_competitors)
        
        # Final validation and filtering
        validated_competitors = self._validate_and_filter_competitors(list(all_competitors), company)
        
        await self.send_status_update(
            websocket_manager, job_id,
            status="competitor_discovery_complete",
            message=f"✅ Found {len(validated_competitors)} validated competitors",
            result={"competitors": validated_competitors}
        )
        
        return validated_competitors

    async def _targeted_competitor_search(self, company: str, description: str, 
                                        industry: str, sector: str) -> Set[str]:
        """Perform targeted searches designed to find real competitors."""
        
        competitors = set()
        
        # Create very specific competitor-focused queries
        queries = []
        
        # Industry-specific competitor queries
        if "payment" in description.lower() or sector.lower() == "payments":
            queries.extend([
                "Stripe PayPal Square Adyen Braintree payment processing competitors",
                "payment gateway providers comparison Stripe alternatives",
                "fintech payment companies competing market leaders"
            ])
        elif "ecommerce" in description.lower() or "e-commerce" in description.lower():
            queries.extend([
                "Shopify WooCommerce BigCommerce Magento ecommerce platform competitors",
                "online store builders comparison alternatives",
                "ecommerce platforms market leaders"
            ])
        elif "communication" in description.lower() or "collaboration" in description.lower():
            queries.extend([
                "Slack Microsoft Teams Discord Zoom communication platform competitors",
                "business collaboration tools alternatives",
                "team communication software comparison"
            ])
        elif "crm" in description.lower() or "customer" in description.lower():
            queries.extend([
                "Salesforce HubSpot Pipedrive CRM competitors",
                "customer relationship management software alternatives",
                "CRM platforms comparison leaders"
            ])
        else:
            # Generic business software queries
            queries.extend([
                f"{sector} software companies market leaders",
                f"{industry} {sector} competitive analysis",
                f"top {sector.lower()} providers {industry.lower()}"
            ])
        
        # Execute searches
        for query in queries:
            try:
                results = await self.tavily.search(query=query, max_results=5, include_answer=True)
                extracted = self._extract_known_companies(results)
                competitors.update(extracted)
                self.logger.info(f"Query '{query}' found {len(extracted)} competitors")
            except Exception as e:
                self.logger.error(f"Targeted search failed for '{query}': {e}")
        
        return competitors

    async def _llm_competitor_generation(self, company: str, description: str, 
                                       industry: str, sector: str) -> Set[str]:
        """Use LLM to generate competitors based on industry knowledge."""
        
        prompt = f"""You are a business analyst with extensive knowledge of competitive landscapes.

Company: {company}
Description: {description}
Industry: {industry}
Sector: {sector}

Based on your knowledge, list the main direct competitors of {company}. Focus on:
1. Companies that serve similar customers
2. Companies with similar business models
3. Well-known players in the {industry} {sector} space
4. Companies customers would consider as alternatives

Return ONLY a simple list of company names, one per line. Do not include descriptions or explanations.
Maximum 8 competitors.

Example format:
PayPal
Square
Adyen

Competitors:"""

        try:
            result = await self.llm.ainvoke(prompt)
            content = result.content.strip()
            
            # Extract company names from response
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            competitors = set()
            for line in lines:
                # Clean up the line
                name = re.sub(r'^[-*•]\s*', '', line)  # Remove bullet points
                name = re.sub(r'\d+\.\s*', '', name)  # Remove numbers
                name = name.strip()
                
                if self._is_valid_competitor_name(name) and name.lower() != company.lower():
                    competitors.add(name)
            
            self.logger.info(f"LLM generated {len(competitors)} potential competitors")
            return competitors
            
        except Exception as e:
            self.logger.error(f"LLM competitor generation failed: {e}")
            return set()

    def _extract_known_companies(self, search_results: Dict) -> Set[str]:
        """Extract known company names using curated patterns and known entities."""
        
        companies = set()
        
        if not search_results.get("results"):
            return companies
        
        # Combine all content
        all_content = " ".join([
            result.get("content", "")
            for result in search_results["results"]
            if result.get("content")
        ])
        
        # Known company patterns - more restrictive
        known_companies = {
            # Payment companies
            "PayPal", "Square", "Adyen", "Braintree", "Worldpay", "Authorize.Net",
            "Checkout.com", "Mollie", "Klarna", "Afterpay", "Razorpay", "Payu",
            
            # Ecommerce platforms
            "Shopify", "WooCommerce", "BigCommerce", "Magento", "Wix", "Squarespace",
            "PrestaShop", "OpenCart", "Volusion", "Etsy", "Amazon", "eBay",
            
            # Communication/Collaboration
            "Microsoft Teams", "Teams", "Discord", "Zoom", "Google Meet", "Skype",
            "Mattermost", "Rocket.Chat", "Notion", "Asana", "Trello", "Monday.com",
            
            # CRM/Sales
            "Salesforce", "HubSpot", "Pipedrive", "Zoho", "Freshworks", "ActiveCampaign",
            "Mailchimp", "Constant Contact", "Sendinblue", "ConvertKit",
            
            # General tech companies
            "Microsoft", "Google", "Apple", "Meta", "Facebook", "LinkedIn", "Twitter",
            "Oracle", "SAP", "IBM", "Cisco", "Adobe", "Intuit", "ServiceNow"
        }
        
        # Look for these known companies in the content
        for company in known_companies:
            if company.lower() in all_content.lower():
                # Verify it appears in a competitive context
                context_keywords = ["competitor", "alternative", "vs", "versus", "compare", "similar", "like"]
                for keyword in context_keywords:
                    if keyword in all_content.lower():
                        companies.add(company)
                        break
                else:
                    # Also add if it appears multiple times (likely legitimate)
                    if all_content.lower().count(company.lower()) >= 2:
                        companies.add(company)
        
        # Additional pattern for "Company Name Inc/Corp/LLC" format
        corp_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Inc|Corp|Corporation|LLC|Ltd)\b'
        corp_matches = re.findall(corp_pattern, all_content)
        for match in corp_matches:
            if self._is_valid_competitor_name(match):
                companies.add(match)
        
        return companies

    def _is_valid_competitor_name(self, name: str) -> bool:
        """Strict validation for competitor names."""
        
        if not name or len(name) < 2:
            return False
        
        # Filter out obvious non-company terms
        invalid_terms = {
            'inc', 'corp', 'ltd', 'llc', 'company', 'co', 'corporation', 'limited',
            'the', 'and', 'or', 'but', 'with', 'for', 'to', 'at', 'by', 'from',
            'solution', 'platform', 'service', 'software', 'system', 'tool',
            'business', 'company', 'enterprise', 'companies', 'providers',
            'customers', 'clients', 'users', 'market', 'industry', 'sector',
            'api', 'app', 'web', 'site', 'page', 'data', 'tech', 'digital',
            'online', 'internet', 'cloud', 'mobile', 'social', 'network'
        }
        
        if name.lower() in invalid_terms:
            return False
        
        # Must be reasonable length (not too short or long)
        if len(name) < 3 or len(name) > 30:
            return False
        
        # Must start with capital letter
        if not name[0].isupper():
            return False
        
        # Must contain mostly letters
        letter_count = sum(1 for c in name if c.isalpha())
        if letter_count / len(name) < 0.6:
            return False
        
        # Filter out generic patterns
        if re.match(r'^[A-Z]{2,5}$', name):  # All caps acronyms
            return False
        
        return True

    def _validate_and_filter_competitors(self, competitors: List[str], target_company: str) -> List[str]:
        """Final validation and filtering with confidence scoring."""
        
        validated = []
        seen = set()
        
        # Create confidence scoring
        scored_competitors = []
        
        for competitor in competitors:
            # Skip target company
            if competitor.lower() == target_company.lower():
                continue
            
            # Skip duplicates
            comp_lower = competitor.lower()
            if comp_lower in seen:
                continue
            
            # Calculate confidence score
            confidence = self._calculate_confidence(competitor)
            
            if confidence >= 0.5:  # Minimum confidence threshold
                scored_competitors.append((competitor, confidence))
                seen.add(comp_lower)
        
        # Sort by confidence (highest first)
        scored_competitors.sort(key=lambda x: x[1], reverse=True)
        
        # Return top competitors
        validated = [comp[0] for comp in scored_competitors[:10]]
        
        self.logger.info(f"Validated {len(validated)} competitors from {len(competitors)} candidates")
        return validated

    def _calculate_confidence(self, company_name: str) -> float:
        """Calculate confidence score for a competitor name."""
        
        confidence = 0.5  # Base confidence
        
        # Known high-confidence companies
        high_confidence_companies = {
            "PayPal", "Square", "Adyen", "Braintree", "Shopify", "BigCommerce",
            "Microsoft Teams", "Teams", "Discord", "Zoom", "Salesforce", "HubSpot",
            "Google", "Microsoft", "Apple", "Meta", "Amazon", "Stripe"
        }
        
        if company_name in high_confidence_companies:
            confidence += 0.4
        
        # Length-based confidence (reasonable company names)
        if 4 <= len(company_name) <= 15:
            confidence += 0.1
        
        # Contains common company patterns
        if any(suffix in company_name for suffix in ["Corp", "Inc", "LLC", "Ltd"]):
            confidence += 0.1
        
        # Proper capitalization
        if company_name[0].isupper() and not company_name.isupper():
            confidence += 0.1
        
        return min(confidence, 1.0)

    async def run(self, state: ResearchState) -> ResearchState:
        """Main entry point for focused competitor discovery."""
        
        company = state.get('company', 'Unknown Company')
        company_info = state.get('company_info', {})
        
        description = company_info.get('description', '')
        industry = company_info.get('industry', 'Technology')
        sector = company_info.get('sector', 'Software')
        
        websocket_manager, job_id = self.get_websocket_info(state)

        self.log_agent_start(state)

        # Execute focused competitor discovery
        competitors = await self.discover_competitors(
            company=company,
            description=description,
            industry=industry,
            sector=sector,
            websocket_manager=websocket_manager,
            job_id=job_id
        )
        
        self.logger.info(f"🎯 Focused discovery found {len(competitors)} competitors for {company}")
        
        # Update state
        updated_state = state.copy()
        
        if 'company_info' in updated_state:
            updated_state['company_info']['competitors'] = competitors
        else:
            updated_state['company_info'] = {'competitors': competitors}

        self.log_agent_complete(state)
        return updated_state


# Use this as the main competitor discovery agent
CompetitorDiscoveryAgent = FocusedCompetitorDiscoveryAgent 