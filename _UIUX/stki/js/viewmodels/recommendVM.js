// _UIUX/stki/js/viewmodels/recommendVM.js
const RecommendVM = {
    init() {
        const btn = document.getElementById('btn-recommend');
        const input = document.getElementById('input-reco-query');
        
        btn.addEventListener('click', () => this.execute());
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this.execute();
        });
        
        const dropArea = document.getElementById('reco-file-drop');
        const fileInput = document.getElementById('input-reco-file');
        const label = document.getElementById('reco-file-label');
        
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
                label.textContent = "Berkas Terpilih: " + fileInput.files[0].name + " (Mencari...)";
                this.executeFile(fileInput.files[0]);
            }
        });
        
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                label.textContent = "Berkas Terpilih: " + fileInput.files[0].name + " (Mencari...)";
                this.executeFile(fileInput.files[0]);
            }
        });
    },

    async execute() {
        const query = document.getElementById('input-reco-query').value.trim();
        if (!query) return;
        this.runRecommendation(query);
    },
    
    async executeFile(file) {
        if (!file) return;
        document.getElementById('input-reco-query').value = ""; // Clear text input
        this.runRecommendation(file);
    },
    
    async runRecommendation(queryOrFile) {
        const alpha = document.getElementById('input-alpha').value;
        RecommendView.renderLoading();

        try {
            const docs = await ApiService.recommend(queryOrFile, alpha, 100);
            RecommendView.renderResults(docs);
        } catch (err) {
            RecommendView.renderError(err.message);
        } finally {
            // Reset file input label
            document.getElementById('reco-file-label').textContent = "Atau unggah dokumen (PDF/DOCX/CSV) untuk mencari literatur yang serupa dengan isi file tersebut...";
            document.getElementById('input-reco-file').value = "";
        }
    }
};
