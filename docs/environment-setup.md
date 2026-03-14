# Environment Setup Guide

## Overview

PMBrain AI uses environment variables for all sensitive configuration. **Never commit secrets to version control.**

---

## Quick Start

### 1. Create your `.env` file

```bash
cp .env.example .env
```

### 2. Configure required variables

Edit `.env` and set your values:

```env
# Django (required)
SECRET_KEY=your-unique-secret-key-here
DEBUG=True
ALLOWED_HOSTS=*

# Gemini AI (required for AI features)
GEMINI_API_KEY=your-gemini-api-key-here
```

### 3. Get your Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Click **"Create API Key"**
3. Copy the key and paste it into your `.env` file
4. **Never share or commit this key**

---

## All Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | `pmbrain-dev-secret-key` | Django secret key — **change in production** |
| `DEBUG` | No | `True` | Enable debug mode |
| `ALLOWED_HOSTS` | No | `*` | Comma-separated allowed hosts |
| `DATABASE_URL` | No | `sqlite:///db.sqlite3` | Database connection string |
| `CORS_ALLOWED_ORIGINS` | No | `localhost:8080` | CORS allowed origins |
| `GEMINI_API_KEY` | Yes | *(none)* | Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-2.5-flash-lite` | Primary Gemini model |
| `GEMINI_FALLBACK_MODEL` | No | `gemini-flash-lite-latest` | Fallback model |
| `GEMINI_MAX_RETRIES` | No | `3` | Max API retry attempts |
| `GEMINI_TIMEOUT` | No | `60` | API timeout in seconds |
| `MAX_CODEBASE_SIZE_MB` | No | `100` | Max upload size for codebases |
| `CODEBASE_STORAGE_PATH` | No | `media/codebases` | Codebase file storage path |
| `GITHUB_CLIENT_ID` | No | *(none)* | GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | No | *(none)* | GitHub OAuth App client secret |
| `GITHUB_REDIRECT_URI` | No | *(none)* | GitHub OAuth redirect URI |
| `GITHUB_ENCRYPTION_KEY` | No | *(auto from SECRET_KEY)* | Token encryption key |
| `MAX_GITHUB_REPO_SIZE_MB` | No | `200` | Max GitHub repo clone size |
| `GITHUB_CLONE_TIMEOUT` | No | `120` | Clone timeout in seconds |

---

## Security Rules

### ⛔ NEVER do this:
```python
# WRONG — hardcoded secret
API_KEY = "AIzaSy..."
```

### ✅ ALWAYS do this:
```python
# CORRECT — loaded from environment
import os
API_KEY = os.getenv("GEMINI_API_KEY", "")
```

### Git Safety

The `.gitignore` file blocks these from being committed:
```
.env
.env.local
.env.*.local
.env.production
.env.staging
```

The `.env.example` file **is** tracked — it contains only placeholder values as a safe template.

---

## What to do if a secret is accidentally committed

1. **Revoke the key immediately** at the provider (Google AI Studio, GitHub, etc.)
2. Remove the secret from the codebase
3. Purge from git history:
   ```bash
   echo 'EXPOSED_KEY==>REMOVED_SECRET' > /tmp/replacements.txt
   python3 -m git_filter_repo --replace-text /tmp/replacements.txt --force
   ```
4. Force push the cleaned history:
   ```bash
   git remote add origin <your-remote-url>
   git push origin --force --all
   ```
5. Clean up local references:
   ```bash
   rm -rf .git/refs/original/
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   ```
6. Generate a **new key** and add it to `.env`
7. Notify your team to re-clone the repository

---

## Verification

Confirm no secrets exist in the repository:

```bash
# Check working tree
git grep "AIzaSy"

# Check all history
git log -S "AIzaSy" --oneline --all

# Both should return NO results
```
