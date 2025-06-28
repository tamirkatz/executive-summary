from __future__ import annotations
import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from tavily import AsyncTavilyClient
from langchain_core.messages import AIMessage

from ..agents.base_agent import BaseAgent

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class SearchQueries(BaseModel):
    queries: List[str] = Field(description="List of 20 competitor search queries", min_length=20, max_length=20)

class CompetitorNames(BaseModel):
    competitors: List[str] = Field(description="List of competitor company names", max_length=50)

class CompetitorWithDescription(BaseModel):
    name: str = Field(description="Competitor company name")
    description: str = Field(description="Brief description of what the company does")

class CompetitorValidation(BaseModel):
    is_competitor: bool = Field(description="Whether this company is actually a competitor")
    reasoning: str = Field(description="Brief explanation of why it is or isn't a competitor")

class ValidatedCompetitors(BaseModel):
    competitors: List[str] = Field(description="List of validated competitor company names")

# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class EnhancedCompetitorDiscoveryAgent(BaseAgent):
    """Simplified competitor discovery agent that finds competitors in 3 phases."""
    
    def __init__(self, llm_model: str = "gpt-4o"):
        super().__init__(agent_type="competitor_discovery_agent")
        
        self.llm_model = llm_model
        self.temperature = 0.3
        self.rate_limit = 5  # Tavily concurrent requests
        
        if not os.getenv("TAVILY_API_KEY"):
            raise ValueError("TAVILY_API_KEY is not configured")
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is not configured")
            
        self.llm = ChatOpenAI(model=self.llm_model, temperature=self.temperature, api_key=os.getenv("OPENAI_API_KEY"))
        self.tavily = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        self.sem = asyncio.Semaphore(self.rate_limit)

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
       
        self.log_agent_start(state)
        company = state.get('company', 'Unknown Company')
        websocket_manager, job_id = self.get_websocket_info(state)
        
        try:
            # Extract profile from state
            profile = state.get("profile", {})
            company_description = profile.get("description", "")
            core_products = profile.get("core_products", [])
            
            # Phase 1: Generate 20 search queries
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🔍 Generating search queries for {company}",
                result={"step": "Competitor Discovery", "substep": "query_generation"}
            )
            
            search_queries = await self._generate_search_queries(company, company_description, core_products)
            
            # Phase 1.5: Generate niche-specific queries
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🎯 Generating niche-specific queries for {company}",
                result={"step": "Competitor Discovery", "substep": "niche_query_generation"}
            )
            
            
            # Phase 2: Execute all searches and combine results
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🌐 Searching with  ({len(search_queries)} general queries)",
                result={"step": "Competitor Discovery", "substep": "search"}
            )
            
            combined_results = await self._execute_searches_and_combine(search_queries)
            
            # Phase 3: Extract competitor names using LLM
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message="🧮 Extracting competitor names",
                result={"step": "Competitor Discovery", "substep": "extraction"}
            )
            
            competitor_names = await self._extract_competitor_names(company, company_description, core_products, combined_results)
            
            # Phase 4: Validate competitors with LLM using descriptions
            await self.send_status_update(
                websocket_manager, job_id,
                status="processing",
                message=f"🔍 Validating {len(competitor_names)} competitors with descriptions",
                result={"step": "Competitor Discovery", "substep": "validation"}
            )
            
            validated_competitors = await self._validate_competitors_with_llm(
                company, company_description, core_products, competitor_names, 
                websocket_manager, job_id
            )
            
            # Store results in state
            state["competitors"] = validated_competitors
            state["competitor_discovery"] = {
                "general_queries": search_queries,
                "initial_competitors_found": len(competitor_names),
                "validated_competitors_found": len(validated_competitors),
                "competitors": validated_competitors,
                "validation_removed": len(competitor_names) - len(validated_competitors)
            }
            
            # Add completion message
            completion_msg = f"✅ Discovered and validated {len(validated_competitors)} competitors for {company} (filtered from {len(competitor_names)} initial candidates)"
            messages = state.get('messages', [])
            messages.append(AIMessage(content=completion_msg))
            state['messages'] = messages
            
            await self.send_status_update(
                websocket_manager, job_id,
                status="completed",
                message=completion_msg,
                result={
                    "step": "Competitor Discovery",
                    "substep": "complete",
                    "initial_competitors_found": len(competitor_names),
                    "validated_competitors_found": len(validated_competitors),
                    "competitors": validated_competitors,
                    "validation_removed": len(competitor_names) - len(validated_competitors)
                }
            )
            
            return state
            
        except Exception as e:
            error_msg = f"❌ Competitor discovery failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            await self.send_status_update(
                websocket_manager, job_id,
                status="error",
                message=error_msg,
                result={"step": "Competitor Discovery", "error": str(e)}
            )
            return state

    async def _generate_search_queries(self, company: str, description: str, core_products: List[str]) -> List[str]:
        """Phase 1: Generate exactly 25 search queries for finding competitors."""
        
        core_products_text = ", ".join(core_products) if core_products else "N/A"
        
        prompt = f"""You are a competitive intelligence analyst. Generate exactly 20 search queries to find competitors for the following company.

Company: {company}
Description: {description}
Core Products: {core_products_text}

Generate search queries that will help discover the company main competitors



Return exactly 20 queries."""

        llm_with_schema = self.llm.with_structured_output(SearchQueries)
        response = await llm_with_schema.ainvoke(prompt)
        self.logger.info(f"Search queries: {response.queries}")
        return response.queries

    async def _execute_searches_and_combine(self, queries: List[str]) -> Dict[str, Any]:
        """Phase 2: Execute all searches concurrently and combine into one object."""
        
        async def _execute_single_search(query: str) -> Dict[str, Any]:
            async with self.sem:
                try:
                    result = await self.tavily.search(
                        query=query, 
                        max_results=5, 
                        include_answer=True,
                        include_raw_content=False
                    )
                    return {
                        "query": query,
                        "results": result.get("results", []),
                        "answer": result.get("answer", "")
                    }
                except Exception as e:
                    self.logger.warning(f"Search failed for query '{query}': {e}")
                    return {
                        "query": query,
                        "results": [],
                        "answer": "",
                        "error": str(e)
                    }

        # Execute all searches concurrently
        search_tasks = [_execute_single_search(query) for query in queries]
        search_results = await asyncio.gather(*search_tasks)
        
        # Combine all results into one object
        combined_results = {
            "total_queries": len(queries),
            "successful_searches": len([r for r in search_results if not r.get("error")]),
            "all_search_results": search_results,
            "all_content": [],
            "all_answers": []
        }
        
        # Extract all content and answers for LLM processing
        for search_result in search_results:
            if not search_result.get("error"):
                # Add answer if available
                if search_result.get("answer"):
                    combined_results["all_answers"].append({
                        "query": search_result["query"],
                        "answer": search_result["answer"]
                    })
                
                # Add all result content
                for result in search_result.get("results", []):
                    combined_results["all_content"].append({
                        "query": search_result["query"],
                        "title": result.get("title", ""),
                        "content": result.get("content", ""),
                        "url": result.get("url", "")
                    })
        
        return combined_results

    async def _extract_competitor_names(self, company: str, description: str, core_products: List[str], combined_results: Dict[str, Any]) -> List[str]:
        """Phase 3: Use LLM to extract competitor names from all search results."""
        
        # Prepare content for LLM
        content_snippets = []
        for content_item in combined_results.get("all_content", []):
            snippet = f"Query: {content_item['query']}\nTitle: {content_item['title']}\nContent: {content_item['content'][:500]}\n---"
            content_snippets.append(snippet)
        
        answer_snippets = []
        for answer_item in combined_results.get("all_answers", []):
            snippet = f"Query: {answer_item['query']}\nAnswer: {answer_item['answer']}\n---"
            answer_snippets.append(snippet)
        
        # Combine all content (limit to avoid token limits)
        all_content = "\n".join(content_snippets)[:15000]  # Limit content length
        all_answers = "\n".join(answer_snippets)[:5000]    # Limit answers length
        
        core_products_text = ", ".join(core_products) if core_products else "N/A"
        
        prompt = f"""You are a competitive intelligence analyst. Extract the names of competitor companies from the search results below.

TARGET COMPANY: {company}
DESCRIPTION: {description}
CORE PRODUCTS: {core_products_text}

SEARCH RESULTS:
{all_content}

SEARCH ANSWERS:
{all_answers}

Instructions:
1. Identify companies that could be competitors to the target company
2. Focus on companies that offer similar products, services, or solutions
3. Include direct competitors, indirect competitors, and alternative solutions
4. Return only clean company names (no descriptions or additional text)
5. Remove duplicates and ensure names are properly formatted
6. Exclude the target company itself
7. Exclude generic terms, technologies, or non-company entities
8. Focus on actual company names that can be researched further

Return a list of competitor company names."""

        llm_with_schema = self.llm.with_structured_output(CompetitorNames)
        response = await llm_with_schema.ainvoke(prompt)
        
        # Clean and deduplicate the results
        competitors = []
        seen = set()
        
        for name in response.competitors:
            # Clean the name
            cleaned_name = name.strip()
            
            # Skip if empty, too long, or is the target company
            if not cleaned_name or len(cleaned_name) > 100 or cleaned_name.lower() == company.lower():
                continue
                
            # Check for duplicates (case-insensitive)
            name_key = cleaned_name.lower()
            if name_key not in seen:
                seen.add(name_key)
                competitors.append(cleaned_name)
        
        return competitors

    async def _validate_competitors_with_llm(self, company: str, company_description: str, 
                                           core_products: List[str], competitor_names: List[str],
                                           websocket_manager=None, job_id=None) -> List[str]:
        """Phase 4: Validate competitors using LLM analysis with company descriptions."""
        
        if not competitor_names:
            return []
        
        # Step 1: Get descriptions for each competitor
        await self.send_status_update(
            websocket_manager, job_id,
            status="processing",
            message=f"📋 Getting descriptions for {len(competitor_names)} competitors",
            result={"step": "Competitor Discovery", "substep": "getting_descriptions"}
        )
        
        competitors_with_descriptions = await self._get_competitor_descriptions(competitor_names)
        
        # Step 2: Validate each competitor with LLM
        await self.send_status_update(
            websocket_manager, job_id,
            status="processing",
            message=f"🤖 Analyzing {len(competitors_with_descriptions)} competitors with LLM",
            result={"step": "Competitor Discovery", "substep": "llm_validation"}
        )
        
        validated_competitors = await self._llm_validate_competitors(
            company, company_description, core_products, competitors_with_descriptions
        )
        
        removed_count = len(competitor_names) - len(validated_competitors)
        
        await self.send_status_update(
            websocket_manager, job_id,
            status="processing",
            message=f"✅ Validation complete: {len(validated_competitors)} competitors confirmed, {removed_count} filtered out",
            result={
                "step": "Competitor Discovery", 
                "substep": "validation_complete",
                "validated": len(validated_competitors),
                "removed": removed_count
            }
        )
        
        return validated_competitors

    async def _get_competitor_descriptions(self, competitor_names: List[str]) -> List[CompetitorWithDescription]:
        """Get brief descriptions for competitor companies using Tavily search."""
        
        async def _get_single_description(name: str) -> CompetitorWithDescription:
            async with self.sem:
                try:
                    # Search for company description
                    query = f'"{name}" company what they do business description'
                    result = await self.tavily.search(
                        query=query,
                        max_results=3,
                        include_answer=True
                    )
                    
                    description = "Unknown company"
                    
                    # Try to get description from answer first
                    if result.get("answer"):
                        description = result["answer"][:200]  # Limit length
                    elif result.get("results") and result["results"][0].get("content"):
                        # Fallback to first result content
                        content = result["results"][0]["content"]
                        description = content[:200]  # Limit length
                    
                    return CompetitorWithDescription(name=name, description=description)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to get description for {name}: {e}")
                    return CompetitorWithDescription(name=name, description="Unknown company")
        
        # Get descriptions concurrently
        description_tasks = [_get_single_description(name) for name in competitor_names]
        competitors_with_descriptions = await asyncio.gather(*description_tasks)
        
        return competitors_with_descriptions

    async def _llm_validate_competitors(self, company: str, company_description: str, 
                                      core_products: List[str], 
                                      competitors_with_descriptions: List[CompetitorWithDescription]) -> List[str]:
        """Use LLM to validate if each company is actually a competitor."""
        
        core_products_text = ", ".join(core_products) if core_products else "N/A"
        
        # Prepare competitor list for validation
        competitor_info = []
        for comp in competitors_with_descriptions:
            competitor_info.append(f"- {comp.name}: {comp.description}")
        
        competitors_text = "\n".join(competitor_info)
        
        prompt = f"""You are a competitive intelligence expert. Analyze the following companies to determine if they are actual competitors to the target company.

TARGET COMPANY: {company}
TARGET DESCRIPTION: {company_description}
TARGET CORE PRODUCTS: {core_products_text}

CANDIDATE COMPANIES TO VALIDATE:
{competitors_text}

For each candidate company, determine if it is a TRUE COMPETITOR based on these criteria:
1. Serves similar customer segments or markets
2. Offers similar products, services, or solutions
3. Customers would realistically consider them as alternatives
4. They operate in overlapping business areas
5. They compete for the same revenue opportunities

A company is NOT a competitor if:
- It operates in a completely different industry
- It serves entirely different customer segments
- It offers complementary rather than competing products
- It's a partner, vendor, or supplier rather than competitor
- It's too broad/generic (like "Google" or "Microsoft" unless specifically competing)

Return only the names of companies that are TRUE COMPETITORS. Be strict in your evaluation."""

        llm_with_schema = self.llm.with_structured_output(ValidatedCompetitors)
        response = await llm_with_schema.ainvoke(prompt)
        
        validated = []
        for name in response.competitors:
            cleaned_name = name.strip()
            if cleaned_name and cleaned_name.lower() != company.lower():
                validated.append(cleaned_name)
        
        self.logger.info(f"LLM validation: {len(validated)} competitors validated from {len(competitors_with_descriptions)} candidates")
        
        return validated
