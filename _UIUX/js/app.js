// _UIUX/js/app.js
const App = {
    async init() {
        this.initTabs();
        this.initDatabaseSelector();
        
        SearchVM.init();
        PredictVM.init();
        TaxonomyVM.init();
        RecommendVM.init();

        await this.updateGlobalStatus();
    },

    initTabs() {
        const navItems = document.querySelectorAll('.nav-item');
        const tabPanes = document.querySelectorAll('.tab-pane');

        navItems.forEach(item => {
            item.addEventListener('click', () => {
                const target = item.getAttribute('data-target');
                
                navItems.forEach(nav => nav.classList.remove('active'));
                tabPanes.forEach(tab => tab.classList.remove('active'));
                
                item.classList.add('active');
                document.getElementById(target).classList.add('active');

                if (target === 'view-taxonomy') {
                    TaxonomyVM.load();
                }
            });
        });
    },

    initDatabaseSelector() {
        const selector = document.getElementById('select-db');
        selector.addEventListener('change', async (e) => {
            const dbType = e.target.value;
            try {
                await ApiService.switchDb(dbType);
                await this.updateGlobalStatus();
                if (document.getElementById('view-taxonomy').classList.contains('active')) {
                    TaxonomyVM.load();
                }
            } catch (err) {
                console.error("Gagal berpindah database:", err);
            }
        });
    },

    async updateGlobalStatus() {
        try {
            const status = await ApiService.getStatus();
            document.getElementById('status-engine').textContent = `ENGINE: ${status.db_type.toUpperCase()}`;
            document.getElementById('status-model').textContent = `MODEL: SOTA MINILM L-12`;
            document.getElementById('select-db').value = status.db_type;
            
            TaxonomyVM.updateStats(status.total_docs, status.optimal_labels_count, status.actual_labels_count);
        } catch (err) {
            document.getElementById('status-engine').textContent = `ENGINE: OFFLINE`;
            console.error("Gagal memuat status:", err);
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
