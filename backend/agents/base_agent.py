import logging
from typing import Dict, Any, Tuple, Optional
from ..services.websocket_manager import WebSocketManager


class BaseAgent:
    """Base class for all agents providing common functionality."""
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.logger = logging.getLogger(f"backend.agents.{agent_type}")
    
    def get_websocket_info(self, state: Dict[str, Any]) -> Tuple[Optional[WebSocketManager], Optional[str]]:
        """Extract WebSocket manager and job ID from state."""
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')
        return websocket_manager, job_id
    
    async def send_status_update(self, 
                               websocket_manager: Optional[WebSocketManager], 
                               job_id: Optional[str],
                               status: str,
                               message: str = None,
                               result: Dict[str, Any] = None):
        """Send status update through WebSocket manager."""
        if websocket_manager and job_id:
            try:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status=status,
                    message=message,
                    result=result
                )
            except Exception as e:
                self.logger.error(f"Error sending status update: {e}")
    
    async def send_error_update(self,
                              websocket_manager: Optional[WebSocketManager],
                              job_id: Optional[str],
                              error_msg: str,
                              step: str,
                              continue_research: bool = True):
        """Send error update through WebSocket manager."""
        if websocket_manager and job_id:
            try:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="error",
                    message=error_msg,
                    result={
                        "step": step,
                        "error": error_msg,
                        "continue_research": continue_research
                    }
                )
            except Exception as e:
                self.logger.error(f"Error sending error update: {e}")
    
    def log_agent_start(self, state: Dict[str, Any]):
        """Log agent start."""
        company = state.get('company', 'Unknown Company')
        self.logger.info(f"Starting {self.agent_type} for {company}")
    
    def log_agent_complete(self, state: Dict[str, Any]):
        """Log agent completion."""
        company = state.get('company', 'Unknown Company')
        self.logger.info(f"Completed {self.agent_type} for {company}")
    
    def log_agent_error(self, context: Dict[str, Any], error: Exception):
        """Log agent error."""
        self.logger.error(f"Error in {self.agent_type}: {error}", exc_info=True) 