from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os


class TavilyQueries(BaseModel):
    """Structured output for Tavily search queries."""
    queries: List[str] = Field(
        description="List of high-quality, specific Tavily search queries", 
        max_items=10
    )


class TavilyQueryGenerator:
    """Generates high-quality Tavily search queries based on user interests."""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Domain-specific sources for different information types
        self.source_mappings = {
            "financial_news": [
                "site:reuters.com",
                "site:bloomberg.com", 
                "site:wsj.com",
                "site:ft.com",
                "site:cnbc.com"
            ],
            "tech_news": [
                "site:techcrunch.com",
                "site:venturebeat.com",
                "site:theverge.com",
                "site:wired.com",
                "site:arstechnica.com"
            ],
            "startup_data": [
                "site:crunchbase.com",
                "site:angellist.com",
                "site:pitchbook.com",
                "site:cbinsights.com"
            ],
            "regulatory": [
                "site:sec.gov",
                "site:fdic.gov",
                "site:federalreserve.gov",
                "site:finra.org",
                "site:cfpb.gov"
            ],
            "industry_reports": [
                "site:statista.com",
                "site:forrester.com",
                "site:gartner.com",
                "site:ibisworld.com",
                "site:grandviewresearch.com"
            ],
            "academic": [
                "site:arxiv.org",
                "site:researchgate.net",
                "site:scholar.google.com",
                "site:ieee.org",
                "site:acm.org"
            ],
            "blogs": [
                "site:medium.com",
                "site:substack.com",
                "site:hashnode.dev",
                "site:dev.to"
            ]
        }
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("user", self._get_user_prompt())
        ])
        
        # Create the runnable chain with structured output
        self.chain = (
            {"interests": RunnablePassthrough()}
            | self.prompt
            | self.llm.with_structured_output(TavilyQueries)
        )
    
    def _get_system_prompt(self) -> str:
        """Generate the system prompt with query generation guidelines."""
        return """You are an expert search query generator who creates high-quality, specific Tavily search queries.

Your task is to convert user interests into precise, actionable search queries that will yield relevant and valuable information.

Query Generation Guidelines:

1. **Specificity**: Make queries specific and targeted, not generic
2. **Source Targeting**: Use site: operators to target specific domains when relevant
3. **Time Relevance**: Include current year or recent timeframes when appropriate
4. **Actionable Terms**: Use terms that indicate actionable insights
5. **Industry Context**: Include industry-specific terminology
6. **Competitive Intelligence**: Target competitor-specific information
7. **Regulatory Focus**: Include regulatory and compliance terms when relevant

Query Types to Generate:
- Market intelligence queries
- Competitive analysis queries
- Technology trend queries
- Regulatory compliance queries
- Industry report queries
- Startup funding queries
- Partnership opportunity queries

Source Targeting Strategy:
- Financial news: site:reuters.com, site:bloomberg.com, site:wsj.com
- Tech news: site:techcrunch.com, site:venturebeat.com
- Startup data: site:crunchbase.com, site:pitchbook.com
- Regulatory: site:sec.gov, site:fdic.gov
- Industry reports: site:statista.com, site:forrester.com
- Academic: site:arxiv.org, site:researchgate.net

Query Quality Standards:
- Each query should be unique and specific
- Include relevant site: operators when targeting specific sources
- Use current year (2025) for time-sensitive topics
- Focus on actionable business intelligence
- Avoid overly broad or generic terms
- Target high-value information sources

Generate up to 10 high-quality queries that would provide valuable insights for the user's interests."""
    
    def _get_user_prompt(self) -> str:
        """Generate the user prompt template."""
        return """Based on these user interests, generate high-quality Tavily search queries:

Strategic Interests: {strategic_interests}
Technology Interests: {technology_interests}
External Signals: {external_signals}
Information Sources: {information_sources}

Generate specific, actionable search queries that would help this person:
1. Stay informed about their strategic interests
2. Monitor technology trends relevant to their role
3. Track external signals and market changes
4. Find information from their preferred sources

Focus on:
- Specific, targeted queries (not generic)
- Relevant site: operators for high-quality sources
- Current year (2025) for time-sensitive topics
- Industry-specific terminology
- Competitive intelligence opportunities
- Regulatory and compliance information when relevant

Provide up to 10 unique, high-quality queries that would yield valuable business intelligence."""
    
    def generate_queries(self, interests: Dict[str, Any]) -> List[str]:
        """
        Generate Tavily search queries based on user interests.
        
        Args:
            interests: Dictionary from InterestInferenceAgent
            
        Returns:
            List of Tavily search queries
        """
        try:
            # Run the chain with structured output
            result = self.chain.invoke({"interests": interests})
            
            # Return the list of queries
            return result.queries
            
        except Exception as e:
            # Fallback to basic queries if generation fails
            return self._get_fallback_queries(interests)
    
    def generate_queries_async(self, interests: Dict[str, Any]) -> List[str]:
        """
        Async version of generate_queries.
        
        Args:
            interests: Dictionary from InterestInferenceAgent
            
        Returns:
            List of Tavily search queries
        """
        try:
            # Run the chain asynchronously with structured output
            result = self.chain.ainvoke({"interests": interests})
            
            # Return the list of queries
            return result.queries
            
        except Exception as e:
            # Fallback to basic queries if generation fails
            return self._get_fallback_queries(interests)
    
    def _get_fallback_queries(self, interests: Dict[str, Any]) -> List[str]:
        """Provide fallback queries based on interests."""
        strategic = interests.get("strategic_interests", [])
        tech = interests.get("technology_interests", [])
        signals = interests.get("external_signals", [])
        sources = interests.get("information_sources", [])
        
        queries = []
        
        # Generate basic queries from strategic interests
        for interest in strategic[:3]:
            queries.append(f"{interest} 2025 site:techcrunch.com")
        
        # Generate tech-focused queries
        for tech_interest in tech[:3]:
            queries.append(f"{tech_interest} trends 2025")
        
        # Generate market signal queries
        for signal in signals[:2]:
            queries.append(f"{signal} site:reuters.com")
        
        # Generate source-specific queries
        for source in sources[:2]:
            if "regulatory" in source.lower():
                queries.append(f"regulatory changes 2025 site:sec.gov")
            elif "financial" in source.lower():
                queries.append(f"market trends 2025 site:bloomberg.com")
            else:
                queries.append(f"industry news 2025 site:techcrunch.com")
        
        return queries[:10]  # Limit to 10 queries
    
    def generate_queries_with_sources(self, interests: Dict[str, Any], target_sources: List[str] = None) -> List[str]:
        """
        Generate queries with specific source targeting.
        
        Args:
            interests: Dictionary from InterestInferenceAgent
            target_sources: List of source categories to prioritize
            
        Returns:
            List of Tavily search queries with source targeting
        """
        if target_sources is None:
            target_sources = ["financial_news", "tech_news", "startup_data"]
        
        # Get base queries
        base_queries = self.generate_queries(interests)
        
        # Enhance with source targeting
        enhanced_queries = []
        for query in base_queries:
            # Check if query already has site: operator
            if "site:" not in query:
                # Add appropriate source based on query content
                if any(word in query.lower() for word in ["funding", "startup", "venture"]):
                    enhanced_queries.append(f"{query} site:crunchbase.com")
                elif any(word in query.lower() for word in ["tech", "ai", "software"]):
                    enhanced_queries.append(f"{query} site:techcrunch.com")
                elif any(word in query.lower() for word in ["market", "financial", "investment"]):
                    enhanced_queries.append(f"{query} site:bloomberg.com")
                else:
                    enhanced_queries.append(query)
            else:
                enhanced_queries.append(query)
        
        return enhanced_queries[:10] 