# AI Agent Architecture Documentation

## Overview

PMBrain AI uses a **LangGraph-style state machine** for agent orchestration. All AI responses come from the **live Gemini API** — there are no mocked or hardcoded responses.

## Gemini Client (`apps/ai_agents/services/gemini_client.py`)

### Key Features
- **REST API direct integration** (no SDK dependency issues)
- **Model failover**: Primary `gemini-2.5-flash-lite` → Fallback `gemini-flash-lite-latest`
- **Retry logic**: Configurable retries with exponential backoff
- **Rate limit handling**: Automatic wait-and-retry on 429 errors
- **Structured JSON output**: Parses and validates JSON responses
- **Streaming support**: `generate_streaming()` for real-time output
- **Logging**: Every API call logged with timing and token usage

### Configuration (`.env`)
```
GEMINI_API_KEY=<your-key>
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_FALLBACK_MODEL=gemini-flash-lite-latest
GEMINI_MAX_RETRIES=3
GEMINI_TIMEOUT=60
```

### Error Handling
```
1. Try primary model (up to max_retries)
   - On 429: exponential backoff, retry
   - On 404: skip to fallback model
   - On timeout: retry with backoff
2. Try fallback model (up to max_retries)
3. If all fail: raise GeminiAPIError
```

## Agent System

### Base Architecture

```python
class AgentState:
    """Shared state passed between agents in a workflow."""
    project: Project
    user: User
    data: dict          # Input data
    results: dict       # Agent results keyed by agent_type
    errors: list        # Errors from failed agents
    agent_runs: list    # AgentRun records for audit

class BaseAgent:
    agent_type: str
    ai: GeminiClient
    
    def run(state) → state:
        # Create AgentRun record
        # Execute agent
        # Update run record with results
        # Return updated state
    
    def execute(state) → dict:
        # Override in subclass
```

### Agents

| Agent | Type Key | Purpose |
|-------|----------|---------|
| EvidenceSummarizerAgent | `evidence_summarizer` | Extract pain points, quotes, topics from raw feedback |
| InsightClusteringAgent | `insight_clustering` | Group evidence into insight clusters |
| OpportunityDiscoveryAgent | `opportunity_discovery` | Generate opportunities from insights |
| OpportunityScoringAgent | `opportunity_scoring` | Score opportunities on 5 dimensions |
| SpecGeneratorAgent | `spec_generator` | Generate complete PRDs |
| ImpactPredictionAgent | `impact_prediction` | Predict adoption, retention, revenue |
| WhatToBuildAgent | `what_to_build` | **Flagship**: Recommend what to build next |
| SpecChatAgent | `spec_chat` | Conversational spec editing |
| **CodeUnderstandingAgent** | `code_understanding` | **NEW**: Analyze uploaded codebases |
| **MarketTrendAgent** | `market_trend` | **NEW**: Analyze market trends |
| **FeatureDiscoveryAgent** | `feature_discovery` | **NEW**: Combined feature discovery |

### Workflows

```python
WORKFLOWS = {
    'full_pipeline': [Evidence → Insights → Opportunities → Scores],
    'evidence_to_insights': [Evidence → Insights],
    'insights_to_opportunities': [Opportunities → Scores],
    'what_to_build': [WhatToBuild (enhanced)],
    'generate_spec': [SpecGenerator],
    'predict_impact': [ImpactPrediction],
    'score_opportunities': [Scoring],
    'edit_spec': [SpecChat],
    'analyze_codebase': [CodeUnderstanding],        # NEW
    'market_trends': [MarketTrend],                 # NEW
    'feature_discovery': [FeatureDiscovery],         # NEW
    'full_discovery': [Evidence → Insights → Opportunities → Scores → Trends → Discovery],  # NEW
}
```

## Prompt Templates (`apps/ai_agents/services/prompt_templates.py`)

All prompts are centralized for consistency and versioning:

- `EVIDENCE_SUMMARIZER_PROMPT`
- `INSIGHT_CLUSTERING_PROMPT`
- `OPPORTUNITY_DISCOVERY_PROMPT`
- `OPPORTUNITY_SCORING_PROMPT`
- `SPEC_GENERATOR_PROMPT`
- `IMPACT_PREDICTION_PROMPT`
- `WHAT_TO_BUILD_PROMPT` (basic)
- `WHAT_TO_BUILD_ENHANCED_PROMPT` (with code + trends)
- `CODE_UNDERSTANDING_PROMPT`
- `MARKET_TREND_PROMPT`
- `FEATURE_DISCOVERY_PROMPT`
- `SPEC_CHAT_PROMPT`

## Data Flow

```
Evidence (upload/API)
    ↓
EvidenceSummarizerAgent
    → Extracts: summary, pain_points, quotes, topics, sentiment, urgency
    ↓
InsightClusteringAgent
    → Generates: clusters with frequency, severity, segments, trends
    ↓
OpportunityDiscoveryAgent
    → Creates: opportunities with problem, solution, risks, alternatives
    ↓
OpportunityScoringAgent
    → Scores: frequency, revenue, retention, alignment, effort
    ↓
[Optional] CodeUnderstandingAgent
    → Analyzes: modules, features, APIs, models, capabilities
    ↓
[Optional] MarketTrendAgent
    → Identifies: emerging features, competitor gaps, market opportunities
    ↓
WhatToBuildAgent (Enhanced)
    → Recommends: feature + evidence + impact + code integration + execution plan
    ↓
SpecGeneratorAgent
    → Generates: PRD, user stories, tasks, QA checklist
```

## Audit Trail

Every agent execution creates an `AgentRun` record:
```
agent_type, status, input_data, output_data,
error_message, started_at, completed_at, duration_seconds,
tokens_used, organization, project, created_by
```

## Key Design Decisions

1. **No mocked responses**: All AI output comes from live Gemini API
2. **REST API over SDK**: Direct HTTP calls for maximum compatibility with Python 3.8
3. **Model failover**: Automatic fallback between models for reliability
4. **Prompt templates**: Centralized for easy tuning and versioning
5. **State machine pattern**: Agents compose into workflows with shared state
6. **Error tolerance**: Individual agent failures don't crash the workflow
