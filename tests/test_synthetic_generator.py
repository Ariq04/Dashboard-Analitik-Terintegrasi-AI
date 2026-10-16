"""
tests/test_synthetic_generator.py
Pengujian Otomatis Integritas dan Validasi Dataset Sintetis Demo.
"""

import os
import sys
import sqlite3
import unittest
import tempfile
import hashlib
import pandas as pd

# Pastikan path direktori proyek tersedia
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scripts.generate_synthetic_data import generate_synthetic_dataset


class TestSyntheticDataIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = os.path.join(BASE_DIR, "data", "demo_klinik.db")
        if not os.path.exists(cls.db_path):
            generate_synthetic_dataset(cls.db_path, seed=42)
        cls.conn = sqlite3.connect(cls.db_path)
        cls.conn.execute("PRAGMA foreign_keys = ON;")

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_1_tables_exist(self):
        """Memverifikasi bahwa seluruh tabel yang dibutuhkan dashboard tersedia."""
        expected_tables = {
            "demo_users",
            "demo_service_categories",
            "demo_services",
            "demo_visits",
            "demo_visit_services",
            "demo_visit_diagnoses",
            "demo_prescriptions",
            "demo_satisfaction_respondents",
            "demo_satisfaction_elements",
            "demo_satisfaction_summary",
        }
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables_found = {row[0] for row in cursor.fetchall()}
        missing = expected_tables - tables_found
        self.assertEqual(len(missing), 0, f"Tabel yang hilang: {missing}")

    def test_2_required_columns_exist(self):
        """Memverifikasi seluruh kolom yang dibutuhkan oleh queries.py dan auth.py."""
        required_schema = {
            "demo_users": ["id_user", "nama_lengkap", "email", "password"],
            "demo_visits": ["no_registrasi", "no_rm", "waktu_daftar", "total", "payment_type"],
            "demo_service_categories": ["id_kategoriKlinik", "kategoriKlinik", "target"],
            "demo_services": ["kode", "nama_layanan", "id_kategori"],
            "demo_visit_services": ["id", "kode", "kodeLayanan", "layanan", "subtotal"],
            "demo_visit_diagnoses": ["id", "kode", "penyakit"],
            "demo_prescriptions": ["id", "kode", "nama_produk", "qty", "subtotal"],
            "demo_satisfaction_respondents": ["id", "tanggal", "jenis_layanan", "q1", "q16"],
        }
        cursor = self.conn.cursor()
        for table, cols in required_schema.items():
            cursor.execute(f"PRAGMA table_info({table});")
            existing_cols = {row[1].lower() for row in cursor.fetchall()}
            for col in cols:
                self.assertIn(col.lower(), existing_cols, f"Kolom {col} tidak ditemukan di tabel {table}")

    def test_3_foreign_keys_integrity(self):
        """Memverifikasi tidak ada pelanggaran relasi Foreign Key."""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA foreign_key_check;")
        fk_violations = cursor.fetchall()
        self.assertEqual(len(fk_violations), 0, f"Pelanggaran Foreign Key terdeteksi: {fk_violations}")

    def test_4_no_duplicate_primary_keys(self):
        """Memverifikasi integritas Primary Key dan constraint keunikan."""
        cursor = self.conn.cursor()
        # Cek duplikat no_registrasi
        cursor.execute("SELECT no_registrasi, COUNT(*) FROM demo_visits GROUP BY no_registrasi HAVING COUNT(*) > 1;")
        self.assertEqual(len(cursor.fetchall()), 0, "Ditemukan no_registrasi duplikat")

        # Cek duplikat email user
        cursor.execute("SELECT email, COUNT(*) FROM demo_users GROUP BY email HAVING COUNT(*) > 1;")
        self.assertEqual(len(cursor.fetchall()), 0, "Ditemukan email user duplikat")

    def test_5_sufficient_volume_for_charts(self):
        """Memverifikasi kecukupan volume data sintetis untuk visualisasi dashboard."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM demo_visits;")
        pendaftaran_count = cursor.fetchone()[0]
        self.assertGreaterEqual(pendaftaran_count, 3000, "Volume pendaftaran tidak cukup untuk tren tahunan")

        cursor.execute("SELECT COUNT(*) FROM demo_satisfaction_respondents;")
        ikm_count = cursor.fetchone()[0]
        self.assertGreaterEqual(ikm_count, 300, "Volume responden IKM tidak cukup untuk analisis unsur")

        # Rentang bulan transaksi minimal 24 bulan
        cursor.execute("SELECT COUNT(DISTINCT SUBSTR(waktu_daftar, 1, 7)) FROM demo_visits;")
        months_count = cursor.fetchone()[0]
        self.assertGreaterEqual(months_count, 24, "Jumlah bulan tidak cukup untuk analisis tren MoM")

    def test_6_ikm_formula_consistency(self):
        """Memverifikasi rumus IKM aplikasi menghasilkan angka yang identik secara matematis."""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT 
            AVG((q1+q2+q3+q4+q5+q6+q7+q8+q9+q10+q11+q12+q13+q14+q15+q16) / 16.0 * 25.0)
        FROM demo_satisfaction_respondents;
        """)
        calculated_ikm = cursor.fetchone()[0]

        cursor.execute("SELECT ikm_konversi FROM demo_satisfaction_summary LIMIT 1;")
        summary_ikm = cursor.fetchone()[0]

        self.assertAlmostEqual(calculated_ikm, summary_ikm, places=1, msg="Nilai IKM konversi tidak konsisten")

    def test_7_revenue_aggregation_match(self):
        """Memverifikasi bahwa total transaksi di demo_visits sama dengan sum(layanan + resep)."""
        df_reg = pd.read_sql("SELECT no_registrasi, total FROM demo_visits LIMIT 200;", self.conn)
        df_lay = pd.read_sql("SELECT kode, SUM(subtotal) as tot_lay FROM demo_visit_services GROUP BY kode;", self.conn)
        df_rx = pd.read_sql("SELECT kode, SUM(subtotal) as tot_rx FROM demo_prescriptions GROUP BY kode;", self.conn)

        merged = df_reg.merge(df_lay, left_on='no_registrasi', right_on='kode', how='left').fillna(0)
        merged = merged.merge(df_rx, left_on='no_registrasi', right_on='kode', how='left').fillna(0)
        merged['expected_total'] = merged['tot_lay'] + merged['tot_rx']

        diff = (merged['total'] - merged['expected_total']).abs().max()
        self.assertLessEqual(diff, 0.01, "Terdapat inkonsistensi total transaksi dengan rincian subtotal")

    def test_8_reproducibility_deterministic(self):
        """Memverifikasi bahwa generator dengan seed yang sama menghasilkan data yang identik."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp1:
            tmp1_path = tmp1.name
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp2:
            tmp2_path = tmp2.name

        try:
            stats1 = generate_synthetic_dataset(tmp1_path, seed=42)
            stats2 = generate_synthetic_dataset(tmp2_path, seed=42)

            self.assertEqual(stats1, stats2, "Statistik baris antar run tidak identik")

            # Verifikasi hash data baris registrasi pertama
            c1 = sqlite3.connect(tmp1_path)
            c2 = sqlite3.connect(tmp2_path)
            rows1 = c1.execute("SELECT * FROM demo_visits ORDER BY no_registrasi LIMIT 50;").fetchall()
            rows2 = c2.execute("SELECT * FROM demo_visits ORDER BY no_registrasi LIMIT 50;").fetchall()
            c1.close()
            c2.close()

            self.assertEqual(rows1, rows2, "Data sintetis tidak identik saat dijalankan dengan seed yang sama")
        finally:
            if os.path.exists(tmp1_path):
                os.remove(tmp1_path)
            if os.path.exists(tmp2_path):
                os.remove(tmp2_path)

    def test_9_no_external_connection(self):
        """Memverifikasi bahwa engine database tidak mengarah ke server MySQL produksi eksternal."""
        from src.database.connection import get_db_engine
        engine = get_db_engine()
        self.assertEqual(engine.dialect.name, "sqlite", "Engine terdeteksi bukan SQLite")
        self.assertNotIn("mysql", str(engine.url), "Terdeteksi URL MySQL pada engine portofolio")


if __name__ == "__main__":
    unittest.main()
