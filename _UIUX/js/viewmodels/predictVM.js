// _UIUX/js/viewmodels/predictVM.js
const PredictVM = {
    init() {
        const btn = document.getElementById('btn-predict');
        btn.addEventListener('click', () => this.execute());
    },

    async execute() {
        const text = document.getElementById('input-predict-text').value.trim();
        if (!text) return;

        PredictView.renderLoading();
        const start = performance.now();

        try {
            const data = await ApiService.predict(text);
            const end = performance.now();
            const latency = (end - start).toFixed(0);
            
            PredictView.renderResults(data, latency);
        } catch (err) {
            PredictView.renderError(err.message);
        }
    }
};
