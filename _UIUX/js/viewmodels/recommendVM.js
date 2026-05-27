// _UIUX/js/viewmodels/recommendVM.js
const RecommendVM = {
    init() {
        const btn = document.getElementById('btn-recommend');
        const input = document.getElementById('input-reco-query');
        
        btn.addEventListener('click', () => this.execute());
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this.execute();
        });
    },

    async execute() {
        const query = document.getElementById('input-reco-query').value.trim();
        const alpha = document.getElementById('input-alpha').value;
        
        if (!query) return;

        RecommendView.renderLoading();

        try {
            const docs = await ApiService.recommend(query, alpha, 100);
            RecommendView.renderResults(docs);
        } catch (err) {
            RecommendView.renderError(err.message);
        }
    }
};
