from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from backend.config import config
from backend.classes.state import ResearchState
from ..agents.base_agent import BaseAgent


class ResearchIntent(BaseModel):
    """Structured research intent for a specific topic."""
    topic: str = Field(description="The research topic or area of focus")
    objectives: List[str] = Field(description="Specific objectives to achieve for this topic", max_items=5)
    target: str = Field(description="Research target: 'Company', 'Competitor', 'Industry', or 'Market'")
    priority: int = Field(description="Priority level 1-5 (5 being highest priority)", ge=1, le=5)
    rationale: str = Field(description="Why this research is important for strategic decision-making")


class ResearchPlan(BaseModel):
    """Complete structured research plan."""
    research_intents: List[ResearchIntent] = Field(description="List of research intents", max_items=12)
    strategic_focus: str = Field(description="Overall strategic focus of the research")
    success_criteria: List[str] = Field(description="How to measure research success", max_items=5)


class ResearchIntentPlanner(BaseAgent):
    """Plans strategic research by defining clear intents and objectives before query generation."""
    
    def __init__(self, model_name: str = "gpt-4o"):
        super().__init__(agent_type="research_intent_planner")
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.1,
            api_key=config.OPENAI_API_KEY
        )
        
        # Role-specific research focus areas
        self.role_research_focus = {
            "CEO": {
                "primary": ["Strategic Positioning", "Competitive Landscape", "Market Opportunities"],
                "secondary": ["Partnership Ecosystem", "Technology Differentiation", "Financial Performance"]
            },
            "CFO": {
                "primary": ["Financial Performance", "Market Valuation", "Investment Landscape"],
                "secondary": ["Competitive Positioning", "Regulatory Environment", "Operational Efficiency"]
            },
            "COO": {
                "primary": ["Operational Capabilities", "Technology Infrastructure", "Process Optimization"],
                "secondary": ["Competitive Operations", "Partnership Integration", "Scalability"]
            },
            "CPO": {
                "primary": ["Product Capabilities", "Technology Architecture", "User Experience"],
                "secondary": ["Competitive Features", "Innovation Trends", "Developer Ecosystem"]
            },
            "CMO": {
                "primary": ["Market Positioning", "Customer Acquisition", "Brand Strategy"],
                "secondary": ["Competitive Marketing", "Customer Insights", "Channel Strategy"]
            }
        }
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("user", self._get_user_prompt())
        ])
        
        self.chain = (
            self.prompt
            | self.llm.with_structured_output(ResearchPlan)
        )
    
    def _get_system_prompt(self) -> str:
        """Generate the system prompt for research planning."""
        return """You are a strategic research planner who designs comprehensive intelligence gathering strategies.

Your role is to create structured research plans that will yield actionable business intelligence. You focus on WHAT we need to know and WHY, not HOW to search for it.

Key Principles:
1. **Strategic Focus**: Every research intent must serve a clear strategic purpose
2. **Objective Clarity**: Each objective should be specific and measurable
3. **Evidence-Based**: Focus on finding concrete evidence, documentation, and factual information
4. **Competitive Intelligence**: Understand each entity (company, competitor) individually before making comparisons
5. **Actionable Outcomes**: Research should lead to specific strategic decisions or actions

Research Intent Categories:
- **Company Deep Dive**: Understanding our own capabilities, positioning, and strategic assets
- **Competitive Analysis**: Individual deep research on each competitor's strengths/weaknesses
- **Market Intelligence**: Industry trends, customer behavior, regulatory environment
- **Technology Assessment**: Technical capabilities, innovation trends, architectural decisions
- **Strategic Opportunities**: Partnership potential, market gaps, expansion opportunities
- **Risk Assessment**: Competitive threats, market disruptions, regulatory risks

Target Classifications:
- **Company**: Research about the primary company
- **Competitor**: Research about specific competitors (individual analysis)
- **Industry**: Broader industry and market research
- **Market**: Customer behavior, market trends, and opportunities

Priority Guidelines:
- Priority 5: Critical for immediate strategic decisions
- Priority 4: Important for medium-term planning
- Priority 3: Valuable for comprehensive understanding
- Priority 2: Nice-to-have contextual information
- Priority 1: Background research

Focus on creating research intents that will find SPECIFIC, FACTUAL information rather than generic industry overviews."""
    
    def _get_user_prompt(self) -> str:
        """Generate the user prompt template."""
        return """Create a comprehensive research plan for strategic intelligence gathering:

Company: {company}
Industry: {industry}
User Role: {user_role}
Competitors: {competitors}
Strategic Interests: {strategic_interests}
Technology Interests: {technology_interests}

Context:
{company_context}

Based on this information, create a structured research plan that will provide actionable intelligence for a {user_role} at {company}.

Focus Areas for {user_role}:
{role_focus_areas}

Requirements:
1. Create 8-12 specific research intents
2. Each intent should have clear, measurable objectives
3. Prioritize based on strategic importance to the {user_role} role
4. Include both company-specific and competitive research
5. Focus on finding concrete evidence and documentation
6. Ensure research will lead to actionable strategic insights

Industry-Specific Considerations:
- For fintech: compliance, API capabilities, merchant connectivity, payment processing architecture
- For AI: model capabilities, infrastructure, safety measures, enterprise deployment
- For e-commerce: logistics, customer acquisition, platform capabilities, marketplace strategy

Strategic Context:
- What competitive advantages does {company} need to understand?
- What market opportunities should be evaluated?
- What competitive threats need assessment?
- What partnership opportunities should be explored?
- What technology gaps might exist?

Create research intents that will answer these strategic questions with specific, factual evidence."""
    
    async def create_research_plan(self, 
                                 company: str,
                                 industry: str, 
                                 user_role: str,
                                 profile: Dict[str, Any],
                                 user_interests: Dict[str, Any],
                                 websocket_manager=None,
                                 job_id=None) -> Dict[str, Any]:
        """Create a comprehensive research plan."""
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message="Creating strategic research plan",
                result={"step": "Research Intent Planning", "substep": "analysis"}
            )
            
            # Extract key information
            competitors = profile.get('competitors', [])
            strategic_interests = user_interests.get('strategic_interests', [])
            technology_interests = user_interests.get('technology_interests', [])
            
            # Get role-specific focus areas
            role_focus = self.role_research_focus.get(user_role, {
                "primary": ["Strategic Positioning", "Competitive Analysis"],
                "secondary": ["Market Opportunities", "Technology Assessment"]
            })
            
            # Create company context
            company_context = self._format_company_context(profile, user_interests)
            
            # Generate research plan
            result = await self.chain.ainvoke({
                "company": company,
                "industry": industry,
                "user_role": user_role,
                "competitors": ", ".join(competitors[:5]),
                "strategic_interests": ", ".join(strategic_interests[:5]),
                "technology_interests": ", ".join(technology_interests[:5]),
                "company_context": company_context,
                "role_focus_areas": self._format_role_focus(role_focus)
            })
            
            research_plan = result.model_dump()
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="plan_complete",
                message="Research plan created successfully",
                result={
                    "step": "Research Intent Planning",
                    "substep": "complete",
                    "total_intents": len(research_plan.get('research_intents', [])),
                    "strategic_focus": research_plan.get('strategic_focus', '')
                }
            )
            
            return research_plan
            
        except Exception as e:
            error_msg = f"Error creating research plan: {str(e)}"
            self.log_agent_error({"company": company}, e)
            
            await self.send_error_update(
                websocket_manager, job_id,
                error_msg=error_msg,
                step="Research Intent Planning",
                continue_research=True
            )
            
            # Return fallback plan
            return self._create_fallback_plan(company, user_role, industry)
    
    def _format_company_context(self, profile: Dict[str, Any], user_interests: Dict[str, Any]) -> str:
        """Format company context for the prompt."""
        context_pieces = []
        
        if description := profile.get('description'):
            context_pieces.append(f"Business: {description}")
        if sector := profile.get('sector'):
            context_pieces.append(f"Sector: {sector}")
        if clients := profile.get('known_clients'):
            context_pieces.append(f"Key Clients: {', '.join(clients[:3])}")
        if partners := profile.get('partners'):
            context_pieces.append(f"Partners: {', '.join(partners[:3])}")
        
        return "\n".join(context_pieces) if context_pieces else "Limited context available"
    
    def _format_role_focus(self, role_focus: Dict[str, List[str]]) -> str:
        """Format role focus areas for the prompt."""
        primary = ", ".join(role_focus.get('primary', []))
        secondary = ", ".join(role_focus.get('secondary', []))
        return f"Primary Focus: {primary}\nSecondary Focus: {secondary}"
    
    def _create_fallback_plan(self, company: str, user_role: str, industry: str) -> Dict[str, Any]:
        """Create a basic fallback research plan."""
        return {
            "research_intents": [
                {
                    "topic": "Company Capabilities",
                    "objectives": [
                        f"Understand {company}'s core product offerings",
                        f"Identify {company}'s key differentiators",
                        f"Assess {company}'s market position"
                    ],
                    "target": "Company",
                    "priority": 5,
                    "rationale": "Essential for understanding our strategic position"
                },
                {
                    "topic": "Competitive Landscape",
                    "objectives": [
                        f"Analyze key competitors in {industry}",
                        "Identify competitive threats and opportunities",
                        "Assess market positioning"
                    ],
                    "target": "Competitor",
                    "priority": 4,
                    "rationale": "Critical for strategic decision-making"
                },
                {
                    "topic": "Market Opportunities",
                    "objectives": [
                        f"Identify growth opportunities in {industry}",
                        "Assess market trends and dynamics",
                        "Evaluate expansion possibilities"
                    ],
                    "target": "Market",
                    "priority": 4,
                    "rationale": "Important for growth strategy"
                }
            ],
            "strategic_focus": f"Comprehensive intelligence gathering for {user_role} strategic decision-making",
            "success_criteria": [
                "Clear understanding of competitive position",
                "Identification of strategic opportunities",
                "Actionable insights for decision-making"
            ]
        }
    
    async def run(self, state: ResearchState) -> ResearchState:
        """Main entry point for the research intent planner."""
        company = state.get('company', 'Unknown Company')
        profile = state.get('profile', {})
        user_interests = state.get('user_interests', {})
        user_role = state.get('user_role', 'CEO')
        websocket_manager, job_id = self.get_websocket_info(state)
        
        self.log_agent_start(state)
        
        # Extract industry from profile
        industry = profile.get('industry', 'Unknown Industry')
        
        # Create comprehensive research plan
        research_plan = await self.create_research_plan(
            company=company,
            industry=industry,
            user_role=user_role,
            profile=profile,
            user_interests=user_interests,
            websocket_manager=websocket_manager,
            job_id=job_id
        )
        
        # Add research plan to state
        state['research_plan'] = research_plan
        state['research_planning_complete'] = True
        
        self.log_agent_complete(state)
        return state 