// _UIUX/js/views/recommendView.js
const RecommendView = {
    renderLoading() {
        document.getElementById('reco-data-results').innerHTML = `<div class="empty-state">SINKRONISASI DATASET...</div>`;
        document.getElementById('reco-docs-results').innerHTML = `<div class="empty-state">SINKRONISASI LITERATUR...</div>`;
    },

    renderResults(docs) {
        const dataContainer = document.getElementById('reco-data-results');
        const docsContainer = document.getElementById('reco-docs-results');
        
        const dataFiles = docs.data_files || [];
        const docFiles = docs.doc_files || [];
        
        document.getElementById('reco-data-count').textContent = `${dataFiles.length} DITEMUKAN`;
        document.getElementById('reco-docs-count').textContent = `${docFiles.length} DITEMUKAN`;
        
        dataContainer.innerHTML = dataFiles.length ? this.buildList(dataFiles) : `<div class="empty-state">NIHIL</div>`;
        docsContainer.innerHTML = docFiles.length ? this.buildList(docFiles) : `<div class="empty-state">NIHIL</div>`;
    },

    buildList(list) {
        let html = '';
        list.forEach((doc, idx) => {
            const rank = String(idx + 1).padStart(2, '0');
            html += `
                <div style="display: flex; padding: 6px 0; border-bottom: 1px dashed var(--color-border-light);">
                    <div style="font-family: var(--font-mono); width: 30px;">[${rank}]</div>
                    <div style="flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 0.85rem;">
                        ${doc.filename}
                    </div>
                    <div style="font-family: var(--font-mono); font-size: 0.8rem; width: 60px; text-align: right;">
                        ${doc.similarity.toFixed(1)}%
                    </div>
                </div>
            `;
        });
        return html;
    },

    renderError(msg) {
        document.getElementById('reco-data-results').innerHTML = `<div class="empty-state" style="color: var(--color-danger)">ERROR: ${msg}</div>`;
        document.getElementById('reco-docs-results').innerHTML = `<div class="empty-state" style="color: var(--color-danger)">ERROR: ${msg}</div>`;
    }
};
