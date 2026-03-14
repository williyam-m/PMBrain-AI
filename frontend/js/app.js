/**
 * PMBrain AI — Main Application
 * YC-Style SaaS Dashboard — Vanilla JS
 */

// ============ Toast Notifications ============
const Toast = {
    show(message, type = 'info') {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        const icons = { success: '✓', error: '✕', info: 'ℹ' };
        toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span><span>${message}</span>`;
        container.appendChild(toast);
        setTimeout(() => { toast.remove(); }, 4000);
    }
};

// ============ Main App ============
const App = {
    currentPage: 'dashboard',
    user: null,
    org: null,
    project: null,
    data: {},

    async init() {
        API.init();
        // Detect auth mode from URL path
        var path = window.location.pathname;
        if (path === '/signup' || path === '/signup/') {
            sessionStorage.setItem('pmbrain_auth_mode', 'signup');
        } else if (path === '/signin' || path === '/signin/') {
            sessionStorage.setItem('pmbrain_auth_mode', 'signin');
        }
        if (API.token) {
            try {
                await this.loadUserContext();
                this.showApp();
            } catch (e) {
                this.showAuth();
            }
        } else {
            this.showAuth();
        }
    },

    async loadUserContext() {
        this.user = await API.me();
        const orgs = await API.getOrgs();
        if (orgs.results && orgs.results.length > 0) {
            this.org = orgs.results[0];
        } else if (orgs.length > 0) {
            this.org = orgs[0];
        }
        if (this.org) {
            const projects = await API.getProjects(this.org.id);
            const projectList = projects.results || projects;
            if (projectList.length > 0) {
                this.project = projectList[0];
                WS.connect(this.project.id);
            }
        }
    },

    showAuth() {
        document.getElementById('app').innerHTML = this.renderAuth();
        this.bindAuthEvents();
        // Check if landing page or URL set auth mode
        const authMode = sessionStorage.getItem('pmbrain_auth_mode');
        if (authMode === 'signup') {
            sessionStorage.removeItem('pmbrain_auth_mode');
            const loginForm = document.getElementById('login-form');
            const regForm = document.getElementById('register-form');
            if (loginForm) loginForm.style.display = 'none';
            if (regForm) regForm.style.display = 'block';
        } else if (authMode === 'signin') {
            sessionStorage.removeItem('pmbrain_auth_mode');
            // Default is already signin, no action needed
        }
    },

    showApp() {
        document.getElementById('app').innerHTML = this.renderLayout();
        this.bindNavEvents();
        this.navigate('dashboard');
    },

    // ============ Auth ============
    renderAuth() {
        return `
        <div class="auth-container">
            <div class="auth-card">
                <div class="logo">
                    <h1><a href="/" style="text-decoration:none;color:inherit">PM<span>Brain</span> AI</a></h1>
                    <p>AI-powered product discovery — know what to build next</p>
                </div>
                <div id="auth-form">
                    <div id="login-form">
                        <div class="form-group">
                            <label>Email</label>
                            <input type="email" id="login-email" placeholder="you@company.com">
                        </div>
                        <div class="form-group">
                            <label>Password</label>
                            <input type="password" id="login-password" placeholder="Enter password">
                        </div>
                        <button class="btn btn-primary btn-full btn-lg" id="btn-login">Sign In</button>
                        <p style="text-align:center;margin-top:16px;font-size:13px;color:var(--gray-500)">
                            Don't have an account? <a href="#" id="show-register" style="color:var(--primary);font-weight:600">Sign Up</a>
                        </p>
                    </div>
                    <div id="register-form" style="display:none">
                        <div class="form-group">
                            <label>Full Name</label>
                            <input type="text" id="reg-name" placeholder="Your name">
                        </div>
                        <div class="form-group">
                            <label>Email</label>
                            <input type="email" id="reg-email" placeholder="you@company.com">
                        </div>
                        <div class="form-group">
                            <label>Password</label>
                            <input type="password" id="reg-password" placeholder="Min 8 characters">
                        </div>
                        <button class="btn btn-primary btn-full btn-lg" id="btn-register">Create Account</button>
                        <p style="text-align:center;margin-top:16px;font-size:13px;color:var(--gray-500)">
                            Already have an account? <a href="#" id="show-login" style="color:var(--primary);font-weight:600">Sign In</a>
                        </p>
                    </div>
                </div>
                
            </div>
        </div>`;
    },

    bindAuthEvents() {
        const self = this;
        document.getElementById('btn-login')?.addEventListener('click', async () => {
            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;
            try {
                const res = await API.login(email, password);
                API.setTokens(res.tokens.access, res.tokens.refresh);
                self.user = res.user;
                await self.loadUserContext();
                self.showApp();
                Toast.show('Welcome to PMBrain AI!', 'success');
            } catch (e) {
                Toast.show('Login failed: ' + e.message, 'error');
            }
        });

        document.getElementById('btn-register')?.addEventListener('click', async () => {
            const name = document.getElementById('reg-name').value;
            const email = document.getElementById('reg-email').value;
            const password = document.getElementById('reg-password').value;
            try {
                const res = await API.register(email, password, name);
                API.setTokens(res.tokens.access, res.tokens.refresh);
                self.user = res.user;
                await self.loadUserContext();
                self.showApp();
                Toast.show('Account created!', 'success');
            } catch (e) {
                Toast.show('Registration failed: ' + e.message, 'error');
            }
        });

        document.getElementById('show-register')?.addEventListener('click', (e) => {
            e.preventDefault();
            document.getElementById('login-form').style.display = 'none';
            document.getElementById('register-form').style.display = 'block';
        });

        document.getElementById('show-login')?.addEventListener('click', (e) => {
            e.preventDefault();
            document.getElementById('register-form').style.display = 'none';
            document.getElementById('login-form').style.display = 'block';
        });
    },

    // ============ Layout ============
    renderLayout() {
        const initials = this.user ? (this.user.full_name || this.user.email || 'U').substring(0, 2).toUpperCase() : 'U';
        const userName = this.user?.full_name || this.user?.email?.split('@')[0] || 'User';
        const orgName = this.org?.name || 'Organization';
        const projectName = this.project?.name || 'Project';

        return `
        <div class="app-layout">
            <aside class="sidebar">
                <div class="sidebar-header">
                    <h1>PM<span>Brain</span> AI</h1>
                    <p>${orgName} → ${projectName}</p>
                </div>
                <nav class="sidebar-nav">
                    <div class="nav-section">
                        <div class="nav-section-title">Overview</div>
                        <div class="nav-item active" data-page="dashboard">
                            <span class="nav-icon">📊</span> Dashboard
                        </div>
                    </div>
                    <div class="nav-section">
                        <div class="nav-section-title">Discovery</div>
                        <div class="nav-item" data-page="evidence">
                            <span class="nav-icon">📋</span> Evidence
                        </div>
                        <div class="nav-item" data-page="insights">
                            <span class="nav-icon">💡</span> Insights
                        </div>
                        <div class="nav-item" data-page="opportunities">
                            <span class="nav-icon">🎯</span> Opportunities
                        </div>
                    </div>
                    <div class="nav-section">
                        <div class="nav-section-title">Build</div>
                        <div class="nav-item" data-page="what-to-build">
                            <span class="nav-icon">🤖</span> What to Build
                            <span class="badge">AI</span>
                        </div>
                        <div class="nav-item" data-page="specs">
                            <span class="nav-icon">📄</span> Specs
                        </div>
                    </div>
                    <div class="nav-section">
                        <div class="nav-section-title">Code & Trends</div>
                        <div class="nav-item" data-page="codebase">
                            <span class="nav-icon">💻</span> Codebase
                            <span class="badge">NEW</span>
                        </div>
                        <div class="nav-item" data-page="feature-discovery">
                            <span class="nav-icon">🔍</span> AI Discovery
                            <span class="badge">NEW</span>
                        </div>
                    </div>
                    <div class="nav-section">
                        <div class="nav-section-title">Analyze</div>
                        <div class="nav-item" data-page="analytics">
                            <span class="nav-icon">📈</span> Analytics
                        </div>
                        <div class="nav-item" data-page="datasources">
                            <span class="nav-icon">🔌</span> Data Sources
                        </div>
                    </div>
                    <div class="nav-section">
                        <div class="nav-section-title">Settings</div>
                        <div class="nav-item" data-page="settings">
                            <span class="nav-icon">⚙️</span> Settings
                        </div>
                    </div>
                </nav>
                <div class="sidebar-footer">
                    <div class="user-info">
                        <div class="user-avatar">${initials}</div>
                        <div class="user-info-text">
                            <div class="name">${userName}</div>
                            <div class="role">Product Manager</div>
                        </div>
                        <button class="btn btn-ghost btn-sm" id="btn-logout" title="Sign Out">↗</button>
                    </div>
                </div>
            </aside>
            <main class="main-content">
                <div class="topbar">
                    <div class="topbar-left">
                        <h2 id="page-title">Dashboard</h2>
                    </div>
                    <div class="topbar-right">
                        <span id="ws-status" class="ws-indicator disconnected" title="WebSocket"></span>
                        <button class="btn btn-ghost btn-sm" id="btn-notifications" title="Notifications">🔔</button>
                        <button class="btn btn-primary btn-sm" id="btn-run-ai">⚡ Run AI Pipeline</button>
                    </div>
                </div>
                <div class="page-content" id="page-content">
                    <div class="loading-overlay"><div class="loading-spinner lg"></div><p>Loading...</p></div>
                </div>
            </main>
        </div>
        <div class="modal-overlay" id="modal-overlay">
            <div class="modal" id="modal-content"></div>
        </div>`;
    },

    bindNavEvents() {
        const self = this;
        document.querySelectorAll('.nav-item[data-page]').forEach(item => {
            item.addEventListener('click', () => {
                const page = item.dataset.page;
                self.navigate(page);
            });
        });

        document.getElementById('btn-logout')?.addEventListener('click', () => {
            API.clearTokens();
            WS.disconnect();
            self.showAuth();
        });

        document.getElementById('btn-run-ai')?.addEventListener('click', () => self.showRunAIModal());
        document.getElementById('btn-notifications')?.addEventListener('click', () => self.navigate('notifications'));
        document.getElementById('modal-overlay')?.addEventListener('click', (e) => {
            if (e.target.id === 'modal-overlay') self.closeModal();
        });
    },

    navigate(page) {
        this.currentPage = page;
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        const navItem = document.querySelector(`.nav-item[data-page="${page}"]`);
        if (navItem) navItem.classList.add('active');

        const titles = {
            'dashboard': 'Dashboard',
            'evidence': 'Evidence',
            'insights': 'Insights',
            'opportunities': 'Opportunities',
            'what-to-build': '🤖 What Should We Build Next?',
            'specs': 'Specifications',
            'codebase': '💻 Codebase Analysis',
            'feature-discovery': '🔍 AI Feature Discovery',
            'analytics': 'Analytics',
            'datasources': 'Data Sources',
            'notifications': 'Notifications',
            'settings': '⚙️ Settings & Integrations',
        };
        document.getElementById('page-title').textContent = titles[page] || page;

        this.loadPage(page);
    },

    async loadPage(page) {
        const content = document.getElementById('page-content');
        content.innerHTML = '<div class="loading-overlay"><div class="loading-spinner lg"></div><p>Loading...</p></div>';

        try {
            switch (page) {
                case 'dashboard': await Pages.dashboard(content); break;
                case 'evidence': await Pages.evidence(content); break;
                case 'insights': await Pages.insights(content); break;
                case 'opportunities': await Pages.opportunities(content); break;
                case 'what-to-build': await Pages.whatToBuild(content); break;
                case 'specs': await Pages.specs(content); break;
                case 'analytics': await Pages.analytics(content); break;
                case 'codebase': await Pages.codebase(content); break;
                case 'feature-discovery': await Pages.featureDiscovery(content); break;
                case 'datasources': await Pages.datasources(content); break;
                case 'notifications': await Pages.notifications(content); break;
                case 'settings': await Pages.settings(content); break;
                default: content.innerHTML = '<div class="empty-state"><h3>Page not found</h3></div>';
            }
        } catch (e) {
            content.innerHTML = `<div class="empty-state"><div class="icon">⚠️</div><h3>Error loading page</h3><p>${e.message}</p></div>`;
        }
    },

    showModal(html) {
        document.getElementById('modal-content').innerHTML = html;
        document.getElementById('modal-overlay').classList.add('active');
    },

    closeModal() {
        document.getElementById('modal-overlay').classList.remove('active');
    },

    showRunAIModal() {
        if (!this.project) {
            Toast.show('No project selected', 'error');
            return;
        }
        this.showModal(`
            <div class="modal-header">
                <h3>⚡ Run AI Pipeline</h3>
                <button class="modal-close" onclick="App.closeModal()">×</button>
            </div>
            <div class="modal-body">
                <p style="margin-bottom:20px;color:var(--gray-600)">Select an AI workflow to run on your project data.</p>
                <div style="display:flex;flex-direction:column;gap:12px">
                    <button class="btn btn-secondary btn-full" onclick="App.runWorkflow('full_pipeline')">
                        🔄 Full Pipeline — Evidence → Insights → Opportunities → Scores
                    </button>
                    <button class="btn btn-secondary btn-full" onclick="App.runWorkflow('evidence_to_insights')">
                        📋→💡 Process Evidence into Insights
                    </button>
                    <button class="btn btn-secondary btn-full" onclick="App.runWorkflow('insights_to_opportunities')">
                        💡→🎯 Generate Opportunities from Insights
                    </button>
                    <button class="btn btn-secondary btn-full" onclick="App.runWorkflow('score_opportunities')">
                        📊 Score All Opportunities
                    </button>
                    <button class="btn btn-secondary btn-full" onclick="App.runWorkflow('market_trends')">
                        📊 Analyze Market Trends
                    </button>
                    <button class="btn btn-secondary btn-full" onclick="App.runWorkflow('feature_discovery')">
                        🔍 AI Feature Discovery (Evidence + Code + Trends)
                    </button>
                    <button class="btn btn-primary btn-full" onclick="App.runWorkflow('what_to_build')">
                        🤖 What Should We Build Next?
                    </button>
                </div>
            </div>
        `);
    },

    async runWorkflow(workflow) {
        this.closeModal();
        Toast.show(`Running ${workflow}...`, 'info');
        try {
            const result = await API.runAgent(workflow, this.project.id);
            Toast.show(`✓ ${workflow} completed!`, 'success');
            this.loadPage(this.currentPage);
            console.log('Workflow result:', result);
        } catch (e) {
            Toast.show(`Error: ${e.message}`, 'error');
        }
    },

    formatDate(d) {
        if (!d) return '-';
        return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    },

    truncate(s, n = 100) {
        if (!s) return '';
        return s.length > n ? s.substring(0, n) + '...' : s;
    }
};

// ============ Pages ============
const Pages = {
    // ---- Dashboard ----
    async dashboard(el) {
        if (!App.project) {
            el.innerHTML = '<div class="empty-state"><div class="icon">🏗️</div><h3>No project found</h3><p>Create a project to get started.</p></div>';
            return;
        }

        let dashData = {};
        try { dashData = await API.getDashboard(App.project.id); } catch(e) { dashData = {metrics:{},top_insights:[],opportunity_leaderboard:[],pipeline:{},spec_status:[],agent_performance:{}}; }

        const m = dashData.metrics || {};
        const pipeline = dashData.pipeline || {};

        el.innerHTML = `
            <div class="metrics-grid">
                <div class="metric-card highlight">
                    <div class="metric-label">Total Evidence</div>
                    <div class="metric-value">${m.evidence_count || 0}</div>
                    <div class="metric-change">${m.evidence_processed || 0} processed</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Insight Clusters</div>
                    <div class="metric-value">${m.insights_count || 0}</div>
                    <div class="metric-change positive">AI-generated</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Opportunities</div>
                    <div class="metric-value">${m.opportunities_count || 0}</div>
                    <div class="metric-change">${pipeline.approved || 0} approved</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Specs Generated</div>
                    <div class="metric-value">${m.specs_count || 0}</div>
                    <div class="metric-change">Versioned artifacts</div>
                </div>
            </div>

            <div style="margin-bottom:24px">
                <div class="card">
                    <div class="card-header"><h3>🎯 Opportunity Pipeline</h3></div>
                    <div class="card-body">
                        <div class="pipeline">
                            <div class="pipeline-stage ${pipeline.discovered ? 'active' : ''}">
                                <div class="stage-count">${pipeline.discovered || 0}</div>
                                <div class="stage-label">Discovered</div>
                            </div>
                            <div class="pipeline-stage ${pipeline.evaluating ? 'active' : ''}">
                                <div class="stage-count">${pipeline.evaluating || 0}</div>
                                <div class="stage-label">Evaluating</div>
                            </div>
                            <div class="pipeline-stage ${pipeline.approved ? 'active' : ''}">
                                <div class="stage-count">${pipeline.approved || 0}</div>
                                <div class="stage-label">Approved</div>
                            </div>
                            <div class="pipeline-stage ${pipeline.in_progress ? 'active' : ''}">
                                <div class="stage-count">${pipeline.in_progress || 0}</div>
                                <div class="stage-label">In Progress</div>
                            </div>
                            <div class="pipeline-stage ${pipeline.shipped ? 'active' : ''}">
                                <div class="stage-count">${pipeline.shipped || 0}</div>
                                <div class="stage-label">Shipped</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="grid-2">
                <div class="card">
                    <div class="card-header"><h3>💡 Top Unmet Needs</h3></div>
                    <div class="card-body">
                        ${(dashData.top_insights || []).map(i => `
                            <div style="display:flex;align-items:center;justify-content:space-between;padding:12px 0;border-bottom:1px solid var(--gray-100)">
                                <div>
                                    <div style="font-size:14px;font-weight:600;color:var(--gray-800)">${i.title || 'Untitled'}</div>
                                    <div style="font-size:12px;color:var(--gray-500);margin-top:2px">${i.frequency || 0} mentions · ${i.trend_direction || 'stable'}</div>
                                </div>
                                <span class="tag severity-${i.severity || 'medium'}">${i.severity || 'medium'}</span>
                            </div>
                        `).join('') || '<div class="empty-state"><p>No insights yet. Run the AI pipeline!</p></div>'}
                    </div>
                </div>

                <div class="card">
                    <div class="card-header"><h3>🏆 Opportunity Leaderboard</h3></div>
                    <div class="card-body">
                        ${(dashData.opportunity_leaderboard || []).map((o, idx) => `
                            <div style="display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid var(--gray-100)">
                                <div style="width:24px;height:24px;border-radius:50%;background:${idx === 0 ? 'var(--primary)' : 'var(--gray-200)'};color:${idx === 0 ? 'white' : 'var(--gray-600)'};display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700">${idx + 1}</div>
                                <div style="flex:1">
                                    <div style="font-size:14px;font-weight:600;color:var(--gray-800)">${o.title}</div>
                                    <span class="tag status-${o.status}" style="margin-top:4px">${o.status}</span>
                                </div>
                                <div style="font-size:20px;font-weight:800;color:var(--primary)">${(o.score || o.total_score || 0).toFixed(1)}</div>
                            </div>
                        `).join('') || '<div class="empty-state"><p>No scored opportunities yet.</p></div>'}
                    </div>
                </div>
            </div>

            <div style="margin-top:24px">
                <div class="card">
                    <div class="card-header">
                        <h3>🤖 Quick Actions</h3>
                    </div>
                    <div class="card-body" style="display:flex;gap:12px;flex-wrap:wrap">
                        <button class="btn btn-primary" onclick="App.navigate('what-to-build')">🤖 What Should We Build Next?</button>
                        <button class="btn btn-secondary" onclick="App.showRunAIModal()">⚡ Run AI Pipeline</button>
                        <button class="btn btn-secondary" onclick="App.navigate('evidence')">📋 Upload Evidence</button>
                        <button class="btn btn-secondary" onclick="App.navigate('opportunities')">🎯 View Opportunities</button>
                    </div>
                </div>
            </div>
        `;
    },

    // ---- Evidence ----
    async evidence(el) {
        let evidence = [];
        let stats = {};
        try {
            const res = await API.getEvidence(App.project.id);
            evidence = res.results || res || [];
            stats = await API.getEvidenceStats(App.project.id);
        } catch(e) {}

        el.innerHTML = `
            <div class="metrics-grid">
                <div class="metric-card"><div class="metric-label">Total Evidence</div><div class="metric-value">${stats.total || evidence.length}</div></div>
                <div class="metric-card"><div class="metric-label">Processed</div><div class="metric-value">${stats.processed || 0}</div></div>
                <div class="metric-card"><div class="metric-label">Unprocessed</div><div class="metric-value">${stats.unprocessed || 0}</div></div>
            </div>

            <div class="card" style="margin-bottom:24px">
                <div class="card-header">
                    <h3>📋 Upload Evidence</h3>
                    <button class="btn btn-primary btn-sm" id="btn-add-evidence">+ Add Evidence</button>
                </div>
                <div class="card-body" id="upload-area" style="display:none">
                    <div class="grid-2">
                        <div class="form-group">
                            <label>Type</label>
                            <select id="ev-type">
                                <option value="support_ticket">Support Ticket</option>
                                <option value="interview_transcript">Interview Transcript</option>
                                <option value="feature_request">Feature Request</option>
                                <option value="nps_survey">NPS Survey</option>
                                <option value="churn_feedback">Churn Feedback</option>
                                <option value="slack_thread">Slack Thread</option>
                                <option value="analytics_event">Analytics Event</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Customer Segment</label>
                            <select id="ev-segment">
                                <option value="enterprise">Enterprise</option>
                                <option value="mid_market">Mid-Market</option>
                                <option value="smb">SMB</option>
                                <option value="startup">Startup</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Title</label>
                        <input type="text" id="ev-title" placeholder="Brief title for this evidence">
                    </div>
                    <div class="form-group">
                        <label>Content</label>
                        <textarea id="ev-text" rows="4" placeholder="Paste customer feedback, ticket content, transcript, etc."></textarea>
                    </div>
                    <div class="form-group">
                        <label>Source</label>
                        <input type="text" id="ev-source" placeholder="e.g., zendesk, intercom, slack">
                    </div>
                    <button class="btn btn-primary" id="btn-submit-evidence">Submit Evidence</button>
                    <button class="btn btn-secondary" id="btn-process-evidence" style="margin-left:8px">⚡ Process with AI</button>
                </div>
            </div>

            <div class="card">
                <div class="card-header"><h3>Evidence Items (${evidence.length})</h3></div>
                <div class="card-body" style="padding:0">
                    <table class="data-table">
                        <thead><tr>
                            <th>Title</th>
                            <th>Type</th>
                            <th>Segment</th>
                            <th>Sentiment</th>
                            <th>Status</th>
                            <th>Date</th>
                        </tr></thead>
                        <tbody>
                            ${evidence.map(e => `
                                <tr onclick="Pages.showEvidenceDetail('${e.id}')">
                                    <td><strong>${App.truncate(e.title || e.text, 60)}</strong></td>
                                    <td><span class="tag tag-gray">${e.evidence_type}</span></td>
                                    <td><span class="tag tag-primary">${e.customer_segment}</span></td>
                                    <td><span class="tag ${e.sentiment === 'negative' ? 'tag-danger' : e.sentiment === 'positive' ? 'tag-success' : 'tag-gray'}">${e.sentiment}</span></td>
                                    <td>${e.is_processed ? '<span class="tag tag-success">Processed</span>' : '<span class="tag tag-warning">Pending</span>'}</td>
                                    <td style="font-size:13px;color:var(--gray-500)">${App.formatDate(e.created_at)}</td>
                                </tr>
                            `).join('') || '<tr><td colspan="6"><div class="empty-state">No evidence yet. Upload some!</div></td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>`;

        document.getElementById('btn-add-evidence')?.addEventListener('click', () => {
            const area = document.getElementById('upload-area');
            area.style.display = area.style.display === 'none' ? 'block' : 'none';
        });

        document.getElementById('btn-submit-evidence')?.addEventListener('click', async () => {
            const data = {
                evidence_type: document.getElementById('ev-type').value,
                customer_segment: document.getElementById('ev-segment').value,
                title: document.getElementById('ev-title').value,
                text: document.getElementById('ev-text').value,
                source_name: document.getElementById('ev-source').value,
                organization: App.org.id,
                project: App.project.id,
            };
            try {
                await API.createEvidence(data);
                Toast.show('Evidence added!', 'success');
                Pages.evidence(el);
            } catch(e) { Toast.show(e.message, 'error'); }
        });

        document.getElementById('btn-process-evidence')?.addEventListener('click', async () => {
            Toast.show('Processing evidence with AI...', 'info');
            try {
                await API.runAgent('evidence_to_insights', App.project.id);
                Toast.show('Evidence processed!', 'success');
                Pages.evidence(el);
            } catch(e) { Toast.show(e.message, 'error'); }
        });
    },

    showEvidenceDetail(id) {
        // Simplified detail view in modal
        App.showModal(`
            <div class="modal-header"><h3>Evidence Detail</h3><button class="modal-close" onclick="App.closeModal()">×</button></div>
            <div class="modal-body"><div class="loading-overlay"><div class="loading-spinner"></div></div></div>
        `);
        API.get(`/evidence/${id}/`).then(e => {
            document.querySelector('#modal-content .modal-body').innerHTML = `
                <div style="margin-bottom:16px"><span class="tag tag-primary">${e.evidence_type}</span> <span class="tag">${e.customer_segment}</span> <span class="tag ${e.sentiment === 'negative' ? 'tag-danger' : 'tag-gray'}">${e.sentiment}</span></div>
                <h4 style="font-size:16px;margin-bottom:8px">${e.title}</h4>
                <p style="color:var(--gray-600);line-height:1.7;margin-bottom:16px">${e.text}</p>
                ${e.summary ? `<div style="margin-top:16px"><h4 style="font-size:14px;margin-bottom:8px">AI Summary</h4><p style="color:var(--gray-600)">${e.summary}</p></div>` : ''}
                ${e.pain_points && e.pain_points.length ? `<div style="margin-top:16px"><h4 style="font-size:14px;margin-bottom:8px">Pain Points</h4><ul style="padding-left:20px">${e.pain_points.map(p => `<li style="margin:4px 0;color:var(--gray-700)">${p}</li>`).join('')}</ul></div>` : ''}
                ${e.key_quotes && e.key_quotes.length ? `<div style="margin-top:16px"><h4 style="font-size:14px;margin-bottom:8px">Key Quotes</h4>${e.key_quotes.map(q => `<div class="evidence-quote">"${q}"</div>`).join('')}</div>` : ''}
            `;
        });
    },

    // ---- Insights ----
    async insights(el) {
        let insights = [];
        let stats = {};
        try {
            const res = await API.getInsights(App.project.id);
            insights = res.results || res || [];
            stats = await API.getInsightStats(App.project.id);
        } catch(e) {}

        el.innerHTML = `
            <div class="metrics-grid">
                <div class="metric-card"><div class="metric-label">Total Insights</div><div class="metric-value">${stats.total || insights.length}</div></div>
                <div class="metric-card"><div class="metric-label">Critical</div><div class="metric-value" style="color:var(--danger)">${stats.critical || 0}</div></div>
                <div class="metric-card"><div class="metric-label">Rising Trends</div><div class="metric-value" style="color:var(--warning)">${stats.rising || 0}</div></div>
                <div class="metric-card"><div class="metric-label">Avg Confidence</div><div class="metric-value">${((stats.avg_confidence || 0) * 100).toFixed(0)}%</div></div>
            </div>

            <div class="card" style="margin-bottom:24px">
                <div class="card-header">
                    <h3>💡 Insight Clusters</h3>
                    <button class="btn btn-primary btn-sm" onclick="App.runWorkflow('evidence_to_insights')">⚡ Regenerate</button>
                </div>
                <div class="card-body" style="padding:0">
                    ${insights.map(i => `
                        <div style="padding:20px 24px;border-bottom:1px solid var(--gray-100);cursor:pointer" onclick="Pages.showInsightDetail('${i.id}')">
                            <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px">
                                <h4 style="font-size:15px;font-weight:700;color:var(--gray-900)">${i.title}</h4>
                                <div style="display:flex;gap:8px;align-items:center;flex-shrink:0">
                                    <span class="tag severity-${i.severity}">${i.severity}</span>
                                    <span style="font-size:12px;color:${i.trend_direction === 'rising' ? 'var(--danger)' : 'var(--gray-500)'}">${i.trend_direction === 'rising' ? '📈 Rising' : i.trend_direction === 'declining' ? '📉 Declining' : '→ Stable'}</span>
                                </div>
                            </div>
                            <p style="font-size:14px;color:var(--gray-600);margin-bottom:8px">${App.truncate(i.summary, 200)}</p>
                            <div style="display:flex;gap:12px;font-size:12px;color:var(--gray-500)">
                                <span>📊 ${i.frequency} mentions</span>
                                <span>🎯 ${(i.confidence * 100).toFixed(0)}% confidence</span>
                                <span>👥 ${(i.segments_affected || []).join(', ')}</span>
                            </div>
                        </div>
                    `).join('') || '<div class="empty-state"><p>No insights yet. Process evidence with AI first.</p></div>'}
                </div>
            </div>`;
    },

    showInsightDetail(id) {
        App.showModal(`
            <div class="modal-header"><h3>Insight Detail</h3><button class="modal-close" onclick="App.closeModal()">×</button></div>
            <div class="modal-body"><div class="loading-overlay"><div class="loading-spinner"></div></div></div>
        `);
        API.get(`/insights/${id}/`).then(i => {
            document.querySelector('#modal-content .modal-body').innerHTML = `
                <div style="display:flex;gap:8px;margin-bottom:16px">
                    <span class="tag severity-${i.severity}">${i.severity}</span>
                    <span class="tag tag-primary">${i.trend_direction}</span>
                    <span class="tag tag-gray">${(i.confidence * 100).toFixed(0)}% confidence</span>
                </div>
                <h3 style="font-size:18px;font-weight:700;margin-bottom:12px">${i.title}</h3>
                <p style="color:var(--gray-600);line-height:1.7;margin-bottom:16px">${i.summary}</p>
                <div style="display:flex;gap:24px;margin-bottom:16px">
                    <div><strong style="font-size:24px;color:var(--primary)">${i.frequency}</strong><br><span style="font-size:12px;color:var(--gray-500)">Mentions</span></div>
                    <div><strong style="font-size:24px">${(i.segments_affected||[]).length}</strong><br><span style="font-size:12px;color:var(--gray-500)">Segments</span></div>
                    <div><strong style="font-size:24px">${i.evidence_count || 0}</strong><br><span style="font-size:12px;color:var(--gray-500)">Evidence Items</span></div>
                </div>
                ${(i.representative_quotes||[]).length ? '<h4 style="font-size:14px;margin-bottom:8px">Representative Quotes</h4>' + i.representative_quotes.map(q => `<div class="evidence-quote">"${q}"</div>`).join('') : ''}
                ${(i.segments_affected||[]).length ? `<div style="margin-top:16px"><h4 style="font-size:14px;margin-bottom:8px">Affected Segments</h4><div style="display:flex;gap:8px">${i.segments_affected.map(s => `<span class="tag tag-primary">${s}</span>`).join('')}</div></div>` : ''}
            `;
        });
    },

    // ---- Opportunities ----
    async opportunities(el) {
        let opps = [];
        let stats = {};
        try {
            const res = await API.getOpportunities(App.project.id);
            opps = res.results || res || [];
            stats = await API.getOppStats(App.project.id);
        } catch(e) {}

        el.innerHTML = `
            <div class="metrics-grid">
                <div class="metric-card"><div class="metric-label">Total</div><div class="metric-value">${stats.total || opps.length}</div></div>
                <div class="metric-card"><div class="metric-label">Evaluating</div><div class="metric-value">${stats.evaluating || 0}</div></div>
                <div class="metric-card"><div class="metric-label">Approved</div><div class="metric-value" style="color:var(--success)">${stats.approved || 0}</div></div>
                <div class="metric-card"><div class="metric-label">Shipped</div><div class="metric-value" style="color:var(--primary)">${stats.shipped || 0}</div></div>
            </div>

            <div style="display:flex;gap:12px;margin-bottom:24px">
                <button class="btn btn-primary btn-sm" onclick="App.runWorkflow('insights_to_opportunities')">⚡ Discover Opportunities</button>
                <button class="btn btn-secondary btn-sm" onclick="App.runWorkflow('score_opportunities')">📊 Score All</button>
            </div>

            <div id="opp-list">
                ${opps.map(o => `
                    <div class="opp-card" onclick="Pages.showOpportunityDetail('${o.id}')">
                        <div class="opp-card-header">
                            <div>
                                <h4>${o.title}</h4>
                                <div style="margin-top:4px;display:flex;gap:8px">
                                    <span class="tag status-${o.status}">${o.status}</span>
                                    ${(o.affected_segments||[]).map(s => `<span class="tag tag-primary">${s}</span>`).join('')}
                                </div>
                            </div>
                            <div class="opp-score">${(o.top_score || 0).toFixed(1)}</div>
                        </div>
                        <p>${App.truncate(o.problem_statement, 180)}</p>
                        <div class="opp-meta">
                            <span style="font-size:12px;color:var(--gray-500)">💡 ${o.insight_count || 0} insights</span>
                            <span style="font-size:12px;color:var(--gray-500)">📋 ${o.evidence_count || 0} evidence</span>
                        </div>
                    </div>
                `).join('') || '<div class="empty-state"><div class="icon">🎯</div><h3>No opportunities yet</h3><p>Run the AI pipeline to discover opportunities from insights.</p></div>'}
            </div>`;
    },

    showOpportunityDetail(id) {
        App.showModal(`
            <div class="modal-header"><h3>Opportunity</h3><button class="modal-close" onclick="App.closeModal()">×</button></div>
            <div class="modal-body"><div class="loading-overlay"><div class="loading-spinner"></div></div></div>
        `);
        API.getOpportunity(id).then(o => {
            const score = o.scores && o.scores[0] ? o.scores[0] : null;
            document.querySelector('#modal-content .modal-body').innerHTML = `
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
                    <div style="display:flex;gap:8px">
                        <span class="tag status-${o.status}">${o.status}</span>
                        ${(o.affected_segments||[]).map(s => `<span class="tag tag-primary">${s}</span>`).join('')}
                    </div>
                    ${score ? `<div style="font-size:32px;font-weight:800;color:var(--primary)">${score.total_score.toFixed(1)}</div>` : ''}
                </div>
                <h3 style="font-size:20px;font-weight:800;margin-bottom:12px">${o.title}</h3>
                <div class="spec-section">
                    <h4>Problem Statement</h4>
                    <p style="color:var(--gray-600);line-height:1.7">${o.problem_statement}</p>
                </div>
                ${o.proposed_solution ? `<div class="spec-section"><h4>Proposed Solution</h4><p style="color:var(--gray-600);line-height:1.7">${o.proposed_solution}</p></div>` : ''}
                ${score ? `
                <div class="spec-section">
                    <h4>Score Breakdown</h4>
                    <div class="score-breakdown">
                        ${[
                            ['Frequency', score.frequency_score],
                            ['Revenue Impact', score.revenue_impact],
                            ['Retention Impact', score.retention_impact],
                            ['Strategic Alignment', score.strategic_alignment],
                            ['Effort (lower=better)', score.effort_estimate],
                        ].map(([label, val]) => `
                            <div class="score-row">
                                <span class="score-label">${label}</span>
                                <div class="score-bar-wrap"><div class="score-bar"><div class="score-bar-fill ${val >= 7 ? 'high' : val >= 4 ? 'medium' : 'low'}" style="width:${val * 10}%"></div></div></div>
                                <span class="score-value">${val.toFixed(1)}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>` : ''}
                ${(o.assumptions||[]).length ? `<div class="spec-section"><h4>Assumptions</h4><ul class="spec-list">${o.assumptions.map(a => `<li>${a}</li>`).join('')}</ul></div>` : ''}
                ${(o.risks||[]).length ? `<div class="spec-section"><h4>Risks</h4><ul class="spec-list">${o.risks.map(r => `<li>${r}</li>`).join('')}</ul></div>` : ''}
                ${(o.alternatives||[]).length ? `<div class="spec-section"><h4>Alternatives</h4><ul class="spec-list">${o.alternatives.map(a => `<li>${typeof a === 'object' ? a.feature || JSON.stringify(a) : a}</li>`).join('')}</ul></div>` : ''}
                <div style="display:flex;gap:8px;margin-top:24px">
                    <button class="btn btn-primary btn-sm" onclick="Pages.generateSpec('${o.id}')">📄 Generate Spec</button>
                    <button class="btn btn-success btn-sm" onclick="Pages.updateOppStatus('${o.id}','approved')">✓ Approve</button>
                    <button class="btn btn-secondary btn-sm" onclick="Pages.updateOppStatus('${o.id}','evaluating')">🔍 Evaluate</button>
                </div>
            `;
        });
    },

    async generateSpec(oppId) {
        App.closeModal();
        Toast.show('Generating spec with AI...', 'info');
        try {
            await API.runAgent('generate_spec', App.project.id, { opportunity_id: oppId });
            Toast.show('Spec generated!', 'success');
            App.navigate('specs');
        } catch(e) { Toast.show(e.message, 'error'); }
    },

    async updateOppStatus(id, status) {
        try {
            await API.updateOppStatus(id, status);
            Toast.show(`Status updated to ${status}`, 'success');
            App.closeModal();
            App.loadPage('opportunities');
        } catch(e) { Toast.show(e.message, 'error'); }
    },

    // ---- What To Build ----
    async whatToBuild(el) {
        el.innerHTML = `
            <div class="ai-recommendation-enhanced" style="text-align:center;padding:48px">
                <div class="ai-rec-badge">🤖 PMBrain AI — Powered by Gemini</div>
                <div class="ai-rec-title" style="font-size:28px;margin:16px 0">What Should We Build Next?</div>
                <p style="color:var(--gray-500);margin-bottom:28px;max-width:560px;margin-left:auto;margin-right:auto;font-size:15px;line-height:1.7">
                    PMBrain AI analyzes your <strong>customer evidence</strong>, <strong>insight clusters</strong>, 
                    <strong>opportunities</strong>, <strong>codebase capabilities</strong>, and <strong>market trends</strong> 
                    to recommend the highest-impact feature to build next — with citations and confidence scores.
                </p>
                <div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-bottom:24px">
                    <span class="code-chip">📋 Evidence</span>
                    <span style="padding:6px 14px;border-radius:100px;font-size:12px;font-weight:600;background:#DBEAFE;color:#1E40AF;border:1px solid #93C5FD">💡 Insights</span>
                    <span style="padding:6px 14px;border-radius:100px;font-size:12px;font-weight:600;background:#D1FAE5;color:#065F46;border:1px solid #6EE7B7">🎯 Opportunities</span>
                    <span class="code-chip">💻 Codebase</span>
                    <span style="padding:6px 14px;border-radius:100px;font-size:12px;font-weight:600;background:#FEF3C7;color:#92400E;border:1px solid #FDE68A">📊 Trends</span>
                </div>
                <div class="form-group" style="max-width:600px;margin:0 auto 20px">
                    <input type="text" id="wtb-query" value="Given our product codebase, customer evidence, and current market trends — what should we build next?" placeholder="Ask PMBrain AI..." style="text-align:center;font-size:15px;padding:16px;border-radius:14px;border-width:2px">
                </div>
                <button class="btn btn-primary btn-lg" id="btn-what-to-build" style="padding:16px 40px;font-size:16px;border-radius:14px">🤖 Get AI Recommendation</button>
            </div>
            <div id="wtb-result"></div>`;

        document.getElementById('btn-what-to-build')?.addEventListener('click', async () => {
            const query = document.getElementById('wtb-query').value;
            const resultEl = document.getElementById('wtb-result');
            resultEl.innerHTML = `
                <div class="ai-analysis-modal" style="position:relative;background:transparent;padding:32px">
                    <div class="ai-analysis-content">
                        <div class="ai-analysis-animation">
                            <div class="ai-pulse-ring"></div>
                            <div class="ai-icon">🤖</div>
                        </div>
                        <h3>AI is thinking...</h3>
                        <div class="ai-analysis-steps">
                            <div class="ai-step active"><span class="ai-step-icon"><div class="loading-spinner" style="width:16px;height:16px"></div></span><span class="ai-step-text">Analyzing customer evidence & insights...</span></div>
                            <div class="ai-step pending"><span class="ai-step-icon">⬜</span><span class="ai-step-text">Evaluating opportunities & scores...</span></div>
                            <div class="ai-step pending"><span class="ai-step-icon">⬜</span><span class="ai-step-text">Checking codebase capabilities...</span></div>
                            <div class="ai-step pending"><span class="ai-step-icon">⬜</span><span class="ai-step-text">Reviewing market trends...</span></div>
                            <div class="ai-step pending"><span class="ai-step-icon">⬜</span><span class="ai-step-text">Generating recommendation with citations...</span></div>
                        </div>
                        <p style="color:var(--gray-500);font-size:13px;margin-top:12px">Gemini AI is synthesizing all your product data to recommend the highest-impact feature...</p>
                    </div>
                </div>`;

            // Animate steps while waiting
            const animSteps = resultEl.querySelectorAll('.ai-step');
            let stepIdx = 0;
            const stepInterval = setInterval(() => {
                if (stepIdx < animSteps.length - 1) {
                    animSteps[stepIdx].className = 'ai-step done';
                    animSteps[stepIdx].querySelector('.ai-step-icon').innerHTML = '✅';
                    stepIdx++;
                    animSteps[stepIdx].className = 'ai-step active';
                    animSteps[stepIdx].querySelector('.ai-step-icon').innerHTML = '<div class="loading-spinner" style="width:16px;height:16px"></div>';
                }
            }, 1500);

            try {
                const result = await API.whatToBuild(App.project.id, query);
                clearInterval(stepInterval);
                const rec = result.results?.what_to_build?.recommendation || result.recommendation || {};
                Pages.renderRecommendation(resultEl, rec);
            } catch(e) {
                clearInterval(stepInterval);
                resultEl.innerHTML = `<div class="empty-state"><p>Error: ${e.message}</p></div>`;
            }
        });
    },

    renderRecommendation(el, rec) {
        if (!rec || !rec.feature) {
            el.innerHTML = '<div class="empty-state"><p>No recommendation generated. Try uploading more evidence first.</p></div>';
            return;
        }

        const impact = rec.expected_impact || {};
        const breakdown = rec.score_breakdown || {};
        const evidence = rec.supporting_evidence || [];
        const alternatives = rec.alternatives || [];
        const trendAlignment = rec.trend_alignment || '';
        const codeIntegration = rec.code_integration_points || [];
        const executionPlan = rec.execution_plan || rec.execution_flow || [];
        const risks = rec.risks || [];
        const assumptions = rec.assumptions || [];
        const tasks = rec.tasks || rec.engineering_tasks || [];

        el.innerHTML = `
            <!-- Enhanced Recommendation Hero -->
            <div class="ai-recommendation-enhanced">
                <div class="ai-rec-header">
                    <div>
                        <div class="ai-rec-badge">🤖 AI RECOMMENDATION</div>
                        <div class="ai-rec-title">${rec.feature}</div>
                        <div class="ai-rec-meta">
                            <span class="ai-rec-meta-item"><strong>${((rec.confidence || 0) * 100).toFixed(0)}%</strong> confidence</span>
                            <span class="ai-rec-meta-item"><strong>${evidence.length}</strong> evidence items</span>
                            ${trendAlignment ? `<span class="trend-alignment-badge">📈 ${trendAlignment}</span>` : ''}
                        </div>
                    </div>
                    <div class="ai-rec-score-ring">
                        <span class="ai-rec-score-value">${(breakdown.total_score || 0).toFixed(1)}</span>
                        <span class="ai-rec-score-label">Score</span>
                    </div>
                </div>
                <p class="ai-rec-summary">${rec.summary || ''}</p>
            </div>

            <!-- Score Breakdown Graph -->
            <div class="grid-2" style="margin-bottom:24px">
                <div class="card">
                    <div class="card-header"><h3>📊 Opportunity Score Breakdown</h3></div>
                    <div class="card-body" id="rec-score-graph"></div>
                </div>
                <div class="card">
                    <div class="card-header"><h3>📈 Expected Impact</h3></div>
                    <div class="card-body">
                        <div class="impact-grid">
                            ${Object.entries(impact).map(([k, v]) => `
                                <div class="impact-item">
                                    <div class="label">${k.replace(/_/g, ' ')}</div>
                                    <div class="value">${v}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Supporting Evidence -->
            ${evidence.length ? `
            <div class="card" style="margin-bottom:24px">
                <div class="card-header"><h3>📋 Supporting Evidence (${evidence.length} citations)</h3></div>
                <div class="card-body">
                    ${evidence.map(e => `
                        <div class="evidence-quote">
                            "${e.quote || e.text || e}"
                            <div class="quote-source">${[e.type, e.segment, e.source].filter(Boolean).join(' · ')}</div>
                        </div>
                    `).join('')}
                </div>
            </div>` : ''}

            <!-- Code Integration Points -->
            ${codeIntegration.length ? `
            <div class="card" style="margin-bottom:24px">
                <div class="card-header"><h3>🔧 Code Integration Points</h3></div>
                <div class="card-body">
                    <div class="code-integration-chips">
                        ${codeIntegration.map(c => `<span class="code-chip">🔌 ${typeof c === 'object' ? (c.module || c.name || JSON.stringify(c)) : c}</span>`).join('')}
                    </div>
                </div>
            </div>` : ''}

            <!-- Execution Flow Chart -->
            ${(typeof executionPlan === 'string' && executionPlan) || (Array.isArray(executionPlan) && executionPlan.length) ? `
            <div class="card" style="margin-bottom:24px">
                <div class="card-header"><h3>🗺️ Execution Flow</h3></div>
                <div class="card-body">
                    ${typeof executionPlan === 'string'
                        ? `<p style="color:var(--gray-600);line-height:1.7">${executionPlan}</p>`
                        : `<div id="rec-execution-flowchart"></div>`
                    }
                </div>
            </div>` : ''}

            <!-- Engineering Tasks (Expandable) -->
            ${tasks.length ? `
            <div class="card" style="margin-bottom:24px">
                <div class="card-header"><h3>⚙️ Implementation Tasks (${tasks.length})</h3></div>
                <div class="card-body" id="rec-tasks-container">
                    ${tasks.map((t, i) => {
                        const title = t.task || t.title || t.name || `Task ${i+1}`;
                        const desc = t.description || t.details || '';
                        const estimate = t.estimate || t.duration || '';
                        const priority = t.priority || '';
                        const deps = t.dependencies || [];
                        return `
                        <div class="task-card">
                            <div class="task-card-header" onclick="this.parentElement.querySelector('.task-card-body').classList.toggle('expanded');this.querySelector('.task-card-expand').classList.toggle('expanded')">
                                <div class="task-card-title">${title}</div>
                                <button class="task-card-expand">▼</button>
                            </div>
                            <div class="task-card-body">
                                ${desc ? `<div class="task-card-desc">${desc}</div>` : ''}
                                <div class="task-card-tags">
                                    ${estimate ? `<span class="execution-step-tag">⏱ ${estimate}</span>` : ''}
                                    ${priority ? `<span class="execution-step-tag" style="background:${priority === 'P0' ? '#FEE2E2;color:#991B1B' : '#FEF3C7;color:#92400E'}">${priority}</span>` : ''}
                                    ${deps.map(d => `<span class="execution-step-tag">↗ ${d}</span>`).join('')}
                                </div>
                            </div>
                        </div>`;
                    }).join('')}
                </div>
            </div>` : ''}

            <!-- Assumptions & Risks -->
            ${assumptions.length || risks.length ? `
            <div class="grid-2" style="margin-bottom:24px">
                ${assumptions.length ? `
                <div class="card">
                    <div class="card-header"><h3>💭 Assumptions</h3></div>
                    <div class="card-body"><ul class="spec-list">${assumptions.map(a => `<li>${a}</li>`).join('')}</ul></div>
                </div>` : ''}
                ${risks.length ? `
                <div class="card">
                    <div class="card-header"><h3>⚠️ Risks</h3></div>
                    <div class="card-body"><ul class="spec-list">${risks.map(r => `<li>${typeof r === 'object' ? (r.risk || r.description || JSON.stringify(r)) : r}</li>`).join('')}</ul></div>
                </div>` : ''}
            </div>` : ''}

            <!-- Alternatives -->
            ${alternatives.length ? `
            <div class="card" style="margin-bottom:24px">
                <div class="card-header"><h3>🔄 Alternatives Considered</h3></div>
                <div class="card-body">
                    ${alternatives.map(a => `
                        <div style="display:flex;align-items:center;justify-content:space-between;padding:14px 0;border-bottom:1px solid var(--gray-100)">
                            <div>
                                <div style="font-weight:600;color:var(--gray-800)">${a.feature || a.name || a}</div>
                                ${a.reason ? `<div style="font-size:13px;color:var(--gray-500);margin-top:2px">${a.reason}</div>` : ''}
                            </div>
                            ${a.score ? `<span style="font-size:20px;font-weight:800;color:var(--gray-500)">${a.score}</span>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>` : ''}

            ${rec.implementation_outline ? `
            <div class="card">
                <div class="card-header"><h3>🔨 Implementation Outline</h3></div>
                <div class="card-body"><p style="color:var(--gray-600);line-height:1.7">${rec.implementation_outline}</p></div>
            </div>` : ''}
        `;

        // Render score graph using component
        setTimeout(() => {
            const scoreContainer = document.getElementById('rec-score-graph');
            if (scoreContainer && typeof ScoreGraphRenderer !== 'undefined') {
                ScoreGraphRenderer.renderBreakdown(scoreContainer, breakdown);
            }

            // Render execution flowchart
            const flowContainer = document.getElementById('rec-execution-flowchart');
            if (flowContainer && Array.isArray(executionPlan) && executionPlan.length && typeof FlowchartRenderer !== 'undefined') {
                FlowchartRenderer.renderExecutionPlan(flowContainer, executionPlan);
            }
        }, 100);
    },

    // ---- Specs ----
    async specs(el) {
        let specs = [];
        try {
            const res = await API.getSpecs(App.project.id);
            specs = res.results || res || [];
        } catch(e) {}

        el.innerHTML = `
            <div class="card">
                <div class="card-header"><h3>📄 Generated Specifications</h3></div>
                <div class="card-body" style="padding:0">
                    ${specs.length ? specs.map(s => `
                        <div style="padding:20px 24px;border-bottom:1px solid var(--gray-100);cursor:pointer" onclick="Pages.showSpecDetail('${s.id}')">
                            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
                                <h4 style="font-size:15px;font-weight:700">${s.title}</h4>
                                <div style="display:flex;gap:8px;align-items:center">
                                    <span class="tag status-${s.status}">${s.status}</span>
                                    <span style="font-size:13px;color:var(--gray-500)">v${s.current_version}</span>
                                </div>
                            </div>
                            <div style="display:flex;gap:16px;align-items:center">
                                <div style="font-size:13px;color:var(--gray-500)">${s.artifact_type.toUpperCase()}</div>
                                <div>
                                    <span style="font-size:12px;color:var(--gray-500)">Readiness:</span>
                                    <span style="font-weight:700;color:${s.readiness_score >= 80 ? 'var(--success)' : s.readiness_score >= 50 ? 'var(--warning)' : 'var(--danger)'}">${s.readiness_score || 0}%</span>
                                </div>
                                <div style="font-size:13px;color:var(--gray-500)">${App.formatDate(s.created_at)}</div>
                            </div>
                        </div>
                    `).join('') : '<div class="empty-state"><div class="icon">📄</div><h3>No specs yet</h3><p>Generate a spec from an opportunity.</p></div>'}
                </div>
            </div>`;
    },

    async showSpecDetail(id) {
        App.navigate('spec-detail');
        document.getElementById('page-title').textContent = 'Spec Detail';
        const el = document.getElementById('page-content');
        el.innerHTML = '<div class="loading-overlay"><div class="loading-spinner lg"></div></div>';

        try {
            const spec = await API.getSpec(id);
            const content = spec.latest_content || {};
            const prd = content.prd || {};
            const readiness = content.readiness_score || {};

            el.innerHTML = `
                <div style="margin-bottom:24px;display:flex;align-items:center;justify-content:space-between">
                    <div>
                        <button class="btn btn-ghost btn-sm" onclick="App.navigate('specs')">← Back to Specs</button>
                        <h2 style="font-size:22px;font-weight:800;margin-top:8px">${spec.title}</h2>
                        <div style="display:flex;gap:8px;margin-top:8px">
                            <span class="tag status-${spec.status}">${spec.status}</span>
                            <span class="tag tag-gray">v${spec.current_version}</span>
                        </div>
                    </div>
                    <div style="display:flex;gap:8px">
                        <button class="btn btn-secondary btn-sm" onclick="Pages.specChangeStatus('${id}','review')">Submit for Review</button>
                        <button class="btn btn-success btn-sm" onclick="Pages.specChangeStatus('${id}','approved')">✓ Approve</button>
                    </div>
                </div>

                <div class="grid-sidebar">
                    <div>
                        ${prd.overview ? `<div class="card" style="margin-bottom:16px"><div class="card-header"><h3>Overview</h3></div><div class="card-body"><p style="color:var(--gray-600);line-height:1.7">${prd.overview}</p></div></div>` : ''}

                        ${prd.goals ? `<div class="card" style="margin-bottom:16px"><div class="card-header"><h3>Goals</h3></div><div class="card-body"><ul class="spec-list">${prd.goals.map(g => `<li>${g}</li>`).join('')}</ul></div></div>` : ''}

                        ${content.user_stories ? `<div class="card" style="margin-bottom:16px"><div class="card-header"><h3>User Stories</h3></div><div class="card-body">
                            ${content.user_stories.map(s => `
                                <div style="padding:12px 0;border-bottom:1px solid var(--gray-100)">
                                    <p style="font-weight:600;margin-bottom:4px">As a ${s.role}, I want to ${s.action} so that ${s.benefit}</p>
                                    ${s.acceptance_criteria ? `<ul style="padding-left:20px;margin-top:8px">${s.acceptance_criteria.map(c => `<li style="font-size:13px;color:var(--gray-600)">${c}</li>`).join('')}</ul>` : ''}
                                </div>
                            `).join('')}
                        </div></div>` : ''}

                        ${content.engineering_tasks ? `<div class="card" style="margin-bottom:16px"><div class="card-header"><h3>Engineering Tasks</h3></div><div class="card-body" style="padding:0">
                            <table class="data-table"><thead><tr><th>Task</th><th>Estimate</th><th>Priority</th></tr></thead><tbody>
                                ${content.engineering_tasks.map(t => `<tr><td>${t.task}</td><td>${t.estimate}</td><td><span class="tag ${t.priority === 'P0' ? 'tag-danger' : 'tag-warning'}">${t.priority}</span></td></tr>`).join('')}
                            </tbody></table>
                        </div></div>` : ''}

                        ${content.edge_cases ? `<div class="card" style="margin-bottom:16px"><div class="card-header"><h3>Edge Cases</h3></div><div class="card-body"><ul class="spec-list">${content.edge_cases.map(e => `<li>${e}</li>`).join('')}</ul></div></div>` : ''}

                        ${content.qa_checklist ? `<div class="card" style="margin-bottom:16px"><div class="card-header"><h3>QA Checklist</h3></div><div class="card-body"><ul class="spec-list">${content.qa_checklist.map(q => `<li>${q}</li>`).join('')}</ul></div></div>` : ''}
                    </div>

                    <div>
                        <div class="card" style="margin-bottom:16px">
                            <div class="card-header"><h3>Readiness Score</h3></div>
                            <div class="card-body" style="text-align:center">
                                <div class="readiness-circle ${(readiness.total||0) >= 80 ? 'readiness-high' : (readiness.total||0) >= 50 ? 'readiness-medium' : 'readiness-low'}">
                                    ${readiness.total || spec.readiness_score || 0}%
                                </div>
                                <div style="margin-top:16px;text-align:left">
                                    ${[
                                        ['Validation Rules', readiness.validation_rules],
                                        ['Error States', readiness.error_states],
                                        ['Edge Cases', readiness.edge_cases],
                                        ['Performance Reqs', readiness.performance_requirements],
                                        ['Security Reqs', readiness.security_requirements],
                                    ].map(([label, val]) => `
                                        <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--gray-100)">
                                            <span style="font-size:13px">${label}</span>
                                            <span style="font-size:14px">${val ? '✅' : '❌'}</span>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>

                        <div class="card" style="margin-bottom:16px">
                            <div class="card-header"><h3>🤖 Chat with AI</h3></div>
                            <div class="chat-container">
                                <div class="chat-messages" id="spec-chat-messages">
                                    <div class="chat-message ai">
                                        <div class="chat-bubble">Hi! I can help refine this spec. Try: "Add error handling for network failures" or "Add a section on security requirements"</div>
                                    </div>
                                </div>
                                <div class="chat-input-area">
                                    <input type="text" id="spec-chat-input" placeholder="Ask AI to edit the spec...">
                                    <button class="btn btn-primary btn-sm" id="btn-spec-chat">Send</button>
                                </div>
                            </div>
                        </div>

                        ${spec.versions && spec.versions.length > 1 ? `
                        <div class="card">
                            <div class="card-header"><h3>Version History</h3></div>
                            <div class="card-body" style="padding:0">
                                ${spec.versions.map(v => `
                                    <div style="padding:12px 16px;border-bottom:1px solid var(--gray-100)">
                                        <div style="display:flex;justify-content:space-between">
                                            <span style="font-weight:600">v${v.version_number}</span>
                                            <span style="font-size:12px;color:var(--gray-500)">${App.formatDate(v.created_at)}</span>
                                        </div>
                                        <p style="font-size:13px;color:var(--gray-500);margin-top:4px">${v.change_summary || 'No description'}</p>
                                    </div>
                                `).join('')}
                            </div>
                        </div>` : ''}
                    </div>
                </div>`;

            // Bind chat
            const chatBtn = document.getElementById('btn-spec-chat');
            const chatInput = document.getElementById('spec-chat-input');
            const chatSend = async () => {
                const msg = chatInput.value.trim();
                if (!msg) return;
                const msgs = document.getElementById('spec-chat-messages');
                msgs.innerHTML += `<div class="chat-message user"><div class="chat-bubble">${msg}</div></div>`;
                chatInput.value = '';
                msgs.innerHTML += `<div class="chat-message ai"><div class="chat-bubble"><div class="loading-spinner"></div> Thinking...</div></div>`;
                msgs.scrollTop = msgs.scrollHeight;

                try {
                    const result = await API.chatSpec(id, msg);
                    const lastBubble = msgs.querySelector('.chat-message.ai:last-child .chat-bubble');
                    const changes = result.results?.spec_chat?.change_summary || result.change_summary || 'Changes applied';
                    lastBubble.innerHTML = `Done! ${changes}. <br><a href="#" onclick="Pages.showSpecDetail('${id}');return false" style="color:var(--primary)">Refresh to see changes</a>`;
                } catch(e) {
                    const lastBubble = msgs.querySelector('.chat-message.ai:last-child .chat-bubble');
                    lastBubble.textContent = 'Error: ' + e.message;
                }
            };
            chatBtn?.addEventListener('click', chatSend);
            chatInput?.addEventListener('keypress', (e) => { if (e.key === 'Enter') chatSend(); });

        } catch(e) {
            el.innerHTML = `<div class="empty-state"><p>Error: ${e.message}</p></div>`;
        }
    },

    async specChangeStatus(id, status) {
        try {
            await API.updateSpecStatus(id, status);
            Toast.show(`Spec status updated to ${status}`, 'success');
            Pages.showSpecDetail(id);
        } catch(e) { Toast.show(e.message, 'error'); }
    },

    // ---- Analytics ----
    async analytics(el) {
        let data = {};
        let insightData = {};
        let oppData = {};
        try {
            data = await API.getDashboard(App.project.id);
            insightData = await API.getInsightAnalytics(App.project.id);
            oppData = await API.getOppAnalytics(App.project.id);
        } catch(e) {}

        const agentPerf = data.agent_performance || {};
        const segPain = insightData.segment_pain_distribution || {};

        el.innerHTML = `
            <div class="grid-2" style="margin-bottom:24px">
                <div class="card">
                    <div class="card-header"><h3>📊 Insight Distribution by Severity</h3></div>
                    <div class="card-body">
                        ${Object.entries(insightData.by_severity || {}).map(([k, v]) => `
                            <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
                                <span class="tag severity-${k}" style="width:80px;text-align:center">${k}</span>
                                <div style="flex:1"><div class="score-bar"><div class="score-bar-fill ${k === 'critical' ? 'low' : k === 'high' ? 'medium' : 'high'}" style="width:${Math.min(v * 10, 100)}%"></div></div></div>
                                <span style="font-weight:700;min-width:30px">${v}</span>
                            </div>
                        `).join('') || '<p style="color:var(--gray-500)">No data</p>'}
                    </div>
                </div>

                <div class="card">
                    <div class="card-header"><h3>👥 Pain by Segment</h3></div>
                    <div class="card-body">
                        ${Object.entries(segPain).map(([k, v]) => `
                            <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
                                <span class="tag tag-primary" style="width:100px;text-align:center">${k}</span>
                                <div style="flex:1"><div class="score-bar"><div class="score-bar-fill high" style="width:${Math.min(v * 15, 100)}%"></div></div></div>
                                <span style="font-weight:700;min-width:30px">${v}</span>
                            </div>
                        `).join('') || '<p style="color:var(--gray-500)">No data</p>'}
                    </div>
                </div>
            </div>

            <div class="grid-2" style="margin-bottom:24px">
                <div class="card">
                    <div class="card-header"><h3>🎯 Opportunity Pipeline</h3></div>
                    <div class="card-body">
                        ${Object.entries(oppData.by_status || {}).map(([k, v]) => `
                            <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--gray-100)">
                                <span class="tag status-${k}">${k}</span>
                                <span style="font-size:20px;font-weight:800">${v}</span>
                            </div>
                        `).join('') || '<p style="color:var(--gray-500)">No data</p>'}
                    </div>
                </div>

                <div class="card">
                    <div class="card-header"><h3>🤖 AI Agent Performance</h3></div>
                    <div class="card-body">
                        <div class="impact-grid">
                            <div class="impact-item"><div class="label">Total Runs</div><div class="value">${agentPerf.total_runs || 0}</div></div>
                            <div class="impact-item"><div class="label">Successful</div><div class="value" style="color:var(--success)">${agentPerf.successful || 0}</div></div>
                            <div class="impact-item"><div class="label">Failed</div><div class="value" style="color:var(--danger)">${agentPerf.failed || 0}</div></div>
                            <div class="impact-item"><div class="label">Avg Duration</div><div class="value">${agentPerf.avg_duration || 0}s</div></div>
                        </div>
                    </div>
                </div>
            </div>

            ${insightData.emerging && insightData.emerging.length ? `
            <div class="card">
                <div class="card-header"><h3>📈 Emerging Pain Points (Rising Trends)</h3></div>
                <div class="card-body" style="padding:0">
                    <table class="data-table">
                        <thead><tr><th>Insight</th><th>Frequency</th><th>Severity</th></tr></thead>
                        <tbody>
                            ${insightData.emerging.map(e => `
                                <tr><td><strong>${e.title}</strong></td><td>${e.frequency}</td><td><span class="tag severity-${e.severity}">${e.severity}</span></td></tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>` : ''}
        `;
    },

    // ---- Codebase (Enhanced with GitHub Integration) ----
    async codebase(el) {
        let codebases = [];
        let analyses = [];
        let githubStatus = { connected: false };
        let linkedRepos = [];
        try {
            const res = await API.getCodebases(App.project.id);
            codebases = res.results || res || [];
            const aRes = await API.getCodebaseAnalyses(App.project.id);
            analyses = aRes.results || aRes || [];
        } catch(e) {}

        // Check GitHub status
        try {
            githubStatus = await API.githubStatus(App.org.id);
        } catch(e) {}

        // Get linked repos
        try {
            const lr = await API.githubLinkedRepos(App.project.id);
            linkedRepos = lr.repos || [];
        } catch(e) {}

        const ghConnected = githubStatus.connected;
        const ghUser = githubStatus.integration?.github_username || '';

        el.innerHTML = `
            <div class="metrics-grid">
                <div class="metric-card"><div class="metric-label">Codebases</div><div class="metric-value">${codebases.length}</div></div>
                <div class="metric-card"><div class="metric-label">GitHub Repos</div><div class="metric-value">${linkedRepos.length}</div></div>
                <div class="metric-card"><div class="metric-label">Analyses</div><div class="metric-value">${analyses.filter(a => a.status === 'completed').length}</div></div>
                <div class="metric-card ${ghConnected ? '' : 'highlight'}"><div class="metric-label">GitHub</div><div class="metric-value" style="font-size:16px">${ghConnected ? '✅ ' + ghUser : '🔗 Not Connected'}</div></div>
            </div>

            <!-- GitHub Repository Linking -->
            <div class="card" style="margin-bottom:24px">
                <div class="card-header">
                    <h3>🐙 GitHub Repositories</h3>
                    <div style="display:flex;gap:8px">
                        ${ghConnected ? `
                            <button class="btn btn-primary btn-sm" id="btn-link-github-repo">+ Link Repository</button>
                            <button class="btn btn-secondary btn-sm" id="btn-browse-repos">Browse Repos</button>
                        ` : `
                            <button class="btn btn-primary btn-sm" id="btn-connect-github">🔗 Connect GitHub</button>
                        `}
                    </div>
                </div>

                <!-- Connect GitHub Panel (hidden when connected) -->
                ${!ghConnected ? `
                <div class="card-body" id="github-connect-panel">
                    <div style="text-align:center;padding:16px">
                        <div style="font-size:48px;margin-bottom:12px">🐙</div>
                        <h4 style="margin-bottom:8px">Connect Your GitHub Account</h4>
                        <p style="color:var(--gray-600);margin-bottom:20px;max-width:450px;margin-left:auto;margin-right:auto">
                            Link your GitHub repositories so PMBrain AI can analyze your codebase and provide better feature recommendations.
                        </p>
                        <div class="form-group" style="max-width:500px;margin:0 auto 16px">
                            <label>GitHub Personal Access Token</label>
                            <input type="password" id="github-token-input" placeholder="ghp_xxxxxxxxxxxxxxxxxxxx" style="font-family:monospace">
                            <p style="font-size:12px;color:var(--gray-400);margin-top:4px">
                                Generate a token at <a href="https://github.com/settings/tokens" target="_blank" style="color:var(--primary)">github.com/settings/tokens</a> 
                                with <strong>repo</strong> and <strong>read:user</strong> scopes.
                            </p>
                        </div>
                        <button class="btn btn-primary" id="btn-github-token-connect">Connect with Token</button>
                    </div>
                </div>` : ''}

                <!-- Link repo panel (hidden by default) -->
                <div class="card-body" id="link-repo-panel" style="display:none">
                    <div class="form-group">
                        <label>GitHub Repository URL</label>
                        <input type="text" id="github-repo-url" placeholder="https://github.com/owner/repository">
                    </div>
                    <button class="btn btn-primary" id="btn-submit-link-repo">Link & Analyze Repository</button>
                    <button class="btn btn-ghost btn-sm" id="btn-cancel-link-repo" style="margin-left:8px">Cancel</button>
                </div>

                <!-- Browse repos panel (hidden by default) -->
                <div class="card-body" id="browse-repos-panel" style="display:none">
                    <div id="browse-repos-loading" class="loading-overlay" style="padding:24px"><div class="loading-spinner"></div><p>Loading repositories...</p></div>
                    <div id="browse-repos-list"></div>
                </div>

                <!-- Linked repos list -->
                ${linkedRepos.length ? `
                <div class="card-body" style="padding:0">
                    <table class="data-table">
                        <thead><tr><th>Repository</th><th>Branch</th><th>Language</th><th>Clone Status</th><th>Analysis</th><th>Actions</th></tr></thead>
                        <tbody>
                            ${linkedRepos.map(r => `
                                <tr>
                                    <td>
                                        <div style="display:flex;align-items:center;gap:8px">
                                            <span style="font-size:18px">🐙</span>
                                            <div>
                                                <strong><a href="${r.repo_url}" target="_blank" style="color:var(--primary);text-decoration:none">${r.repo_full_name}</a></strong>
                                                ${r.is_private ? ' <span class="tag tag-warning" style="font-size:10px">private</span>' : ''}
                                                ${r.description ? `<div style="font-size:12px;color:var(--gray-500)">${App.truncate(r.description, 60)}</div>` : ''}
                                            </div>
                                        </div>
                                    </td>
                                    <td><span class="tag tag-gray">${r.default_branch}</span></td>
                                    <td>${r.language ? `<span class="tag tag-primary">${r.language}</span>` : '-'}</td>
                                    <td><span class="tag ${r.clone_status === 'completed' ? 'tag-success' : r.clone_status === 'cloning' ? 'tag-warning' : r.clone_status === 'failed' ? 'tag-danger' : 'tag-gray'}">${r.clone_status}</span></td>
                                    <td>${r.analysis_status ? `<span class="tag ${r.analysis_status === 'completed' ? 'tag-success' : r.analysis_status === 'processing' ? 'tag-warning' : 'tag-gray'}">${r.analysis_status}</span>` : '<span class="tag tag-gray">Not analyzed</span>'}</td>
                                    <td>
                                        <button class="btn btn-primary btn-sm" onclick="Pages.analyzeGitHubRepo('${r.id}', '${r.repo_full_name}')">⚡ Analyze</button>
                                        ${r.codebase_id && r.analysis_status === 'completed' ? `<button class="btn btn-secondary btn-sm" onclick="Pages.showCodeAnalysis('${r.codebase_id}')" style="margin-left:4px">View</button>` : ''}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>` : (ghConnected ? '<div class="card-body"><div class="empty-state" style="padding:24px"><p>No repositories linked yet. Click "Link Repository" to add one.</p></div></div>' : '')}
            </div>

            <!-- File Upload Section -->
            <div class="card" style="margin-bottom:24px">
                <div class="card-header">
                    <h3>📦 Upload Codebase (ZIP/TAR)</h3>
                    <button class="btn btn-secondary btn-sm" id="btn-toggle-upload">+ Upload Code</button>
                </div>
                <div class="card-body" id="code-upload-area" style="display:none">
                    <p style="margin-bottom:16px;color:var(--gray-600)">Upload your product codebase as a <strong>.zip</strong> or <strong>.tar.gz</strong> archive.</p>
                    <div class="form-group">
                        <label>Codebase Name</label>
                        <input type="text" id="cb-name" placeholder="e.g., My Product Backend">
                    </div>
                    <div class="form-group">
                        <label>Code Archive (zip or tar.gz, max 100MB)</label>
                        <input type="file" id="cb-file" accept=".zip,.tar.gz,.tgz" style="padding:10px">
                    </div>
                    <button class="btn btn-primary" id="btn-upload-codebase">Upload & Analyze</button>
                    <p style="font-size:12px;color:var(--gray-400);margin-top:8px">⚡ Only static analysis — no code execution.</p>
                </div>
            </div>

            <!-- Uploaded Codebases Table -->
            ${codebases.length ? `
            <div class="card" style="margin-bottom:24px">
                <div class="card-header"><h3>📦 Uploaded Codebases</h3></div>
                <div class="card-body" style="padding:0">
                    <table class="data-table">
                        <thead><tr><th>Name</th><th>Type</th><th>Files</th><th>Status</th><th>Actions</th></tr></thead>
                        <tbody>
                            ${codebases.map(c => `
                                <tr>
                                    <td><strong>${c.name}</strong></td>
                                    <td><span class="tag ${c.source_type === 'git' ? 'tag-purple' : 'tag-gray'}">${c.source_type}</span></td>
                                    <td>${c.file_count} files</td>
                                    <td>${c.latest_analysis ? `<span class="tag ${c.latest_analysis.status === 'completed' ? 'tag-success' : c.latest_analysis.status === 'processing' ? 'tag-warning' : 'tag-gray'}">${c.latest_analysis.status}</span>` : '<span class="tag tag-gray">Not analyzed</span>'}</td>
                                    <td>
                                        <button class="btn btn-primary btn-sm" onclick="Pages.analyzeCodebase('${c.id}')">⚡ Analyze</button>
                                        ${c.latest_analysis && c.latest_analysis.status === 'completed' ? `<button class="btn btn-secondary btn-sm" onclick="Pages.showCodeAnalysis('${c.latest_analysis.id}')" style="margin-left:4px">View</button>` : ''}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>` : ''}

            ${analyses.filter(a => a.status === 'completed').length ? `
            <div class="card">
                <div class="card-header"><h3>🔬 Latest Analysis</h3></div>
                <div class="card-body">
                    ${analyses.filter(a => a.status === 'completed').slice(0, 1).map(a => `
                        <h4 style="margin-bottom:12px">${a.codebase_name || 'Codebase'}</h4>
                        <p style="color:var(--gray-600);line-height:1.7;margin-bottom:16px">${a.system_summary || 'No summary'}</p>
                        ${a.technology_stack && a.technology_stack.length ? `<div style="margin-bottom:12px"><strong>Tech Stack:</strong> ${a.technology_stack.map(t => `<span class="tag tag-primary" style="margin:2px">${t}</span>`).join('')}</div>` : ''}
                        ${a.existing_features && a.existing_features.length ? `
                        <div style="margin-bottom:12px"><strong>Existing Features:</strong>
                            <ul class="spec-list">${a.existing_features.slice(0, 8).map(f => `<li>${typeof f === 'object' ? (f.name || f.description || JSON.stringify(f)) : f}</li>`).join('')}</ul>
                        </div>` : ''}
                        <button class="btn btn-secondary btn-sm" onclick="Pages.showCodeAnalysis('${a.id}')">View Full Analysis</button>
                    `).join('')}
                </div>
            </div>` : ''}

            <!-- AI Analysis Loading Overlay (shown during analysis) -->
            <div id="ai-analysis-overlay" style="display:none" class="ai-analysis-modal">
                <div class="ai-analysis-content">
                    <div class="ai-analysis-animation">
                        <div class="ai-pulse-ring"></div>
                        <div class="ai-icon">🧠</div>
                    </div>
                    <h3 id="ai-analysis-title">Analyzing Codebase...</h3>
                    <div class="ai-analysis-steps" id="ai-analysis-steps"></div>
                    <p id="ai-analysis-detail" style="color:var(--gray-500);font-size:13px;margin-top:12px"></p>
                </div>
            </div>
        `;

        // Event bindings
        document.getElementById('btn-toggle-upload')?.addEventListener('click', () => {
            const area = document.getElementById('code-upload-area');
            area.style.display = area.style.display === 'none' ? 'block' : 'none';
        });

        // Connect GitHub with token
        document.getElementById('btn-connect-github')?.addEventListener('click', () => {
            const panel = document.getElementById('github-connect-panel');
            if (panel) panel.style.display = panel.style.display === 'none' ? 'block' : 'block';
        });

        document.getElementById('btn-github-token-connect')?.addEventListener('click', async () => {
            const token = document.getElementById('github-token-input').value.trim();
            if (!token) { Toast.show('Please enter a GitHub token', 'error'); return; }
            try {
                Toast.show('Connecting to GitHub...', 'info');
                const result = await API.githubConnectToken(token, App.org.id);
                Toast.show(`Connected as ${result.integration.github_username}!`, 'success');
                Pages.codebase(el);
            } catch(e) { Toast.show('Connection failed: ' + e.message, 'error'); }
        });

        // Link repo panel toggle
        document.getElementById('btn-link-github-repo')?.addEventListener('click', () => {
            document.getElementById('link-repo-panel').style.display = 'block';
            document.getElementById('browse-repos-panel').style.display = 'none';
        });
        document.getElementById('btn-cancel-link-repo')?.addEventListener('click', () => {
            document.getElementById('link-repo-panel').style.display = 'none';
        });

        // Submit link repo
        document.getElementById('btn-submit-link-repo')?.addEventListener('click', async () => {
            const repoUrl = document.getElementById('github-repo-url').value.trim();
            if (!repoUrl) { Toast.show('Please enter a repository URL', 'error'); return; }
            try {
                Pages.showAIAnalysisOverlay('Linking Repository...', [
                    { text: 'Validating repository URL...', status: 'active' },
                    { text: 'Checking access permissions...', status: 'pending' },
                    { text: 'Fetching repository metadata...', status: 'pending' },
                ]);
                const result = await API.githubLinkRepo(App.project.id, repoUrl);
                Toast.show(result.message, 'success');
                Pages.hideAIAnalysisOverlay();
                Pages.codebase(el);
            } catch(e) {
                Pages.hideAIAnalysisOverlay();
                Toast.show(e.message, 'error');
            }
        });

        // Browse repos
        document.getElementById('btn-browse-repos')?.addEventListener('click', async () => {
            const panel = document.getElementById('browse-repos-panel');
            panel.style.display = 'block';
            document.getElementById('link-repo-panel').style.display = 'none';
            document.getElementById('browse-repos-loading').style.display = 'flex';
            document.getElementById('browse-repos-list').innerHTML = '';

            try {
                const data = await API.githubRepos(App.org.id, App.project.id);
                const repos = data.repos || [];
                document.getElementById('browse-repos-loading').style.display = 'none';
                document.getElementById('browse-repos-list').innerHTML = repos.length ? `
                    <div style="max-height:400px;overflow-y:auto">
                        ${repos.map(r => `
                            <div style="display:flex;align-items:center;justify-content:space-between;padding:12px 0;border-bottom:1px solid var(--gray-100)">
                                <div>
                                    <div style="font-weight:600">${r.full_name} ${r.private ? '<span class="tag tag-warning" style="font-size:10px">private</span>' : ''}</div>
                                    <div style="font-size:12px;color:var(--gray-500)">${r.description || 'No description'} · ${r.language || 'Unknown'} · ⭐ ${r.stargazers_count}</div>
                                </div>
                                ${r.already_linked ? '<span class="tag tag-success">Linked</span>' : `<button class="btn btn-primary btn-sm" onclick="Pages.quickLinkRepo('${r.html_url}')">Link</button>`}
                            </div>
                        `).join('')}
                    </div>
                ` : '<p style="color:var(--gray-500);text-align:center;padding:24px">No repositories found.</p>';
            } catch(e) {
                document.getElementById('browse-repos-loading').style.display = 'none';
                document.getElementById('browse-repos-list').innerHTML = `<p style="color:var(--danger);padding:16px">Error: ${e.message}</p>`;
            }
        });

        // Upload codebase
        document.getElementById('btn-upload-codebase')?.addEventListener('click', async () => {
            const name = document.getElementById('cb-name').value;
            const fileInput = document.getElementById('cb-file');
            const file = fileInput.files[0];
            if (!file) { Toast.show('Please select a file', 'error'); return; }
            if (!name) { Toast.show('Please enter a name', 'error'); return; }

            const formData = new FormData();
            formData.append('file', file);
            formData.append('name', name);
            formData.append('organization', App.org.id);
            formData.append('project', App.project.id);

            Pages.showAIAnalysisOverlay('Uploading Codebase...', [
                { text: 'Uploading archive...', status: 'active' },
                { text: 'Extracting files...', status: 'pending' },
                { text: 'Running AI analysis...', status: 'pending' },
            ]);

            try {
                const cb = await API.uploadCodebase(formData);
                Pages.updateAIAnalysisStep(0, 'done');
                Pages.updateAIAnalysisStep(1, 'active');

                // Auto-trigger analysis
                try {
                    Pages.updateAIAnalysisStep(1, 'done');
                    Pages.updateAIAnalysisStep(2, 'active');
                    Pages.updateAIAnalysisDetail('Gemini AI is analyzing your codebase structure, modules, features, and APIs...');
                    await API.analyzeCodebase(cb.id);
                    Pages.updateAIAnalysisStep(2, 'done');
                    Toast.show('Analysis complete!', 'success');
                } catch(e) {
                    Toast.show('Analysis: ' + e.message, 'error');
                }
                Pages.hideAIAnalysisOverlay();
                Pages.codebase(el);
            } catch(e) {
                Pages.hideAIAnalysisOverlay();
                Toast.show(e.message, 'error');
            }
        });
    },

    // Quick link a repo from browse list
    async quickLinkRepo(repoUrl) {
        try {
            Pages.showAIAnalysisOverlay('Linking Repository...', [
                { text: 'Validating repository...', status: 'active' },
                { text: 'Fetching metadata...', status: 'pending' },
            ]);
            const result = await API.githubLinkRepo(App.project.id, repoUrl);
            Toast.show(result.message, 'success');
            Pages.hideAIAnalysisOverlay();
            App.loadPage('codebase');
        } catch(e) {
            Pages.hideAIAnalysisOverlay();
            Toast.show(e.message, 'error');
        }
    },

    // Analyze a GitHub-linked repo
    async analyzeGitHubRepo(repoId, repoName) {
        Pages.showAIAnalysisOverlay(`Analyzing ${repoName}...`, [
            { text: 'Cloning repository (shallow, read-only)...', status: 'active' },
            { text: 'Extracting code structure...', status: 'pending' },
            { text: 'AI analyzing modules & features...', status: 'pending' },
            { text: 'Generating capability map...', status: 'pending' },
        ]);
        Pages.updateAIAnalysisDetail('Securely cloning the repository for static analysis. No code is executed.');

        try {
            // Simulate step progression with delay
            setTimeout(() => { Pages.updateAIAnalysisStep(0, 'done'); Pages.updateAIAnalysisStep(1, 'active'); }, 2000);
            setTimeout(() => {
                Pages.updateAIAnalysisStep(1, 'done');
                Pages.updateAIAnalysisStep(2, 'active');
                Pages.updateAIAnalysisDetail('Gemini AI is analyzing architecture, frameworks, modules, APIs, and features...');
            }, 4000);

            const result = await API.githubAnalyzeRepo(repoId);

            Pages.updateAIAnalysisStep(2, 'done');
            Pages.updateAIAnalysisStep(3, 'done');
            Pages.updateAIAnalysisDetail('Analysis complete!');
            Toast.show(result.message || 'Analysis complete!', 'success');

            setTimeout(() => {
                Pages.hideAIAnalysisOverlay();
                App.loadPage('codebase');
            }, 1000);
        } catch(e) {
            Pages.hideAIAnalysisOverlay();
            Toast.show('Analysis error: ' + e.message, 'error');
        }
    },

    async analyzeCodebase(id) {
        Pages.showAIAnalysisOverlay('Analyzing Codebase...', [
            { text: 'Reading file structure...', status: 'active' },
            { text: 'AI analyzing code patterns...', status: 'pending' },
            { text: 'Generating insights...', status: 'pending' },
        ]);
        Pages.updateAIAnalysisDetail('Gemini AI is performing deep static analysis of your codebase...');

        try {
            setTimeout(() => { Pages.updateAIAnalysisStep(0, 'done'); Pages.updateAIAnalysisStep(1, 'active'); }, 1500);
            await API.analyzeCodebase(id);
            Pages.updateAIAnalysisStep(1, 'done');
            Pages.updateAIAnalysisStep(2, 'done');
            Toast.show('Analysis complete!', 'success');
            setTimeout(() => {
                Pages.hideAIAnalysisOverlay();
                App.loadPage('codebase');
            }, 800);
        } catch(e) {
            Pages.hideAIAnalysisOverlay();
            Toast.show('Analysis error: ' + e.message, 'error');
        }
    },

    // === Interactive AI Analysis Overlay ===
    showAIAnalysisOverlay(title, steps = []) {
        let overlay = document.getElementById('ai-analysis-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'ai-analysis-overlay';
            overlay.className = 'ai-analysis-modal';
            overlay.innerHTML = `
                <div class="ai-analysis-content">
                    <div class="ai-analysis-animation">
                        <div class="ai-pulse-ring"></div>
                        <div class="ai-icon">🧠</div>
                    </div>
                    <h3 id="ai-analysis-title"></h3>
                    <div class="ai-analysis-steps" id="ai-analysis-steps"></div>
                    <p id="ai-analysis-detail"></p>
                </div>
            `;
            document.body.appendChild(overlay);
        }
        overlay.style.display = 'flex';
        document.getElementById('ai-analysis-title').textContent = title;
        document.getElementById('ai-analysis-detail').textContent = '';

        const stepsEl = document.getElementById('ai-analysis-steps');
        stepsEl.innerHTML = steps.map((s, i) => `
            <div class="ai-step ${s.status}" data-step="${i}">
                <span class="ai-step-icon">${s.status === 'active' ? '<div class="loading-spinner" style="width:16px;height:16px"></div>' : s.status === 'done' ? '✅' : '⬜'}</span>
                <span class="ai-step-text">${s.text}</span>
            </div>
        `).join('');
    },

    updateAIAnalysisStep(index, newStatus) {
        const step = document.querySelector(`.ai-step[data-step="${index}"]`);
        if (!step) return;
        step.className = `ai-step ${newStatus}`;
        const icon = step.querySelector('.ai-step-icon');
        if (newStatus === 'active') icon.innerHTML = '<div class="loading-spinner" style="width:16px;height:16px"></div>';
        else if (newStatus === 'done') icon.innerHTML = '✅';
        else icon.innerHTML = '⬜';
    },

    updateAIAnalysisDetail(text) {
        const el = document.getElementById('ai-analysis-detail');
        if (el) el.textContent = text;
    },

    hideAIAnalysisOverlay() {
        const overlay = document.getElementById('ai-analysis-overlay');
        if (overlay) overlay.style.display = 'none';
    },

    async showCodeAnalysis(id) {
        // Navigate to a full-page view for the rich analysis
        App.navigate('code-analysis-detail');
        document.getElementById('page-title').textContent = '🔬 Codebase Analysis';
        const el = document.getElementById('page-content');
        el.innerHTML = '<div class="loading-overlay"><div class="loading-spinner lg"></div><p>Loading analysis...</p></div>';

        try {
            const a = await API.getCodebaseAnalysis(id);
            const comp = a.competitor_comparison || {};
            const newFeatures = a.new_feature_opportunities || [];
            const missingCaps = a.missing_capabilities || [];
            const improvements = a.improvement_areas || [];

            el.innerHTML = `
                <button class="btn btn-ghost btn-sm" onclick="App.navigate('codebase')" style="margin-bottom:16px">\u2190 Back to Codebase</button>

                <!-- Analysis Hero -->
                <div class="ai-recommendation-enhanced" style="margin-bottom:24px">
                    <div class="ai-rec-header">
                        <div>
                            <div class="ai-rec-badge">\uD83D\uDD2C PRODUCT CAPABILITY ANALYSIS</div>
                            <div class="ai-rec-title">${a.codebase_name || 'Codebase'}</div>
                            <div class="ai-rec-meta">
                                <span class="ai-rec-meta-item"><strong>${(a.existing_features || []).length}</strong> detected features</span>
                                <span class="ai-rec-meta-item"><strong>${(a.technology_stack || []).length}</strong> technologies</span>
                                <span class="ai-rec-meta-item"><strong>${(a.api_endpoints || []).length}</strong> API endpoints</span>
                                <span class="ai-rec-meta-item"><strong>${newFeatures.length}</strong> new opportunities</span>
                            </div>
                        </div>
                    </div>
                    <p class="ai-rec-summary">${a.system_summary || ''}</p>
                </div>

                <!-- Tech Stack & Architecture -->
                <div class="grid-2" style="margin-bottom:24px">
                    <div class="card">
                        <div class="card-header"><h3>\uD83D\uDEE0\uFE0F Technology Stack</h3></div>
                        <div class="card-body">
                            <div style="display:flex;flex-wrap:wrap;gap:8px">
                                ${(a.technology_stack || []).map(function(t) { return '<span class="tag tag-primary" style="padding:6px 14px;font-size:13px">' + t + '</span>'; }).join('')}
                            </div>
                        </div>
                    </div>
                    <div class="card">
                        <div class="card-header"><h3>\uD83C\uDFD7\uFE0F Architecture Patterns</h3></div>
                        <div class="card-body">
                            <div style="display:flex;flex-wrap:wrap;gap:8px">
                                ${(a.architecture_patterns || []).map(function(p) {
                                    var name = typeof p === 'object' ? (p.name || '') : p;
                                    var desc = typeof p === 'object' && p.description ? p.description : '';
                                    return '<div style="padding:8px 0;border-bottom:1px solid var(--gray-100)"><span class="tag tag-purple" style="margin-right:8px">' + name + '</span>' + (desc ? '<span style="font-size:12px;color:var(--gray-500)">' + desc + '</span>' : '') + '</div>';
                                }).join('')}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Existing Feature Map -->
                ${(a.existing_features || []).length ? '<div class="card" style="margin-bottom:24px"><div class="card-header"><h3>\u2705 Existing Feature Map</h3></div><div class="card-body"><div class="existing-features-tree">' + (a.existing_features || []).map(function(f) {
                    var name = typeof f === 'object' ? (f.name || '') : f;
                    var desc = typeof f === 'object' ? (f.description || '') : '';
                    var completeness = typeof f === 'object' ? (f.completeness || 'complete') : 'complete';
                    var cat = typeof f === 'object' ? (f.category || '') : '';
                    var tagClass = completeness === 'complete' ? 'tag-success' : completeness === 'partial' ? 'tag-warning' : 'tag-gray';
                    return '<div style="display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid var(--gray-100)"><div style="flex:1"><strong style="font-size:14px">' + name + '</strong>' + (desc ? '<br><span style="font-size:12px;color:var(--gray-500)">' + desc + '</span>' : '') + '</div><span class="tag ' + tagClass + '">' + completeness + '</span>' + (cat ? '<span class="tag tag-gray">' + cat + '</span>' : '') + '</div>';
                }).join('') + '</div></div></div>' : ''}

                <!-- Competitor Comparison Table -->
                ${comp.common_competitor_features && comp.common_competitor_features.length ? '<div class="card" style="margin-bottom:24px"><div class="card-header"><h3>\uD83C\uDFC6 Competitor Feature Comparison</h3>' + (comp.detected_product_type ? '<span class="tag tag-primary">' + comp.detected_product_type + '</span>' : '') + '</div><div class="card-body" style="padding:0"><table class="data-table"><thead><tr><th>Feature</th><th>Status in Your Product</th><th>Importance</th></tr></thead><tbody>' + comp.common_competitor_features.map(function(cf) {
                    var statusClass = cf.status === 'present' ? 'tag-success' : cf.status === 'missing' ? 'tag-danger' : 'tag-warning';
                    var impClass = cf.importance === 'critical' ? 'severity-critical' : cf.importance === 'high' ? 'severity-high' : cf.importance === 'medium' ? 'severity-medium' : 'severity-low';
                    return '<tr><td><strong>' + cf.feature + '</strong></td><td><span class="tag ' + statusClass + '">' + cf.status + '</span></td><td><span class="tag ' + impClass + '">' + cf.importance + '</span></td></tr>';
                }).join('') + '</tbody></table></div></div>' : ''}

                ${comp.competitive_gaps && comp.competitive_gaps.length ? '<div class="card" style="margin-bottom:24px"><div class="card-header"><h3>\u26A0\uFE0F Competitive Gaps</h3></div><div class="card-body"><ul class="spec-list">' + comp.competitive_gaps.map(function(g) { return '<li>' + g + '</li>'; }).join('') + '</ul></div></div>' : ''}

                <!-- Missing Capabilities -->
                ${missingCaps.length ? '<div class="card" style="margin-bottom:24px"><div class="card-header"><h3>\uD83D\uDEA8 Missing Capabilities</h3></div><div class="card-body"><ul class="spec-list">' + missingCaps.map(function(c) { return '<li>' + c + '</li>'; }).join('') + '</ul></div></div>' : ''}

                <!-- NEW FEATURE OPPORTUNITIES -->
                ${newFeatures.length ? '<div style="margin-bottom:24px"><h2 style="font-size:20px;font-weight:800;margin-bottom:16px">\uD83D\uDCA1 AI-Suggested New Features (' + newFeatures.length + ')</h2>' + newFeatures.map(function(nf, idx) {
                    var scores = nf.opportunity_scores || {};
                    var timeline = nf.estimated_timeline || {};
                    var engTasks = nf.engineering_tasks || {};
                    var execFlow = nf.execution_flow || [];
                    var totalScore = 0;
                    var scoreCount = 0;
                    ['frequency', 'revenue_impact', 'retention_impact', 'strategic_alignment'].forEach(function(k) { if (scores[k]) { totalScore += scores[k]; scoreCount++; } });
                    var avgScore = scoreCount > 0 ? (totalScore / scoreCount).toFixed(1) : 'N/A';

                    return '<div class="card" style="margin-bottom:16px">'
                        + '<div class="card-header"><h3>\uD83D\uDCA1 ' + (nf.feature_name || 'Feature ' + (idx + 1)) + '</h3><span style="font-size:20px;font-weight:800;color:var(--primary)">' + avgScore + '</span></div>'
                        + '<div class="card-body">'
                        + '<div class="grid-2" style="margin-bottom:16px"><div>'
                        + '<h4 style="font-size:13px;font-weight:700;color:var(--gray-500);margin-bottom:4px">PROBLEM</h4>'
                        + '<p style="font-size:14px;color:var(--gray-700);line-height:1.7">' + (nf.problem_statement || '') + '</p>'
                        + '</div><div>'
                        + '<h4 style="font-size:13px;font-weight:700;color:var(--gray-500);margin-bottom:4px">BUSINESS VALUE</h4>'
                        + '<p style="font-size:14px;color:var(--gray-700);line-height:1.7">' + (nf.business_value || '') + '</p>'
                        + '</div></div>'
                        + (nf.target_users ? '<p style="font-size:13px;color:var(--gray-500);margin-bottom:16px">\uD83D\uDC65 Target Users: <strong>' + nf.target_users + '</strong> \u00B7 Complexity: <span class="tag ' + (nf.implementation_complexity === 'low' ? 'tag-success' : nf.implementation_complexity === 'high' ? 'tag-danger' : 'tag-warning') + '">' + (nf.implementation_complexity || 'medium') + '</span></p>' : '')

                        // Opportunity Score Graph
                        + (Object.keys(scores).length ? '<div style="margin-bottom:20px"><h4 style="font-size:14px;font-weight:700;margin-bottom:12px">\uD83D\uDCCA Opportunity Scores</h4><div id="nf-scores-' + idx + '"></div></div>' : '')

                        // Timeline visualization
                        + (Object.keys(timeline).length ? '<div style="margin-bottom:20px"><h4 style="font-size:14px;font-weight:700;margin-bottom:12px">\uD83D\uDCC5 Implementation Timeline</h4><div class="timeline-viz">' + Object.entries(timeline).map(function(entry, wi) {
                            return '<div class="timeline-week"><div class="timeline-week-header"><div class="timeline-week-num">' + entry[0].replace(/_/g, ' ').toUpperCase() + '</div></div><div class="timeline-week-content">' + entry[1] + '</div></div>';
                        }).join('') + '</div></div>' : '')

                        // Engineering tasks
                        + (Object.keys(engTasks).length ? '<div style="margin-bottom:20px"><h4 style="font-size:14px;font-weight:700;margin-bottom:12px">\u2699\uFE0F Engineering Tasks</h4>' + Object.entries(engTasks).map(function(entry) {
                            return '<div style="margin-bottom:12px"><h5 style="font-size:13px;font-weight:600;text-transform:capitalize;color:var(--gray-600);margin-bottom:6px">' + entry[0] + '</h5><ul class="spec-list">' + (Array.isArray(entry[1]) ? entry[1] : []).map(function(t) { return '<li>' + t + '</li>'; }).join('') + '</ul></div>';
                        }).join('') + '</div>' : '')

                        // Execution Flow
                        + (execFlow.length ? '<div style="margin-bottom:16px"><h4 style="font-size:14px;font-weight:700;margin-bottom:12px">\uD83D\uDDFA\uFE0F Execution Flow</h4><div id="nf-flow-' + idx + '"></div></div>' : '')

                        // Code Integration Points
                        + ((nf.code_integration_points || []).length ? '<div><h4 style="font-size:14px;font-weight:700;margin-bottom:8px">\uD83D\uDD27 Code Integration Points</h4><div style="display:flex;flex-wrap:wrap;gap:6px">' + nf.code_integration_points.map(function(c) { return '<span class="code-chip">' + c + '</span>'; }).join('') + '</div></div>' : '')

                        + '</div></div>';
                }).join('') + '</div>' : ''}

                <!-- Modules & APIs (collapsible) -->
                ${(a.major_modules || []).length ? '<div class="card" style="margin-bottom:24px"><div class="card-header"><h3>\uD83D\uDCE6 Major Modules (' + (a.major_modules || []).length + ')</h3></div><div class="card-body">' + (a.major_modules || []).map(function(m) {
                    var name = typeof m === 'object' ? (m.name || '') : m;
                    var purpose = typeof m === 'object' ? (m.purpose || '') : '';
                    return '<div style="padding:10px 0;border-bottom:1px solid var(--gray-100)"><strong>' + name + '</strong>' + (purpose ? '<br><span style="font-size:13px;color:var(--gray-500)">' + purpose + '</span>' : '') + '</div>';
                }).join('') + '</div></div>' : ''}

                ${(a.api_endpoints || []).length ? '<div class="card" style="margin-bottom:24px"><div class="card-header"><h3>\uD83D\uDD0C API Endpoints (' + (a.api_endpoints || []).length + ')</h3></div><div class="card-body" style="padding:0"><table class="data-table"><thead><tr><th>Method</th><th>Path</th><th>Description</th></tr></thead><tbody>' + (a.api_endpoints || []).slice(0, 30).map(function(e) {
                    if (typeof e === 'object') return '<tr><td><span class="tag tag-primary">' + (e.method || '') + '</span></td><td style="font-family:monospace;font-size:13px">' + (e.path || '') + '</td><td style="font-size:13px;color:var(--gray-600)">' + (e.description || '') + '</td></tr>';
                    return '<tr><td colspan="3">' + e + '</td></tr>';
                }).join('') + '</tbody></table></div></div>' : ''}

                <!-- Improvement Areas -->
                ${improvements.length ? '<div class="card" style="margin-bottom:24px"><div class="card-header"><h3>\uD83D\uDD27 Improvement Areas</h3></div><div class="card-body"><ul class="spec-list">' + improvements.map(function(i) { return '<li>' + i + '</li>'; }).join('') + '</ul></div></div>' : ''}
            `;

            // Render score graphs and flowcharts for each new feature
            setTimeout(function() {
                newFeatures.forEach(function(nf, idx) {
                    var scores = nf.opportunity_scores || {};
                    var scoreContainer = document.getElementById('nf-scores-' + idx);
                    if (scoreContainer && Object.keys(scores).length && typeof ScoreGraphRenderer !== 'undefined') {
                        ScoreGraphRenderer.renderBreakdown(scoreContainer, scores);
                    }
                    var flowContainer = document.getElementById('nf-flow-' + idx);
                    var execFlow = nf.execution_flow || [];
                    if (flowContainer && execFlow.length && typeof FlowchartRenderer !== 'undefined') {
                        FlowchartRenderer.renderExecutionPlan(flowContainer, execFlow);
                    }
                });
            }, 200);

        } catch(e) {
            el.innerHTML = '<div class="empty-state"><p>Error: ' + e.message + '</p></div>';
        }
    },

    // ---- Feature Discovery ----
    async featureDiscovery(el) {
        let features = [];
        let trends = [];
        try {
            const fRes = await API.getFeatureDiscoveries(App.project.id);
            features = fRes.results || fRes || [];
            const tRes = await API.getMarketTrends(App.project.id);
            trends = tRes.results || tRes || [];
        } catch(e) {}

        el.innerHTML = `
            <div class="metrics-grid">
                <div class="metric-card highlight"><div class="metric-label">AI Discovered Features</div><div class="metric-value">${features.length}</div></div>
                <div class="metric-card"><div class="metric-label">Market Analyses</div><div class="metric-value">${trends.length}</div></div>
                <div class="metric-card"><div class="metric-label">Evidence-Driven</div><div class="metric-value">${features.filter(f => f.source_type === 'evidence' || f.source_type === 'combined').length}</div></div>
                <div class="metric-card"><div class="metric-label">Trend-Driven</div><div class="metric-value">${features.filter(f => f.source_type === 'trend').length}</div></div>
            </div>

            <div style="display:flex;gap:12px;margin-bottom:24px">
                <button class="btn btn-primary" id="btn-discover-features">🔍 Run AI Feature Discovery</button>
                <button class="btn btn-secondary" id="btn-gen-trends">📊 Analyze Market Trends</button>
            </div>

            ${trends.length ? `
            <div class="card" style="margin-bottom:24px">
                <div class="card-header"><h3>📊 Latest Market Trends</h3></div>
                <div class="card-body">
                    ${trends.slice(0, 1).map(t => `
                        <p style="color:var(--gray-600);line-height:1.7;margin-bottom:16px">${t.trend_summary || 'No summary'}</p>
                        ${t.emerging_features && t.emerging_features.length ? `
                        <h4 style="font-size:14px;margin-bottom:8px">🚀 Emerging Features</h4>
                        ${t.emerging_features.slice(0, 5).map(f => `
                            <div style="padding:8px 0;border-bottom:1px solid var(--gray-100)">
                                <strong>${typeof f === 'object' ? (f.feature || f.name || '') : f}</strong>
                                ${typeof f === 'object' && f.description ? `<br><span style="font-size:13px;color:var(--gray-500)">${f.description}</span>` : ''}
                            </div>
                        `).join('')}` : ''}
                        ${t.market_gap_opportunities && t.market_gap_opportunities.length ? `
                        <h4 style="font-size:14px;margin:16px 0 8px">🎯 Market Gap Opportunities</h4>
                        ${t.market_gap_opportunities.slice(0, 5).map(g => `
                            <div style="padding:8px 0;border-bottom:1px solid var(--gray-100)">
                                <strong>${typeof g === 'object' ? (g.opportunity || g.name || '') : g}</strong>
                                ${typeof g === 'object' && g.market_size ? `<br><span style="font-size:13px;color:var(--gray-500)">Market: ${g.market_size}</span>` : ''}
                            </div>
                        `).join('')}` : ''}
                    `).join('')}
                </div>
            </div>` : ''}

            <div class="card">
                <div class="card-header"><h3>🔍 AI-Discovered Feature Opportunities</h3></div>
                <div class="card-body" style="padding:0">
                    ${features.length ? features.map(f => `
                        <div style="padding:20px 24px;border-bottom:1px solid var(--gray-100)">
                            <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px">
                                <h4 style="font-size:15px;font-weight:700">${f.feature_name}</h4>
                                <div style="display:flex;gap:8px">
                                    <span class="tag ${f.source_type === 'combined' ? 'tag-primary' : f.source_type === 'trend' ? 'tag-purple' : f.source_type === 'code' ? 'tag-success' : 'tag-gray'}">${f.source_type}</span>
                                    <span class="tag ${f.implementation_complexity === 'low' ? 'tag-success' : f.implementation_complexity === 'high' ? 'tag-danger' : 'tag-warning'}">${f.implementation_complexity} complexity</span>
                                </div>
                            </div>
                            <p style="font-size:14px;color:var(--gray-600);margin-bottom:8px">${App.truncate(f.problem_statement, 200)}</p>
                            ${f.execution_plan ? `<p style="font-size:13px;color:var(--gray-500)"><strong>Plan:</strong> ${App.truncate(f.execution_plan, 150)}</p>` : ''}
                            ${f.code_integration_points && f.code_integration_points.length ? `<div style="margin-top:8px;font-size:12px;color:var(--gray-500)">🔧 Integration: ${f.code_integration_points.slice(0, 3).join(', ')}</div>` : ''}
                        </div>
                    `).join('') : '<div class="empty-state"><div class="icon">🔍</div><h3>No discoveries yet</h3><p>Run AI Feature Discovery to analyze evidence, code, and market trends.</p></div>'}
                </div>
            </div>
        `;

        document.getElementById('btn-discover-features')?.addEventListener('click', async () => {
            Pages.showAIAnalysisOverlay('AI Feature Discovery', [
                { text: 'Analyzing customer evidence...', status: 'active' },
                { text: 'Reviewing insight clusters...', status: 'pending' },
                { text: 'Scanning codebase capabilities...', status: 'pending' },
                { text: 'Checking market trends...', status: 'pending' },
                { text: 'Discovering new opportunities...', status: 'pending' },
            ]);
            Pages.updateAIAnalysisDetail('Gemini AI is synthesizing all data sources to discover new feature opportunities...');
            setTimeout(() => { Pages.updateAIAnalysisStep(0, 'done'); Pages.updateAIAnalysisStep(1, 'active'); }, 2000);
            setTimeout(() => { Pages.updateAIAnalysisStep(1, 'done'); Pages.updateAIAnalysisStep(2, 'active'); }, 4000);

            try {
                await API.discoverFeatures(App.project.id);
                Pages.updateAIAnalysisStep(2, 'done');
                Pages.updateAIAnalysisStep(3, 'done');
                Pages.updateAIAnalysisStep(4, 'done');
                Toast.show('Feature discovery complete!', 'success');
                setTimeout(() => { Pages.hideAIAnalysisOverlay(); Pages.featureDiscovery(el); }, 800);
            } catch(e) { Pages.hideAIAnalysisOverlay(); Toast.show(e.message, 'error'); }
        });

        document.getElementById('btn-gen-trends')?.addEventListener('click', async () => {
            Pages.showAIAnalysisOverlay('Market Trend Analysis', [
                { text: 'Analyzing industry trends...', status: 'active' },
                { text: 'Identifying competitor features...', status: 'pending' },
                { text: 'Finding market gaps...', status: 'pending' },
            ]);
            Pages.updateAIAnalysisDetail('Gemini AI is analyzing current SaaS market trends for your product category...');
            setTimeout(() => { Pages.updateAIAnalysisStep(0, 'done'); Pages.updateAIAnalysisStep(1, 'active'); }, 2000);

            try {
                await API.generateMarketTrends(App.project.id);
                Pages.updateAIAnalysisStep(1, 'done');
                Pages.updateAIAnalysisStep(2, 'done');
                Toast.show('Market analysis complete!', 'success');
                setTimeout(() => { Pages.hideAIAnalysisOverlay(); Pages.featureDiscovery(el); }, 800);
            } catch(e) { Pages.hideAIAnalysisOverlay(); Toast.show(e.message, 'error'); }
        });
    },

    // ---- Data Sources ----
    async datasources(el) {
        let sources = [];
        try {
            const res = await API.get(`/datasources/?project=${App.project.id}`);
            sources = res.results || res || [];
        } catch(e) {}

        el.innerHTML = `
            <div class="card">
                <div class="card-header"><h3>🔌 Data Sources</h3></div>
                <div class="card-body" style="padding:0">
                    ${sources.length ? `
                    <table class="data-table">
                        <thead><tr><th>Name</th><th>Type</th><th>Status</th><th>Evidence</th><th>Last Synced</th></tr></thead>
                        <tbody>
                            ${sources.map(s => `
                                <tr>
                                    <td><strong>${s.name}</strong><br><span style="font-size:12px;color:var(--gray-500)">${s.description || ''}</span></td>
                                    <td><span class="tag tag-gray">${s.source_type}</span></td>
                                    <td>${s.is_active ? '<span class="tag tag-success">Active</span>' : '<span class="tag tag-gray">Inactive</span>'}</td>
                                    <td>${s.evidence_count}</td>
                                    <td style="font-size:13px;color:var(--gray-500)">${s.last_synced_at ? App.formatDate(s.last_synced_at) : 'Never'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>` : '<div class="empty-state"><div class="icon">🔌</div><h3>No data sources configured</h3></div>'}
                </div>
            </div>`;
    },

    // ---- Notifications ----
    async notifications(el) {
        let notifications = [];
        try {
            const res = await API.getNotifications();
            notifications = res.results || res || [];
        } catch(e) {}

        el.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3>🔔 Notifications</h3>
                    <button class="btn btn-ghost btn-sm" onclick="Pages.markAllRead()">Mark all read</button>
                </div>
                <div class="card-body" style="padding:0">
                    ${notifications.length ? notifications.map(n => `
                        <div style="padding:16px 24px;border-bottom:1px solid var(--gray-100);${n.is_read ? '' : 'background:var(--primary-bg)'}" onclick="Pages.markNotifRead('${n.id}')">
                            <div style="display:flex;align-items:center;gap:12px">
                                <span style="font-size:20px">${n.notification_type === 'opportunity_discovered' ? '🎯' : n.notification_type === 'spec_ready' ? '📄' : '🔔'}</span>
                                <div>
                                    <div style="font-weight:600;font-size:14px">${n.title}</div>
                                    <div style="font-size:13px;color:var(--gray-500)">${n.message || ''}</div>
                                    <div style="font-size:12px;color:var(--gray-400);margin-top:4px">${App.formatDate(n.created_at)}</div>
                                </div>
                                ${!n.is_read ? '<span class="tag tag-primary" style="margin-left:auto">New</span>' : ''}
                            </div>
                        </div>
                    `).join('') : '<div class="empty-state"><p>No notifications yet.</p></div>'}
                </div>
            </div>`;
    },

    async markNotifRead(id) {
        try { await API.markRead(id); } catch(e) {}
    },

    async markAllRead() {
        try { await API.markAllRead(); Toast.show('All marked read', 'success'); } catch(e) {}
    },
};

// ============ Init ============
document.addEventListener('DOMContentLoaded', () => App.init());
