// _UIUX/shared/js/apiService.js
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

    async search(query, alpha) {
        const res = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, alpha })
        });
        return res.json();
    },

    async recommend(queryOrFile, alpha, limit = 100) {
        if (queryOrFile instanceof File) {
            const formData = new FormData();
            formData.append('file', queryOrFile);
            formData.append('alpha', alpha);
            formData.append('limit', limit);
            formData.append('offset', 0);
            const res = await fetch('/api/recommend', {
                method: 'POST',
                body: formData
            });
            return res.json();
        } else {
            const res = await fetch('/api/recommend', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: queryOrFile, alpha, limit, offset: 0 })
            });
            return res.json();
        }
    },

    async ingestUpload(file) {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch('/api/ingest', {
            method: 'POST',
            body: formData
        });
        return res.json();
    },

    async getLabels() {
        const res = await fetch('/api/labels');
        return res.json();
    },

    async getDocuments() {
        const res = await fetch('/api/documents');
        return res.json();
    },

    async generateTaxonomy() {
        const res = await fetch('/api/taxonomy/generate', { method: 'POST' });
        return res.json();
    }
};
