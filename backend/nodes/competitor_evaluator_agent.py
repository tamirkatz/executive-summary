import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from backend.config import config
from ..classes import ResearchState
from ..agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class CompetitorQualityScore(BaseModel):
    overall_score: float = Field(description="Overall quality score 0-1 for the competitor list")
    quantity_score: float = Field(description="Score for having sufficient number of competitors")
    relevance_score: float = Field(description="Score for how relevant competitors are to the company")
    diversity_score: float = Field(description="Score for diversity of competitor types and sources")
    confidence_score: float = Field(description="Score based on confidence levels of competitors")
    issues_found: List[str] = Field(description="List of issues identified with the competitor list")
    recommendations: List[str] = Field(description="Recommendations for improvement")
    pass_threshold: bool = Field(description="Whether the list meets minimum quality threshold")


class CompetitorEvaluatorAgent(BaseAgent):
    def __init__(self, model_name: str = "gpt-4o-mini"):
        super().__init__(agent_type="competitor_evaluator_agent")
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.1,
            api_key=config.OPENAI_API_KEY
        )
        
        # Quality thresholds
        self.min_competitors = 4
        self.min_overall_score = 0.7
        self.min_relevance_score = 0.6

    async def evaluate_competitor_list(self, 
                                     competitors: List[str], 
                                     company: str, 
                                     description: str,
                                     candidate_details: List[Dict] = None,
                                     websocket_manager=None, 
                                     job_id=None) -> CompetitorQualityScore:
        """Evaluate the quality of a competitor list using multiple criteria."""
        
        await self.send_status_update(
            websocket_manager, job_id,
            status="processing",
            message=f"Evaluating competitor list quality for {company}",
            result={"step": "Competitor Evaluation", "substep": "analysis"}
        )
        
        issues = []
        recommendations = []
        
        # 1. Quantity Score
        quantity_score = min(1.0, len(competitors) / self.min_competitors)
        if len(competitors) < self.min_competitors:
            issues.append(f"Only {len(competitors)} competitors found, need at least {self.min_competitors}")
            recommendations.append("Expand search queries to include industry-specific terms")
        
        # 2. Relevance Score using LLM analysis
        relevance_score = await self._assess_competitor_relevance(
            competitors, company, description
        )
        
        if relevance_score < self.min_relevance_score:
            issues.append(f"Low relevance score ({relevance_score:.2f}) - competitors may not be direct matches")
            recommendations.append("Focus search on companies with similar business models and target markets")
        
        # 3. Diversity Score
        diversity_score = self._calculate_diversity_score(competitors, candidate_details)
        
        # 4. Confidence Score (if candidate details available)
        confidence_score = self._calculate_confidence_score(candidate_details) if candidate_details else 0.8
        
        # 5. Check for generic or low-quality entries
        generic_issues = self._check_for_generic_entries(competitors)
        if generic_issues:
            issues.extend(generic_issues)
            recommendations.append("Filter out generic terms and non-specific company names")
        
        # 6. Check for duplicate or similar entries
        duplicate_issues = self._check_for_duplicates(competitors)
        if duplicate_issues:
            issues.extend(duplicate_issues)
            recommendations.append("Implement better deduplication logic")
        
        # Calculate overall score
        overall_score = (
            quantity_score * 0.25 +
            relevance_score * 0.35 +
            diversity_score * 0.2 +
            confidence_score * 0.2
        )
        
        # Determine if list passes threshold
        pass_threshold = (
            overall_score >= self.min_overall_score and
            len(competitors) >= self.min_competitors and
            relevance_score >= self.min_relevance_score and
            len(issues) <= 2
        )
        
        evaluation = CompetitorQualityScore(
            overall_score=overall_score,
            quantity_score=quantity_score,
            relevance_score=relevance_score,
            diversity_score=diversity_score,
            confidence_score=confidence_score,
            issues_found=issues,
            recommendations=recommendations,
            pass_threshold=pass_threshold
        )
        
        await self.send_status_update(
            websocket_manager, job_id,
            status="evaluation_complete",
            message=f"Competitor evaluation completed: Score {overall_score:.2f}, Pass: {pass_threshold}",
            result={
                "step": "Competitor Evaluation",
                "substep": "complete",
                "evaluation": evaluation.model_dump()
            }
        )
        
        return evaluation

    async def _assess_competitor_relevance(self, competitors: List[str], company: str, description: str) -> float:
        """Use LLM to assess how relevant the competitors are to the company."""
        
        competitors_text = ", ".join(competitors)
        
        relevance_prompt = f"""You are a business analyst evaluating competitor relevance.

Main Company: {company}
Description: {description}

Proposed Competitors: {competitors_text}

Assess how relevant these competitors are as a group to {company} based on:
1. Similar products/services offered
2. Similar target market and customers
3. Similar business model
4. Geographic/market overlap

Consider:
- Are these DIRECT competitors that customers would compare to {company}?
- Do they operate in the same market segment?
- Would a customer considering {company} also consider these alternatives?

Rate the overall relevance of this competitor list from 0.0 to 1.0:
- 1.0 = Excellent list of highly relevant direct competitors
- 0.8 = Good list with most competitors being relevant
- 0.6 = Moderate list with some relevant competitors
- 0.4 = Poor list with few relevant competitors
- 0.2 = Very poor list with mostly irrelevant entries
- 0.0 = Completely irrelevant competitors

Return only the numerical score (e.g., 0.75):"""

        try:
            result = await self.llm.ainvoke(relevance_prompt)
            score_text = result.content.strip()
            return float(score_text)
        except Exception as e:
            self.logger.error(f"Error assessing competitor relevance: {e}")
            return 0.5  # Default moderate score

    def _calculate_diversity_score(self, competitors: List[str], candidate_details: List[Dict] = None) -> float:
        """Calculate diversity score based on variety in competitor names and sources."""
        
        if not competitors:
            return 0.0
        
        # Basic diversity: check for variety in company names
        unique_words = set()
        for competitor in competitors:
            words = competitor.lower().split()
            unique_words.update(words)
        
        # Score based on lexical diversity
        lexical_diversity = len(unique_words) / max(1, len(' '.join(competitors).split()))
        
        # If we have candidate details, factor in source diversity
        source_diversity = 1.0
        if candidate_details:
            sources = [detail.get('source', 'unknown') for detail in candidate_details]
            unique_sources = len(set(sources))
            source_diversity = min(1.0, unique_sources / 3)  # Expect at least 3 different sources
        
        return (lexical_diversity + source_diversity) / 2

    def _calculate_confidence_score(self, candidate_details: List[Dict] = None) -> float:
        """Calculate average confidence score from candidate details."""
        
        if not candidate_details:
            return 0.8  # Default score when no details available
        
        confidences = []
        for detail in candidate_details:
            confidence = detail.get('confidence_score', 0.5)
            confidences.append(confidence)
        
        return sum(confidences) / len(confidences) if confidences else 0.5

    def _check_for_generic_entries(self, competitors: List[str]) -> List[str]:
        """Check for generic or low-quality competitor entries."""
        
        issues = []
        generic_terms = [
            'companies', 'startups', 'businesses', 'solutions', 'platforms', 
            'tools', 'services', 'software', 'systems', 'products', 'providers'
        ]
        
        generic_competitors = []
        for competitor in competitors:
            competitor_lower = competitor.lower()
            if any(term in competitor_lower for term in generic_terms):
                if len(competitor.split()) <= 2:  # Short generic terms are more problematic
                    generic_competitors.append(competitor)
        
        if generic_competitors:
            issues.append(f"Found generic entries: {', '.join(generic_competitors)}")
        
        # Check for very short names (likely incomplete)
        short_names = [c for c in competitors if len(c.strip()) < 3]
        if short_names:
            issues.append(f"Found very short names: {', '.join(short_names)}")
        
        return issues

    def _check_for_duplicates(self, competitors: List[str]) -> List[str]:
        """Check for potential duplicate entries."""
        
        issues = []
        seen = set()
        duplicates = []
        
        for competitor in competitors:
            normalized = competitor.lower().strip()
            if normalized in seen:
                duplicates.append(competitor)
            seen.add(normalized)
        
        if duplicates:
            issues.append(f"Found potential duplicates: {', '.join(duplicates)}")
        
        # Check for very similar names (basic similarity)
        similar_pairs = []
        competitors_lower = [c.lower() for c in competitors]
        for i, comp1 in enumerate(competitors_lower):
            for j, comp2 in enumerate(competitors_lower[i+1:], i+1):
                # Simple similarity check
                if self._are_similar_names(comp1, comp2):
                    similar_pairs.append((competitors[i], competitors[j]))
        
        if similar_pairs:
            pairs_text = [f"({pair[0]}, {pair[1]})" for pair in similar_pairs]
            issues.append(f"Found similar names: {', '.join(pairs_text)}")
        
        return issues

    def _are_similar_names(self, name1: str, name2: str) -> bool:
        """Check if two company names are very similar."""
        
        # Simple similarity: if one name is contained in another and they're close in length
        if name1 in name2 or name2 in name1:
            if abs(len(name1) - len(name2)) <= 3:
                return True
        
        # Check for common words
        words1 = set(name1.split())
        words2 = set(name2.split())
        common_words = words1 & words2
        
        # If most words are common, they might be variants of the same company
        if len(common_words) >= 2 and len(common_words) >= min(len(words1), len(words2)) * 0.7:
            return True
        
        return False

    async def run(self, state: ResearchState) -> ResearchState:
        """Main entry point for the competitor evaluator agent."""
        company = state.get('company', 'Unknown Company')
        company_info = state.get('company_info', {})
        description = company_info.get('description', '')
        competitors = company_info.get('competitors', [])
        
        # Get candidate details if available
        discovery_result = state.get('competitor_discovery_result', {})
        candidate_details = discovery_result.get('candidate_details', [])
        
        websocket_manager, job_id = self.get_websocket_info(state)

        self.log_agent_start(state)

        # Evaluate competitor list
        evaluation = await self.evaluate_competitor_list(
            competitors=competitors,
            company=company,
            description=description,
            candidate_details=candidate_details,
            websocket_manager=websocket_manager,
            job_id=job_id
        )
        
        self.logger.info(f"Competitor evaluation completed for {company}. Score: {evaluation.overall_score:.2f}, Pass: {evaluation.pass_threshold}")
        
        # Update the state with evaluation results
        updated_state = state.copy()
        updated_state['competitor_evaluation'] = evaluation.model_dump()
        
        # If evaluation didn't pass and we haven't exceeded max iterations, 
        # we could trigger re-discovery (this would be handled by the orchestrator)
        if not evaluation.pass_threshold:
            self.logger.warning(f"Competitor list for {company} did not pass quality threshold")
            await self.send_status_update(
                websocket_manager, job_id,
                status="evaluation_failed",
                message=f"Competitor list quality below threshold: {evaluation.overall_score:.2f}",
                result={
                    "step": "Competitor Evaluation",
                    "substep": "quality_check_failed",
                    "issues": evaluation.issues_found,
                    "recommendations": evaluation.recommendations
                }
            )
        else:
            await self.send_status_update(
                websocket_manager, job_id,
                status="evaluation_passed",
                message=f"Competitor list meets quality standards: {evaluation.overall_score:.2f}",
                result={
                    "step": "Competitor Evaluation",
                    "substep": "quality_check_passed",
                    "score": evaluation.overall_score
                }
            )

        self.log_agent_complete(state)
        return updated_state 