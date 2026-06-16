// _UIUX/ds/js/viewmodels/taxonomyVM.js
const TaxonomyVM = {
    init() {
        // Bind generate button
        const btnGen = document.getElementById('btn-generate-taxonomy');
        if (btnGen) {
            btnGen.addEventListener('click', () => this.executeGenerate());
        }

        // Bind sliders with LocalStorage persistence
        const sl1 = document.getElementById('slider-l1');
        const vl1 = document.getElementById('val-l1');
        if (sl1 && vl1) {
            const saved1 = localStorage.getItem('stki_threshold_l1');
            if (saved1) { sl1.value = saved1; vl1.textContent = parseFloat(saved1).toFixed(2); }
            sl1.addEventListener('input', e => {
                vl1.textContent = parseFloat(e.target.value).toFixed(2);
                localStorage.setItem('stki_threshold_l1', e.target.value);
            });
            sl1.addEventListener('change', e => {
                fetch('/api/taxonomy/settings', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({key: 'threshold_l1', value: e.target.value}) });
            });
        }

        const sl2 = document.getElementById('slider-l2');
        const vl2 = document.getElementById('val-l2');
        if (sl2 && vl2) {
            const saved2 = localStorage.getItem('stki_threshold_l2');
            if (saved2) { sl2.value = saved2; vl2.textContent = parseFloat(saved2).toFixed(2); }
            sl2.addEventListener('input', e => {
                vl2.textContent = parseFloat(e.target.value).toFixed(2);
                localStorage.setItem('stki_threshold_l2', e.target.value);
            });
            sl2.addEventListener('change', e => {
                fetch('/api/taxonomy/settings', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({key: 'threshold_l2', value: e.target.value}) });
            });
        }

        this.setupDropzone();

        // Bind pipeline nodes
        document.getElementById('node-db')?.addEventListener('click', () => {
            TaxonomyView.setActiveNode('node-db', 'panel-db');
        });
        document.getElementById('node-onnx')?.addEventListener('click', () => {
            TaxonomyView.setActiveNode('node-onnx', 'panel-onnx');
        });
        document.getElementById('node-kmeans')?.addEventListener('click', () => {
            TaxonomyView.setActiveNode('node-kmeans', 'panel-kmeans');
        });
        document.getElementById('node-taxonomy')?.addEventListener('click', () => {
            TaxonomyView.setActiveNode('node-taxonomy', 'panel-taxonomy');
        });
    },

    currentPage: 1,
    currentFilter: 'all',
    totalPages: 1,

    async load() {
        try {
            const labels = await ApiService.getLabels();
            TaxonomyView.renderList(labels);
            
            this.fetchDocuments();
        } catch (err) {
            console.error(err);
        }
    },

    async fetchDocuments() {
        try {
            if (typeof TaxonomyView.showLoading === 'function') {
                TaxonomyView.showLoading();
            }
            const docsRes = await ApiService.getDocuments(this.currentPage, 50, this.currentFilter);
            if (docsRes.status === 'success') {
                this.totalPages = docsRes.total_pages;
                this.currentPage = docsRes.page;
                // [DEBUG METRICS] Teruskan informasi ke View untuk merender log debug
                TaxonomyView.renderDocuments(docsRes.documents, docsRes.total, this.currentPage, this.totalPages, docsRes.debug_time_ms);
            } else {
                TaxonomyView.renderError(docsRes.message || "Gagal memuat dokumen.");
            }
        } catch (err) {
            console.error(err);
            TaxonomyView.renderError(err.toString());
        }
    },

    changeFilter(filterType) {
        this.currentFilter = filterType;
        this.currentPage = 1; // reset to first page
        this.fetchDocuments();
    },

    nextPage() {
        if (this.currentPage < this.totalPages) {
            this.currentPage++;
            this.fetchDocuments();
        }
    },

    prevPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.fetchDocuments();
        }
    },

    async updateStats(totalDocs, optimal, taxonomy) {
        TaxonomyView.updateTelemetry(totalDocs, optimal);
        TaxonomyView.setTaxonomyData(taxonomy);
        if (taxonomy) {
            const listL1 = document.getElementById('list-l1');
            const listL2 = document.getElementById('list-l2');
            
            if (listL1 && taxonomy.Layer_1_Domain) {
                listL1.innerHTML = taxonomy.Layer_1_Domain.map(l => 
                    `<div class="ledger-row" style="padding: 6px; border-bottom: 1px dashed var(--color-border); display: flex; justify-content: space-between; align-items:center; transition: background 0.2s;" onmouseover="this.style.background='var(--color-bg)'" onmouseout="this.style.background='transparent'">
                        <span style="font-weight:bold;">${l}</span>
                        <div style="display:flex; gap:8px;">
                            <button onclick="TaxonomyVM.editLabel('${l}', 'Layer_1_Domain')" class="btn" style="padding:2px 6px; font-size:0.7rem; border-width: 1px;">EDIT</button>
                            <button onclick="TaxonomyVM.deleteLabel('${l}', 'Layer_1_Domain')" class="btn btn-danger" style="padding:2px 6px; font-size:0.7rem; border-width: 1px;">X</button>
                        </div>
                    </div>`
                ).join('');
            }
            if (listL2 && taxonomy.Layer_2_Detail) {
                listL2.innerHTML = taxonomy.Layer_2_Detail.map(l => 
                    `<div class="ledger-row" style="padding: 6px; border-bottom: 1px dashed var(--color-border); display: flex; justify-content: space-between; align-items:center; transition: background 0.2s;" onmouseover="this.style.background='var(--color-bg)'" onmouseout="this.style.background='transparent'">
                        <span style="font-weight:bold;">${l}</span>
                        <div style="display:flex; gap:8px;">
                            <button onclick="TaxonomyVM.editLabel('${l}', 'Layer_2_Detail')" class="btn" style="padding:2px 6px; font-size:0.7rem; border-width: 1px;">EDIT</button>
                            <button onclick="TaxonomyVM.deleteLabel('${l}', 'Layer_2_Detail')" class="btn btn-danger" style="padding:2px 6px; font-size:0.7rem; border-width: 1px;">X</button>
                        </div>
                    </div>`
                ).join('');
            }
            
            // Inject dynamic filters
            const filterEl = document.getElementById('filter-db-explorer');
            if (filterEl && taxonomy.Layer_1_Domain && taxonomy.Layer_2_Detail) {
                // Keep the standard options
                let optionsHtml = `
                    <option value="all">SEMUA DOKUMEN</option>
                    <option value="outlier">OUTLIERS (Tidak Terklasifikasi)</option>
                    <option value="overlap">VENN OVERLAPS (>1 Label)</option>
                `;
                if (taxonomy.Layer_1_Domain.length > 0) {
                    optionsHtml += `<optgroup label="LAYER 1 (DOMAIN)">`;
                    taxonomy.Layer_1_Domain.forEach(l => {
                        optionsHtml += `<option value="label_${l}">${l}</option>`;
                    });
                    optionsHtml += `</optgroup>`;
                }
                if (taxonomy.Layer_2_Detail.length > 0) {
                    optionsHtml += `<optgroup label="LAYER 2 (DETAIL)">`;
                    taxonomy.Layer_2_Detail.forEach(l => {
                        optionsHtml += `<option value="label_${l}">${l}</option>`;
                    });
                    optionsHtml += `</optgroup>`;
                }
                
                // Save current value before overwriting
                const currentVal = filterEl.value;
                filterEl.innerHTML = optionsHtml;
                
                // Restore value if it still exists
                if (filterEl.querySelector(`option[value="${currentVal}"]`)) {
                    filterEl.value = currentVal;
                }
            }
            
            // Sync fallback if localStorage empty
            const sl1 = document.getElementById('slider-l1');
            const vl1 = document.getElementById('val-l1');
            if (sl1 && !localStorage.getItem('stki_threshold_l1') && taxonomy.threshold_l1) {
                sl1.value = taxonomy.threshold_l1;
                vl1.textContent = parseFloat(taxonomy.threshold_l1).toFixed(2);
            }
            
            const sl2 = document.getElementById('slider-l2');
            const vl2 = document.getElementById('val-l2');
            if (sl2 && !localStorage.getItem('stki_threshold_l2') && taxonomy.threshold_l2) {
                sl2.value = taxonomy.threshold_l2;
                vl2.textContent = parseFloat(taxonomy.threshold_l2).toFixed(2);
            }
            
            // Render Saved Metrics (Persistence state)
            if (taxonomy.metrics) {
                const mout = document.getElementById('metric-outliers');
                const moutc = document.getElementById('metric-outliers-count');
                if (mout) mout.textContent = `${taxonomy.metrics.outlier_pct}%`;
                if (moutc) moutc.textContent = `${taxonomy.metrics.outliers} / ${taxonomy.metrics.total_docs} Docs`;
                
                const mov = document.getElementById('metric-overlaps');
                const movc = document.getElementById('metric-overlaps-count');
                if (mov) mov.textContent = `${taxonomy.metrics.overlap_pct}%`;
                if (movc) movc.textContent = `${taxonomy.metrics.overlaps} / ${taxonomy.metrics.total_docs} Docs`;
            }
        }
    },

    executeGenerate() {
        UIHelpers.showCustomModal(
            "WARNING: Tindakan ini akan mengeksekusi algoritma Cosine Thresholding secara masif berdasar seluruh data di database. Lanjutkan?", 
            async () => {
                TaxonomyView.clearTerminal();
                TaxonomyView.renderTerminalLog("MEMULAI PROSES ALGORITMA MULTI-LABEL CLUSTERING...");
                
                TaxonomyView.setEdgeAnimation('edge-1', true);
                TaxonomyView.setEdgeAnimation('edge-2', true);
                TaxonomyView.setEdgeAnimation('edge-3', true);
                
                const t1 = parseFloat(document.getElementById('slider-l1')?.value || 0.50);
                const t2 = parseFloat(document.getElementById('slider-l2')?.value || 0.55);
                
                // Mulai polling progres
                window._progressInterval = setInterval(async () => {
                    try {
                        const pRes = await fetch('/api/taxonomy/progress');
                        const pData = await pRes.json();
                        if (pData.status === 'running') {
                            TaxonomyView.renderProgressAnim(pData.stage, pData.current, pData.total);
                        } else {
                            TaxonomyView.hideProgressAnim();
                        }
                    } catch (e) {}
                }, 800);
                
                try {
                    const data = await ApiService.generateTaxonomy(t1, t2);
                    if (data.status === 'success') {
                        TaxonomyView.renderTerminalLog(`SUKSES: ${data.message}`, "success");
                        TaxonomyView.renderTerminalLog(`LAYER 1 DOMAIN TERBENTUK: ${data.taxonomy.Layer_1_Domain.length} label`, "info");
                        TaxonomyView.renderTerminalLog(`LAYER 2 DETAIL TERBENTUK: ${data.taxonomy.Layer_2_Detail.length} label`, "info");
                        
                        // Update Telemetry Matrix
                        if (data.metrics) {
                            const mout = document.getElementById('metric-outliers');
                            const moutc = document.getElementById('metric-outliers-count');
                            if (mout) mout.textContent = `${data.metrics.outlier_pct}%`;
                            if (moutc) moutc.textContent = `${data.metrics.outliers} / ${data.metrics.total_docs} Docs`;
                            
                            const mov = document.getElementById('metric-overlaps');
                            const movc = document.getElementById('metric-overlaps-count');
                            if (mov) mov.textContent = `${data.metrics.overlap_pct}%`;
                            if (movc) movc.textContent = `${data.metrics.overlaps} / ${data.metrics.total_docs} Docs`;
                            
                            TaxonomyView.renderTerminalLog(`TELEMETRY: Outliers=${data.metrics.outlier_pct}% | Overlaps=${data.metrics.overlap_pct}%`, "info");
                        }
                        
                        // Refresh list
                        this.load();
                        App.updateGlobalStatus();
                    } else {
                        TaxonomyView.renderTerminalLog(`GAGAL: ${data.message || data.error}`, "error");
                    }
                } catch (err) {
                    TaxonomyView.renderTerminalLog(`SYSTEM ERROR: ${err.message}`, "error");
                } finally {
                    clearInterval(window._progressInterval);
                    TaxonomyView.hideProgressAnim();
                    TaxonomyView.setEdgeAnimation('edge-1', false);
                    TaxonomyView.setEdgeAnimation('edge-2', false);
                    TaxonomyView.setEdgeAnimation('edge-3', false);
                }
            }
        );
    },

    setupDropzone() {
        const dropzone = document.getElementById('dropzone');
        const fileInput = document.getElementById('batch-file-input');
        const btnWipe = document.getElementById('btn-wipe-db');
        
        if (dropzone && fileInput) {
            dropzone.addEventListener('click', () => fileInput.click());
            
            dropzone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropzone.style.borderColor = 'var(--color-primary)';
                dropzone.style.backgroundColor = 'var(--color-highlight)';
            });
            
            dropzone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                dropzone.style.borderColor = 'var(--color-border)';
                dropzone.style.backgroundColor = 'var(--color-bg)';
            });
            
            dropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropzone.style.borderColor = 'var(--color-border)';
                dropzone.style.backgroundColor = 'var(--color-bg)';
                if (e.dataTransfer.files.length) {
                    this.uploadBatch(e.dataTransfer.files);
                }
            });
            
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length) {
                    this.uploadBatch(e.target.files);
                }
            });
        }
        
        if (btnWipe) {
            btnWipe.addEventListener('click', () => this.wipeDatabase());
        }
    },

    wipeDatabase() {
        UIHelpers.showCustomModal(
            "DANGER: Apakah Anda yakin ingin menghapus SELURUH dokumen di pangkalan data aktif? Tindakan ini tidak bisa dibatalkan.",
            async () => {
                try {
                    const res = await fetch('/api/documents/wipe', { method: 'POST' });
                    const data = await res.json();
                    if (data.status === 'success') {
                        TaxonomyView.renderTerminalLog(`WIPE SUCCESS: ${data.message}`, "success");
                        this.load();
                        App.updateGlobalStatus();
                    } else {
                        TaxonomyView.renderTerminalLog(`WIPE FAILED: ${data.message}`, "error");
                    }
                } catch (err) {
                    TaxonomyView.renderTerminalLog(`WIPE ERROR: ${err.message}`, "error");
                }
            }
        );
    },

    async uploadBatch(files) {
        const progress = document.getElementById('upload-progress');
        progress.style.display = 'block';
        progress.innerHTML = `<span style="color:var(--color-warn)">Memproses ${files.length} dokumen... Mohon tunggu.</span>`;
        
        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files[]', files[i]);
        }
        
        try {
            const res = await fetch('/api/documents/batch_upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            
            if (data.status === 'success') {
                progress.innerHTML = `<span style="color:var(--color-success)">${data.message}</span>`;
                this.load();
                App.updateGlobalStatus();
            } else {
                progress.innerHTML = `<span style="color:var(--color-danger)">GAGAL: ${data.message}</span>`;
            }
        } catch (err) {
            progress.innerHTML = `<span style="color:var(--color-danger)">ERROR: ${err.message}</span>`;
        }
    },

    async addLabel(layer) {
        const inputId = layer === 'Layer_1_Domain' ? 'input-l1' : 'input-l2';
        const inputEl = document.getElementById(inputId);
        const labelName = inputEl.value.trim();
        
        if (!labelName) return;
        
        try {
            const res = await fetch('/api/taxonomy/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: labelName, layer: layer })
            });
            const data = await res.json();
            if (data.status === 'success') {
                inputEl.value = '';
                App.updateGlobalStatus();
            } else {
                alert(data.error || "Gagal menambah label.");
            }
        } catch (err) {
            console.error(err);
        }
    },

    editLabel(oldName, layer) {
        const newName = prompt(`Masukkan nama baru untuk label '${oldName}':\n(Perhatian: Dokumen terkait akan di-scan ulang secara otomatis)`, oldName);
        if (!newName || newName.trim() === '' || newName === oldName) return;
        
        UIHelpers.showCustomModal(
            `Ubah label '${oldName}' menjadi '${newName}'? Sistem akan memicu re-embedding latar belakang untuk memperbarui status dokumen.`,
            async () => {
                try {
                    const res = await fetch('/api/taxonomy/edit', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ old_name: oldName, new_name: newName.trim(), layer: layer })
                    });
                    const data = await res.json();
                    if (data.status === 'success') {
                        App.updateGlobalStatus();
                        TaxonomyView.renderTerminalLog(`MASS EDIT SUKSES: Memicu pemindaian ulang latar belakang...`, "success");
                    } else {
                        TaxonomyView.renderTerminalLog(`GAGAL EDIT: ${data.error}`, "error");
                    }
                } catch (err) {
                    console.error(err);
                }
            }
        );
    },

    deleteLabel(labelName, layer) {
        UIHelpers.showCustomModal(
            `Hapus label '${labelName}' secara permanen dari sistem? Dokumen terkait akan dievaluasi ulang tanpa label ini.`,
            async () => {
                try {
                    const res = await fetch('/api/taxonomy/delete', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name: labelName, layer: layer })
                    });
                    const data = await res.json();
                    if (data.status === 'success') {
                        App.updateGlobalStatus();
                        TaxonomyView.renderTerminalLog(`HAPUS SUKSES: Memicu pemindaian ulang latar belakang...`, "success");
                    } else {
                        TaxonomyView.renderTerminalLog(`GAGAL HAPUS: ${data.error}`, "error");
                    }
                } catch (err) {
                    console.error(err);
                    TaxonomyView.renderTerminalLog(`SYSTEM ERROR: ${err.message}`, "error");
                }
            }
        );
    }
};
