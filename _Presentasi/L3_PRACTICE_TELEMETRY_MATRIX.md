# [L3] THEORY & PRACTICE: TELEMETRY MATRIX VISUALIZATION

Dalam STKI Data Science Terminal, keluaran klasifikasi irisan ganda (*Multi-Label Venn*) tidak dikembalikan sebagai string label mati. Sistem dituntut untuk membeberkan secara blak-blakan metrik penolakan (batas $\tau$), bobot penalti *Lexical Gatekeeper*, dan distribusi klaster layer 1 dan 2 dalam sebuah ruang pandang (*viewport*) tunggal. Ini dinamakan *Telemetry Matrix*. 

Metriks ini menyajikan statistik kardinalitas: rasio dokumen-ke-label yang dianut. Berdasarkan *Neobrutalism UI*, matriks ini menyingkapkan *Outlier Fallback* ("Tidak Terklasifikasi") dengan warna kontras darurat, bukan menyembunyikannya ke halaman belakang, mengundang *Data Scientist* untuk memperbaiki ambang batas $\tau$ secara *real-time*.

### 1. Landasan Logika: Konversi State ke Komponen

Konversi status dokumen ke Matriks Telemetri bertumpu pada logika rendering kondisi absolut (*Boolean Mapping*):
- $\text{State}_{Pass}$: Nilai Cosine $\ge \tau_{layer}$. Diberikan render komponen *Solid Fill Border*.
- $\text{State}_{Reject}$: Nilai Cosine $< \tau_{layer}$ atau terkena penalti *Stop-Word* $0.05 \times$. Dibuang, kecuali memicu *Fallback State*.
- $\text{State}_{Fallback}$: Himpunan irisan kosong, $\emptyset$. Memaksa injeksi label darurat dan komponen dirender berkedip kaku (*Mechanistic Pulse*).

### 2. Implementasi Source Code

*Source File:* `_UIUX/ds/main.js` (Representasi Pemetaan *Frontend*)
Render elemen dilakukan secara proksimal di ekosistem JavaScript klien dengan membaca payload `JSON` dari C-Engine SQLite.

```javascript
// Render Label Badge Neobrutalism
function createNeobrutalistBadge(labelName) {
    const badge = document.createElement("span");
    badge.className = "neo-badge";
    
    // Logika Pemetaan Kardinalitas
    if (labelName === "Tidak Terklasifikasi") {
        badge.classList.add("outlier-badge"); // Red/Black hard contrast
        badge.innerHTML = `[!] ANOMALI: ${labelName}`;
    } else {
        badge.classList.add("valid-badge"); // Green/Black hard contrast
        badge.innerHTML = labelName;
    }
    
    return badge;
}

// Render Elemen Baris Tabel
function renderDocumentRow(docData) {
    const row = document.createElement("div");
    row.className = "neo-card doc-row";
    
    const labelContainer = document.createElement("div");
    labelContainer.className = "telemetry-matrix-container";
    
    // Iterasi array O(1) karena data sudah dibersihkan oleh C-Engine Backend
    docData.labels.forEach(label => {
        labelContainer.appendChild(createNeobrutalistBadge(label));
    });
    
    row.appendChild(labelContainer);
    return row;
}
```

### 3. Batas Eksekusi & Mitigasi Limit

- **DOM Reflow Saturation:** Menyuntikkan puluhan ribu *node* lencana (*badge*) baru secara bersamaan ke dalam kerangka tabel akan membekukan *thread* utama JavaScript (Browser membeku).
- **Mitigasi:** Fragmentasi Render. Dokumen tidak pernah dilempar bulat-bulat. Terminal memaksakan paginasi ketat (limit 50 node per blok *Accordion*), dan rendering node memanfaatkan abstraksi kelas `DocumentFragment` sebelum ditempel paksa ke DOM absolut, menekan iterasi modifikasi lebar/tinggi elemen hingga 0 *repaint*.

---
*Konteks: Eksekusi L3 dari [[L2_UIUX_NEOBRUTALISM]]*
