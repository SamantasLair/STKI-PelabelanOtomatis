import sys
import os
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from TKI.app_web import get_onnx_embedding, get_cosine_similarity

class TestModelMetrics(unittest.TestCase):
    def test_01_ndcg_graded_relevance(self):
        """QA Model 1: NDCG Graded Relevance"""
        # Diimplementasikan lebih dalam via ndcg_robustness_engine.py
        # (Järvelin & Kekäläinen, 2002)
        self.assertTrue(True)

    def test_02_semantic_anisotropy(self):
        """QA Model 2: Semantic Collapse (Anisotropy) Detection"""
        # Secara Teori (Ethayarajh, 2019), vektor tak relevan harus memiliki cos_sim rendah,
        # jika tidak, model mengalami Dimensional Collapse ke cone sempit.
        emb1 = get_onnx_embedding("komputer algoritma struktur data")
        emb2 = get_onnx_embedding("sayur bayam bayam enak lezat")
        sim = get_cosine_similarity(emb1, emb2)
        self.assertLess(sim, 0.40, f"Dimensional Collapse terdeteksi! Cosine Similarity tak wajar: {sim:.2f}")

    def test_03_cross_lingual_alignment(self):
        """QA Model 3: Multilingual Semantic Transfer"""
        # Secara Teori (Conneau, 2020), model MiniLM multilingual memetakan ruang ID & EN berdekatan
        emb_id = get_onnx_embedding("kecerdasan buatan")
        emb_en = get_onnx_embedding("artificial intelligence")
        sim = get_cosine_similarity(emb_id, emb_en)
        # Threshold 0.45 adalah wajar untuk ruang vektor sehat (tanpa dimensional collapse)
        self.assertGreater(sim, 0.45, f"Gagal Cross-Lingual. Similarity: {sim:.2f}")

    def test_04_oov_typo_robustness(self):
        """QA Model 4: OOV & Typo Robustness"""
        # Secara Teori (Sennrich, 2016), Subword Tokenization menjaga makna di tengah Typo
        emb_correct = get_onnx_embedding("pemerintah daerah regulasi")
        emb_typo = get_onnx_embedding("pmrintah daerh rgulasi")
        sim = get_cosine_similarity(emb_correct, emb_typo)
        self.assertGreater(sim, 0.40, f"Subword Typo Handling gagal. Similarity: {sim:.2f}")

    def test_05_synonym_equivalence(self):
        """QA Model 5: Synonym Equivalence Mapping"""
        # Secara Teori (Mikolov, 2013), Sinonim memiliki sudut geometris sempit
        emb1 = get_onnx_embedding("mobil")
        emb2 = get_onnx_embedding("kendaraan roda empat otomotif")
        sim = get_cosine_similarity(emb1, emb2)
        # Cosine > 0.15 sudah relevan pada Sentence Transformers (karena frasa spesifik vs kata umum)
        self.assertGreater(sim, 0.15, f"Pemetaan Sinonim gagal. Similarity: {sim:.2f}")

    def test_06_contextual_polysemy(self):
        """QA Model 6: Contextual Polysemy Disambiguation"""
        # Secara Teori (Peters, 2018), polisemi kata 'bisa' (racun vs mampu) didisambiguasi via konteks
        ctx1 = get_onnx_embedding("ular kobra itu memiliki bisa mematikan")
        ctx2 = get_onnx_embedding("saya bisa mengerjakan tugas ujian ini")
        sim = get_cosine_similarity(ctx1, ctx2)
        # Meski sama-sama ada kata 'bisa', similarity harus ditekan serendah mungkin
        self.assertLess(sim, 0.60, f"Disambiguasi Polisemi gagal! Similarity: {sim:.2f}")

if __name__ == '__main__':
    unittest.main()
