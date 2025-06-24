import logging
from typing import Any, AsyncIterator, Dict

from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph

from .classes.state import InputState, ResearchState
from .nodes import GroundingNode
from .nodes.collector import Collector
from .nodes.curator import Curator
from .nodes.enricher import Enricher
from .nodes.insight_synthesizer import InsightSynthesizer
from .nodes.researchers import (
    UnifiedResearcher,
    SpecializedResearcher,
)
from .nodes.interest_inference_agent import InterestInferenceAgent
from .nodes.research_intent_planner import ResearchIntentPlanner
from .nodes.query_composer import QueryComposer
from .nodes.user_profile_enrichment_agent import UserProfileEnrichmentAgent
from .nodes.profile_enrichment_orchestrator import ProfileEnrichmentOrchestrator
from .nodes.executive_report_composer import ExecutiveReportComposer

# Import the new enhanced pre-research agents
from .nodes.company_research_agent import CompanyResearchAgent
from .nodes.industry_research_agent import IndustryResearchAgent
from .nodes.competitors_research_agent import CompetitorsResearchAgent
from .nodes.enhanced_data_integrator import EnhancedDataIntegrator

logger = logging.getLogger(__name__)

class EnhancedGraph:
    """
    Enhanced Graph that integrates the three-agent pre-research workflow
    with the existing company research system.
    
    New Flow:
    [Company Research Agent] → [Industry Research Agent] → [Competitors Research Agent] 
    → [Collector Node] → [Existing Workflow]
    """
    
    def __init__(self, company=None, url=None, user_role=None,
                 websocket_manager=None, job_id=None, include_specialized_research=False,
                 enable_enhanced_pre_research=True, use_enhanced_profile_enrichment=True):
        self.websocket_manager = websocket_manager
        self.job_id = job_id
        self.include_specialized_research = include_specialized_research
        self.enable_enhanced_pre_research = enable_enhanced_pre_research
        self.use_enhanced_profile_enrichment = use_enhanced_profile_enrichment
        
        # Initialize ResearchState with enhanced default values
        from .classes.state import default_research_state
        self.input_state = {
            **default_research_state,
            'company': company,
            'company_url': url,
            'user_role': user_role,
            'websocket_manager': websocket_manager,
            'job_id': job_id,
            'messages': [
                SystemMessage(content="🚀 Enhanced researcher starting investigation with three-agent pre-research workflow and comprehensive competitive intelligence")
            ]
        }

        # Initialize all nodes including the new enhanced agents
        self._init_enhanced_nodes()
        self._build_enhanced_workflow()

    def _init_enhanced_nodes(self):
        """Initialize all workflow nodes including the new enhanced pre-research agents"""
        
        # Enhanced Pre-Research Agents
        if self.enable_enhanced_pre_research:
            self.company_research_agent = CompanyResearchAgent()
            self.industry_research_agent = IndustryResearchAgent()
            self.competitors_research_agent = CompetitorsResearchAgent()
            self.enhanced_data_integrator = EnhancedDataIntegrator()
        
        # Existing workflow nodes
        self.unified_researcher = UnifiedResearcher()
        self.collector = Collector()
        self.curator = Curator()
        self.enricher = Enricher()
        self.insight_synthesizer = InsightSynthesizer()
        
        # Choose between enhanced modular profile enrichment or legacy agent
        if self.use_enhanced_profile_enrichment:
            self.profile_enrichment_agent = ProfileEnrichmentOrchestrator()
        else:
            self.profile_enrichment_agent = UserProfileEnrichmentAgent()
            
        self.interest_inference_agent = InterestInferenceAgent()
        self.research_intent_planner = ResearchIntentPlanner()
        self.query_composer = QueryComposer()
        self.executive_report_composer = ExecutiveReportComposer()
        
        # Optional specialized researcher
        if self.include_specialized_research:
            self.specialized_researcher = SpecializedResearcher()

    def _build_enhanced_workflow(self):
        """Configure the enhanced state graph workflow with pre-research agents"""
        self.workflow = StateGraph(ResearchState)
        
        if self.enable_enhanced_pre_research:
            # Add the three new pre-research agents
            self.workflow.add_node("company_research_agent", self.company_research_agent.run)
            self.workflow.add_node("industry_research_agent", self.industry_research_agent.run)
            self.workflow.add_node("competitors_research_agent", self.competitors_research_agent.run)
            
            # Add the data integrator node
            self.workflow.add_node("enhanced_data_integrator", self.enhanced_data_integrator.run)
            
            # Set entry point to the enhanced pre-research flow
            self.workflow.set_entry_point("company_research_agent")
            
            # Connect the three pre-research agents in sequence
            self.workflow.add_edge("company_research_agent", "industry_research_agent")
            self.workflow.add_edge("industry_research_agent", "competitors_research_agent")
            
            # Connect competitors research to data integrator, then to profile enrichment
            self.workflow.add_edge("competitors_research_agent", "enhanced_data_integrator")
            self.workflow.add_edge("enhanced_data_integrator", "user_profile_enrichment")
        else:
            # Use original entry point if enhanced pre-research is disabled
            self.workflow.set_entry_point("user_profile_enrichment")
        
        # Add existing workflow nodes
        self.workflow.add_node("user_profile_enrichment", self.profile_enrichment_agent.run)
        self.workflow.add_node("interest_inference", self.interest_inference_agent.run)
        self.workflow.add_node("research_intent_planning", self.research_intent_planner.run)
        self.workflow.add_node("query_composition", self.query_composer.run)
        self.workflow.add_node("collector", self.collector.run)
        self.workflow.add_node("unified_researcher", self.unified_researcher.run)
        
        # Optional specialized researcher node
        if self.include_specialized_research:
            self.workflow.add_node("specialized_researcher", self.specialized_researcher.run)
        
        self.workflow.add_node("curator", self.curator.run)
        self.workflow.add_node("enricher", self.enricher.run)
        self.workflow.add_node("insight_synthesizer", self.insight_synthesizer.run)
        self.workflow.add_node("executive_report_composer", self.executive_report_composer.run)
        
        # Configure existing workflow edges
        self.workflow.set_finish_point("executive_report_composer")
        
        if self.enable_enhanced_pre_research:
            # For enhanced workflow, skip query generation and go directly to curation
            # since we already have the data from enhanced pre-research
            self.workflow.add_edge("user_profile_enrichment", "curator")
        else:
            # Standard workflow with query generation and research
            # Connect profile enrichment to interest inference
            self.workflow.add_edge("user_profile_enrichment", "interest_inference")
            
            # Connect interest inference to research intent planning
            self.workflow.add_edge("interest_inference", "research_intent_planning")
            
            # Connect research intent planning to query composition
            self.workflow.add_edge("research_intent_planning", "query_composition")
            
            # Connect query composition to collector
            self.workflow.add_edge("query_composition", "collector")

            # Connect collector to unified researcher
            self.workflow.add_edge("collector", "unified_researcher")
            
            # Optional specialized researcher connection
            if self.include_specialized_research:
                self.workflow.add_edge("unified_researcher", "specialized_researcher")
                self.workflow.add_edge("specialized_researcher", "curator")
            else:
                # Connect unified researcher directly to curator
                self.workflow.add_edge("unified_researcher", "curator")

        # Connect remaining nodes
        self.workflow.add_edge("curator", "enricher")
        self.workflow.add_edge("enricher", "insight_synthesizer")
        self.workflow.add_edge("insight_synthesizer", "executive_report_composer")

    async def run(self, thread: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """Execute the enhanced research workflow"""
        compiled_graph = self.workflow.compile()
        
        # Send initial status update about enhanced workflow
        if self.websocket_manager and self.job_id:
            await self.websocket_manager.send_status_update(
                job_id=self.job_id,
                status="started",
                message="🚀 Starting enhanced three-agent pre-research workflow",
                result={
                    "workflow_type": "enhanced",
                    "pre_research_enabled": self.enable_enhanced_pre_research,
                    "specialized_research_enabled": self.include_specialized_research,
                    "total_agents": 3 if self.enable_enhanced_pre_research else 0,
                    "company": self.input_state.get('company', 'Unknown'),
                    "phases": [
                        "Company Intelligence Gathering",
                        "Industry Analysis", 
                        "Competitive Intelligence",
                        "Research Planning",
                        "Data Collection",
                        "Analysis & Synthesis",
                        "Executive Report Generation"
                    ] if self.enable_enhanced_pre_research else [
                        "Research Planning",
                        "Data Collection", 
                        "Analysis & Synthesis",
                        "Executive Report Generation"
                    ]
                }
            )
        
        async for state in compiled_graph.astream(
            self.input_state,
            thread
        ):
            # Yield state after CompanyResearchAgent
            if state.get("company_factual_data") and not state.get("industry_intelligence"):
                yield state

            # Yield state after IndustryResearchAgent
            elif state.get("industry_intelligence") and not state.get("enhanced_competitor_data"):
                yield state

            # Yield state after CompetitorsResearchAgent
            elif state.get("enhanced_competitor_data") and not state.get("profile"):
                yield state

            # Handle WebSocket updates
            if self.websocket_manager and self.job_id:
                await self._handle_enhanced_ws_update(state)

            # Yield final state
            yield state

    async def _handle_enhanced_ws_update(self, state: Dict[str, Any]):
        """Handle WebSocket updates with enhanced state information"""
        # Determine current phase based on state
        current_phase = self._determine_current_phase(state)
        
        # Calculate enhanced progress
        progress = self._calculate_enhanced_progress(state)
        
        # Extract enhanced metrics
        enhanced_metrics = self._extract_enhanced_metrics(state)
        
        update = {
            "type": "enhanced_state_update",
            "data": {
                "current_phase": current_phase,
                "progress": progress,
                "enhanced_metrics": enhanced_metrics,
                "pre_research_complete": state.get("pre_research_complete", False),
                "company_intelligence": bool(state.get("company_factual_data", {}).get("intelligence_summary")),
                "industry_intelligence": bool(state.get("industry_intelligence", {}).get("intelligence_summary")),
                "competitor_intelligence": bool(state.get("enhanced_competitor_data", {}).get("intelligence_summary")),
                "keys": list(state.keys())
            }
        }
        
        await self.websocket_manager.broadcast_to_job(
            self.job_id,
            update
        )

    def _determine_current_phase(self, state: Dict[str, Any]) -> str:
        """Determine the current phase of the enhanced workflow"""
        if not self.enable_enhanced_pre_research:
            return self._determine_standard_phase(state)
        
        # Enhanced workflow phases
        if state.get("company_factual_data") and not state.get("industry_intelligence"):
            return "Company Intelligence Gathering"
        elif state.get("industry_intelligence") and not state.get("enhanced_competitor_data"):
            return "Industry Analysis"
        elif state.get("enhanced_competitor_data") and not state.get("profile"):
            return "Competitive Intelligence"
        elif state.get("profile") and not state.get("research_plan"):
            return "Research Planning"
        elif state.get("categorized_queries") and not state.get("curated_company_data"):
            return "Data Collection"
        elif state.get("strategic_insights") and not state.get("report"):
            return "Analysis & Synthesis"
        elif state.get("report"):
            return "Executive Report Generation"
        else:
            return "Initialization"

    def _determine_standard_phase(self, state: Dict[str, Any]) -> str:
        """Determine phase for standard workflow"""
        if state.get("profile") and not state.get("research_plan"):
            return "Research Planning"
        elif state.get("categorized_queries") and not state.get("curated_company_data"):
            return "Data Collection"
        elif state.get("strategic_insights") and not state.get("report"):
            return "Analysis & Synthesis"
        elif state.get("report"):
            return "Executive Report Generation"
        else:
            return "Initialization"

    def _calculate_enhanced_progress(self, state: Dict[str, Any]) -> int:
        """Calculate progress percentage for enhanced workflow"""
        if not self.enable_enhanced_pre_research:
            return self._calculate_standard_progress(state)
        
        # Enhanced workflow progress calculation
        total_phases = 7
        completed_phases = 0
        
        # Pre-research phases (40% of total progress)
        if state.get("company_factual_data", {}).get("intelligence_summary"):
            completed_phases += 1
        if state.get("industry_intelligence", {}).get("intelligence_summary"):
            completed_phases += 1  
        if state.get("enhanced_competitor_data", {}).get("intelligence_summary"):
            completed_phases += 1
        
        # Standard workflow phases (60% of total progress)
        if state.get("research_plan"):
            completed_phases += 1
        if state.get("curated_company_data"):
            completed_phases += 1
        if state.get("strategic_insights"):
            completed_phases += 1
        if state.get("report"):
            completed_phases += 1
        
        return int((completed_phases / total_phases) * 100)

    def _calculate_standard_progress(self, state: Dict[str, Any]) -> int:
        """Calculate progress for standard workflow"""
        total_phases = 4
        completed_phases = 0
        
        if state.get("research_plan"):
            completed_phases += 1
        if state.get("curated_company_data"):
            completed_phases += 1
        if state.get("strategic_insights"):
            completed_phases += 1
        if state.get("report"):
            completed_phases += 1
        
        return int((completed_phases / total_phases) * 100)

    def _extract_enhanced_metrics(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract enhanced metrics from state"""
        metrics = {
            "pre_research_metrics": {},
            "workflow_metrics": {},
            "data_quality": {}
        }
        
        if self.enable_enhanced_pre_research:
            # Company research metrics
            company_data = state.get("company_factual_data", {})
            if company_data:
                metrics["pre_research_metrics"]["company_sources"] = len(
                    company_data.get("intelligence_summary", {}).get("data_sources", [])
                )
                metrics["pre_research_metrics"]["company_reliability"] = company_data.get("reliability_score", 0.0)
            
            # Industry research metrics
            industry_data = state.get("industry_intelligence", {})
            if industry_data:
                metrics["pre_research_metrics"]["industry_sources"] = len(
                    industry_data.get("intelligence_summary", {}).get("data_sources", [])
                )
            
            # Competitor research metrics
            competitor_data = state.get("enhanced_competitor_data", {})
            if competitor_data:
                metrics["pre_research_metrics"]["competitors_analyzed"] = competitor_data.get("total_competitors", 0)
                metrics["pre_research_metrics"]["competitor_profiles"] = len(
                    competitor_data.get("comprehensive_profiles", {})
                )
        
        # Standard workflow metrics
        metrics["workflow_metrics"]["total_queries"] = state.get("total_queries", 0)
        metrics["workflow_metrics"]["financial_docs"] = len(state.get("financial_data", {}))
        metrics["workflow_metrics"]["news_docs"] = len(state.get("news_data", {}))
        metrics["workflow_metrics"]["company_docs"] = len(state.get("company_data", {}))
        
        # Data quality metrics
        all_docs = (
            len(state.get("financial_data", {})) +
            len(state.get("news_data", {})) +
            len(state.get("company_data", {})) +
            len(state.get("competitor_data", {}))
        )
        metrics["data_quality"]["total_documents"] = all_docs
        metrics["data_quality"]["has_insights"] = bool(state.get("strategic_insights"))
        
        return metrics
    
    def compile(self):
        """Compile the enhanced workflow graph"""
        graph = self.workflow.compile()
        return graph

    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get a summary of the configured workflow"""
        return {
            "workflow_type": "enhanced" if self.enable_enhanced_pre_research else "standard",
            "pre_research_agents": 3 if self.enable_enhanced_pre_research else 0,
            "specialized_research": self.include_specialized_research,
            "total_nodes": len(self.workflow.nodes) if hasattr(self.workflow, 'nodes') else 0,
            "agents": {
                "company_research_agent": self.enable_enhanced_pre_research,
                "industry_research_agent": self.enable_enhanced_pre_research,
                "competitors_research_agent": self.enable_enhanced_pre_research,
                "unified_researcher": True,
                "specialized_researcher": self.include_specialized_research,
                "executive_report_composer": True
            },
            "capabilities": {
                "factual_company_data": self.enable_enhanced_pre_research,
                "industry_intelligence": self.enable_enhanced_pre_research,
                "enhanced_competitor_analysis": self.enable_enhanced_pre_research,
                "multi_source_verification": self.enable_enhanced_pre_research,
                "real_time_intelligence": self.enable_enhanced_pre_research,
                "technology_stack_analysis": self.enable_enhanced_pre_research,
                "strategic_movement_tracking": self.enable_enhanced_pre_research,
                "partnership_mapping": self.enable_enhanced_pre_research
            }
        }


# Backward compatibility: Keep the original Graph class available
class Graph(EnhancedGraph):
    """
    Original Graph class that now inherits from EnhancedGraph for backward compatibility.
    By default, it runs the standard workflow without enhanced pre-research.
    """
    
    def __init__(self, company=None, url=None, user_role=None,
                 websocket_manager=None, job_id=None, include_specialized_research=False,
                 use_enhanced_profile_enrichment=True):
        # Call parent with enhanced pre-research disabled by default for backward compatibility
        super().__init__(
            company=company,
            url=url,
            user_role=user_role,
            websocket_manager=websocket_manager,
            job_id=job_id,
            include_specialized_research=include_specialized_research,
            enable_enhanced_pre_research=False,  # Disabled by default for backward compatibility
            use_enhanced_profile_enrichment=use_enhanced_profile_enrichment
        )


# Factory function for easy enhanced workflow creation
def create_enhanced_workflow(company=None, url=None, user_role=None,
                           websocket_manager=None, job_id=None, 
                           include_specialized_research=False,
                           enable_enhanced_pre_research=True,
                           use_enhanced_profile_enrichment=True) -> EnhancedGraph:
    """
    Factory function to create an enhanced workflow with the three-agent pre-research system.
    
    Args:
        company: Company name to research
        url: Company website URL
        user_role: User's role for context
        websocket_manager: WebSocket manager for real-time updates
        job_id: Job ID for tracking
        include_specialized_research: Whether to include specialized research
        enable_enhanced_pre_research: Whether to enable the three-agent pre-research workflow
        use_enhanced_profile_enrichment: Whether to use the new modular profile enrichment system
    
    Returns:
        EnhancedGraph: Configured enhanced workflow instance
    """
    return EnhancedGraph(
        company=company,
        url=url,
        user_role=user_role,
        websocket_manager=websocket_manager,
        job_id=job_id,
        include_specialized_research=include_specialized_research,
        enable_enhanced_pre_research=enable_enhanced_pre_research,
        use_enhanced_profile_enrichment=use_enhanced_profile_enrichment
    ) 