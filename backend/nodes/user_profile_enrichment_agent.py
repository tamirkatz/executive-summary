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
    customer_segments: List[str] = Field(description="List of customer segments of the company", max_items=10)
    known_clients: List[str] = Field(description="List of notable clients or customers", max_items=10)
    partners: List[str] = Field(description="List of partners of the company", max_items=10)
    use_cases: List[str] = Field(description="List of use cases for the company's products or services", max_items=10)
    core_products: List[str] = Field(description="List of core products or services of the company", max_items=10)
    synonyms: List[str] = Field(description="List of synonyms and jargons the company's products or services are known by", max_items=10)


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
                "customer_segments": ["E-commerce", "SaaS", "Marketplaces", "Subscription Services"],
                "known_clients": ["Amazon", "Google", "Uber", "Shopify", "Spotify"],
                "partners": ["Shopify", "WooCommerce", "Salesforce", "Microsoft"],
                "use_cases": ["Payment Processing", "Subscription Management", "E-commerce", "Marketplaces"],
                "core_products": ["Stripe API", "Stripe Checkout", "Stripe Connect", "Stripe Issuing"],
                "synonyms": ["Payment Processing", "Subscription Management", "E-commerce", "Marketplaces"]
            },
            {
                "company": "OpenAI",
                "role": "CPO",
                "description": "OpenAI is an AI research and deployment company. Our mission is to ensure that artificial general intelligence benefits all of humanity.",
                "industry": "Artificial Intelligence",
                "sector": "Machine Learning",
                "customer_segments": ["Technology", "Healthcare", "Finance", "Education", "Entertainment"],
                "known_clients": ["Microsoft", "GitHub", "Shopify", "Snapchat", "Duolingo"],
                "partners": ["Microsoft", "GitHub", "Salesforce", "Shopify"],
                "use_cases": ["AI Research", "AI Deployment", "AI Training", "AI Inference"],
                "core_products": ["OpenAI API", "OpenAI Models", "OpenAI Fine-tuning", "OpenAI Embeddings"],
                "synonyms": ["AI Research", "AI Deployment", "AI Training", "AI Inference"]
            },
            {
                "company": "Algolia",
                "role": "CTO",
                "description": "Algolia is a search-as-a-service platform that provides APIs for building fast, relevant search experiences in applications and websites.",
                "industry": "Search Technology",
                "sector": "API Services",
                "customer_segments": ["E-commerce", "SaaS", "Media", "Enterprise Software"],
                "known_clients": ["Medium", "Stripe", "Twitch", "Periscope", "Product Hunt"],
                "partners": ["Shopify", "Magento", "WordPress", "Netlify"],
                "use_cases": ["Search Experience", "Search Optimization", "Search Personalization", "Search Analytics"],
                "core_products": ["Algolia API", "Algolia InstantSearch", "Algolia Search API", "Algolia Search SDK"],
                "synonyms": ["Search Experience", "Search Optimization", "Search Personalization", "Search Analytics"]
            },
            {
              "company":"Tavily",
              "role":"CEO",
              "description":"Tavily is a search engine, designed for AI agents.",
              "industry":"AI agents search",
              "sector":"Search Engine",
              "customer_segments":["B2B saas"],
              "known_clients":["AI companies", "Research teams"],
              "partners":["IBM","Nvidia","Langchain"],
              "use_cases":["AI agents search"],
              "core_products":["Tavily API", "Tavily Search API", "Tavily Search SDK", "Tavily Search API"],
              "synonyms":["Rag pipeline", "Rag search", "Rag search engine", "Rag search API","agent search"]
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
            f"Company: {ex['company']}\nRole: {ex['role']}\nDescription: {ex['description']}\nIndustry: {ex['industry']}\nSector: {ex['sector']}\nClients Industries: {', '.join(ex.get('customer_segments', []))}\nKnown Clients: {', '.join(ex.get('known_clients', []))}\nPartners: {', '.join(ex.get('partners', []))}"
            for ex in self.examples
        ])

        return f"""You are an expert business analyst who enriches user profiles with detailed company information.

Your task is to analyze the provided company information and create a comprehensive profile that includes industry classification, competitive landscape, and business relationships.

Examples of enriched profiles:

{examples_text}

Guidelines:
1. FIRST and MOST IMPORTANT: Carefully read the additional information to understand what the company actually does
2. Use the business description to accurately determine the industry and sector (don't assume based on company name alone)
3. Be specific and accurate in your classifications based on actual business activities:
   - API/Search companies: "Search Technology", "API Services", or "Developer Tools"
   - AI/ML platforms: "Artificial Intelligence" or "Machine Learning Platform"  
   - SaaS tools: "Software as a Service" or specific vertical (e.g., "Marketing Technology")
   - E-commerce: "E-commerce Platform" or "Online Retail"
   - Fintech: "Financial Technology" or specific area (e.g., "Payment Processing")
8. Consider the user's role when determining what information is most important
9. Keep lists concise but comprehensive (max 10 items each)
10. Ensure all fields are populated with meaningful information based on actual business activities
11. For technology companies, be precise about their technology focus in both industry and sector fields"""


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
        """Enhanced company information extraction using comprehensive Tavily crawling."""
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"Deep crawling business information from {url}",
                result={"step": "Profile Enrichment", "substep": "deep_extraction"}
            )

            # Step 1: Multi-angle business information gathering
            business_info_sources = []
            
            # Try direct website crawling first
            try:
                crawl_response = await self.tavily.search(
                    query=f"site:{url}",
                    search_depth="advanced",
                    max_results=5,
                    include_answer=True,
                    include_raw_content=True
                )
                if crawl_response.get("results"):
                    for result in crawl_response["results"]:
                        if result.get("content"):
                            business_info_sources.append({
                                "source": "direct_crawl",
                                "content": result["content"],
                                "url": result.get("url", url)
                            })
            except Exception as e:
                self.logger.warning(f"Direct crawl failed for {url}: {e}")

            # Step 2: Targeted business description search
            targeted_queries = [
                f"site:{url} \"what we do\" OR \"about us\" OR \"company overview\"",
                f"site:{url} \"our mission\" OR \"our vision\" OR \"our products\"",
                f"site:{url} \"services\" OR \"solutions\" OR \"platform\"",
                f"site:{url} \"technology\" OR \"API\" OR \"software\""
            ]

            for query in targeted_queries:
                try:
                    response = await self.tavily.search(
                        query=query,
                        max_results=3,
                        include_answer=True
                    )
                    if response.get("results"):
                        for result in response["results"]:
                            if result.get("content"):
                                business_info_sources.append({
                                    "source": "targeted_search",
                                    "content": result["content"],
                                    "query": query
                                })
                except Exception as e:
                    self.logger.warning(f"Targeted search failed for query {query}: {e}")

            # Step 3: Extract and synthesize business description
            if business_info_sources:
                business_description = await self._synthesize_business_description(
                    business_info_sources, url, websocket_manager, job_id
                )
                return business_description
            else:
                # Fallback: Company name search
                return await self._fallback_company_search(url, websocket_manager, job_id)

        except Exception as e:
            self.logger.error(f"Enhanced company info extraction error for {url}: {e}")
            return await self._fallback_company_search(url, websocket_manager, job_id)

    async def _synthesize_business_description(self, sources: List[Dict], url: str, websocket_manager=None, job_id=None) -> str:
        """Synthesize accurate business description from multiple sources."""
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message="Synthesizing business description from multiple sources",
                result={"step": "Profile Enrichment", "substep": "synthesis"}
            )

            # Combine all content
            all_content = []
            for source in sources:
                content = source.get("content", "").strip()
                if content and len(content) > 50:  # Filter out very short content
                    all_content.append(content)

            if not all_content:
                return ""

            # Use LLM to extract and synthesize the core business description
            synthesis_prompt = f"""You are a business intelligence expert analyzing company information.

Website: {url}
Raw Content Sources: {len(all_content)} sources

Content to analyze:
{chr(10).join([f"Source {i+1}: {content[:500]}..." for i, content in enumerate(all_content)])}

Extract the most accurate, concise business description that clearly explains:
1. What this company actually does (products/services)
2. Their primary business model (B2B, B2C, API, SaaS, etc.)
3. Their target market/customers
4. Their key technology or approach (if technical company)

CRITICAL INSTRUCTIONS:
- Focus on FACTUAL business activities, not marketing language
- If it's a technology company, clearly identify the technology type (AI, search, API, etc.)
- If it's an API/service provider, specify what the API/service does
- Avoid generic terms like "innovative solutions" or "cutting-edge"
- Be specific about the actual product or service offered
- Maximum 2-3 sentences but be comprehensive

Business Description:"""

            result = await self.llm.ainvoke(synthesis_prompt)
            business_description = result.content.strip()
            
            self.logger.info(f"Synthesized business description for {url}: {business_description[:100]}...")
            return business_description

        except Exception as e:
            self.logger.error(f"Business description synthesis error: {e}")
            return " ".join(all_content)[:500] if all_content else ""

    async def _fallback_company_search(self, url: str, websocket_manager=None, job_id=None) -> str:
        """Fallback method for company information when direct crawling fails."""
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message="Using fallback business information search",
                result={"step": "Profile Enrichment", "substep": "fallback_search"}
            )

            # Extract company name from URL
            company_name = url.replace("https://", "").replace("http://", "").replace("www.", "").split(".")[0]
            
            # Search for company information
            fallback_query = f'"{company_name}" company business model what they do products services'
            response = await self.tavily.search(
                query=fallback_query,
                max_results=3,
                include_answer=True
            )
            
            if response.get("results") and response["results"][0].get("content"):
                return response["results"][0]["content"]
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Fallback company search error: {e}")
            return ""

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

            company_description = enriched_data.get("description", "") or additional_info
            industry = enriched_data.get("industry", "Technology")
            sector = enriched_data.get("sector", "Software")
            

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
                "customer_segments": [],
                "known_clients": [],
                "partners": [],
                "use_cases": [],
                "core_products": [],
                "synonyms": []
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
            "known_clients": enriched_profile.get("known_clients", []),
            "use_cases": enriched_profile.get("use_cases", []),
            "core_products": enriched_profile.get("core_products", []),
            "synonyms": enriched_profile.get("synonyms", []),
            "customer_segments": enriched_profile.get("customer_segments", []),
            # Pass through websocket info
            "websocket_manager": websocket_manager,
            "job_id": job_id
        }

        self.log_agent_complete(state)
        return research_state
