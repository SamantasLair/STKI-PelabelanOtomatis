// _UIUX/ds/js/app.js
const App = {
    async init() {
        UIHelpers.initTabs((target) => {
            if (target === 'view-taxonomy') {
                TaxonomyVM.load();
            }
        });
        UIHelpers.initDatabaseSelector((dbType) => {
            if (document.getElementById('view-taxonomy').classList.contains('active')) {
                TaxonomyVM.load();
            }
        });
        
        TaxonomyVM.init();

        await this.updateGlobalStatus();
        TaxonomyVM.load();
    },

    async updateGlobalStatus() {
        await UIHelpers.updateGlobalStatus((status) => {
            TaxonomyVM.updateStats(status.total_docs, status.optimal_labels_count, status.taxonomy);
        });
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
