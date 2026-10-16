def get_pendapatan_bulanan_query():
    """
    Query Tren Pendapatan Bulanan (Diperbarui).
    Sumber: demo_visits
    Kolom: waktu_daftar, total
    """
    return """
    SELECT 
        YEAR(waktu_daftar) as tahun,
        MONTH(waktu_daftar) as bulan,
        SUM(total) as total_pendapatan
    FROM demo_visits
    WHERE total IS NOT NULL
    GROUP BY YEAR(waktu_daftar), MONTH(waktu_daftar)
    ORDER BY tahun ASC, bulan ASC;
    """

def get_growth_drivers_query():
    """
    Query Analisis Pertumbuhan.
    PENTING: Gunakan %%Y dan %%m agar Python tidak error membaca simbol persen.
    """
    return """
    SELECT 
        DATE_FORMAT(waktu_daftar, '%%Y-%%m') as periode,
        COUNT(no_registrasi) as jumlah_kunjungan,
        SUM(total) as total_pendapatan
    FROM demo_visits
    WHERE total IS NOT NULL
    GROUP BY periode
    ORDER BY periode ASC;
    """

def get_trend_kontribusi_query():
    """
    Mengelompokkan pendapatan berdasarkan tipe layanan (Paket vs Satuan)
    menggunakan pencarian kata kunci (Regex) langsung di SQL.
    """
    return """
    SELECT 
        DATE_FORMAT(p.waktu_daftar, '%%Y-%%m') as periode,
        CASE 
            -- Jika nama layanan mengandung kata kunci ini, anggap sebagai 'Paket'
            WHEN l.layanan REGEXP 'paket|sesi|promo|12x|30x|24jam|bulan' THEN 'Paket'
            ELSE 'Satuan'
        END as tipe_layanan,
        SUM(l.subtotal) as total_pendapatan
    FROM demo_visit_services l
    JOIN demo_visits p ON l.kode = p.no_registrasi
    WHERE l.subtotal IS NOT NULL
    GROUP BY periode, tipe_layanan
    ORDER BY periode ASC;
    """

def get_top_10_layanan_query():
    """
    Mengambil Top 10 Layanan.
    Update: Menggunakan kolom 'subtotal' sesuai konfirmasi user.
    """
    return """
    SELECT 
        layanan AS nama_layanan, 
        CASE 
            WHEN layanan LIKE '%%Paket%%' THEN 'Paket'
            ELSE 'Satuan'
        END as kategori,
        SUM(subtotal) as total_pendapatan -- SUDAH DIPERBAIKI (total -> subtotal)
    FROM demo_visit_services
    GROUP BY layanan, kategori
    ORDER BY total_pendapatan DESC;
    """

def get_pasien_baru_lama_query():
    """
    Menghitung jumlah pasien Baru vs Lama per bulan.
    Logika: Pasien Baru adalah jika bulan kunjungan = bulan kunjungan pertama kali seumur hidup.
    """
    return """
    WITH FirstVisit AS (
        SELECT 
            no_rm, 
            MIN(waktu_daftar) as first_visit_date
        FROM demo_visits
        GROUP BY no_rm
    )
    SELECT 
        DATE_FORMAT(p.waktu_daftar, '%%Y-%%m') as bulan,
        CASE 
            WHEN DATE_FORMAT(p.waktu_daftar, '%%Y-%%m') = DATE_FORMAT(fv.first_visit_date, '%%Y-%%m') THEN 'Pasien Baru'
            ELSE 'Pasien Lama'
        END as status_pasien,
        COUNT(DISTINCT p.no_rm) as jumlah_pasien
    FROM demo_visits p
    JOIN FirstVisit fv ON p.no_rm = fv.no_rm
    GROUP BY bulan, status_pasien
    ORDER BY bulan ASC;
    """

def get_heatmap_kunjungan_query():
    """
    Mengambil data dasar untuk Heatmap Bulan vs Jam.
    Kita ambil Tahun, Bulan (Angka), dan Jam.
    """
    return """
    SELECT 
        YEAR(waktu_daftar) as tahun,
        MONTH(waktu_daftar) as bulan,
        HOUR(waktu_daftar) as jam,
        COUNT(no_registrasi) as jumlah_kunjungan
    FROM demo_visits
    GROUP BY tahun, bulan, jam
    ORDER BY tahun, bulan, jam;
    """

def get_rata_rata_kunjungan_query():
    """
    Menghitung rasio total kunjungan dibagi jumlah pasien unik per bulan.
    """
    return """
    SELECT 
        DATE_FORMAT(waktu_daftar, '%%Y-%%m') as bulan,
        COUNT(no_registrasi) as total_kunjungan,
        COUNT(DISTINCT no_rm) as total_pasien_unik
    FROM demo_visits
    GROUP BY bulan
    ORDER BY bulan ASC;
    """

def get_top_penyakit_query():
    return """
    SELECT 
        p.waktu_daftar,
        i.penyakit AS nama_penyakit  -- PENTING: Tambahkan 'AS nama_penyakit' di sini!
    FROM demo_visit_diagnoses i
    JOIN demo_visits p ON i.kode = p.no_registrasi
    WHERE i.penyakit IS NOT NULL
    ORDER BY p.waktu_daftar DESC;
    """
def get_top_produk_query():
    """
    Mengambil data QTY (untuk Stok) dan SUBTOTAL (untuk Omzet).
    """
    return """
    SELECT 
        DATE(p.waktu_daftar) as tanggal,
        r.nama_produk as nama_obat,
        SUM(r.qty) as total_terjual,      -- Untuk Analisis Stok
        SUM(r.subtotal) as total_pendapatan -- Untuk Analisis Omzet
    FROM demo_prescriptions r
    JOIN demo_visits p ON r.kode = p.no_registrasi
    GROUP BY tanggal, r.nama_produk
    ORDER BY total_terjual DESC;
    """

def get_realisasi_pendapatan_per_kategori_query():
    """
    Menghitung TOTAL PENDAPATAN (Rp) per bulan per kategori.
    Update: Mengambil TARGET dari database (demo_service_categories).
    """
    return """
    SELECT 
        DATE_FORMAT(p.waktu_daftar, '%%Y-%%m') as bulan,
        
        -- Ambil Nama Kategori
        COALESCE(k.kategoriKlinik, 'Lainnya') as kategori,
        
        -- Ambil Target Bulanan dari DB (Jika null anggap 0)
        COALESCE(k.target, 0) as target_bulanan,
        
        SUM(l.subtotal) as aktual_pendapatan
        
    FROM demo_visit_services l
    
    -- JOIN ke Transaksi
    JOIN demo_visits p ON l.kode = p.no_registrasi
    
    -- JOIN ke Master Layanan
    LEFT JOIN demo_services m ON l.kodeLayanan = m.kode
    
    -- JOIN ke Master Kategori (Ambil Target di sini)
    LEFT JOIN demo_service_categories k ON m.id_kategori = k.id_kategoriKlinik
    
    WHERE p.waktu_daftar IS NOT NULL
    
    GROUP BY bulan, kategori, target_bulanan
    ORDER BY bulan ASC;
    """

# ==========================================================
# IKM (Indeks Kepuasan Masyarakat)
# ==========================================================

def get_ikm_responden_query():
    """
    Mengambil seluruh data responden IKM.
    """
    return """
    SELECT *
    FROM demo_satisfaction_respondents
    ORDER BY tanggal;
    """


def get_ikm_unsur_query():
    """
    Mengambil nilai setiap unsur pelayanan (Q1-Q16).
    """
    return """
    SELECT
        unsur,
        total_nilai,
        rata_rata
    FROM demo_satisfaction_elements
    ORDER BY CAST(SUBSTRING(unsur,2) AS UNSIGNED);
    """


def get_ikm_summary_query():
    """
    Mengambil ringkasan hasil IKM.
    """
    return """
    SELECT
        jumlah_responden,
        nilai_ikm,
        ikm_konversi,
        mutu,
        kategori
    FROM demo_satisfaction_summary
    ORDER BY id DESC
    LIMIT 1;
    """


def get_ikm_layanan_query():
    """
    Menghitung rata-rata IKM setiap jenis layanan.
    Tidak perlu membuat tabel baru.
    """
    return """
    SELECT
        jenis_layanan,
        ROUND(AVG(
            (Q1+Q2+Q3+Q4+Q5+Q6+Q7+Q8+
             Q9+Q10+Q11+Q12+Q13+Q14+Q15+Q16)
            /16*25
        ),2) AS ikm
    FROM demo_satisfaction_respondents
    GROUP BY jenis_layanan
    ORDER BY ikm DESC;
    """

def get_ikm_ranking_query():
    """
    Ranking unsur pelayanan berdasarkan nilai rata-rata.
    """
    return """
    SELECT
        unsur,
        total_nilai,
        rata_rata
    FROM demo_satisfaction_elements
    ORDER BY rata_rata DESC;
    """

def get_ikm_trend_query():
    """
    Trend nilai IKM per bulan.
    """
    return """
    SELECT
        DATE_FORMAT(tanggal,'%%Y-%%m') AS bulan,
        ROUND(
            AVG(
                (Q1+Q2+Q3+Q4+Q5+Q6+Q7+Q8+
                 Q9+Q10+Q11+Q12+Q13+Q14+Q15+Q16)
                /16*25
            ),
        2) AS ikm
    FROM demo_satisfaction_respondents
    GROUP BY bulan
    ORDER BY bulan;
    """

# def get_metode_pembayaran_query():
#     return """
#     SELECT 
#         payment_type AS metode_bayar, 
#         COUNT(no_registrasi) as total_transaksi,
#         SUM(total) as total_pendapatan
#     FROM demo_visits
#     WHERE total IS NOT NULL
#     GROUP BY payment_type;
#     """
