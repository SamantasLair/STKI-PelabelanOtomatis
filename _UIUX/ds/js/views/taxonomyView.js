// GLOBAL VARIABLES FOR COPY
window._currentTaxonomyData = null;
window._currentLabelsData = [];

const TaxonomyView = {
    setTaxonomyData(tax) {
        window._currentTaxonomyData = tax;
    },

    renderList(labels) {
        window._currentLabelsData = labels || [];
        const container = document.getElementById('taxonomy-list');
        
        if (!labels || labels.length === 0) {
            container.innerHTML = `<div class="empty-state">TAKSONOMI KOSONG / BELUM DIGENERATE.</div>`;
            return;
        }

        let html = '<table style="width: 100%; border-collapse: collapse; font-family: var(--font-mono); font-size: 0.85rem;">';
        html += `
            <tr style="border-bottom: 1px solid var(--color-border); background: var(--color-bg);">
                <th style="text-align: left; padding: 4px; display:flex; align-items:center; gap:8px;">
                    <button class="btn-copy" onclick="copyFullTaxonomy(event)" style="background:var(--color-paper); border:1px solid var(--color-border); font-family:var(--font-mono); font-size:9px; cursor:pointer; padding:2px 6px; font-weight:bold; transition:all 0.2s;" onmouseover="this.style.background='var(--color-ink)'; this.style.color='var(--color-paper)'" onmouseout="this.style.background='var(--color-paper)'; this.style.color='var(--color-ink)'">[COPY ALL]</button>
                    LABEL DINAMIS (K-MEANS + TF-IDF)
                </th>
                <th style="text-align: right; padding: 4px;">DISTRIBUSI (N)</th>
            </tr>
        `;

        labels.forEach((item, i) => {
            html += `
                <tr style="border-bottom: 1px dashed var(--color-border-light); transition: background-color 0.2s;" onmouseover="this.style.backgroundColor='var(--color-bg)'" onmouseout="this.style.backgroundColor='transparent'">
                    <td id="tax-label-${i}" style="padding: 4px;">${item.label}</td>
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
        
        // Buat container animasi progres jika belum ada
        if (!document.getElementById('taxonomy-progress-anim')) {
            const wrapper = document.createElement('div');
            wrapper.id = 'taxonomy-progress-anim';
            wrapper.style.display = 'none';
            wrapper.style.fontFamily = 'var(--font-mono)';
            wrapper.style.fontSize = '0.8rem';
            wrapper.style.padding = '8px';
            wrapper.style.borderTop = '1px dashed var(--color-border)';
            wrapper.style.marginTop = '10px';
            wrapper.style.background = 'var(--color-bg)';
            term.parentNode.insertBefore(wrapper, term.nextSibling);
        }
    },

    renderProgressAnim(stage, current, total) {
        const wrapper = document.getElementById('taxonomy-progress-anim');
        if (!wrapper) return;
        wrapper.style.display = 'block';
        
        let pct = 0;
        if (total > 0) pct = Math.floor((current / total) * 100);
        
        // Animasi playful (Neobrutalism blocks)
        const ticks = Math.floor(Date.now() / 300) % 4; // Berubah tiap 300ms
        const dotAnim = ['.   ', '..  ', '... ', '....'][ticks];
        const blockAnim = ['▖', '▘', '▝', '▗'][ticks];
        
        const barWidth = 20;
        const filled = Math.floor((pct / 100) * barWidth);
        const barStr = '█'.repeat(filled) + '░'.repeat(Math.max(0, barWidth - filled));
        
        wrapper.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:bold; color:var(--color-primary);">${blockAnim} SEDANG MEMPROSES: ${stage.toUpperCase()} ${dotAnim}</span>
                <span style="font-weight:bold;">${current} / ${total} [${pct}%]</span>
            </div>
            <div style="margin-top: 4px; color:var(--color-ink); letter-spacing: 2px;">
                ${barStr}
            </div>
        `;
    },

    hideProgressAnim() {
        const wrapper = document.getElementById('taxonomy-progress-anim');
        if (wrapper) wrapper.style.display = 'none';
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
    showLoading() {
        const container = document.getElementById('db-explorer-list');
        const preview = document.getElementById('db-explorer-preview');
        
        // Desain progres loader retro
        if (container) {
            container.innerHTML = `
                <div style="padding: 20px; text-align: center; font-family: var(--font-mono); color: var(--color-ink);">
                    <div style="font-size: 1.5rem; font-weight: bold; margin-bottom: 10px;">[ MEMPROSES DATA ]</div>
                    <div style="width: 80%; border: 1px solid var(--color-ink); height: 10px; margin: 0 auto; background: var(--color-paper); position: relative; overflow: hidden;">
                        <div style="position: absolute; top:0; left:0; height: 100%; width: 30%; background: var(--color-ink); animation: loading-bar 1s infinite alternate;"></div>
                    </div>
                    <div style="font-size: 0.75rem; margin-top: 10px; color: var(--color-ink-muted);">Mohon Tunggu... Server Memory-Safe Mode Aktif</div>
                    <style>@keyframes loading-bar { 0% { left: 0%; } 100% { left: 70%; } }</style>
                </div>
            `;
        }
        
        if (preview) {
            preview.innerHTML = `<div class="empty-state">MEMUAT ISI DOKUMEN...</div>`;
        }
    },

    renderError(msg) {
        const container = document.getElementById('db-explorer-list');
        const preview = document.getElementById('db-explorer-preview');
        if (container) {
            container.innerHTML = `
                <div style="padding: 30px; text-align: center; border: 2px dashed red; background: #ffebeb; color: #d00;">
                    <h3 style="margin-bottom: 15px; font-weight: bold;">[ SERVER ERROR DETECTED ]</h3>
                    <div style="font-family: monospace; font-size: 12px; background: #fff; padding: 10px; border: 1px solid red; display: inline-block;">
                        ${msg}
                    </div>
                    <div style="margin-top: 15px; font-size: 11px; color: #555;">(Periksa log server atau format database)</div>
                </div>
            `;
        }
        if (preview) preview.innerHTML = `<div class="empty-state">KONEKSI TERPUTUS</div>`;
    },

    renderDocuments(docs, total, page, totalPages, debugTime = null) {
        window._filteredDocs = docs; // Data yang sudah di-filter secara aman di Server
        const container = document.getElementById('db-explorer-list');
        const countLabel = document.getElementById('db-explorer-count');
        const preview = document.getElementById('db-explorer-preview');
        const pageInfo = document.getElementById('db-pagination-info');
        
        if (countLabel) countLabel.textContent = `${total} DOCS`;
        if (pageInfo) pageInfo.textContent = `PAGE ${page} / ${totalPages}`;
        
        if (!docs || docs.length === 0) {
            container.innerHTML = `<div class="empty-state">TIDAK ADA DOKUMEN MEMENUHI FILTER.</div>`;
            preview.innerHTML = `<div class="empty-state">PILIH DOKUMEN UNTUK MELIHAT ISI</div>`;
            return;
        }

        let html = '';
        if (debugTime !== null) {
            html += `<div style="font-family: var(--font-mono); font-size: 10px; color: #888; border-bottom: 1px dashed #ccc; padding: 4px; background: #fafafa; margin-bottom: 5px;">
                [DEBUG METRICS] Server I/O Fetch Time: <strong>${debugTime} ms</strong>
            </div>`;
        }
        
        docs.forEach((doc, idx) => {
            let tagsHtml = '';
            if (doc.labels && Array.isArray(doc.labels) && doc.labels.length > 0) {
                doc.labels.forEach(l => {
                    const isOutlier = (l === 'Tidak Terklasifikasi');
                    let tagClass = 'tag';
                    if (!isOutlier && window._currentTaxonomyData) {
                        const l1 = window._currentTaxonomyData.Layer_1_Domain || [];
                        if (l1.includes(l)) tagClass = 'tag tag-l1';
                        else tagClass = 'tag tag-l2';
                    }
                    tagsHtml += `<span class="${tagClass}" style="${isOutlier ? 'color:var(--color-danger); border-color:var(--color-danger);' : ''}">${l}</span>`;
                });
            } else {
                tagsHtml = `<span class="tag" style="color:var(--color-danger); border-color:var(--color-danger);">Tidak Terklasifikasi</span>`;
            }
            
            html += `
            <div class="accordion-row" onclick="previewDocumentFiltered(${idx})" style="padding: 10px; border-bottom: 1px dashed var(--color-border); font-family: var(--font-mono); font-size: 0.8rem;">
                <div style="font-weight:bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px;">ID: ${doc.id}</div>
                <div class="tag-list" style="margin-top:0;">${tagsHtml}</div>
            </div>
            `;
        });
        
        container.innerHTML = html;
        if (docs.length > 0) {
            window.previewDocumentFiltered(0);
        }
    }
};

window.previewDocumentFiltered = function(idx) {
    if (!window._filteredDocs || !window._filteredDocs[idx]) return;
    const doc = window._filteredDocs[idx];
    const preview = document.getElementById('db-explorer-preview');
    
    let tagsStr = doc.labels ? doc.labels.join(', ') : 'Tidak Terklasifikasi';
    
    preview.innerHTML = `
        <div style="font-family: var(--font-mono); font-size: 0.85rem; margin-bottom: 15px;">
            <div style="font-weight: bold; border-bottom: 1px solid var(--color-ink); padding-bottom: 4px; margin-bottom: 8px;">DOKUMEN #${doc.id}</div>
            <div style="color: var(--color-ink-muted);">LABEL: <span style="color:var(--color-ink); font-weight:bold;">${tagsStr}</span></div>
        </div>
        <div style="line-height: 1.6; font-size: 0.9rem;">
            ${doc.content}
        </div>
    `;
    const selectedRow = document.getElementById('row-' + doc.id);
    if (selectedRow) selectedRow.style.backgroundColor = 'var(--color-highlight)';
};

// GLOBAL: COPY FULL TAXONOMY ANIMATION
window.copyFullTaxonomy = function(event) {
    const selObj = document.getElementById('select-db');
    let dbName = selObj ? selObj.options[selObj.selectedIndex].text : "DATABASE";
    // Title case it to look nice
    dbName = dbName.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');

    let text = `Dari database ${dbName}\n`;
    
    const countMap = {};
    window._currentLabelsData.forEach(l => {
        countMap[l.label] = l.count;
    });

    const tax = window._currentTaxonomyData;
    let l1 = tax && tax.Layer_1_Domain ? tax.Layer_1_Domain : [];
    let l2 = tax && tax.Layer_2_Detail ? tax.Layer_2_Detail : [];
    
    // [FIXED] Stale Taxonomy Protection
    // Jika backend secara tidak sengaja mengembalikan fallback ("Umum") namun tabel aktual 
    // (_currentLabelsData) memiliki lebih dari 1 label riil, maka parsing label langsung dari tabel.
    if (l1.includes("Umum") && window._currentLabelsData.length > 1) {
        l1 = [];
        l2 = [];
        window._currentLabelsData.forEach(item => {
            if (item.label.toLowerCase().includes("domain")) {
                l1.push(item.label);
            } else {
                l2.push(item.label);
            }
        });
    }

    if (l1.length > 0) {
        text += "Level 1 :\n";
        l1.forEach(l => {
            const count = countMap[l] || 0;
            text += `- ${l} <${count} dokumen>\n`;
        });
    }

    if (l2.length > 0) {
        text += "\nLevel 2 :\n";
        l2.forEach(l => {
            const count = countMap[l] || 0;
            text += `- ${l} <${count} dokumen>\n`;
        });
    }

    // 1. Copy text to clipboard
    navigator.clipboard.writeText(text).catch(err => console.error("Clipboard failed:", err));
    
    // 2. Swarm Animation
    const mouseX = event.clientX;
    const mouseY = event.clientY;

    window._currentLabelsData.forEach((item, i) => {
        const cell = document.getElementById(`tax-label-${i}`);
        if (!cell) return;
        
        const rect = cell.getBoundingClientRect();
        
        const animEl = document.createElement('div');
        animEl.textContent = item.label;
        animEl.className = 'copy-anim-float';
        // Add random slight delay so they look like a swarm flying one by one
        const delay = Math.random() * 0.2;
        animEl.style.animationDelay = `${delay}s`;
        
        animEl.style.left = rect.left + 'px';
        animEl.style.top = rect.top + 'px';
        
        const tx = mouseX - rect.left;
        const ty = mouseY - rect.top;
        
        animEl.style.setProperty('--tx', tx + 'px');
        animEl.style.setProperty('--ty', ty + 'px');
        
        document.body.appendChild(animEl);
        
        setTimeout(() => {
            if (document.body.contains(animEl)) {
                document.body.removeChild(animEl);
            }
        }, 800 + (delay * 1000));
    });
};
