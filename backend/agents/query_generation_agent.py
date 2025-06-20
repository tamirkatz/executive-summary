from typing import Dict, List, Any, Optional
import random
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
                "{company} customer base {year}"
            ],
            "competitor_analysis": [
                "{company} vs {competitor} comparison {year}",
                "{competitor} market position {year}",
                "{competitor} business strategy {year}",
                "{competitor} recent developments {year}",
                "{competitor} competitive analysis {year}",
                "{company} competitors {year}",
                "competition in {industry} {year}",
                "{competitor} strengths weaknesses {year}",
                "{competitor} market share {year}",
                "{competitor} growth strategy {year}"
            ],
            "industry_insights": [
                "{industry} trends {year}",
                "{industry} market size {year}",
                "{industry} growth rate {year}",
                "{industry} challenges {year}",
                "{industry} opportunities {year}",
                "{industry} regulations {year}",
                "{industry} key players {year}",
                "{industry} future outlook {year}",
                "{industry} technology adoption {year}",
                "{industry} customer behavior {year}"
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
            ],
            "news_monitoring": [
                "{company} recent news {year}",
                "{company} announcements {year}",
                "{company} press releases {year}",
                "{company} media coverage {year}",
                "{company} industry news {year}",
                "{company} developments {year}",
                "{company} updates {year}",
                "{company} latest news {year}",
                "{company} breaking news {year}",
                "{company} news articles {year}"
            ],
            "regulatory_compliance": [
                "{company} regulatory compliance {year}",
                "{company} legal issues {year}",
                "{company} regulatory challenges {year}",
                "{industry} regulations {year}",
                "{company} compliance requirements {year}",
                "{company} legal proceedings {year}",
                "{company} regulatory approval {year}",
                "{company} compliance status {year}",
                "{company} regulatory risks {year}",
                "{company} legal framework {year}"
            ],
            "partnership_analysis": [
                "{company} partnerships {year}",
                "{company} strategic alliances {year}",
                "{company} collaborations {year}",
                "{company} joint ventures {year}",
                "{company} integration partners {year}",
                "{company} technology partnerships {year}",
                "{company} business partnerships {year}",
                "{company} partnership strategy {year}",
                "{company} partner ecosystem {year}",
                "{company} alliance network {year}"
            ]
        }
    
    def build_queries(self, 
                     company_name: str, 
                     industry: str, 
                     year: str,
                     categories: List[str] = None,
                     max_queries_per_category: int = 5) -> List[str]:
        """
        Build queries for specified categories.
        
        Args:
            company_name: Name of the company
            industry: Industry name
            year: Year for queries
            categories: List of categories to generate queries for
            max_queries_per_category: Maximum queries per category
            
        Returns:
            List of generated queries
        """
        if categories is None:
            categories = list(self.templates.keys())
        
        queries = []
        for category in categories:
            if category in self.templates:
                category_templates = self.templates[category]
                # Randomly select templates up to max_queries_per_category
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
    """Generates Tavily-ready queries based on user profile, competitors, and company data."""
    
    def __init__(self):
        self.template_builder = QueryTemplateBuilder()
    
    def generate_queries(self,
                        user_profile: Dict[str, Any],
                        known_competitors: List[Dict[str, Any]],
                        domain_registry: List[Dict[str, Any]],
                        company_keywords: List[str],
                        company_name: str,
                        industry: str,
                        year: str = None) -> List[str]:
        """
        Generate Tavily-ready queries based on provided inputs.
        
        Args:
            user_profile: User profile with role and preferences
            known_competitors: List of competitor dictionaries
            domain_registry: List of domain dictionaries
            company_keywords: List of company-specific keywords
            company_name: Name of the company to research
            industry: Industry name
            year: Year for queries (defaults to current year)
            
        Returns:
            List of 10-50 Tavily-ready queries
        """
        if year is None:
            from datetime import datetime
            year = str(datetime.now().year)
        
        queries = []
        
        # 1. Generate role-specific queries based on user profile
        role_queries = self._generate_role_specific_queries(
            user_profile, company_name, industry, year
        )
        queries.extend(role_queries)
        
        # 2. Generate competitor-focused queries
        competitor_queries = self._generate_competitor_queries(
            known_competitors, company_name, year
        )
        queries.extend(competitor_queries)
        
        # 3. Generate domain-specific queries
        domain_queries = self._generate_domain_queries(
            domain_registry, company_name, year
        )
        queries.extend(domain_queries)
        
        # 4. Generate keyword-enhanced queries
        keyword_queries = self._generate_keyword_queries(
            company_keywords, company_name, industry, year
        )
        queries.extend(keyword_queries)
        
        # 5. Generate general research queries
        general_queries = self._generate_general_queries(
            company_name, industry, year
        )
        queries.extend(general_queries)
        
        # Remove duplicates and limit to 10-50 queries
        unique_queries = list(set(queries))
        return unique_queries[:50] if len(unique_queries) > 50 else unique_queries
    
    def _generate_role_specific_queries(self, 
                                      user_profile: Dict[str, Any],
                                      company_name: str,
                                      industry: str,
                                      year: str) -> List[str]:
        """Generate queries specific to the user's business role."""
        role = user_profile.get("role")
        if not role:
            return []
        
        role_categories = {
            BusinessRole.CEO: ["company_analysis", "industry_insights", "financial_analysis", "strategy"],
            BusinessRole.CFO: ["financial_analysis", "regulatory_compliance", "company_analysis"],
            BusinessRole.COO: ["operations", "partnership_analysis", "company_analysis"],
            BusinessRole.CPO: ["product", "partnership_analysis", "company_analysis"],
            BusinessRole.CMO: ["marketing", "partnership_analysis", "company_analysis"],
            BusinessRole.CSO: ["security", "regulatory_compliance", "company_analysis"],
            BusinessRole.CRO: ["risk", "regulatory_compliance", "company_analysis"]
        }
        
        categories = role_categories.get(role, ["company_analysis"])
        return self.template_builder.build_queries(
            company_name, industry, year, categories, max_queries_per_category=3
        )
    
    def _generate_competitor_queries(self,
                                   known_competitors: List[Dict[str, Any]],
                                   company_name: str,
                                   year: str) -> List[str]:
        """Generate queries focused on known competitors."""
        queries = []
        
        for competitor in known_competitors[:5]:  # Limit to top 5 competitors
            competitor_name = competitor.get("name", "")
            if competitor_name:
                competitor_queries = self.template_builder.build_queries(
                    company_name, "", year, ["competitor_analysis"], max_queries_per_category=2
                )
                # Replace company placeholder with competitor name for some queries
                for query in competitor_queries:
                    if "{competitor}" in query:
                        queries.append(query.replace("{competitor}", competitor_name))
                    else:
                        queries.append(query)
        
        return queries
    
    def _generate_domain_queries(self,
                               domain_registry: List[Dict[str, Any]],
                               company_name: str,
                               year: str) -> List[str]:
        """Generate queries based on domain registry categories."""
        queries = []
        
        # Group domains by category
        domains_by_category = {}
        for domain in domain_registry:
            category = domain.get("category", "")
            domain_name = domain.get("domain", "")
            if category and domain_name:
                if category not in domains_by_category:
                    domains_by_category[category] = []
                domains_by_category[category].append(domain_name)
        
        # Generate queries for each category
        for category, domains in domains_by_category.items():
            if "regulators" in category:
                queries.extend([
                    f"{company_name} regulatory compliance {year}",
                    f"{company_name} legal requirements {year}",
                    f"{company_name} regulatory approval {year}"
                ])
            elif "key_partners" in category:
                queries.extend([
                    f"{company_name} partnerships {year}",
                    f"{company_name} strategic alliances {year}",
                    f"{company_name} integration partners {year}"
                ])
            elif "industry_blogs" in category:
                queries.extend([
                    f"{company_name} industry coverage {year}",
                    f"{company_name} media mentions {year}",
                    f"{company_name} press coverage {year}"
                ])
        
        return queries
    
    def _generate_keyword_queries(self,
                                company_keywords: List[str],
                                company_name: str,
                                industry: str,
                                year: str) -> List[str]:
        """Generate queries enhanced with company-specific keywords."""
        queries = []
        
        for keyword in company_keywords[:10]:  # Limit to top 10 keywords
            queries.extend([
                f"{company_name} {keyword} {year}",
                f"{keyword} {industry} {company_name} {year}",
                f"{company_name} {keyword} strategy {year}",
                f"{company_name} {keyword} implementation {year}"
            ])
        
        return queries
    
    def _generate_general_queries(self,
                                company_name: str,
                                industry: str,
                                year: str) -> List[str]:
        """Generate general research queries."""
        return self.template_builder.build_queries(
            company_name, industry, year, 
            ["company_analysis", "industry_insights", "news_monitoring"], 
            max_queries_per_category=3
        ) 