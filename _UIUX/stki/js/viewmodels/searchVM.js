// _UIUX/stki/js/viewmodels/searchVM.js
const SearchVM = {
    init() {
        const btn = document.getElementById('btn-search');
        const input = document.getElementById('input-search-query');
        
        btn.addEventListener('click', () => this.execute());
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this.execute();
        });
    },

    async execute() {
        const query = document.getElementById('input-search-query').value.trim();
        const alpha = document.getElementById('input-alpha').value;
        
        if (!query) return;

        SearchView.renderLoading();
        const start = performance.now();

        try {
            const docs = await ApiService.search(query, alpha);
            const end = performance.now();
            
            const telemetry = {
                latency: (end - start).toFixed(0),
                alpha: alpha
            };
            
            SearchView.renderResults(docs, telemetry);
        } catch (err) {
            SearchView.renderError(err.message);
        }
    }
};
