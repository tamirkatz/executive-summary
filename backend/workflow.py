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

logger = logging.getLogger(__name__)

class Graph:
    def __init__(self, company=None, url=None, user_role=None,
                 websocket_manager=None, job_id=None, include_specialized_research=False):
        self.websocket_manager = websocket_manager
        self.job_id = job_id
        self.include_specialized_research = include_specialized_research
        
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
                SystemMessage(content="Expert researcher starting investigation")
            ]
        }

        # Initialize nodes with WebSocket manager and job ID
        self._init_nodes()
        self._build_workflow()

    def _init_nodes(self):
        """Initialize all workflow nodes"""
        # self.ground = GroundingNode()
        self.unified_researcher = UnifiedResearcher()
        self.collector = Collector()
        self.curator = Curator()
        self.enricher = Enricher()
        self.insight_synthesizer = InsightSynthesizer()
        self.user_profile_enrichment_agent = UserProfileEnrichmentAgent()
        self.interest_inference_agent = InterestInferenceAgent()
        self.research_intent_planner = ResearchIntentPlanner()
        self.query_composer = QueryComposer()
        self.executive_report_composer = ExecutiveReportComposer()
        
        
        # Optional specialized researcher
        if self.include_specialized_research:
            self.specialized_researcher = SpecializedResearcher()

    def _build_workflow(self):
        """Configure the state graph workflow"""
        self.workflow = StateGraph(ResearchState)
        
        # Add nodes with their respective processing functions
        # self.workflow.add_node("grounding", self.ground.run)
        self.workflow.add_node("user_profile_enrichment", self.user_profile_enrichment_agent.run)
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
        # Configure workflow edges
        self.workflow.set_entry_point("user_profile_enrichment")
        self.workflow.set_finish_point("executive_report_composer")
        
        # Connect profile enrichment to interest inference
        self.workflow.add_edge("user_profile_enrichment", "interest_inference")
        
        # Connect interest inference to research intent planning
        self.workflow.add_edge("interest_inference", "research_intent_planning")
        
        # Connect research intent planning to query composition
        self.workflow.add_edge("research_intent_planning", "query_composition")
        
        # Connect query composition to collector (collect queries)
        self.workflow.add_edge("query_composition", "collector")

        # Connect collector to unified researcher (provide categorized queries)
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
        """Execute the research workflow"""
        compiled_graph = self.workflow.compile()
        
        async for state in compiled_graph.astream(
            self.input_state,
            thread
        ):
            if self.websocket_manager and self.job_id:
                await self._handle_ws_update(state)
            yield state

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