// _UIUX/stki/js/viewmodels/ingestVM.js
// _UIUX/stki/js/viewmodels/ingestVM.js
const IngestVM = {
    init() {
        const btn = document.getElementById('btn-ingest');
        btn.addEventListener('click', () => this.execute());
        
        const dropArea = document.getElementById('ingest-file-drop');
        const fileInput = document.getElementById('input-file-ingest');
        const label = document.getElementById('ingest-file-label');
        
        dropArea.addEventListener('click', () => fileInput.click());
        
        dropArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropArea.classList.add('dragover');
        });
        
        dropArea.addEventListener('dragleave', () => {
            dropArea.classList.remove('dragover');
        });
        
        dropArea.addEventListener('drop', (e) => {
            e.preventDefault();
            dropArea.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                label.textContent = "Terpilih: " + fileInput.files[0].name;
            }
        });
        
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                label.textContent = "Terpilih: " + fileInput.files[0].name;
            }
        });
    },

    async execute() {
        const fileInput = document.getElementById('input-file-ingest');
        if (fileInput.files.length === 0) {
            IngestView.appendLog("GAGAL: Tidak ada file yang dipilih.", "error");
            return;
        }

        const file = fileInput.files[0];
        IngestView.appendLog(`MEMULAI INGESTI: ${file.name} (${(file.size / 1024).toFixed(2)} KB)`, "warn");

        try {
            // Upload, Extract Text, Compute Embedding, and Insert to DB
            const data = await ApiService.ingestUpload(file);
            
            if (data.status === 'success') {
                IngestView.appendLog(`EKSTRAKSI TEKS SUKSES: ${data.content.substring(0, 50)}...`, "info");
                IngestView.appendLog(`KLASIFIKASI ONNX (K-MEANS LABEL): [${data.labels.join(', ')}]`, "info");
                IngestView.appendLog(`SIMPAN KE DB: ${data.filename} BERHASIL DISISIPKAN.`, "success");
                
                // Update global UI status (N documents increased)
                App.updateGlobalStatus();
            } else {
                IngestView.appendLog(`ERROR API: ${data.error}`, "error");
            }
        } catch (err) {
            IngestView.appendLog(`SYSTEM ERROR: ${err.message}`, "error");
        } finally {
            IngestView.resetInput();
            document.getElementById('ingest-file-label').textContent = "Klik atau Seret Dokumen ke Sini (PDF/DOCX/CSV)";
        }
    }
};
