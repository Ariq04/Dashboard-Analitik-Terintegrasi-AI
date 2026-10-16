"""
scripts/generate_synthetic_data.py
Generator Data Sintetis Deterministik untuk Dashboard Portofolio Klinik Pratama Demo.

Karakteristik:
- 100% Data Sintetis fiktif (bukan data riil pasien atau institusi tertentu).
- Deterministik: Menggunakan random seed tetap (default: 42) sehingga hasil generate selalu identik.
- Menghasilkan basis data SQLite lokal mandiri di 'data/demo_klinik.db'.
- Memenuhi seluruh relasi Foreign Key, integritas matematis, dan dialek kueri aplikasi.
"""

import os
import sys
import random
import hashlib
import sqlite3
from datetime import datetime, date, timedelta

# Pastikan path root proyek tersedia
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def create_schema(conn: sqlite3.Connection):
    """Membangun skema tabel SQLite sesuai kebutuhan seluruh kueri dashboard."""
    cursor = conn.cursor()

    # 1. Tabel Pengguna (Autentikasi Demo)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS demo_users (
        id_user INTEGER PRIMARY KEY,
        nama_lengkap TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );
    """)

    # 2. Tabel Master Kategori Layanan Klinik
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS demo_service_categories (
        id_kategoriKlinik INTEGER PRIMARY KEY,
        kategoriKlinik TEXT NOT NULL,
        target REAL NOT NULL DEFAULT 0
    );
    """)

    # 3. Tabel Master Layanan Klinik
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS demo_services (
        kode TEXT PRIMARY KEY,
        nama_layanan TEXT NOT NULL,
        id_kategori INTEGER NOT NULL,
        FOREIGN KEY (id_kategori) REFERENCES demo_service_categories(id_kategoriKlinik)
    );
    """)

    # 4. Tabel Transaksi Pendaftaran / Kunjungan Pasien
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS demo_visits (
        no_registrasi TEXT PRIMARY KEY,
        no_rm TEXT NOT NULL,
        waktu_daftar TEXT NOT NULL,
        total REAL NOT NULL DEFAULT 0,
        payment_type TEXT
    );
    """)

    # 5. Tabel Detail Layanan Pendaftaran
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS demo_visit_services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kode TEXT NOT NULL,
        kodeLayanan TEXT NOT NULL,
        layanan TEXT NOT NULL,
        subtotal REAL NOT NULL DEFAULT 0,
        FOREIGN KEY (kode) REFERENCES demo_visits(no_registrasi),
        FOREIGN KEY (kodeLayanan) REFERENCES demo_services(kode)
    );
    """)

    # 6. Tabel Diagnosis / Keluhan Pasien (ICD)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS demo_visit_diagnoses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kode TEXT NOT NULL,
        penyakit TEXT NOT NULL,
        FOREIGN KEY (kode) REFERENCES demo_visits(no_registrasi)
    );
    """)

    # 7. Tabel Resep / Produk Farmasi
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS demo_prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kode TEXT NOT NULL,
        nama_produk TEXT NOT NULL,
        qty INTEGER NOT NULL DEFAULT 1,
        subtotal REAL NOT NULL DEFAULT 0,
        FOREIGN KEY (kode) REFERENCES demo_visits(no_registrasi)
    );
    """)

    # 8. Tabel Responden IKM (Indeks Kepuasan Masyarakat)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS demo_satisfaction_respondents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tanggal TEXT NOT NULL,
        jenis_layanan TEXT NOT NULL,
        nama_responden TEXT,
        usia INTEGER,
        jenis_kelamin TEXT,
        q1 INTEGER NOT NULL,
        q2 INTEGER NOT NULL,
        q3 INTEGER NOT NULL,
        q4 INTEGER NOT NULL,
        q5 INTEGER NOT NULL,
        q6 INTEGER NOT NULL,
        q7 INTEGER NOT NULL,
        q8 INTEGER NOT NULL,
        q9 INTEGER NOT NULL,
        q10 INTEGER NOT NULL,
        q11 INTEGER NOT NULL,
        q12 INTEGER NOT NULL,
        q13 INTEGER NOT NULL,
        q14 INTEGER NOT NULL,
        q15 INTEGER NOT NULL,
        q16 INTEGER NOT NULL
    );
    """)

    # 9. Tabel Ringkasan Unsur IKM
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS demo_satisfaction_elements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unsur TEXT NOT NULL,
        total_nilai REAL NOT NULL,
        rata_rata REAL NOT NULL
    );
    """)

    # 10. Tabel Ringkasan Global IKM
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS demo_satisfaction_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        jumlah_responden INTEGER NOT NULL,
        nilai_ikm REAL NOT NULL,
        ikm_konversi REAL NOT NULL,
        mutu TEXT NOT NULL,
        kategori TEXT NOT NULL
    );
    """)

    conn.commit()


def generate_synthetic_dataset(db_path: str, seed: int = 42):
    """Menghasilkan dataset sintetis deterministik dan menyimpannya ke SQLite."""
    random.seed(seed)

    # Pastikan folder target tersedia
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    # Buka koneksi baru ke SQLite
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    create_schema(conn)

    cursor = conn.cursor()

    # Bersihkan tabel jika dijalankan ulang
    for table in [
        "demo_satisfaction_summary", "demo_satisfaction_elements", "demo_satisfaction_respondents",
        "demo_prescriptions", "demo_visit_diagnoses", "demo_visit_services",
        "demo_visits", "demo_services", "demo_service_categories", "demo_users"
    ]:
        cursor.execute(f"DELETE FROM {table};")

    # =========================================================================
    # 1. GENERATE USERS (Akun Demo Aman)
    # =========================================================================
    users_data = [
        (1, "dr. Hendra Pratama (Demo)", "demo@klinikpratama.com", hashlib.md5("demo123".encode()).hexdigest()),
        (2, "Manajer Operasional (Demo)", "admin@klinikpratama.com", hashlib.md5("admin123".encode()).hexdigest()),
    ]
    cursor.executemany("INSERT INTO demo_users (id_user, nama_lengkap, email, password) VALUES (?, ?, ?, ?)", users_data)

    # =========================================================================
    # 2. GENERATE KATEGORI & MASTER LAYANAN
    # =========================================================================
    categories = [
        (1, "Poli Umum", 40_000_000.0),
        (2, "Poli Gigi & Mulut", 35_000_000.0),
        (3, "Tindakan Medis & Bedah Minor", 30_000_000.0),
        (4, "Kebidanan & KIA", 25_000_000.0),
        (5, "Laboratorium Klinis", 20_000_000.0),
        (6, "Fisioterapi & Rehab", 18_000_000.0),
    ]
    cursor.executemany("INSERT INTO demo_service_categories (id_kategoriKlinik, kategoriKlinik, target) VALUES (?, ?, ?)", categories)

    services_master = [
        # Poli Umum
        ("LAY-PU-01", "Konsultasi Dokter Umum Satuan", 1, 60_000, "Satuan"),
        ("LAY-PU-02", "Pemeriksaan Kesehatan Berkala Satuan", 1, 90_000, "Satuan"),
        ("LAY-PU-03", "Paket Medical Check Up Tahunan", 1, 450_000, "Paket"),
        
        # Poli Gigi
        ("LAY-PG-01", "Pemeriksaan & Konsultasi Gigi Satuan", 2, 75_000, "Satuan"),
        ("LAY-PG-02", "Pembersihan Karang Gigi (Scaling) Satuan", 2, 250_000, "Satuan"),
        ("LAY-PG-03", "Paket Perawatan Gigi Estetik Promo", 2, 600_000, "Paket"),

        # Tindakan Medis
        ("LAY-TM-01", "Perawatan Luka & Ganti Verban Satuan", 3, 85_000, "Satuan"),
        ("LAY-TM-02", "Injeksi Terapi Medis Satuan", 3, 50_000, "Satuan"),
        ("LAY-TM-03", "Paket Perawatan Pasca Bedah 24jam Sesi", 3, 750_000, "Paket"),

        # Kebidanan & KIA
        ("LAY-KB-01", "Pemeriksaan Kehamilan (ANC) Satuan", 4, 100_000, "Satuan"),
        ("LAY-KB-02", "Pelayanan KB & Imunisasi Anak Satuan", 4, 80_000, "Satuan"),
        ("LAY-KB-03", "Paket Perawatan Ibu & Bayi Bulan", 4, 900_000, "Paket"),

        # Laboratorium
        ("LAY-LB-01", "Pemeriksaan Darah Lengkap Satuan", 5, 85_000, "Satuan"),
        ("LAY-LB-02", "Skrining Kolesterol & Asam Urat Satuan", 5, 70_000, "Satuan"),
        ("LAY-LB-03", "Paket Skrining Metabolik Komplit Promo", 5, 380_000, "Paket"),

        # Fisioterapi
        ("LAY-FT-01", "Fisioterapi Terapi Latihan Satuan", 6, 120_000, "Satuan"),
        ("LAY-FT-02", "Paket Terapi Cedera 12x Sesi", 6, 1_200_000, "Paket"),
        ("LAY-FT-03", "Paket Rehabilitasi Stroke 30x Sesi", 6, 2_800_000, "Paket"),
    ]

    for kode, nama, cat_id, _, _ in services_master:
        cursor.execute("INSERT INTO demo_services (kode, nama_layanan, id_kategori) VALUES (?, ?, ?)", (kode, nama, cat_id))

    # Master Penyakit Fiktif (ICD-10 Populer)
    penyakit_list = [
        "Infeksi Saluran Pernapasan Akut (ISPA)",
        "Hipertensi Esensial",
        "Dispepsia / Gastritis",
        "Faringitis Akut",
        "Diabetes Melitus Tipe 2",
        "Cephalgia (Sakit Kepala Tension)",
        "Dermatitis Kontak Alergika",
        "Mialgia (Nyeri Otot)",
        "Pulpitis / Karies Gigi",
        "Gastroenteritis Akut",
        "Konjungtivitis",
        "Tonsilitis Akut"
    ]
    # Bobot probabilitas penyakit (ISPA dan Hipertensi lebih sering)
    penyakit_weights = [0.22, 0.18, 0.15, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04, 0.02, 0.02, 0.01]

    # Master Obat Farmasi Fiktif
    obat_catalog = [
        ("Paracetamol 500 mg", 15_000, (10, 20)),
        ("Amoxicillin 500 mg", 25_000, (10, 15)),
        ("Omeprazole 20 mg", 35_000, (7, 14)),
        ("Cetirizine 10 mg", 20_000, (5, 10)),
        ("Vitamin C 500 mg Tab", 15_000, (10, 30)),
        ("Antasida Doen Tab Kunyah", 12_000, (10, 20)),
        ("Ibuprofen 400 mg", 22_000, (10, 15)),
        ("Metformin 500 mg", 28_000, (15, 30)),
        ("Amlodipine 5 mg", 30_000, (15, 30)),
        ("Dexamethasone 0.5 mg", 10_000, (5, 10)),
        ("Oralit Sachet", 10_000, (5, 10)),
        ("Ciprofloxacin 500 mg", 38_000, (10, 15)),
    ]

    payment_types = ["Tunai", "Transfer Bank", "QRIS", "Asuransi Rekanan"]
    payment_weights = [0.40, 0.25, 0.25, 0.10]

    # =========================================================================
    # 3. GENERATE KUNJUNGAN & TRANSAKSI (Januari 2023 s/d Desember 2025 = 36 Bulan)
    # =========================================================================
    # Buat pool pasien fiktif (no_rm)
    total_patients_pool = 1200
    patients_pool = [f"RM-{str(i).zfill(5)}" for i in range(1, total_patients_pool + 1)]

    start_date = date(2023, 1, 1)
    end_date = date(2025, 12, 31)
    num_days = (end_date - start_date).days + 1

    # Pola jam sibuk: mayoritas kunjungan di jam 08:00 - 11:00 dan 16:00 - 19:00
    hours_dist = (
        [8]*8 + [9]*15 + [10]*18 + [11]*14 + [12]*6 +
        [13]*4 + [14]*6 + [15]*8 + [16]*16 + [17]*18 + [18]*14 + [19]*10 + [20]*4
    )

    reg_counter = 1
    pendaftaran_rows = []
    layanan_rows = []
    icd_rows = []
    resep_rows = []

    # Pelacakan pasien baru vs lama: pasien yang belum pernah berkunjung adalah Pasien Baru
    visited_patients = set()

    # Rata-rata 3 - 5 kunjungan per hari (total ~3.800 kunjungan dalam 3 tahun)
    current_date = start_date
    while current_date <= end_date:
        # Sedikit lebih banyak pada hari kerja dibanding akhir pekan
        weekday = current_date.weekday()
        if weekday < 5:
            daily_visits = random.randint(3, 6)
        else:
            daily_visits = random.randint(1, 4)

        for _ in range(daily_visits):
            no_registrasi = f"REG-{current_date.strftime('%Y%m%d')}-{str(reg_counter).zfill(4)}"
            reg_counter += 1

            # 65% kemungkinan pasien lama jika sudah ada riwayat, 35% pasien baru
            if visited_patients and random.random() < 0.65:
                patient_rm = random.choice(list(visited_patients))
            else:
                patient_rm = random.choice(patients_pool)
                visited_patients.add(patient_rm)

            hour = random.choice(hours_dist)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            waktu_daftar = f"{current_date.strftime('%Y-%m-%d')} {hour:02d}:{minute:02d}:{second:02d}"

            payment = random.choices(payment_types, weights=payment_weights)[0]

            # Pilih 1 - 2 layanan
            num_services = random.choices([1, 2], weights=[0.8, 0.2])[0]
            selected_services = random.sample(services_master, num_services)

            reg_services_total = 0.0
            for s_code, s_name, _, base_price, _ in selected_services:
                # Sedikit variasi harga (+- 5%)
                price_variation = random.uniform(0.95, 1.05)
                subtotal_layanan = round(base_price * price_variation, -3)
                reg_services_total += subtotal_layanan

                layanan_rows.append((
                    no_registrasi,
                    s_code,
                    s_name,
                    subtotal_layanan
                ))

            # Pilih 1 diagnosis ICD
            penyakit = random.choices(penyakit_list, weights=penyakit_weights)[0]
            icd_rows.append((no_registrasi, penyakit))

            # 75% kunjungan menyertakan resep farmasi (1-2 item)
            reg_resep_total = 0.0
            if random.random() < 0.75:
                num_drugs = random.choices([1, 2], weights=[0.7, 0.3])[0]
                selected_drugs = random.sample(obat_catalog, num_drugs)
                for drug_name, unit_price, qty_range in selected_drugs:
                    qty = random.randint(*qty_range)
                    subtotal_obat = float(qty * unit_price)
                    reg_resep_total += subtotal_obat

                    resep_rows.append((
                        no_registrasi,
                        drug_name,
                        qty,
                        subtotal_obat
                    ))

            total_transaksi = reg_services_total + reg_resep_total
            pendaftaran_rows.append((
                no_registrasi,
                patient_rm,
                waktu_daftar,
                total_transaksi,
                payment
            ))

        current_date += timedelta(days=1)

    # Masukkan data registrasi dan detail
    cursor.executemany("INSERT INTO demo_visits VALUES (?, ?, ?, ?, ?)", pendaftaran_rows)
    cursor.executemany("INSERT INTO demo_visit_services (kode, kodeLayanan, layanan, subtotal) VALUES (?, ?, ?, ?)", layanan_rows)
    cursor.executemany("INSERT INTO demo_visit_diagnoses (kode, penyakit) VALUES (?, ?)", icd_rows)
    cursor.executemany("INSERT INTO demo_prescriptions (kode, nama_produk, qty, subtotal) VALUES (?, ?, ?, ?)", resep_rows)

    # =========================================================================
    # 4. GENERATE SURVEI IKM (Indeks Kepuasan Masyarakat)
    # =========================================================================
    # 400 Responden disebar di tahun 2024 - 2026 agar konsisten dengan filter periode demo
    ikm_services = ["Poli Umum", "Poli Gigi", "Laboratorium", "Farmasi", "Fisioterapi", "Kebidanan & KIA"]
    ikm_weights = [0.30, 0.22, 0.18, 0.15, 0.08, 0.07]

    ikm_start = date(2025, 1, 1)
    ikm_end = date(2026, 7, 31)
    ikm_days = (ikm_end - ikm_start).days

    responden_rows = []
    total_responden_count = 420

    for i in range(1, total_responden_count + 1):
        tgl = ikm_start + timedelta(days=random.randint(0, ikm_days))
        tgl_str = tgl.strftime("%Y-%m-%d")
        layanan = random.choices(ikm_services, weights=ikm_weights)[0]
        nama_resp = f"Responden #{str(i).zfill(3)}"
        usia = random.randint(18, 65)
        jk = random.choice(["L", "P"])

        # Skor Q1-Q16 (skala 1-4)
        # Distribusi skor: mayoritas 3 (Baik) dan 4 (Sangat Baik), sedikit 2 (Kurang Baik)
        # Menghasilkan rata-rata total di kisaran 3.25 - 3.55 (IKM konversi 81 - 89, Mutu B/A)
        scores = []
        for q_idx in range(1, 17):
            # Berikan variasi realistis per unsur:
            # Q1 (Kesesuaian biaya) dan Q3 (Keramahan petugas) cenderung tinggi
            # Q2 (Kecepatan waktu tunggu) dan Q9 (Kenyamanan ruang tunggu) sedikit lebih variatif
            if q_idx in [1, 3, 7]:
                q_val = random.choices([2, 3, 4], weights=[0.05, 0.40, 0.55])[0]
            elif q_idx in [2, 9]:
                q_val = random.choices([2, 3, 4], weights=[0.15, 0.55, 0.30])[0]
            else:
                q_val = random.choices([2, 3, 4], weights=[0.08, 0.47, 0.45])[0]
            scores.append(q_val)

        responden_rows.append((
            tgl_str, layanan, nama_resp, usia, jk, *scores
        ))

    cursor.executemany("""
    INSERT INTO demo_satisfaction_respondents (
        tanggal, jenis_layanan, nama_responden, usia, jenis_kelamin,
        q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12, q13, q14, q15, q16
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, responden_rows)

    # Hitung data agregat demo_satisfaction_elements
    unsur_aggregates = []
    for q_idx in range(1, 17):
        col_name = f"q{q_idx}"
        cursor.execute(f"SELECT SUM({col_name}), AVG({col_name}) FROM demo_satisfaction_respondents;")
        tot, avg = cursor.fetchone()
        unsur_aggregates.append((f"Q{q_idx}", float(tot), round(float(avg), 2)))

    cursor.executemany("INSERT INTO demo_satisfaction_elements (unsur, total_nilai, rata_rata) VALUES (?, ?, ?)", unsur_aggregates)

    # Hitung data demo_satisfaction_summary
    cursor.execute("""
    SELECT 
        COUNT(*),
        AVG((q1+q2+q3+q4+q5+q6+q7+q8+q9+q10+q11+q12+q13+q14+q15+q16) / 16.0)
    FROM demo_satisfaction_respondents;
    """)
    n_resp, avg_global = cursor.fetchone()
    ikm_konversi = avg_global * 25.0

    if ikm_konversi >= 88.31:
        mutu, kategori = "A", "Sangat Baik"
    elif ikm_konversi >= 76.61:
        mutu, kategori = "B", "Baik"
    elif ikm_konversi >= 65.00:
        mutu, kategori = "C", "Kurang Baik"
    else:
        mutu, kategori = "D", "Tidak Baik"

    cursor.execute("""
    INSERT INTO demo_satisfaction_summary (jumlah_responden, nilai_ikm, ikm_konversi, mutu, kategori)
    VALUES (?, ?, ?, ?, ?)
    """, (n_resp, round(avg_global, 3), round(ikm_konversi, 2), mutu, kategori))

    conn.commit()
    conn.close()

    return {
        "demo_users": len(users_data),
        "demo_service_categories": len(categories),
        "demo_services": len(services_master),
        "demo_visits": len(pendaftaran_rows),
        "demo_visit_services": len(layanan_rows),
        "demo_visit_diagnoses": len(icd_rows),
        "demo_prescriptions": len(resep_rows),
        "demo_satisfaction_respondents": len(responden_rows),
        "demo_satisfaction_elements": len(unsur_aggregates),
        "demo_satisfaction_summary": 1,
    }


if __name__ == "__main__":
    db_target = os.path.join(BASE_DIR, "data", "demo_klinik.db")
    print("[INFO] Memulai pembuatan dataset sintetis demo...")
    stats = generate_synthetic_dataset(db_target, seed=42)
    print("[SUCCESS] Berhasil membuat database demo di:", db_target)
    for table, count in stats.items():
        print(f"   - {table}: {count:,} baris")
