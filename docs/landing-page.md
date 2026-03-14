# PMBrain AI — Landing Page Architecture

## Route Structure (Updated)

| Route | Target | Purpose |
|-------|--------|---------|
| `/` | `landing.html` | Marketing homepage (landing page) |
| `/signin` | `index.html` | Login page (auto-detects signin mode) |
| `/signup` | `index.html` | Registration page (auto-detects signup mode) |
| `/dashboard` | `index.html` | Authenticated application |
| `/landing/` | `landing.html` | Legacy backward-compatible route |

## Authentication-Based Button Behavior

The landing page checks `localStorage.pmbrain_token`:

- **Logged in**: Shows "Access PMBrain AI →" button pointing to `/dashboard`
- **Not logged in**: Shows "Sign In" → `/signin` and "Start Free →" → `/signup`

## Landing Page Sections

1. **Hero** — Gradient text, floating orbs, 3D grid, auth-aware CTAs
2. **AI Intelligence Loop** — 6-node circular visualization (fixed positioning)
3. **Feature Grid** — 6 hover-animated capability cards
4. **Codebase Intelligence** — Split layout with animated dark flow diagram
5. **AI Insights Demo** — macOS-style window with live score bars
6. **CTA Section** — Dark gradient with floating orbs
7. **Footer** — Logo + nav links

## AI Provider Mentions Removed

The hero section no longer displays:
- "6 AI Agents"
- "100% Live Gemini AI"
- "∞ Evidence Sources"

Replaced with vendor-neutral product capability messaging:
- "🤖 Autonomous Product Intelligence"
- "🔍 Continuous Insight Discovery"
- "🎯 AI-Powered Strategy Engine"

## AI Loop Fix

Nodes are positioned using explicit CSS classes (`.loop-pos-1` through `.loop-pos-6`) in clockwise order:

```
1. Customer Evidence (12 o'clock)
2. AI Insights (2 o'clock)
3. Opportunities (4 o'clock)
4. Execution Specs (6 o'clock)
5. Product Release (8 o'clock)
6. Performance Data (10 o'clock)
```

## Technical Details

- **No frameworks** — Pure Vanilla JS + CSS
- **GPU-accelerated animations** — Only `transform`/`opacity`/`filter` animated
- **Responsive** — 3 breakpoints (1024px, 768px, 480px)
- **Lazy animations** — IntersectionObserver reveals on scroll
