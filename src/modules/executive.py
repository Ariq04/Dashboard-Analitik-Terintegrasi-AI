# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
# pyrefly: ignore [missing-import]
import plotly.express as px
# pyrefly: ignore [missing-import]
import plotly.graph_objects as go
# pyrefly: ignore [missing-import]
from plotly.subplots import make_subplots
from datetime import date
from src.database.queries import get_realisasi_pendapatan_per_kategori_query
#from src.database.queries import get_metode_pembayaran_query

from src.database.connection import get_db_engine
from src.database.queries import (
    get_pendapatan_bulanan_query, 
    get_growth_drivers_query,
    get_trend_kontribusi_query,
    get_top_10_layanan_query
)

# --- 1. CONFIGURATION & CSS (PERBAIKAN VISUAL) ---
def apply_final_style():
    st.markdown("""
        <style>
        /* GLOBAL SETTINGS */
        .stApp { background-color: #0e1117; }
        .block-container { 
            padding-top: 1.5rem; 
            padding-bottom: 3rem; 
            padding-left: 2rem; 
            padding-right: 2rem; 
        }
        h1, h2, h3 { color: #ffffff; font-family: 'Segoe UI', sans-serif; font-weight: 700; }
        
        /* --- STYLING KPI CARD --- */
        div[data-testid="stMetric"] {
            background-color: #1c202a;
            padding: 15px 20px;
            border-radius: 8px;
            border-left: 6px solid #636EFA;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border-top: 1px solid #2d3342;
            border-right: 1px solid #2d3342;
            border-bottom: 1px solid #2d3342;
        }
        
        div[data-testid="stMetricLabel"] { font-size: 14px; color: #a0aab9; font-weight: 500; }
        div[data-testid="stMetricValue"] { font-size: 28px; color: #ffffff; font-weight: 700; padding-bottom: 5px; }
        div[data-testid="stMetricDelta"] {
            font-size: 14px; background-color: rgba(255, 255, 255, 0.05);
            padding: 2px 8px; border-radius: 4px; width: fit-content;
        }
        
        /* --- CHART CONTAINER --- */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #161920;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 1rem;
        }
        
        /* --- TABS STYLING --- */
        button[data-baseweb="tab"] {
            color: #a0aab9;
            font-weight: 600;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #ffffff;
            background-color: #1c202a;
            border-radius: 4px;
        }

        /* --- STYLING FILTER DATE --- */
        div[data-testid="stDateInput"] label { color: #ffffff; font-size: 14px; font-weight: 600; }
        </style>
    """, unsafe_allow_html=True)

# --- 2. FUNGSI LOAD DATA ---
def load_all_data():
    try:
        engine = get_db_engine()
        df_trend = pd.read_sql(get_pendapatan_bulanan_query(), engine)
        df_growth = pd.read_sql(get_growth_drivers_query(), engine)
        df_kontribusi = pd.read_sql(get_trend_kontribusi_query(), engine)
        df_top10 = pd.read_sql(get_top_10_layanan_query(), engine)
        df_target = pd.read_sql(get_realisasi_pendapatan_per_kategori_query(), engine)
        # df_metode = pd.read_sql(get_metode_pembayaran_query(), engine)


        # Preprocessing
        df_trend['date'] = pd.to_datetime(dict(year=df_trend.tahun, month=df_trend.bulan, day=1))
        map_bulan_indo = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'Mei', 6:'Jun', 7:'Jul', 8:'Agu', 9:'Sep', 10:'Okt', 11:'Nov', 12:'Des'}
        df_trend['nama_bulan'] = df_trend['bulan'].map(map_bulan_indo)
        df_trend['tahun'] = df_trend['tahun'].astype(str)

        df_growth['date'] = pd.to_datetime(df_growth['periode'] + '-01')
        df_growth['RPK'] = df_growth.apply(lambda x: x['total_pendapatan'] / x['jumlah_kunjungan'] if x['jumlah_kunjungan'] > 0 else 0, axis=1)

        df_kontribusi['date'] = pd.to_datetime(df_kontribusi['periode'] + '-01')

        if df_target is not None and not df_target.empty:
            df_target['date'] = pd.to_datetime(df_target['bulan'] + '-01')

        return df_trend, df_growth, df_kontribusi, df_top10, df_target, None
    except Exception as e:
        return None, None, None, None, None, str(e)

# --- 3. HELPER FILTER ---
def filter_dataframe_by_date(df, date_col, start_date, end_date):
    if df is None or df.empty: return df
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)
    return df[(df[date_col] >= start_ts) & (df[date_col] <= end_ts)]

# --- 4. MAIN APP ---
def run():
    apply_final_style()
    
    # --- LOAD DATA FIRST ---
    df_trend_raw, df_growth_raw, df_kontribusi_raw, df_top10, df_target_raw, error = load_all_data()
    if error:
        st.error(f"Database Error: {error}")
        return

    # Tentukan periode default dari data yang tersedia di DB
    if df_trend_raw is not None and not df_trend_raw.empty:
        default_start = df_trend_raw['date'].min().date()
        default_end = df_trend_raw['date'].max().date()
    else:
        today = date.today()
        default_start = date(today.year, 1, 1)
        default_end = today

    # --- HEADER & FILTER ---
    col_L, col_R = st.columns([3, 1.2], gap="large")
    with col_L:
        st.title("Executive Dashboard")
        st.caption("Monitoring Kinerja Bisnis & Operasional Klinik Pratama • Data Sintetis Demonstrasi")
    with col_R:
        date_range = st.date_input("Filter Periode", value=(default_start, default_end), format="YYYY/MM/DD")

    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = default_start, default_end

    df_trend = filter_dataframe_by_date(df_trend_raw, 'date', start_date, end_date)
    df_growth = filter_dataframe_by_date(df_growth_raw, 'date', start_date, end_date)
    df_kontribusi = filter_dataframe_by_date(df_kontribusi_raw, 'date', start_date, end_date)
    df_target = filter_dataframe_by_date(df_target_raw, 'date', start_date, end_date)
    #df_metode = filter_dataframe_by_date(df_metode  , 'date', start_date, end_date)
    
    if df_trend.empty:
        st.warning("Data tidak ditemukan pada periode ini.")
        return

    map_bulan = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'Mei', 6:'Jun', 7:'Jul', 8:'Agu', 9:'Sep', 10:'Okt', 11:'Nov', 12:'Des'}

    # --- ROW 1: KPI MATRIX (DATA REAL-TIME) ---
    st.markdown("##### Key Performance Indicators")
    
    total_rev = df_trend['total_pendapatan'].sum()
    total_visit = df_growth['jumlah_kunjungan'].sum()
    avg_rpk = total_rev / total_visit if total_visit > 0 else 0

    # 1. Hitung Target Global Periode Terpilih
    if df_target is not None and not df_target.empty:
        df_target_rank = df_target.groupby('kategori').agg({
            'aktual_pendapatan': 'sum',
            'target_bulanan': 'max'
        }).reset_index()
        num_months_target = df_target['bulan'].nunique()
        df_target_rank['total_target_period'] = df_target_rank['target_bulanan'] * num_months_target
        total_target_global = df_target_rank['total_target_period'].sum()
    else:
        total_target_global = 0

    # 2. Delta Revenue vs Target
    if total_target_global > 0:
        rev_vs_target_pct = ((total_rev - total_target_global) / total_target_global) * 100
        rev_delta_str = f"{rev_vs_target_pct:+.1f}% vs Target"
    else:
        rev_delta_str = "No Target"

    # 3. MoM Kunjungan & MoM RPK (Membandingkan bulan terakhir vs bulan sebelumnya)
    df_growth_sorted = df_growth.sort_values('date') if df_growth is not None else pd.DataFrame()
    if len(df_growth_sorted) >= 2:
        latest_visit = df_growth_sorted.iloc[-1]['jumlah_kunjungan']
        prev_visit = df_growth_sorted.iloc[-2]['jumlah_kunjungan']
        visit_mom_pct = ((latest_visit - prev_visit) / prev_visit * 100) if prev_visit > 0 else 0
        visit_delta_str = f"{visit_mom_pct:+.1f}% MoM"

        latest_rpk = df_growth_sorted.iloc[-1]['RPK']
        prev_rpk = df_growth_sorted.iloc[-2]['RPK']
        rpk_mom_pct = ((latest_rpk - prev_rpk) / prev_rpk * 100) if prev_rpk > 0 else 0
        rpk_delta_str = f"{rpk_mom_pct:+.1f}% MoM"
    else:
        visit_delta_str = "1 Periode"
        rpk_delta_str = "1 Periode"

    # 4. Target Capaian & Status
    if total_target_global > 0:
        capaian_pct = (total_rev / total_target_global) * 100
        capaian_val_str = f"{capaian_pct:.1f}%"
        if capaian_pct >= 100:
            capaian_delta_str = "Target Tercapai"
        elif capaian_pct >= 80:
            capaian_delta_str = "On Track"
        else:
            capaian_delta_str = "- Under Target"
    else:
        capaian_val_str = "N/A"
        capaian_delta_str = "No Target"

    k1, k2, k3, k4 = st.columns(4)
    
    k1.metric(
        label="Total Revenue", 
        value=f"Rp {total_rev/1_000_000_000:.2f} M" if total_rev >= 1_000_000_000 else f"Rp {total_rev/1_000_000:.1f} Jt",
        delta=rev_delta_str
    )
    
    k2.metric(
        label="Total Kunjungan", 
        value=f"{total_visit:,.0f} Pasien",
        delta=visit_delta_str
    )
    
    k3.metric(
        label="Rata-rata RPK", 
        value=f"Rp {avg_rpk:,.0f}",
        delta=rpk_delta_str
    )
    
    k4.metric(
        label="Target Capaian", 
        value=capaian_val_str,
        delta=capaian_delta_str
    )

    st.write("") # Spacer

    # --- ROW 2: CHART UTAMA (TREND & TOP 10) ---
    col_chart_L, col_chart_R = st.columns([2, 1], gap="medium")
    
    # GRAFIK 1: TREN PENDAPATAN
    with col_chart_L:
        with st.container(border=True): 
            st.subheader("Tren Pendapatan")
            fig_trend = px.area(df_trend, x='bulan', y='total_pendapatan', color='tahun', markers=True, color_discrete_sequence=['#00C9A7', '#845EC2', '#FF9671', '#4B49AC', '#00D2FC'])
            fig_trend.update_layout(
                height=350, margin=dict(l=10, r=10, t=30, b=10),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(tickmode='array', tickvals=list(range(1,13)), ticktext=list(map_bulan.values()), showgrid=False, title=None),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title=None, tickfont=dict(color='#a0aab9')),
                legend=dict(orientation="h", y=1.1, x=0, title=None), hovermode="x unified"
            )
            st.plotly_chart(fig_trend, use_container_width=True)

    # GRAFIK 2: TOP 10 LAYANAN (DENGAN TABS FILTERING)
    with col_chart_R:
        with st.container(border=True):
            st.subheader("Top 10 Layanan")
            
            # Membuat Tabs untuk Navigasi
            tab_gabungan, tab_satuan, tab_paket = st.tabs(["Gabungan", "Satuan", "Paket"])
            
            # Helper function untuk plot agar coding lebih rapi
            def plot_top_10(df_source, color_hex):
                if df_source.empty:
                    st.info("Data tidak tersedia.")
                    return
                
                # Ambil Top 10 dari data yang sudah difilter
                df_sorted = df_source.sort_values(by="total_pendapatan", ascending=True).tail(10)
                
                fig = px.bar(
                    df_sorted, 
                    y='nama_layanan', 
                    x='total_pendapatan', 
                    orientation='h', 
                    text_auto='.2s', 
                    color_discrete_sequence=[color_hex]
                )
                fig.update_layout(
                    height=350, 
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, showticklabels=False),
                    yaxis=dict(showgrid=False, title=None, tickfont=dict(size=11, color='#ffffff')), 
                    showlegend=False
                )
                fig.update_traces(textposition='inside', textfont=dict(color='white'))
                st.plotly_chart(fig, use_container_width=True)

            # --- KONTEN TAB GABUNGAN ---
            with tab_gabungan:
                # Agregat ulang agar jika ada nama layanan sama beda kategori (jarang terjadi) tetap aman
                df_all = df_top10.groupby('nama_layanan')['total_pendapatan'].sum().reset_index()
                plot_top_10(df_all, '#4B49AC') # Warna Ungu

            # --- KONTEN TAB SATUAN ---
            with tab_satuan:
                df_satuan = df_top10[df_top10['kategori'] == 'Satuan']
                plot_top_10(df_satuan, '#00D2FC') # Warna Cyan/Biru Muda

            # --- KONTEN TAB PAKET ---
            with tab_paket:
                df_paket = df_top10[df_top10['kategori'] == 'Paket']
                plot_top_10(df_paket, '#FF9671') # Warna Orange

    # --- ROW 3: GROWTH DRIVERS ---
    with st.container(border=True):
        st.subheader("Analisis Growth Drivers")
        fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
        fig_dual.add_trace(go.Scatter(x=df_growth['date'], y=df_growth['jumlah_kunjungan'], name="Kunjungan", line=dict(color='#00D2FC', width=3), mode='lines+markers'), secondary_y=False)
        fig_dual.add_trace(go.Scatter(x=df_growth['date'], y=df_growth['RPK'], name="RPK (Rp)", line=dict(color='#FF6F91', width=3, dash='dot'), mode='lines+markers'), secondary_y=True)
        fig_dual.update_layout(
            height=350, margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", y=1.1, x=0), hovermode="x unified"
        )
        fig_dual.update_yaxes(title_text="Jml Kunjungan", showgrid=True, gridcolor='rgba(255,255,255,0.05)', secondary_y=False)
        fig_dual.update_yaxes(title_text="RPK (Rp)", showgrid=False, secondary_y=True)
        fig_dual.update_xaxes(showgrid=False)
        st.plotly_chart(fig_dual, use_container_width=True)

    # --- ROW 4: KONTRIBUSI LAYANAN ---
    with st.container(border=True):
        st.subheader("Tren Kontribusi Layanan")
        fig_stack = px.bar(
            df_kontribusi, x='date', y='total_pendapatan', color='tipe_layanan',
            color_discrete_map={'Paket': '#4C72B0', 'Satuan': '#DD8452'}
        )
        fig_stack.update_layout(
            height=300, margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title=None, showgrid=False), yaxis=dict(title=None, showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
            legend=dict(orientation="h", y=1.1, x=0, title=None), hovermode="x unified"
        )
        st.plotly_chart(fig_stack, use_container_width=True)
    
    # with st.container(border=True): # Membuat wadah border kotak yang rapi
    #      st.subheader("Metode Pembayaran Pasien") # Judul Grafik
    #      fig_metode = px.pie(
    #         df_metode, 
    #         names='metode_bayar', 
    #         values='total_pendapatan',
    #         hole=0.4, # Membuat efek Donut Chart modern
    #         color_discrete_sequence=['#00D2FC', '#845EC2', '#FF9671'])

    #      fig_metode.update_layout(
    #     margin=dict(l=50, r=50, t=40, b=40), # Margin sedikit lebih lebar
    #     paper_bgcolor='rgba(0,0,0,0)',
    #     plot_bgcolor='rgba(0,0,0,0)',
    #     font=dict(color='#ffffff') # Teks putih agar kontras
    #     )
    #      st.plotly_chart(fig_metode, use_container_width=True) # Render ke layar
    

