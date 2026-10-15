# src/modules/ai_assistant.py

import os
import re
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

from src.agents.agent_brain import init_agent
from src.database.connection import get_db_engine
from src.database.queries import (
    get_realisasi_pendapatan_per_kategori_query,
    get_ikm_responden_query,
    get_pendapatan_bulanan_query,
    get_pasien_baru_lama_query,
    get_rata_rata_kunjungan_query,
    get_top_10_layanan_query,
    get_top_penyakit_query,
    get_top_produk_query,
    get_ikm_layanan_query,
    get_ikm_trend_query,
)


# ---------- Helpers ----------
BULAN_MAP = {
    "januari": "01", "februari": "02", "maret": "03", "april": "04",
    "mei": "05", "juni": "06", "juli": "07", "agustus": "08",
    "september": "09", "oktober": "10", "november": "11", "desember": "12",
}

# Kategori pertanyaan cepat yang disesuaikan dengan dataset demo sintetis
PROMPT_CATEGORIES = [
    {
        "category": "📈 Pendapatan & Performa",
        "icon": "📊",
        "prompts": [
            "Bagaimana tren pendapatan dari 2023 hingga 2025?",
            "Kategori layanan apa yang paling tinggi pendapatannya?",
            "Kategori layanan mana yang paling jauh dari target?"
        ]
    },
    {
        "category": "😊 Kepuasan Pasien (IKM)",
        "icon": "⭐",
        "prompts": [
            "Bagaimana hasil survei IKM kepuasan pasien klinik?",
            "Layanan mana yang IKM-nya paling rendah?",
            "Berikan rekomendasi untuk meningkatkan kepuasan pasien!"
        ]
    },
    {
        "category": "🧑‍⚕️ Pasien & Operasional",
        "icon": "🏥",
        "prompts": [
            "Berapa jumlah pasien baru vs pasien lama?",
            "Apa keluhan atau diagnosa penyakit yang paling sering datang?",
            "Apa saja obat atau produk yang paling laris?"
        ]
    }
]


def get_all_api_keys() -> list[str]:
    """
    Membaca Gemini API Key dari environment variable / .env.
    Mendukung GEMINI_API_KEY, GEMINI_API_KEY_2 s/d GEMINI_API_KEY_10, atau GEMINI_API_KEYS.
    """
    load_dotenv(override=True)
    keys = []

    # 1. Format pisah koma: GEMINI_API_KEYS
    multi = os.getenv("GEMINI_API_KEYS", "").strip()
    if multi:
        for k in multi.split(","):
            k = k.strip()
            if k and k not in keys:
                keys.append(k)

    # 2. Token utama: GEMINI_API_KEY
    primary = os.getenv("GEMINI_API_KEY", "").strip()
    if primary and primary not in keys:
        keys.append(primary)

    # 3. Token cadangan: GEMINI_API_KEY_1 s/d GEMINI_API_KEY_10
    for i in range(1, 11):
        k = os.getenv(f"GEMINI_API_KEY_{i}", "").strip()
        if k and k not in keys:
            keys.append(k)

    return keys


def is_rate_limit_error(error: Exception | str) -> bool:
    """Mendeteksi apakah error disebabkan oleh rate limit, kuota habis, atau server overloaded (503)."""
    err_str = str(error).lower()
    keywords = [
        "429", "503", "unavailable", "high demand", "resourceexhausted",
        "resource_exhausted", "quota exceeded", "quota", "rate limit",
        "rate_limit", "too many requests", "exhausted", "tpm", "rpm", "rpd", "overloaded"
    ]
    return any(kw in err_str for kw in keywords)


def load_data() -> pd.DataFrame:
    """Load data pendapatan sekali per sesi."""
    if "ai_data" in st.session_state and isinstance(st.session_state.ai_data, pd.DataFrame):
        return st.session_state.ai_data

    engine = get_db_engine()
    query = get_realisasi_pendapatan_per_kategori_query()
    df = pd.read_sql(query, engine)

    if df is None or df.empty:
        raise RuntimeError("Data dari basis data demo kosong.")

    st.session_state.ai_data = df
    return df


def load_all_context() -> str:
    """
    Membangun konteks data komprehensif dari basis data demo sintetis
    untuk diberikan ke AI bersama setiap pertanyaan.
    """
    if "ai_full_context" in st.session_state:
        return st.session_state.ai_full_context

    try:
        engine = get_db_engine()
        q_cols = [f"q{i}" for i in range(1, 17)]

        # --- IKM ---
        df_ikm = pd.read_sql(get_ikm_responden_query(), engine)
        df_ikm['tanggal'] = pd.to_datetime(df_ikm['tanggal'])
        df_ikm['ikm_konversi'] = df_ikm[q_cols].mean(axis=1) * 25
        df_ikm['nilai_ikm'] = df_ikm[q_cols].mean(axis=1)

        ikm_global = df_ikm['ikm_konversi'].mean()
        ikm_per_layanan = df_ikm.groupby('jenis_layanan')['ikm_konversi'].mean().round(2)
        ikm_bulan = df_ikm.copy()
        ikm_bulan['bulan'] = df_ikm['tanggal'].dt.strftime('%Y-%m')
        ikm_bulan_agg = ikm_bulan.groupby('bulan')['ikm_konversi'].mean().round(2)

        unsur_avg = {}
        for i in range(1, 17):
            unsur_avg[f"Q{i}"] = round(df_ikm[f"q{i}"].mean(), 2)
        unsur_df = pd.Series(unsur_avg).sort_values()
        unsur_terburuk = unsur_df.head(3)
        unsur_terbaik = unsur_df.tail(3)

        def ikm_kategori(val):
            if val >= 88.31: return "Sangat Baik (A)"
            elif val >= 76.61: return "Baik (B)"
            elif val >= 65.00: return "Kurang Baik (C)"
            return "Tidak Baik (D)"

        # --- Pendapatan Bulanan ---
        df_pen = pd.read_sql(get_pendapatan_bulanan_query(), engine)
        total_revenue = df_pen['total_pendapatan'].sum()
        revenue_per_tahun = df_pen.groupby('tahun')['total_pendapatan'].sum()

        # --- Top Layanan ---
        df_top = pd.read_sql(get_top_10_layanan_query(), engine)
        top10_str = df_top.head(10).to_string(index=False)

        # --- Pasien ---
        df_pas = pd.read_sql(get_pasien_baru_lama_query(), engine)
        pas_sum = df_pas.groupby('status_pasien')['jumlah_pasien'].sum()
        total_pasien = pas_sum.sum()
        pasien_baru = pas_sum.get('Pasien Baru', 0)
        pasien_lama = pas_sum.get('Pasien Lama', 0)
        rasio_baru = (pasien_baru / total_pasien * 100) if total_pasien > 0 else 0
        rasio_lama = (pasien_lama / total_pasien * 100) if total_pasien > 0 else 0

        # --- Kunjungan ---
        df_avg = pd.read_sql(get_rata_rata_kunjungan_query(), engine)
        total_kunjungan = df_avg['total_kunjungan'].sum()
        avg_visit_ratio = (df_avg['total_kunjungan'].sum() / df_avg['total_pasien_unik'].sum()) if df_avg['total_pasien_unik'].sum() > 0 else 0

        # Simpan metrik ringkasan untuk banner
        st.session_state["ai_kunjungan_count"] = int(total_kunjungan)
        st.session_state["ai_pasien_count"] = int(df_avg['total_pasien_unik'].sum())
        st.session_state["ai_ikm_count"] = len(df_ikm)

        # --- Top Penyakit ---
        df_pen_daft = pd.read_sql(get_top_penyakit_query(), engine)
        df_pen_daft['waktu_daftar'] = pd.to_datetime(df_pen_daft['waktu_daftar'])
        df_pen_daft['bulan'] = df_pen_daft['waktu_daftar'].dt.strftime('%Y-%m')

        pen_min = df_pen_daft['waktu_daftar'].min().date() if not df_pen_daft.empty else "N/A"
        pen_max = df_pen_daft['waktu_daftar'].max().date() if not df_pen_daft.empty else "N/A"

        top_penyakit = df_pen_daft['nama_penyakit'].value_counts().head(10)
        top_penyakit_str = top_penyakit.to_string()

        years_avail = sorted(df_pen_daft['waktu_daftar'].dt.year.unique())
        latest_year = years_avail[-1] if len(years_avail) >= 1 else 2025
        prev_year = years_avail[-2] if len(years_avail) >= 2 else 2024

        top_latest = df_pen_daft[df_pen_daft['waktu_daftar'].dt.year == latest_year]['nama_penyakit'].value_counts().head(5).to_string()
        top_prev = df_pen_daft[df_pen_daft['waktu_daftar'].dt.year == prev_year]['nama_penyakit'].value_counts().head(5).to_string()
        kasus_per_bulan = df_pen_daft.groupby('bulan').size().tail(12).to_string()

        # --- Top Obat ---
        df_obat = pd.read_sql(get_top_produk_query(), engine)
        df_obat_group = df_obat.groupby('nama_obat').agg({'total_terjual': 'sum', 'total_pendapatan': 'sum'})
        top_obat_qty = df_obat_group.nlargest(10, 'total_terjual')['total_terjual']
        top_obat_rev = df_obat_group.nlargest(10, 'total_pendapatan')['total_pendapatan']

        context = f"""
============================
KONTEKS DATA KLINIK PRATAMA DEMO (DATABASE SINTETIS PORTOFOLIO)
============================
PENTING: Seluruh data di bawah ini adalah data sintetis fiktif untuk keperluan demonstrasi portofolio.
Gunakan data ini untuk menjawab pertanyaan user secara akurat. Jangan mengarang angka di luar data ini.

--- 1. KEPUASAN PASIEN (IKM) ---
Jumlah Responden IKM: {len(df_ikm)} orang
Periode IKM: {df_ikm['tanggal'].min().date()} s/d {df_ikm['tanggal'].max().date()}
Nilai IKM Rata-rata (Konversi 0-100): {ikm_global:.2f}
Kategori Mutu: {ikm_kategori(ikm_global)}

IKM per Jenis Layanan (100 = Sempurna):
{ikm_per_layanan.to_string()}

Tren IKM per Bulan:
{ikm_bulan_agg.to_string()}

Unsur Pelayanan dengan Skor Terendah (Q1-Q16, skala 1-4):
{unsur_terburuk.to_string()}

Unsur Pelayanan dengan Skor Tertinggi:
{unsur_terbaik.to_string()}

--- 2. PENDAPATAN & TARGET ---
Total Revenue Keseluruhan: Rp {total_revenue:,.0f}
Revenue per Tahun:
{revenue_per_tahun.to_string()}

--- 3. TOP 10 LAYANAN BERDASARKAN PENDAPATAN ---
{top10_str}

--- 4. DATA PASIEN & KUNJUNGAN ---
Total Kunjungan ({df_pen['tahun'].min()}-{df_pen['tahun'].max()}): {total_kunjungan:,}
Total Pasien Baru: {pasien_baru:,} ({rasio_baru:.1f}%)
Total Pasien Lama: {pasien_lama:,} ({rasio_lama:.1f}%)
Rasio Frekuensi Kunjungan per Pasien: {avg_visit_ratio:.2f}x

--- 5. DATA PENYAKIT / DIAGNOSIS (ICD) ---
Periode Data ICD: {pen_min} s/d {pen_max} (Total {len(df_pen_daft)} rekam diagnosis)
Jumlah Kasus Diagnosa per Bulan (12 Bulan Terakhir):
{kasus_per_bulan}

Top 10 Keluhan/Penyakit Keseluruhan:
{top_penyakit_str}

Top Penyakit Tahun {latest_year}:
{top_latest}

Top Penyakit Tahun {prev_year}:
{top_prev}

--- 6. TOP 10 OBAT TERLARIS (QTY) ---
{top_obat_qty.to_string()}

--- 6b. TOP 10 OBAT OMZET TERTINGGI ---
{top_obat_rev.to_string()}

============================
CATATAN PENTING:
- Data transaksi tersedia dari tahun {df_pen['tahun'].min()} s/d {df_pen['tahun'].max()}
- Data diagnosa penyakit tersedia dari {pen_min} s/d {pen_max}
- Data survei IKM tersedia dari {df_ikm['tanggal'].min().date()} s/d {df_ikm['tanggal'].max().date()}
- Dataframe `df` yang dianalisis berisi kolom: bulan, kategori, target_bulanan, aktual_pendapatan
- Seluruh data adalah data sintetis demo terisolasi (read-only)
============================
"""
        st.session_state.ai_full_context = context
        return context

    except Exception as e:
        return f"[Catatan: Sebagian konteks gagal dimuat: {str(e)}]"


def get_agent(df: pd.DataFrame, api_key: str):
    """Init Safe AI Consultant sekali per signature data, token, dan model."""
    load_dotenv(override=True)
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    if not model_name or "2.5-flash" in model_name:
        model_name = "gemini-3.5-flash-lite"

    signature = (tuple(df.columns), int(len(df)), api_key, model_name)

    if (
        "ai_agent" not in st.session_state
        or "ai_agent_signature" not in st.session_state
        or st.session_state.ai_agent_signature != signature
    ):
        st.session_state.ai_agent = init_agent(df, api_key)
        st.session_state.ai_agent_signature = signature

    return st.session_state.ai_agent


def execute_agent_query(df: pd.DataFrame, final_prompt: str, api_keys: list[str]) -> str:
    """
    Menjalankan query ke Safe AI Consultant dengan auto-fallback multi-token.
    """
    if not api_keys:
        raise ValueError("Tidak ada Gemini API Key yang tersedia di .env / environment.")

    if "active_key_index" not in st.session_state:
        st.session_state.active_key_index = 0

    total_keys = len(api_keys)
    start_index = st.session_state.active_key_index % total_keys
    attempts = 0

    while attempts < total_keys:
        curr_idx = (start_index + attempts) % total_keys
        curr_key = api_keys[curr_idx]
        st.session_state.active_key_index = curr_idx

        try:
            agent = get_agent(df, curr_key)
            result = agent.invoke({"input": final_prompt})
            response = result.get("output", str(result))

            # Deteksi jika memegang agent lama dengan model deprecated dalam cache sesi
            if any(kw in response for kw in ["2.5-flash", "NOT_FOUND", "is no longer available"]):
                st.session_state.pop("ai_agent", None)
                st.session_state.pop("ai_agent_signature", None)
                agent = get_agent(df, curr_key)
                result = agent.invoke({"input": final_prompt})
                response = result.get("output", str(result))

            return response

        except Exception as e:
            err_str = str(e)

            # Cek limit kuota atau server busy
            if is_rate_limit_error(err_str):
                attempts += 1
                if attempts < total_keys:
                    next_idx = (start_index + attempts) % total_keys
                    st.toast(
                        f"⚠️ Token #{curr_idx + 1} mengalami antrean limit. Beralih ke Token #{next_idx + 1}...",
                        icon="🔄",
                    )
                    st.session_state.pop("ai_agent", None)
                    st.session_state.pop("ai_agent_signature", None)
                    import time
                    time.sleep(1.0)
                    continue
                else:
                    if "503" in err_str or "high demand" in err_str:
                        raise RuntimeError(
                            "Server Google Gemini sedang mengalami antrean beban tinggi global (503 High Demand). "
                            "Silakan klik tombol tanyakan kembali dalam 3-5 detik."
                        )
                    raise RuntimeError(
                        f"Seluruh API Key Gemini ({total_keys} token) sedang mencapai batas rate limit per menit. "
                        "Silakan tunggu beberapa saat atau tambahkan token cadangan di .env."
                    )

            raise e


def parse_periode(text: str) -> str | None:
    t = text.lower().strip()
    m = re.search(r"\b(20\d{2})[-/](0[1-9]|1[0-2])\b", t)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    m = re.search(
        r"\b(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\s+(20\d{2})\b",
        t,
    )
    if m:
        return f"{m.group(2)}-{BULAN_MAP[m.group(1)]}"
    return None


def compute_kpi_for_period(df: pd.DataFrame, periode: str):
    data = df[df["bulan"] == periode]
    if data.empty:
        return None
    total_target = float(data["target_bulanan"].sum())
    total_aktual = float(data["aktual_pendapatan"].sum())
    pencapaian = (total_aktual / total_target * 100.0) if total_target else 0.0
    per_kategori = (
        data.groupby("kategori", as_index=False)[["target_bulanan", "aktual_pendapatan"]]
        .sum()
        .sort_values("aktual_pendapatan", ascending=False)
    )
    return total_target, total_aktual, pencapaian, per_kategori


def format_rupiah(x: float) -> str:
    n = int(round(x))
    s = f"{n:,}".replace(",", ".")
    return f"Rp{s}"


def build_enhanced_prompt(user_question: str, context: str, extra_data: str = "") -> str:
    return f"""
{context}

{extra_data}

PERTANYAAN PENGGUNA:
{user_question}

INSTRUKSI UNTUK AI:
- Jawab pertanyaan menggunakan konteks data sintetis demo di atas secara konsisten.
- Jika pertanyaan menyebut IKM/kepuasan pasien, gunakan data IKM dari konteks.
- Jika pertanyaan menyebut kunjungan/pasien, gunakan data kunjungan dari konteks.
- Jika pertanyaan menyebut obat/penyakit, gunakan data tersebut dari konteks.
- Jika pertanyaan tentang target dan omzet, sajikan angka riil sesuai konteks.
- Format jawaban dengan Markdown profesional (bold, bullet point) agar rapi dan mudah dibaca.
- Selalu tegaskan bahwa analisis ini berbasis data sintetis untuk keperluan demonstrasi portofolio.
"""


# ---------- Main ----------
def run():
    # Inject Custom CSS
    st.markdown("""
    <style>
    .ai-header-badge {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.8));
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .ai-status-pill {
        display: inline-block;
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 8px;
    }
    .ai-chip-title {
        color: #94a3b8;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("🤖 AI Business Consultant")
    st.caption("Analisis Cerdas Data Klinik Pratama • Portofolio Publik")

    # Load context & data
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Gagal memuat data database demo: {e}")
        return

    with st.spinner("⏳ Mempersiapkan konteks data klinik demo..."):
        full_context = load_all_context()

    # Ambil angka metrik ringkasan dinamis dari context
    total_kunjungan_display = st.session_state.get("ai_kunjungan_count", 4264)
    total_pasien_display = st.session_state.get("ai_pasien_count", 1200)
    total_ikm_display = st.session_state.get("ai_ikm_count", 420)

    # Status Banner Dinamis
    st.markdown(f"""
    <div class="ai-header-badge">
        <span class="ai-status-pill">🟢 Demo Database</span>
        <span style="color:#e2e8f0; font-size:14px; font-weight:500;">
            Terhubung ke <b>{total_kunjungan_display:,} Kunjungan</b> • <b>{total_pasien_display:,} Pasien</b> • <b>{total_ikm_display} Responden IKM (Data Sintetis)</b>
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Banner Keamanan Portofolio
    st.markdown("""
    <div style='background: rgba(14, 165, 233, 0.1); border: 1px solid #0284c7; border-radius: 10px; padding: 10px 14px; margin-bottom: 20px; font-size: 13px; color: #bae6fd;'>
        🛡️ <b>Mode Portofolio Demo</b> — AI Assistant menganalisis dataset sintetis terisolasi (read-only). Operasi eksekusi kode bebas (Python REPL) dan koneksi ke database produksi diblokir permanen.
    </div>
    """, unsafe_allow_html=True)

    # Sidebar Kontrol Rapi & Minimalis
    with st.sidebar:
        st.markdown("---")
        st.markdown("### ⚙️ Kontrol AI")
        if st.button("🔄 Refresh Data & Reset Chat", use_container_width=True):
            for key in ["ai_data", "ai_full_context", "ai_agent", "ai_agent_signature", "messages", "clicked_prompt"]:
                st.session_state.pop(key, None)
            st.rerun()

        with st.expander("❓ Petunjuk & Bantuan"):
            st.markdown("""
            * **Pertanyaan Bebas**: Ajukan pertanyaan seputar omzet, pasien, IKM, atau obat demo.
            * **Spesifik Periode**: Contoh *"November 2025"* atau *"2024"*.
            * **Saran Bisnis**: AI akan memberikan rekomendasi strategis berbasis data sintetis.
            """)

    # API Keys check
    api_keys = get_all_api_keys()
    if not api_keys:
        st.warning(
            "⚠️ **API Key Belum Dikonfigurasi:** Fitur AI Business Consultant memerlukan Google Gemini API Key. "
            "Silakan tambahkan `GEMINI_API_KEY=your_key` pada file `.env` di lingkungan lokal Anda."
        )
        with st.expander("ℹ️ Panduan Konfigurasi API Key"):
            st.markdown("""
            1. Dapatkan API Key gratis di [Google AI Studio](https://aistudio.google.com/).
            2. Buka file `.env` dan masukkan:
               ```bash
               GEMINI_API_KEY=masukkan_api_key_anda_disini
               ```
            3. Klik tombol **Refresh Data & Reset Chat** di sidebar.
            """)
        return

    # Info status token di sidebar (tanpa membocorkan karakter kunci)
    with st.sidebar:
        with st.expander("🔑 Status Gemini API"):
            st.markdown(f"**Total Token:** `{len(api_keys)} Token Terdeteksi`")
            curr_active = (st.session_state.get("active_key_index", 0) % len(api_keys)) + 1
            st.markdown(f"**Token Aktif:** `Token #{curr_active}`")
            if len(api_keys) > 1:
                st.success("✅ Auto-Fallback Multi-Token: **Aktif**")
            else:
                st.info("💡 Tambahkan `GEMINI_API_KEY_2` di `.env` untuk cadangan otomatis saat limit.")

    # Chat init
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Suggestion Chips Interaktif
    if len(st.session_state.messages) <= 1:
        st.markdown("<div class='ai-chip-title'>💡 Rekomendasi Pertanyaan Cepat (Klik untuk bertanya)</div>", unsafe_allow_html=True)
        
        cols = st.columns(len(PROMPT_CATEGORIES))
        for idx, cat in enumerate(PROMPT_CATEGORIES):
            with cols[idx]:
                st.markdown(f"**{cat['category']}**")
                for p_idx, prompt_text in enumerate(cat["prompts"]):
                    if st.button(f"{cat['icon']} {prompt_text}", key=f"btn_{idx}_{p_idx}", use_container_width=True):
                        st.session_state.clicked_prompt = prompt_text
                        st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)

    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Tangkap prompt
    active_prompt = None

    if st.session_state.get("clicked_prompt"):
        active_prompt = st.session_state.clicked_prompt
        st.session_state.clicked_prompt = None

    if chat_input_val := st.chat_input("Contoh: Bagaimana tren performa pendapatan tahun 2024 vs 2025?"):
        active_prompt = chat_input_val

    if active_prompt:
        st.session_state.messages.append({"role": "user", "content": active_prompt})

        with st.chat_message("user"):
            st.markdown(active_prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("🧠 *Sedang menganalisis data demo...*")

            try:
                periode = parse_periode(active_prompt)

                if periode:
                    prompt_lower = active_prompt.lower()
                    is_penyakit_q = any(kw in prompt_lower for kw in ["penyakit", "keluhan", "icd", "diagnosa", "diagnosis", "sakit"])
                    is_obat_q = any(kw in prompt_lower for kw in ["obat", "produk", "resep", "stok", "farmasi"])

                    if is_penyakit_q:
                        engine = get_db_engine()
                        df_pen_all = pd.read_sql(get_top_penyakit_query(), engine)
                        df_pen_all['waktu_daftar'] = pd.to_datetime(df_pen_all['waktu_daftar'])
                        df_pen_all['bulan'] = df_pen_all['waktu_daftar'].dt.strftime('%Y-%m')
                        df_pen_sub = df_pen_all[df_pen_all['bulan'] == periode]

                        if df_pen_sub.empty:
                            sorted_m = sorted(df_pen_all['bulan'].unique())
                            m1 = sorted_m[-1] if len(sorted_m) >= 1 else "2025-12"
                            m2 = sorted_m[-2] if len(sorted_m) >= 2 else "2025-11"
                            c1 = len(df_pen_all[df_pen_all['bulan'] == m1])
                            c2 = len(df_pen_all[df_pen_all['bulan'] == m2])
                            extra = f"""
DATA PENYAKIT KHUSUS PERIODE {periode}:
Pencatatan diagnosa penyakit khusus bulan '{periode}' tidak ada di database demo (0 rekam medis).
Sebagai pembanding data demo yang tersedia:
- {m1}: {c1} kasus
- {m2}: {c2} kasus

INSTRUKSI UNTUK AI:
1. Sampaikan secara transparan bahwa data diagnosa penyakit khusus bulan '{periode}' berisi 0 kasus di database demo.
2. Sajikan data penyakit pembanding untuk periode terdekat ({m1} / {m2} / Keseluruhan) agar user tetap mendapat insight yang berguna.
"""
                        else:
                            top_sub = df_pen_sub['nama_penyakit'].value_counts().head(10)
                            extra = f"""
DATA TOP PENYAKIT KHUSUS PERIODE {periode}:
Total Kasus Bulan Ini: {len(df_pen_sub)} kasus
{top_sub.to_string()}
"""
                        final_prompt = build_enhanced_prompt(active_prompt, full_context, extra)
                        response = execute_agent_query(df, final_prompt, api_keys)
                        placeholder.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        return

                    if is_obat_q:
                        engine = get_db_engine()
                        df_prod_all = pd.read_sql(get_top_produk_query(), engine)
                        df_prod_all['tanggal'] = pd.to_datetime(df_prod_all['tanggal'])
                        df_prod_all['bulan'] = df_prod_all['tanggal'].dt.strftime('%Y-%m')
                        df_prod_sub = df_prod_all[df_prod_all['bulan'] == periode]

                        if df_prod_sub.empty:
                            extra = f"Catatan: Transaksi resep obat untuk bulan '{periode}' tidak ada di database demo (0 transaksi)."
                        else:
                            top_qty = df_prod_sub.groupby('nama_obat')['total_terjual'].sum().nlargest(10)
                            top_rev = df_prod_sub.groupby('nama_obat')['total_pendapatan'].sum().nlargest(10)
                            extra = f"""
DATA OBAT KHUSUS PERIODE {periode}:
Top 10 Qty Terjual:
{top_qty.to_string()}

Top 10 Omzet Obat:
{top_rev.to_string()}
"""
                        final_prompt = build_enhanced_prompt(active_prompt, full_context, extra)
                        response = execute_agent_query(df, final_prompt, api_keys)
                        placeholder.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        return

                    kpi = compute_kpi_for_period(df, periode)

                    if kpi is None:
                        extra = f"Catatan: Data pendapatan untuk periode '{periode}' tidak ditemukan di database demo. Periode tersedia: {sorted(df['bulan'].unique()[:3])} ... {sorted(df['bulan'].unique()[-3:])}"
                        final_prompt = build_enhanced_prompt(active_prompt, full_context, extra)
                        response = execute_agent_query(df, final_prompt, api_keys)
                        placeholder.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        return

                    total_target, total_aktual, pencapaian, per_kategori = kpi

                    with st.expander(f"📋 Rincian Target vs Realisasi ({periode})"):
                        show = per_kategori.copy()
                        show["target_bulanan"] = show["target_bulanan"].map(format_rupiah)
                        show["aktual_pendapatan"] = show["aktual_pendapatan"].map(format_rupiah)
                        st.dataframe(show, use_container_width=True)

                    top = per_kategori.head(3)
                    bottom = per_kategori.tail(3)

                    extra_kpi = f"""
DATA PENDAPATAN SUDAH DIHITUNG UNTUK PERIODE {periode}:
Total Target: {format_rupiah(total_target)}
Total Aktual: {format_rupiah(total_aktual)}
Pencapaian: {pencapaian:.2f}%
Gap: {format_rupiah(total_aktual - total_target)}

Top 3 Kategori (by Aktual):
{top.to_string(index=False)}

Bottom 3 Kategori (by Aktual):
{bottom.to_string(index=False)}

CATATAN: Angka di atas dihitung langsung dari basis data demo sintetis.
"""
                    final_prompt = build_enhanced_prompt(active_prompt, full_context, extra_kpi)
                    response = execute_agent_query(df, final_prompt, api_keys)
                    placeholder.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    return

                # Pertanyaan umum tanpa periode spesifik
                final_prompt = build_enhanced_prompt(active_prompt, full_context)
                response = execute_agent_query(df, final_prompt, api_keys)
                placeholder.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception as e:
                placeholder.error(f"Terjadi kendala: {e}")