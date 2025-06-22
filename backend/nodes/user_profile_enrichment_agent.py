import os
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from backend.config import config
from tavily import AsyncTavilyClient
from ..classes import InputState, ResearchState
from ..agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class EnrichedProfile(BaseModel):
    company: str = Field(description="The company name")
    role: str = Field(description="The user's business role")
    description: str = Field(description="A brief description of what the company does")
    industry: str = Field(description="The primary industry sector")
    sector: str = Field(description="The primary sector of the company")
    clients_industries: List[str] = Field(description="The main industries of the clients of the company")
    competitors: List[str] = Field(description="List of main competitors", max_items=10)
    known_clients: List[str] = Field(description="List of notable clients or customers", max_items=10)
    partners: List[str] = Field(description="List of partners of the company", max_items=10)


class UserProfileEnrichmentAgent(BaseAgent):
    def __init__(self, model_name: str = "gpt-4o-mini"):
        super().__init__(agent_type="profile_enrichment_agent")
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.1,
            api_key=config.OPENAI_API_KEY
        )

        self.tavily = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

        self.examples = [
            {
                "company": "Stripe",
                "role": "CEO",
                "description": "Stripe is a technology company that builds economic infrastructure for the internet. Businesses of every size—from new startups to Fortune 500s—use our software to accept payments and grow their revenue globally.",
                "industry": "Financial Technology",
                "sector": "Payments",
                "clients_industries": ["E-commerce", "SaaS", "Marketplaces", "Subscription Services"],
                "competitors": ["PayPal", "Square", "Adyen", "Braintree", "Checkout.com"],
                "known_clients": ["Amazon", "Google", "Uber", "Shopify", "Spotify"],
                "partners": ["Shopify", "WooCommerce", "Salesforce", "Microsoft"]
            },
            {
                "company": "OpenAI",
                "role": "CPO",
                "description": "OpenAI is an AI research and deployment company. Our mission is to ensure that artificial general intelligence benefits all of humanity.",
                "industry": "Artificial Intelligence",
                "sector": "Machine Learning",
                "clients_industries": ["Technology", "Healthcare", "Finance", "Education", "Entertainment"],
                "competitors": ["Anthropic", "Google DeepMind", "Microsoft", "Meta AI", "Cohere"],
                "known_clients": ["Microsoft", "GitHub", "Shopify", "Snapchat", "Duolingo"],
                "partners": ["Microsoft", "GitHub", "Salesforce", "Shopify"]
            }
        ]

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("user", "Please enrich the profile for:\n\nCompany: {company}\nRole: {role}\nAdditional Info: {additional_info}")
        ])

        self.chain = (
            {"company": RunnablePassthrough(), "role": RunnablePassthrough(), "additional_info": RunnablePassthrough()}
            | self.prompt
            | self.llm.with_structured_output(EnrichedProfile)
        )

    def _get_system_prompt(self) -> str:
        examples_text = "\n\n".join([
            f"Company: {ex['company']}\nRole: {ex['role']}\nDescription: {ex['description']}\nIndustry: {ex['industry']}\nSector: {ex['sector']}\nClients Industries: {', '.join(ex['clients_industries'])}\nCompetitors: {', '.join(ex['competitors'])}\nKnown Clients: {', '.join(ex['known_clients'])}\nPartners: {', '.join(ex['partners'])}"
            for ex in self.examples
        ])

        return f"""You are an expert business analyst who enriches user profiles with detailed company information.

Your task is to analyze the provided company information and create a comprehensive profile that includes industry classification, competitive landscape, and business relationships.

Examples of enriched profiles:

{examples_text}

Guidelines:
1. Be specific and accurate in your classifications
2. Focus on the most relevant DIRECT competitors (companies offering similar products/services to similar customers)
3. Consider the user's role when determining what information is most important
4. Use the additional information provided to enhance the profile
5. For competitors, prioritize companies that customers would compare or choose between
6. Avoid including partners, vendors, or companies in completely different industries as competitors
7. If information is not available, make reasonable inferences based on the company name and industry
8. Keep lists concise but comprehensive (max 10 items each)
9. Ensure all fields are populated with meaningful information"""

    async def _search_with_tavily(self, query: str, websocket_manager=None, job_id=None) -> Optional[str]:
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"Searching for: {query}",
                result={"step": "Profile Enrichment", "substep": "searching"}
            )

            results = await self.tavily.search(query=query)
            return results["results"][0]["url"] if results["results"] else None
        except Exception as e:
            self.logger.error(f"Tavily search error: {e}")
            return None

    async def _scrape_company_info(self, url: str, websocket_manager=None, job_id=None) -> str:
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"Extracting company information from {url}",
                result={"step": "Profile Enrichment", "substep": "extracting"}
            )

            response = await self.tavily.search(query=f"site:{url} company description OR about us")
            return response["results"][0]["content"] if response["results"] else ""
        except Exception as e:
            self.logger.error(f"Company info extraction error: {e}")
            return ""

    async def _find_competitors_with_llm(self, company: str, websocket_manager=None, job_id=None) -> List[str]:
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"Finding competitors for {company}",
                result={"step": "Profile Enrichment", "substep": "competitor_analysis"}
            )

            # Direct GPT query for competitor identification
            competitor_prompt = f"""You are a business intelligence expert with comprehensive knowledge of companies and competitive landscapes.

Identify the main direct competitors of {company}.

Consider companies that:
1. Operate in the same industry and market segment as {company}
2. Offer similar products or services
3. Target similar customer demographics
4. Would be considered alternatives that customers compare when making purchasing decisions

IMPORTANT RULES:
- Return ONLY company names (no descriptions, explanations, or additional text)
- Separate names with commas
- Do NOT include {company} itself
- Do NOT include customers, partners, suppliers, or vendors
- Do NOT include generic terms like "startups", "companies", "businesses"
- Focus on DIRECT competitors, not just companies in the same broad industry
- Maximum 8 competitors
- Use well-known, established competitor names

Main competitors of {company}:"""

            result = await self.llm.ainvoke(competitor_prompt)
            raw_competitors = result.content.strip()
            
            # Clean and validate extracted competitors
            competitors = []
            if raw_competitors:
                potential_competitors = [c.strip() for c in raw_competitors.split(",") if c.strip()]
                
                for competitor in potential_competitors:
                    # Clean up the competitor name
                    cleaned = self._clean_competitor_name(competitor)
                    
                    # Validate it looks like a real company name
                    if self._validate_competitor_name(cleaned, company):
                        competitors.append(cleaned)
            
            self.logger.info(f"GPT identified {len(competitors)} competitors for {company}: {competitors}")
            return competitors[:10]  # Limit to top 10 competitors
            
        except Exception as e:
            self.logger.error(f"Competitor analysis error: {e}")
            return []

    def _clean_competitor_name(self, name: str) -> str:
        """Clean and normalize competitor names."""
        # Remove common prefixes/suffixes and clean formatting
        name = name.strip()
        
        # Remove quotes and extra whitespace
        name = name.replace('"', '').replace("'", "").strip()
        
        # Remove common business suffixes for cleaner names (but keep them if they're part of the brand)
        # Don't remove if it's clearly part of the brand name
        suffixes_to_consider = [' Inc', ' Inc.', ' Corp', ' Corp.', ' LLC', ' Ltd', ' Ltd.', ' Co', ' Co.']
        
        # Only remove if the name would still be meaningful without it
        for suffix in suffixes_to_consider:
            if name.endswith(suffix) and len(name.replace(suffix, '').strip()) > 2:
                name = name.replace(suffix, '').strip()
                break
        
        return name

    def _validate_competitor_name(self, name: str, company: str) -> bool:
        """Validate that a competitor name looks legitimate."""
        if not name or len(name) < 2:
            return False
        
        # Don't include the company itself
        if name.lower() == company.lower():
            return False
        
        # Filter out generic terms
        generic_terms = {
            'competitors', 'companies', 'startups', 'businesses', 'firms', 'services', 
            'solutions', 'platforms', 'providers', 'vendors', 'others', 'alternatives',
            'industry', 'market', 'sector', 'players', 'leaders', 'enterprises'
        }
        
        if name.lower() in generic_terms:
            return False
        
        # Filter out names that are too short or look like fragments
        if len(name) < 3 or name.count(' ') > 5:  # Avoid very short names or very long descriptions
            return False
        
        # Must start with a capital letter (proper company names do)
        if not name[0].isupper():
            return False
        
        return True



    async def _get_fallback_competitors(self, company: str, industry: str) -> List[str]:
        """Fallback method to identify competitors when online search fails."""
        try:
            fallback_prompt = f"""You are a business intelligence expert. Based on your knowledge, identify the main competitors for {company} in the {industry} industry.

Consider companies that:
1. Operate in the same market segment as {company}
2. Offer similar products or services
3. Target similar customer demographics
4. Are well-known players in the {industry} space

Return only the company names separated by commas, maximum 5 competitors.
Focus on established, well-known competitors that would be considered direct rivals.

Main competitors of {company}:"""

            result = await self.llm.ainvoke(fallback_prompt)
            competitors = [c.strip() for c in result.content.split(",") if c.strip()]
            
            # Validate fallback competitors
            validated = []
            for competitor in competitors:
                cleaned = self._clean_competitor_name(competitor)
                if self._validate_competitor_name(cleaned, company):
                    validated.append(cleaned)
            
            return validated[:5]  # Return max 5 fallback competitors
            
        except Exception as e:
            self.logger.error(f"Fallback competitor identification failed: {e}")
            return []

    async def enrich_profile_async(self, company: str, role: str, company_url: Optional[str] = None, websocket_manager=None, job_id=None) -> Dict[str, Any]:
        """Async version of enrich_profile with websocket integration."""
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"Starting profile enrichment for {company}",
                result={"step": "Profile Enrichment", "substep": "initialization"}
            )

            # Discover or confirm URL
            if not company_url:
                company_url = await self._search_with_tavily(f"{company} official website", websocket_manager, job_id)

            # Scrape extended company info
            additional_info = ""
            if company_url:
                additional_info = await self._scrape_company_info(company_url, websocket_manager, job_id)

            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"Analyzing company profile for {company}",
                result={"step": "Profile Enrichment", "substep": "analysis"}
            )

            # Run enrichment chain with additional_info injected
            result = await self.chain.ainvoke({
                "company": company,
                "role": role,
                "additional_info": additional_info
            })

            enriched_data = result.model_dump()

            # ENHANCED: Merge LLM-generated competitors from profile with direct LLM competitor query
            llm_competitors = enriched_data.get("competitors", [])
            fresh_competitors = await self._find_competitors_with_llm(company, websocket_manager, job_id)
            
            # Combine and deduplicate competitors from both sources
            all_competitors = []
            seen_competitors = set()
            
            # Prioritize fresh competitors (more accurate)
            for competitor in fresh_competitors:
                competitor_lower = competitor.lower()
                if competitor_lower not in seen_competitors:
                    all_competitors.append(competitor)
                    seen_competitors.add(competitor_lower)
            
            # Add LLM competitors that aren't duplicates
            for competitor in llm_competitors:
                competitor_lower = competitor.lower()
                if competitor_lower not in seen_competitors and len(all_competitors) < 10:
                    all_competitors.append(competitor)
                    seen_competitors.add(competitor_lower)
            
            # Use fallback if no competitors found
            if len(all_competitors) == 0:
                industry = enriched_data.get("industry", "Unknown")
                fallback_competitors = await self._get_fallback_competitors(company, industry)
                all_competitors.extend(fallback_competitors)
                self.logger.info(f"Used fallback competitor identification for {company}, found: {fallback_competitors}")
            
            enriched_data["competitors"] = all_competitors[:10]  # Limit to top 10

            await self.send_status_update(
                websocket_manager, job_id,
                status="profile_complete",
                message=f"Profile enrichment completed for {company}",
                result={
                    "step": "Profile Enrichment",
                    "substep": "complete",
                    "profile": enriched_data
                }
            )

            return enriched_data

        except Exception as e:
            error_msg = f"Error enriching profile for {company}: {str(e)}"
            self.log_agent_error({"company": company}, e)
            
            await self.send_error_update(
                websocket_manager, job_id,
                error_msg=error_msg,
                step="Profile Enrichment",
                continue_research=True
            )

            # Return fallback profile
            return {
                "company": company,
                "role": role,
                "description": "A company in the business sector",
                "industry": "Unknown",
                "sector": "Unknown",
                "clients_industries": [],
                "competitors": [],
                "known_clients": [],
                "partners": []
            }

        """Synchronous version of enrich_profile for backward compatibility."""
        try:
            # Discover or confirm URL
            if not company_url:
                # Note: This would need to be made async or use sync client
                pass

            # Run enrichment chain with additional_info injected
            result = self.chain.invoke({
                "company": company,
                "role": role,
                "additional_info": ""
            })

            enriched_data = result.model_dump()

            return enriched_data

        except Exception as e:
            self.logger.error(f"Error enriching profile for {company}: {e}")
            return {
                "company": company,
                "role": role,
                "description": "A company in the business sector",
                "industry": "Unknown",
                "sector": "Unknown",
                "clients_industries": [],
                "competitors": [],
                "known_clients": [],
                "partners": []
            }

    async def run(self, state: InputState) -> ResearchState:
        """Main entry point for the profile enrichment agent following the common node pattern."""
        company = state.get('company', 'Unknown Company')
        role = state.get('user_role', 'Unknown Role')
        company_url = state.get('company_url')
        websocket_manager, job_id = self.get_websocket_info(state)

        self.log_agent_start(state)

        # Enrich the profile
        enriched_profile = await self.enrich_profile_async(
            company=company,
            role=role,
            company_url=company_url,
            websocket_manager=websocket_manager,
            job_id=job_id
        )
        
        # Log competitor identification results for debugging
        competitors = enriched_profile.get('competitors', [])
        self.logger.info(f"Profile enrichment completed for {company}. Found {len(competitors)} competitors: {competitors[:5]}")
        
        if not competitors:
            self.logger.warning(f"No competitors identified for {company}. This may indicate an issue with competitor discovery.")

        # Create ResearchState with enriched profile
        research_state = {
            # Copy input fields
            "company": state.get('company'),
            "company_url": state.get('company_url'),
            "user_role": state.get('user_role'),
            # Add enriched profile
            "profile": enriched_profile,
            # Initialize research fields
            "messages": [],
            "site_scrape": {},
            "financial_data": {},
            "news_data": {},
            "company_data": {},
            "curated_financial_data": {},
            "curated_news_data": {},
            "curated_company_data": {},
            "financial_briefing": "",
            "news_briefing": "",
            "company_briefing": "",
            "references": [],
            "briefings": {},
            "report": "",
            # Initialize query generation fields
            "generated_queries": [],
            "query_generation_complete": False,
            "categorized_queries": {},
            "total_queries": 0,
            "query_collection_complete": False,
            # Pass through websocket info
            "websocket_manager": websocket_manager,
            "job_id": job_id
        }

        self.log_agent_complete(state)
        return research_state
