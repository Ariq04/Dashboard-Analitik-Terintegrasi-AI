"""
tests/test_dashboard_modules.py
Pengujian Otomatis Integrasi Modul Dashboard dengan Database Demo Sintetis.
"""

import os
import sys
import unittest
import pandas as pd
from datetime import date

# Pastikan root proyek masuk ke sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.database.connection import get_db_engine
from src.modules import executive, targets, operational, ikm
from src.auth.auth import login, verify_password


class TestDashboardIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = get_db_engine()

    def test_1_executive_data_loading_and_kpis(self):
        """Memverifikasi pemuatan data modul Executive Overview dan perhitungan KPI."""
        df_trend, df_growth, df_kontribusi, df_top10, df_target, err = executive.load_all_data()
        self.assertIsNone(err, f"Executive data load error: {err}")
        self.assertIsNotNone(df_trend)
        self.assertFalse(df_trend.empty)
        self.assertFalse(df_growth.empty)
        self.assertFalse(df_kontribusi.empty)
        self.assertFalse(df_top10.empty)
        self.assertFalse(df_target.empty)

        # Cek konsistensi KPI
        total_rev = df_trend['total_pendapatan'].sum()
        total_visit = df_growth['jumlah_kunjungan'].sum()
        self.assertGreater(total_rev, 100_000_000, "Total revenue harus mencerminkan riwayat transaksi multi-tahun")
        self.assertGreater(total_visit, 3000, "Total kunjungan harus mencukupi")

        # Cek perhitungan RPK
        avg_rpk = total_rev / total_visit
        self.assertGreater(avg_rpk, 10_000, "Rata-rata RPK harus bernilai masuk akal")

    def test_2_targets_performance_monitor(self):
        """Memverifikasi modul Layanan & Produk / Performance Monitor."""
        df_target, err = targets.load_data()
        self.assertIsNone(err, f"Targets data load error: {err}")
        self.assertIsNotNone(df_target)
        self.assertFalse(df_target.empty)

        # Cek kelengkapan kolom target dan aktual
        self.assertIn("target_bulanan", df_target.columns)
        self.assertIn("aktual_pendapatan", df_target.columns)
        self.assertIn("kategori", df_target.columns)

        # Cek jumlah kategori aktif
        categories = df_target['kategori'].unique()
        self.assertGreaterEqual(len(categories), 5, "Minimal ada 5 kategori layanan aktif")

    def test_3_operational_patient_and_clinical(self):
        """Memverifikasi modul Operasional (Pasien Baru/Lama, Heatmap, Obat, Penyakit)."""
        df_new_old, df_heatmap, df_avg, df_penyakit, df_produk, err = operational.load_data()
        self.assertIsNone(err, f"Operational data load error: {err}")
        self.assertFalse(df_new_old.empty)
        self.assertFalse(df_heatmap.empty)
        self.assertFalse(df_avg.empty)
        self.assertFalse(df_penyakit.empty)
        self.assertFalse(df_produk.empty)

        # Cek sebaran jam kunjungan pada heatmap
        hours_present = df_heatmap['jam'].unique()
        self.assertGreaterEqual(len(hours_present), 10, "Heatmap harus memuat variasi jam kunjungan klinik")

        # Cek data pasien baru vs lama
        statuses = df_new_old['status_pasien'].unique()
        self.assertIn("Pasien Baru", statuses)
        self.assertIn("Pasien Lama", statuses)

        # Cek ranking penyakit & obat
        self.assertIn("nama_penyakit", df_penyakit.columns)
        self.assertIn("nama_obat", df_produk.columns)

    def test_4_ikm_satisfaction_metrics(self):
        """Memverifikasi modul Kepuasan Pasien / IKM dan rumus perhitungan."""
        from src.database import queries
        df_resp = pd.read_sql(queries.get_ikm_responden_query(), self.engine)
        self.assertFalse(df_resp.empty)
        self.assertGreaterEqual(len(df_resp), 300)

        # Hitung skor Q1-Q16
        q_cols = [f"q{i}" for i in range(1, 17)]
        df_resp['rata_responden'] = df_resp[q_cols].mean(axis=1)
        df_resp['ikm_konversi'] = df_resp['rata_responden'] * 25

        nilai_ikm = df_resp['rata_responden'].mean()
        ikm_konversi = nilai_ikm * 25
        mutu, kategori = ikm.calculate_mutu_kategori(ikm_konversi)

        self.assertGreater(nilai_ikm, 2.5)
        self.assertGreater(ikm_konversi, 60.0)
        self.assertIn(mutu, ["A", "B"])
        self.assertIn(kategori, ["Sangat Baik", "Baik"])

    def test_5_authentication_flow_and_security(self):
        """Memverifikasi autentikasi demo dan fungsi verifikasi password aman."""
        # 1. Login demo valid
        self.assertTrue(login("demo@klinikpratama.com", "demo123"))
        self.assertTrue(login("admin@klinikpratama.com", "admin123"))

        # 2. Login invalid ditolak
        self.assertFalse(login("demo@klinikpratama.com", "passwordsalah"))
        self.assertFalse(login("hacker@unknown.com", "demo123"))
        self.assertFalse(login("", ""))

        # 3. Uji fungsi verify_password (SHA-256 & MD5 timing-safe)
        import hashlib
        sha_hash = "sha256$" + hashlib.sha256("test_secret".encode()).hexdigest()
        self.assertTrue(verify_password("test_secret", sha_hash))
        self.assertFalse(verify_password("wrong_secret", sha_hash))

    def test_6_no_confidential_branding_in_non_ai_code(self):
        """Memverifikasi seluruh file non-AI tidak lagi memuat nama institusi atau lokasi asli."""
        files_to_check = [
            os.path.join(BASE_DIR, "app.py"),
            os.path.join(BASE_DIR, "src", "auth", "login.py"),
            os.path.join(BASE_DIR, "src", "auth", "auth.py"),
            os.path.join(BASE_DIR, "src", "components", "sidebar.py"),
            os.path.join(BASE_DIR, "src", "modules", "executive.py"),
            os.path.join(BASE_DIR, "src", "modules", "targets.py"),
            os.path.join(BASE_DIR, "src", "modules", "operational.py"),
            os.path.join(BASE_DIR, "src", "modules", "ikm.py"),
            os.path.join(BASE_DIR, "utils", "ikm_helper.py"),
        ]

        forbidden_words = ["keimedika", "kei medika", "jambi"]

        for filepath in files_to_check:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lower()
                for word in forbidden_words:
                    self.assertNotIn(
                        word,
                        content,
                        f"Kata sensitif '{word}' masih ditemukan di {os.path.basename(filepath)}"
                    )


if __name__ == "__main__":
    unittest.main()
