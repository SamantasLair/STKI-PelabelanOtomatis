// _UIUX/js/views/predictView.js
const PredictView = {
    renderLoading() {
        const container = document.getElementById('predict-results');
        container.innerHTML = `<div class="empty-state">MENGKALKULASI TENSOR ONNX...</div>`;
    },

    renderResults(data, latency) {
        const container = document.getElementById('predict-results');
        
        if (data.error) {
            this.renderError(data.error);
            return;
        }

        const bestL1 = data.layer_1[0];
        const bestL2 = data.layer_2[0];

        let html = `
            <div style="font-family: var(--font-mono); font-size: 0.85rem; margin-bottom: var(--spacing-md); color: var(--color-ink-muted);">
                LATENSI INFERENSI: ${latency}ms | DIMENSIONAL COLLAPSE RISK: LOW
            </div>
            <div style="font-weight: bold; margin-bottom: var(--spacing-sm); border-bottom: 1px solid var(--color-border); padding-bottom: 4px;">
                KEPUTUSAN DOMAIN (L1): ${bestL1.label} (${bestL1.score.toFixed(2)}%)
            </div>
            <div style="margin-bottom: var(--spacing-lg);">
        `;

        data.layer_1.forEach(item => {
            html += this.buildBar(item.label, item.score);
        });

        html += `
            </div>
            <div style="font-weight: bold; margin-bottom: var(--spacing-sm); border-bottom: 1px solid var(--color-border); padding-bottom: 4px;">
                KEPUTUSAN DETAIL (L2): ${bestL2.label} (${bestL2.score.toFixed(2)}%)
            </div>
            <div>
        `;

        data.layer_2.slice(0, 5).forEach(item => {
            html += this.buildBar(item.label, item.score);
        });

        html += `</div>`;
        container.innerHTML = html;
    },

    buildBar(label, score) {
        return `
            <div style="display: flex; align-items: center; margin-bottom: 4px; font-family: var(--font-mono); font-size: 0.8rem;">
                <div style="width: 150px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${label}</div>
                <div class="telemetry-bar-container" style="flex: 1; height: 8px; margin: 0 var(--spacing-sm);">
                    <div class="telemetry-bar-fill" style="width: ${score}%;"></div>
                </div>
                <div style="width: 50px; text-align: right;">${score.toFixed(1)}%</div>
            </div>
        `;
    },

    renderError(msg) {
        const container = document.getElementById('predict-results');
        container.innerHTML = `<div class="empty-state" style="color: var(--color-danger)">ERROR: ${msg}</div>`;
    }
};
