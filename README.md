# PMBrain AI, Complete Documentation

## 🧠 What is PMBrain AI?

**PMBrain AI is Cursor for Product Management.** It's an AI-native SaaS platform that helps product teams decide **what to build next**, not just how to build it.

The system continuously ingests customer conversations, product analytics, feedback, and research signals, then automatically identifies product opportunities and generates implementation-ready specs.

---

## 📐 Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend                    │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │Dashboard │Evidence  │Insights  │Opps      │Specs     │  │
│  └────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┘  │
│       └──────────┴──────────┴──────────┴──────────┘         │
│                     REST API + WebSocket                      │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                   Django Backend (API-First)                  │
│  ┌─────────┬──────────┬──────────┬──────────┬─────────┐    │
│  │accounts │evidence  │insights  │opps      │specs    │    │
│  │orgs     │datasrc   │ai_agents │collab    │analytics│    │
│  │projects │audit     │notifs    │          │         │    │
│  └────┬────┴────┬─────┴────┬─────┴──────────┴─────────┘    │
│       │         │          │                                 │
│  ┌────┴─────────┴──────────┴──────────────────────┐        │
│  │        Agent Orchestration Engine               │        │
│  │  (LangGraph-style State Machine Workflows)      │        │
│  │                                                  │        │
│  │  EvidenceSummarizer → InsightClustering →        │        │
│  │  OpportunityDiscovery → Scoring → SpecGen        │        │
│  └─────────────────────┬────────────────────────────┘        │
│                        │                                     │ 
└──────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                     Database                            │
│  users, organizations, projects, evidence, insights,         │
│  opportunities, scores, specs, versions, audit_events        │
└──────────────────────────────────────────────────────────────┘
```

### Design Principles
1. **AI-first architecture** — AI agents are core, not bolted on
2. **Event-driven ingestion** — Evidence flows through processing pipeline
3. **Modular agent system** — Each agent has single responsibility
4. **Multi-tenant SaaS** — Organization → Project data isolation
5. **Full auditability** — Every action logged to audit trail
6. **Deterministic workflows** — Agent chains produce reproducible results
7. **Secure tenant isolation** — Middleware enforces org boundaries
8. **Versioned artifacts** — All specs have full version history
9. **API-first design** — Frontend consumes same API as integrations

---

## 🗂️ Project Structure

```
PMBrain-AI/
├── manage.py                   # Django management
├── setup.sh                    # One-click setup & launch
├── requirements.txt            # Python dependencies
├── .env                        # Environment configuration
│
├── pmbrain/                    # Django project config
│   ├── settings.py             # All settings (JWT, DRF, CORS, etc.)
│   ├── urls.py                 # URL routing
│   ├── asgi.py                 # ASGI + WebSocket config
│   └── wsgi.py                 # WSGI config
│
├── apps/                       # Django applications
│   ├── core/                   # Base models, permissions, mixins
│   │   ├── models.py           # TimeStampedModel, TenantModel, ProjectScopedModel
│   │   ├── permissions.py      # Role-based permission classes
│   │   ├── mixins.py           # TenantQuerySetMixin, AuditMixin
│   │   └── management/commands/seed_demo.py
│   │
│   ├── accounts/               # User management + JWT auth
│   │   ├── models.py           # Custom User model
│   │   ├── serializers.py      # Register, Login, User serializers
│   │   ├── views.py            # Register, Login, Me endpoints
│   │   └── urls.py
│   │
│   ├── organizations/          # Multi-tenant organizations
│   │   ├── models.py           # Organization, OrgMembership
│   │   ├── serializers.py
│   │   ├── views.py            # CRUD + invite + members
│   │   └── urls.py
│   │
│   ├── projects/               # Projects within organizations
│   │   ├── models.py           # Project with scoring weights
│   │   └── ...
│   │
│   ├── datasources/            # Data source configuration
│   │   ├── models.py           # DataSource (8 types supported)
│   │   └── ...
│   │
│   ├── evidence/               # Raw evidence ingestion
│   │   ├── models.py           # RawEvidence, EvidenceAttachment
│   │   ├── views.py            # CRUD + bulk_upload + stats
│   │   └── ...
│   │
│   ├── insights/               # AI-generated insight clusters
│   │   ├── models.py           # InsightCluster, InsightTrend
│   │   ├── views.py            # CRUD + top_unmet_needs + by_segment
│   │   └── ...
│   │
│   ├── opportunities/          # Product opportunities
│   │   ├── models.py           # Opportunity, OpportunityScore, OutcomeMetric
│   │   ├── views.py            # CRUD + leaderboard + outcomes
│   │   └── ...
│   │
│   ├── ai_agents/              # AI agent system
│   │   ├── models.py           # AgentRun, ProductPrompt
│   │   ├── services/
│   │   │   ├── gemini_client.py      # Gemini API + mock responses
│   │   │   └── agent_orchestrator.py # LangGraph-style workflow engine
│   │   ├── views.py            # RunAgent, WhatToBuild endpoints
│   │   └── ...
│   │
│   ├── specs/                  # Generated specifications
│   │   ├── models.py           # GeneratedArtifact, ArtifactVersion
│   │   ├── views.py            # CRUD + chat + rollback + diff
│   │   └── ...
│   │
│   ├── collaboration/          # Comments, approvals, reviews
│   │   ├── models.py           # Comment, Approval, ReviewRequest
│   │   └── ...
│   │
│   ├── analytics/              # Dashboard aggregations
│   │   ├── views.py            # Dashboard, InsightAnalytics, OppAnalytics
│   │   └── ...
│   │
│   ├── audit/                  # Audit trail
│   │   ├── models.py           # AuditEvent
│   │   ├── middleware.py        # Auto-log API mutations
│   │   └── ...
│   │
│   └── notifications/          # In-app + WebSocket notifications
│       ├── models.py           # Notification
│       ├── consumers.py        # WebSocket consumer
│       ├── routing.py          # WebSocket URL routing
│       └── ...
│
├── frontend/                   # Vanilla JS + CSS frontend
│   ├── css/styles.css          # Complete YC-style design system
│   └── js/
│       ├── api.js              # REST API client with JWT handling
│       ├── websocket.js        # WebSocket manager
│       └── app.js              # Full SPA with all pages
│
└── templates/
    └── index.html              # HTML entry point
```

---

## 🔑 Authentication System

### Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register/` | Create account |
| POST | `/api/auth/login/` | Sign in, get JWT tokens |
| GET | `/api/auth/me/` | Get/update current user |
| POST | `/api/auth/token/refresh/` | Refresh JWT token |

### Roles
| Role | Permissions |
|------|-------------|
| `org-owner` | Full access to organization |
| `product-manager` | Manage evidence, insights, opportunities, specs |
| `engineer` | View all, contribute to specs |
| `reviewer` | View and comment |

### JWT Token Flow
1. Login → receive `access` + `refresh` tokens
2. All API calls include `Authorization: Bearer <access_token>`
3. On 401 → automatically refresh using refresh token
4. Refresh expired → redirect to login

---

## 🔌 API Reference

### Evidence
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/evidence/?project=<id>` | List evidence |
| POST | `/api/evidence/` | Create evidence |
| POST | `/api/evidence/bulk_upload/` | Bulk upload |
| GET | `/api/evidence/stats/?project=<id>` | Statistics |
| GET | `/api/evidence/<id>/` | Get single |

### Insights
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/insights/?project=<id>` | List insights |
| GET | `/api/insights/top_unmet_needs/?project=<id>` | Top 10 |
| GET | `/api/insights/by_segment/?project=<id>` | By segment |
| GET | `/api/insights/stats/?project=<id>` | Statistics |

### Opportunities
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/opportunities/?project=<id>` | List opportunities |
| GET | `/api/opportunities/leaderboard/?project=<id>` | Ranked by score |
| POST | `/api/opportunities/<id>/update_status/` | Change status |
| POST | `/api/opportunities/<id>/add_outcome/` | Add outcome metric |

### AI Agents
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/agents/run/` | Run any workflow |
| POST | `/api/agents/what-to-build/` | "What should we build?" |
| GET | `/api/agents/runs/?project=<id>` | List agent runs |

### Specs
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/specs/?project=<id>` | List specs |
| GET | `/api/specs/<id>/` | Get spec with versions |
| POST | `/api/specs/<id>/chat/` | AI spec editing |
| POST | `/api/specs/<id>/update_status/` | Change status |
| POST | `/api/specs/<id>/rollback/` | Rollback to version |
| GET | `/api/specs/<id>/diff/?v1=1&v2=2` | Compare versions |

### Analytics
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/analytics/dashboard/?project=<id>` | Main dashboard |
| GET | `/api/analytics/insights/?project=<id>` | Insight analytics |
| GET | `/api/analytics/opportunities/?project=<id>` | Opp analytics |

---

## 🤖 AI Agent System

### Agent Types

| Agent | Input | Output | Purpose |
|-------|-------|--------|---------|
| `EvidenceSummarizerAgent` | Raw evidence text | Summary, pain points, quotes | Extract structured data from evidence |
| `InsightClusteringAgent` | Processed evidence | Insight clusters | Group related problems |
| `OpportunityDiscoveryAgent` | Insight clusters | Opportunities | Generate product opportunities |
| `OpportunityScoringAgent` | Opportunities | Scores | Score on 5 dimensions |
| `SpecGeneratorAgent` | Opportunity | Full PRD | Generate implementation spec |
| `ImpactPredictionAgent` | Opportunity | Predictions | Predict adoption/revenue/retention |
| `WhatToBuildAgent` | All project data | Recommendation | Answer "what to build next?" |
| `SpecChatAgent` | Spec + message | Updated spec | Conversational editing |

### Workflows (LangGraph-style)

```python
WORKFLOWS = {
    'full_pipeline': [
        EvidenceSummarizerAgent,    # Step 1: Process evidence
        InsightClusteringAgent,      # Step 2: Cluster into insights
        OpportunityDiscoveryAgent,   # Step 3: Generate opportunities
        OpportunityScoringAgent,     # Step 4: Score all
    ],
    'what_to_build': [WhatToBuildAgent],
    'generate_spec': [SpecGeneratorAgent],
    'predict_impact': [ImpactPredictionAgent],
    'edit_spec': [SpecChatAgent],
}
```

### Scoring Formula

```
total_score = (0.25 × frequency) + (0.25 × revenue) + (0.20 × retention)
            + (0.15 × alignment) - (0.15 × effort)
```

Weights are customizable per project in project settings.

---

## 📊 Database Schema

### Core Tables

| Table | Key Fields | Description |
|-------|-----------|-------------|
| `users` | id, email, full_name, role | Custom user model |
| `organizations` | id, name, slug | Multi-tenant organizations |
| `org_memberships` | org_id, user_id, role | Role-based membership |
| `projects` | id, org_id, name, scoring_weights | Product projects |
| `data_sources` | id, project_id, source_type | Input data sources |
| `raw_evidence` | id, project_id, type, text, pain_points | Customer evidence |
| `insight_clusters` | id, project_id, title, frequency, severity | AI insights |
| `opportunities` | id, project_id, title, problem, status | Product opportunities |
| `opportunity_scores` | id, opp_id, frequency, revenue, total | Scoring |
| `generated_artifacts` | id, opp_id, type, status, version | Specs |
| `artifact_versions` | id, artifact_id, version, content | Versioned content |
| `audit_events` | id, actor, action, entity, timestamp | Audit trail |
| `notifications` | id, user_id, type, title, is_read | In-app notifications |
| `comments` | id, entity_type, entity_id, text | Comments |
| `approvals` | id, entity_type, entity_id, status | Approval workflow |
| `outcome_metrics` | id, opp_id, metric_type, predicted, actual | Post-launch tracking |
| `agent_runs` | id, agent_type, status, input, output | AI execution log |

### Multi-Tenant Hierarchy

```
Organization
  └── Project
       ├── DataSource
       ├── RawEvidence
       ├── InsightCluster
       ├── Opportunity
       │    ├── OpportunityScore
       │    └── OutcomeMetric
       └── GeneratedArtifact
            └── ArtifactVersion
```

Every record includes: `organization_id`, `project_id`, `created_by`, `created_at`

---

## 🖥️ Frontend

### Technology
- **Vanilla JavaScript** — No framework, fast loading
- **CSS Custom Properties** — Consistent design system
- **WebSocket** — Real-time updates via Django Channels
- **Single Page Application** — Client-side routing

### Pages
| Page | Description |
|------|-------------|
| Dashboard | Metrics, pipeline, top insights, opportunity leaderboard |
| Evidence | Upload, view, process customer evidence |
| Insights | AI-generated insight clusters with severity/trend |
| Opportunities | Scored opportunities with pipeline status |
| What to Build | AI recommendation engine |
| Specs | Generated PRDs with version history + AI chat |
| Analytics | Segment analysis, pipeline stats, agent performance |
| Data Sources | Connected data source management |

### Design System
- **Primary color:** Electric Blue (#2563EB)
- **Typography:** Inter font, strong weight hierarchy
- **Layout:** Fixed sidebar, fluid content area
- **Cards:** White background, subtle borders, rounded corners

---

## 🚀 Getting Started

### Quick Start
```bash
cd PMBrain-AI
chmod +x setup.sh
./setup.sh
```

### Manual Setup
```bash
# Install dependencies
pip3 install -r requirements.txt

# Run migrations
python3 manage.py makemigrations accounts organizations projects datasources evidence insights opportunities ai_agents specs collaboration audit notifications
python3 manage.py migrate

# Collect static files
python3 manage.py collectstatic --noinput

# Seed demo data
python3 manage.py seed_demo

# Start server
python3 manage.py runserver 0.0.0.0:8000
```

### Configuration (.env)
```
SECRET_KEY=your-secret-key
DEBUG=True
GEMINI_API_KEY=your-gemini-api-key-here  # Optional — works with mock data
```

### Demo Credentials
- **Email:** `demo@pmbrain.ai`
- **Password:** `demo1234`
- **Organization:** Acme SaaS
- **Project:** Acme CRM (with 15 evidence items, 4 insights, 3 opportunities)

---

## 🎯 Demo Flow

1. **Login** → `demo@pmbrain.ai` / `demo1234`
2. **Dashboard** → See metrics, pipeline, top insights
3. **Evidence** → View 15 pre-loaded customer feedback items
4. **Run AI Pipeline** → Click "⚡ Run AI Pipeline" button
5. **Insights** → See AI-clustered pain points
6. **Opportunities** → View scored opportunities
7. **What to Build** → Ask "What should we build next for our CRM?"
8. **Generate Spec** → Click on opportunity → "Generate Spec"
9. **Review Spec** → View PRD with user stories, tasks, QA checklist
10. **Chat with AI** → Edit spec conversationally
11. **Approve** → Move through draft → review → approved → shipped

---

## 🔧 Gemini AI Integration

### With API Key
Set `GEMINI_API_KEY` in `.env` to use real Gemini AI responses.

### Without API Key (Demo Mode)
The system includes intelligent mock responses that simulate realistic AI outputs for every agent type. The demo is fully functional without an API key.

### Mock Response Quality
Mock responses include:
- Realistic evidence summaries with pain points
- Multi-cluster insight generation
- Scored opportunity discovery
- Complete PRD generation with user stories, tasks, QA
- Impact predictions with confidence scores

---

## 🔒 Security Features

1. **JWT authentication** on all API endpoints
2. **Role-based permissions** (org-owner, product-manager, engineer, reviewer)
3. **Multi-tenant data isolation** — middleware filters by organization
4. **Audit trail** — every mutation logged with actor, timestamp, IP
5. **CORS protection** — configurable allowed origins
6. **CSRF protection** — Django middleware enabled

---

## 📡 Real-Time Updates (WebSocket)

### Connection
```javascript
ws://host/ws/project/<project_id>/
```

### Message Types
- `agent_update` — AI job completed/failed
- `insight_update` — New insights generated
- `opportunity_update` — Opportunity scored/status changed
- `spec_update` — Spec generated/edited
- `notification` — User notification

---
