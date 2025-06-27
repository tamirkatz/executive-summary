import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from tavily import AsyncTavilyClient
from ..classes import ResearchState
from ..agents.base_agent import BaseAgent
from ..config import config
logger = logging.getLogger(__name__)

class CompanyResearchAgent(BaseAgent):
    """
    Enhanced Company Research Agent that extracts factual, verifiable data about companies
    using advanced Tavily crawl capabilities and strategic intelligence gathering.
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        super().__init__(agent_type="company_research_agent")
        
        if not config.TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY is not configured")
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
            
        self.tavily_client = AsyncTavilyClient(api_key=config.TAVILY_API_KEY)
        self.openai_client = ChatOpenAI(
            model=model_name,
            temperature=0.1,
            api_key=config.OPENAI_API_KEY
        )
        
        # Enhanced Tavily crawl parameters for factual data extraction
        self.crawl_params = {
            "max_depth": 3,
            "max_breadth": 25,
            "limit": 60,
            "instructions": """Extract FACTUAL DATA ONLY: revenue numbers, customer names, product specifications, 
            technology stack, team size, geographic presence, specific partnerships. Ignore marketing language, 
            focus on verifiable data, concrete metrics, and specific technical details. Prioritize: 
            1) Financial data (revenue, funding, growth metrics)
            2) Product specifications and features
            3) Customer case studies with specific names
            4) Technology stack and architecture details
            5) Team size and organizational structure
            6) Geographic presence and office locations
            7) Partnership details and integration capabilities""",
            "categories": ["About", "Investors", "Customers", "Technology", "Careers", "Press", "Legal", "Products", "Solutions"],
            "exclude_paths": ["/blog/*", "/marketing/*", "/events/*", "/media/*", "/news/*"],
            "extract_depth": "advanced"
        }
        
        # Source reliability scoring
        self.source_reliability = {
            "sec_filing": 0.95,
            "company_website": 0.9,
            "job_posting": 0.85,
            "press_release": 0.8,
            "news_article": 0.7,
            "social_media": 0.5
        }

    async def run(self, state: ResearchState) -> Dict[str, Any]:
        """Main execution method for the Company Research Agent."""
        self.log_agent_start(state)
        company = state.get('company', 'Unknown Company')
        company_url = state.get('company_url', '')
        websocket_manager, job_id = self.get_websocket_info(state)
        
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🏢 Starting comprehensive company research for {company}",
                result={
                    "step": "Company Research Agent",
                    "company": company,
                    "phase": "initialization"
                }
            )
            
            # Initialize company intelligence structure
            company_intelligence = {
                "company_overview": {
                    "main_products": [],
                    "technology_stack": [],
                    "target_industries": [],
                    "key_customers": [],
                    "business_model": "",
                    "revenue_model": ""
                },
                "strategic_focus": {
                    "current_priorities": [],
                    "technology_investments": [],
                    "market_expansion": [],
                    "product_roadmap": []
                },
                "financial_status": {
                    "recent_funding": "",
                    "growth_indicators": [],
                    "partnerships": []
                },
                "organizational_insights": {
                    "hiring_trends": [],
                    "team_size": "",
                    "key_executives": [],
                    "geographic_presence": []
                },
                "data_sources": [],
                "last_updated": datetime.now().isoformat(),
                "reliability_score": 0.0
            }
            
            # Phase 1: Strategic Website Crawling
            if company_url:
                website_data = await self._crawl_company_website(
                    company, company_url, websocket_manager, job_id
                )
                if website_data:
                    company_intelligence = await self._integrate_website_data(
                        company_intelligence, website_data, websocket_manager, job_id
                    )
            
            # Phase 2: SEC Filing Analysis (for public companies)
            sec_data = await self._analyze_sec_filings(
                company, websocket_manager, job_id
            )
            if sec_data:
                company_intelligence = await self._integrate_sec_data(
                    company_intelligence, sec_data, websocket_manager, job_id
                )
            
            # Phase 3: Job Posting Analysis
            job_data = await self._analyze_job_postings(
                company, websocket_manager, job_id
            )
            if job_data:
                company_intelligence = await self._integrate_job_data(
                    company_intelligence, job_data, websocket_manager, job_id
                )
            
            # Phase 4: Financial and Partnership Data
            financial_data = await self._gather_financial_data(
                company, websocket_manager, job_id
            )
            if financial_data:
                company_intelligence = await self._integrate_financial_data(
                    company_intelligence, financial_data, websocket_manager, job_id
                )
            
            # Phase 5: Product and Customer Analysis
            product_data = await self._analyze_products_customers(
                company, websocket_manager, job_id
            )
            if product_data:
                company_intelligence = await self._integrate_product_data(
                    company_intelligence, product_data, websocket_manager, job_id
                )
            
            # Calculate overall reliability score
            company_intelligence["reliability_score"] = self._calculate_reliability_score(
                company_intelligence["data_sources"]
            )
            
            # Update state with comprehensive company data
            state['company_factual_data'] = {
                "website_analysis": company_intelligence.get("company_overview", {}),
                "financial_data": company_intelligence.get("financial_status", {}),
                "product_specifications": company_intelligence.get("strategic_focus", {}),
                "customer_segments": {
                    "key_customers": company_intelligence["company_overview"].get("key_customers", []),
                    "target_industries": company_intelligence["company_overview"].get("target_industries", [])
                },
                "technology_stack": {
                    "technologies": company_intelligence["company_overview"].get("technology_stack", []),
                    "investments": company_intelligence["strategic_focus"].get("technology_investments", [])
                },
                "organizational_structure": company_intelligence.get("organizational_insights", {}),
                "intelligence_summary": company_intelligence,
                "reliability_score": company_intelligence["reliability_score"]
            }
            
            # Add completion message
            completion_msg = f"✅ Company research complete for {company}. Extracted {len(company_intelligence['data_sources'])} verified sources with {company_intelligence['reliability_score']:.2f} reliability score."
            
            messages = state.get('messages', [])
            messages.append(AIMessage(content=completion_msg))
            state['messages'] = messages
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="completed",
                message=completion_msg,
                result={
                    "step": "Company Research Agent",
                    "company": company,
                    "sources_count": len(company_intelligence['data_sources']),
                    "reliability_score": company_intelligence['reliability_score'],
                    "key_findings": {
                        "products": len(company_intelligence["company_overview"].get("main_products", [])),
                        "customers": len(company_intelligence["company_overview"].get("key_customers", [])),
                        "technologies": len(company_intelligence["company_overview"].get("technology_stack", [])),
                        "partnerships": len(company_intelligence["financial_status"].get("partnerships", []))
                    }
                }
            )
            
            self.log_agent_complete(state)
            return state
            
        except Exception as e:
            error_msg = f"Error in Company Research Agent: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            await self.send_error_update(
                websocket_manager, job_id, error_msg, "Company Research Agent"
            )
            # Return state with empty data but don't fail
            state['company_factual_data'] = {
                "website_analysis": {},
                "financial_data": {},
                "product_specifications": {},
                "customer_segments": {},
                "technology_stack": {},
                "organizational_structure": {},
                "error": error_msg
            }
            return state

    async def _crawl_company_website(self, company: str, company_url: str, 
                                   websocket_manager=None, job_id=None) -> Optional[Dict[str, Any]]:
        """Perform strategic website crawling with fact-focused instructions."""
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🕷️ Crawling {company} website for factual data",
                result={"step": "Website Crawling", "url": company_url}
            )
            
            # Use Tavily crawl with enhanced parameters
            crawl_result = await self.tavily_client.crawl(
                url=company_url,
                **self.crawl_params
            )
            
            if not crawl_result or not crawl_result.get("results"):
                return None
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"✅ Crawled {len(crawl_result['results'])} pages from {company} website",
                result={
                    "step": "Website Crawling",
                    "pages_crawled": len(crawl_result['results']),
                    "categories_found": list(set(r.get('category', 'unknown') for r in crawl_result['results']))
                }
            )
            
            return {
                "source": "website_crawl",
                "url": company_url,
                "results": crawl_result["results"],
                "reliability": self.source_reliability["company_website"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error crawling company website: {e}")
            return None

    async def _analyze_sec_filings(self, company: str, websocket_manager=None, job_id=None) -> Optional[Dict[str, Any]]:
        """Analyze SEC filings for public companies."""
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"📋 Searching for SEC filings for {company}",
                result={"step": "SEC Analysis", "company": company}
            )
            
            # Search for SEC filings
            sec_queries = [
                f"{company} SEC filing 10-K annual report",
                f"{company} SEC filing 10-Q quarterly report",
                f"{company} SEC filing 8-K current report",
                f'site:sec.gov "{company}" financial statements'
            ]
            
            sec_results = []
            for query in sec_queries:
                try:
                    results = await self.tavily_client.search(
                        query=query,
                        search_depth="advanced",
                        max_results=3,
                        include_domains=["sec.gov", "edgar.sec.gov"]
                    )
                    
                    if results and results.get("results"):
                        sec_results.extend(results["results"])
                        
                except Exception as e:
                    self.logger.warning(f"SEC search failed for query '{query}': {e}")
                    continue
            
            if not sec_results:
                return None
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"✅ Found {len(sec_results)} SEC filing references for {company}",
                result={
                    "step": "SEC Analysis",
                    "filings_found": len(sec_results)
                }
            )
            
            return {
                "source": "sec_filings",
                "results": sec_results,
                "reliability": self.source_reliability["sec_filing"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing SEC filings: {e}")
            return None

    async def _analyze_job_postings(self, company: str, websocket_manager=None, job_id=None) -> Optional[Dict[str, Any]]:
        """Analyze job postings for strategic direction insights."""
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"💼 Analyzing job postings for {company} strategic insights",
                result={"step": "Job Analysis", "company": company}
            )
            
            # Search for recent job postings
            job_queries = [
                f'"{company}" job openings hiring 2024',
                f'"{company}" careers software engineer job posting',
                f'"{company}" hiring technology positions',
                f'site:linkedin.com "{company}" job openings'
            ]
            
            job_results = []
            for query in job_queries:
                try:
                    results = await self.tavily_client.search(
                        query=query,
                        search_depth="basic",
                        max_results=5,
                        include_domains=["linkedin.com", "glassdoor.com", "indeed.com", "lever.co", "greenhouse.io"]
                    )
                    
                    if results and results.get("results"):
                        job_results.extend(results["results"])
                        
                except Exception as e:
                    self.logger.warning(f"Job search failed for query '{query}': {e}")
                    continue
            
            if not job_results:
                return None
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"✅ Found {len(job_results)} job posting references for {company}",
                result={
                    "step": "Job Analysis",
                    "postings_found": len(job_results)
                }
            )
            
            return {
                "source": "job_postings",
                "results": job_results,
                "reliability": self.source_reliability["job_posting"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing job postings: {e}")
            return None

    async def _gather_financial_data(self, company: str, websocket_manager=None, job_id=None) -> Optional[Dict[str, Any]]:
        """Gather financial and partnership data."""
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"💰 Gathering financial and partnership data for {company}",
                result={"step": "Financial Analysis", "company": company}
            )
            
            # Search for financial and partnership information
            financial_queries = [
                f'"{company}" funding round investment 2024',
                f'"{company}" revenue growth financial results',
                f'"{company}" partnership agreement deal',
                f'"{company}" acquisition merger business'
            ]
            
            financial_results = []
            for query in financial_queries:
                try:
                    results = await self.tavily_client.search(
                        query=query,
                        search_depth="advanced",
                        max_results=4,
                        topic="finance"
                    )
                    
                    if results and results.get("results"):
                        financial_results.extend(results["results"])
                        
                except Exception as e:
                    self.logger.warning(f"Financial search failed for query '{query}': {e}")
                    continue
            
            if not financial_results:
                return None
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"✅ Found {len(financial_results)} financial data points for {company}",
                result={
                    "step": "Financial Analysis",
                    "data_points": len(financial_results)
                }
            )
            
            return {
                "source": "financial_data",
                "results": financial_results,
                "reliability": self.source_reliability["press_release"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error gathering financial data: {e}")
            return None

    async def _analyze_products_customers(self, company: str, websocket_manager=None, job_id=None) -> Optional[Dict[str, Any]]:
        """Analyze products and customer information."""
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🛍️ Analyzing products and customers for {company}",
                result={"step": "Product Analysis", "company": company}
            )
            
            # Search for product and customer information
            product_queries = [
                f'"{company}" products features specifications',
                f'"{company}" customer case study success story',
                f'"{company}" API documentation technical specs',
                f'"{company}" technology stack architecture'
            ]
            
            product_results = []
            for query in product_queries:
                try:
                    results = await self.tavily_client.search(
                        query=query,
                        search_depth="basic",
                        max_results=4
                    )
                    
                    if results and results.get("results"):
                        product_results.extend(results["results"])
                        
                except Exception as e:
                    self.logger.warning(f"Product search failed for query '{query}': {e}")
                    continue
            
            if not product_results:
                return None
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"✅ Found {len(product_results)} product/customer data points for {company}",
                result={
                    "step": "Product Analysis",
                    "data_points": len(product_results)
                }
            )
            
            return {
                "source": "product_customer_data",
                "results": product_results,
                "reliability": self.source_reliability["company_website"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing products and customers: {e}")
            return None

    async def _integrate_website_data(self, intelligence: Dict[str, Any], website_data: Dict[str, Any],
                                    websocket_manager=None, job_id=None) -> Dict[str, Any]:
        """Integrate website crawl data into company intelligence."""
        try:
            # Use OpenAI to extract structured data from website crawl
            structured_data = await self._extract_structured_data(
                website_data["results"], "website", websocket_manager, job_id
            )
            
            # Merge structured data into intelligence
            if structured_data:
                intelligence = self._merge_intelligence_data(intelligence, structured_data)
            
            # Add to data sources
            intelligence["data_sources"].append({
                "source": website_data["source"],
                "url": website_data["url"],
                "reliability": website_data["reliability"],
                "timestamp": website_data["timestamp"],
                "pages_crawled": len(website_data["results"])
            })
            
            return intelligence
            
        except Exception as e:
            self.logger.error(f"Error integrating website data: {e}")
            return intelligence

    async def _integrate_sec_data(self, intelligence: Dict[str, Any], sec_data: Dict[str, Any],
                                websocket_manager=None, job_id=None) -> Dict[str, Any]:
        """Integrate SEC filing data into company intelligence."""
        try:
            # Use OpenAI to extract structured data from SEC filings
            structured_data = await self._extract_structured_data(
                sec_data["results"], "sec_filing", websocket_manager, job_id
            )
            
            # Merge structured data into intelligence
            if structured_data:
                intelligence = self._merge_intelligence_data(intelligence, structured_data)
            
            # Add to data sources
            intelligence["data_sources"].append({
                "source": sec_data["source"],
                "reliability": sec_data["reliability"],
                "timestamp": sec_data["timestamp"],
                "filings_found": len(sec_data["results"])
            })
            
            return intelligence
            
        except Exception as e:
            self.logger.error(f"Error integrating SEC data: {e}")
            return intelligence

    async def _integrate_job_data(self, intelligence: Dict[str, Any], job_data: Dict[str, Any],
                                websocket_manager=None, job_id=None) -> Dict[str, Any]:
        """Integrate job posting data into company intelligence."""
        try:
            # Use OpenAI to extract structured data from job postings
            structured_data = await self._extract_structured_data(
                job_data["results"], "job_posting", websocket_manager, job_id
            )
            
            # Merge structured data into intelligence
            if structured_data:
                intelligence = self._merge_intelligence_data(intelligence, structured_data)
            
            # Add to data sources
            intelligence["data_sources"].append({
                "source": job_data["source"],
                "reliability": job_data["reliability"],
                "timestamp": job_data["timestamp"],
                "postings_analyzed": len(job_data["results"])
            })
            
            return intelligence
            
        except Exception as e:
            self.logger.error(f"Error integrating job data: {e}")
            return intelligence

    async def _integrate_financial_data(self, intelligence: Dict[str, Any], financial_data: Dict[str, Any],
                                      websocket_manager=None, job_id=None) -> Dict[str, Any]:
        """Integrate financial data into company intelligence."""
        try:
            # Use OpenAI to extract structured data from financial sources
            structured_data = await self._extract_structured_data(
                financial_data["results"], "financial", websocket_manager, job_id
            )
            
            # Merge structured data into intelligence
            if structured_data:
                intelligence = self._merge_intelligence_data(intelligence, structured_data)
            
            # Add to data sources
            intelligence["data_sources"].append({
                "source": financial_data["source"],
                "reliability": financial_data["reliability"],
                "timestamp": financial_data["timestamp"],
                "data_points": len(financial_data["results"])
            })
            
            return intelligence
            
        except Exception as e:
            self.logger.error(f"Error integrating financial data: {e}")
            return intelligence

    async def _integrate_product_data(self, intelligence: Dict[str, Any], product_data: Dict[str, Any],
                                    websocket_manager=None, job_id=None) -> Dict[str, Any]:
        """Integrate product and customer data into company intelligence."""
        try:
            # Use OpenAI to extract structured data from product sources
            structured_data = await self._extract_structured_data(
                product_data["results"], "product_customer", websocket_manager, job_id
            )
            
            # Merge structured data into intelligence
            if structured_data:
                intelligence = self._merge_intelligence_data(intelligence, structured_data)
            
            # Add to data sources
            intelligence["data_sources"].append({
                "source": product_data["source"],
                "reliability": product_data["reliability"],
                "timestamp": product_data["timestamp"],
                "data_points": len(product_data["results"])
            })
            
            return intelligence
            
        except Exception as e:
            self.logger.error(f"Error integrating product data: {e}")
            return intelligence

    async def _extract_structured_data(self, results: List[Dict[str, Any]], source_type: str,
                                     websocket_manager=None, job_id=None) -> Optional[Dict[str, Any]]:
        """Use OpenAI to extract structured data from search results."""
        try:
            # Combine all content from results
            combined_content = "\n\n".join([
                f"Title: {result.get('title', '')}\nContent: {result.get('content', '')}\nURL: {result.get('url', '')}"
                for result in results[:10]  # Limit to first 10 results
            ])
            
            if not combined_content.strip():
                return None
            
            # Create extraction prompt based on source type
            extraction_prompts = {
                "website": """Extract the following factual information from the company website content:
                1. Main products and services (specific names and features)
                2. Technology stack and platforms used
                3. Target industries and customer segments
                4. Key customers (specific company names mentioned)
                5. Business model and revenue model
                6. Team size and organizational structure
                7. Geographic presence and office locations
                
                Return as JSON with these exact keys: main_products, technology_stack, target_industries, key_customers, business_model, revenue_model, team_size, geographic_presence""",
                
                "sec_filing": """Extract the following financial information from SEC filing content:
                1. Recent funding rounds and amounts
                2. Revenue figures and growth metrics
                3. Key partnerships and strategic alliances
                4. Major business risks and opportunities
                5. Executive team and key personnel
                
                Return as JSON with these exact keys: recent_funding, growth_indicators, partnerships, business_risks, key_executives""",
                
                "job_posting": """Extract the following organizational insights from job posting content:
                1. Hiring trends and growth areas
                2. Technology investments and stack expansion
                3. Market expansion plans
                4. Product roadmap hints
                5. Team size indicators
                
                Return as JSON with these exact keys: hiring_trends, technology_investments, market_expansion, product_roadmap, team_size_indicators""",
                
                "financial": """Extract the following financial information:
                1. Recent funding and investment details
                2. Growth indicators and metrics
                3. Partnership announcements
                4. Acquisition or merger activity
                
                Return as JSON with these exact keys: recent_funding, growth_indicators, partnerships, acquisition_activity""",
                
                "product_customer": """Extract the following product and customer information:
                1. Product specifications and features
                2. Customer case studies and success stories
                3. Technology architecture details
                4. Integration capabilities
                
                Return as JSON with these exact keys: product_specifications, customer_case_studies, technology_architecture, integration_capabilities"""
            }
            
            prompt = extraction_prompts.get(source_type, extraction_prompts["website"])
            
            # Use OpenAI to extract structured data
            response = await self.openai_client.ainvoke([
                {"role": "system", "content": f"""You are a business intelligence analyst extracting factual data from company information. 
                Focus on specific, verifiable facts and avoid marketing language. Extract only concrete information that can be verified.
                Always return valid JSON format with the requested keys, even if some values are empty arrays or strings."""},
                {"role": "user", "content": f"{prompt}\n\nContent to analyze:\n{combined_content[:8000]}"}  # Limit content length
            ])
            
            # Parse JSON response
            try:
                extracted_data = json.loads(response.content)
                return extracted_data
            except json.JSONDecodeError:
                # Try to extract JSON from response if it's wrapped in text
                content = response.content
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                    return json.loads(json_content)
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting structured data: {e}")
            return None

    def _merge_intelligence_data(self, intelligence: Dict[str, Any], structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge structured data into the intelligence structure."""
        try:
            # Map extracted data to intelligence structure
            field_mapping = {
                # Company overview fields
                "main_products": ("company_overview", "main_products"),
                "technology_stack": ("company_overview", "technology_stack"),
                "target_industries": ("company_overview", "target_industries"),
                "key_customers": ("company_overview", "key_customers"),
                "business_model": ("company_overview", "business_model"),
                "revenue_model": ("company_overview", "revenue_model"),
                
                # Strategic focus fields
                "hiring_trends": ("strategic_focus", "current_priorities"),
                "technology_investments": ("strategic_focus", "technology_investments"),
                "market_expansion": ("strategic_focus", "market_expansion"),
                "product_roadmap": ("strategic_focus", "product_roadmap"),
                
                # Financial status fields
                "recent_funding": ("financial_status", "recent_funding"),
                "growth_indicators": ("financial_status", "growth_indicators"),
                "partnerships": ("financial_status", "partnerships"),
                
                # Organizational insights fields
                "team_size": ("organizational_insights", "team_size"),
                "team_size_indicators": ("organizational_insights", "team_size"),
                "key_executives": ("organizational_insights", "key_executives"),
                "geographic_presence": ("organizational_insights", "geographic_presence")
            }
            
            for data_key, value in structured_data.items():
                if data_key in field_mapping and value:
                    section, field = field_mapping[data_key]
                    
                    if isinstance(value, list):
                        # Extend existing list with new items
                        current_list = intelligence[section].get(field, [])
                        if isinstance(current_list, list):
                            intelligence[section][field] = list(set(current_list + value))  # Remove duplicates
                        else:
                            intelligence[section][field] = value
                    else:
                        # Update string fields
                        if not intelligence[section].get(field):
                            intelligence[section][field] = value
            
            return intelligence
            
        except Exception as e:
            self.logger.error(f"Error merging intelligence data: {e}")
            return intelligence

    def _calculate_reliability_score(self, data_sources: List[Dict[str, Any]]) -> float:
        """Calculate overall reliability score based on data sources."""
        if not data_sources:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for source in data_sources:
            reliability = source.get("reliability", 0.5)
            weight = 1.0  # Equal weight for now, could be enhanced with source quality metrics
            
            total_score += reliability * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0 