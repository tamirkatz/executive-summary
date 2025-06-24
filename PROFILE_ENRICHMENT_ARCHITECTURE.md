# Modular Profile Enrichment Architecture

This document describes the new modular approach to profile enrichment, breaking down the monolithic `UserProfileEnrichmentAgent` into specialized, coordinated agents.

## Architecture Overview

The new system consists of four main components:

1. **CompanyInfoAgent** - Extracts basic company information
2. **CompetitorDiscoveryAgent** - Sophisticated competitor discovery with feedback loops
3. **CompetitorEvaluatorAgent** - Quality assessment and validation
4. **ProfileEnrichmentOrchestrator** - Coordinates the entire process

## Component Details

### 1. CompanyInfoAgent

**Purpose**: Extracts basic company information without competitors.

**Input**:

- Company name
- User role
- Company URL (optional)

**Output**:

- Company description
- Industry classification
- Sector information
- Client industries
- Known clients
- Partners

**Key Features**:

- Deep web crawling using Tavily
- Business description synthesis
- Industry classification based on actual business activities

### 2. CompetitorDiscoveryAgent

**Purpose**: Discovers competitors using a sophisticated iterative approach with multiple search strategies.

**Input**:

- Company name
- Company description (from CompanyInfoAgent)
- Company URL

**Process**:

1. **Multi-iteration Loop** (max 3 iterations):

   - **Iteration 1**: Broad discovery queries
   - **Iteration 2**: Platform-specific queries (G2, Reddit, Quora)
   - **Iteration 3**: Niche and specialized queries

2. **Query Generation**: 3-5 Tavily queries per iteration using patterns like:

   - "companies offering similar services to X"
   - "alternatives to X for developers"
   - "market leaders in [category]"
   - "G2 alternatives to X"
   - "Reddit discussions X alternatives"

3. **Candidate Extraction**: LLM-powered extraction from search results

4. **Validation**: Tavily crawl to verify competitor accuracy

5. **Ranking**: Score based on:
   - Frequency across sources
   - Similarity to company profile (cosine similarity)
   - Confidence scores

**Key Features**:

- Parallel search execution
- Source diversity tracking
- Automatic deduplication
- Confidence scoring
- Frequency-based ranking

### 3. CompetitorEvaluatorAgent

**Purpose**: Evaluates competitor list quality and provides feedback for refinement.

**Evaluation Criteria**:

- **Quantity Score**: Minimum 4 competitors required
- **Relevance Score**: LLM assessment of competitor similarity
- **Diversity Score**: Variety in sources and competitor types
- **Confidence Score**: Average confidence of candidates
- **Quality Checks**:
  - Generic term detection
  - Duplicate identification
  - Minimum length validation

**Output**:

- Overall quality score (0-1)
- Pass/fail threshold determination
- Specific issues identified
- Recommendations for improvement

### 4. ProfileEnrichmentOrchestrator

**Purpose**: Coordinates the entire profile enrichment process with feedback loops.

**Process Flow**:

1. Run CompanyInfoAgent to extract basic information
2. **Competitor Discovery Loop** (max 3 attempts):
   - Run CompetitorDiscoveryAgent
   - Run CompetitorEvaluatorAgent
   - If quality threshold met → continue
   - If not → refine and retry
3. Finalize results and update state

## Quality Assurance Features

### Feedback Loop Mechanism

- **Automatic Refinement**: If competitor quality is below threshold, the system automatically refines search strategies
- **Progressive Iteration**: Each iteration uses different search patterns to maximize discovery
- **Early Termination**: If quality threshold is met early, saves API calls

### Validation Strategies

- **Tavily Crawl Validation**: Verifies competitor information through additional searches
- **LLM Similarity Assessment**: Uses GPT-4 to assess business model similarity
- **Multi-source Verification**: Tracks and weights competitors found across multiple sources

### Quality Metrics

- **Relevance Scoring**: 0-1 scale for how similar competitors are to the target company
- **Confidence Tracking**: Per-candidate confidence scores
- **Source Diversity**: Ensures competitors come from varied, reliable sources

## Usage Examples

### Basic Usage with Orchestrator

```python
from backend.nodes import ProfileEnrichmentOrchestrator

# Input state
input_state = {
    'company': 'Algolia',
    'company_url': 'https://www.algolia.com',
    'user_role': 'CTO'
}

# Run complete enrichment
orchestrator = ProfileEnrichmentOrchestrator()
result_state = await orchestrator.run(input_state)

# Access results
company_info = result_state['company_info']
competitors = company_info['competitors']
evaluation = result_state['competitor_evaluation']
```

### Individual Agent Usage

```python
from backend.nodes import CompanyInfoAgent, CompetitorDiscoveryAgent

# Step 1: Extract company info
company_agent = CompanyInfoAgent()
research_state = await company_agent.run(input_state)

# Step 2: Discover competitors
competitor_agent = CompetitorDiscoveryAgent()
research_state = await competitor_agent.run(research_state)
```

## Configuration Options

### CompetitorDiscoveryAgent Settings

- `max_iterations`: Maximum discovery attempts (default: 3)
- `min_competitors_required`: Minimum competitors needed (default: 4)
- Model selection: GPT-4o for accuracy, GPT-4o-mini for speed

### CompetitorEvaluatorAgent Thresholds

- `min_overall_score`: Minimum quality score (default: 0.7)
- `min_relevance_score`: Minimum relevance threshold (default: 0.6)
- `min_competitors`: Minimum quantity required (default: 4)

### ProfileEnrichmentOrchestrator Controls

- `max_competitor_iterations`: Maximum refinement attempts (default: 3)

## Benefits of Modular Architecture

### 1. **Specialized Focus**

Each agent has a single, well-defined responsibility, leading to better performance and maintainability.

### 2. **Quality Assurance**

The feedback loop ensures high-quality competitor discovery through iterative refinement.

### 3. **Scalability**

Individual agents can be optimized, replaced, or extended independently.

### 4. **Transparency**

Each step is tracked and logged, providing clear insight into the enrichment process.

### 5. **Flexibility**

Agents can be used individually or in different combinations based on specific needs.

### 6. **Robust Error Handling**

Each agent includes fallback mechanisms and graceful degradation.

## Monitoring and Debugging

### WebSocket Status Updates

The system provides real-time status updates through WebSocket connections:

- Step progress tracking
- Quality assessment results
- Error notifications with continuation options

### Logging and Metrics

- Detailed logging for each agent
- Performance metrics for search queries
- Quality score tracking over time

### Debug Information

- Query history preservation
- Candidate pool inspection
- Evaluation criteria breakdown

## Migration from Original System

The original `UserProfileEnrichmentAgent` can be replaced with the `ProfileEnrichmentOrchestrator` with minimal code changes. The API remains compatible while providing significantly enhanced competitor discovery capabilities.

## Future Enhancements

### Potential Improvements

1. **Semantic Similarity**: Use embeddings for more sophisticated competitor similarity assessment
2. **Industry-Specific Templates**: Customized search patterns for different industries
3. **Real-time Quality Adjustment**: Dynamic threshold adjustment based on industry complexity
4. **Competitor Categorization**: Classify competitors by type (direct, indirect, emerging)
5. **Partnership Discovery**: Enhanced partner identification using similar techniques
