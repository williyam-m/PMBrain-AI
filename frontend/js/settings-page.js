/**
 * PMBrain AI — Settings Page
 * GitHub Integration + Organization Settings
 */

// Extend Pages object with settings page
Pages.settings = async function(el) {
    let githubStatus = { connected: false };
    try { githubStatus = await API.githubStatus(App.org.id); } catch(e) {}

    const ghConnected = githubStatus.connected;
    const ghIntegration = githubStatus.integration || {};

    el.innerHTML = `
        <div class="grid-2">
            <div class="card" style="margin-bottom:24px">
                <div class="card-header"><h3>🐙 GitHub Integration</h3></div>
                <div class="card-body">
                    ${ghConnected ? `
                        <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px;padding:16px;background:var(--gray-50);border-radius:var(--radius-lg)">
                            <img src="${ghIntegration.avatar_url || ''}" width="48" height="48" style="border-radius:50%;border:2px solid var(--success)" onerror="this.style.display='none'">
                            <div>
                                <div style="font-weight:700;font-size:16px">@${ghIntegration.github_username}</div>
                                <span class="tag tag-success">Connected</span>
                                <span style="font-size:12px;color:var(--gray-500);margin-left:8px">Since ${App.formatDate(ghIntegration.connected_at)}</span>
                            </div>
                        </div>
                        <p style="color:var(--gray-600);margin-bottom:16px;font-size:14px">
                            Your GitHub account is connected. You can link repositories from the <strong>Codebase</strong> page.
                        </p>
                        <div style="display:flex;gap:8px">
                            <button class="btn btn-secondary btn-sm" onclick="App.navigate('codebase')">💻 Go to Codebase</button>
                            <button class="btn btn-danger btn-sm" id="btn-disconnect-github">Disconnect GitHub</button>
                        </div>
                    ` : `
                        <div style="text-align:center;padding:20px">
                            <div style="font-size:48px;margin-bottom:12px">🐙</div>
                            <h4 style="margin-bottom:8px">Connect GitHub</h4>
                            <p style="color:var(--gray-600);margin-bottom:20px">
                                Link your GitHub account to enable repository analysis and code-aware feature recommendations.
                            </p>
                            <div class="form-group" style="text-align:left;max-width:400px;margin:0 auto">
                                <label>GitHub Personal Access Token</label>
                                <input type="password" id="settings-gh-token" placeholder="ghp_xxxxxxxxxxxxxxxxxxxx" style="font-family:monospace">
                                <p style="font-size:12px;color:var(--gray-400);margin-top:4px">
                                    Generate at <a href="https://github.com/settings/tokens" target="_blank" style="color:var(--primary)">github.com/settings/tokens</a>
                                    with <strong>repo</strong> and <strong>read:user</strong> scopes.
                                </p>
                            </div>
                            <button class="btn btn-primary" id="btn-settings-connect-github">Connect GitHub</button>
                        </div>
                    `}
                </div>
            </div>

            <div class="card" style="margin-bottom:24px">
                <div class="card-header"><h3>🏢 Organization</h3></div>
                <div class="card-body">
                    <div class="form-group">
                        <label>Organization Name</label>
                        <input type="text" value="${App.org?.name || ''}" readonly style="background:var(--gray-50)">
                    </div>
                    <div class="form-group">
                        <label>Current Project</label>
                        <input type="text" value="${App.project?.name || ''}" readonly style="background:var(--gray-50)">
                    </div>
                    <div class="form-group">
                        <label>Product Context</label>
                        <textarea id="settings-product-context" rows="3" placeholder="Describe your product and target users...">${App.project?.product_context || ''}</textarea>
                    </div>
                    <button class="btn btn-primary btn-sm" id="btn-update-project-context">Update Context</button>
                </div>
            </div>
        </div>

        <div class="card" style="margin-bottom:24px">
            <div class="card-header"><h3>🔑 Configuration</h3></div>
            <div class="card-body">
                <div class="grid-3">
                    <div class="impact-item"><div class="label">AI Engine</div><div class="value">Gemini AI</div></div>
                    <div class="impact-item"><div class="label">Primary Model</div><div class="value">gemini-2.5-flash-lite</div></div>
                    <div class="impact-item"><div class="label">Auth</div><div class="value">JWT + Session</div></div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-header"><h3>👤 Account</h3></div>
            <div class="card-body">
                <div class="grid-3">
                    <div class="impact-item"><div class="label">Email</div><div class="value">${App.user?.email || '-'}</div></div>
                    <div class="impact-item"><div class="label">Name</div><div class="value">${App.user?.full_name || '-'}</div></div>
                    <div class="impact-item"><div class="label">Member Since</div><div class="value">${App.formatDate(App.user?.created_at)}</div></div>
                </div>
            </div>
        </div>
    `;

    // Bind events
    document.getElementById('btn-settings-connect-github')?.addEventListener('click', async () => {
        const token = document.getElementById('settings-gh-token').value.trim();
        if (!token) { Toast.show('Please enter a token', 'error'); return; }
        try {
            Toast.show('Connecting to GitHub...', 'info');
            const result = await API.githubConnectToken(token, App.org.id);
            Toast.show('Connected as @' + result.integration.github_username + '!', 'success');
            Pages.settings(el);
        } catch(e) { Toast.show('Failed: ' + e.message, 'error'); }
    });

    document.getElementById('btn-disconnect-github')?.addEventListener('click', async () => {
        if (!confirm('Disconnect GitHub? Linked repos will remain but cannot be re-synced.')) return;
        try {
            await API.githubDisconnect(App.org.id);
            Toast.show('GitHub disconnected', 'success');
            Pages.settings(el);
        } catch(e) { Toast.show(e.message, 'error'); }
    });

    document.getElementById('btn-update-project-context')?.addEventListener('click', async () => {
        const ctx = document.getElementById('settings-product-context').value;
        try {
            await API.patch('/projects/' + App.project.id + '/', { product_context: ctx });
            App.project.product_context = ctx;
            Toast.show('Product context updated!', 'success');
        } catch(e) { Toast.show(e.message, 'error'); }
    });
};
