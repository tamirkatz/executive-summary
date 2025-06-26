import os
import logging
import asyncio
from typing import List, Dict, Any, Optional, Set, Tuple
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
    category: str = Field(description="Type of competitor: direct, indirect, or emerging")


class CompetitorAnalysis(BaseModel):
    """Structure for comprehensive competitor analysis"""
    direct_competitors: List[CompetitorInfo] = Field(description="Direct competitors offering similar products")
    indirect_competitors: List[CompetitorInfo] = Field(description="Indirect competitors solving similar problems")
    emerging_competitors: List[CompetitorInfo] = Field(description="Emerging competitors or new threats")
    analysis_summary: str = Field(description="Summary of the competitive landscape")


class EnhancedCompetitorDiscoveryAgent(BaseAgent):
    """
    Enhanced competitor discovery agent that leverages comprehensive profile data
    to generate targeted, accurate competitor searches.
    """
    
    def __init__(self):
        super().__init__(agent_type="enhanced_competitor_discovery_agent")
        
        # Use gpt-4o for the core competitor analysis and query generation (more reliable than o3)
        self.llm = ChatOpenAI(
            model="gpt-4o",
            api_key=config.OPENAI_API_KEY,
            temperature=0.3
        )
        
        # Use gpt-4o for extraction and validation too
        self.extraction_llm = ChatOpenAI(
            model="gpt-4o", 
            api_key=config.OPENAI_API_KEY,
            temperature=0.2
        )
        
        self.tavily = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    async def discover_competitors(self, enriched_profile: Dict[str, Any], websocket_manager=None, job_id=None) -> Dict[str, Any]:
        """Main competitor discovery method using enriched profile data"""
        
        company_name = enriched_profile.get('company', 'Unknown')
        
        await self.send_status_update(
            websocket_manager, job_id,
            status="processing",
            message=f"🧠 Analyzing competitive landscape for {company_name} using enriched profile data",
            result={"step": "Competitor Discovery", "substep": "profile_analysis"}
        )
        
        # Step 1: Generate targeted search queries from enriched profile
        search_queries = await self._generate_targeted_queries(enriched_profile)
        
        await self.send_status_update(
            websocket_manager, job_id,
            status="processing",
            message=f"🔍 Generated {len(search_queries)} targeted queries, searching for competitors",
            result={"step": "Competitor Discovery", "substep": "targeted_search"}
        )
        
        # Step 2: Execute targeted searches in parallel
        search_results = await self._execute_targeted_searches(search_queries, company_name)
        
        await self.send_status_update(
            websocket_manager, job_id,
            status="processing",
            message=f"📊 Analyzing {len(search_results)} search results to identify competitors",
            result={"step": "Competitor Discovery", "substep": "competitor_extraction"}
        )
        
        # Step 3: Extract and analyze competitors from search results
        competitors = await self._extract_competitors_from_results(
            search_results, enriched_profile, company_name
        )
        
        # **CRITICAL FIX: Add fallback searches if not enough competitors found**
        if len(competitors) < 5:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🔄 Found only {len(competitors)} initial competitors, executing fallback searches",
                result={"step": "Competitor Discovery", "substep": "fallback_search"}
            )
            
            fallback_competitors = await self._execute_fallback_searches(
                enriched_profile, company_name, existing_competitors=competitors
            )
            competitors.update(fallback_competitors)
        
        # Step 4: Validate and enrich competitor data
        validated_competitors = await self._validate_and_enrich_competitors(
            competitors, enriched_profile, company_name
        )
        
        # Step 5: Generate final competitive analysis
        final_analysis = await self._generate_competitive_analysis(
            validated_competitors, enriched_profile
        )
        
        await self.send_status_update(
            websocket_manager, job_id,
            status="competitor_discovery_complete",
            message=f"✅ Competitor analysis complete: {len(validated_competitors)} validated competitors across all categories",
            result={"competitors": validated_competitors, "analysis": final_analysis}
        )
        
        return {
            "competitors": validated_competitors,
            "competitive_analysis": final_analysis,
            "methodology": "enhanced_profile_driven_discovery",
            "search_queries_used": search_queries
        }

    async def _generate_targeted_queries(self, enriched_profile: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate intelligent, LLM-driven search queries based on deep profile analysis"""
        
        company_name = enriched_profile.get('company', '')
        
        # **DEBUG: Log the enriched profile data we're working with**
        self.logger.info(f"=== QUERY GENERATION DEBUG ===")
        self.logger.info(f"Company: {company_name}")
        self.logger.info(f"Sector: {enriched_profile.get('sector', 'NONE')}")
        self.logger.info(f"Industry: {enriched_profile.get('industry', 'NONE')}")
        self.logger.info(f"Description: {enriched_profile.get('description', 'NONE')[:200]}...")
        self.logger.info(f"Core products: {enriched_profile.get('core_products', [])}")
        self.logger.info(f"Use cases: {enriched_profile.get('use_cases', [])}")
        self.logger.info(f"Customer segments: {enriched_profile.get('customer_segments', [])}")
        self.logger.info(f"Profile keys: {list(enriched_profile.keys())}")
        
        # **REVOLUTIONARY APPROACH: Use LLM to intelligently design search strategy**
        query_generation_prompt = f"""You are an expert competitive intelligence researcher. Design a laser-focused search strategy to find REAL competitors to {company_name} in the {enriched_profile.get('sector', '')} space.

COMPANY PROFILE:
- Company: {company_name}
- Description: {enriched_profile.get('description', '')}
- Industry: {enriched_profile.get('industry', '')}
- Sector: {enriched_profile.get('sector', '')}
- Core Products: {enriched_profile.get('core_products', [])}
- Use Cases: {enriched_profile.get('use_cases', [])}
- Customer Segments: {enriched_profile.get('customer_segments', [])}
- Synonyms: {enriched_profile.get('synonyms', [])}

CRITICAL REQUIREMENTS:
1. Find STARTUPS and SCALE-UPS in the {enriched_profile.get('sector', '')} space, NOT big tech
2. Target companies that directly compete with {company_name}'s core offerings
3. Focus on comparison sites, startup directories, and tech blogs that list emerging competitors
4. Generate queries that return specialized players, not generic solutions

BANNED RESULTS (avoid these completely):
- Google, Microsoft, Amazon, Apple, Meta, Facebook, IBM, Oracle, Salesforce
- Generic search engines (unless AI-specific competitors)
- Infrastructure providers (AWS, Azure, GCP)
- Productivity tools (Slack, Teams, Zoom) unless direct competitors

QUERY STRATEGY FOR {enriched_profile.get('sector', '')}:
Generate 15-20 surgical queries targeting:
1. Direct product comparisons with known competitors
2. "Alternative to [known competitor]" searches
3. Startup directory searches (ProductHunt, Crunchbase)
4. Developer community discussions (Reddit, HackerNews)
5. Tech blog roundups and reviews
6. API/tool comparison sites

OUTPUT FORMAT (EXACTLY as shown):

query: "exact search string"
type: search_category
reasoning: specific explanation of competitive value

CRITICAL: Each query must be laser-focused on finding companies that directly compete with {company_name} in {enriched_profile.get('sector', '')}.

Generate 15-20 queries now:"""

        try:
            self.logger.info(f"Sending query generation prompt to LLM...")
            self.logger.debug(f"LLM model: {self.llm.model_name}")
            self.logger.debug(f"Prompt length: {len(query_generation_prompt)} characters")
            
            response = await self.llm.ainvoke(query_generation_prompt)
            
            self.logger.info(f"LLM response received, length: {len(response.content)} characters")
            self.logger.debug(f"Raw LLM response: {response.content[:500]}...")
            
            queries = []
            
            # Parse LLM response to extract queries
            lines = response.content.split('\n')
            current_query = {}
            
            self.logger.info(f"Parsing {len(lines)} lines from LLM response...")
            
            for line in lines:
                line = line.strip()
                if line.startswith('query:'):
                    # Save previous query if exists
                    if current_query.get('query'):
                        queries.append(current_query)
                    # Start new query
                    current_query = {"query": line.split(':', 1)[1].strip().strip('"')}
                elif line.startswith('type:') and current_query.get('query'):
                    current_query["type"] = line.split(':', 1)[1].strip().strip('"')
                elif line.startswith('reasoning:') and current_query.get('query'):
                    current_query["context"] = line.split(':', 1)[1].strip().strip('"')
                # Legacy format support
                elif line.startswith('- query:'):
                    if current_query.get('query'):
                        queries.append(current_query)
                    current_query = {"query": line.split(':', 1)[1].strip().strip('"')}
                elif line.startswith('- type:') and current_query.get('query'):
                    current_query["type"] = line.split(':', 1)[1].strip().strip('"')
                elif line.startswith('- reasoning:') and current_query.get('query'):
                    current_query["context"] = line.split(':', 1)[1].strip().strip('"')
            
            # Add the last query
            if current_query.get('query'):
                queries.append(current_query)
            
            self.logger.info(f"Extracted {len(queries)} raw queries from LLM response")
            for i, q in enumerate(queries):
                self.logger.debug(f"Query {i+1}: {q}")
            
            # Validate and clean queries
            validated_queries = []
            for q in queries:
                if (q.get('query') and len(q['query']) > 10 and 
                    company_name.lower() not in q['query'].lower()):
                    validated_queries.append({
                        "query": q['query'],
                        "type": q.get('type', 'llm_generated'),
                        "context": q.get('context', f"LLM-generated query for {company_name}")
                    })
                    self.logger.debug(f"Validated query: {q['query']}")
                else:
                    self.logger.debug(f"Rejected query: {q} (invalid or contains company name)")
            
            self.logger.info(f"After validation: {len(validated_queries)} queries")
            
            if len(validated_queries) < 10:
                self.logger.warning(f"Only {len(validated_queries)} validated queries, adding fallback queries...")
                # Fallback: Add some strategic manual queries
                sector = enriched_profile.get('sector', '')
                if sector:
                    fallback_queries = [
                        {
                            "query": f'"{sector}" alternatives comparison 2024',
                            "type": "sector_alternatives",
                            "context": f"Finding {sector} alternatives"
                        },
                        {
                            "query": f'best {sector} tools startups companies',
                            "type": "sector_startups", 
                            "context": f"Finding startups in {sector}"
                        }
                    ]
                    validated_queries.extend(fallback_queries)
                    self.logger.info(f"Added {len(fallback_queries)} fallback queries")
            
            self.logger.info(f"Final query count: {len(validated_queries)} intelligent queries for {company_name}")
            return validated_queries[:20]
            
        except Exception as e:
            self.logger.error(f"LLM query generation failed: {e}")
            self.logger.error(f"Exception type: {type(e).__name__}")
            self.logger.error(f"Exception details: {str(e)}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Fallback to basic queries if LLM fails
            self.logger.warning("Falling back to basic query generation...")
            return await self._generate_fallback_queries(enriched_profile)

    async def _generate_fallback_queries(self, enriched_profile: Dict[str, Any]) -> List[Dict[str, str]]:
        """Fallback query generation if LLM approach fails"""
        
        sector = enriched_profile.get('sector', '')
        industry = enriched_profile.get('industry', '')
        
        self.logger.warning(f"=== FALLBACK QUERY GENERATION ===")
        self.logger.warning(f"Sector: {sector}")
        self.logger.warning(f"Industry: {industry}")
        
        basic_queries = []
        if sector:
            basic_queries = [
                {
                    "query": f'"{sector}" competitors alternatives',
                    "type": "basic_alternatives",
                    "context": f"Basic search for {sector} alternatives"
                },
                {
                    "query": f'{sector} vs comparison tools',
                    "type": "basic_comparison",
                    "context": f"Basic comparison search for {sector}"
                }
            ]
            self.logger.warning(f"Generated {len(basic_queries)} basic fallback queries")
        else:
            self.logger.error("No sector available for fallback query generation!")
        
        for i, q in enumerate(basic_queries):
            self.logger.warning(f"Fallback query {i+1}: {q['query']}")
        
        return basic_queries

    def _get_sector_seeds(self, sector: str, industry: str) -> List[str]:
        """Get known competitors/platforms for specific sectors to use as search seeds"""
        
        sector_lower = sector.lower() if sector else ""
        industry_lower = industry.lower() if industry else ""
        
        # **CRITICAL: Comprehensive seed competitors by sector**
        sector_seeds = {
            # No-code/Low-code platforms
            "no-code": ["Bubble", "Webflow", "Zapier", "Airtable", "Notion", "Retool"],
            "low-code": ["OutSystems", "Mendix", "PowerApps", "Bubble", "Retool", "AppGyver"],
            "development platform": ["Bubble", "Webflow", "Retool", "Glide", "AppSheet", "Adalo"],
            "website builder": ["Webflow", "Wix", "Squarespace", "Framer", "Editor X", "Tilda"],
            "app builder": ["Bubble", "Glide", "Adalo", "Thunkable", "AppGyver", "FlutterFlow"],
            
            # AI/Modern development
            "ai development": ["Cursor", "GitHub Copilot", "Replit", "Lovable", "Bolt", "v0"],
            "ai platform": ["Lovable", "Bolt", "v0", "Cursor", "Replit", "Claude Artifacts"],
            
            # Business automation
            "automation": ["Zapier", "Make", "Power Automate", "n8n", "Integromat", "Pabbly"],
            "workflow": ["Monday.com", "Asana", "ClickUp", "Notion", "Airtable", "Smartsheet"],
            
            # Database and backend
            "database": ["Airtable", "Notion", "Supabase", "Firebase", "MongoDB", "PlanetScale"],
            "backend": ["Supabase", "Firebase", "AWS Amplify", "Retool", "Xano", "Backendless"],
            
            # E-commerce
            "ecommerce": ["Shopify", "WooCommerce", "BigCommerce", "Wix", "Squarespace", "Webflow"],
            "commerce": ["Shopify", "BigCommerce", "Magento", "WooCommerce", "PrestaShop", "OpenCart"]
        }
        
        # Find matching seeds
        seeds = []
        for key, companies in sector_seeds.items():
            if key in sector_lower or key in industry_lower:
                seeds.extend(companies)
        
        # If no specific match, use general development/platform seeds
        if not seeds:
            seeds = ["Bubble", "Webflow", "Retool", "Zapier", "Notion", "Airtable"]
        
        return list(set(seeds))[:5]  # Return up to 5 unique seeds

    async def _execute_fallback_searches(self, enriched_profile: Dict[str, Any], 
                                       company_name: str, 
                                       existing_competitors: Set[str]) -> Set[str]:
        """Execute fallback searches when initial searches don't find enough competitors"""
        
        sector = enriched_profile.get('sector', '')
        industry = enriched_profile.get('industry', '')
        
        # **CRITICAL: Use curated comparison and alternative sites + targeted competitor searches**
        fallback_queries = [
            f'{sector} tools comparison site:alternativeto.net',
            f'{sector} alternatives site:capterra.com', 
            f'{sector} comparison site:g2.com',
            f'"{sector}" vs alternatives comparison',
            f'best {sector} 2024 list startups',
            f'{sector} platforms ProductHunt directory',
            f'{industry} {sector} emerging companies TechCrunch',
            f'{sector} marketplace directory list'
        ]
        
        # **NEW: Add sector-specific targeted searches for missing key competitors**
        if sector.lower() in ['ai search', 'search api', 'ai search api']:
            fallback_queries.extend([
                '"You.com" AI search API startup',
                '"SearchGPT" OpenAI search competitor',
                '"Kagi" search engine startup API',
                '"Phind" AI search developer tools',
                '"Brave Search" API independent search',
                'AI search API startups 2024 Perplexity competitors',
                'semantic search API companies Exa Metaphor alternatives',
                'developer search tools API not Google alternatives'
            ])
        elif sector.lower() in ['ai development', 'ai coding', 'ai development platform']:
            fallback_queries.extend([
                '"Cursor" AI coding IDE competitor',
                '"v0" Vercel AI development platform',
                '"Bolt" AI full-stack development',
                '"Windsurf" Codeium AI coding assistant',
                'AI coding assistants startups GitHub Copilot alternatives',
                'AI development platforms not Microsoft startups'
            ])
        elif sector.lower() in ['no-code', 'low-code', 'visual programming']:
            fallback_queries.extend([
                '"Webflow" visual development competitor',
                '"Retool" internal tools builder alternative',
                '"Glide" no-code app builder startup',
                '"Adalo" mobile app no-code platform',
                'no-code startups Bubble alternatives comparison'
            ])
        
        fallback_results = []
        for query in fallback_queries:
            try:
                results = await self.tavily.search(
                    query=query,
                    max_results=3,
                    include_answer=True
                )
                
                if results and results.get("results"):
                    for result in results["results"]:
                        fallback_results.append({
                            **result,
                            "query_type": "fallback_search",
                            "query_context": f"Fallback search for {sector}",
                            "original_query": query
                        })
                
                await asyncio.sleep(0.2)  # Delay between fallback searches
                
            except Exception as e:
                self.logger.warning(f"Fallback search failed for '{query}': {e}")
                continue
        
        # Extract competitors from fallback results
        fallback_competitors = set()
        if fallback_results:
            for result in fallback_results:
                competitors_from_result = await self._extract_companies_from_result_batch(
                    [result], enriched_profile, company_name, "fallback_search"
                )
                fallback_competitors.update(competitors_from_result)
        
        # Filter out existing competitors
        new_competitors = fallback_competitors - existing_competitors
        
        self.logger.info(f"Fallback searches found {len(new_competitors)} additional competitors")
        return new_competitors

    async def _execute_targeted_searches(self, queries: List[Dict[str, str]], company_name: str) -> List[Dict[str, Any]]:
        """Execute all targeted searches in parallel"""
        
        search_tasks = []
        for query_info in queries:
            search_tasks.append(
                self._single_targeted_search(query_info, company_name)
            )
        
        # Execute searches in parallel with a reasonable batch size
        results = []
        batch_size = 5  # Process 5 searches at a time to avoid rate limits
        
        for i in range(0, len(search_tasks), batch_size):
            batch = search_tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            
            for result in batch_results:
                if not isinstance(result, Exception) and result:
                    results.extend(result)
            
            # Small delay between batches
            if i + batch_size < len(search_tasks):
                await asyncio.sleep(0.5)
        
        self.logger.info(f"Completed {len(queries)} searches, got {len(results)} total results")
        return results

    async def _single_targeted_search(self, query_info: Dict[str, str], company_name: str) -> List[Dict[str, Any]]:
        """Execute a single targeted search"""
        
        try:
            results = await self.tavily.search(
                query=query_info["query"],
                max_results=5,
                include_answer=True
            )
            
            if not results or not results.get("results"):
                return []
            
            # Enrich results with query context
            enriched_results = []
            for result in results["results"]:
                enriched_results.append({
                    **result,
                    "query_type": query_info["type"],
                    "query_context": query_info["context"],
                    "original_query": query_info["query"]
                })
            
            return enriched_results
            
        except Exception as e:
            self.logger.warning(f"Search failed for query '{query_info['query']}': {e}")
            return []

    async def _extract_competitors_from_results(self, search_results: List[Dict[str, Any]], 
                                              enriched_profile: Dict[str, Any], 
                                              company_name: str) -> Set[str]:
        """Extract competitor names from search results using LLM analysis"""
        
        if not search_results:
            return set()
        
        # Group results by type for more targeted analysis
        results_by_type = {}
        for result in search_results:
            result_type = result.get("query_type", "general")
            if result_type not in results_by_type:
                results_by_type[result_type] = []
            results_by_type[result_type].append(result)
        
        all_competitors = set()
        
        # Process each type of results
        for result_type, results in results_by_type.items():
            if len(results) > 0:
                competitors = await self._extract_companies_from_result_batch(
                    results, enriched_profile, company_name, result_type
                )
                all_competitors.update(competitors)
        
        self.logger.info(f"Extracted {len(all_competitors)} unique potential competitors")
        return all_competitors

    async def _extract_companies_from_result_batch(self, results: List[Dict[str, Any]], 
                                                 enriched_profile: Dict[str, Any],
                                                 company_name: str, 
                                                 result_type: str) -> Set[str]:
        """Extract companies from a batch of similar result types"""
        
        # Combine content from this batch
        combined_content = []
        for result in results[:5]:  # Top 5 results per batch
            content = result.get("content", "")
            if content and len(content) > 50:
                combined_content.append(content[:1000])  # Limit content length
        
        if not combined_content:
            return set()
        
        content_text = "\n\n---\n\n".join(combined_content)
        
        # Context about what we're looking for
        industry = enriched_profile.get('industry', '')
        sector = enriched_profile.get('sector', '')
        products = ', '.join(enriched_profile.get('core_products', [])[:3])
        
        extraction_prompt = f"""You are an expert competitive intelligence analyst. Extract ONLY the most relevant direct competitors to {company_name} from the following text.

COMPANY CONTEXT:
- Target Company: {company_name}
- Industry: {industry}
- Sector: {sector}
- Core Products: {products}
- Search Type: {result_type}

EXTRACTION REQUIREMENTS:
1. Extract ONLY companies that are DIRECT competitors in the {sector} space
2. Companies must offer similar products/services to what {company_name} offers
3. ABSOLUTELY EXCLUDE these categories:
   - Generic big tech (Google, Microsoft, Amazon, Apple, Meta) unless they have a specific competing product
   - Enterprise software giants (Salesforce, Oracle, SAP, IBM) unless directly competing
   - Generic productivity tools (Teams, Slack, Zoom, Dropbox) unless specifically in same niche
   - Infrastructure providers (AWS, Azure, GCP) unless directly competing
4. PRIORITIZE these types of companies:
   - Startups and scale-ups in the same space
   - SaaS companies with similar offerings  
   - Companies mentioned in comparison contexts
   - Emerging platforms and tools
   - Niche-specific competitors

QUALITY CRITERIA:
- Company must be actively operating in {sector}
- Must serve similar customer segments
- Must be mentioned as alternative/competitor/similar
- Must be realistically comparable to {company_name}

EXAMPLES:
For an AI search company: Perplexity, SearchGPT, You.com, Exa (GOOD) vs Google, Microsoft (BAD)
For a no-code platform: Bubble, Webflow, Retool (GOOD) vs Salesforce, Oracle (BAD)

TEXT TO ANALYZE:
{content_text[:4000]}

OUTPUT FORMAT:
List only the most relevant competitor names, one per line. Maximum 6 companies. Quality over quantity.

Competitor names:"""

        try:
            response = await self.extraction_llm.ainvoke(extraction_prompt)
            
            companies = set()
            
            # **REVOLUTIONARY: Much more sophisticated filtering**
            
            # Comprehensive big tech exclusions - MASSIVELY EXPANDED
            big_tech_exclusions = {
                # Big Tech Core
                'google', 'microsoft', 'amazon', 'apple', 'meta', 'facebook', 'alphabet',
                'tesla', 'netflix', 'uber', 'airbnb', 'twitter', 'x', 'tiktok', 'instagram',
                'bing', 'cortana', 'openai', 'anthropic', 'chatgpt',
                
                # Enterprise Software Giants  
                'salesforce', 'oracle', 'ibm', 'sap', 'cisco', 'vmware', 'servicenow',
                'workday', 'adobe', 'autodesk', 'intuit', 'snowflake', 'palantir',
                
                # Generic Productivity/Collaboration
                'teams', 'slack', 'zoom', 'dropbox', 'box', 'atlassian', 'jira', 'confluence',
                'asana', 'trello', 'monday.com', 'notion', 'clickup', 'airtable',
                
                # Cloud/Infrastructure
                'aws', 'azure', 'gcp', 'cloudflare', 'digitalocean', 'heroku', 'vercel',
                'firebase', 'supabase', 'stripe', 'twilio',
                
                # Search Engines (Big Tech)
                'bing search', 'google search', 'yahoo', 'duckduckgo', 'startpage',
                'ecosia', 'yandex', 'baidu',
                
                # Generic Terms
                'api', 'platform', 'tool', 'service', 'solution', 'software', 'search engine',
                'web search', 'internet search', 'online search'
            }
            
            for line in response.content.split('\n'):
                name = line.strip().strip('-').strip('*').strip().strip('•').strip('1.').strip('2.').strip('3.').strip('4.').strip('5.').strip('6.')
                name_clean = name.lower().strip()
                
                # Skip if empty or too short
                if not name or len(name) < 2:
                    continue
                
                # Skip if it's the target company
                if name_clean == company_name.lower():
                    continue
                
                # Skip big tech exclusions
                if name_clean in big_tech_exclusions:
                    continue
                
                # Skip if contains excluded terms
                excluded_terms = [
                    'http', 'www', '.com', '.io', '.net', '.org', '.ai', '.co',
                    'inc.', 'ltd.', 'llc', 'corp.', 'corporation', 'limited',
                    'the ', 'and ', 'or ', 'for ', 'with ', 'to ', 'of ', 'in ',
                    'company', 'companies', 'platform', 'solution', 'service', 
                    'software', 'tools', 'app', 'website', 'site', 'system',
                    'enterprise', 'business', 'management', 'suite'
                ]
                
                if any(term in name_clean for term in excluded_terms):
                    continue
                
                # Valid length check
                if len(name_clean) > 2 and len(name_clean) < 25:
                    companies.add(name)
            
            return companies
            
        except Exception as e:
            self.logger.warning(f"Company extraction failed for {result_type}: {e}")
            return set()

    async def _validate_and_enrich_competitors(self, competitors: Set[str], 
                                             enriched_profile: Dict[str, Any],
                                             company_name: str) -> List[Dict[str, Any]]:
        """Validate competitors and enrich with additional context"""
        
        if not competitors:
            return []
        
        validation_tasks = []
        competitor_list = list(competitors)
        
        # Process competitors in batches
        batch_size = 3
        validated_competitors = []
        
        for i in range(0, len(competitor_list), batch_size):
            batch = competitor_list[i:i + batch_size]
            batch_tasks = [
                self._validate_single_competitor(comp, enriched_profile, company_name)
                for comp in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if not isinstance(result, Exception) and result:
                    validated_competitors.append(result)
            
            # Small delay between batches
            if i + batch_size < len(competitor_list):
                await asyncio.sleep(0.3)
        
        # Sort by confidence score
        validated_competitors.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)
        
        self.logger.info(f"Validated {len(validated_competitors)} competitors")
        return validated_competitors[:20]  # Return top 20

    async def _validate_single_competitor(self, competitor_name: str,
                                        enriched_profile: Dict[str, Any],
                                        company_name: str) -> Optional[Dict[str, Any]]:
        """Validate and enrich a single competitor"""
        
        try:
            sector = enriched_profile.get("sector", "")
            
            # **CRITICAL FIX: Use multiple targeted validation queries**
            validation_queries = [
                f'"{competitor_name}" vs {sector} comparison review',
                f'"{competitor_name}" {sector} platform features pricing',
                f'"{competitor_name}" alternative to {sector} tools'
            ]
            
            all_content = []
            for query in validation_queries:
                try:
                    results = await self.tavily.search(
                        query=query,
                        max_results=2,
                        include_answer=True
                    )
                    
                    if results and results.get("results"):
                        for result in results["results"]:
                            content = result.get("content", "")
                            if content and len(content) > 50:
                                all_content.append(content[:800])  # Shorter chunks
                except:
                    continue
                
                # Small delay between queries
                await asyncio.sleep(0.1)
            
            if not all_content:
                # **REJECT if no validation content found**
                self.logger.warning(f"No validation content found for {competitor_name}")
                return None
            
            # Analyze combined content to determine competitor validity
            combined_content = "\n\n---\n\n".join(all_content[:3])  # Top 3 content pieces
            
            analysis = await self._analyze_competitor_relevance(
                competitor_name, combined_content, enriched_profile, company_name
            )
            
            # **CRITICAL: Reject low-confidence competitors**
            confidence = analysis.get("confidence_score", 0) if analysis else 0
            if confidence < 0.6:
                self.logger.info(f"Rejecting {competitor_name} due to low confidence: {confidence}")
                return None
            else:
                self.logger.info(f"Accepting {competitor_name} with confidence: {confidence}")
            
            return analysis
            
        except Exception as e:
            self.logger.warning(f"Validation failed for {competitor_name}: {e}")
            return None

    async def _analyze_competitor_relevance(self, competitor_name: str, content: str,
                                          enriched_profile: Dict[str, Any],
                                          company_name: str) -> Dict[str, Any]:
        """Analyze how relevant a competitor is using LLM"""
        
        analysis_prompt = f"""You are an expert competitive intelligence analyst. Determine if {competitor_name} is a legitimate startup/scale-up competitor to {company_name} in the {enriched_profile.get('sector', '')} space.

TARGET COMPANY PROFILE:
- Company: {company_name}
- Description: {enriched_profile.get('description', '')}
- Industry: {enriched_profile.get('industry', '')}
- Sector: {enriched_profile.get('sector', '')}
- Core Products: {', '.join(enriched_profile.get('core_products', []))}
- Use Cases: {', '.join(enriched_profile.get('use_cases', []))}
- Customer Segments: {', '.join(enriched_profile.get('customer_segments', []))}

CANDIDATE COMPETITOR INFORMATION:
{content[:2500]}

INSTANT DISQUALIFICATION (Score 0.0 immediately):
- Big Tech: Google, Microsoft, Amazon, Apple, Meta, Facebook, IBM, Oracle, Salesforce, OpenAI, Anthropic
- Search Engines: Bing, Yahoo, DuckDuckGo (unless AI-specific startups)
- Infrastructure: AWS, Azure, GCP, Cloudflare
- Generic Productivity: Slack, Teams, Zoom, Dropbox (unless direct sector match)

STARTUP/SCALE-UP COMPETITION CRITERIA (Must meet ALL):
1. **Startup/Scale-up**: Must be a smaller company/startup, NOT a tech giant
2. **Sector Match**: Must operate specifically in "{enriched_profile.get('sector', '')}" space
3. **Direct Competition**: Must offer similar products/services that directly substitute for {company_name}
4. **Customer Overlap**: Must target the same customer segments ({', '.join(enriched_profile.get('customer_segments', []))})
5. **Business Model**: Must have comparable business model and approach

CONFIDENCE SCORING (EXTREMELY STRICT):
- 0.9-1.0: Direct startup competitor with nearly identical {enriched_profile.get('sector', '')} offerings
- 0.7-0.8: Strong startup competitor in same niche with significant overlap
- 0.6-0.7: Moderate startup competitor with some product overlap
- 0.5 or below: NOT a legitimate competitor (AUTOMATIC REJECTION)

CRITICAL: If {competitor_name} is a big tech company or doesn't specifically compete in {enriched_profile.get('sector', '')}, score 0.0.

OUTPUT FORMAT:
Category: [direct/indirect/not_relevant]
Confidence: [0.0-1.0]
Evidence: [specific evidence showing competitive relationship in {enriched_profile.get('sector', '')}]
Reasoning: [detailed analysis focusing on startup vs startup competition]
Description: [what {competitor_name} does specifically in {enriched_profile.get('sector', '')} space]"""

        try:
            response = await self.extraction_llm.ainvoke(analysis_prompt)
            lines = response.content.strip().split('\n')
            
            category = "potential"
            confidence = 0.5
            reasoning = "Automated analysis"
            description = f"Company in {enriched_profile.get('industry', 'same industry')}"
            evidence = "Limited information available"
            
            for line in lines:
                if line.startswith("Category:"):
                    category = line.split(":", 1)[1].strip().lower()
                elif line.startswith("Confidence:"):
                    try:
                        confidence_str = line.split(":", 1)[1].strip()
                        confidence = float(confidence_str)
                        self.logger.info(f"Parsed confidence for {competitor_name}: {confidence}")
                    except Exception as e:
                        self.logger.warning(f"Failed to parse confidence '{line}' for {competitor_name}: {e}")
                        confidence = 0.5
                elif line.startswith("Evidence:"):
                    evidence = line.split(":", 1)[1].strip()
                elif line.startswith("Reasoning:"):
                    reasoning = line.split(":", 1)[1].strip()
                elif line.startswith("Description:"):
                    description = line.split(":", 1)[1].strip()
            
            result = {
                "name": competitor_name,
                "description": description,
                "reasoning": reasoning,
                "confidence_score": confidence,
                "category": category,
                "source": "validated_analysis",
                "evidence": evidence
            }
            
            self.logger.info(f"Final analysis result for {competitor_name}: {result}")
            return result
            
        except Exception as e:
            self.logger.warning(f"Analysis failed for {competitor_name}: {e}")
            return {
                "name": competitor_name,
                "description": f"Company in {enriched_profile.get('industry', 'same industry')}",
                "reasoning": "Found through market research",
                "confidence_score": 0.5,
                "category": "potential",
                "source": "basic_validation"
            }

    async def _generate_competitive_analysis(self, competitors: List[Dict[str, Any]],
                                           enriched_profile: Dict[str, Any]) -> str:
        """Generate a comprehensive competitive landscape analysis"""
        
        if not competitors:
            return "No significant competitors identified in the current market analysis."
        
        # Categorize competitors
        direct = [c for c in competitors if c.get("category") == "direct"]
        indirect = [c for c in competitors if c.get("category") == "indirect"]
        emerging = [c for c in competitors if c.get("category") == "emerging"]
        
        analysis_prompt = f"""Generate a competitive landscape analysis based on the following data:

Company Profile:
- Company: {enriched_profile.get('company', '')}
- Industry: {enriched_profile.get('industry', '')}
- Sector: {enriched_profile.get('sector', '')}
- Core Products: {', '.join(enriched_profile.get('core_products', []))}

Direct Competitors ({len(direct)}): {', '.join([c['name'] for c in direct[:5]])}
Indirect Competitors ({len(indirect)}): {', '.join([c['name'] for c in indirect[:5]])}
Emerging Competitors ({len(emerging)}): {', '.join([c['name'] for c in emerging[:5]])}

Provide a 2-3 paragraph analysis covering:
1. Overview of the competitive landscape intensity
2. Key competitive threats and market positioning
3. Strategic implications and opportunities

Keep it concise and strategic."""

        try:
            response = await self.llm.ainvoke(analysis_prompt)
            return response.content.strip()
        except Exception as e:
            self.logger.warning(f"Competitive analysis generation failed: {e}")
            return f"Identified {len(competitors)} competitors across direct, indirect, and emerging categories. Further analysis recommended."

    async def run(self, state: ResearchState) -> ResearchState:
        """Main entry point for the enhanced competitor discovery agent."""
        
        websocket_manager, job_id = self.get_websocket_info(state)
        self.log_agent_start(state)

        # Get enriched profile data
        enriched_profile = state.get('profile', {})
        
        # **DEBUG: Log what we receive from the state**
        self.logger.info(f"=== COMPETITOR DISCOVERY AGENT START ===")
        self.logger.info(f"State keys: {list(state.keys())}")
        self.logger.info(f"Profile keys: {list(enriched_profile.keys()) if enriched_profile else 'EMPTY'}")
        self.logger.info(f"Profile company: {enriched_profile.get('company', 'NOT_FOUND')}")
        self.logger.info(f"Profile sector: {enriched_profile.get('sector', 'NOT_FOUND')}")
        self.logger.info(f"Profile industry: {enriched_profile.get('industry', 'NOT_FOUND')}")
        self.logger.info(f"Profile description length: {len(enriched_profile.get('description', ''))}")
        
        if not enriched_profile.get('company'):
            error_msg = "No enriched profile data available for competitor discovery"
            self.logger.error(error_msg)
            await self.send_error_update(websocket_manager, job_id, error_msg, "Competitor Discovery")
            state['competitors'] = []
            return state

        try:
            # Discover competitors using the enhanced profile-driven method
            result = await self.discover_competitors(
                enriched_profile=enriched_profile,
                websocket_manager=websocket_manager,
                job_id=job_id
            )

            # Update the state with discovered competitors and analysis
            state['competitors'] = result.get('competitors', [])
            state['competitive_analysis'] = result.get('competitive_analysis', '')
            
            self.log_agent_complete(state)
            return state
            
        except Exception as e:
            error_msg = f"Enhanced competitor discovery failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            await self.send_error_update(websocket_manager, job_id, error_msg, "Competitor Discovery")
            state['competitors'] = []
            return state


# Keep compatibility with existing names
CompetitorDiscoveryAgent = EnhancedCompetitorDiscoveryAgent
SimpleCompetitorDiscoveryAgent = EnhancedCompetitorDiscoveryAgent
FocusedCompetitorDiscoveryAgent = EnhancedCompetitorDiscoveryAgent 