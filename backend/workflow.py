import logging
from typing import Any, AsyncIterator, Dict
import asyncio

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

# Global storage for jobs waiting for competitor review (legacy)
pending_competitor_reviews = {}

# NEW: Event registry & modifications buffer for async competitor review handling
competitor_review_events: Dict[str, asyncio.Event] = {}
competitor_modifications_pending: Dict[str, list] = {}

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
        """Decide whether we need a competitor review pause"""
        competitors = state.get("competitors", [])

        if competitors:
            job_id = state.get("job_id")
            if job_id:
                # Keep a snapshot for debug purposes
                pending_competitor_reviews[job_id] = state
                logger.info(
                    f"Competitors discovered – user review required (job {job_id})"
                )
            return "competitor_review_wait"

        # If no competitors, proceed directly to analysis (skipping review)
        logger.info("No competitors discovered – skipping competitor review")
        return "competitor_analysis_node"

    async def _competitor_review_wait(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Pause the workflow and wait for the user to review competitors."""

        websocket_manager = state.get("websocket_manager")
        job_id = state.get("job_id")
        competitors = state.get("competitors", [])

        # Format competitors for the frontend dialog
        competitor_objects = []
        for comp in competitors:
            if isinstance(comp, str):
                competitor_objects.append(
                    {
                        "name": comp,
                        "category": "discovered",
                        "confidence": 0.8,
                        "description": f"Discovered competitor: {comp}",
                        "evidence": "Automated discovery",
                    }
                )
            else:
                competitor_objects.append(comp)

        # Notify frontend that a review is required
        if websocket_manager and job_id:
            await websocket_manager.send_status_update(
                job_id=job_id,
                status="competitor_review_required",
                message=f"Please review the {len(competitor_objects)} discovered competitors",
                result={
                    "step": "Competitor Review",
                    "competitors": competitor_objects,
                    "message": "Review and modify the competitor list before continuing analysis",
                },
            )

        # Prepare an asyncio.Event for this job (creates if missing)
        review_event = competitor_review_events.setdefault(job_id, asyncio.Event())

        # Flag state so the outer loop / endpoints know we're waiting
        state["competitor_review_pending"] = True

        logger.info(
            f"Workflow paused – awaiting competitor review (job {job_id})"
        )

        # --- Wait until the user presses "Continue Research" ---
        await review_event.wait()

        # Retrieve the modified competitor list (if any)
        modified = competitor_modifications_pending.pop(job_id, None)
        if modified is not None:
            competitor_names = [
                m.get("name") if isinstance(m, dict) else str(m) for m in modified
            ]
            state["competitors"] = competitor_names
            logger.info(
                f"Received {len(competitor_names)} modified competitors – resuming workflow (job {job_id})"
            )

        # Clear flags & event (prepare for GC)
        state["competitor_review_pending"] = False
        review_event.clear()
        competitor_review_events.pop(job_id, None)

        # Continue to next node
        return state

    def _build_full_workflow(self):
        """Build the full end-to-end workflow with a single finish point."""

        self.workflow = StateGraph(ResearchState)

        # --- Node registration ---
        self.workflow.add_node("user_profile_enrichment", self.profile_enrichment_agent.run)
        self.workflow.add_node("competitor_discovery_node", self.competitor_discovery_agent.run)
        self.workflow.add_node("competitor_review_wait", self._competitor_review_wait)
        self.workflow.add_node("competitor_analysis_node", self.competitor_analyst_agent.run)
        self.workflow.add_node("sector_trend_analysis", self.sector_trend_agent.run)
        self.workflow.add_node("client_trend_analysis", self.client_trend_agent.run)
        self.workflow.add_node("comprehensive_report_generator", self.comprehensive_report_generator.run)

        # --- Flow edges ---
        self.workflow.set_entry_point("user_profile_enrichment")
        self.workflow.add_edge("user_profile_enrichment", "competitor_discovery_node")

        # Conditional path: review required or skip directly to analysis
        self.workflow.add_conditional_edges(
            "competitor_discovery_node",
            self._should_review_competitors,
            {
                "competitor_review_wait": "competitor_review_wait",
                "competitor_analysis_node": "competitor_analysis_node",
            },
        )

        # From review, always continue to competitor analysis
        self.workflow.add_edge("competitor_review_wait", "competitor_analysis_node")

        # Main analysis chain
        self.workflow.add_edge("competitor_analysis_node", "sector_trend_analysis")
        self.workflow.add_edge("sector_trend_analysis", "client_trend_analysis")
        self.workflow.add_edge("client_trend_analysis", "comprehensive_report_generator")

        # Single finish point
        self.workflow.set_finish_point("comprehensive_report_generator")

    async def run(self, thread: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """Execute the discovery phase workflow (Phase 1) - stops after competitor discovery"""
        try:
            # Build unified workflow
            self._build_full_workflow()
            
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
            self._build_full_workflow()
            
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
        """Compile the unified workflow (backwards compatibility stub)."""
        self._build_full_workflow()
        return self.workflow.compile()