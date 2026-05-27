// _UIUX/ds/js/viewmodels/taxonomyVM.js
const TaxonomyVM = {
    init() {
        // Bind generate button
        const btnGen = document.getElementById('btn-generate-taxonomy');
        if (btnGen) {
            btnGen.addEventListener('click', () => this.executeGenerate());
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

    async load() {
        try {
            const labels = await ApiService.getLabels();
            TaxonomyView.renderList(labels);
            
            const docsRes = await ApiService.getDocuments();
            if (docsRes.status === 'success') {
                TaxonomyView.renderDocuments(docsRes.documents);
            }
        } catch (err) {
            console.error(err);
        }
    },

    async updateStats(totalDocs, optimal, taxonomy) {
        TaxonomyView.updateTelemetry(totalDocs, optimal);
        if (taxonomy) {
            const ulL1 = document.getElementById('list-l1');
            const ulL2 = document.getElementById('list-l2');
            
            if (ulL1 && taxonomy.Layer_1_Domain) {
                ulL1.innerHTML = taxonomy.Layer_1_Domain.map(l => 
                    `<li style="padding: 4px; border-bottom: 1px dashed var(--color-border); display: flex; justify-content: space-between;">
                        <span>${l}</span>
                        <button onclick="TaxonomyVM.deleteLabel('${l}')" style="background:none; border:none; color:var(--color-danger); cursor:pointer;">X</button>
                    </li>`
                ).join('');
            }
            if (ulL2 && taxonomy.Layer_2_Detail) {
                ulL2.innerHTML = taxonomy.Layer_2_Detail.map(l => 
                    `<li style="padding: 4px; border-bottom: 1px dashed var(--color-border); display: flex; justify-content: space-between;">
                        <span>${l}</span>
                        <button onclick="TaxonomyVM.deleteLabel('${l}')" style="background:none; border:none; color:var(--color-danger); cursor:pointer;">X</button>
                    </li>`
                ).join('');
            }
        }
    },

    async executeGenerate() {
        const confirmAction = confirm("WARNING: Tindakan ini akan mengeksekusi K-Means Clustering dan merekonstruksi taksonomi secara masif berdasar seluruh data di database. Lanjutkan?");
        if (!confirmAction) return;
        
        TaxonomyView.clearTerminal();
        TaxonomyView.renderTerminalLog("MEMULAI PROSES ALGORITMA K-MEANS & TF-IDF...");
        
        TaxonomyView.setEdgeAnimation('edge-1', true);
        TaxonomyView.setEdgeAnimation('edge-2', true);
        TaxonomyView.setEdgeAnimation('edge-3', true);
        
        try {
            const data = await ApiService.generateTaxonomy();
            if (data.status === 'success') {
                TaxonomyView.renderTerminalLog(`SUKSES: ${data.message}`, "success");
                TaxonomyView.renderTerminalLog(`LAYER 1 DOMAIN TERBENTUK: ${data.taxonomy.Layer_1_Domain.length} cluster`, "info");
                TaxonomyView.renderTerminalLog(`LAYER 2 DETAIL TERBENTUK: ${data.taxonomy.Layer_2_Detail.length} cluster`, "info");
                
                // Refresh list
                this.load();
                App.updateGlobalStatus();
            } else {
                TaxonomyView.renderTerminalLog(`GAGAL: ${data.message || data.error}`, "error");
            }
        } catch (err) {
            TaxonomyView.renderTerminalLog(`SYSTEM ERROR: ${err.message}`, "error");
        } finally {
            TaxonomyView.setEdgeAnimation('edge-1', false);
            TaxonomyView.setEdgeAnimation('edge-2', false);
            TaxonomyView.setEdgeAnimation('edge-3', false);
        }
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

    async wipeDatabase() {
        if (!confirm("DANGER: Apakah Anda yakin ingin menghapus SELURUH dokumen di pangkalan data aktif? Tindakan ini tidak bisa dibatalkan.")) return;
        
        try {
            const res = await fetch('/api/documents/wipe', { method: 'POST' });
            const data = await res.json();
            if (data.status === 'success') {
                alert(data.message);
                this.load();
                App.updateGlobalStatus();
            } else {
                alert(data.message);
            }
        } catch (err) {
            alert("Error wiping database: " + err.message);
        }
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

    async addLabel(level) {
        const inputId = level === 'layer_1' ? 'input-l1' : 'input-l2';
        const inputEl = document.getElementById(inputId);
        const labelName = inputEl.value.trim();
        
        if (!labelName) return;
        
        try {
            const res = await fetch('/api/labels/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ label: labelName, level: level })
            });
            const data = await res.json();
            if (data.status === 'success') {
                inputEl.value = '';
                this.load();
            } else {
                alert(data.message);
            }
        } catch (err) {
            console.error(err);
        }
    },

    async deleteLabel(labelName) {
        if (!confirm(`Hapus label '${labelName}'?`)) return;
        
        try {
            const res = await fetch('/api/labels/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ label: labelName })
            });
            const data = await res.json();
            if (data.status === 'success') {
                this.load();
                App.updateGlobalStatus();
            } else {
                alert(data.message);
            }
        } catch (err) {
            console.error(err);
        }
    }
};
