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


class CompanyInfo(BaseModel):
    company: str = Field(description="The company name")
    role: str = Field(description="The user's business role")
    description: str = Field(description="A brief description of what the company does")
    industry: str = Field(description="The primary industry sector")
    sector: str = Field(description="The primary sector of the company")
    clients_industries: List[str] = Field(description="The main industries of the clients of the company")
    known_clients: List[str] = Field(description="List of notable clients or customers", max_items=10)
    partners: List[str] = Field(description="List of partners of the company", max_items=10)


class CompanyInfoAgent(BaseAgent):
    def __init__(self, model_name: str = "gpt-4o-mini"):
        super().__init__(agent_type="company_info_agent")
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
                "known_clients": ["Amazon", "Google", "Uber", "Shopify", "Spotify"],
                "partners": ["Shopify", "WooCommerce", "Salesforce", "Microsoft"]
            }
        ]

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("user", "Please extract company information for:\n\nCompany: {company}\nRole: {role}\nAdditional Info: {additional_info}")
        ])

        self.chain = (
            {"company": RunnablePassthrough(), "role": RunnablePassthrough(), "additional_info": RunnablePassthrough()}
            | self.prompt
            | self.llm.with_structured_output(CompanyInfo)
        )

    def _get_system_prompt(self) -> str:
        return """You are an expert business analyst who extracts detailed company information.

Your task is to analyze the provided company information and create a comprehensive profile that includes industry classification and business relationships.

Guidelines:
1. Carefully read the additional information to understand what the company actually does
2. Use the business description to accurately determine the industry and sector
3. Be specific and accurate in your classifications based on actual business activities
4. Focus on extracting factual information about the company's business model and operations
5. Ensure all fields are populated with meaningful information based on actual business activities
6. DO NOT include competitors in this extraction - that will be handled separately"""

    async def _search_with_tavily(self, query: str, websocket_manager=None, job_id=None) -> Optional[str]:
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"Searching for: {query}",
                result={"step": "Company Info Extraction", "substep": "searching"}
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
                result={"step": "Company Info Extraction", "substep": "deep_extraction"}
            )

            # Try direct website crawling
            try:
                crawl_response = await self.tavily.search(
                    query=f"site:{url}",
                    search_depth="advanced",
                    max_results=5,
                    include_answer=True,
                    include_raw_content=True
                )
                if crawl_response.get("results"):
                    content = crawl_response["results"][0].get("content", "")
                    if content:
                        return content
            except Exception as e:
                self.logger.warning(f"Direct crawl failed for {url}: {e}")

            return ""

        except Exception as e:
            self.logger.error(f"Enhanced company info extraction error for {url}: {e}")
            return ""

    async def extract_company_info_async(self, company: str, role: str, company_url: Optional[str] = None, websocket_manager=None, job_id=None) -> Dict[str, Any]:
        """Extract company information without competitors."""
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"Starting company info extraction for {company}",
                result={"step": "Company Info Extraction", "substep": "initialization"}
            )

            # Discover or confirm URL
            if not company_url:
                company_url = await self._search_with_tavily(f"{company} official website", websocket_manager, job_id)

            # Scrape extended company info
            additional_info = ""
            if company_url:
                additional_info = await self._scrape_company_info(company_url, websocket_manager, job_id)

            # Run extraction chain with additional_info injected
            result = await self.chain.ainvoke({
                "company": company,
                "role": role,
                "additional_info": additional_info
            })

            company_info = result.model_dump()

            await self.send_status_update(
                websocket_manager, job_id,
                status="company_info_complete",
                message=f"Company info extraction completed for {company}",
                result={
                    "step": "Company Info Extraction",
                    "substep": "complete",
                    "company_info": company_info
                }
            )

            return company_info

        except Exception as e:
            error_msg = f"Error extracting company info for {company}: {str(e)}"
            self.log_agent_error({"company": company}, e)
            
            await self.send_error_update(
                websocket_manager, job_id,
                error_msg=error_msg,
                step="Company Info Extraction",
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
                "known_clients": [],
                "partners": []
            }

    async def run(self, state: InputState) -> ResearchState:
        """Main entry point for the company info agent."""
        company = state.get('company', 'Unknown Company')
        role = state.get('user_role', 'Unknown Role')
        company_url = state.get('company_url')
        websocket_manager, job_id = self.get_websocket_info(state)

        self.log_agent_start(state)

        # Extract company info
        company_info = await self.extract_company_info_async(
            company=company,
            role=role,
            company_url=company_url,
            websocket_manager=websocket_manager,
            job_id=job_id
        )
        
        self.logger.info(f"Company info extraction completed for {company}")

        # Create ResearchState with company info
        research_state = {
            # Copy input fields
            "company": state.get('company'),
            "company_url": state.get('company_url'),
            "user_role": state.get('user_role'),
            # Add company info (without competitors - they'll be added by CompetitorDiscoveryAgent)
            "company_info": company_info,
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