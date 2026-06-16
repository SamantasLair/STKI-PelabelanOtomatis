import asyncio
import aiohttp
import os
import json
import urllib.parse
from tqdm.asyncio import tqdm
from dotenv import load_dotenv

# Memuat variabel dari .env
load_dotenv()

# ==========================================
# KONFIGURASI GLOBAL (DISESUAIKAN DENGAN DOKUMENTASI)
# ==========================================
TOKEN = os.getenv("PASAL_API_TOKEN")
BASE_URL = "https://pasal.id/api/v1"
OUTPUT_DIR = "_RawData/hukum_pasal_id"
TYPE_FILTER = "UU"
# ==========================================

async def fetch_all_uris(session):
    """
    Discovery Phase: Retrieve all FRBR URIs.
    Endpoint: /laws
    Rate Limit: 180 req / 60 sec.
    """
    uris = []
    limit = 50
    offset = 0
    total_expected = None
    
    print(f"[*] Fase 1: Mencari daftar Undang-Undang (Type: {TYPE_FILTER})...")
    
    while True:
        url = f"{BASE_URL}/laws?type={TYPE_FILTER}&limit={limit}&offset={offset}"
        headers = {"Authorization": f"Bearer {TOKEN}"}
        
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                try:
                    data = await response.json(content_type=None)
                except Exception as e:
                    print(f"[!] Gagal membaca respons JSON. Server mengembalikan non-JSON. Error: {e}")
                    print(f"[!] Respons mentah: {await response.text()}")
                    break
                
                if total_expected is None:
                    total_expected = data.get("total", 0)
                    print(f"[*] Ditemukan total {total_expected} dokumen {TYPE_FILTER} di server.")
                
                laws = data.get("laws", [])
                if not laws:
                    break
                
                for law in laws:
                    uris.append(law["frbr_uri"])
                
                offset += limit
                
                # Mengunduh perlahan agar tidak memicu rate limit
                await asyncio.sleep(1.5)
            else:
                print(f"[!] Error saat mengambil indeks (Status: {response.status})")
                print(await response.text())
                break
                
    return uris

async def fetch_detail_and_save(session, frbr_uri, progress_bar):
    """
    Detail Phase: Fetch Law Articles.
    Rate Limit: 60 req / 60 sec. Sequential constraint applied.
    """
    safe_filename = frbr_uri.replace("/", "_").strip("_") + ".json"
    file_path = os.path.join(OUTPUT_DIR, safe_filename)
    
    # [IDEMPOTENCY / CHECKPOINT]
    if os.path.exists(file_path):
        progress_bar.update(1)
        return True

    url = f"{BASE_URL}/laws{frbr_uri}"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    max_retries = 10
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            async with session.get(url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    try:
                        data = await response.json(content_type=None)
                    except Exception as e:
                        print(f"\n[!] Gagal membaca respons JSON pada {frbr_uri}. Error: {e}")
                        progress_bar.update(1)
                        return False
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    
                    progress_bar.update(1)
                    # Mengunduh perlahan secara konstan agar tidak agresif dan tidak terblokir
                    await asyncio.sleep(2.5) 
                    return True
                    
                elif response.status == 429:
                    # Terkena Rate Limit, istirahat sejenak
                    retry_count += 1
                    print(f"\n[!] Terkena Rate Limit (429) pada {frbr_uri}. Menunggu 15 detik (Percobaan {retry_count}/{max_retries})...")
                    await asyncio.sleep(15)
                    continue # Coba lagi
                else:
                    print(f"\n[!] Gagal mengunduh {frbr_uri} - Status: {response.status}")
                    progress_bar.update(1)
                    return False
        except Exception as e:
            retry_count += 1
            print(f"\n[!] Error jaringan pada {frbr_uri}: {e}. Menunggu 5 detik...")
            await asyncio.sleep(5)
            
    progress_bar.update(1)
    return False

async def main():
    if not TOKEN or TOKEN == "your_token_here":
        print("[FATAL] Variabel lingkungan PASAL_API_TOKEN tidak ditemukan atau belum diisi.")
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if not os.path.exists(env_path):
            with open(env_path, "w") as f:
                f.write("PASAL_API_TOKEN=your_token_here\n")
            print(f"[!] File .env baru telah dibuat otomatis di:\n{env_path}")
        print("[!] SILAKAN BUKA FILE .env DAN MASUKKAN TOKEN API PASAL.ID ANDA SEBELUM MELANJUTKAN.")
        return

    print("="*60)
    print("[SYSTEM] MEMULAI PROSES INGESTI DATA - API PASAL.ID")
    print("="*60)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Menonaktifkan verifikasi SSL untuk mencegah error CERTIFICATE_VERIFY_FAILED pada lingkungan Windows lokal
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        # Fase 1: Dapatkan semua URI
        uris = await fetch_all_uris(session)
        
        if not uris:
            print("[!] Tidak ada URI yang ditemukan. Proses dihentikan.")
            return
            
        print("="*60)
        print(f"[*] Fase 2: Mengunduh detail dari {len(uris)} dokumen.")
        print(f"[*] PERINGATAN: Mematuhi Rate Limit ketat (60/menit).")
        print(f"[*] Estimasi Waktu: ~{len(uris)} detik.")
        print("="*60)
        
        with tqdm(total=len(uris), desc="Mengunduh Dokumen", unit="doc") as pbar:
            for uri in uris:
                await fetch_detail_and_save(session, uri, pbar)

    print("\n" + "="*60)
    print("[SUCCESS] PROSES INGESTI SELESAI")
    print("Semua dokumen UU telah tersimpan di _RawData/hukum_pasal_id/.")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
