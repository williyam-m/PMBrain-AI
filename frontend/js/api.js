/**
 * PMBrain AI — API Client
 * Handles all HTTP communication with the Django backend.
 */
const API = {
    baseURL: '/api',
    token: null,

    init() {
        this.token = localStorage.getItem('pmbrain_token');
        this.refreshToken = localStorage.getItem('pmbrain_refresh');
    },

    headers() {
        const h = { 'Content-Type': 'application/json' };
        if (this.token) h['Authorization'] = `Bearer ${this.token}`;
        return h;
    },

    async request(method, path, data = null) {
        const opts = {
            method,
            headers: this.headers(),
        };
        if (data && method !== 'GET') {
            opts.body = JSON.stringify(data);
        }
        try {
            const res = await fetch(`${this.baseURL}${path}`, opts);
            if (res.status === 401) {
                const refreshed = await this.refreshAccessToken();
                if (refreshed) {
                    opts.headers = this.headers();
                    const retry = await fetch(`${this.baseURL}${path}`, opts);
                    return retry.json();
                } else {
                    App.showAuth();
                    throw new Error('Session expired');
                }
            }
            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: res.statusText }));
                throw new Error(err.detail || err.error || JSON.stringify(err));
            }
            return res.json();
        } catch (e) {
            if (e.message !== 'Session expired') {
                console.error(`API ${method} ${path} error:`, e);
            }
            throw e;
        }
    },

    async refreshAccessToken() {
        if (!this.refreshToken) return false;
        try {
            const res = await fetch(`${this.baseURL}/auth/token/refresh/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh: this.refreshToken }),
            });
            if (res.ok) {
                const data = await res.json();
                this.token = data.access;
                localStorage.setItem('pmbrain_token', data.access);
                return true;
            }
        } catch (e) {}
        return false;
    },

    get(path) { return this.request('GET', path); },
    post(path, data) { return this.request('POST', path, data); },
    put(path, data) { return this.request('PUT', path, data); },
    patch(path, data) { return this.request('PATCH', path, data); },
    delete(path) { return this.request('DELETE', path); },

    // Auth
    login(email, password) {
        return this.post('/auth/login/', { email, password });
    },
    register(email, password, full_name) {
        return this.post('/auth/register/', { email, password, full_name });
    },
    me() { return this.get('/auth/me/'); },

    // Organizations
    getOrgs() { return this.get('/organizations/'); },
    createOrg(data) { return this.post('/organizations/', data); },

    // Projects
    getProjects(orgId) { return this.get(`/projects/?organization=${orgId}`); },
    getProject(id) { return this.get(`/projects/${id}/`); },

    // Evidence
    getEvidence(projectId) { return this.get(`/evidence/?project=${projectId}`); },
    createEvidence(data) { return this.post('/evidence/', data); },
    bulkUpload(items) { return this.post('/evidence/bulk_upload/', { items }); },
    getEvidenceStats(projectId) { return this.get(`/evidence/stats/?project=${projectId}`); },

    // Insights
    getInsights(projectId) { return this.get(`/insights/?project=${projectId}`); },
    getTopInsights(projectId) { return this.get(`/insights/top_unmet_needs/?project=${projectId}`); },
    getInsightStats(projectId) { return this.get(`/insights/stats/?project=${projectId}`); },
    getInsightsBySegment(projectId) { return this.get(`/insights/by_segment/?project=${projectId}`); },

    // Opportunities
    getOpportunities(projectId) { return this.get(`/opportunities/?project=${projectId}`); },
    getOpportunity(id) { return this.get(`/opportunities/${id}/`); },
    getLeaderboard(projectId) { return this.get(`/opportunities/leaderboard/?project=${projectId}`); },
    updateOppStatus(id, status) { return this.post(`/opportunities/${id}/update_status/`, { status }); },
    getOppStats(projectId) { return this.get(`/opportunities/stats/?project=${projectId}`); },

    // AI Agents
    runAgent(workflow, projectId, inputData = {}) {
        return this.post('/agents/run/', { workflow, project_id: projectId, input_data: inputData });
    },
    whatToBuild(projectId, query) {
        return this.post('/agents/what-to-build/', { project_id: projectId, query });
    },
    getAgentRuns(projectId) { return this.get(`/agents/runs/?project=${projectId}`); },

    // Specs
    getSpecs(projectId) { return this.get(`/specs/?project=${projectId}`); },
    getSpec(id) { return this.get(`/specs/${id}/`); },
    chatSpec(id, message) { return this.post(`/specs/${id}/chat/`, { message }); },
    updateSpecStatus(id, status) { return this.post(`/specs/${id}/update_status/`, { status }); },
    getSpecVersions(id) { return this.get(`/specs/${id}/versions/`); },

    // Analytics
    getDashboard(projectId) { return this.get(`/analytics/dashboard/?project=${projectId}`); },
    getInsightAnalytics(projectId) { return this.get(`/analytics/insights/?project=${projectId}`); },
    getOppAnalytics(projectId) { return this.get(`/analytics/opportunities/?project=${projectId}`); },

    // Codebase
    getCodebases(projectId) { return this.get(`/codebase/codebases/?project=${projectId}`); },
    uploadCodebase(formData) {
        const opts = {
            method: 'POST',
            headers: {},
            body: formData,
        };
        if (this.token) opts.headers['Authorization'] = `Bearer ${this.token}`;
        return fetch(`${this.baseURL}/codebase/codebases/upload/`, opts).then(r => {
            if (!r.ok) return r.json().then(e => { throw new Error(e.error || 'Upload failed'); });
            return r.json();
        });
    },
    analyzeCodebase(id) { return this.post(`/codebase/codebases/${id}/analyze/`); },
    getCodebaseAnalyses(projectId) { return this.get(`/codebase/analyses/?project=${projectId}`); },
    getCodebaseAnalysis(id) { return this.get(`/codebase/analyses/${id}/`); },
    getMarketTrends(projectId) { return this.get(`/codebase/trends/?project=${projectId}`); },
    generateMarketTrends(projectId) { return this.post('/codebase/trends/generate/', { project_id: projectId }); },
    getFeatureDiscoveries(projectId) { return this.get(`/codebase/features/?project=${projectId}`); },
    discoverFeatures(projectId) { return this.post('/codebase/features/discover/', { project_id: projectId }); },

    // GitHub Integration
    githubStatus(orgId) { return this.get(`/integrations/github/status/?organization_id=${orgId}`); },
    githubConnectToken(accessToken, orgId) {
        return this.post('/integrations/github/connect-token/', {
            access_token: accessToken,
            organization_id: orgId,
        });
    },
    githubDisconnect(orgId) {
        return this.post('/integrations/github/disconnect/', { organization_id: orgId });
    },
    githubRepos(orgId, projectId, page = 1) {
        return this.get(`/integrations/github/repos/?organization_id=${orgId}&project_id=${projectId}&page=${page}`);
    },
    githubLinkRepo(projectId, repoUrl) {
        return this.post('/integrations/github/link-repo/', {
            project_id: projectId,
            repo_url: repoUrl,
        });
    },
    githubLinkedRepos(projectId) {
        return this.get(`/integrations/github/linked-repos/?project_id=${projectId}`);
    },
    githubAnalyzeRepo(repoId) {
        return this.post('/integrations/github/analyze-repo/', { repo_id: repoId });
    },
    githubUnlinkRepo(repoId) {
        return this.post('/integrations/github/unlink-repo/', { repo_id: repoId });
    },

    // Notifications
    getNotifications() { return this.get('/notifications/'); },
    markRead(id) { return this.post(`/notifications/${id}/mark_read/`); },
    markAllRead() { return this.post('/notifications/mark_all_read/'); },
    unreadCount() { return this.get('/notifications/unread_count/'); },

    setTokens(access, refresh) {
        this.token = access;
        this.refreshToken = refresh;
        localStorage.setItem('pmbrain_token', access);
        localStorage.setItem('pmbrain_refresh', refresh);
    },

    clearTokens() {
        this.token = null;
        this.refreshToken = null;
        localStorage.removeItem('pmbrain_token');
        localStorage.removeItem('pmbrain_refresh');
    }
};

API.init();
