# PMBrain AI — AI Response Format Specification

## Overview

All AI responses in PMBrain follow a structured JSON format.
The frontend renders these structured sections with visual components.

## Response Sections

### 1. Recommendation Summary
```json
{
  "feature": "Feature name",
  "confidence": 0.91,
  "summary": "Executive summary with data citations"
}
```
Rendered as: Hero card with gradient background, score ring.

### 2. Supporting Evidence
```json
{
  "supporting_evidence": [
    {"type": "interview", "quote": "...", "segment": "enterprise", "source": "Q4 Interview"}
  ]
}
```
Rendered as: Quote cards with colored left borders.

### 3. Opportunity Score Graph
```json
{
  "score_breakdown": {
    "frequency": 8.5,
    "revenue_impact": 7.2,
    "retention_impact": 9.0,
    "strategic_alignment": 8.8,
    "effort_estimate": 6.5,
    "total_score": 8.0
  }
}
```
Rendered as: Animated score bars via `ScoreGraphRenderer`.

### 4. Execution Flow
```json
{
  "execution_flow": [
    {"phase": "Backend API", "description": "Build WebSocket endpoints", "estimate": "1 week"},
    {"phase": "Frontend", "description": "Dashboard components", "estimate": "1 week"}
  ]
}
```
Rendered as: Connected node flowchart via `FlowchartRenderer`.

### 5. Implementation Tasks
```json
{
  "tasks": [
    {"task": "Add scoring service", "description": "...", "priority": "P0", "estimate": "3 days", "dependencies": []}
  ]
}
```
Rendered as: Expandable task cards with priority badges.

### 6. Risks and Assumptions
```json
{
  "risks": ["Risk 1", {"risk": "Risk 2", "mitigation": "..."}],
  "assumptions": ["Assumption 1"]
}
```
Rendered as: Bullet lists in side-by-side cards.

### 7. Competitor Analysis (Code Analysis v2)
```json
{
  "competitor_comparison": {
    "detected_product_type": "CRM",
    "common_competitor_features": [
      {"feature": "AI Lead Scoring", "status": "missing", "importance": "critical"}
    ],
    "competitive_gaps": ["Predictive forecasting"]
  }
}
```
Rendered as: Color-coded comparison table.

### 8. Implementation Timeline (Code Analysis v2)
```json
{
  "estimated_timeline": {
    "week_1": "Architecture design, data model updates",
    "week_2": "Backend API implementation",
    "week_3": "Frontend integration",
    "week_4": "Testing and rollout"
  }
}
```
Rendered as: Horizontal milestone cards with gradient headers.

## Visual Components

| Component | File | Usage |
|-----------|------|-------|
| `FlowchartRenderer` | `frontend/landing/components/flowchart.js` | Execution flows, pipelines |
| `ScoreGraphRenderer` | `frontend/landing/components/scoregraph.js` | Opportunity scores, breakdowns |

Both components are pure Vanilla JS + CSS, work in both the landing page and the app dashboard.

## Frontend Rendering Pipeline

```
AI JSON Response
    → Parse structured sections
    → Render hero card (recommendation)
    → Render ScoreGraphRenderer (scores)
    → Render FlowchartRenderer (execution flow)
    → Render expandable task cards
    → Render evidence quotes
    → Render competitor table (if code analysis)
    → Render timeline visualization (if code analysis)
```
