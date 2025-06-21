from typing import Dict, List, Any, Optional
import random
from datetime import datetime
from backend.classes.state import ResearchState
from backend.models import BusinessRole


class QueryTemplateBuilder:
    """Builds query templates for different research categories and contexts."""
    
    def __init__(self):
        self.templates = {
            "company_analysis": [
                "{company} overview {year}",
                "{company} business model {year}",
                "{company} revenue model {year}",
                "{company} target market {year}",
                "{company} competitive advantages {year}",
                "{company} leadership team {year}",
                "{company} funding history {year}",
                "{company} partnerships {year}",
                "{company} technology stack {year}",
                "{company} customer base {year}",
                "{company} growth strategy {year}",
                "{company} market position {year}",
                "{company} valuation {year}",
                "{company} financial performance {year}",
                "{company} strategic initiatives {year}"
            ],
            "technology_analysis": [
                "{company} technology stack {year}",
                "{company} AI implementation {year}",
                "{company} digital transformation {year}",
                "{company} software architecture {year}",
                "{company} cloud infrastructure {year}",
                "{company} data analytics {year}",
                "{company} automation {year}",
                "{company} cybersecurity {year}",
                "{company} API integration {year}",
                "{company} machine learning {year}",
                "{company} blockchain {year}",
                "{company} IoT implementation {year}",
                "{company} edge computing {year}",
                "{company} quantum computing {year}",
                "{company} 5G technology {year}"
            ],
            "financial_analysis": [
                "{company} financial performance {year}",
                "{company} revenue growth {year}",
                "{company} funding rounds {year}",
                "{company} investors {year}",
                "{company} valuation {year}",
                "{company} profitability {year}",
                "{company} cash flow {year}",
                "{company} financial metrics {year}",
                "{company} IPO plans {year}",
                "{company} financial health {year}"
            ]
        }
    
    def build_queries(self, 
                     company_name: str, 
                     industry: str, 
                     year: str,
                     categories: List[str] = None,
                     max_queries_per_category: int = 5) -> List[str]:
        """Build queries for specified categories."""
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
                    query = template.format(
                        company=company_name,
                        industry=industry,
                        year=year
                    )
                    queries.append(query)
        
        return queries


class QueryGenerationAgent:
    """Generates comprehensive Tavily-ready queries based on user interests and company data."""
    
    def __init__(self):
        self.template_builder = QueryTemplateBuilder()
        self.year = str(datetime.now().year)
    
    async def generate_queries_from_interests_async(self,
                                                  user_interests: Dict[str, Any],
                                                  company_name: str,
                                                  industry: str,
                                                  competitors: List[str] = None,
                                                  year: str = None,
                                                  websocket_manager=None,
                                                  job_id=None) -> List[str]:
        """Generate queries based on user interests."""
        if year is None:
            year = self.year
            
        queries = []
        
        # Basic company queries
        queries.extend([
            f"{company_name} overview {year}",
            f"{company_name} business model {year}",
            f"{company_name} financial performance {year}",
            f"{company_name} recent news {year}",
            f"{company_name} market position {year}"
        ])
        
        # Industry queries
        queries.extend([
            f"{industry} market trends {year}",
            f"{industry} market size {year}",
            f"{industry} key players {year}"
        ])
        
        # Competitor queries
        if competitors:
            for competitor in competitors[:3]:  # Limit to top 3
                queries.append(f"{company_name} vs {competitor} comparison {year}")
        
        return queries[:20]  # Limit total queries
    
    def generate_queries(self,
                        user_profile: Dict[str, Any],
                        known_competitors: List[Dict[str, Any]],
                        domain_registry: List[Dict[str, Any]],
                        company_keywords: List[str],
                        company_name: str,
                        industry: str,
                        year: str = None) -> List[str]:
        """Generate queries based on various inputs."""
        if year is None:
            year = self.year
            
        queries = []
        
        # Basic queries
        queries.extend([
            f"{company_name} overview {year}",
            f"{company_name} business strategy {year}",
            f"{company_name} financial performance {year}",
            f"{company_name} market position {year}",
            f"{company_name} recent developments {year}"
        ])
        
        # Industry queries
        queries.extend([
            f"{industry} market analysis {year}",
            f"{industry} trends {year}",
            f"{industry} competition {year}"
        ])
        
        # Keyword-based queries
        for keyword in company_keywords[:5]:  # Limit keywords
            queries.append(f"{company_name} {keyword} {year}")
        
        return queries[:25]  # Limit total queries
    
    async def run(self, state: ResearchState) -> ResearchState:
        """Run the query generation agent."""
        try:
            company_name = state.get('company', 'Unknown Company')
            industry = state.get('industry', 'Unknown Industry')
            
            # Generate basic queries
            queries = self.generate_queries(
                user_profile={},
                known_competitors=[],
                domain_registry=[],
                company_keywords=[],
                company_name=company_name,
                industry=industry
            )
            
            state['generated_queries'] = queries
            return state
            
        except Exception as e:
            print(f"Error in QueryGenerationAgent: {e}")
            # Return basic queries as fallback
            company_name = state.get('company', 'Unknown Company')
            state['generated_queries'] = [
                f"{company_name} overview {self.year}",
                f"{company_name} business model {self.year}",
                f"{company_name} recent news {self.year}"
            ]
            return state 