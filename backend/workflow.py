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
from .nodes.executive_report_composer import ExecutiveReportComposer
from .nodes.competitor_discovery_agent import EnhancedCompetitorDiscoveryAgent
from .nodes.competitor_analyst_agent import CompetitorAnalystAgent
from .nodes.sector_trend_agent import SectorTrendAgent
from .nodes.client_trend_agent import ClientTrendAgent
from .nodes.comprehensive_report_generator import ComprehensiveReportGenerator

logger = logging.getLogger(__name__)

# Global storage for jobs waiting for competitor review
pending_competitor_reviews = {}

class Graph:
    def __init__(self, company=None, url=None, user_role=None,
                 websocket_manager=None, job_id=None, include_specialized_research=False,
                 use_enhanced_profile_enrichment=True):
        self.websocket_manager = websocket_manager
        self.job_id = job_id
        self.include_specialized_research = include_specialized_research
        self.use_enhanced_profile_enrichment = use_enhanced_profile_enrichment
        
        # Initialize ResearchState with default values from the state definition
        from .classes.state import default_research_state
        self.input_state = {
            **default_research_state,
            'company': company,
            'company_url': url,
            'user_role': user_role,
            'websocket_manager': websocket_manager,
            'job_id': job_id,
            'messages': [
                SystemMessage(content="Expert researcher starting investigation with profile enrichment, competitor discovery, competitor news analysis, and sector trend analysis")
            ]
        }

        self._init_nodes()
        self.workflow = None  # Will be built in run()

    def _init_nodes(self):
        """Initialize all workflow nodes"""
        # self.ground = GroundingNode()
        self.unified_researcher = UnifiedResearcher()
        self.collector = Collector()
        self.curator = Curator()
        self.enricher = Enricher()
        self.insight_synthesizer = InsightSynthesizer()
        
        # Add competitor discovery agent, competitor analyst agent, and trend agents
        self.competitor_discovery_agent = EnhancedCompetitorDiscoveryAgent()
        self.competitor_analyst_agent = CompetitorAnalystAgent()
        self.sector_trend_agent = SectorTrendAgent()
        self.client_trend_agent = ClientTrendAgent()
        
        # Add comprehensive report generator
        self.comprehensive_report_generator = ComprehensiveReportGenerator()
        
        self.profile_enrichment_agent = UserProfileEnrichmentAgent()
            
        self.interest_inference_agent = InterestInferenceAgent()
        self.research_intent_planner = ResearchIntentPlanner()
        self.query_composer = QueryComposer()
        self.executive_report_composer = ExecutiveReportComposer()
        
        # Optional specialized researcher
        if self.include_specialized_research:
            self.specialized_researcher = SpecializedResearcher()

    def _should_review_competitors(self, state: Dict[str, Any]) -> str:
        """Conditional function to determine if competitors need user review"""
        # Check if competitors were discovered
        competitors = state.get("competitors", [])
        
        # Always require review if competitors were found
        if competitors:
            job_id = state.get("job_id")
            if job_id:
                # Store the current state for resumption later
                pending_competitor_reviews[job_id] = state
                logger.info(f"Storing state for competitor review in job {job_id}")
            return "competitor_review_wait"
        else:
            # No competitors found, complete discovery workflow
            logger.info("No competitors found, completing discovery workflow")
            return "discovery_complete"

    async def _discovery_complete(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node that handles completion when no competitors are found"""
        websocket_manager = state.get("websocket_manager")
        job_id = state.get("job_id")
        
        logger.info(f"Discovery completed for job {job_id} with no competitors found")
        
        if websocket_manager and job_id:
            await websocket_manager.send_status_update(
                job_id=job_id,
                status="discovery_complete_no_competitors",
                message="Discovery completed - no competitors found to analyze",
                result={
                    "step": "Discovery Complete",
                    "competitors": [],
                    "message": "No competitors found for analysis"
                }
            )
        
        state["discovery_complete"] = True
        state["competitor_review_pending"] = False
        
        return state

    async def _competitor_review_wait(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node that waits for user to review and modify competitors"""
        websocket_manager = state.get("websocket_manager")
        job_id = state.get("job_id")
        competitors = state.get("competitors", [])
        
        # Convert competitor names to full competitor objects for the frontend
        competitor_objects = []
        for competitor in competitors:
            if isinstance(competitor, str):
                competitor_objects.append({
                    "name": competitor,
                    "category": "discovered",
                    "confidence": 0.8,
                    "description": f"Discovered competitor: {competitor}",
                    "evidence": "Automated discovery"
                })
            else:
                competitor_objects.append(competitor)
        
        logger.info(f"Waiting for competitor review for job {job_id} with {len(competitor_objects)} competitors")
        
        # Send status to trigger frontend competitor review
        if websocket_manager and job_id:
            await websocket_manager.send_status_update(
                job_id=job_id,
                status="competitor_review_required",
                message=f"Please review the {len(competitor_objects)} discovered competitors",
                result={
                    "step": "Competitor Review",
                    "competitors": competitor_objects,
                    "message": "Review and modify the competitor list before continuing analysis"
                }
            )
        
        # Mark state as waiting for review
        state["competitor_review_pending"] = True
        state["competitor_review_step"] = "waiting_for_user"
        
        return state

    def _build_discovery_workflow(self):
        """Configure the discovery phase workflow (Phase 1) - stops after competitor discovery"""
        self.workflow = StateGraph(ResearchState)
        
        # Add nodes for discovery phase only
        self.workflow.add_node("user_profile_enrichment", self.profile_enrichment_agent.run)
        self.workflow.add_node("competitor_discovery_node", self.competitor_discovery_agent.run)
        self.workflow.add_node("competitor_review_wait", self._competitor_review_wait)
        self.workflow.add_node("discovery_complete", self._discovery_complete)
        
        # Configure workflow edges for discovery phase
        self.workflow.set_entry_point("user_profile_enrichment")
        
        # Connect profile enrichment to competitor discovery
        self.workflow.add_edge("user_profile_enrichment", "competitor_discovery_node")
        
        # Add conditional edge from competitor discovery
        self.workflow.add_conditional_edges(
            "competitor_discovery_node",
            self._should_review_competitors,
            {
                "competitor_review_wait": "competitor_review_wait",
                "discovery_complete": "discovery_complete"  # If no competitors, complete discovery
            }
        )
        
        # IMPORTANT: Both competitor_review_wait and discovery_complete end the workflow
        # This ensures the workflow stops and waits for user input or completes if no competitors
        self.workflow.set_finish_point("competitor_review_wait")
        self.workflow.set_finish_point("discovery_complete")

    def _build_analysis_workflow(self):
        """Configure the analysis phase workflow (Phase 2) - runs after user review"""
        self.workflow = StateGraph(ResearchState)
        
        # Add nodes for analysis phase
        self.workflow.add_node("competitor_analysis_node", self.competitor_analyst_agent.run)
        self.workflow.add_node("sector_trend_analysis", self.sector_trend_agent.run)
        self.workflow.add_node("client_trend_analysis", self.client_trend_agent.run)
        self.workflow.add_node("comprehensive_report_generator", self.comprehensive_report_generator.run)
        
        # Configure workflow edges for analysis phase
        self.workflow.set_entry_point("competitor_analysis_node")
        self.workflow.set_finish_point("comprehensive_report_generator")
        
        # Connect analysis nodes in sequence
        self.workflow.add_edge("competitor_analysis_node", "sector_trend_analysis")
        self.workflow.add_edge("sector_trend_analysis", "client_trend_analysis")
        self.workflow.add_edge("client_trend_analysis", "comprehensive_report_generator")

    async def run(self, thread: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """Execute the discovery phase workflow (Phase 1) - stops after competitor discovery"""
        try:
            # Build discovery workflow only
            self._build_discovery_workflow()
            
            if not self.workflow:
                raise ValueError("Discovery workflow not properly initialized")

            compiled_graph = self.workflow.compile()
            
            # Run the discovery workflow - will stop at competitor review or end
            async for state in compiled_graph.astream(
                self.input_state,
                thread
            ):
                if self.websocket_manager and self.job_id:
                    await self._handle_ws_update(state)
                
                yield state
        except Exception as e:
            logger.error(f"Error in discovery workflow: {e}")
            raise

    async def run_analysis_phase(self, state: Dict[str, Any], thread: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """Execute the analysis phase workflow (Phase 2) - runs after user review"""
        try:
            # Build analysis workflow
            self._build_analysis_workflow()
            
            if not self.workflow:
                raise ValueError("Analysis workflow not properly initialized")

            compiled_graph = self.workflow.compile()
            
            # Run the analysis workflow starting from competitor analysis
            async for updated_state in compiled_graph.astream(
                state,
                thread
            ):
                if self.websocket_manager and self.job_id:
                    await self._handle_ws_update(updated_state)
                
                yield updated_state
        except Exception as e:
            logger.error(f"Error in analysis workflow: {e}")
            raise

    async def _handle_ws_update(self, state: Dict[str, Any]):
        """Handle WebSocket updates based on state changes"""
        update = {
            "type": "state_update",
            "data": {
                "current_node": state.get("current_node", "unknown"),
                "progress": state.get("progress", 0),
                "keys": list(state.keys())
            }
        }
        await self.websocket_manager.broadcast_to_job(
            self.job_id,
            update
        )
    
    def compile(self):
        """Compile the discovery workflow for backward compatibility"""
        self._build_discovery_workflow()
        graph = self.workflow.compile()
        return graph