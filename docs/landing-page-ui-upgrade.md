# PMBrain AI — Landing Page & AI Response UI Upgrade

## Overview

This document covers the production UI upgrade that adds a modern, animated landing page and enhanced AI response visualization to PMBrain AI.

## Architecture

### File Structure
```
frontend/
├── landing/                        # NEW — Landing page assets
│   ├── landing.css                 # 3D animated landing page styles
│   ├── landing.js                  # Landing page logic + rendering
│   ├── animations.js               # IntersectionObserver + parallax
│   └── components/
│       ├── flowchart.js            # Reusable flowchart renderer
│       └── scoregraph.js           # Reusable score graph renderer
├── css/
│   └── styles.css                  # Enhanced with AI response styles
├── js/
│   ├── app.js                      # Enhanced recommendation rendering
│   ├── api.js                      # Unchanged
│   ├── settings-page.js            # Unchanged
│   └── websocket.js                # Unchanged
templates/
├── landing.html                    # NEW — Landing page template
└── index.html                      # Updated — includes components
```

### Routes
| Route | Template | Purpose |
|-------|----------|---------|
| `/landing/` | `landing.html` | Marketing landing page |
| `/` | `index.html` | Main application (login/dashboard) |

## Landing Page Sections

### 1. Hero Section
- Large animated headline with gradient text
- Floating gradient orbs (GPU-accelerated CSS)
- Rotating perspective grid
- Authentication-aware CTA buttons
- Social proof metrics

### 2. AI Intelligence Loop
- Dark-themed section
- 6-node circular visualization
- SVG animated dashed arrows
- Central glowing PMBrain AI brain
- Hover-activated nodes

### 3. Feature Grid
- 6 feature cards with hover animations
- Top-border gradient reveal on hover
- Icon scale + rotate animations
- Tag chips per feature
- 3-column responsive grid

### 4. Codebase Intelligence
- Split layout: text + animated diagram
- 4-step dark-themed flow diagram
- Nodes animate in with stagger
- Hover slide-right effect

### 5. AI Insights Demo
- macOS-style window frame
- Score graph with animated fill bars
- Evidence quote cards
- Execution flowchart (using component)
- Score breakdown visualization

### 6. CTA Section
- Dark gradient background
- Floating orbs
- Large headline + action button

### 7. Footer
- Logo + navigation links

## Authentication-Aware Buttons

```javascript
if (user_is_logged_in) {
    // Shows: "Access PMBrain AI" / "Open Dashboard"
    showButton("Access PMBrain AI")
} else {
    // Shows: "Sign In" + "Start Free"
    showButtons("Sign In", "Start Free")
}
```

Token check: `localStorage.getItem('pmbrain_token')`

When "Start Free" is clicked, sets `sessionStorage.pmbrain_auth_mode = 'signup'` so the main app shows the registration form.

## 3D Animation Techniques

| Technique | CSS Property | Used In |
|-----------|-------------|---------|
| Floating orbs | `filter: blur()` + `animation` | Hero, CTA |
| Perspective grid | `transform: perspective() rotateX()` | Hero |
| Scroll reveal | `IntersectionObserver` | All sections |
| Parallax orbs | `transform: translateY()` via JS | Hero |
| Score bar fill | `transition: width` + `data-width` | Demo, AI results |
| Stagger children | `transition-delay` via nth-child | Feature grid |
| Node hover glow | `box-shadow` + `transform: scale()` | AI loop |

All animations use `will-change: transform` and GPU-accelerated properties for 60fps performance.

## Enhanced AI Response Visualization

### Recommendation Card (Enhanced)
- Gradient background with glow effect
- Score ring (circular)
- Trend alignment badge
- Confidence + evidence count metadata

### Score Graph Component
```javascript
ScoreGraphRenderer.renderBreakdown(container, {
    frequency: 8.5,
    revenue_impact: 7.2,
    retention_impact: 9.0,
    strategic_alignment: 8.8
});
```
- Animated fill bars with color-coding
- High (green), Medium (yellow), Low (red)
- IntersectionObserver triggers animation on scroll

### Flowchart Component
```javascript
FlowchartRenderer.renderExecutionPlan(container, [
    { phase: 'Backend API', tasks: 3, estimate: '2 weeks' },
    { phase: 'Frontend Build', tasks: 5, estimate: '3 weeks' }
]);
```
- Vertical connected nodes with arrows
- Hover scale effect
- Phase metadata (estimate, task count)

### Task Cards (Expandable)
- Click-to-expand pattern
- Priority badges (P0 = red, P1 = yellow)
- Dependency chips
- Estimate tags

### Code Integration Points
- Purple pill badges
- Shows affected modules from codebase analysis

## Responsive Breakpoints

| Breakpoint | Changes |
|-----------|---------|
| `> 1024px` | Full 3-column grid, side-by-side layouts |
| `768-1024px` | 2-column grid, stacked code intel |
| `< 768px` | Single column, hidden nav links, stacked hero buttons |
| `< 480px` | Full-width buttons, minimal nav |

Animations degrade gracefully — heavy effects disabled on mobile via media queries.

## Performance

- **No external libraries** — pure CSS + Vanilla JS
- **Lazy animation** — IntersectionObserver triggers only when visible
- **GPU-accelerated** — only `transform`, `opacity`, `filter` animated
- **Compressed** — WhiteNoise gzip compression on all static files
- **Score bars** — `data-width` attribute + transition (no JS animation loop)

## Security

- No sensitive data on landing page
- Auth token checked but never exposed
- No API calls from landing page
- All links use relative paths

## Zero Breakage Verification

All existing endpoints return 200:
- Dashboard, Evidence, Insights, Opportunities
- Codebases, GitHub Integration
- Auth (login, register, token refresh)
- All WebSocket connections
- All navigation routes in the SPA
