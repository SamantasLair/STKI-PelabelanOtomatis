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
            
            // Map label ke kelas premium (L1 / L2) berdasarkan taxonomy state
            const tags = doc.labels.map(l => {
                const isOutlier = (l === 'Tidak Terklasifikasi');
                let tagClass = 'tag';
                if (!isOutlier && window._globalTaxonomy) {
                    const l1 = window._globalTaxonomy.Layer_1_Domain || [];
                    if (l1.includes(l)) tagClass = 'tag tag-l1';
                    else tagClass = 'tag tag-l2';
                }
                const styleAttr = isOutlier ? 'style="color:var(--color-danger); border-color:var(--color-danger);"' : '';
                return `<span class="${tagClass}" ${styleAttr}>${l}</span>`;
            }).join('');
            
            const displayTitle = doc.filename || (doc.content.includes(' - ') ? doc.content.split(' - ')[0] : 'ARSIP TAK BERNAMA');
            
            html += `
                <div class="ledger-row deal-card-anim" style="animation-delay: ${idx * 0.08}s;" onclick="this.classList.toggle('expanded')">
                    <div style="display:flex; width: 100%;">
                        <div class="row-col col-rank">[${rank}]</div>
                        <div class="row-col col-main">
                            <div class="doc-title">${displayTitle}</div>
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
                    <div class="card-hidden-content" style="font-family: var(--font-mono); font-size: 0.85rem; color: #444; white-space: pre-wrap;">
                        ${doc.content}
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
