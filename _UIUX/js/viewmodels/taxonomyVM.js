// _UIUX/js/viewmodels/taxonomyVM.js
const TaxonomyVM = {
    init() {
        const btnRelabel = document.getElementById('btn-relabel');
        btnRelabel.addEventListener('click', () => this.executeRegenerate());
    },

    async load() {
        try {
            const labels = await ApiService.getLabels();
            TaxonomyView.renderList(labels);
        } catch (err) {
            console.error(err);
        }
    },

    async updateStats(totalDocs, optimal, actual) {
        TaxonomyView.updateTelemetry(totalDocs, optimal, actual);
    },

    async executeRegenerate() {
        const confirmAction = confirm("TINDAKAN BATCH: Menginferensi ulang seluruh dokumen. Lanjutkan?");
        if (!confirmAction) return;
        
        try {
            const data = await ApiService.regenerateLabels();
            if (data.status === 'success') {
                this.pollProgress();
            }
        } catch (err) {
            console.error(err);
        }
    },

    pollProgress() {
        const interval = setInterval(async () => {
            try {
                const progress = await ApiService.pollRegenerateProgress();
                TaxonomyView.renderProgress(progress);
                
                if (progress.status === 'success' || progress.status === 'failed') {
                    clearInterval(interval);
                    if (progress.status === 'success') {
                        this.load();
                        App.updateGlobalStatus();
                    }
                }
            } catch (err) {
                clearInterval(interval);
                console.error(err);
            }
        }, 800);
    }
};
