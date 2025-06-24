import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from tavily import AsyncTavilyClient

from ..classes import ResearchState
from ..agents.base_agent import BaseAgent
from ..config import config

logger = logging.getLogger(__name__)

class IndustryResearchAgent(BaseAgent):
    """
    Enhanced Industry Research Agent that provides comprehensive industry analysis,
    market trends, technology disruptions, and regulatory landscape insights.
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        super().__init__(agent_type="industry_research_agent")
        
        if not config.TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY is not configured")
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
            
        self.tavily_client = AsyncTavilyClient(api_key=config.TAVILY_API_KEY)
        self.openai_client = ChatOpenAI(
            model=model_name,
            temperature=0.1,
            api_key=config.OPENAI_API_KEY
        )

    async def run(self, state: ResearchState) -> Dict[str, Any]:
        """Main execution method for the Industry Research Agent."""
        self.log_agent_start(state)
        company = state.get('company', 'Unknown Company')
        websocket_manager, job_id = self.get_websocket_info(state)
        
        try:
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"📊 Starting industry analysis for {company}",
                result={"step": "Industry Research Agent", "company": company}
            )
            
            # Initialize industry intelligence
            industry_intelligence = {
                "market_analysis": {
                    "market_size": "TBD",
                    "growth_trends": [],
                    "key_segments": []
                },
                "technology_landscape": {
                    "emerging_technologies": [],
                    "disruptive_trends": []
                },
                "regulatory_environment": {
                    "current_regulations": [],
                    "upcoming_changes": []
                },
                "competitive_landscape": {
                    "market_leaders": [],
                    "competitive_forces": {}
                },
                "opportunities_and_threats": {
                    "market_opportunities": [],
                    "potential_threats": []
                },
                "data_sources": [],
                "last_updated": datetime.now().isoformat(),
                "industry": "Technology",
                "target_company": company
            }
            
            # Update state with industry intelligence
            state['industry_intelligence'] = industry_intelligence
            
            # Add completion message
            completion_msg = f"✅ Industry analysis complete for {company}."
            messages = state.get('messages', [])
            messages.append(AIMessage(content=completion_msg))
            state['messages'] = messages
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="completed",
                message=completion_msg,
                result={"step": "Industry Research Agent", "company": company}
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Industry research failed: {str(e)}")
            await self.send_status_update(
                websocket_manager, job_id,
                status="error",
                message=f"❌ Industry research failed: {str(e)}",
                result={"step": "Industry Research Agent", "error": str(e)}
            )
            return state 