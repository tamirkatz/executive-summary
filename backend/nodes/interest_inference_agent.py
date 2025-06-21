from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from backend.config import config
from ..classes import InputState, ResearchState
from ..agents.base_agent import BaseAgent


class UserInterests(BaseModel):
    """Structured output for inferred user interests."""
    strategic_interests: List[str] = Field(
        description="List of strategic business interests and goals relevant to the user's role and company", 
        max_items=10
    )
    technology_interests: List[str] = Field(
        description="List of technology-related interests and focus areas relevant to the user's role and company", 
        max_items=10
    )
    external_signals: List[str] = Field(
        description="List of external market signals, trends, and competitive moves to monitor", 
        max_items=10
    )
    information_sources: List[str] = Field(
        description="List of preferred information sources and channels for staying informed", 
        max_items=10
    )
    industry_focus: List[str] = Field(
        description="List of specific industries and sectors to focus on based on company and role", 
        max_items=8
    )
    partnership_opportunities: List[str] = Field(
        description="List of potential partnership and collaboration opportunities", 
        max_items=8
    )


class InterestInferenceAgent(BaseAgent):
    """Infers user interests based on enriched profile data using OpenAI."""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        super().__init__(agent_type="interest_inference_agent")
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
            self.prompt
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
8. Focus on actionable, specific interests that would help the user make better decisions

Output Guidelines:
- Strategic interests: Business goals, market opportunities, competitive strategies, growth areas
- Technology interests: Tech focus areas, innovation priorities, technical capabilities, digital transformation
- External signals: Market trends, competitive moves, regulatory changes, industry developments to monitor
- Information sources: Preferred channels for staying informed and making decisions
- Industry focus: Specific industries and sectors relevant to the company's business and user's role
- Partnership opportunities: Potential collaborations, strategic partnerships, ecosystem relationships

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
- Partnership and ecosystem opportunities

Provide specific, actionable interests that would help this person stay informed and make better decisions."""
    
    async def infer_interests_async(self, profile: Dict[str, Any], websocket_manager=None, job_id=None) -> Dict[str, Any]:
        """
        Async version of infer_interests with websocket integration.
        
        Args:
            profile: Dictionary from UserProfileEnrichmentAgent
            websocket_manager: WebSocket manager for status updates
            job_id: Job ID for status updates
            
        Returns:
            Dictionary containing inferred interests
        """
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message="Analyzing user interests and preferences",
                result={"step": "Interest Inference", "substep": "analysis"}
            )

            # Run the chain with structured output
            result = await self.chain.ainvoke({
                "company": profile.get("company", "Unknown Company"),
                "role": profile.get("role", "Unknown Role"),
                "description": profile.get("description", "No description available"),
                "industry": profile.get("industry", "Unknown Industry"),
                "sector": profile.get("sector", "Unknown Sector"),
                "clients_industries": ", ".join(profile.get("clients_industries", [])),
                "competitors": ", ".join(profile.get("competitors", [])),
                "known_clients": ", ".join(profile.get("known_clients", [])),
                "partners": ", ".join(profile.get("partners", []))
            })
            
            # Convert to dictionary
            interests = result.model_dump()
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="interests_complete",
                message="User interests analysis completed",
                result={
                    "step": "Interest Inference",
                    "substep": "complete",
                    "interests": interests
                }
            )
            
            return interests
            
        except Exception as e:
            # Fallback to basic interests if inference fails
            role = profile.get("role", "Unknown")
            error_msg = f"Error inferring interests for {role}: {str(e)}"
            self.log_agent_error({"role": role}, e)
            
            await self.send_error_update(
                websocket_manager, job_id,
                error_msg=error_msg,
                step="Interest Inference",
                continue_research=True
            )
            
            return self._get_fallback_interests(role)
    

    
    def _get_fallback_interests(self, role: str) -> Dict[str, Any]:
        """Provide fallback interests based on role."""
        
        return {
            "strategic_interests": [
                "market expansion",
                "competitive positioning", 
                "business growth",
                "strategic partnerships",
                "industry leadership"
            ],
            "technology_interests": [
                "digital transformation",
                "automation",
                "data analytics",
                "cloud technologies",
                "innovation trends"
            ],
            "external_signals": [
                "market trends",
                "competitor moves",
                "regulatory changes",
                "industry developments",
                "economic indicators"
            ],
            "information_sources": [
                "industry reports",
                "business news",
                "competitive analysis",
                "market research",
                "professional networks"
            ],
            "industry_focus": [
                "primary industry",
                "adjacent markets",
                "emerging sectors",
                "global markets"
            ],
            "partnership_opportunities": [
                "strategic alliances",
                "technology partnerships",
                "channel partnerships",
                "ecosystem collaborations"
            ]
        }
    
    async def run(self, state: ResearchState) -> ResearchState:
        """Main entry point for the interest inference agent following the common node pattern."""
        company = state.get('company', 'Unknown Company')
        profile = state.get('profile', {})
        websocket_manager, job_id = self.get_websocket_info(state)

        self.log_agent_start(state)

        # Check if we have a profile to work with
        if not profile:
            self.logger.warning(f"No profile found in state for {company}")
            # Create a minimal profile from available data
            profile = {
                "company": company,
                "role": state.get('user_role', 'Unknown Role'),
                "description": f"Company in the business sector",
                "industry": "Unknown",
                "sector": "Unknown",
                "clients_industries": [],
                "competitors": [],
                "known_clients": [],
                "partners": []
            }

        # Infer interests
        interests = await self.infer_interests_async(
            profile=profile,
            websocket_manager=websocket_manager,
            job_id=job_id
        )

        # Update the state with interests
        state['user_interests'] = interests

        self.log_agent_complete(state)
        return state 