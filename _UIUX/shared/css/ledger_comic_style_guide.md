# Refined Retro Ledger - Style Guide

## Konsep Inti
Desain ini menggabungkan tema **Ledger (Buku Besar/Parchment)** klasik STKI dengan interaktivitas **Neobrutalism / 80s Comic Inking**.
Fokus utamanya adalah pada elemen *Hard Shadows* (bayangan padat tanpa blur) dan interaksi mekanis (tombol yang benar-benar masuk secara visual saat ditekan).

## 1. Palet Warna (Dipertahankan)
- Latar Belakang: `--color-bg` (Parchment/Kertas)
- Elemen Kertas: `--color-paper` (Putih gading)
- Tinta: `--color-ink` (Hitam pudar pekat)
- Aksen: Merah Bata/Marun (Danger), Biru Pudar/Primary.
- *Aturan: Jangan menggunakan warna neon/clashing 80-an murni.*

## 2. Garis & Batas (Inking)
- Border harus tetap tajam namun rasional: `1px` atau `2px solid var(--color-ink)`.
- Jangan menggunakan border yang terlalu tebal (misal > 3px) agar hierarki visual akademik tetap terjaga.

## 3. Bayangan (Hard Shadows)
- DILARANG menggunakan bayangan kabur (`blur > 0px`).
- Formula Bayangan: `box-shadow: 2px 2px 0px var(--color-ink)`.
- Untuk elemen yang lebih besar atau mengambang, bisa menggunakan `4px 4px 0px`.

## 4. Animasi Interaktif (Mechanical Pop)
- Keadaan Normal: Memiliki *Hard Shadow*.
- Keadaan Ditekan (`:active`): Elemen bergeser menutupi bayangannya sendiri, memberikan ilusi mekanis.
```css
.btn:active {
    transform: translate(2px, 2px);
    box-shadow: 0px 0px 0px var(--color-ink);
}
```

## 5. UI Elements Khusus
- **Slider (`input[type=range]`):** Menghilangkan `-webkit-appearance: none;` asli peramban. Tuas (*thumb*) harus berupa kotak mekanis bergaris tepi, dan jalur (*track*) harus berupa garis hitam solid tebal.
- **Tooltip (`[data-tooltip]`):** Tampil seperti kotak teks komik atau deskripsi *blueprint*, dengan *hard shadow*, garis tegas, dan font monospace atau proporsional. Tidak menggunakan UI bawaan Windows/Mac.
