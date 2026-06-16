import sys
import os
import csv
import json

# Pastikan import DBConnection bisa berjalan dari direktori root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from TKI.database import DBConnection

def export_to_looker_wide(output_csv="looker_dashboard_feed.csv"):
    conn = DBConnection('_databases/stki_master.db')
    cursor = conn.cursor()
    
    # 1. Ambil Master Taxonomy (L1 dan L2)
    l1_master = set()
    l2_master = set()
    try:
        cursor.execute("SELECT layer, name FROM tb_tax_hukum")
        taxes = cursor.fetchall()
        for layer, name in taxes:
            if layer == "Layer_1_Domain":
                l1_master.add(name)
            elif layer == "Layer_2_Detail":
                l2_master.add(name)
    except Exception as e:
        print(f"Warning: Gagal mengambil taksonomi. Mungkin belum digenerate. {e}")

    # 2. Ambil Data Dokumen
    wide_data = []
    
    try:
        cursor.execute("SELECT id, filename, content, labels FROM tb_docs_hukum")
        documents = cursor.fetchall()
    except Exception as e:
        print(f"Error reading documents: {e}")
        documents = []
        
    for doc in documents:
        doc_id, filename, content, labels_str = doc
        
        # Parsing JSON labels
        try:
            labels = json.loads(labels_str)
        except:
            labels = []
            
        # Ekstraksi Tahun dan Kategori secara langsung dari Filename (Sangat Akurat)
        # Contoh filename: akn_id_act_uu_1945_1.json
        tahun_terbit = "Unknown"
        kategori_dokumen = "Unknown"
        
        parts = filename.replace(".json", "").split("_")
        if len(parts) >= 5:
            kategori_raw = parts[3].upper()
            kategori_dokumen = "Undang-Undang" if kategori_raw == "UU" else kategori_raw
            tahun_terbit = parts[4]
            
        layer_1_domains = []
        layer_2_details = []
        
        # Kategorisasi setiap label
        for lbl in labels:
            if lbl in l1_master:
                layer_1_domains.append(lbl)
            elif lbl in l2_master:
                layer_2_details.append(lbl)
                
        # Jika belum di-generate taksonominya, kita coba deteksi pattern "Domain X"
        if not layer_1_domains:
            for lbl in labels:
                if lbl.startswith("Domain "):
                    layer_1_domains.append(lbl)
                    
        # Logika Outlier: Jika tidak ada Layer 1 yang ditugaskan ke dokumen ini
        is_outlier = "Yes" if len(layer_1_domains) == 0 else "No"
        
        # Ambil Primary Label (Label pertama) untuk visualisasi Pie Chart Looker Studio yang saling eksklusif
        layer_1_primary = layer_1_domains[0] if layer_1_domains else "Belum Diklasifikasi"
        layer_2_primary = layer_2_details[0] if layer_2_details else "Belum Diklasifikasi"
        
        # Content Snippet
        content_snippet = ""
        if content:
            clean_content = content.replace("\n", " ").strip()
            content_snippet = clean_content[:150] + ("..." if len(clean_content) > 150 else "")
            
        wide_data.append({
            "document_id": doc_id,
            "filename": filename,
            "tahun_terbit": tahun_terbit,
            "layer_1_primary": layer_1_primary,
            "layer_2_primary": layer_2_primary,
            "layer_1_all": ", ".join(layer_1_domains),
            "layer_2_all": ", ".join(layer_2_details),
            "jumlah_label": len(labels),
            "indikator_outlier": is_outlier,
            "content_snippet": content_snippet
        })
                    
    conn.close()
    
    # 3. Simpan ke CSV (Format Wide)
    headers = [
        "document_id", "filename", "tahun_terbit", 
        "layer_1_primary", "layer_2_primary", "layer_1_all", "layer_2_all", "jumlah_label", 
        "indikator_outlier", "content_snippet"
    ]
    
    output_path = os.path.join(os.path.dirname(__file__), output_csv)
    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(wide_data)
        
    print(f"Berhasil mengekspor {len(wide_data)} baris data WIDE Looker Studio ke {output_path}")

if __name__ == "__main__":
    export_to_looker_wide()
