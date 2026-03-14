# PMBrain AI — Code Analysis Enhancements (v2)

## Overview

The codebase analysis system has been enhanced to provide deeper product intelligence.
Beyond simple code summarization, it now performs:

1. **Existing Feature Detection** — Maps all user-facing capabilities
2. **Competitor Feature Comparison** — Compares against similar products
3. **Market Trend Alignment** — Identifies SaaS patterns
4. **New Feature Opportunities** — AI-suggested features with full implementation plans
5. **Implementation Timelines** — Week-by-week engineering plans
6. **Execution Flowcharts** — Visual step-by-step diagrams

## New Database Fields

Added to `CodebaseAnalysis` model:

| Field | Type | Description |
|-------|------|-------------|
| `missing_capabilities` | JSONField | Things the codebase doesn't support yet |
| `improvement_areas` | JSONField | Technical debt and improvement opportunities |
| `competitor_comparison` | JSONField | Feature comparison with competitors |
| `new_feature_opportunities` | JSONField | AI-suggested features with scores |

## Enhanced AI Prompt

The `CODE_UNDERSTANDING_PROMPT` now instructs the AI to:

1. Identify ALL existing product features with completeness status
2. Compare against competitor capabilities
3. Identify competitive gaps
4. Suggest new features with:
   - Problem statement
   - Business value
   - Target users
   - Implementation complexity
   - 4-week timeline breakdown
   - Backend + frontend task breakdown
   - Execution flow steps
   - Opportunity scores (0-10 per dimension)
   - Code integration points

## Frontend Visualization

The analysis detail view now includes:

### Feature Map
Grid view of all detected features with completeness badges (complete/partial/stub).

### Competitor Comparison Table
| Feature | Status | Importance |
|---------|--------|------------|
| AI Lead Scoring | Missing | Critical |
| Pipeline Forecasting | Partial | High |

### New Feature Opportunity Cards
Each card includes:
- Score graph (animated bars)
- Timeline visualization (horizontal milestones)
- Engineering task breakdown
- Execution flowchart
- Code integration chips

### Visual Components Used
- `ScoreGraphRenderer` — Animated opportunity score bars
- `FlowchartRenderer` — Connected execution flow nodes
- Timeline visualization — Horizontal week cards
- Competitor table — Color-coded status/importance

## API Response Schema (v2)

```json
{
  "system_summary": "...",
  "existing_features": [{"name": "...", "description": "...", "completeness": "complete", "category": "auth"}],
  "competitor_comparison": {
    "detected_product_type": "CRM",
    "common_competitor_features": [{"feature": "...", "status": "missing", "importance": "critical"}],
    "competitive_gaps": ["..."]
  },
  "new_feature_opportunities": [{
    "feature_name": "...",
    "problem_statement": "...",
    "business_value": "...",
    "target_users": "...",
    "implementation_complexity": "medium",
    "estimated_timeline": {"week_1": "...", "week_2": "..."},
    "engineering_tasks": {"backend": ["..."], "frontend": ["..."]},
    "execution_flow": [{"phase": "...", "description": "...", "estimate": "..."}],
    "opportunity_scores": {"frequency": 8, "revenue_impact": 7},
    "code_integration_points": ["..."]
  }],
  "missing_capabilities": ["..."],
  "improvement_areas": ["..."]
}
```

## Backward Compatibility

- The API returns all existing fields plus new ones
- Old clients that don't read the new fields are unaffected
- No existing API endpoints were changed
- Migration adds nullable JSONField columns with defaults
