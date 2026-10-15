# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
# pyrefly: ignore [missing-import]
import plotly.express as px
# pyrefly: ignore [missing-import]
import plotly.graph_objects as go
from datetime import date
from src.database.connection import get_db_engine
from src.database.queries import (
    get_pasien_baru_lama_query,
    get_heatmap_kunjungan_query,
    get_rata_rata_kunjungan_query,
    get_top_penyakit_query,
    get_top_produk_query
)

# --- 1. CONFIGURATION & CSS (EXECUTIVE STYLE - FIXED ALIGNMENT & COLOR) ---
def apply_executive_style():
    st.markdown("""
        <style>
        /* Global Background */
        .stApp { background-color: #0e1117; }
        .block-container { 
            padding-top: 1.5rem; 
            padding-bottom: 3rem; 
            padding-left: 2rem; 
            padding-right: 2rem; 
        }
        h1, h2, h3 { color: #ffffff; font-family: 'Segoe UI', sans-serif; font-weight: 700; }
        
        /* --- STYLING KPI CARD (SAMA PERSIS DENGAN EXECUTIVE) --- */
        div[data-testid="stMetric"] {
            background-color: #1c202a;
            padding: 15px 20px;
            border-radius: 8px;
            
            /* WARNA GARIS BIRU UTAMA (SAMA DENGAN EXECUTIVE) */
            border-left: 6px solid #636EFA; 
            
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border-top: 1px solid #2d3342;
            border-right: 1px solid #2d3342;
            border-bottom: 1px solid #2d3342;
            
            /* Pengaturan Layout (Agar Judul Rata Atas & Tinggi Sama) */
            min-height: 140px; 
            display: flex;
            flex-direction: column;
            justify-content: flex-start; /* Judul mulai dari atas */
            gap: 5px; /* Jarak rapi antara judul dan angka */
        }
        
        /* Label Judul Kecil */
        div[data-testid="stMetricLabel"] { 
            font-size: 14px; 
            color: #a0aab9; 
            font-weight: 500;
        }
        
        /* Angka Utama Besar */
        div[data-testid="stMetricValue"] { 
            font-size: 28px; 
            color: #ffffff; 
            font-weight: 700;
        }
        
        /* Delta / Persen (Badge Style) */
        div[data-testid="stMetricDelta"] {
            font-size: 14px;
            background-color: rgba(255, 255, 255, 0.05);
            padding: 2px 8px;
            border-radius: 4px;
            width: fit-content;
        }
        
        /* --- CHART CONTAINER --- */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #161920;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 1rem;
        }
        
        /* Date Input Label */
        div[data-testid="stDateInput"] label { color: #ffffff; font-size: 14px; font-weight: 600; }
        </style>
    """, unsafe_allow_html=True)

# --- 2. LOAD DATA ---
def load_data():
    try:
        engine = get_db_engine()
        df_new_old = pd.read_sql(get_pasien_baru_lama_query(), engine)
        df_heatmap = pd.read_sql(get_heatmap_kunjungan_query(), engine)
        df_avg = pd.read_sql(get_rata_rata_kunjungan_query(), engine)
        df_penyakit = pd.read_sql(get_top_penyakit_query(), engine) 
        df_produk = pd.read_sql(get_top_produk_query(), engine)
        
        # Preprocessing
        df_new_old['date'] = pd.to_datetime(df_new_old['bulan'] + '-01')
        df_avg['date'] = pd.to_datetime(df_avg['bulan'] + '-01')
        df_heatmap['date'] = pd.to_datetime(dict(year=df_heatmap.tahun, month=df_heatmap.bulan, day=1))
        df_penyakit['waktu_daftar'] = pd.to_datetime(df_penyakit['waktu_daftar'])
        df_produk['tanggal'] = pd.to_datetime(df_produk['tanggal']) 
        
        return df_new_old, df_heatmap, df_avg, df_penyakit, df_produk, None
    except Exception as e:
        return None, None, None, None, None, str(e)

# --- 3. HELPER FILTER ---
def filter_by_date(df, date_col, start, end):
    if df is None or df.empty: return df
    s = pd.Timestamp(start)
    e = pd.Timestamp(end)
    return df[(df[date_col] >= s) & (df[date_col] <= e)]

# --- 4. MAIN PROGRAM ---
def run():
    apply_executive_style()
    
    # Load Data First
    df_new_old_raw, df_heatmap_raw, df_avg_raw, df_penyakit_raw, df_produk_raw, error = load_data()
    
    if error:
        st.error(f"Database Error: {error}")
        return

    # Tentukan periode default dari data yang tersedia di DB
    if df_new_old_raw is not None and not df_new_old_raw.empty:
        default_start = df_new_old_raw['date'].min().date()
        default_end = df_new_old_raw['date'].max().date()
    else:
        today = date.today()
        default_start = date(today.year, 1, 1)
        default_end = today

    # Header & Filter
    col_L, col_R = st.columns([3, 1.2], gap="large")
    with col_L:
        st.title("Operational & Patient")
        st.caption("Analisis Kunjungan, Jam Sibuk, Medis, dan Farmasi • Data Sintetis Demonstrasi")
    with col_R:
        date_range = st.date_input("Filter Periode", value=(default_start, default_end), format="YYYY/MM/DD")

    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = default_start, default_end

    df_new_old = filter_by_date(df_new_old_raw, 'date', start_date, end_date)
    df_heatmap = filter_by_date(df_heatmap_raw, 'date', start_date, end_date)
    df_avg = filter_by_date(df_avg_raw, 'date', start_date, end_date)
    df_penyakit = filter_by_date(df_penyakit_raw, 'waktu_daftar', start_date, end_date)
    df_produk = filter_by_date(df_produk_raw, 'tanggal', start_date, end_date)

    if df_new_old.empty:
        st.warning("Data tidak tersedia untuk periode ini.")
        return

    # --- ROW 1: KPI ---
    total_visit = df_avg['total_kunjungan'].sum()
    summary_patient = df_new_old.groupby('status_pasien')['jumlah_pasien'].sum()
    jml_baru = summary_patient.get('Pasien Baru', 0)
    jml_lama = summary_patient.get('Pasien Lama', 0)
    
    # Rasio
    total_pat = jml_baru + jml_lama
    ratio_new = (jml_baru / total_pat * 100) if total_pat > 0 else 0
    avg_visit_ratio = df_avg['total_kunjungan'].sum() / df_avg['total_pasien_unik'].sum() if df_avg['total_pasien_unik'].sum() > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(label="Total Kunjungan", value=f"{total_visit:,.0f}")
    k2.metric(label="Pasien Baru", value=f"{jml_baru:,.0f}", delta=f"{ratio_new:.1f}% Share")
    k3.metric(label="Pasien Lama", value=f"{jml_lama:,.0f}", delta="Retensi")
    k4.metric(label="Freq. Kunjungan", value=f"{avg_visit_ratio:.2f}x", delta="Avg per Pasien")

    st.write("") 

    # --- ROW 2: CHART GRID (HEATMAP & BAR) ---
    c_heatmap, c_bar = st.columns([1.6, 1.4], gap="medium")

    # [KIRI] HEATMAP (WARNA: TEAL - HARMONIS)
    with c_heatmap:
        with st.container(border=True):
            st.subheader("Heatmap Jam Sibuk")
            pivot_heatmap = df_heatmap.pivot_table(index='bulan', columns='jam', values='jumlah_kunjungan', aggfunc='sum', fill_value=0)
            pivot_heatmap = pivot_heatmap.reindex(index=range(1, 13), fill_value=0)
            pivot_heatmap = pivot_heatmap.reindex(columns=range(24), fill_value=0)
            
            map_bulan = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'Mei', 6:'Jun', 7:'Jul', 8:'Agu', 9:'Sep', 10:'Okt', 11:'Nov', 12:'Des'}
            pivot_heatmap.index = pivot_heatmap.index.map(map_bulan)
            
            fig_heat = px.imshow(
                pivot_heatmap,
                labels=dict(x="Jam", y="Bulan", color="Jml"),
                x=pivot_heatmap.columns, y=pivot_heatmap.index,
                # PERUBAHAN: Warna 'Teal' lebih sejuk & profesional dibanding YlGnBu
                color_continuous_scale='Teal', 
                text_auto=True, aspect="auto"
            )
            fig_heat.update_layout(
                height=350, margin=dict(l=0, r=0, t=30, b=0),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(side="bottom", title="Jam Kunjungan"), yaxis=dict(title=None)
            )
            st.plotly_chart(fig_heat, use_container_width=True)

    # [KANAN] PASIEN BARU VS LAMA (WARNA: CYAN & SALMON)
    with c_bar:
        with st.container(border=True):
            st.subheader("Pasien Baru vs Lama")
            fig_bar = px.bar(
                df_new_old, x='bulan', y='jumlah_pasien', color='status_pasien', 
                barmode='group',
                # Warna tetap dipertahankan karena kontrasnya bagus (Cyan & Soft Red)
                color_discrete_map={'Pasien Baru': '#00D2FC', 'Pasien Lama': '#FF6F91'}
            )
            fig_bar.update_layout(
                height=350, margin=dict(l=10, r=10, t=30, b=10),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(title=None, showgrid=False),
                yaxis=dict(title=None, showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                legend=dict(orientation="h", y=1.1, x=0, title=None), hovermode="x unified"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    # --- ROW 3: ANALISIS MEDIS & FARMASI ---
    st.write("")
    st.markdown("### Analisis Medis & Farmasi")
    
    col_med, col_drug = st.columns(2, gap="medium")

    # [KIRI] TOP 10 PENYAKIT (WARNA: TEAL - SENADA HEATMAP)
    with col_med:
        with st.container(border=True):
            st.subheader(f" Top 10 Keluhan")
            if not df_penyakit.empty:
                top_disease = df_penyakit['nama_penyakit'].value_counts().nlargest(10).reset_index()
                top_disease.columns = ['Penyakit', 'Kasus']
                
                fig_dis = px.bar(
                    top_disease, x='Kasus', y='Penyakit', orientation='h', text_auto=True,
                    color='Kasus', color_continuous_scale='Teal' # Senada dengan Heatmap
                )
                fig_dis.update_layout(
                    height=400, margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    yaxis=dict(autorange="reversed", title=None),
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig_dis, use_container_width=True)
            else:
                st.info("Tidak ada data penyakit.")

    # [KANAN] TOP 10 PRODUK (WARNA: BLUES & GREENS)
    with col_drug:
        with st.container(border=True):
            st.subheader(f"Top 10 Obat/Produk")
            
            if not df_produk.empty:
                df_prod_grouped = df_produk.groupby('nama_obat').agg({
                    'total_terjual': 'sum',
                    'total_pendapatan': 'sum'
                }).reset_index()

                tab_qty, tab_rev = st.tabs(["Stok Terlaris (Qty)", "Omzet Tertinggi (Rp)"])
                
                # TAB 1: QTY (Gunakan BLUES agar senada dengan tema utama)
                with tab_qty:
                    top_qty = df_prod_grouped.nlargest(10, 'total_terjual')
                    fig_qty = px.bar(
                        top_qty, x='total_terjual', y='nama_obat', orientation='h', text_auto=True,
                        color='total_terjual', color_continuous_scale='Blues' # Ganti dari Purple ke Blue
                    )
                    fig_qty.update_layout(
                        height=350, margin=dict(l=10, r=10, t=10, b=10),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        yaxis=dict(autorange="reversed", title=None),
                        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Pcs Terjual"),
                        coloraxis_showscale=False
                    )
                    st.plotly_chart(fig_qty, use_container_width=True)

                # TAB 2: REVENUE (Gunakan GREENS - Simbol Uang)
                with tab_rev:
                    top_rev = df_prod_grouped.nlargest(10, 'total_pendapatan')
                    fig_rev = px.bar(
                        top_rev, x='total_pendapatan', y='nama_obat', orientation='h', 
                        text_auto='.2s', 
                        color='total_pendapatan', color_continuous_scale='Greens' # Tetap Hijau (Uang)
                    )
                    fig_rev.update_layout(
                        height=350, margin=dict(l=10, r=10, t=10, b=10),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        yaxis=dict(autorange="reversed", title=None),
                        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Total Pendapatan (Rp)"),
                        coloraxis_showscale=False
                    )
                    st.plotly_chart(fig_rev, use_container_width=True)

            else:
                st.info("Tidak ada data penjualan produk/obat.")