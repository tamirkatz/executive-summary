from typing import Dict, List, Any, Optional
import random
from datetime import datetime
from backend.classes.state import ResearchState
from backend.models import BusinessRole


class QueryTemplateBuilder:
    """Builds deep research queries for comprehensive company intelligence."""
    
    def __init__(self):
        self.templates = {
            # Deep company understanding queries
            "company_deep_dive": [
                "{company} product architecture documentation {year}",
                "{company} technical documentation {year}",
                "{company} design partners program {year}",
                "{company} strategic customers case studies {year}",
                "{company} enterprise clients implementation {year}",
                "{company} API documentation developer resources {year}",
                "{company} engineering blog technical insights {year}",
                "{company} product roadmap announcements {year}",
                "{company} customer success stories {year}",
                "{company} technical partnerships integrations {year}"
            ],
            
            # Strategic positioning and capabilities
            "strategic_capabilities": [
                "{company} core technology stack {year}",
                "{company} competitive differentiation {year}",
                "{company} intellectual property patents {year}",
                "{company} research and development focus {year}",
                "{company} engineering team expertise {year}",
                "{company} technology acquisitions {year}",
                "{company} platform capabilities {year}",
                "{company} scalability architecture {year}",
                "{company} security infrastructure {year}",
                "{company} data processing capabilities {year}"
            ],
            
            # Market positioning and customer insights
            "market_positioning": [
                "{company} target market segments {year}",
                "{company} customer acquisition strategy {year}",
                "{company} pricing strategy model {year}",
                "{company} go-to-market approach {year}",
                "{company} channel partnerships {year}",
                "{company} customer retention metrics {year}",
                "{company} market penetration strategy {year}",
                "{company} customer feedback testimonials {year}",
                "{company} user experience design {year}",
                "{company} customer support approach {year}"
            ],
            
            # Competitive intelligence (individual company research)
            "competitor_deep_research": [
                "{competitor} product capabilities analysis {year}",
                "{competitor} technical architecture {year}",
                "{competitor} strategic partnerships {year}",
                "{competitor} customer base analysis {year}",
                "{competitor} recent product launches {year}",
                "{competitor} funding and investment {year}",
                "{competitor} hiring patterns engineering {year}",
                "{competitor} technology stack choices {year}",
                "{competitor} market expansion strategy {year}",
                "{competitor} weaknesses and challenges {year}"
            ],
            
            # Industry and ecosystem understanding
            "industry_ecosystem": [
                "{industry} technology trends {year}",
                "{industry} regulatory developments {year}",
                "{industry} emerging standards {year}",
                "{industry} customer behavior shifts {year}",
                "{industry} innovation patterns {year}",
                "{industry} partnership ecosystems {year}",
                "{industry} market consolidation trends {year}",
                "{industry} new entrant threats {year}",
                "{industry} technology disruption {year}",
                "{industry} investment landscape {year}"
            ],
            
            # Strategic opportunities and threats
            "strategic_analysis": [
                "{company} expansion opportunities {year}",
                "{company} strategic vulnerabilities {year}",
                "{company} partnership potential {year}",
                "{company} technology gaps {year}",
                "{company} market share growth {year}",
                "{company} competitive threats {year}",
                "{company} innovation opportunities {year}",
                "{company} operational challenges {year}",
                "{company} regulatory risks {year}",
                "{company} financial performance {year}"
            ]
        }
    
    def build_research_queries(self, 
                             company_name: str, 
                             industry: str, 
                             year: str,
                             competitors: List[str] = None,
                             categories: List[str] = None,
                             max_queries_per_category: int = 4) -> List[str]:
        """Build comprehensive research queries for deep understanding."""
        if categories is None:
            categories = list(self.templates.keys())
        
        queries = []
        
        for category in categories:
            if category in self.templates:
                category_templates = self.templates[category]
                selected_templates = random.sample(
                    category_templates, 
                    min(max_queries_per_category, len(category_templates))
                )
                
                for template in selected_templates:
                    if category == "competitor_deep_research" and competitors:
                        # Generate separate deep research queries for each competitor
                        for competitor in competitors[:3]:  # Focus on top 3 competitors
                            query = template.format(
                                competitor=competitor,
                                year=year
                            )
                            queries.append(query)
                    else:
                        query = template.format(
                            company=company_name,
                            industry=industry,
                            year=year
                        )
                        queries.append(query)
        
        return queries


class QueryGenerationAgent:
    """Generates deep research queries for comprehensive strategic intelligence."""
    
    def __init__(self):
        self.template_builder = QueryTemplateBuilder()
        self.year = str(datetime.now().year)
        
        # Role-specific research priorities
        self.role_research_priorities = {
            "CEO": [
                "strategic_capabilities", "market_positioning", "strategic_analysis",
                "competitor_deep_research", "industry_ecosystem"
            ],
            "CFO": [
                "strategic_analysis", "market_positioning", "competitor_deep_research",
                "industry_ecosystem", "strategic_capabilities"
            ],
            "COO": [
                "strategic_capabilities", "company_deep_dive", "strategic_analysis",
                "competitor_deep_research", "industry_ecosystem"
            ],
            "CPO": [
                "company_deep_dive", "strategic_capabilities", "competitor_deep_research",
                "market_positioning", "industry_ecosystem"
            ],
            "CMO": [
                "market_positioning", "competitor_deep_research", "strategic_analysis",
                "industry_ecosystem", "company_deep_dive"
            ],
            "CSO": [
                "strategic_capabilities", "strategic_analysis", "competitor_deep_research",
                "industry_ecosystem", "company_deep_dive"
            ],
            "CRO": [
                "strategic_analysis", "industry_ecosystem", "competitor_deep_research",
                "strategic_capabilities", "market_positioning"
            ]
        }
    
    def _generate_industry_specific_research_queries(self, company_name: str, industry: str, 
                                                   sector: str, year: str) -> List[str]:
        """Generate industry-specific deep research queries."""
        queries = []
        
        # Industry-specific research patterns
        industry_research = {
            "Financial Technology": [
                f"{company_name} payment processing architecture {year}",
                f"{company_name} compliance framework implementation {year}",
                f"{company_name} fraud detection capabilities {year}",
                f"{company_name} merchant onboarding process {year}",
                f"{company_name} API ecosystem partnerships {year}",
                f"{company_name} regulatory compliance strategy {year}",
                f"{company_name} risk management systems {year}",
                f"{company_name} international expansion approach {year}",
                f"{company_name} developer tools documentation {year}",
                f"{company_name} enterprise integration capabilities {year}",
                # Research fintech ecosystem trends
                f"payment processing innovation trends {year}",
                f"fintech regulatory landscape changes {year}",
                f"merchant connectivity standards {year}",
                f"payment orchestration platforms {year}",
                f"embedded finance opportunities {year}"
            ],
            "Artificial Intelligence": [
                f"{company_name} model architecture details {year}",
                f"{company_name} training data approach {year}",
                f"{company_name} compute infrastructure scaling {year}",
                f"{company_name} AI safety measures {year}",
                f"{company_name} enterprise deployment tools {year}",
                f"{company_name} API rate limits pricing {year}",
                f"{company_name} fine-tuning capabilities {year}",
                f"{company_name} multimodal capabilities {year}",
                f"{company_name} developer ecosystem tools {year}",
                f"{company_name} research publications {year}",
                # Research AI ecosystem trends
                f"large language model capabilities comparison {year}",
                f"AI regulation compliance requirements {year}",
                f"enterprise AI adoption patterns {year}",
                f"AI infrastructure requirements {year}",
                f"AI safety standards development {year}"
            ],
            "E-commerce": [
                f"{company_name} logistics network capabilities {year}",
                f"{company_name} inventory management system {year}",
                f"{company_name} customer acquisition channels {year}",
                f"{company_name} marketplace seller tools {year}",
                f"{company_name} payment processing integration {year}",
                f"{company_name} mobile app capabilities {year}",
                f"{company_name} supply chain partnerships {year}",
                f"{company_name} customer service approach {year}",
                f"{company_name} data analytics capabilities {year}",
                f"{company_name} international expansion {year}",
                # Research e-commerce ecosystem trends
                f"e-commerce platform capabilities comparison {year}",
                f"mobile commerce adoption trends {year}",
                f"supply chain optimization technologies {year}",
                f"customer experience personalization {year}",
                f"social commerce integration trends {year}"
            ]
        }
        
        # Add industry-specific queries if available
        if industry in industry_research:
            queries.extend(industry_research[industry])
        
        return queries
    
    def _generate_competitive_research_strategy(self, company_name: str, 
                                              competitors: List[str], 
                                              industry: str, year: str) -> List[str]:
        """Generate strategic competitive research queries for deep understanding."""
        queries = []
        
        # For each competitor, generate comprehensive research queries
        for competitor in competitors[:4]:  # Focus on top 4 competitors
            queries.extend([
                # Deep product understanding
                f"{competitor} product documentation analysis {year}",
                f"{competitor} customer case studies {year}",
                f"{competitor} technical capabilities overview {year}",
                f"{competitor} pricing strategy analysis {year}",
                f"{competitor} customer testimonials feedback {year}",
                
                # Strategic positioning
                f"{competitor} market positioning strategy {year}",
                f"{competitor} target customer segments {year}",
                f"{competitor} partnership ecosystem {year}",
                f"{competitor} go-to-market approach {year}",
                f"{competitor} competitive advantages {year}",
                
                # Operational insights
                f"{competitor} engineering team structure {year}",
                f"{competitor} recent hiring patterns {year}",
                f"{competitor} technology investments {year}",
                f"{competitor} product development roadmap {year}",
                f"{competitor} customer support quality {year}",
                
                # Market performance
                f"{competitor} market share trends {year}",
                f"{competitor} customer growth metrics {year}",
                f"{competitor} financial performance {year}",
                f"{competitor} funding and investments {year}",
                f"{competitor} expansion strategy {year}"
            ])
        
        # Industry positioning analysis
        queries.extend([
            f"{industry} market leaders comparison {year}",
            f"{industry} innovation trends analysis {year}",
            f"{industry} customer preferences shifts {year}",
            f"{industry} technology adoption patterns {year}",
            f"{industry} competitive landscape evolution {year}"
        ])
        
        return queries
    
    def _generate_strategic_opportunity_queries(self, company_name: str, industry: str,
                                              user_interests: Dict[str, Any], year: str) -> List[str]:
        """Generate queries to identify strategic opportunities and gaps."""
        queries = []
        
        # Strategic opportunity research
        strategic_interests = user_interests.get("strategic_interests", [])
        for interest in strategic_interests[:5]:
            queries.extend([
                f"{company_name} {interest} capability assessment {year}",
                f"{industry} {interest} market opportunity {year}",
                f"{interest} technology trends {year}",
                f"{interest} partnership opportunities {year}"
            ])
        
        # Technology opportunity research
        tech_interests = user_interests.get("technology_interests", [])
        for tech in tech_interests[:5]:
            queries.extend([
                f"{company_name} {tech} implementation status {year}",
                f"{tech} adoption trends {industry} {year}",
                f"{tech} competitive advantage opportunities {year}",
                f"{tech} market maturity analysis {year}"
            ])
        
        # Partnership and ecosystem opportunities
        partnership_opps = user_interests.get("partnership_opportunities", [])
        for opp in partnership_opps[:3]:
            queries.extend([
                f"{company_name} {opp} partnership potential {year}",
                f"{opp} ecosystem development trends {year}",
                f"{opp} strategic alliance opportunities {year}"
            ])
        
        return queries
    
    async def generate_comprehensive_research_queries(self,
                                                    user_interests: Dict[str, Any],
                                                    company_name: str,
                                                    industry: str,
                                                    competitors: List[str] = None,
                                                    year: str = None,
                                                    profile: Dict[str, Any] = None,
                                                    user_role: str = None,
                                                    websocket_manager=None,
                                                    job_id=None) -> List[str]:
        """Generate comprehensive research queries for strategic intelligence."""
        if year is None:
            year = self.year
        
        if competitors is None:
            competitors = []
            
        queries = []
        
        if websocket_manager and job_id:
            await websocket_manager.send_status_update(
                job_id=job_id,
                status="processing",
                message="Generating comprehensive research strategy",
                result={
                    "step": "Query Generation",
                    "substep": "research_planning"
                }
            )
        
        # 1. Deep company research (understand our own capabilities first)
        role_categories = self.role_research_priorities.get(user_role, ["strategic_capabilities"])
        company_research_queries = self.template_builder.build_research_queries(
            company_name, industry, year, 
            competitors=competitors,
            categories=role_categories,
            max_queries_per_category=3
        )
        queries.extend(company_research_queries)
        
        # 2. Industry-specific deep research
        sector = profile.get('sector', '') if profile else ''
        industry_queries = self._generate_industry_specific_research_queries(
            company_name, industry, sector, year
        )
        queries.extend(industry_queries)
        
        # 3. Comprehensive competitive research (understand each competitor deeply)
        if competitors:
            competitive_queries = self._generate_competitive_research_strategy(
                company_name, competitors, industry, year
            )
            queries.extend(competitive_queries)
        
        # 4. Strategic opportunity identification
        opportunity_queries = self._generate_strategic_opportunity_queries(
            company_name, industry, user_interests, year
        )
        queries.extend(opportunity_queries)
        
        # 5. Add specific high-value research for fintech companies
        if industry == "Financial Technology" or "payment" in company_name.lower():
            queries.extend([
                f"{company_name} merchant connectivity protocol support {year}",
                f"{company_name} payment orchestration capabilities {year}",
                f"{company_name} compliance automation tools {year}",
                f"{company_name} developer ecosystem growth {year}",
                f"{company_name} enterprise payment solutions {year}",
                f"MCP server adoption payment industry {year}",
                f"payment processing API standardization {year}",
                f"embedded finance market opportunities {year}",
                f"gaming payment regulation compliance {year}",
                f"cross-border payment innovation {year}"
            ])
        
        # Remove duplicates and prioritize
        unique_queries = list(dict.fromkeys(queries))
        
        if websocket_manager and job_id:
            await websocket_manager.send_status_update(
                job_id=job_id,
                status="research_queries_ready",
                message=f"Generated {len(unique_queries)} research queries",
                result={
                    "step": "Query Generation",
                    "total_queries": len(unique_queries),
                    "research_approach": "comprehensive_intelligence"
                }
            )
        
        return unique_queries[:60]  # Comprehensive research requires more queries
    
    async def run(self, state: ResearchState) -> ResearchState:
        """Main entry point for the query generation agent."""
        try:
            company_name = state.get('company', 'Unknown Company')
            user_interests = state.get('user_interests', {})
            profile = state.get('profile', {})
            user_role = state.get('user_role', 'CEO')
            websocket_manager = state.get('websocket_manager')
            job_id = state.get('job_id')
            
            # Extract data from profile
            industry = profile.get('industry', 'Unknown Industry')
            competitors = profile.get('competitors', [])
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message=f"Planning comprehensive research for {company_name}",
                    result={
                        "step": "Query Generation",
                        "substep": "strategic_planning"
                    }
                )
            
            # Generate comprehensive research queries
            if user_interests:
                queries = await self.generate_comprehensive_research_queries(
                    user_interests=user_interests,
                    company_name=company_name,
                    industry=industry,
                    competitors=competitors,
                    profile=profile,
                    user_role=user_role,
                    websocket_manager=websocket_manager,
                    job_id=job_id
                )
            else:
                # Fallback to basic research queries
                queries = [
                    f"{company_name} technical capabilities documentation {self.year}",
                    f"{company_name} strategic partnerships {self.year}",
                    f"{company_name} customer case studies {self.year}",
                    f"{industry} market analysis {self.year}",
                    f"{industry} competitive landscape {self.year}"
                ]
            
            state['generated_queries'] = queries
            state['query_generation_complete'] = True
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="queries_complete",
                    message=f"Research strategy complete: {len(queries)} queries",
                    result={
                        "step": "Query Generation",
                        "total_queries": len(queries),
                        "approach": "deep_research_methodology"
                    }
                )
            
            return state
            
        except Exception as e:
            print(f"Error in QueryGenerationAgent: {e}")
            # Return basic research queries as fallback
            company_name = state.get('company', 'Unknown Company')
            state['generated_queries'] = [
                f"{company_name} capabilities analysis {self.year}",
                f"{company_name} strategic positioning {self.year}",
                f"{company_name} market opportunities {self.year}"
            ]
            state['query_generation_complete'] = True
            return state 