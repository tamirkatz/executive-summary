import logging
from typing import Dict, Any
from ..classes import InputState, ResearchState
from ..agents.base_agent import BaseAgent
from .company_info_agent import CompanyInfoAgent
from .competitor_discovery_agent import CompetitorDiscoveryAgent
from .competitor_evaluator_agent import CompetitorEvaluatorAgent

logger = logging.getLogger(__name__)


class ProfileEnrichmentOrchestrator(BaseAgent):
    """Orchestrates the profile enrichment process using specialized agents."""
    
    def __init__(self):
        super().__init__(agent_type="profile_enrichment_orchestrator")
        self.company_info_agent = CompanyInfoAgent()
        self.competitor_discovery_agent = CompetitorDiscoveryAgent()
        self.competitor_evaluator_agent = CompetitorEvaluatorAgent()
        self.max_competitor_iterations = 3

    async def run(self, state: InputState) -> ResearchState:
        """Main orchestration method that coordinates all profile enrichment steps."""
        websocket_manager, job_id = self.get_websocket_info(state)
        
        self.log_agent_start(state)
        
        await self.send_status_update(
            websocket_manager, job_id,
            status="processing",
            message="Starting comprehensive profile enrichment",
            result={"step": "Profile Enrichment", "substep": "orchestration_start"}
        )

        # Step 1: Extract basic company information
        self.logger.info("Step 1: Extracting company information")
        research_state = await self.company_info_agent.run(state)
        
        # Step 2: Discover competitors with evaluation loop
        self.logger.info("Step 2: Starting competitor discovery with evaluation")
        
        competitor_iteration = 0
        competitor_quality_passed = False
        
        while competitor_iteration < self.max_competitor_iterations and not competitor_quality_passed:
            competitor_iteration += 1
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"Competitor discovery attempt {competitor_iteration}/{self.max_competitor_iterations}",
                result={"step": "Profile Enrichment", "substep": f"competitor_attempt_{competitor_iteration}"}
            )
            
            # Run competitor discovery
            research_state = await self.competitor_discovery_agent.run(research_state)
            
            # Evaluate the results
            research_state = await self.competitor_evaluator_agent.run(research_state)
            
            # Check if evaluation passed
            evaluation = research_state.get('competitor_evaluation', {})
            competitor_quality_passed = evaluation.get('pass_threshold', False)
            
            if competitor_quality_passed:
                self.logger.info(f"Competitor discovery succeeded on iteration {competitor_iteration}")
                break
            else:
                self.logger.warning(f"Competitor discovery iteration {competitor_iteration} did not meet quality threshold")
                
                # If we haven't reached max iterations, refine the approach
                if competitor_iteration < self.max_competitor_iterations:
                    await self.send_status_update(
                        websocket_manager, job_id,
                        status="processing",
                        message=f"Refining competitor search for iteration {competitor_iteration + 1}",
                        result={"step": "Profile Enrichment", "substep": "competitor_refinement"}
                    )
                    
                    # Clear previous candidate pool for fresh search
                    self.competitor_discovery_agent.candidate_pool = []
                    self.competitor_discovery_agent.query_history = []
        
        # Final status update
        if competitor_quality_passed:
            final_message = f"Profile enrichment completed successfully with {len(research_state.get('company_info', {}).get('competitors', []))} competitors"
        else:
            final_message = f"Profile enrichment completed with limited competitor data after {self.max_competitor_iterations} attempts"
        
        await self.send_status_update(
            websocket_manager, job_id,
            status="profile_enrichment_complete",
            message=final_message,
            result={
                "step": "Profile Enrichment",
                "substep": "complete",
                "competitor_iterations": competitor_iteration,
                "quality_passed": competitor_quality_passed,
                "final_profile": research_state.get('company_info', {})
            }
        )
        
        # Ensure we have a complete research state
        if 'profile' not in research_state:
            research_state['profile'] = research_state.get('company_info', {})
        
        self.logger.info(f"Profile enrichment orchestration completed. Competitor quality passed: {competitor_quality_passed}")
        
        self.log_agent_complete(state)
        return research_state 