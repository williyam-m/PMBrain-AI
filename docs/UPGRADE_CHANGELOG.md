# PMBrain AI — Upgrade Changelog

## Summary of All Changes

This document details every change made during the system upgrade.

---

## 1. Gemini AI Integration — Real API, No Mocks

### Changed: `apps/ai_agents/services/gemini_client.py`
- **REMOVED**: All `_mock_*` methods (evidence, insights, opportunities, scoring, specs, what-to-build, impact)
- **REMOVED**: Old `google.generativeai` SDK dependency (incompatible with Python 3.8)
- **ADDED**: Direct REST API integration via `requests` library
- **ADDED**: Model failover: `gemini-2.5-flash-lite` → `gemini-flash-lite-latest`
- **ADDED**: Retry logic with configurable `GEMINI_MAX_RETRIES`
- **ADDED**: Exponential backoff for rate limits (429 errors)
- **ADDED**: `generate_streaming()` method for real-time output
- **ADDED**: JSON response parsing with markdown fence removal
- **ADDED**: Detailed logging of every API call (model, duration, tokens)
- **ADDED**: `GeminiAPIError` exception class

### Changed: `.env`
- **SET**: `GEMINI_API_KEY=<your-api-key>` *(loaded from environment variable — never commit real keys)*
- **ADDED**: `GEMINI_MODEL=gemini-2.5-flash-lite`
- **ADDED**: `GEMINI_FALLBACK_MODEL=gemini-flash-lite-latest`
- **ADDED**: `GEMINI_MAX_RETRIES=3`
- **ADDED**: `GEMINI_TIMEOUT=60`

### Changed: `pmbrain/settings.py`
- **ADDED**: `GEMINI_MODEL`, `GEMINI_FALLBACK_MODEL`, `GEMINI_MAX_RETRIES`, `GEMINI_TIMEOUT` settings
- **ADDED**: `MAX_CODEBASE_SIZE_MB`, `CODEBASE_STORAGE_PATH` settings
- **ADDED**: `DATA_UPLOAD_MAX_MEMORY_SIZE`, `FILE_UPLOAD_MAX_MEMORY_SIZE`

---

## 2. Removed All Demo/Placeholder Data

### Changed: `frontend/js/app.js`
- **REMOVED**: Pre-filled `value="demo@pmbrain.ai"` from login email input
- **REMOVED**: Pre-filled `value="demo1234"` from login password input
- **REMOVED**: "Demo: demo@pmbrain.ai / demo1234" text from login page

### Note
- The `seed_demo.py` management command still exists for development convenience
- Seeded data in the database is preserved (it's real data, not UI placeholders)

---

## 3. Authorization Fix

### Changed: `apps/accounts/views.py`
- **ADDED**: `_setup_default_org()` method to `RegisterView`
- New users now automatically get:
  - An Organization (named from user or defaults to "User's Workspace")
  - An OrgMembership (role: org-owner)
  - A default Project (named "My Product")
- Registration response now includes `organization` data

### Changed: `apps/ai_agents/views.py`
- **ADDED**: `_validate_project_access()` helper function for consistent auth checks
- **FIXED**: `WhatToBuildView` and `RunAgentView` now use centralized auth validation
- **IMPROVED**: Error messages are more descriptive ("Not a member of this organization")
- **ADDED**: Import of `OrgMembership` for direct membership queries

---

## 4. New Feature: Codebase Analysis

### New App: `apps/codebase/`
- `models.py`: Codebase, CodebaseAnalysis, MarketTrend, FeatureDiscovery models
- `serializers.py`: DRF serializers for all models
- `views.py`: Upload, analyze, trend, discovery endpoints with security
- `urls.py`: URL routing
- `apps.py`: App config

### Changed: `pmbrain/settings.py`
- **ADDED**: `'apps.codebase'` to `INSTALLED_APPS`

### Changed: `pmbrain/urls.py`
- **ADDED**: `path('api/codebase/', include('apps.codebase.urls'))`

---

## 5. New AI Agents

### New File: `apps/ai_agents/services/prompt_templates.py`
- Centralized all prompt templates for all agents
- 12 prompt templates total

### Changed: `apps/ai_agents/services/agent_orchestrator.py`
- **ADDED**: `CodeUnderstandingAgent` — analyzes uploaded codebases
- **ADDED**: `MarketTrendAgent` — analyzes market trends
- **ADDED**: `FeatureDiscoveryAgent` — discovers features from combined data
- **ENHANCED**: `WhatToBuildAgent` — now considers codebase and market trends
- **ADDED**: New workflows: `analyze_codebase`, `market_trends`, `feature_discovery`, `full_discovery`
- **UPDATED**: Error handling uses `GeminiAPIError` for AI-specific errors

### Changed: `apps/ai_agents/models.py`
- **ADDED**: Agent type choices: `code_understanding`, `market_trend`, `feature_discovery`

### Changed: `apps/ai_agents/serializers.py`
- **ADDED**: Workflow choices: `analyze_codebase`, `market_trends`, `feature_discovery`, `full_discovery`

---

## 6. Frontend Updates

### Changed: `frontend/js/app.js`
- **ADDED**: "Code & Trends" nav section with Codebase and AI Discovery pages
- **ADDED**: `Pages.codebase()` — upload code, view analyses
- **ADDED**: `Pages.featureDiscovery()` — view AI discoveries and market trends
- **ADDED**: `Pages.analyzeCodebase()` — trigger codebase analysis
- **ADDED**: `Pages.showCodeAnalysis()` — modal with analysis results
- **ADDED**: New workflow buttons in Run AI Pipeline modal
- **UPDATED**: Page routing and title mapping

### Changed: `frontend/js/api.js`
- **ADDED**: `uploadCodebase()`, `analyzeCodebase()`, `getCodebaseAnalyses()`, `getCodebaseAnalysis()`
- **ADDED**: `getMarketTrends()`, `generateMarketTrends()`
- **ADDED**: `getFeatureDiscoveries()`, `discoverFeatures()`

---

## 7. Documentation

### New Files:
- `docs/authorization-fix.md` — Authorization fix details
- `docs/codebase-analysis.md` — Codebase analysis feature documentation
- `docs/ai-agent-architecture.md` — Complete AI agent architecture
- `docs/UPGRADE_CHANGELOG.md` — This file

---

## 8. Infrastructure

### Changed: `setup.sh`
- **REMOVED**: Demo credential references
- **ADDED**: Media directory creation (`media/codebases`)
- **UPDATED**: Start message directs users to register

### Database:
- **NEW**: `codebases` table
- **NEW**: `codebase_analyses` table
- **NEW**: `market_trends` table
- **NEW**: `feature_discoveries` table

---

## Files Modified (Summary)

| File | Change Type |
|------|-------------|
| `.env` | Modified (API key + new settings) |
| `pmbrain/settings.py` | Modified (new app + settings) |
| `pmbrain/urls.py` | Modified (codebase routes) |
| `apps/ai_agents/services/gemini_client.py` | **Rewritten** (REST API, no mocks) |
| `apps/ai_agents/services/agent_orchestrator.py` | Modified (3 new agents + enhanced what-to-build) |
| `apps/ai_agents/services/prompt_templates.py` | **New file** |
| `apps/ai_agents/models.py` | Modified (new agent types) |
| `apps/ai_agents/serializers.py` | Modified (new workflows) |
| `apps/ai_agents/views.py` | Modified (auth fix) |
| `apps/accounts/views.py` | Modified (auto-create org) |
| `apps/codebase/*.py` | **New app** (5 files) |
| `frontend/js/app.js` | Modified (new pages, removed demo) |
| `frontend/js/api.js` | Modified (new API methods) |
| `setup.sh` | Modified |
| `docs/*.md` | **New files** (4 docs) |

## Verification

All changes verified with:
1. `python3 manage.py check` — 0 issues
2. `python3 manage.py migrate` — All migrations applied
3. New user registration → org auto-creation → API access → ✅
4. Existing demo user → all data preserved → all endpoints working → ✅
5. All 12 API endpoint categories tested → ✅
6. Frontend loads and renders correctly → ✅
