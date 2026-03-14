/**
 * PMBrain AI - Landing Page
 * 3D Animated YC-Startup Landing
 * Vanilla JS + Pure CSS
 *
 * Route: / (homepage)
 * Auth: /signin, /signup
 * App: /dashboard
 */

var Landing = {
    isLoggedIn: false,

    init: function() {
        this.checkAuth();
        this.render();
        LandingAnimations.init();
    },

    checkAuth: function() {
        var token = localStorage.getItem('pmbrain_token');
        this.isLoggedIn = !!token;
    },

    render: function() {
        var root = document.getElementById('landing-root');
        if (!root) return;
        root.innerHTML = [
            this.renderNav(),
            this.renderHero(),
            this.renderAILoop(),
            this.renderFeatures(),
            this.renderCodeIntel(),
            this.renderInsightsDemo(),
            this.renderCTA(),
            this.renderFooter()
        ].join('');
        this.bindEvents();
    },

    renderNav: function() {
        var authBtns = this.isLoggedIn
            ? '<a class="nav-btn nav-btn-primary" href="/dashboard">Access PMBrain AI \u2192</a>'
            : '<a class="nav-btn nav-btn-ghost" href="/signin">Sign In</a><a class="nav-btn nav-btn-primary" href="/signup">Start Free \u2192</a>';
        return '<nav class="landing-nav" id="landing-nav">'
            + '<a class="nav-logo" href="/"><div class="nav-logo-icon">\uD83E\uDDE0</div><div class="nav-logo-text">PM<span>Brain</span> AI</div></a>'
            + '<div class="nav-links"><a class="nav-link" href="#features">Features</a><a class="nav-link" href="#code-intel">Code Analysis</a><a class="nav-link" href="#demo">Demo</a>' + authBtns + '</div></nav>';
    },

    renderHero: function() {
        var heroBtn = this.isLoggedIn
            ? '<a class="hero-btn hero-btn-primary" href="/dashboard">Open Dashboard \u2192</a>'
            : '<a class="hero-btn hero-btn-primary" href="/signup">Get Started Free \u2192</a>';
        return '<section class="hero">'
            + '<div class="hero-bg-canvas"><div class="hero-orb hero-orb-1"></div><div class="hero-orb hero-orb-2"></div><div class="hero-orb hero-orb-3"></div><div class="hero-grid"></div></div>'
            + '<div class="hero-content">'
            + '<div class="hero-eyebrow"><span class="pulse-dot"></span>AI-Powered Product Intelligence</div>'
            + '<h1 class="hero-title"><span class="gradient-text">Autonomous AI</span><br>for Product Managers</h1>'
            + '<p class="hero-subtitle">PMBrain AI continuously analyzes customer evidence, product usage, and your codebase to recommend what your team should build next \u2014 with citations and confidence scores.</p>'
            + '<div class="hero-actions">' + heroBtn + '<a class="hero-btn hero-btn-secondary" href="#demo">See How It Works</a></div>'
            + '<div class="hero-social-proof">'
            + '<div class="social-proof-item"><span class="number">\uD83E\uDD16</span> Autonomous Product Intelligence</div>'
            + '<div class="social-proof-item"><span class="number">\uD83D\uDD0D</span> Continuous Insight Discovery</div>'
            + '<div class="social-proof-item"><span class="number">\uD83C\uDFAF</span> AI-Powered Strategy Engine</div>'
            + '</div></div></section>';
    },

    renderAILoop: function() {
        return '<section class="section section-dark" id="ai-loop"><div class="container">'
            + '<div class="section-header"><div class="section-eyebrow">\u26A1 THE INTELLIGENCE LOOP</div>'
            + '<h2 class="section-title fade-in-up">Autonomous Product<br>Intelligence Cycle</h2>'
            + '<p class="section-desc fade-in-up">PMBrain AI runs a continuous loop \u2014 collecting evidence, finding patterns, discovering opportunities, and generating actionable specs.</p></div>'
            + '<div class="ai-loop-wrapper fade-in-up"><div class="ai-loop-ring" id="ai-loop-ring">'
            + '<svg class="loop-svg" viewBox="0 0 500 500"><circle cx="250" cy="250" r="195" class="loop-arrow-bg"/><circle cx="250" cy="250" r="195" class="loop-arrow"/></svg>'
            + '<div class="loop-node loop-pos-1"><span class="loop-node-icon">\uD83D\uDCCB</span><span class="loop-node-label">Customer Evidence</span></div>'
            + '<div class="loop-node loop-pos-2"><span class="loop-node-icon">\uD83D\uDCA1</span><span class="loop-node-label">AI Insights</span></div>'
            + '<div class="loop-node loop-pos-3"><span class="loop-node-icon">\uD83C\uDFAF</span><span class="loop-node-label">Opportunities</span></div>'
            + '<div class="loop-node loop-pos-4"><span class="loop-node-icon">\uD83D\uDCC4</span><span class="loop-node-label">Execution Specs</span></div>'
            + '<div class="loop-node loop-pos-5"><span class="loop-node-icon">\uD83D\uDE80</span><span class="loop-node-label">Product Release</span></div>'
            + '<div class="loop-node loop-pos-6"><span class="loop-node-icon">\uD83D\uDCCA</span><span class="loop-node-label">Performance Data</span></div>'
            + '<div class="loop-center"><span class="loop-center-icon">\uD83E\uDDE0</span><span class="loop-center-text">PMBrain AI</span></div>'
            + '</div></div></div></section>';
    },

    renderFeatures: function() {
        var features = [
            { icon: '\uD83E\uDD16', title: 'Autonomous AI for Product Managers', desc: 'AI continuously analyzes feedback, analytics, and product signals to discover what teams should build next. No manual analysis required.', tags: ['Autonomous', 'Real-time', 'AI-Driven'] },
            { icon: '\uD83D\uDCCB', title: 'Customer Evidence Intelligence', desc: 'Automatically aggregate and analyze customer interviews, support tickets, feature requests, churn feedback, and NPS signals.', tags: ['NPS', 'Support Tickets', 'Interviews', 'Churn'] },
            { icon: '\uD83D\uDCA1', title: 'Insight Clustering Engine', desc: 'PMBrain detects recurring pain points across all your evidence and identifies product opportunities you might have missed.', tags: ['Pattern Detection', 'Clustering', 'Severity'] },
            { icon: '\uD83C\uDFAF', title: 'Opportunity Prioritization', desc: 'Each opportunity is ranked using AI-driven impact scoring across frequency, revenue impact, retention, strategic alignment, and effort.', tags: ['Scoring', 'Prioritization', 'Impact'] },
            { icon: '\uD83D\uDCBB', title: 'Codebase Analysis', desc: 'PMBrain analyzes your product codebase \u2014 architecture, capabilities, and missing features \u2014 then suggests aligned improvements.', tags: ['GitHub', 'Code Analysis', 'Architecture'] },
            { icon: '\uD83D\uDCCA', title: 'Market Trend Intelligence', desc: 'AI scans market trends, competitor features, and emerging SaaS patterns to find gap opportunities for your product.', tags: ['Trends', 'Competitors', 'Market Gaps'] }
        ];
        var cards = features.map(function(f) {
            var tagHtml = f.tags.map(function(t) { return '<span class="feature-tag">' + t + '</span>'; }).join('');
            return '<div class="feature-card fade-in-up"><div class="feature-icon"><span>' + f.icon + '</span></div><h3 class="feature-title">' + f.title + '</h3><p class="feature-desc">' + f.desc + '</p><div class="feature-tags">' + tagHtml + '</div></div>';
        }).join('');
        return '<section class="section section-gradient" id="features"><div class="container">'
            + '<div class="section-header"><div class="section-eyebrow">\u2728 CAPABILITIES</div>'
            + '<h2 class="section-title fade-in-up">Everything You Need to<br>Decide What to Build</h2>'
            + '<p class="section-desc fade-in-up">AI agents work together to transform raw signals into confident build recommendations.</p></div>'
            + '<div class="features-grid stagger-children">' + cards + '</div></div></section>';
    },

    renderCodeIntel: function() {
        return '<section class="section" id="code-intel"><div class="container"><div class="code-intel-visual">'
            + '<div class="code-intel-text fade-in-up"><div class="section-eyebrow">\uD83D\uDCBB CODEBASE INTELLIGENCE</div>'
            + '<h3>Upload Your Codebase.<br>AI Understands Your Product.</h3>'
            + '<p>Connect your GitHub repository or upload a code archive. PMBrain AI performs deep static analysis to map your product\'s architecture and capabilities \u2014 then recommends features aligned with market needs.</p>'
            + '<ul class="code-intel-list">'
            + '<li><span class="check-icon">\u2713</span> Architecture & framework detection</li>'
            + '<li><span class="check-icon">\u2713</span> API endpoint mapping</li>'
            + '<li><span class="check-icon">\u2713</span> Data model analysis</li>'
            + '<li><span class="check-icon">\u2713</span> Feature capability mapping</li>'
            + '<li><span class="check-icon">\u2713</span> Missing capability identification</li>'
            + '<li><span class="check-icon">\u2713</span> GitHub integration</li></ul></div>'
            + '<div class="code-diagram fade-in-up" id="code-diagram"><div class="diagram-flow">'
            + '<div class="diagram-node"><div class="diagram-node-icon" style="background:rgba(37,99,235,0.2)">\uD83D\uDC19</div><div class="diagram-node-text"><div class="diagram-node-title">GitHub Repository</div><div class="diagram-node-desc">Connect or upload your codebase</div></div></div><div class="diagram-connector"></div>'
            + '<div class="diagram-node"><div class="diagram-node-icon" style="background:rgba(124,58,237,0.2)">\uD83D\uDD2C</div><div class="diagram-node-text"><div class="diagram-node-title">AI Code Analysis</div><div class="diagram-node-desc">Deep static analysis engine</div></div></div><div class="diagram-connector"></div>'
            + '<div class="diagram-node"><div class="diagram-node-icon" style="background:rgba(16,185,129,0.2)">\uD83D\uDDFA\uFE0F</div><div class="diagram-node-text"><div class="diagram-node-title">Capability Map</div><div class="diagram-node-desc">Features, APIs, models, patterns</div></div></div><div class="diagram-connector"></div>'
            + '<div class="diagram-node"><div class="diagram-node-icon" style="background:rgba(245,158,11,0.2)">\uD83D\uDC8E</div><div class="diagram-node-text"><div class="diagram-node-title">Feature Opportunities</div><div class="diagram-node-desc">Code-aware build recommendations</div></div></div>'
            + '</div></div></div></div></section>';
    },

    renderInsightsDemo: function() {
        return '<section class="section section-gradient" id="demo"><div class="container">'
            + '<div class="section-header"><div class="section-eyebrow">\uD83E\uDD16 AI IN ACTION</div>'
            + '<h2 class="section-title fade-in-up">See How PMBrain AI<br>Thinks and Recommends</h2>'
            + '<p class="section-desc fade-in-up">Here\'s how an AI recommendation looks \u2014 structured, scored, with citations to evidence and clear execution plans.</p></div>'
            + '<div class="demo-container fade-in-up"><div class="demo-titlebar"><div class="demo-dot demo-dot-red"></div><div class="demo-dot demo-dot-yellow"></div><div class="demo-dot demo-dot-green"></div><span class="demo-title">PMBrain AI \u2014 What Should We Build Next?</span></div>'
            + '<div class="demo-body">'
            + '<div class="demo-insight-header"><div><div class="demo-badge">\uD83E\uDD16 AI RECOMMENDATION</div><h3 style="font-size:22px;font-weight:800;margin-top:12px;color:#111827;letter-spacing:-0.5px">Real-Time Collaboration Dashboard</h3><p style="font-size:14px;color:#6B7280;margin-top:4px">Confidence: 91% \u00B7 Score: 8.7/10 \u00B7 47 evidence items</p></div><div class="demo-score-circle">8.7</div></div>'
            + '<p style="font-size:15px;color:#4B5563;line-height:1.7;margin:16px 0 24px">Based on analysis of 47 evidence items across 3 customer segments, a real-time collaboration dashboard would address the #1 pain point (team alignment) while leveraging existing WebSocket infrastructure in your codebase.</p>'
            + '<div class="demo-quote">"We spend 2+ hours daily just aligning on priorities across teams. A shared dashboard would save us at least 10 hours per week."<div class="demo-quote-source">Enterprise Customer \u00B7 Q4 Interview \u00B7 Acme Corp</div></div>'
            + '<div class="demo-quote" style="border-color:#7C3AED;background:#F5F3FF">"The lack of real-time visibility is our top churn risk factor for enterprise accounts."<div class="demo-quote-source">Support Ticket #4827 \u00B7 Critical Priority</div></div>'
            + '<h4 style="font-size:15px;font-weight:700;margin:24px 0 16px;color:#111827">\uD83D\uDCCA Opportunity Score Breakdown</h4>'
            + '<div class="demo-scores" id="demo-scores">'
            + this._row('Frequency', 92, '9.2', '#10B981', '#34D399')
            + this._row('Revenue Impact', 85, '8.5', '#10B981', '#34D399')
            + this._row('Retention Impact', 90, '9.0', '#10B981', '#34D399')
            + this._row('Strategic Alignment', 88, '8.8', '#10B981', '#34D399')
            + this._row('Effort (Low=Better)', 72, '7.2', '#F59E0B', '#FBBF24')
            + this._row('Market Demand', 95, '9.5', '#10B981', '#34D399')
            + '</div>'
            + '<h4 style="font-size:15px;font-weight:700;margin:28px 0 16px;color:#111827">\uD83D\uDD27 Code Integration Points</h4>'
            + '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:20px"><span style="padding:4px 12px;border-radius:100px;font-size:12px;font-weight:600;background:#EDE9FE;color:#5B21B6">WebSocket Layer</span><span style="padding:4px 12px;border-radius:100px;font-size:12px;font-weight:600;background:#DBEAFE;color:#1E40AF">REST API</span><span style="padding:4px 12px;border-radius:100px;font-size:12px;font-weight:600;background:#D1FAE5;color:#065F46">React Components</span><span style="padding:4px 12px;border-radius:100px;font-size:12px;font-weight:600;background:#FEF3C7;color:#92400E">Database Models</span></div>'
            + '<div id="demo-flowchart" style="margin-top:20px"></div>'
            + '</div></div></div></section>';
    },

    _row: function(label, width, value, c1, c2) {
        return '<div class="demo-score-row"><div class="demo-score-label">' + label + '</div><div class="demo-score-track"><div class="demo-score-fill" data-width="' + width + '" style="width:0;background:linear-gradient(90deg,' + c1 + ',' + c2 + ')"></div></div><div class="demo-score-value">' + value + '</div></div>';
    },

    renderCTA: function() {
        var btn = this.isLoggedIn
            ? '<a class="cta-btn" href="/dashboard">Open Dashboard \u2192</a>'
            : '<a class="cta-btn" href="/signup">Start Free \u2014 No Credit Card \u2192</a>';
        return '<section class="cta-section"><div class="cta-orb cta-orb-1"></div><div class="cta-orb cta-orb-2"></div>'
            + '<div class="cta-content"><h2 class="cta-title fade-in-up">Know What to Build Next.<br>With Confidence.</h2>'
            + '<p class="cta-desc fade-in-up">Given your codebase, customer evidence, and market trends \u2014 PMBrain AI tells you exactly what to build and why.</p>'
            + '<div class="fade-in-up">' + btn + '</div></div></section>';
    },

    renderFooter: function() {
        return '<footer class="landing-footer"><div class="footer-content">'
            + '<div class="footer-logo"><span style="font-size:24px">\uD83E\uDDE0</span><div class="footer-logo-text"><span>PM</span>Brain AI</div></div>'
            + '<div class="footer-links"><a class="footer-link" href="#features">Features</a><a class="footer-link" href="#code-intel">Code Analysis</a><a class="footer-link" href="#demo">Demo</a><a class="footer-link" href="#ai-loop">AI Loop</a></div>'
            + '<div class="footer-copy">\u00A9 ' + new Date().getFullYear() + ' PMBrain AI. Built for product teams.</div></div></footer>';
    },

    bindEvents: function() {
        document.querySelectorAll('a[href^="#"]').forEach(function(link) {
            link.addEventListener('click', function(e) {
                var target = document.querySelector(link.getAttribute('href'));
                if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
            });
        });
        setTimeout(function() {
            var fcContainer = document.getElementById('demo-flowchart');
            if (fcContainer && typeof FlowchartRenderer !== 'undefined') {
                FlowchartRenderer.render(fcContainer, [
                    { icon: '\uD83C\uDFAF', title: 'Feature Spec', subtitle: 'Auto-generated PRD' },
                    { icon: '\u2699\uFE0F', title: 'Backend Changes', subtitle: 'WebSocket + API endpoints' },
                    { icon: '\uD83C\uDFA8', title: 'Frontend Build', subtitle: 'Dashboard components' },
                    { icon: '\uD83E\uDDEA', title: 'Testing', subtitle: 'Integration + E2E tests' },
                    { icon: '\uD83D\uDE80', title: 'Deployment', subtitle: 'Progressive rollout' }
                ], { animated: true, compact: false });
            }
        }, 800);
    }
};

document.addEventListener('DOMContentLoaded', function() { Landing.init(); });
