// _UIUX/ds/js/views/taxonomyView.js
const TaxonomyView = {
    renderList(labels) {
        const container = document.getElementById('taxonomy-list');
        
        if (!labels || labels.length === 0) {
            container.innerHTML = `<div class="empty-state">TAKSONOMI KOSONG / BELUM DIGENERATE.</div>`;
            return;
        }

        let html = '<table style="width: 100%; border-collapse: collapse; font-family: var(--font-mono); font-size: 0.85rem;">';
        html += `
            <tr style="border-bottom: 1px solid var(--color-border); background: var(--color-bg);">
                <th style="text-align: left; padding: 4px;">LABEL DINAMIS (K-MEANS + TF-IDF)</th>
                <th style="text-align: right; padding: 4px;">DISTRIBUSI (N)</th>
            </tr>
        `;

        labels.forEach(item => {
            html += `
                <tr style="border-bottom: 1px dashed var(--color-border-light);">
                    <td style="padding: 4px;">${item.label}</td>
                    <td style="text-align: right; padding: 4px;">${item.count}</td>
                </tr>
            `;
        });
        
        html += '</table>';
        container.innerHTML = html;
    },

    updateTelemetry(totalDocs, optimal) {
        const span = document.getElementById('taxonomy-telemetry');
        if (span) span.textContent = `N: ${totalDocs} | TARGET RICE (K): ${optimal}`;
    },

    renderTerminalLog(msg, type = 'info') {
        const term = document.getElementById('taxonomy-terminal');
        term.style.display = 'block';
        
        const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
        let color = 'var(--color-ink)';
        if (type === 'error') color = 'var(--color-danger)';
        if (type === 'success') color = 'var(--color-safe)';
        
        term.innerHTML += `<div style="color: ${color}; margin-bottom: 2px; font-family: var(--font-mono); font-size: 0.8rem;">[${timestamp}] ${msg}</div>`;
        term.scrollTop = term.scrollHeight;
    },
    
    clearTerminal() {
        const term = document.getElementById('taxonomy-terminal');
        term.innerHTML = '';
        term.style.display = 'none';
    },

    // PIPELINE INTERACTION
    setActiveNode(nodeId, panelId) {
        document.querySelectorAll('.pipeline-node').forEach(el => el.classList.remove('active-node'));
        document.querySelectorAll('.node-panel').forEach(el => el.style.display = 'none');
        
        if (nodeId) document.getElementById(nodeId).classList.add('active-node');
        if (panelId) document.getElementById(panelId).style.display = 'block';
    },

    setEdgeAnimation(edgeId, isActive) {
        const edge = document.getElementById(edgeId);
        if (edge) {
            if (isActive) edge.classList.add('active');
            else edge.classList.remove('active');
        }
    },

    // DATABASE EXPLORER
    renderDocuments(docs) {
        window._loadedDocs = docs;
        const container = document.getElementById('db-explorer-list');
        const countLabel = document.getElementById('db-explorer-count');
        const preview = document.getElementById('db-explorer-preview');
        
        if (countLabel) countLabel.textContent = `${docs.length} DOKUMEN`;
        
        if (!docs || docs.length === 0) {
            container.innerHTML = `<div class="empty-state">DATABASE KOSONG.</div>`;
            preview.innerHTML = `<div class="empty-state">TIDAK ADA DOKUMEN.</div>`;
            return;
        }

        let html = '';
        docs.forEach((doc, idx) => {
            html += `
                <div id="row-${doc.id}" class="ledger-row db-row" onclick="previewDocument(${idx})" style="cursor: pointer;">
                    <div class="row-col col-rank">${doc.id}</div>
                    <div class="row-col col-main">
                        <div class="doc-title" style="font-size: 0.9rem;">${doc.filename}</div>
                        <div class="tag-list" style="margin-top: 4px;">
                            ${doc.labels.map(l => `<span class="tag" style="font-size: 0.65rem;">${l}</span>`).join('')}
                        </div>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
        preview.innerHTML = `<div class="empty-state">PILIH DOKUMEN DI KIRI UNTUK MELIHAT ISI PENUH</div>`;
    }
};

window.previewDocument = function(idx) {
    const doc = window._loadedDocs[idx];
    if (!doc) return;
    
    const preview = document.getElementById('db-explorer-preview');
    preview.innerHTML = `
        <h3 style="margin-top:0; margin-bottom: 8px; font-family: var(--font-serif); border-bottom: 2px solid var(--color-ink); padding-bottom: 8px;">${doc.filename}</h3>
        <div style="margin-bottom:16px;">
            ${doc.labels.map(l => `<span class="tag">${l}</span>`).join('')}
        </div>
        <div style="font-family: var(--font-mono); font-size: 0.85rem; line-height: 1.5; white-space: pre-wrap; color: var(--color-ink-muted);">
            ${doc.content}
        </div>
    `;
    
    // Highlight selected row
    document.querySelectorAll('.db-row').forEach(el => el.style.backgroundColor = 'transparent');
    const selectedRow = document.getElementById('row-' + doc.id);
    if (selectedRow) selectedRow.style.backgroundColor = 'var(--color-highlight)';
};
