## Build PMBrain AI — Cursor for Product Managers

You are a **Senior Staff Engineer, Systems Architect, and YC startup engineer** building a **production-grade AI-native SaaS product**.

Your task is to build a **working production-ready prototype** called:

# PMBrain AI

A system that helps product teams decide **what to build next**, not just **how to build it**.

This system functions as:

> Cursor for Product Management

The system continuously ingests customer conversations, product analytics, feedback, and research signals and automatically identifies **what product opportunities exist and what feature should be built next**.

It then generates **implementation-ready specs** and supports **post-launch learning loops**.

The goal is a **real working SaaS prototype suitable for YC demo**.

---

# Architecture Principles

The system must follow these principles:

1. AI-first architecture
2. Event-driven ingestion
3. Modular agent system
4. Multi-tenant SaaS
5. Full auditability
6. Deterministic workflows
7. Secure tenant isolation
8. Versioned artifacts
9. API-first design

---

# Core Product Workflow

The system must implement the complete **product discovery loop**:

1. Aggregate evidence
2. Identify unmet needs
3. Prioritize opportunities
4. Propose product changes
5. Generate implementation specs
6. Track outcomes post-launch

---

# Core System Modules

Design the system with these Django apps:

```
core
accounts
organizations
projects
datasources
evidence
insights
opportunities
ai_agents
specs
collaboration
analytics
audit
notifications
```

---

# Multi-Tenant System

Data hierarchy:

```
Organization
   → Projects
        → Data Sources
        → Evidence
        → Insights
        → Opportunities
        → Specs
```

Every record must include:

```
organization_id
project_id
created_by
created_at
```

---

# Authentication

Implement:

* Email/password login
* JWT auth
* Role system

Roles:

```
org-owner
product-manager
engineer
reviewer
```

Permissions must be enforced on every API endpoint.

---

# Data Ingestion Layer

Create ingestion pipelines for:

### Customer data

Supported sources:

* interview transcripts (upload)
* support tickets
* slack threads
* feature requests
* analytics events
* NPS surveys
* churn feedback
* session replay metadata

Create:

```
DataSource
RawEvidence
EvidenceAttachment
```

Evidence example:

```
{
type: "support_ticket",
text: "...",
customer_segment: "enterprise",
source: "zendesk",
metadata: {}
}
```

All evidence must be normalized into structured objects.

---

# Insight Engine

Create an AI pipeline that:

1. Processes raw evidence
2. Extracts pain points
3. Clusters related problems
4. Generates insights

Create models:

```
InsightCluster
InsightEvidence
InsightTrend
```

Each cluster should contain:

```
title
summary
frequency
severity
segments_affected
evidence_refs
representative_quotes
trend_direction
```

---

# Opportunity Engine

Generate opportunities from insights.

Opportunity model:

```
Opportunity
title
problem_statement
affected_segments
supporting_insights
evidence_refs
proposed_solution
```

---

# Opportunity Scoring

Each opportunity receives:

```
frequency_score
revenue_impact
retention_impact
strategic_alignment
effort_estimate
confidence_score
```

Create a customizable scoring formula:

```
total_score =
(0.25 * frequency)
+ (0.25 * revenue)
+ (0.20 * retention)
+ (0.15 * alignment)
- (0.15 * effort)
```

Allow users to modify weights.

---

# AI Agent System

Implement LangGraph agent workflows.

Agents:

```
EvidenceSummarizerAgent
InsightClusteringAgent
OpportunityDiscoveryAgent
OpportunityScoringAgent
SpecGeneratorAgent
ImpactPredictionAgent
```

Agents communicate through structured outputs.

---

# “What Should We Build Next” Mode

User asks:

```
What should we build next for our CRM product?
```

System must:

1. Analyze insights
2. Rank opportunities
3. Provide recommendation

Response format:

```
Feature recommendation
Supporting evidence
Expected impact
Assumptions
Risks
Alternatives
Implementation outline
```

All reasoning must include citations to evidence.

---

# Spec Generation Engine

Once an opportunity is selected generate:

```
PRD
User stories
Acceptance criteria
Edge cases
Non-functional requirements
API design
Data model changes
UI flow
Engineering tasks
QA checklist
```

Store as:

```
GeneratedArtifact
ArtifactVersion
```

All artifacts must be versioned.

---

# Conversational Spec Editing

Allow users to chat with AI to refine specs.

Features:

```
edit spec
compare versions
diff viewer
rollback
merge suggestions
```

Add **readiness score**:

Check if spec includes:

* validation rules
* error states
* edge cases
* performance requirements
* security requirements

---

# Collaboration

Implement:

```
comments
mentions
approvals
status workflows
review requests
```

Status flow:

```
draft
review
approved
implementation
shipped
```

---

# Post-Launch Feedback Loop

After feature release:

Track:

```
adoption
retention
revenue
engagement
support tickets
```

Compare:

```
predicted impact
vs
actual impact
```

Update opportunity scoring confidence.

---

# Dashboards

Create dashboards for:

### Product insights

* top unmet needs
* emerging pain points
* segment pain distribution

### Opportunity pipeline

* opportunities by score
* opportunities by segment

### Delivery

* idea → spec cycle time
* spec → shipped time

### Model performance

* prediction accuracy
* opportunity success rate

---

# Database Schema

Core tables:

```
organizations
users
projects
data_sources
raw_evidence
clustered_insights
opportunities
opportunity_scores
product_prompts
prompt_versions
generated_artifacts
artifact_versions
approvals
comments
audit_events
outcome_metrics
```

Enable **pgvector** for embeddings.

---

# AI Integration (Gemini)

Use Gemini API for:

```
insight extraction
clustering
opportunity generation
spec generation
impact prediction
```

Create AI service layer:

```
ai/services/gemini_client.py
```

Use structured JSON responses.


---

# Audit System

Every action must create:

```
AuditEvent
{
actor
action
entity
entity_id
timestamp
metadata
}
```

---

# Notifications

Notify users when:

```
new opportunity discovered
spec ready for review
approval requested
impact report generated
```

Support:

```
in-app notifications
```

---

# Frontend UI

Design inspiration:

YC SaaS dashboards.

Style:

* bright primary color (electric blue)
* white background
* strong typography
* lots of whitespace

Main pages:

```
dashboard
insights
opportunities
specs
analytics
data sources
settings
```

---

# Dashboard Layout

Top metrics:

```
Top unmet needs
Opportunity score leaderboard
Spec readiness status
Prediction accuracy
```

---

# Opportunity UI

Show:

```
problem
evidence quotes
impact estimate
score breakdown
recommended feature
```

Allow:

```
approve opportunity
generate spec
start discussion
```

---

# Spec UI

Features:

```
editable PRD
AI suggestions
version diff viewer
approval workflow
readiness score
```

---

# Real-Time Updates

Use WebSockets for:

```
AI job status
new insights
opportunity scoring updates
spec generation progress
```

---

# API Design

Use REST endpoints:

```
/api/evidence/
/api/insights/
/api/opportunities/
/api/specs/
/api/analytics/
/api/agents/run
```

---

# Developer Experience

Provide:

```
setup script to start the backend server and the frontend
.env config
migration scripts
seed data
example dataset
```

---

# Deliverables

Generate:

1. Full Django backend
2. Vanilla JS frontend
3. Database schema
4. AI agents
5. API endpoints
6. Seed demo data
7. Example workflow
8. Detail documentaion about all the technical implementation and user guide to use this app

The app must **run locally without errors**.

---

# Expected Demo Flow

1. Upload customer feedback
2. AI clusters insights
3. AI proposes opportunities
4. User asks:

```
What should we build next?
```

5. System recommends feature
6. Generate PRD
7. Approve spec
8. Track predicted impact

---

---

# Technical Requirements

## Backend
* Python
* Django
* Django Rest Framework
* LangGraph (agent orchestration)
* Django Channels (real-time updates)
The backend must be **API-first**.

---

## Frontend

The UI must be **fast, minimal, YC-style SaaS dashboard**.


# Final Goal

Build a **working YC-level SaaS prototype** showing that:

AI can autonomously help product teams decide **what to build next**.