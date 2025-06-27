try:
    from typing import TypedDict, NotRequired, Required, Dict, List, Any
except ImportError:
    from typing_extensions import TypedDict, NotRequired, Required, Dict, List, Any
from backend.services.websocket_manager import WebSocketManager

#Define the input state
class InputState(TypedDict, total=False):
    company: Required[str]
    company_url: NotRequired[str]
    user_role: Required[str]
    websocket_manager: NotRequired[WebSocketManager]
    job_id: NotRequired[str]
    

class ResearchState(InputState):
    site_scrape: Dict[str, Any]
    messages: List[Any]
    profile: Dict[str, Any]  # Enriched user profile from UserProfileEnrichmentAgent
    user_interests: Dict[str, Any]  # Inferred user interests from InterestInferenceAgent
    financial_data: Dict[str, Any]
    news_data: Dict[str, Any]
    company_data: Dict[str, Any]
    competitor_data: Dict[str, Any]  # Dedicated competitor intelligence data
    curated_financial_data: Dict[str, Any]
    curated_news_data: Dict[str, Any]
    curated_company_data: Dict[str, Any]
    curated_competitor_data: Dict[str, Any]  # Curated competitor intelligence data
    strategic_insights: Dict[str, Any]  # Synthesized insights from InsightSynthesizer
    financial_briefing: str
    news_briefing: str
    company_briefing: str
    competitor_briefing: str  # Dedicated competitor briefing
    references: List[str]
    briefings: Dict[str, Any]
    report: str
    research_plan: Dict[str, Any]  # Structured research plan from ResearchIntentPlanner
    research_planning_complete: bool  # Flag indicating research planning is complete
    queries: List[Dict[str, Any]]  # Surgical queries from QueryComposer
    query_composition_complete: bool  # Flag indicating query composition is complete
    generated_queries: List[str]  # Legacy field for backward compatibility
    query_generation_complete: bool  # Legacy field for backward compatibility
    categorized_queries: Dict[str, List[str]]  # Queries organized by category from Collector
    total_queries: int  # Total number of queries generated
    query_collection_complete: bool  # Flag indicating query collection is complete
    sector_trends: List[Dict[str, Any]]  # Industry and sector trend data from SectorTrendAgent
    
    # Workflow fields that are actually populated
    client_trends: NotRequired[List[Dict[str, Any]]]  # Client industry trends from ClientTrendAgent
    
    # Competitor discovery fields (used by current workflow)
    competitor_discovery: NotRequired[Dict[str, Any]]  # Competitor discovery results from EnhancedCompetitorDiscoveryAgent
    competitors: NotRequired[List[str]]  # Simple competitor list from competitor discovery agents
    competitor_analysis: NotRequired[Dict[str, Any]]  # Competitor analysis results from CompetitorAnalystAgent
    
    # Additional workflow fields that are populated
    specialized_data: NotRequired[Dict[str, Any]]  # Specialized researcher data
    reference_titles: NotRequired[List[str]]  # Reference titles from curator
    reference_info: NotRequired[Dict[str, Any]]  # Reference information from curator
    
    # Profile-derived fields for easier access
    known_clients: NotRequired[List[str]]  # Notable clients from profile
    use_cases: NotRequired[List[str]]  # Use cases from profile  
    core_products: NotRequired[List[str]]  # Core products from profile
    synonyms: NotRequired[List[str]]  # Synonyms from profile
    customer_segments: NotRequired[List[str]]  # Customer segments from profile

default_research_state = {
    "site_scrape": {},
    "messages": [],
    "profile": {},
    "user_interests": {},
    "financial_data": {},
    "news_data": {},
    "company_data": {},
    "competitor_data": {},  # NEW: Dedicated competitor data
    "curated_financial_data": {},
    "curated_news_data": {},
    "curated_company_data": {},
    "curated_competitor_data": {},  # NEW: Curated competitor data
    "strategic_insights": {},
    "financial_briefing": "",
    "news_briefing": "",
    "company_briefing": "",
    "competitor_briefing": "",  # NEW: Competitor briefing
    "references": [],
    "briefings": {},
    "report": "",
    "research_plan": {},
    "research_planning_complete": False,
    "queries": [],
    "query_composition_complete": False,
    "generated_queries": [],
    "query_generation_complete": False,
    "categorized_queries": {},
    "total_queries": 0,
    "query_collection_complete": False,
    "sector_trends": [],
    
    # Workflow fields that are actually populated
    "client_trends": [],
    
    # Competitor discovery fields (used by current workflow)
    "competitor_discovery": {},
    "competitors": [],
    "competitor_analysis": {},
    
    # Additional workflow fields that are populated
    "specialized_data": {},
    "reference_titles": [],
    "reference_info": {},
    
    # Profile-derived fields
    "known_clients": [],
    "use_cases": [],
    "core_products": [],
    "synonyms": [],
    "customer_segments": []
}