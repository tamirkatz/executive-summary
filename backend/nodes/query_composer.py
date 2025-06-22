from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from backend.config import config
from backend.classes.state import ResearchState
from ..agents.base_agent import BaseAgent


class TargetedQuery(BaseModel):
    """A surgical query aligned to specific research objectives."""
    query: str = Field(description="The search query string")
    intent_topic: str = Field(description="The research intent topic this query serves")
    objectives_served: List[str] = Field(description="Specific objectives this query will help achieve")
    target_type: str = Field(description="Type of target: Company, Competitor, Industry, Market")
    query_type: str = Field(description="Type of query: documentation, news, technical, financial, strategic")
    expected_sources: List[str] = Field(description="Expected types of sources this query will find")
    rationale: str = Field(description="Why this specific query will find valuable information")


class QuerySet(BaseModel):
    """Complete set of surgical queries for research execution."""
    queries: List[TargetedQuery] = Field(description="List of targeted queries", max_items=50)
    coverage_analysis: str = Field(description="Analysis of how these queries cover the research intents")
    execution_strategy: str = Field(description="Strategy for executing these queries effectively")


class QueryComposer(BaseAgent):
    """Composes surgical, intent-aligned queries from structured research plans."""
    
    def __init__(self, model_name: str = "gpt-4o"):
        super().__init__(agent_type="query_composer")
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.1,
            api_key=config.OPENAI_API_KEY
        )
        
        # Query templates for different research objectives
        self.query_templates = {
            "product_documentation": [
                'site:{company_domain} documentation',
                'site:{company_domain} API reference',
                'site:{company_domain} developer guide',
                'site:{company_domain} features',
                'site:{company_domain} technical specifications'
            ],
            "company_intelligence": [
                '"{company}" design partners site:techcrunch.com',
                '"{company}" strategic customers',
                '"{company}" partnerships announced',
                '"{company}" funding round',
                '"{company}" executive team changes'
            ],
            "competitive_analysis": [
                '"{competitor}" product architecture',
                '"{competitor}" technical capabilities',
                '"{competitor}" customer case studies',
                '"{competitor}" pricing strategy',
                '"{competitor}" recent developments'
            ],
            "technology_trends": [
                '{technology} implementation trends {year}',
                '{technology} enterprise adoption',
                '{technology} regulatory compliance',
                '{technology} market growth',
                '{technology} competitive landscape'
            ],
            "market_intelligence": [
                '{industry} market trends {year}',
                '{industry} regulatory changes',
                '{industry} customer behavior',
                '{industry} growth opportunities',
                '{industry} competitive dynamics'
            ]
        }
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a precision query composer who creates surgical search queries aligned to specific research objectives.

Your role is to translate strategic research intents into highly targeted search queries that will find specific, factual information rather than generic content.

Key Principles:
1. **Surgical Precision**: Each query should target specific documents, sources, or information types
2. **Intent Alignment**: Every query must directly serve one or more research objectives
3. **Source Targeting**: Use site: operators, specific domains, and source types strategically
4. **Evidence Focus**: Target documentation, technical specs, announcements, case studies, not opinions
5. **Competitive Intelligence**: For competitors, focus on individual deep research, not comparisons

Query Types and Strategies:

**Documentation Queries**:
- site:docs.company.com features
- site:company.com/developers API
- "company technical architecture"
- "company integration guide"

**Intelligence Queries**:
- "company" design partners site:techcrunch.com
- "company strategic customers" site:businesswire.com
- "company partnership" announced 2024
- "company executive" joins OR hired

**Competitive Queries** (Individual Analysis):
- "competitor" product capabilities
- "competitor" customer testimonials
- "competitor" technical documentation
- "competitor" pricing model
- "competitor" recent launches

**Technology Queries**:
- technology implementation enterprise
- technology compliance requirements
- technology market adoption 2024
- technology security considerations

**Market Queries**:
- industry trends report 2024
- industry regulatory updates
- industry customer preferences
- industry growth forecast

**Avoid These Query Patterns**:
- Generic comparisons: "company A vs company B"
- Broad overviews: "fintech industry overview"
- Opinion-based: "best payment processor"
- Vague searches: "company information"

**Target High-Value Sources**:
- Company documentation sites
- Technical blogs and engineering posts
- Press releases and announcements
- Industry reports and analyst content
- Regulatory filings and compliance docs
- Customer case studies and testimonials
- Developer community discussions

Focus on queries that will find SPECIFIC, FACTUAL, ACTIONABLE information that directly serves the research objectives."""),
            ("user", """Create surgical search queries for the following research plan:

Company: {company}
Industry: {industry}
Competitors: {competitors}

Research Intents:
{research_intents}

Requirements:
1. Generate 20-30 highly targeted queries
2. Each query must align to specific research objectives
3. Use surgical targeting (site: operators, specific terms, source types)
4. Focus on finding documentation, announcements, technical specs, case studies
5. Avoid generic comparisons or broad overviews
6. Target high-value sources that contain factual information

For each query, specify:
- The exact search string
- Which research intent topic it serves
- Which specific objectives it will help achieve
- Expected source types it will find
- Why this query will find valuable information

Company Context:
{company_context}

Strategic Focus:
{strategic_focus}

Generate queries that will find specific, actionable intelligence rather than generic industry information.""")
        ])
        
        self.chain = self.prompt | self.llm.with_structured_output(QuerySet)
    
    async def compose_queries(self,
                            company: str,
                            industry: str,
                            research_plan: Dict[str, Any],
                            profile: Dict[str, Any],
                            websocket_manager=None,
                            job_id=None) -> List[Dict[str, Any]]:
        """Compose surgical queries from research intents."""
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message="Composing targeted search queries",
                result={"step": "Query Composition", "substep": "analysis"}
            )
            
            # Extract research intents
            research_intents = research_plan.get('research_intents', [])
            strategic_focus = research_plan.get('strategic_focus', '')
            competitors = profile.get('competitors', [])
            
            # Format research intents for prompt
            formatted_intents = self._format_research_intents(research_intents)
            company_context = self._format_company_context(profile)
            
            # Generate query set
            result = await self.chain.ainvoke({
                "company": company,
                "industry": industry,
                "competitors": ", ".join(competitors[:5]),
                "research_intents": formatted_intents,
                "company_context": company_context,
                "strategic_focus": strategic_focus
            })
            
            query_set = result.model_dump()
            queries = query_set.get('queries', [])
            
            # Convert to expected format
            formatted_queries = []
            for i, query_data in enumerate(queries):
                formatted_queries.append({
                    "id": i + 1,
                    "query": query_data.get('query', ''),
                    "intent_topic": query_data.get('intent_topic', ''),
                    "objectives_served": query_data.get('objectives_served', []),
                    "target_type": query_data.get('target_type', ''),
                    "query_type": query_data.get('query_type', ''),
                    "expected_sources": query_data.get('expected_sources', []),
                    "rationale": query_data.get('rationale', '')
                })
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="queries_composed",
                message="Search queries composed successfully",
                result={
                    "step": "Query Composition",
                    "substep": "complete",
                    "total_queries": len(formatted_queries),
                    "coverage": query_set.get('coverage_analysis', ''),
                    "strategy": query_set.get('execution_strategy', '')
                }
            )
            
            return formatted_queries
            
        except Exception as e:
            error_msg = f"Error composing queries: {str(e)}"
            self.log_agent_error({"company": company}, e)
            
            await self.send_error_update(
                websocket_manager, job_id,
                error_msg=error_msg,
                step="Query Composition",
                continue_research=True
            )
            
            # Return fallback queries
            return self._create_fallback_queries(company, industry, profile)
    
    def _format_research_intents(self, research_intents: List[Dict[str, Any]]) -> str:
        """Format research intents for the prompt."""
        formatted = []
        for intent in research_intents:
            topic = intent.get('topic', '')
            objectives = intent.get('objectives', [])
            target = intent.get('target', '')
            priority = intent.get('priority', 3)
            rationale = intent.get('rationale', '')
            
            formatted.append(f"""
Topic: {topic}
Target: {target}
Priority: {priority}/5
Objectives:
{chr(10).join(f"  - {obj}" for obj in objectives)}
Rationale: {rationale}
""")
        
        return "\n".join(formatted)
    
    def _format_company_context(self, profile: Dict[str, Any]) -> str:
        """Format company context for the prompt."""
        context_pieces = []
        
        if description := profile.get('description'):
            context_pieces.append(f"Business: {description}")
        if sector := profile.get('sector'):
            context_pieces.append(f"Sector: {sector}")
        if website := profile.get('website'):
            context_pieces.append(f"Website: {website}")
        if clients := profile.get('known_clients'):
            context_pieces.append(f"Key Clients: {', '.join(clients[:3])}")
        
        return "\n".join(context_pieces) if context_pieces else "Limited context available"
    
    def _create_fallback_queries(self, company: str, industry: str, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create basic fallback queries with heavy competitor focus."""
        fallback_queries = []
        competitors = profile.get('competitors', [])
        
        # COMPETITOR-FOCUSED QUERIES (Priority #1)
        for competitor in competitors[:5]:  # Focus on top 5 competitors
            competitor_queries = [
                # Recent launches and product updates
                f'"{competitor}" product launch 2024',
                f'"{competitor}" new features announcement 2024',
                f'"{competitor}" product update release 2024',
                f'"{competitor}" platform expansion 2024', 
                
                # Partnerships and integrations
                f'"{competitor}" partnership announcement 2024',
                f'"{competitor}" integration launch 2024',
                f'"{competitor}" strategic alliance 2024',
                f'"{competitor}" collaboration news 2024',
                
                # Funding and acquisitions
                f'"{competitor}" funding round 2024',
                f'"{competitor}" acquisition news 2024',
                f'"{competitor}" investment announcement 2024',
                f'"{competitor}" merger deal 2024',
                
                # Market moves and expansion
                f'"{competitor}" market expansion 2024',
                f'"{competitor}" new market entry 2024',
                f'"{competitor}" geographic expansion 2024',
                
                # Technology and innovation
                f'"{competitor}" technology innovation 2024',
                f'"{competitor}" API updates 2024',
                f'"{competitor}" developer platform 2024',
                
                # Business developments
                f'"{competitor}" executive hire 2024',
                f'"{competitor}" strategic move 2024',
                f'"{competitor}" business model change 2024'
            ]
            
            for i, query in enumerate(competitor_queries):
                fallback_queries.append({
                    "id": len(fallback_queries) + 1,
                    "query": query,
                    "intent_topic": f"Competitor Intelligence - {competitor}",
                    "objectives_served": [f"Track {competitor} latest moves"],
                    "target_type": "News",
                    "query_type": "competitor_focus",
                    "expected_sources": ["Press releases", "Tech news", "Business news"],
                    "rationale": f"Monitor recent developments from key competitor {competitor}"
                })
        
        # Company queries (secondary priority)
        company_queries = [
            f'"{company}" vs competitors 2024',
            f'"{company}" competitive advantage 2024',
            f'"{company}" market position 2024'
        ]
        
        for query in company_queries:
            fallback_queries.append({
                "id": len(fallback_queries) + 1,
                "query": query,
                "intent_topic": "Company Positioning",
                "objectives_served": ["Understand competitive position"],
                "target_type": "Mixed",
                "query_type": "company_comparison",
                "expected_sources": ["Industry reports", "Analysis"],
                "rationale": "Understand company's position vs competitors"
            })
        
        # Industry trend queries (tertiary priority)
        industry_queries = [
            f'{industry} latest developments 2024',
            f'{industry} regulatory changes 2024',
            f'{industry} market trends 2024'
        ]
        
        for query in industry_queries:
            fallback_queries.append({
                "id": len(fallback_queries) + 1,
                "query": query,
                "intent_topic": "Industry Intelligence",
                "objectives_served": ["Monitor industry changes"],
                "target_type": "Industry",
                "query_type": "industry_trend",
                "expected_sources": ["Industry publications", "Research"],
                "rationale": "Track industry-wide developments"
            })
        
        return fallback_queries
    
    async def run(self, state: ResearchState) -> ResearchState:
        """Main entry point for the query composer."""
        company = state.get('company', 'Unknown Company')
        profile = state.get('profile', {})
        research_plan = state.get('research_plan', {})
        websocket_manager, job_id = self.get_websocket_info(state)
        
        self.log_agent_start(state)
        
        # Extract industry from profile
        industry = profile.get('industry', 'Unknown Industry')
        
        # Compose surgical queries from research intents
        queries = await self.compose_queries(
            company=company,
            industry=industry,
            research_plan=research_plan,
            profile=profile,
            websocket_manager=websocket_manager,
            job_id=job_id
        )
        
        # Add queries to state
        state['queries'] = queries
        state['query_composition_complete'] = True
        
        self.log_agent_complete(state)
        return state 