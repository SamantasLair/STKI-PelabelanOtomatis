import sys
from huggingface_hub import HfApi

# Minta input nama repo jika tidak ada argumen
repo_id = input("Masukkan nama repo Hugging Face Space baru Anda (contoh: AMUE/STKI-Engine): ").strip()

if not repo_id:
    print("Nama repo tidak boleh kosong!")
    sys.exit(1)

api = HfApi()

print(f"Menginisiasi upload ke {repo_id} via Python API...")

try:
    api.upload_folder(
        folder_path=".",
        repo_id=repo_id,
        repo_type="space",
        ignore_patterns=[
            "*.db",
            "*.sqlite3",
            "onnx_model.zip", # Exclude zip to save 41MB (model is already unzipped)
            "_RawData/*",
            "_BackupDemo/*",
            ".git/*",
            "venv/*",
            "env/*",
            "testing/*",
            "_Quality_Assurance/*",
            "_Fondasi/*",
            "_doctrine/*",
            "_memory/system_error.log",
            "__pycache__/*",
            "*.pyc",
            "DS/*",
            "_databases/*",
            "*.docx",
            "ETL_HAKI/*",
            "ETL_Looker/*",
            "LAPORAN_AKHIR_STKI.md"
        ]
    )
    print("✅ Berhasil! Semua file kode telah terkirim ke Hugging Face Spaces.")
except Exception as e:
    print(f"❌ Gagal: {e}")
