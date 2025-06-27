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

    def _build_workflow(self):
        """Configure the state graph workflow"""
        # Use InputState for the first node (competitor_discovery) since it can handle the conversion
        # All subsequent nodes will work with ResearchState
        self.workflow = StateGraph(ResearchState)
        
        # Add nodes with their respective processing functions
        # self.workflow.add_node("grounding", self.ground.run)
        self.workflow.add_node("user_profile_enrichment", self.profile_enrichment_agent.run)
        self.workflow.add_node("competitor_discovery_node", self.competitor_discovery_agent.run)
        self.workflow.add_node("competitor_analysis_node", self.competitor_analyst_agent.run)
        
        # Add trend analysis nodes
        self.workflow.add_node("sector_trend_analysis", self.sector_trend_agent.run)
        self.workflow.add_node("client_trend_analysis", self.client_trend_agent.run)
        
        # Add comprehensive report generator
        self.workflow.add_node("comprehensive_report_generator", self.comprehensive_report_generator.run)
        
        # Configure workflow edges
        self.workflow.set_entry_point("user_profile_enrichment")
        self.workflow.set_finish_point("comprehensive_report_generator")
        
        # Connect profile enrichment to competitor discovery
        self.workflow.add_edge("user_profile_enrichment", "competitor_discovery_node")
        
        # Connect competitor discovery to competitor analysis, then to trend analysis
        self.workflow.add_edge("competitor_discovery_node", "competitor_analysis_node")
        self.workflow.add_edge("competitor_analysis_node", "sector_trend_analysis")
        self.workflow.add_edge("sector_trend_analysis", "client_trend_analysis")
        
        # Connect client trend analysis directly to comprehensive report generator
        self.workflow.add_edge("client_trend_analysis", "comprehensive_report_generator")

    async def run(self, thread: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """Execute the research workflow"""
        try:
            # Build workflow with all agents
            self._build_workflow()
            
            if not self.workflow:
                raise ValueError("Workflow not properly initialized")

            compiled_graph = self.workflow.compile()
            
            # Run the complete workflow
            async for state in compiled_graph.astream(
                self.input_state,
                thread
            ):
                if self.websocket_manager and self.job_id:
                    await self._handle_ws_update(state)
                
                yield state
        except Exception as e:
            logger.error(f"Error in run method: {e}")
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
        graph = self.workflow.compile()
        return graph