import logging
from typing import Any, Dict, List

from langchain_core.messages import AIMessage

from ...classes import ResearchState
from .base import BaseResearcher

logger = logging.getLogger(__name__)

class SpecializedResearcher(BaseResearcher):
    def __init__(self) -> None:
        super().__init__()
        self.analyst_type = "specialized_researcher"

    async def analyze(self, state: ResearchState) -> Dict[str, Any]:
        company = state.get('company', 'Unknown Company')
        websocket_manager = state.get('websocket_manager')
        job_id = state.get('job_id')
        
        try:
            # Get categorized queries from collector agent
            categorized_queries = state.get('categorized_queries', {})
            
            if not categorized_queries:
                logger.warning(f"No categorized queries found for {company}")
                return {
                    'message': "No categorized queries available for specialized research",
                    'specialized_data': {},
                    'analyst_type': self.analyst_type
                }
            
            # Focus on specialized categories that might need extra attention
            specialized_categories = {
                'technology': [],
                'market': [],
                'competitor': [],
                'partnership': [],
                'regulatory': [],
                'geopolitical': [],
                'risk': [],
                'opportunity': []
            }
            
            # Extract specialized queries
            for category, queries in categorized_queries.items():
                if category in specialized_categories and queries:
                    specialized_categories[category] = queries[:5]  # Limit to 5 queries per category
            
            # Filter out empty categories
            specialized_categories = {k: v for k, v in specialized_categories.items() if v}
            
            if not specialized_categories:
                return {
                    'message': "No specialized categories found for additional research",
                    'specialized_data': {},
                    'analyst_type': self.analyst_type
                }
            
            # Add message to show specialized queries
            queries_msg = "🔬 Specialized research queries:\n"
            for category, queries in specialized_categories.items():
                if queries:
                    queries_msg += f"\n• {category.title()}: {len(queries)} queries"
                    for query in queries[:2]:  # Show first 2 queries per category
                        queries_msg += f"\n  - {query}"
                    if len(queries) > 2:
                        queries_msg += f"\n  ... and {len(queries) - 2} more"
            
            messages = state.get('messages', [])
            messages.append(AIMessage(content=queries_msg))
            state['messages'] = messages

            # Send initial status through WebSocket
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message="Specialized research queries prepared",
                    result={
                        "step": "Specialized Researcher",
                        "analyst_type": "Specialized Researcher",
                        "categories": list(specialized_categories.keys()),
                        "total_queries": sum(len(queries) for queries in specialized_categories.values())
                    }
                )
            
            # Initialize specialized data container
            specialized_data = {}
            
            # Process each specialized category
            for category, queries in specialized_categories.items():
                if not queries:
                    continue
                
                # Send status update for category processing
                if websocket_manager and job_id:
                    await websocket_manager.send_status_update(
                        job_id=job_id,
                        status="processing",
                        message=f"Processing specialized {category} queries",
                        result={
                            "step": "Specialized Researcher",
                            "category": category,
                            "query_count": len(queries)
                        }
                    )
                
                # Set appropriate analyst type for search parameters
                original_analyst_type = self.analyst_type
                self.analyst_type = "company_analyst"  # Use company analyst for specialized research
                
                try:
                    # Search documents for this category
                    documents = await self.search_documents(state, queries)
                    
                    # Add documents to specialized data container
                    for url, doc in documents.items():
                        doc['query'] = f"specialized_{category}: {doc.get('query', '')}"
                        doc['category'] = category
                        specialized_data[url] = doc
                finally:
                    # Restore original analyst type
                    self.analyst_type = original_analyst_type

            # Send completion status
            completion_msg = f"Completed specialized research with {len(specialized_data)} documents across {len(specialized_categories)} categories"
            
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="processing",
                    message=completion_msg,
                    result={
                        "step": "Specialized Researcher",
                        "analyst_type": "Specialized Researcher",
                        "specialized_documents": len(specialized_data),
                        "categories_processed": len(specialized_categories)
                    }
                )
            
            # Update state
            messages.append(AIMessage(content=completion_msg))
            state['messages'] = messages
            state['specialized_data'] = specialized_data

            return {
                'message': completion_msg,
                'specialized_data': specialized_data,
                'analyst_type': self.analyst_type,
                'specialized_categories': specialized_categories
            }

        except Exception as e:
            error_msg = f"Specialized research failed: {str(e)}"
            logger.error(error_msg)
            
            # Send error status
            if websocket_manager and job_id:
                await websocket_manager.send_status_update(
                    job_id=job_id,
                    status="error",
                    message=error_msg,
                    result={
                        "analyst_type": "Specialized Researcher",
                        "error": str(e)
                    }
                )
            raise  # Re-raise to maintain error flow

    async def run(self, state: ResearchState) -> Dict[str, Any]:
        return await self.analyze(state) 