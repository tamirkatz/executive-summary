import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from tavily import AsyncTavilyClient

from ..classes import ResearchState
from ..agents.base_agent import BaseAgent
from ..config import config

logger = logging.getLogger(__name__)

class CompetitorsResearchAgent(BaseAgent):
    """
    Enhanced Competitors Research Agent that provides deep competitive intelligence
    using advanced Tavily crawl, real-time monitoring, and multi-source discovery.
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        super().__init__(agent_type="competitors_research_agent")
        
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
        
        # Enhanced Tavily crawl parameters for competitor intelligence
        self.competitor_crawl_params = {
            "max_depth": 4,
            "max_breadth": 30,
            "limit": 80,
            "instructions": """Extract COMPETITIVE INTELLIGENCE: product features and pricing, technology 
            capabilities, customer segments, recent funding or partnerships, hiring patterns, strategic 
            initiatives, product roadmap hints, market positioning, and competitive advantages. Focus on 
            factual, actionable intelligence that reveals strategic direction and capabilities.""",
            "categories": ["About", "Products", "Pricing", "Customers", "Investors", "News", "Careers", "Technology"],
            "exclude_paths": ["/blog/*", "/marketing/*", "/events/*", "/media/*"],
            "extract_depth": "advanced"
        }
        
        # Competitor discovery sources
        self.discovery_sources = [
            "crunchbase.com",
            "pitchbook.com", 
            "cbinsights.com",
            "owler.com",
            "similarweb.com",
            "g2.com",
            "capterra.com"
        ]

    async def run(self, state: ResearchState) -> Dict[str, Any]:
        """Main execution method for the Competitors Research Agent."""
        self.log_agent_start(state)
        company = state.get('company', 'Unknown Company')
        websocket_manager, job_id = self.get_websocket_info(state)
        
        # Get industry information - try multiple sources
        profile = state.get('profile', {})
        industry = profile.get('industry', 'Technology')
        
        # Try to get industry from company data if available
        company_data = state.get('company_factual_data', {})
        if company_data and company_data.get('customer_segments', {}).get('target_industries'):
            industry = company_data['customer_segments']['target_industries'][0]
        
        # Start with empty known competitors - we'll discover them using AI
        known_competitors = []
        
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🥊 Starting enhanced competitor research for {company}",
                result={
                    "step": "Competitors Research Agent",
                    "company": company,
                    "ai_discovery_mode": True,
                    "phase": "initialization"
                }
            )
            
            # Initialize competitive intelligence structure
            competitive_intelligence = {
                "comprehensive_profiles": {},
                "technology_comparisons": {
                    "technology_stacks": {},
                    "product_capabilities": {},
                    "integration_ecosystems": {}
                },
                "strategic_movements": {
                    "recent_funding": {},
                    "executive_changes": {},
                    "strategic_partnerships": {},
                    "product_launches": {}
                },
                "partnership_networks": {
                    "technology_partners": {},
                    "channel_partners": {},
                    "integration_partnerships": {}
                },
                "real_time_updates": {
                    "news_mentions": {},
                    "hiring_patterns": {},
                    "pricing_changes": {},
                    "market_movements": {}
                },
                "discovered_competitors": [],
                "data_sources": [],
                "last_updated": datetime.now().isoformat(),
                "target_company": company,
                "industry": industry
            }
            
            # Phase 1: Enhanced Competitor Discovery
            all_competitors = await self._discover_all_competitors(
                company, industry, known_competitors, websocket_manager, job_id
            )
            competitive_intelligence["discovered_competitors"] = all_competitors
            
            # Phase 2: Comprehensive Competitor Profiling
            if all_competitors:
                profiles = await self._profile_competitors_comprehensive(
                    all_competitors, websocket_manager, job_id
                )
                if profiles:
                    competitive_intelligence["comprehensive_profiles"] = profiles
            
            # Phase 3: Technology Stack Analysis
            tech_analysis = await self._analyze_competitor_technology(
                all_competitors, websocket_manager, job_id
            )
            if tech_analysis:
                competitive_intelligence["technology_comparisons"] = tech_analysis
            
            # Phase 4: Strategic Movement Tracking
            strategic_data = await self._track_strategic_movements(
                all_competitors, websocket_manager, job_id
            )
            if strategic_data:
                competitive_intelligence["strategic_movements"] = strategic_data
            
            # Phase 5: Partnership Ecosystem Mapping
            partnership_data = await self._map_partnership_networks(
                all_competitors, websocket_manager, job_id
            )
            if partnership_data:
                competitive_intelligence["partnership_networks"] = partnership_data
            
            # Phase 6: Real-Time Intelligence Gathering
            realtime_data = await self._gather_realtime_intelligence(
                all_competitors, websocket_manager, job_id
            )
            if realtime_data:
                competitive_intelligence["real_time_updates"] = realtime_data
            
            # Update state with comprehensive competitor data
            state['enhanced_competitor_data'] = {
                "comprehensive_profiles": competitive_intelligence.get("comprehensive_profiles", {}),
                "technology_comparisons": competitive_intelligence.get("technology_comparisons", {}),
                "strategic_movements": competitive_intelligence.get("strategic_movements", {}),
                "partnership_networks": competitive_intelligence.get("partnership_networks", {}),
                "real_time_updates": competitive_intelligence.get("real_time_updates", {}),
                "discovered_competitors": competitive_intelligence.get("discovered_competitors", []),
                "intelligence_summary": competitive_intelligence,
                "total_competitors": len(all_competitors)
            }
            
            # Add completion message
            completion_msg = f"✅ Enhanced competitor research complete. Analyzed {len(all_competitors)} competitors with {len(competitive_intelligence['data_sources'])} intelligence sources."
            
            messages = state.get('messages', [])
            messages.append(AIMessage(content=completion_msg))
            state['messages'] = messages
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="completed",
                message=completion_msg,
                result={
                    "step": "Competitors Research Agent",
                    "company": company,
                    "total_competitors": len(all_competitors),
                    "ai_discovered_competitors": len(all_competitors),
                    "sources_count": len(competitive_intelligence['data_sources']),
                    "key_findings": {
                        "profiles": len(competitive_intelligence["comprehensive_profiles"]),
                        "tech_comparisons": len(competitive_intelligence["technology_comparisons"].get("technology_stacks", {})),
                        "strategic_moves": len(competitive_intelligence["strategic_movements"].get("recent_funding", {})),
                        "partnerships": len(competitive_intelligence["partnership_networks"].get("technology_partners", {}))
                    }
                }
            )
            
            self.log_agent_complete(state)
            return state
            
        except Exception as e:
            error_msg = f"Error in Competitors Research Agent: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            await self.send_error_update(
                websocket_manager, job_id, error_msg, "Competitors Research Agent"
            )
            # Return state with empty data but don't fail
            state['enhanced_competitor_data'] = {
                "comprehensive_profiles": {},
                "technology_comparisons": {},
                "strategic_movements": {},
                "partnership_networks": {},
                "real_time_updates": {},
                "discovered_competitors": [],
                "error": error_msg
            }
            return state

    async def _discover_all_competitors(self, company: str, industry: str, known_competitors: List[str],
                                      websocket_manager=None, job_id=None) -> List[str]:
        """Enhanced competitor discovery using multiple sources."""
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🔍 Discovering all competitors for {company}",
                result={"step": "Competitor Discovery", "discovery_mode": "AI-powered"}
            )
            
            all_competitors = set()
            
            # Primary Method: AI-powered competitor identification (most reliable)
            ai_competitors = await self._ai_competitor_discovery(company, industry)
            if ai_competitors:
                all_competitors.update(ai_competitors)
                await self.send_status_update(
                    websocket_manager, job_id,
                    status="processing",
                    message=f"🤖 AI discovered {len(ai_competitors)} competitors",
                    result={"discovered": len(ai_competitors)}
                )
            
            # Supplementary Method: Search-based discovery (if we need more)
            if len(all_competitors) < 8:
                search_competitors = await self._search_based_discovery(company, industry)
                if search_competitors:
                    new_competitors = set(search_competitors) - all_competitors
                    all_competitors.update(new_competitors)
                    if new_competitors:
                        await self.send_status_update(
                            websocket_manager, job_id,
                            status="processing",
                            message=f"🔍 Search discovered {len(new_competitors)} additional competitors"
                        )
            
            # Clean and validate competitor list
            final_competitors = []
            for competitor in all_competitors:
                if competitor and competitor.lower() != company.lower():
                    cleaned = self._clean_competitor_name(competitor)
                    if self._validate_competitor_name(cleaned, company):
                        final_competitors.append(cleaned)
            
            # Remove duplicates and limit to top 20
            final_competitors = list(set(final_competitors))[:20]
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"✅ Discovered {len(final_competitors)} total competitors",
                result={
                    "step": "Competitor Discovery",
                    "total_found": len(final_competitors),
                    "ai_discovered": len(final_competitors)
                }
            )
            
            return final_competitors
            
        except Exception as e:
            self.logger.error(f"Error in competitor discovery: {e}")
            return known_competitors

    async def _ai_competitor_discovery(self, company: str, industry: str) -> List[str]:
        """Use OpenAI to discover comprehensive competitor list - primary discovery method."""
        try:
            prompt = f"""Who are the main competitors of {company}?

Please provide a comprehensive list of companies that compete with {company} in the {industry} space.

Include companies that:
1. Offer similar products or services
2. Target the same customer segments
3. Would be compared by potential customers when making purchasing decisions
4. Compete for market share in the same industry

Requirements:
- List only real company names (no descriptions)
- One company name per line
- Do NOT include {company} itself
- Focus on well-known, established competitors
- Include both direct and indirect competitors
- Maximum 12 competitors
- Prioritize companies that customers would actually evaluate as alternatives

Main competitors:"""
            
            response = await self.openai_client.ainvoke([
                {"role": "system", "content": "You are a market research expert who knows competitive landscapes across industries. Provide accurate, real company names only."},
                {"role": "user", "content": prompt}
            ])
            
            if response and response.content:
                # Split by lines and clean up
                competitors = []
                for line in response.content.strip().split('\n'):
                    line = line.strip()
                    # Remove numbering, bullets, and other formatting
                    line = line.lstrip('123456789.- ')
                    if line and line.lower() != company.lower():
                        cleaned = self._clean_competitor_name(line)
                        if cleaned and self._validate_competitor_name(cleaned, company):
                            competitors.append(cleaned)
                
                return competitors[:12]  # Limit to top 12
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error in AI competitor discovery: {e}")
            return []

    async def _search_based_discovery(self, company: str, industry: str) -> List[str]:
        """Discover competitors through search queries."""
        try:
            discovery_queries = [
                f'"{company}" competitors alternative solutions',
                f'"{company}" vs comparison competitive analysis',
                f'{industry} companies similar to "{company}"',
                f'"{company}" competitive landscape market share',
                f'top {industry} companies alternatives to "{company}"'
            ]
            
            discovered_competitors = set()
            
            for query in discovery_queries:
                try:
                    results = await self.tavily_client.search(
                        query=query,
                        search_depth="basic",
                        max_results=5,
                        include_domains=self.discovery_sources
                    )
                    
                    if results and results.get("results"):
                        # Extract competitor names from search results
                        competitors = await self._extract_competitors_from_results(
                            results["results"], company
                        )
                        discovered_competitors.update(competitors)
                        
                except Exception as e:
                    self.logger.warning(f"Search discovery failed for query '{query}': {e}")
                    continue
            
            return list(discovered_competitors)
            
        except Exception as e:
            self.logger.error(f"Error in search-based discovery: {e}")
            return []

    async def _database_discovery(self, company: str, industry: str) -> List[str]:
        """Discover competitors from industry databases."""
        try:
            database_queries = [
                f'site:crunchbase.com "{company}" competitors {industry}',
                f'site:owler.com "{company}" competitive landscape',
                f'site:g2.com "{company}" alternatives competitors',
                f'site:capterra.com "{company}" competitors software'
            ]
            
            discovered_competitors = set()
            
            for query in database_queries:
                try:
                    results = await self.tavily_client.search(
                        query=query,
                        search_depth="basic",
                        max_results=3
                    )
                    
                    if results and results.get("results"):
                        competitors = await self._extract_competitors_from_results(
                            results["results"], company
                        )
                        discovered_competitors.update(competitors)
                        
                except Exception as e:
                    self.logger.warning(f"Database discovery failed for query '{query}': {e}")
                    continue
            
            return list(discovered_competitors)
            
        except Exception as e:
            self.logger.error(f"Error in database discovery: {e}")
            return []

    async def _extract_competitors_from_results(self, results: List[Dict[str, Any]], company: str) -> List[str]:
        """Extract competitor names from search results using AI."""
        try:
            # Combine content from results
            combined_content = "\n\n".join([
                f"Title: {result.get('title', '')}\nContent: {result.get('content', '')}"
                for result in results[:5]
            ])
            
            if not combined_content.strip():
                return []
            
            prompt = f"""Extract competitor company names mentioned in the following content about {company}.

RULES:
- Return ONLY company names (no descriptions)
- One name per line
- Do NOT include {company} itself
- Focus on actual companies, not generic terms
- Maximum 10 companies
- Include only companies that appear to be direct competitors

Content:
{combined_content[:4000]}

Competitor names:"""
            
            response = await self.openai_client.ainvoke([
                {"role": "system", "content": "You are extracting competitor company names from business content."},
                {"role": "user", "content": prompt}
            ])
            
            if response and response.content:
                competitors = [line.strip() for line in response.content.split("\n") if line.strip()]
                return [self._clean_competitor_name(c) for c in competitors if c]
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error extracting competitors from results: {e}")
            return []

    async def _profile_competitors_comprehensive(self, competitors: List[str],
                                               websocket_manager=None, job_id=None) -> Dict[str, Any]:
        """Create comprehensive profiles for each competitor."""
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"📋 Profiling {len(competitors)} competitors comprehensively",
                result={"step": "Competitor Profiling", "competitors_count": len(competitors)}
            )
            
            profiles = {}
            
            # Process competitors in batches to avoid rate limits
            batch_size = 5
            for i in range(0, len(competitors), batch_size):
                batch = competitors[i:i+batch_size]
                
                # Process batch concurrently
                batch_tasks = [
                    self._profile_single_competitor(competitor, websocket_manager, job_id)
                    for competitor in batch
                ]
                
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for competitor, result in zip(batch, batch_results):
                    if not isinstance(result, Exception) and result:
                        profiles[competitor] = result
                
                # Brief pause between batches
                if i + batch_size < len(competitors):
                    await asyncio.sleep(1)
            
            return profiles
            
        except Exception as e:
            self.logger.error(f"Error profiling competitors: {e}")
            return {}

    async def _profile_single_competitor(self, competitor: str, websocket_manager=None, job_id=None) -> Optional[Dict[str, Any]]:
        """Create detailed profile for a single competitor."""
        try:
            # Search for competitor information
            competitor_queries = [
                f'"{competitor}" company overview products services',
                f'"{competitor}" funding revenue business model',
                f'"{competitor}" customers technology stack',
                f'"{competitor}" recent news announcements'
            ]
            
            competitor_data = []
            for query in competitor_queries:
                try:
                    results = await self.tavily_client.search(
                        query=query,
                        search_depth="basic",
                        max_results=3
                    )
                    
                    if results and results.get("results"):
                        competitor_data.extend(results["results"])
                        
                except Exception as e:
                    self.logger.warning(f"Competitor search failed for '{competitor}': {e}")
                    continue
            
            if not competitor_data:
                return None
            
            # Extract structured profile using AI
            profile = await self._extract_competitor_profile(competitor, competitor_data)
            return profile
            
        except Exception as e:
            self.logger.error(f"Error profiling competitor {competitor}: {e}")
            return None

    async def _extract_competitor_profile(self, competitor: str, data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract structured competitor profile using AI."""
        try:
            # Combine data content
            combined_content = "\n\n".join([
                f"Title: {item.get('title', '')}\nContent: {item.get('content', '')}\nURL: {item.get('url', '')}"
                for item in data[:8]
            ])
            
            if not combined_content.strip():
                return None
            
            prompt = f"""Extract a structured profile for {competitor} from the following information:

{combined_content[:6000]}

Return as JSON with these exact keys:
- company_overview: Brief description of what the company does
- main_products: List of main products/services
- target_market: Description of target customers/market
- business_model: How they make money
- recent_funding: Any recent funding information
- technology_focus: Key technologies they use/focus on
- competitive_position: How they position themselves in market
- recent_developments: Any recent news or developments

Focus on factual information only."""
            
            response = await self.openai_client.ainvoke([
                {"role": "system", "content": "You are a business analyst extracting structured competitor profiles from information."},
                {"role": "user", "content": prompt}
            ])
            
            # Parse JSON response
            try:
                profile_data = json.loads(response.content)
                profile_data["last_updated"] = datetime.now().isoformat()
                profile_data["data_sources"] = len(data)
                return profile_data
            except json.JSONDecodeError:
                # Try to extract JSON from response
                content = response.content
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                    profile_data = json.loads(json_content)
                    profile_data["last_updated"] = datetime.now().isoformat()
                    profile_data["data_sources"] = len(data)
                    return profile_data
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting competitor profile for {competitor}: {e}")
            return None

    async def _analyze_competitor_technology(self, competitors: List[str],
                                           websocket_manager=None, job_id=None) -> Dict[str, Any]:
        """Analyze competitor technology stacks and capabilities."""
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🔧 Analyzing technology stacks for {len(competitors)} competitors",
                result={"step": "Technology Analysis", "competitors_count": len(competitors)}
            )
            
            tech_analysis = {
                "technology_stacks": {},
                "product_capabilities": {},
                "integration_ecosystems": {}
            }
            
            # Analyze top competitors only for detailed tech analysis
            top_competitors = competitors[:8]
            
            for competitor in top_competitors:
                try:
                    tech_data = await self._analyze_single_competitor_tech(competitor)
                    if tech_data:
                        tech_analysis["technology_stacks"][competitor] = tech_data.get("technology_stack", [])
                        tech_analysis["product_capabilities"][competitor] = tech_data.get("capabilities", [])
                        tech_analysis["integration_ecosystems"][competitor] = tech_data.get("integrations", [])
                        
                except Exception as e:
                    self.logger.warning(f"Tech analysis failed for {competitor}: {e}")
                    continue
            
            return tech_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing competitor technology: {e}")
            return {}

    async def _analyze_single_competitor_tech(self, competitor: str) -> Optional[Dict[str, Any]]:
        """Analyze technology stack for a single competitor."""
        try:
            tech_queries = [
                f'"{competitor}" technology stack architecture API',
                f'"{competitor}" technical documentation developer',
                f'"{competitor}" integrations partnerships tech',
                f'"{competitor}" engineering blog technical details'
            ]
            
            tech_data = []
            for query in tech_queries:
                try:
                    results = await self.tavily_client.search(
                        query=query,
                        search_depth="basic",
                        max_results=3,
                        include_domains=["github.com", "docs.", "api.", "developer.", "engineering.", "tech."]
                    )
                    
                    if results and results.get("results"):
                        tech_data.extend(results["results"])
                        
                except Exception as e:
                    continue
            
            if not tech_data:
                return None
            
            # Extract technology information using AI
            return await self._extract_technology_info(competitor, tech_data)
            
        except Exception as e:
            self.logger.error(f"Error analyzing tech for {competitor}: {e}")
            return None

    async def _extract_technology_info(self, competitor: str, data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract technology information using AI."""
        try:
            combined_content = "\n\n".join([
                f"Title: {item.get('title', '')}\nContent: {item.get('content', '')}"
                for item in data[:6]
            ])
            
            if not combined_content.strip():
                return None
            
            prompt = f"""Extract technology information for {competitor} from the following content:

{combined_content[:5000]}

Return as JSON with these exact keys:
- technology_stack: List of technologies, frameworks, and platforms they use
- capabilities: List of technical capabilities and features they offer
- integrations: List of third-party integrations and partnerships they support

Focus on specific technologies and capabilities mentioned."""
            
            response = await self.openai_client.ainvoke([
                {"role": "system", "content": "You are a technical analyst extracting technology information from company data."},
                {"role": "user", "content": prompt}
            ])
            
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                content = response.content
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                    return json.loads(json_content)
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting technology info for {competitor}: {e}")
            return None

    async def _track_strategic_movements(self, competitors: List[str],
                                       websocket_manager=None, job_id=None) -> Dict[str, Any]:
        """Track recent strategic movements of competitors."""
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"📈 Tracking strategic movements for {len(competitors)} competitors",
                result={"step": "Strategic Movement Tracking", "competitors_count": len(competitors)}
            )
            
            strategic_data = {
                "recent_funding": {},
                "executive_changes": {},
                "strategic_partnerships": {},
                "product_launches": {}
            }
            
            current_year = datetime.now().year
            
            # Track movements for top competitors
            top_competitors = competitors[:10]
            
            for competitor in top_competitors:
                try:
                    movements = await self._track_single_competitor_movements(competitor, current_year)
                    if movements:
                        strategic_data["recent_funding"][competitor] = movements.get("funding", [])
                        strategic_data["executive_changes"][competitor] = movements.get("executives", [])
                        strategic_data["strategic_partnerships"][competitor] = movements.get("partnerships", [])
                        strategic_data["product_launches"][competitor] = movements.get("products", [])
                        
                except Exception as e:
                    self.logger.warning(f"Strategic tracking failed for {competitor}: {e}")
                    continue
            
            return strategic_data
            
        except Exception as e:
            self.logger.error(f"Error tracking strategic movements: {e}")
            return {}

    async def _track_single_competitor_movements(self, competitor: str, year: int) -> Optional[Dict[str, Any]]:
        """Track strategic movements for a single competitor."""
        try:
            movement_queries = [
                f'"{competitor}" funding round investment {year}',
                f'"{competitor}" executive changes hire CEO CTO {year}',
                f'"{competitor}" partnership deal acquisition {year}',
                f'"{competitor}" product launch announcement {year}'
            ]
            
            movement_data = []
            for query in movement_queries:
                try:
                    results = await self.tavily_client.search(
                        query=query,
                        search_depth="basic",
                        max_results=3,
                        topic="news"
                    )
                    
                    if results and results.get("results"):
                        movement_data.extend(results["results"])
                        
                except Exception as e:
                    continue
            
            if not movement_data:
                return None
            
            # Extract strategic movements using AI
            return await self._extract_strategic_movements(competitor, movement_data)
            
        except Exception as e:
            self.logger.error(f"Error tracking movements for {competitor}: {e}")
            return None

    async def _extract_strategic_movements(self, competitor: str, data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract strategic movements using AI."""
        try:
            combined_content = "\n\n".join([
                f"Title: {item.get('title', '')}\nContent: {item.get('content', '')}"
                for item in data[:8]
            ])
            
            if not combined_content.strip():
                return None
            
            prompt = f"""Extract recent strategic movements for {competitor} from the following news content:

{combined_content[:5000]}

Return as JSON with these exact keys:
- funding: List of recent funding rounds or investments
- executives: List of executive changes or key hires
- partnerships: List of strategic partnerships or deals
- products: List of new product launches or announcements

Include dates and amounts when available."""
            
            response = await self.openai_client.ainvoke([
                {"role": "system", "content": "You are a business analyst extracting strategic business movements from news content."},
                {"role": "user", "content": prompt}
            ])
            
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                content = response.content
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                    return json.loads(json_content)
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting strategic movements for {competitor}: {e}")
            return None

    async def _map_partnership_networks(self, competitors: List[str],
                                      websocket_manager=None, job_id=None) -> Dict[str, Any]:
        """Map partnership networks of competitors."""
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🤝 Mapping partnership networks for {len(competitors)} competitors",
                result={"step": "Partnership Mapping", "competitors_count": len(competitors)}
            )
            
            partnership_data = {
                "technology_partners": {},
                "channel_partners": {},
                "integration_partnerships": {}
            }
            
            # Map partnerships for top competitors
            top_competitors = competitors[:8]
            
            for competitor in top_competitors:
                try:
                    partnerships = await self._map_single_competitor_partnerships(competitor)
                    if partnerships:
                        partnership_data["technology_partners"][competitor] = partnerships.get("technology", [])
                        partnership_data["channel_partners"][competitor] = partnerships.get("channel", [])
                        partnership_data["integration_partnerships"][competitor] = partnerships.get("integration", [])
                        
                except Exception as e:
                    self.logger.warning(f"Partnership mapping failed for {competitor}: {e}")
                    continue
            
            return partnership_data
            
        except Exception as e:
            self.logger.error(f"Error mapping partnership networks: {e}")
            return {}

    async def _map_single_competitor_partnerships(self, competitor: str) -> Optional[Dict[str, Any]]:
        """Map partnerships for a single competitor."""
        try:
            partnership_queries = [
                f'"{competitor}" partners technology integrations',
                f'"{competitor}" partner program ecosystem',
                f'"{competitor}" reseller channel partners',
                f'"{competitor}" integration marketplace'
            ]
            
            partnership_data = []
            for query in partnership_queries:
                try:
                    results = await self.tavily_client.search(
                        query=query,
                        search_depth="basic",
                        max_results=3
                    )
                    
                    if results and results.get("results"):
                        partnership_data.extend(results["results"])
                        
                except Exception as e:
                    continue
            
            if not partnership_data:
                return None
            
            # Extract partnership information using AI
            return await self._extract_partnership_info(competitor, partnership_data)
            
        except Exception as e:
            self.logger.error(f"Error mapping partnerships for {competitor}: {e}")
            return None

    async def _extract_partnership_info(self, competitor: str, data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract partnership information using AI."""
        try:
            combined_content = "\n\n".join([
                f"Title: {item.get('title', '')}\nContent: {item.get('content', '')}"
                for item in data[:6]
            ])
            
            if not combined_content.strip():
                return None
            
            prompt = f"""Extract partnership information for {competitor} from the following content:

{combined_content[:5000]}

Return as JSON with these exact keys:
- technology: List of technology partners and platforms they integrate with
- channel: List of channel partners, resellers, and distributors
- integration: List of specific integration partnerships and marketplace presence

Focus on specific company names and partnership types."""
            
            response = await self.openai_client.ainvoke([
                {"role": "system", "content": "You are a business analyst extracting partnership information from company data."},
                {"role": "user", "content": prompt}
            ])
            
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                content = response.content
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                    return json.loads(json_content)
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting partnership info for {competitor}: {e}")
            return None

    async def _gather_realtime_intelligence(self, competitors: List[str],
                                          websocket_manager=None, job_id=None) -> Dict[str, Any]:
        """Gather real-time intelligence on competitors."""
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"⚡ Gathering real-time intelligence for {len(competitors)} competitors",
                result={"step": "Real-time Intelligence", "competitors_count": len(competitors)}
            )
            
            realtime_data = {
                "news_mentions": {},
                "hiring_patterns": {},
                "pricing_changes": {},
                "market_movements": {}
            }
            
            # Gather real-time data for top competitors
            top_competitors = competitors[:6]
            
            for competitor in top_competitors:
                try:
                    realtime_info = await self._gather_single_competitor_realtime(competitor)
                    if realtime_info:
                        realtime_data["news_mentions"][competitor] = realtime_info.get("news", [])
                        realtime_data["hiring_patterns"][competitor] = realtime_info.get("hiring", [])
                        realtime_data["pricing_changes"][competitor] = realtime_info.get("pricing", [])
                        realtime_data["market_movements"][competitor] = realtime_info.get("market", [])
                        
                except Exception as e:
                    self.logger.warning(f"Real-time gathering failed for {competitor}: {e}")
                    continue
            
            return realtime_data
            
        except Exception as e:
            self.logger.error(f"Error gathering real-time intelligence: {e}")
            return {}

    async def _gather_single_competitor_realtime(self, competitor: str) -> Optional[Dict[str, Any]]:
        """Gather real-time intelligence for a single competitor."""
        try:
            current_date = datetime.now().strftime("%Y-%m")
            realtime_queries = [
                f'"{competitor}" news {current_date}',
                f'"{competitor}" hiring jobs {current_date}',
                f'"{competitor}" pricing changes {current_date}',
                f'"{competitor}" market performance {current_date}'
            ]
            
            realtime_data = []
            for query in realtime_queries:
                try:
                    results = await self.tavily_client.search(
                        query=query,
                        search_depth="basic",
                        max_results=3,
                        topic="news"
                    )
                    
                    if results and results.get("results"):
                        realtime_data.extend(results["results"])
                        
                except Exception as e:
                    continue
            
            if not realtime_data:
                return None
            
            # Extract real-time information using AI
            return await self._extract_realtime_info(competitor, realtime_data)
            
        except Exception as e:
            self.logger.error(f"Error gathering real-time info for {competitor}: {e}")
            return None

    async def _extract_realtime_info(self, competitor: str, data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract real-time information using AI."""
        try:
            combined_content = "\n\n".join([
                f"Title: {item.get('title', '')}\nContent: {item.get('content', '')}"
                for item in data[:8]
            ])
            
            if not combined_content.strip():
                return None
            
            prompt = f"""Extract recent real-time information for {competitor} from the following content:

{combined_content[:5000]}

Return as JSON with these exact keys:
- news: List of recent news mentions and developments
- hiring: List of recent hiring activities or job postings
- pricing: List of any pricing changes or announcements
- market: List of market movements or performance updates

Focus on the most recent information only."""
            
            response = await self.openai_client.ainvoke([
                {"role": "system", "content": "You are a business analyst extracting recent real-time business information."},
                {"role": "user", "content": prompt}
            ])
            
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                content = response.content
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                    return json.loads(json_content)
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting real-time info for {competitor}: {e}")
            return None

    def _clean_competitor_name(self, name: str) -> str:
        """Clean and normalize competitor names."""
        name = name.strip().replace('"', '').replace("'", "")
        
        # Remove common business suffixes for cleaner names
        suffixes_to_remove = [' Inc', ' Inc.', ' Corp', ' Corp.', ' LLC', ' Ltd', ' Ltd.', ' Co', ' Co.']
        for suffix in suffixes_to_remove:
            if name.endswith(suffix) and len(name.replace(suffix, '').strip()) > 2:
                name = name.replace(suffix, '').strip()
                break
        
        return name

    def _validate_competitor_name(self, name: str, company: str) -> bool:
        """Validate competitor names."""
        if not name or len(name) < 2:
            return False
        
        # Check if it's the same as the target company
        if name.lower() == company.lower():
            return False
        
        # Check for common invalid patterns
        invalid_patterns = [
            'and', 'or', 'the', 'inc', 'corp', 'llc', 'ltd', 'co',
            'company', 'companies', 'business', 'enterprise', 'startup',
            'similar', 'alternative', 'competitor', 'like', 'such as'
        ]
        
        if name.lower() in invalid_patterns:
            return False
        
        # Must contain letters (not just numbers/symbols)
        if not any(c.isalpha() for c in name):
            return False
        
        return True 