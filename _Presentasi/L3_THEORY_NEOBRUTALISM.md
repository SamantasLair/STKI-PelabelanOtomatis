# [L3] THEORY & PRACTICE: NEOBRUTALISM DESIGN THEORY

Di ekosistem L2 *Neobrutalism Frontend*, antarmuka tidak dikonstruksi untuk kenyamanan visual (*aesthetic comfort*), melainkan untuk **efisiensi transmisi data dan penekanan arsitektural**. Filosofi *Neobrutalisme* STKI membuang elemen DOM yang memakan waktu (bayangan difusi yang difilter berlapis, blur latar belakang *glassmorphism*, gradien berlapis komputasi GPU berlebih). Pendekatan ini adalah manifestasi langsung dari kecepatan O(1) *Backend*, di mana transisi interaksi harus bersifat seketika (mekanistik).

Antarmuka Neobrutalisme menyokong *BIG DATA Doctrine* karena penumpukan visual *raw* berbasis *hard-border* dan *high-contrast block* menuntut pemrosesan *Rendering Tree* (*Layouting* & *Painting*) seminimal mungkin dari web browser.

### 1. Landasan Visual & Atribut Metrik DOM

Arsitektur DOM dikuantifikasi sebagai kumpulan node biner dengan hierarki sesedikit mungkin.
Kriteria Rendering STKI Neobrutalism:
- **Border Stroke:** Tepi absolut hitam tebal (minimum $2$px, disarankan $3$px-$4$px).
- **Shadow Offset:** Tanpa gradasi *blur*. Proyeksi bayangan menggunakan translasi X dan Y murni secara absolut (`box-shadow: 4px 4px 0px #000;`).
- **Chromaticity:** Saturasi absolut. Warna hanya direpresentasikan dalam kode Hex primer bertenaga tinggi tanpa peredaman alpha (contoh: *Bright Yellow*, *Saturated Red*, *Neon Blue*).

### 2. Implementasi Source Code

*Source File:* `_UIUX/stki/index.css` (Ekstraksi Kelas Utilitas Sentral)
Logika visual ini tidak menggunakan *framework* kompleks semacam Tailwind pada inti telemetri untuk mencegah *bloat* kelas DOM, melainkan mengandalkan *Vanilla CSS Variables* tersentralisasi.

```css
:root {
  --neo-border: 3px solid #111;
  --neo-shadow: 6px 6px 0px #111;
  --neo-hover-shadow: 2px 2px 0px #111;
  
  --bg-primary: #f8f5ee; /* Kertas Ledger */
  --accent-alert: #ff4757; /* Penalti Cosine */
  --accent-pass: #2ed573; /* Irisan Venn Lulus */
}

.neo-card {
  background-color: #fff;
  border: var(--neo-border);
  box-shadow: var(--neo-shadow);
  transition: all 0.1s cubic-bezier(0, 1, 0, 1); /* Transisi Mekanistik Kaku */
  border-radius: 4px;
}

.neo-card:active {
  box-shadow: var(--neo-hover-shadow);
  transform: translate(4px, 4px); /* Taktil: Penekanan Fisik */
}
```

### 3. Batas Eksekusi & Mitigasi Limit

- **Saturasi Visual Kognitif (Cognitive Overload):** Border yang sangat tebal dapat menghancurkan hierarki tipografi jika tidak diimbangi dengan *whitespace* absolut di dalam padding elemen.
- **Mitigasi:** Aturan "Spasial Kosong" O(2) memaksakan padding ganda pada semua *Container Neobrutalist*. Setiap informasi numerik teoretis (contohnya variabel matriks $\alpha$) wajib diletakkan pada bingkai taktil yang besar untuk membedakannya dari derau N-Gram dokumen biasa.

---
*Konteks: Eksekusi L3 dari [[L2_UIUX_NEOBRUTALISM]]*
