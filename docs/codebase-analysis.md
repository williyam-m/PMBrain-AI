# Codebase Analysis Feature Documentation

## Overview

PMBrain AI now supports **uploading and analyzing product codebases** so the AI can combine:
- Customer evidence
- Insight clusters
- Opportunities
- **Actual product code**
- **Market trends**

to generate **better, code-aware feature recommendations**.

## Architecture

### New Django App: `apps/codebase/`

```
apps/codebase/
├── __init__.py
├── apps.py
├── models.py          # Codebase, CodebaseAnalysis, MarketTrend, FeatureDiscovery
├── serializers.py     # DRF serializers
├── views.py           # Upload, analyze, trend, discovery endpoints
├── urls.py            # URL routing
└── migrations/
    └── 0001_initial.py
```

### Models

#### `Codebase`
- **name**: Name of the uploaded codebase
- **source_type**: `zip` | `tar` | `git`
- **storage_path**: Local path to extracted files
- **file_size_bytes**: Archive size
- **file_count**: Number of files extracted

#### `CodebaseAnalysis`
AI-generated analysis results:
- **system_summary**: Natural language description of the system
- **major_modules**: List of modules with names, purposes, dependencies
- **existing_features**: Features identified in the code
- **api_endpoints**: API routes discovered
- **database_models**: Data models found
- **capability_map**: What the system can do
- **technology_stack**: Languages, frameworks, tools
- **architecture_patterns**: MVC, REST, etc.

#### `MarketTrend`
- **trend_summary**: Market landscape overview
- **emerging_features**: What's new in the market
- **competitor_features**: What competitors have
- **market_gap_opportunities**: Where gaps exist

#### `FeatureDiscovery`
Combined analysis results:
- **feature_name**: Discovered feature
- **problem_statement**: What problem it solves
- **evidence_links**: References to customer evidence
- **code_integration_points**: Where in the codebase it fits
- **implementation_complexity**: low | medium | high | very_high
- **execution_plan**: Step-by-step implementation
- **expected_impact**: Revenue, retention, engagement estimates
- **trend_alignment**: Which market trends it aligns with
- **source_type**: evidence | code | trend | combined

## API Endpoints

### Codebase Management
```
POST   /api/codebase/codebases/upload/     Upload zip/tar.gz
GET    /api/codebase/codebases/            List codebases
POST   /api/codebase/codebases/{id}/analyze/  Trigger AI analysis
```

### Analysis Results
```
GET    /api/codebase/analyses/             List analyses
GET    /api/codebase/analyses/{id}/        Get analysis detail
```

### Market Trends
```
GET    /api/codebase/trends/               List trend analyses
POST   /api/codebase/trends/generate/      Generate new analysis
```

### Feature Discovery
```
GET    /api/codebase/features/             List discovered features
POST   /api/codebase/features/discover/    Run AI feature discovery
```

## Security

### Upload Security
1. **File size limit**: Configurable via `MAX_CODEBASE_SIZE_MB` (default: 100MB)
2. **Path traversal prevention**: Archives are scanned for `..` paths before extraction
3. **No code execution**: Only static analysis is performed
4. **Binary file exclusion**: .exe, .dll, .so, etc. are skipped
5. **Directory exclusion**: node_modules, .git, venv, etc. are skipped

### Analysis Security
- Code files are read but never executed
- Maximum 200 files analyzed per codebase
- Maximum 100KB per file
- Content truncated to 5KB per file for AI prompts

## Upload Flow

```
1. User uploads .zip or .tar.gz file
2. Server validates:
   - File size ≤ 100MB
   - Valid archive format
   - No path traversal in entries
3. Archive extracted to media/codebases/{uuid}/source/
4. Codebase record created in database
5. User triggers analysis
6. CodeUnderstandingAgent:
   - Walks file tree (skips binaries, node_modules, etc.)
   - Reads code files (≤100KB each)
   - Sends file structure + code samples to Gemini
   - Stores structured analysis results
```

## AI Integration

### CodeUnderstandingAgent
Uses `CODE_UNDERSTANDING_PROMPT` to analyze:
- File structure and directory layout
- Code content from key files
- Product context from project settings

Returns structured JSON with modules, features, APIs, models, capabilities.

### MarketTrendAgent
Uses `MARKET_TREND_PROMPT` to analyze:
- Current SaaS industry trends
- Competitor landscape
- Emerging technologies
- Market gaps

### FeatureDiscoveryAgent
Uses `FEATURE_DISCOVERY_PROMPT` combining:
- All evidence summaries
- Insight clusters
- Existing opportunities
- Codebase analysis results
- Market trend data

## Enhanced "What to Build"

The `WhatToBuildAgent` now considers:
1. Customer evidence and insights
2. Scored opportunities
3. **Codebase capabilities** (if analysis exists)
4. **Market trends** (if analysis exists)

The response includes:
- `trend_alignment`: How the recommendation aligns with market trends
- `code_integration_points`: Where in the existing codebase to implement
- `execution_plan`: Detailed plan considering existing code
