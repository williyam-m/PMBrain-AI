# Authorization Fix Documentation

## Problem Statement

When a **new user** registered and attempted to call:
```
POST /api/agents/what-to-build/
```
The API returned **403 Not Authorized**, even though the user had a valid JWT token.

### Root Cause

1. **No organization auto-creation**: New users registered without an organization or project being created
2. **Organization-dependent authorization**: The `WhatToBuildView` checked `project.organization.members.filter(user=request.user)` — but new users had no memberships
3. **Frontend assumed org/project existed**: The `loadUserContext()` method in `app.js` would find no orgs/projects, leading to null references

## Solution

### 1. Auto-create organization and project on registration (`apps/accounts/views.py`)

```python
class RegisterView(APIView):
    def post(self, request):
        # ... registration logic ...
        org_data = self._setup_default_org(user, request.data)
        return Response({
            'user': ...,
            'tokens': ...,
            'organization': org_data,  # New: return org info
        })
    
    def _setup_default_org(self, user, data):
        """Creates:
        - Organization (named from user or request data)
        - OrgMembership (role: org-owner)
        - Default Project
        """
```

### 2. Centralized project access validation (`apps/ai_agents/views.py`)

```python
def _validate_project_access(user, project_id):
    """Validates:
    1. Project exists
    2. User is a member of the project's organization
    Returns (project, error_response) tuple
    """
```

### 3. Consistent membership checks

All endpoints now use `OrgMembership.objects.filter()` queries instead of `project.organization.members.filter()` for clarity and consistency.

## Authorization Flow

```
User registers
  → Auto-creates Organization (role: org-owner)
  → Auto-creates Default Project
  → Returns JWT tokens + org info

User calls /api/agents/what-to-build/
  → JWT validated
  → Project looked up
  → OrgMembership checked (user ↔ project.organization)
  → Access granted
```

## Roles & Permissions

| Role | What to Build | Run Agents | Create Evidence | Generate Specs |
|------|--------------|------------|-----------------|----------------|
| org-owner | ✅ | ✅ | ✅ | ✅ |
| product-manager | ✅ | ✅ | ✅ | ✅ |
| engineer | ✅ | ✅ | ✅ | ❌ |
| reviewer | ✅ | ❌ | ❌ | ❌ |

## Security Notes

- Authorization is NOT bypassed — proper membership validation is enforced
- Multi-tenant isolation is preserved via `TenantQuerySetMixin`
- All data queries filter by organization membership
- Slug uniqueness enforced for organization names
