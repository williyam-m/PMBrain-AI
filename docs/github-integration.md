# GitHub Integration — PMBrain AI

## Overview

PMBrain AI now supports **GitHub repository integration**, allowing users to connect their GitHub accounts, link repositories to projects, and trigger AI-powered codebase analysis.

This enables the system to answer:
> "Given our GitHub repository, customer feedback, and market trends — what feature should we build next?"

---

## Architecture

```
User → Connect GitHub (OAuth or PAT)
     → Link Repository URL
     → System validates access via GitHub API
     → Repository metadata stored
     → Shallow clone (read-only, depth=1)
     → Code extracted for static analysis
     → Codebase record created
     → CodeUnderstandingAgent runs via Gemini AI
     → Analysis stored in CodebaseAnalysis
     → Used in WhatToBuild recommendations
```

---

## OAuth Flow

### Standard OAuth (requires GitHub OAuth App)
1. User clicks "Connect GitHub"
2. Frontend calls `POST /api/integrations/github/connect/`
3. Backend returns GitHub OAuth authorization URL
4. User authorizes on GitHub
5. GitHub redirects to `GET /api/integrations/github/callback/`
6. Backend exchanges code for access token
7. Token is **encrypted** and stored

### Personal Access Token (simpler, for demos)
1. User generates PAT at github.com/settings/tokens
2. Calls `POST /api/integrations/github/connect-token/`
3. Backend validates token via GitHub API
4. Token is **encrypted** and stored

---

## Token Security

- Access tokens are **encrypted at rest** using Fernet symmetric encryption
- Encryption key derived from `SECRET_KEY` or custom `GITHUB_ENCRYPTION_KEY`
- Tokens are **never exposed** in any API response
- The `GitHubIntegrationSerializer` explicitly excludes token fields
- Clone URLs with tokens are constructed server-side only

---

## Repository Linking

### Validation Flow
1. Parse URL → extract owner/repo
2. Call GitHub API to verify repo exists
3. Confirm user has read access
4. Check for duplicate links
5. Store repository metadata
6. Create `GitHubRepository` record

### Supported URL Formats
```
https://github.com/owner/repo
https://github.com/owner/repo.git
https://github.com/owner/repo/
```

---

## Repository Cloning

### Strategy
- **Shallow clone** (`--depth 1`, `--single-branch`) for efficiency
- Read-only: no push, no code execution
- `.git` directory removed after clone
- Maximum repo size: 200MB (configurable)
- Clone timeout: 120s (configurable)

### Storage
```
/storage/repos/{organization_id}/{project_id}/{repo_name}/
```

### Security
- `GIT_TERMINAL_PROMPT=0` prevents credential prompts
- Path traversal prevention
- Binary file exclusion
- File size limits per file (100KB for analysis)
- Maximum 200 files analyzed

---

## AI Analysis Pipeline

```
GitHub Repo Connected
    ↓
clone_repository() — shallow, read-only
    ↓
extract_code_info() — file structure + code samples
    ↓
create_codebase_from_repo() — Codebase model record
    ↓
CodeUnderstandingAgent → Gemini AI
    ↓
CodebaseAnalysis record with:
  - system_summary
  - major_modules
  - existing_features
  - api_endpoints
  - database_models
  - capability_map
  - technology_stack
  - architecture_patterns
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/integrations/github/connect/` | Start OAuth flow |
| `GET` | `/api/integrations/github/callback/` | OAuth callback |
| `POST` | `/api/integrations/github/connect-token/` | Connect via PAT |
| `GET` | `/api/integrations/github/status/` | Check connection status |
| `POST` | `/api/integrations/github/disconnect/` | Disconnect GitHub |
| `GET` | `/api/integrations/github/repos/` | List accessible repos |
| `POST` | `/api/integrations/github/link-repo/` | Link repo to project |
| `GET` | `/api/integrations/github/linked-repos/` | List linked repos |
| `POST` | `/api/integrations/github/analyze-repo/` | Clone + analyze |
| `POST` | `/api/integrations/github/unlink-repo/` | Unlink repo |

---

## Models

### GitHubIntegration
| Field | Type | Description |
|-------|------|-------------|
| organization | FK | Multi-tenant scope |
| user | FK | GitHub-connected user |
| github_user_id | BigInt | GitHub user ID |
| github_username | Char | GitHub login |
| avatar_url | URL | GitHub avatar |
| _access_token | Binary | Fernet-encrypted token |
| scopes | Char | OAuth scopes granted |
| is_active | Bool | Active connection |

### GitHubRepository
| Field | Type | Description |
|-------|------|-------------|
| integration | FK | Parent integration |
| github_repo_id | BigInt | GitHub repo ID |
| repo_name | Char | Repository name |
| repo_full_name | Char | owner/repo |
| repo_url | URL | GitHub URL |
| default_branch | Char | Main branch |
| clone_status | Char | pending/cloning/completed/failed |
| clone_path | Char | Local path |
| codebase | FK | Linked Codebase record |

---

## Audit Events

All GitHub actions create audit events:
- `github_connected` — OAuth or PAT connection
- `github_disconnected` — Disconnection
- `github_repo_linked` — Repository linked
- `github_repo_analyzed` — Analysis triggered
- `github_repo_unlinked` — Repository unlinked

---

## Configuration

### Environment Variables
```
GITHUB_CLIENT_ID=       # For OAuth flow
GITHUB_CLIENT_SECRET=   # For OAuth flow
GITHUB_REDIRECT_URI=    # OAuth callback URL
GITHUB_ENCRYPTION_KEY=  # Token encryption (auto-gen if blank)
MAX_GITHUB_REPO_SIZE_MB=200
GITHUB_CLONE_TIMEOUT=120
```

---

## Testing

14 automated tests cover:
- URL parsing (standard, .git suffix, trailing slash, invalid)
- Token encryption/decryption roundtrip
- Token not stored in plaintext
- Unauthenticated access rejection
- Cross-organization isolation
- Repository linking success
- Duplicate link prevention
- Invalid URL rejection

Run: `python3 manage.py test apps.github_integration`
