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

    async getLedgers() {
        const res = await fetch('/api/ledgers');
        return res.json();
    },

    async createLedger(name) {
        const res = await fetch('/api/ledgers/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        return res.json();
    },

    async renameLedger(oldName, newName) {
        const res = await fetch('/api/ledgers/rename', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ old_name: oldName, new_name: newName })
        });
        return res.json();
    },

    async deleteLedger(name) {
        const res = await fetch('/api/ledgers/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
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

    async getDocuments(page = 1, limit = 50, filter = 'all') {
        const res = await fetch(`/api/documents?page=${page}&limit=${limit}&filter=${filter}`);
        return res.json();
    },

    async generateTaxonomy(t1 = 0.50, t2 = 0.55) {
        const res = await fetch('/api/taxonomy/generate', { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ threshold_l1: t1, threshold_l2: t2 })
        });
        return res.json();
    }
};
