/**
 * PMBrain AI — WebSocket Manager
 * Real-time updates for AI jobs, insights, scoring, spec progress.
 */
const WS = {
    socket: null,
    projectId: null,
    listeners: {},
    reconnectAttempts: 0,
    maxReconnect: 5,

    connect(projectId) {
        this.projectId = projectId;
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const url = `${protocol}//${host}/ws/project/${projectId}/`;

        try {
            this.socket = new WebSocket(url);

            this.socket.onopen = () => {
                console.log('🔌 WebSocket connected');
                this.reconnectAttempts = 0;
                this.updateIndicator(true);
            };

            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };

            this.socket.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateIndicator(false);
                this.attemptReconnect();
            };

            this.socket.onerror = (err) => {
                console.log('WebSocket connection unavailable (server may not support WS)');
                this.updateIndicator(false);
            };
        } catch (e) {
            console.log('WebSocket not available');
            this.updateIndicator(false);
        }
    },

    handleMessage(data) {
        const type = data.type;
        console.log('📡 WS message:', type, data);

        // Fire registered listeners
        if (this.listeners[type]) {
            this.listeners[type].forEach(cb => cb(data.data || data));
        }

        // Global handlers
        if (type === 'agent_update') {
            Toast.show(`AI Agent completed: ${data.data?.workflow || 'unknown'}`, 'success');
        }
        if (type === 'notification') {
            Toast.show(data.data?.title || 'New notification', 'info');
        }
    },

    on(type, callback) {
        if (!this.listeners[type]) this.listeners[type] = [];
        this.listeners[type].push(callback);
    },

    off(type) {
        delete this.listeners[type];
    },

    send(data) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
        }
    },

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnect) {
            this.reconnectAttempts++;
            setTimeout(() => {
                if (this.projectId) this.connect(this.projectId);
            }, 2000 * this.reconnectAttempts);
        }
    },

    updateIndicator(connected) {
        const el = document.getElementById('ws-status');
        if (el) {
            el.className = `ws-indicator ${connected ? 'connected' : 'disconnected'}`;
            el.title = connected ? 'Real-time connected' : 'Real-time disconnected';
        }
    },

    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }
};
