from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from backend.config import config


class UserInterests(BaseModel):
    """Structured output for inferred user interests."""
    strategic_interests: List[str] = Field(
        description="List of strategic business interests and goals", 
        max_items=8
    )
    technology_interests: List[str] = Field(
        description="List of technology-related interests and focus areas", 
        max_items=8
    )
    external_signals: List[str] = Field(
        description="List of external market signals and trends to monitor", 
        max_items=8
    )
    information_sources: List[str] = Field(
        description="List of preferred information sources and channels", 
        max_items=8
    )


class InterestInferenceAgent:
    """Infers user interests based on enriched profile data using OpenAI."""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.2,
            api_key=config.OPENAI_API_KEY
        )
        
        # Role-specific reasoning patterns
        self.role_patterns = {
            "CEO": {
                "focus": "strategic vision, market expansion, competitive positioning, investor relations",
                "interests": "global expansion, market share, competitive intelligence, industry trends",
                "sources": "industry reports, financial news, competitor analysis, regulatory updates"
            },
            "CFO": {
                "focus": "financial performance, risk management, compliance, investor relations",
                "interests": "financial metrics, regulatory compliance, funding opportunities, market valuation",
                "sources": "financial news, regulatory sites, investor relations, market analysis"
            },
            "COO": {
                "focus": "operational efficiency, process optimization, partnerships, scaling",
                "interests": "operational excellence, partnership opportunities, scaling strategies, efficiency gains",
                "sources": "operations blogs, industry reports, partnership news, efficiency studies"
            },
            "CPO": {
                "focus": "product strategy, user experience, market fit, competitive products",
                "interests": "product innovation, user research, competitive products, market trends",
                "sources": "product blogs, tech news, user research reports, competitive analysis"
            },
            "CMO": {
                "focus": "marketing strategy, customer acquisition, brand positioning, market trends",
                "interests": "customer acquisition, brand building, marketing trends, competitive positioning",
                "sources": "marketing blogs, social media trends, customer research, competitive analysis"
            },
            "CSO": {
                "focus": "security strategy, compliance, risk management, threat intelligence",
                "interests": "cybersecurity threats, compliance requirements, security technologies, risk mitigation",
                "sources": "security blogs, threat intelligence, regulatory sites, security conferences"
            },
            "CRO": {
                "focus": "risk management, compliance, regulatory changes, operational risk",
                "interests": "regulatory compliance, risk mitigation, operational risk, compliance technologies",
                "sources": "regulatory sites, risk management blogs, compliance news, industry reports"
            }
        }
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("user", self._get_user_prompt())
        ])
        
        # Create the runnable chain with structured output
        self.chain = (
            {"profile": RunnablePassthrough()}
            | self.prompt
            | self.llm.with_structured_output(UserInterests)
        )
    
    def _get_system_prompt(self) -> str:
        """Generate the system prompt with role-specific reasoning."""
        return """You are an expert business analyst who infers user interests based on their company profile and role.

Your task is to analyze the provided company information and user role to determine their likely interests and information needs.

Role-Specific Focus Areas:

CEO: Strategic vision, market expansion, competitive positioning, investor relations
CFO: Financial performance, risk management, compliance, investor relations  
COO: Operational efficiency, process optimization, partnerships, scaling
CPO: Product strategy, user experience, market fit, competitive products
CMO: Marketing strategy, customer acquisition, brand positioning, market trends
CSO: Security strategy, compliance, risk management, threat intelligence
CRO: Risk management, compliance, regulatory changes, operational risk

Reasoning Guidelines:
1. Consider the company's industry, sector, and business model
2. Analyze competitors and market position
3. Consider the user's role and typical responsibilities
4. Factor in company size, growth stage, and market presence
5. Consider regulatory environment and compliance needs
6. Think about technology adoption and innovation focus
7. Consider partnership and ecosystem relationships

Output Guidelines:
- Strategic interests: Business goals, market opportunities, competitive strategies
- Technology interests: Tech focus areas, innovation priorities, technical capabilities
- External signals: Market trends, competitive moves, regulatory changes to monitor
- Information sources: Preferred channels for staying informed and making decisions

Provide specific, actionable interests that would be relevant for someone in this role at this company."""
    
    def _get_user_prompt(self) -> str:
        """Generate the user prompt template."""
        return """Please analyze this user profile and infer their likely interests:

Company: {company}
Role: {role}
Description: {description}
Industry: {industry}
Sector: {sector}
Clients Industries: {clients_industries}
Competitors: {competitors}
Known Clients: {known_clients}
Partners: {partners}

Based on this information, what would be the most relevant interests for someone in the {role} role at {company}?

Consider:
- The company's business model and market position
- The role's typical responsibilities and focus areas
- Industry trends and competitive landscape
- Regulatory environment and compliance needs
- Technology adoption and innovation priorities

Provide specific, actionable interests that would help this person stay informed and make better decisions."""
    
    def infer_interests(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Infer user interests based on enriched profile data.
        
        Args:
            profile: Dictionary from UserProfileEnrichmentAgent
            
        Returns:
            Dictionary containing inferred interests
        """
        try:
            # Run the chain with structured output
            result = self.chain.invoke({"profile": profile})
            
            # Convert to dictionary
            return result.model_dump()
            
        except Exception as e:
            # Fallback to basic interests if inference fails
            role = profile.get("role", "Unknown")
            return self._get_fallback_interests(role)
    
    def infer_interests_async(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Async version of infer_interests.
        
        Args:
            profile: Dictionary from InterestInferenceAgent
            
        Returns:
            Dictionary containing inferred interests
        """
        try:
            # Run the chain asynchronously with structured output
            result = self.chain.ainvoke({"profile": profile})
            
            # Convert to dictionary
            return result.model_dump()
            
        except Exception as e:
            # Fallback to basic interests if inference fails
            role = profile.get("role", "Unknown")
            return self._get_fallback_interests(role)
    
    def _get_fallback_interests(self, role: str) -> Dict[str, Any]:
        """Provide fallback interests based on role."""
        role_pattern = self.role_patterns.get(role, self.role_patterns["CEO"])
        
        return {
            "strategic_interests": [
                "market expansion",
                "competitive positioning", 
                "business growth",
                "strategic partnerships"
            ],
            "technology_interests": [
                "digital transformation",
                "automation",
                "data analytics",
                "cloud technologies"
            ],
            "external_signals": [
                "market trends",
                "competitor moves",
                "regulatory changes",
                "industry developments"
            ],
            "information_sources": [
                "industry reports",
                "business news",
                "competitive analysis",
                "market research"
            ]
        } 