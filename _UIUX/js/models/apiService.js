// _UIUX/js/models/apiService.js
const ApiService = {
    async getStatus() {
        const res = await fetch('/api/status');
        return res.json();
    },

    async switchDb(dbType) {
        const res = await fetch('/api/switch_db', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ db_type: dbType })
        });
        return res.json();
    },

    async getLabels() {
        const res = await fetch('/api/labels');
        return res.json();
    },

    async search(query, alpha) {
        const res = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, alpha })
        });
        return res.json();
    },

    async predict(text) {
        const res = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        return res.json();
    },

    async recommend(query, alpha, limit = 100) {
        const res = await fetch('/api/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, alpha, limit, offset: 0 })
        });
        return res.json();
    },

    async regenerateLabels() {
        const res = await fetch('/api/labels/regenerate', { method: 'POST' });
        return res.json();
    },

    async pollRegenerateProgress() {
        const res = await fetch('/api/labels/regenerate/progress');
        return res.json();
    }
};
