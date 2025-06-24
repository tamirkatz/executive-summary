# Enhanced Three-Agent Pre-Research Workflow

## Overview

The Enhanced Three-Agent Pre-Research Workflow extends the existing company research system with a comprehensive pre-research phase that gathers factual, verifiable intelligence before the main research workflow begins.

## Architecture

```
[Company Research Agent] → [Industry Research Agent] → [Competitors Research Agent]
→ [User Profile Enrichment] → [Existing Workflow]
```

### New Flow vs Original Flow

**Enhanced Flow:**

1. **Company Research Agent** - Factual company data extraction
2. **Industry Research Agent** - Comprehensive industry analysis
3. **Competitors Research Agent** - Deep competitive intelligence
4. **User Profile Enrichment** - Enhanced with pre-research data
5. **[Existing Workflow]** - All remaining steps unchanged

**Original Flow:**

1. **User Profile Enrichment** - Standard profile enrichment
2. **[Existing Workflow]** - All remaining steps unchanged

## New Agents

### 1. Company Research Agent (`CompanyResearchAgent`)

**Purpose**: Extract factual, verifiable company data using advanced Tavily crawl capabilities.

**Key Features:**

- Strategic website crawling with fact-focused instructions
- SEC filing analysis for public companies
- Job posting analysis for strategic direction insights
- Financial and partnership data extraction
- Product specification and customer analysis

**Tavily Crawl Parameters:**

```python
crawl_params = {
    "max_depth": 3,
    "max_breadth": 25,
    "limit": 60,
    "instructions": "Extract FACTUAL DATA ONLY: revenue numbers, customer names, product specifications...",
    "categories": ["About", "Investors", "Customers", "Technology", "Careers", "Press", "Legal", "Products", "Solutions"],
    "exclude_paths": ["/blog/*", "/marketing/*", "/events/*", "/media/*"],
    "extract_depth": "advanced"
}
```

**Output Structure:**

```python
company_factual_data = {
    "website_analysis": {},      # Product specs, tech stack, customers
    "financial_data": {},        # Revenue, funding, partnerships
    "product_specifications": {}, # Features, capabilities, roadmap
    "customer_segments": {},     # Target industries, key customers
    "technology_stack": {},      # Technologies, investments
    "organizational_structure": {}, # Team size, hiring, executives
    "intelligence_summary": {},  # Complete intelligence summary
    "reliability_score": 0.0     # Data reliability score (0-1)
}
```

### 2. Industry Research Agent (`IndustryResearchAgent`)

**Purpose**: Comprehensive industry analysis including market trends, technology disruptions, and regulatory landscape.

**Research Domains:**

- **Market Trends**: Size, growth, adoption rates, forecasts
- **Technology Disruptions**: Emerging tech, patents, innovation
- **Regulatory Landscape**: Policy changes, compliance, impact
- **Competitive Dynamics**: Market share, consolidation, benchmarks
- **Opportunity Analysis**: Growth opportunities, market gaps

**Data Sources:**

- Management consulting firms (McKinsey, BCG, Bain, Deloitte, PWC)
- Research firms (Gartner, Forrester, IDC)
- Financial news (Bloomberg, Reuters, WSJ, FT)
- Government sources (.gov domains)
- Academic institutions

**Output Structure:**

```python
industry_intelligence = {
    "market_trends": {
        "market_size_data": [],
        "growth_forecasts": [],
        "adoption_rates": [],
        "customer_behavior": []
    },
    "technology_disruptions": {
        "emerging_technologies": [],
        "innovation_patterns": [],
        "patent_activity": [],
        "transformation_trends": []
    },
    "regulatory_landscape": {
        "recent_policies": [],
        "compliance_changes": [],
        "regulatory_impact": [],
        "upcoming_regulations": []
    },
    "competitive_dynamics": {
        "market_concentration": [],
        "competitive_intensity": [],
        "industry_benchmarks": [],
        "consolidation_trends": []
    },
    "opportunity_analysis": {
        "growth_opportunities": [],
        "market_gaps": [],
        "regulatory_opportunities": [],
        "technology_convergence": []
    }
}
```

### 3. Competitors Research Agent (`CompetitorsResearchAgent`)

**Purpose**: Deep competitive intelligence using enhanced Tavily crawl and real-time monitoring.

**Key Capabilities:**

- **Enhanced Competitor Discovery**: AI-powered identification of all competitors
- **Comprehensive Profiling**: Detailed profiles for each competitor
- **Technology Analysis**: Tech stacks, capabilities, integrations
- **Strategic Movement Tracking**: Funding, partnerships, executive changes
- **Partnership Mapping**: Technology and channel partner networks
- **Real-time Intelligence**: Recent news, hiring, pricing changes

**Discovery Methods:**

1. **AI-Powered Discovery**: Uses OpenAI to identify comprehensive competitor lists
2. **Search-Based Discovery**: Targeted searches across comparison sites
3. **Database Discovery**: Crunchbase, Owler, G2, Capterra analysis

**Enhanced Crawl Parameters:**

```python
competitor_crawl_params = {
    "max_depth": 4,
    "max_breadth": 30,
    "limit": 80,
    "instructions": "Extract COMPETITIVE INTELLIGENCE: product features and pricing, technology capabilities...",
    "categories": ["About", "Products", "Pricing", "Customers", "Investors", "News", "Careers", "Technology"],
    "exclude_paths": ["/blog/*", "/marketing/*", "/events/*", "/media/*"],
    "extract_depth": "advanced"
}
```

**Output Structure:**

```python
enhanced_competitor_data = {
    "comprehensive_profiles": {},      # Detailed competitor profiles
    "technology_comparisons": {        # Tech stack comparisons
        "technology_stacks": {},
        "product_capabilities": {},
        "integration_ecosystems": {}
    },
    "strategic_movements": {           # Recent strategic activities
        "recent_funding": {},
        "executive_changes": {},
        "strategic_partnerships": {},
        "product_launches": {}
    },
    "partnership_networks": {         # Partner ecosystems
        "technology_partners": {},
        "channel_partners": {},
        "integration_partnerships": {}
    },
    "real_time_updates": {            # Real-time intelligence
        "news_mentions": {},
        "hiring_patterns": {},
        "pricing_changes": {},
        "market_movements": {}
    },
    "discovered_competitors": [],      # All discovered competitors
    "total_competitors": 0             # Total number analyzed
}
```

## Enhanced State Management

### New State Fields

```python
# Enhanced Pre-Research State Fields
company_factual_data: Dict[str, Any]      # Company Research Agent results
industry_intelligence: Dict[str, Any]     # Industry Research Agent results
enhanced_competitor_data: Dict[str, Any]  # Competitors Research Agent results
pre_research_complete: bool               # Flag indicating pre-research completion
```

### Default Values

All new state fields have comprehensive default structures to ensure compatibility.

## Usage

### Basic Enhanced Workflow

```python
from backend import create_enhanced_workflow

# Create enhanced workflow with three-agent pre-research
workflow = create_enhanced_workflow(
    company="Stripe",
    url="https://stripe.com",
    user_role="CEO",
    websocket_manager=websocket_manager,
    job_id="job_123",
    enable_enhanced_pre_research=True,  # Enable three-agent pre-research
    include_specialized_research=False
)

# Run the workflow
async for state in workflow.run(thread={"configurable": {"thread_id": "1"}}):
    print(f"Current phase: {state.get('current_phase', 'Unknown')}")
```

### Backward Compatibility

```python
from backend import Graph

# Original workflow still works unchanged
workflow = Graph(
    company="Stripe",
    url="https://stripe.com",
    user_role="CEO"
)
```

### Individual Agent Usage

```python
from backend import CompanyResearchAgent, IndustryResearchAgent, CompetitorsResearchAgent

# Use agents individually
company_agent = CompanyResearchAgent()
industry_agent = IndustryResearchAgent()
competitors_agent = CompetitorsResearchAgent()

# Run individual agents
state = {"company": "Stripe", "company_url": "https://stripe.com"}
enhanced_state = await company_agent.run(state)
```

## Data Quality Framework

### Source Reliability Scoring

- **SEC filings**: 0.95 reliability
- **Company website**: 0.9 reliability
- **Job postings**: 0.85 reliability
- **Press releases**: 0.8 reliability
- **News articles**: 0.7 reliability
- **Social media**: 0.5 reliability

### Multi-Source Verification

- Cross-reference facts across multiple sources
- Prioritize primary sources over secondary
- Flag unverified information
- Calculate overall reliability scores

### Temporal Relevance

- Prioritize data from last 12 months
- Weight recent information higher
- Track data freshness and update frequency

## Advanced Features

### Smart Rate Limiting

- Automatic rate limiting for API calls
- Retry logic with exponential backoff
- Concurrent request management
- Error handling and graceful degradation

### Real-Time Progress Updates

- WebSocket integration for live updates
- Phase tracking and progress calculation
- Enhanced metrics and analytics
- Error reporting and status updates

### Caching and Performance

- Result caching to avoid redundant API calls
- Intelligent query deduplication
- Parallel processing where possible
- Memory-efficient data structures

## Configuration Options

### Enhanced Workflow Options

```python
workflow = create_enhanced_workflow(
    company="CompanyName",
    url="https://company.com",
    user_role="Executive",
    websocket_manager=ws_manager,
    job_id="unique_job_id",
    include_specialized_research=True,    # Include specialized researcher
    enable_enhanced_pre_research=True     # Enable three-agent pre-research
)
```

### Agent-Specific Configuration

```python
# Company Research Agent
company_agent = CompanyResearchAgent(model_name="gpt-4o-mini")

# Industry Research Agent
industry_agent = IndustryResearchAgent(model_name="gpt-4o-mini")

# Competitors Research Agent
competitors_agent = CompetitorsResearchAgent(model_name="gpt-4o-mini")
```

## Error Handling

### Graceful Degradation

- Agents continue processing even if individual searches fail
- Partial results returned rather than complete failure
- Error logging for debugging and monitoring
- Fallback strategies for critical failures

### WebSocket Error Updates

- Real-time error notifications
- Detailed error context and suggestions
- Continue/retry options for users
- Comprehensive error logging

## Performance Considerations

### API Rate Limiting

- Implemented across all agents
- Respectful of Tavily API limits
- Batch processing for efficiency
- Intelligent request spacing

### Memory Management

- Efficient data structures
- Streaming results where possible
- Garbage collection optimization
- Memory usage monitoring

### Parallel Processing

- Concurrent agent execution where appropriate
- Parallel search query processing
- Non-blocking I/O operations
- Efficient resource utilization

## Monitoring and Analytics

### Enhanced Metrics

- **Pre-research metrics**: Sources, reliability scores, data quality
- **Workflow metrics**: Query counts, document counts, processing times
- **Data quality metrics**: Verification rates, source diversity, freshness

### Progress Tracking

- **Phase identification**: Clear indication of current workflow phase
- **Progress calculation**: Accurate percentage completion
- **Enhanced state monitoring**: Real-time state change tracking
- **Performance analytics**: Timing and efficiency metrics

## Future Enhancements

### Planned Features

1. **Machine Learning Integration**: Automated competitor scoring and ranking
2. **Trend Analysis**: Historical trend tracking and prediction
3. **Custom Agent Templates**: Industry-specific agent configurations
4. **Advanced Visualization**: Interactive dashboards and reports
5. **API Integration**: Third-party data source integrations

### Extension Points

- **Custom Agents**: Framework for building domain-specific agents
- **Data Connectors**: Integration with CRM, sales tools, etc.
- **Notification Systems**: Slack, email, webhook integrations
- **Export Formats**: PDF, PowerPoint, Excel export options

## Best Practices

### Usage Guidelines

1. **Always provide company URLs** for enhanced website crawling
2. **Use descriptive job IDs** for better tracking and debugging
3. **Enable WebSocket updates** for real-time monitoring
4. **Monitor API usage** to stay within rate limits
5. **Review reliability scores** to assess data quality

### Performance Optimization

1. **Use parallel processing** when analyzing multiple companies
2. **Cache results** for repeated analyses
3. **Limit competitor counts** for faster processing
4. **Monitor memory usage** for large-scale operations
5. **Implement proper error handling** for production use

## Troubleshooting

### Common Issues

1. **API Key Configuration**: Ensure TAVILY_API_KEY and OPENAI_API_KEY are set
2. **Rate Limiting**: Reduce concurrent requests if hitting limits
3. **Memory Issues**: Process smaller batches for large competitor lists
4. **Network Timeouts**: Implement retry logic for network operations
5. **Data Quality**: Verify source reliability scores and cross-reference facts

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
logging.getLogger('backend').setLevel(logging.DEBUG)
```

### Support

For issues and questions:

1. Check the error logs for detailed information
2. Verify API key configuration and permissions
3. Review WebSocket status updates for real-time debugging
4. Monitor system resources and API usage
5. Contact support with detailed error logs and reproduction steps
