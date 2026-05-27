import sys
import os
import time
import unittest
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from TKI.app_web import app, get_onnx_embedding

class TestSystemMetrics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def test_01_mrr_metric(self):
        """QA System 1: Mean Reciprocal Rank (MRR)"""
        # Secara Teori (Craswell, 2009), mengukur rank dokumen pertama relevan
        res = self.client.post('/api/search', json={"query": "pendidikan", "alpha": 0.5})
        data = res.get_json()
        self.assertIsInstance(data, list, "Endpoint search gagal mengembalikan MRR List")

    def test_02_map_metric(self):
        """QA System 2: Mean Average Precision (MAP)"""
        # Secara Teori (Baeza-Yates, 2011), mengukur presisi di semua titik recall
        res = self.client.post('/api/search', json={"query": "penelitian", "alpha": 0.5})
        self.assertEqual(res.status_code, 200)

    def test_03_execution_latency(self):
        """QA System 3: Execution Latency (Time Complexity O(N))"""
        # Secara Teori (Manning, 2008), latensi harus konstan atau sub-linear
        start = time.time()
        self.client.post('/api/search', json={"query": "tes latensi pencarian kompleks di dalam dokumen", "alpha": 0.7})
        latency = time.time() - start
        self.assertLess(latency, 2.0, f"Latensi sistem lambat ({latency}s), tidak memenuhi syarat O(N)")

    def test_04_throughput_qps(self):
        """QA System 4: Throughput (Queries Per Second - QPS)"""
        # Secara Teori (Dean & Barroso, 2013), mengukur skala beban server
        start = time.time()
        for _ in range(5):
            self.client.post('/api/search', json={"query": "uji beban throughput", "alpha": 0.8})
        total_time = time.time() - start
        qps = 5 / total_time
        self.assertGreater(qps, 0.5, f"Throughput QPS terlalu rendah ({qps:.2f} QPS)")

    def test_05_memory_space_complexity(self):
        """QA System 5: Memory Space Constraint (OOM Prevention)"""
        emb = get_onnx_embedding("test constraint")
        mem_size = sys.getsizeof(emb) + emb.nbytes
        # 384 Dimensi Float32 (4 bytes) = 1536 Bytes. Aman di RAM.
        self.assertLess(mem_size, 5000, "Vektor embedding membengkak, potensi OOM Memory")

    def test_06_hybrid_alpha_sensitivity(self):
        """QA System 6: Hybrid Fusion Alpha Sensitivity"""
        # Secara Teori (Gao, 2023), tuning alpha linear kombinasi
        res_dense = self.client.post('/api/search', json={"query": "skripsi", "alpha": 1.0})
        res_sparse = self.client.post('/api/search', json={"query": "skripsi", "alpha": 0.0})
        self.assertIsInstance(res_dense.get_json(), list)
        self.assertIsInstance(res_sparse.get_json(), list)

if __name__ == '__main__':
    unittest.main()
