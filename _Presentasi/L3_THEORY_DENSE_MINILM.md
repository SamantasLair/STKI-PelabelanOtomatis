# [L3] THEORY & PRACTICE: DENSE MINILM 384-D

Vektorisasi dokumen adalah tulang punggung dari representasi semantik pada arsitektur pencarian hibrida STKI. Sistem ini mendelegasikan beban pemahaman bahasa alami (NLP) kepada model *State-of-the-Art* `paraphrase-multilingual-MiniLM-L12-v2`. Karena Python sering mengalami latensi interpretasi dan konsumsi *overhead* RAM yang berat saat menjalankan PyTorch secara murni, arsitektur secara drastis direformasi dengan mengonversi model utuh tersebut ke dalam format `ONNX` (Open Neural Network Exchange).

Eksekusi mesin ONNX dibatasi pada tingkat `CPUExecutionProvider` guna membuktikan tesis bahwa pengambilan informasi berbasis *Dense* dapat beroperasi dalam tingkat performa milidetik tanpa memerlukan akselerator GPU (Cuda), menjamin *deployment* di server *legacy*.

### 1. Landasan Matematis: Arsitektur Ekstraksi Fitur

Model mentah (*base model*) memancarkan representasi tensor dalam dimensi `[1, seq_len, 384]`. Nilai spasial ini tidak dapat digunakan langsung untuk kalkulasi titik (dot product). Agar tensor multi-token ini direduksi menjadi satu ekuivalensi representasi vektor uniter berdimensi tunggal `[384]`, sistem menerapkan **Mean Pooling** yang dikalkulasi secara paksa dengan meratakan *Attention Mask*.

Formula matematis untuk *Mean Pooling*:
$$ v_{doc} = \frac{\sum_{i=1}^{N} (h_i \cdot m_i)}{\max(\sum_{i=1}^{N} m_i, \epsilon)} $$

Di mana:
- $h_i$ adalah *hidden state* token ke-$i$
- $m_i$ adalah nilai *attention mask* (1 valid, 0 padding)
- $\epsilon = 1 \times 10^{-9}$ sebagai penahan *ZeroDivisionError*

### 2. Implementasi Source Code

*Source File:* `TKI/app_web.py`
Kode di bawah mengeksekusi inferensi ONNX melalui alur memori NumPy murni, mem-*bypass* utilitas konvensional *HuggingFace*.

```python
@lru_cache(maxsize=2000)
def get_onnx_embedding(text):
    if session is None or tokenizer is None:
        return np.zeros(5)
    
    # 1. Reduksi Entropi Input
    distilled_text = extract_key_sentences(text, num_sentences=5)
    
    # 2. Tokenisasi via Rust Engine
    encoded = tokenizer.encode(distilled_text.lower())
    input_ids = np.array([encoded.ids], dtype=np.int64)
    attention_mask = np.array([encoded.attention_mask], dtype=np.int64)
    
    # 3. ONNX Inference (C++ Backend)
    outputs = session.run(None, {"input_ids": input_ids, "attention_mask": attention_mask})
    
    # 4. Kalkulasi Mean Pooling Manual
    last_hidden_state = outputs[0]
    attention_mask_expanded = np.expand_dims(attention_mask, axis=-1)
    sum_embeddings = np.sum(last_hidden_state * attention_mask_expanded, axis=1)
    sum_mask = np.clip(np.sum(attention_mask_expanded, axis=1), a_min=1e-9, a_max=None)
    sentence_embedding = (sum_embeddings / sum_mask)[0]
    
    return sentence_embedding
```

### 3. Batas Eksekusi & Mitigasi Limit

- **Maximum Sequence Length Limit:** Model MiniLM membatasi horizon pemahaman hingga 256 token. Jika paper akademik berekspansi melebihi limit ini, representasi akhirnya akan mengalami "buta bagian belakang". 
- **Mitigasi:** Fungsi pembungkus `extract_key_sentences` yang menggunakan *TextRank/PageRank* asinkron untuk memilah 5 kalimat dengan bobot graf tertinggi sebelum disuntikkan ke dalam *Tokenizer*. Hal ini menjamin esensi paragraf ke-100 tetap masuk ke dimensi representasi spasial jika terbukti berbobot berat.

---
*Konteks: Eksekusi L3 dari [[L2_HYBRID_SEARCH]]*
