// _UIUX/stki/js/views/searchView.js
const SearchView = {
    renderLoading() {
        const container = document.getElementById('search-results');
        container.innerHTML = `<div class="empty-state">MENGEKSEKUSI PENCARIAN HIBRIDA...</div>`;
    },

    renderResults(docs, telemetry) {
        const container = document.getElementById('search-results');
        const telemetrySpan = document.getElementById('search-telemetry');
        
        telemetrySpan.textContent = `LATENSI: ${telemetry.latency}ms | TOTAL: ${docs.length} ARSIP | ALPHA: ${telemetry.alpha}`;

        if (docs.length === 0) {
            container.innerHTML = `<div class="empty-state">TIDAK DITEMUKAN ARSIP YANG MEMENUHI AMBANG BATAS.</div>`;
            return;
        }

        let html = '';
        docs.forEach((doc, idx) => {
            const rank = String(idx + 1).padStart(2, '0');
            const tags = doc.labels.map(l => `<span class="tag">${l}</span>`).join('');
            
            html += `
                <div class="ledger-row">
                    <div class="row-col col-rank">[${rank}]</div>
                    <div class="row-col col-main">
                        <div class="doc-title">${doc.filename}</div>
                        <div class="doc-snippet">${doc.content.substring(0, 150)}...</div>
                        <div class="tag-list">${tags}</div>
                    </div>
                    <div class="row-col col-score">
                        <div>HYBRID: ${(doc.similarity).toFixed(2)}%</div>
                        <div style="color: var(--color-ink-muted); font-size: 0.75rem;">
                            DENSE: ${(doc.dense_score).toFixed(2)}% | SPARSE: ${(doc.sparse_score).toFixed(2)}%
                        </div>
                        <div class="telemetry-bar-container">
                            <div class="telemetry-bar-fill" style="width: ${doc.similarity}%"></div>
                        </div>
                    </div>
                </div>
            `;
        });
        container.innerHTML = html;
    },

    renderError(msg) {
        const container = document.getElementById('search-results');
        container.innerHTML = `<div class="empty-state" style="color: var(--color-danger)">ERROR: ${msg}</div>`;
    }
};
