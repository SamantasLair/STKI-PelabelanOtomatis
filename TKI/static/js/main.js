// State Globals
let activeDatabaseType = 'akademik';
let alphaValue = 0.70;
let selectedLabelName = '';

// Inisialisasi awal
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initStatus();
    loadDatabaseLabels();
});

// 1. SYSTEM NAVIGATION (TABS)
function initTabs() {
    const menuItems = document.querySelectorAll('.menu-item');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    const pageHeaders = {
        'search-tab': {
            title: 'Hybrid Retrieval & Search Engine',
            desc: 'Pencarian semantik berkepadatan tinggi (Dense BERT) dikawinkan dengan BM25 leksikal persis.'
        },
        'predict-tab': {
            title: 'Semantic Document Analysis',
            desc: 'Inferensi zero-shot neural untuk memetakan dokumen ke taksonomi multi-layer secara waktu-nyata.'
        },
        'taxonomy-tab': {
            title: 'Taxonomy & Metadata Manager',
            desc: 'Kelola taksonomi dinamis, hitung Rice Rule matematika, dan jalankan batch relabeling ONNX.'
        },
        'recommendation-tab': {
            title: 'Smart Content Recommendation',
            desc: 'Rekomendasi aset terpisah antara file Data (.csv/.xlsx) dan file Literatur Akademik (.pdf/.docx).'
        }
    };

    menuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetTab = item.getAttribute('data-tab');
            
            // Toggle active menu class
            menuItems.forEach(m => m.classList.remove('active'));
            item.classList.add('active');
            
            // Toggle active tab panes
            tabPanes.forEach(pane => {
                pane.classList.remove('active');
                if (pane.id === targetTab) {
                    pane.classList.add('active');
                }
            });

            // Update Topbar
            const header = pageHeaders[targetTab];
            if (header) {
                document.getElementById('page-title').textContent = header.title;
                document.getElementById('page-desc').textContent = header.desc;
            }
        });
    });
}

// 2. SYSTEM STATUS & DB SWITCHER
async function initStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        activeDatabaseType = data.db_type;
        
        // Update switcher buttons
        const dbSelector = document.getElementById('db-selector');
        if (dbSelector) {
            dbSelector.value = activeDatabaseType;
        }
        
        // Update Rice Rule Stats
        document.getElementById('lbl-stat-docs').textContent = data.total_docs;
        document.getElementById('lbl-stat-optimal').textContent = data.optimal_labels_count;
        document.getElementById('lbl-stat-actual').textContent = data.actual_labels_count;
        
    } catch (err) {
        console.error('Gagal mengambil status sistem:', err);
    }
}

async function switchDatabase(targetDb) {
    showToast(`Beralih ke Database ${targetDb.toUpperCase()}...`);
    
    try {
        const response = await fetch('/api/switch_db', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ db_type: targetDb })
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            activeDatabaseType = targetDb;
            showToast(data.message);
            
            // Refresh Status & UI
            await initStatus();
            loadDatabaseLabels();
            
            // Clear current Search results/inputs
            document.getElementById('inp-search-query').value = '';
            document.getElementById('search-results-container').innerHTML = `
                <div class="empty-state">
                    <h3>Database Dialihkan</h3>
                    <p>Masukkan kata kunci kueri untuk mencari di dalam database ${targetDb.toUpperCase()} yang baru.</p>
                </div>
            `;
            document.getElementById('results-count-bar').style.display = 'none';
        }
    } catch (err) {
        showToast('Gagal memindahkan database aktif', 'error');
    }
}

// 3. HYBRID SEARCH
function updateAlphaDisplay(val) {
    alphaValue = parseFloat(val);
    document.getElementById('val-alpha-display').textContent = alphaValue.toFixed(2);
}

// Toggle Leaderboard Snippet Content
function toggleLeaderboardContent(btn) {
    const item = btn.closest('.leaderboard-item');
    const content = item.querySelector('.leaderboard-content-highlight');
    const isHidden = content.style.display === 'none';
    content.style.display = isHidden ? 'block' : 'none';
    btn.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
}

async function executeSearch() {
    const query = document.getElementById('inp-search-query').value.trim();
    if (!query) {
        showToast('Ketik kueri pencarian terlebih dahulu!', 'error');
        return;
    }
    
    const resultsContainer = document.getElementById('search-results-container');
    resultsContainer.innerHTML = `
        <div class="empty-state">
            <h3>Menghitung Skor Kemiripan Hibrida...</h3>
            <p>Inferensi model BERT ONNX dan kombinasi skor leksikal BM25 sedang diproses...</p>
        </div>
    `;
    
    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query, alpha: alphaValue })
        });
        const docs = await response.json();
        
        resultsContainer.innerHTML = '';
        
        if (docs.length === 0) {
            resultsContainer.innerHTML = `
                <div class="empty-state">
                    <h3>Dokumen Tidak Ditemukan</h3>
                    <p>Tidak ada berkas di database yang melampaui batas keyakinan kueri ini.</p>
                </div>
            `;
            document.getElementById('results-count-bar').style.display = 'none';
            return;
        }
        
        document.getElementById('results-count').textContent = docs.length;
        document.getElementById('results-count-bar').style.display = 'block';
        
        docs.forEach((doc, idx) => {
            const tagsHtml = doc.labels.map(l => `<span class="doc-tag">${l}</span>`).join('');
            const rank = String(idx + 1).padStart(2, '0');
            const rankClass = idx === 0 ? 'rank-1' : idx === 1 ? 'rank-2' : idx === 2 ? 'rank-3' : 'rank-other';
            
            const card = document.createElement('div');
            card.className = `leaderboard-item ${rankClass}`;
            card.innerHTML = `
                <div class="leaderboard-rank">${rank}</div>
                <div class="leaderboard-details">
                    <div class="leaderboard-meta">
                        <span class="leaderboard-name">${doc.filename}</span>
                        <div class="leaderboard-tags">${tagsHtml}</div>
                    </div>
                    <div class="leaderboard-score-wrapper">
                        <div class="leaderboard-progress-container">
                            <div class="leaderboard-progress-bar" style="width: ${doc.similarity.toFixed(1)}%"></div>
                        </div>
                        <div class="leaderboard-score-value">${doc.similarity.toFixed(1)}% Similarity</div>
                    </div>
                </div>
                <button class="leaderboard-toggle-btn" onclick="toggleLeaderboardContent(this)">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4 h-4" style="transition: transform var(--transition-speed) ease;"><path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" /></svg>
                </button>
                <div class="leaderboard-content-highlight" style="display: none;">
                    <div class="score-breakdown">
                        <span class="breakdown-item">BERT Dense: <strong>${doc.dense_score.toFixed(1)}%</strong></span>
                        <span class="breakdown-divider">|</span>
                        <span class="breakdown-item">BM25 Sparse: <strong>${doc.sparse_score.toFixed(1)}%</strong></span>
                    </div>
                    <div class="highlight-text">${doc.content}</div>
                </div>
            `;
            resultsContainer.appendChild(card);
        });
        
    } catch (err) {
        showToast('Kesalahan memproses pencarian hibrida', 'error');
    }
}

// ================= RECOMMENDATION ENGINE =================
async function executeRecommendation() {
    const query = document.getElementById('inp-reco-query').value.trim();
    if (!query) {
        showToast('Ketik kueri pencarian terlebih dahulu!', 'error');
        return;
    }
    
    const dataContainer = document.getElementById('reco-data-container');
    const docsContainer = document.getElementById('reco-docs-container');
    
    dataContainer.innerHTML = `<div class="empty-state"><p>Mencari dataset...</p></div>`;
    docsContainer.innerHTML = `<div class="empty-state"><p>Mencari literatur...</p></div>`;
    
    try {
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query, alpha: alphaValue, limit: 100, offset: 0 })
        });
        const docs = await response.json();
        
        dataContainer.innerHTML = '';
        docsContainer.innerHTML = '';
        
        const dataFiles = docs.data_files || [];
        const docFiles = docs.doc_files || [];
        
        document.getElementById('count-reco-data').textContent = dataFiles.length;
        document.getElementById('count-reco-docs').textContent = docFiles.length;
        
        const renderItem = (doc, idx) => {
            const rank = String(idx + 1).padStart(2, '0');
            return `
                <div class="leaderboard-item" style="padding: 12px 16px; margin-bottom: 8px;">
                    <div class="leaderboard-rank" style="font-size: 16px;">${rank}</div>
                    <div class="leaderboard-details">
                        <div class="leaderboard-meta">
                            <span class="leaderboard-name" style="font-size: 13px;">${doc.filename}</span>
                        </div>
                        <div class="leaderboard-score-wrapper" style="margin-top: 6px;">
                            <div class="leaderboard-progress-container" style="height: 6px;">
                                <div class="leaderboard-progress-bar" style="width: ${doc.similarity.toFixed(1)}%; background: ${doc.similarity > 80 ? 'var(--color-success)' : 'var(--color-primary)'};"></div>
                            </div>
                            <div class="leaderboard-score-value" style="font-size: 11px;">${doc.similarity.toFixed(1)}% Match</div>
                        </div>
                    </div>
                </div>
            `;
        };
        
        if (dataFiles.length === 0) {
            dataContainer.innerHTML = `<div class="empty-state"><p>Tidak ada dataset yang cocok ditemukan.</p></div>`;
        } else {
            dataFiles.forEach((doc, idx) => { dataContainer.innerHTML += renderItem(doc, idx); });
        }
        
        if (docFiles.length === 0) {
            docsContainer.innerHTML = `<div class="empty-state"><p>Tidak ada literatur yang cocok ditemukan.</p></div>`;
        } else {
            docFiles.forEach((doc, idx) => { docsContainer.innerHTML += renderItem(doc, idx); });
        }
        
    } catch (err) {
        showToast('Kesalahan memproses pencarian rekomendasi', 'error');
    }
}

// 4. BATCH CLASSIFIER / PREDICTOR
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    document.getElementById('lbl-file-name').textContent = file.name;
    document.getElementById('txt-predict-input').value = 'Membaca dan memproses berkas...';
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showToast('Mengunggah dan membaca isi berkas...');
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        if (data.error) {
            showToast(data.error, 'error');
            document.getElementById('txt-predict-input').value = '';
            return;
        }
        
        // Letakkan isi file di textarea dan otomatis trigger analisa
        document.getElementById('txt-predict-input').value = data.content;
        showToast('Berkas berhasil dibaca! Memicu inferensi ONNX...');
        
        executePrediction();
        
    } catch (err) {
        showToast('Kesalahan saat mengunggah berkas', 'error');
        document.getElementById('txt-predict-input').value = '';
    }
}

async function executePrediction() {
    const text = document.getElementById('txt-predict-input').value.trim();
    if (!text) {
        showToast('Masukkan konten teks untuk dianalisis!', 'error');
        return;
    }
    
    showToast('Menganalisis makna semantik via BERT ONNX...');
    
    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        const data = await response.json();
        
        if (data.error) {
            showToast(data.error, 'error');
            return;
        }
        
        // Renders Best Tier Banner
        const bestL1 = data.layer_1[0].label;
        const bestL1Score = data.layer_1[0].score;
        const bestL2 = data.layer_2[0].label;
        const bestL2Score = data.layer_2[0].score;
        
        document.getElementById('best-tag-l1').textContent = `${bestL1} (${bestL1Score.toFixed(1)}%)`;
        document.getElementById('best-tag-l2').textContent = `${bestL2} (${bestL2Score.toFixed(1)}%)`;
        
        // Render Layer 1 Bars
        const containerL1 = document.getElementById('prediction-bars-l1');
        containerL1.innerHTML = '';
        data.layer_1.forEach(item => {
            containerL1.appendChild(createProgressBarItem(item.label, item.score));
        });
        
        // Render Layer 2 Bars (Top 5 saja agar rapi)
        const containerL2 = document.getElementById('prediction-bars-l2');
        containerL2.innerHTML = '';
        data.layer_2.slice(0, 5).forEach(item => {
            containerL2.appendChild(createProgressBarItem(item.label, item.score));
        });
        
        showToast('Klasifikasi semantik berhasil diselesaikan!');
        
    } catch (err) {
        showToast('Gagal memproses inferensi ONNX', 'error');
    }
}

function createProgressBarItem(label, score) {
    const div = document.createElement('div');
    div.className = 'progress-item';
    div.innerHTML = `
        <span class="progress-label" title="${label}">${label}</span>
        <div class="progress-track">
            <div class="progress-fill" style="width: ${score.toFixed(1)}%"></div>
        </div>
        <span class="progress-val">${score.toFixed(1)}%</span>
    `;
    return div;
}

// 5. TAXONOMY CRUD MANAGER
async function loadDatabaseLabels(filterStr = '') {
    const container = document.getElementById('db-labels-container');
    container.innerHTML = `<div style="text-align: center; color: var(--text-muted); font-size: 12px; padding: 24px;">Memuat data taksonomi...</div>`;
    
    try {
        const response = await fetch('/api/labels');
        const labels = await response.json();
        
        container.innerHTML = '';
        
        const filtered = labels.filter(item => item.label.toLowerCase().includes(filterStr.toLowerCase()));
        
        if (filtered.length === 0) {
            container.innerHTML = `<div style="text-align: center; color: var(--text-muted); font-size: 12px; padding: 24px;">Tidak ada label yang cocok</div>`;
            return;
        }
        
        filtered.forEach(item => {
            const div = document.createElement('div');
            div.className = `label-list-item ${selectedLabelName === item.label ? 'selected' : ''}`;
            div.innerHTML = `
                <span class="lbl-name">${item.label}</span>
                <span class="lbl-badge-count">${item.count} Dokumen</span>
            `;
            
            div.addEventListener('click', () => {
                // Select label
                selectedLabelName = item.label;
                document.querySelectorAll('.label-list-item').forEach(el => el.classList.remove('selected'));
                div.classList.add('selected');
                
                // Populate inputs
                document.getElementById('inp-active-label').value = item.label;
                document.getElementById('inp-old-label').value = item.label;
            });
            
            container.appendChild(div);
        });
        
    } catch (err) {
        container.innerHTML = `<div style="text-align: center; color: var(--color-danger); font-size: 12px; padding: 24px;">Gagal memuat label</div>`;
    }
}

async function executeEditLabel() {
    const oldName = document.getElementById('inp-old-label').value.trim();
    const newName = document.getElementById('inp-active-label').value.trim();
    
    if (!oldName) {
        showToast('Pilih label dari daftar terlebih dahulu!', 'error');
        return;
    }
    if (!newName) {
        showToast('Nama label baru tidak boleh kosong!', 'error');
        return;
    }
    if (oldName === newName) return;
    
    try {
        const response = await fetch('/api/labels/edit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ old_name: oldName, new_name: newName })
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            showToast(data.message);
            selectedLabelName = '';
            document.getElementById('inp-old-label').value = '';
            document.getElementById('inp-active-label').value = '';
            loadDatabaseLabels();
            initStatus();
        } else {
            showToast(data.message, 'error');
        }
    } catch (err) {
        showToast('Kesalahan saat memperbarui label', 'error');
    }
}

async function executeDeleteLabel() {
    const label = document.getElementById('inp-old-label').value.trim();
    if (!label) {
        showToast('Pilih label dari daftar terlebih dahulu!', 'error');
        return;
    }
    
    const confirmDelete = confirm(`Apakah Anda yakin ingin menghapus label '${label}' dari semua berkas dokumen?`);
    if (!confirmDelete) return;
    
    try {
        const response = await fetch('/api/labels/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ label: label })
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            showToast(data.message);
            selectedLabelName = '';
            document.getElementById('inp-old-label').value = '';
            document.getElementById('inp-active-label').value = '';
            loadDatabaseLabels();
            initStatus();
        } else {
            showToast(data.message, 'error');
        }
    } catch (err) {
        showToast('Gagal menghapus label', 'error');
    }
}

async function executeAddLabel(level) {
    const label = document.getElementById('inp-active-label').value.trim();
    if (!label) {
        showToast('Ketik nama label yang ingin ditambahkan!', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/labels/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ label: label, level: level })
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            showToast(data.message);
            document.getElementById('inp-active-label').value = '';
            loadDatabaseLabels();
            initStatus();
        } else {
            showToast(data.message, 'error');
        }
    } catch (err) {
        showToast('Gagal menambahkan label taksonomi baru', 'error');
    }
}

// 6. BATCH ACTIONS WITH ASYNC PROGRESS POLLING
async function executeRegenerateLabels() {
    const confirmAction = confirm("Tindakan batch ini akan menginferensi ulang seluruh dokumen database dengan model BERT-mini. Lanjutkan?");
    if (!confirmAction) return;
    
    try {
        const response = await fetch('/api/labels/regenerate', { method: 'POST' });
        const data = await response.json();
        
        if (data.status === 'success') {
            // Show Overlay Progress Dialog
            const overlay = document.getElementById('progress-overlay-pane');
            overlay.style.display = 'flex';
            
            // Start Polling
            pollRegenerateProgress();
        } else {
            showToast(data.message, 'error');
        }
    } catch (err) {
        showToast('Kesalahan memicu batch relabeling', 'error');
    }
}

function pollRegenerateProgress() {
    const fill = document.getElementById('progress-fill');
    const text = document.getElementById('progress-status-text');
    const overlay = document.getElementById('progress-overlay-pane');
    
    const interval = setInterval(async () => {
        try {
            const res = await fetch('/api/labels/regenerate/progress');
            const progress = await res.json();
            
            if (progress.status === 'running') {
                fill.style.width = `${progress.percentage}%`;
                fill.textContent = `${progress.percentage}%`;
                text.textContent = `Memproses: ${progress.current} / ${progress.total} Berkas`;
            } else if (progress.status === 'success') {
                clearInterval(interval);
                fill.style.width = '100%';
                fill.textContent = '100%';
                text.textContent = 'Selesai!';
                
                setTimeout(() => {
                    overlay.style.display = 'none';
                    showToast('Batch regenerasi label ONNX sukses diselesaikan!');
                    loadDatabaseLabels();
                    initStatus();
                }, 1000);
            } else if (progress.status === 'failed') {
                clearInterval(interval);
                overlay.style.display = 'none';
                showToast('Batch regenerasi label mengalami kegagalan sistem!', 'error');
            }
        } catch (err) {
            clearInterval(interval);
            overlay.style.display = 'none';
            showToast('Koneksi polling terputus', 'error');
        }
    }, 800);
}

async function executeResetDatabase() {
    const confirmReset = confirm("Tindakan ini akan menghapus database aktif dan meresetnya ke sampel awal 1.000 berkas secara bersih. Lanjutkan?");
    if (!confirmReset) return;
    
    showToast('Sedang mereset dan memicu ulang seeding database...');
    
    try {
        const response = await fetch('/api/reset_db', { method: 'POST' });
        const data = await response.json();
        
        if (data.status === 'success') {
            showToast(data.message);
            await initStatus();
            loadDatabaseLabels();
        } else {
            showToast(data.message, 'error');
        }
    } catch (err) {
        showToast('Gagal mereset database', 'error');
    }
}

// 7. TOAST NOTIFICATION UTILITY
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    
    if (type === 'error') {
        toast.classList.add('error');
    } else {
        toast.classList.remove('error');
    }
    
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}
