# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
# pyrefly: ignore [missing-import]
import plotly.express as px
from datetime import date

from src.database.connection import get_db_engine
from src.database import queries


# 
# STYLE
# 

def apply_style():

    st.markdown("""
    <style>

    .stApp{
        background:#0e1117;
    }

    div[data-testid="stMetric"]{
        background:#161b22;
        border:1px solid #30363d;
        border-left:6px solid #00D2FC;
        border-radius:12px;
        padding:18px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }

    div[data-testid="stMetricLabel"] { font-size: 14px; color: #a0aab9; font-weight: 500; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #ffffff; font-weight: 700; }

    div[data-testid="stVerticalBlockBorderWrapper"]{
        background:#161b22;
        border:1px solid #30363d;
        border-radius:12px;
        padding:18px;
    }

    div[data-testid="stDateInput"] label { color: #ffffff; font-size: 14px; font-weight: 600; }

    </style>
    """, unsafe_allow_html=True)


def calculate_mutu_kategori(ikm_konversi):
    if ikm_konversi >= 88.31:
        return "A", "Sangat Baik"
    elif ikm_konversi >= 76.61:
        return "B", "Baik"
    elif ikm_konversi >= 65.00:
        return "C", "Kurang Baik"
    else:
        return "D", "Tidak Baik"


# MAIN

def run(filters=None):

    apply_style()

    engine = get_db_engine()

    # LOAD DATA RESPONDEN TERLEBIH DAHULU
    df_responden_raw = pd.read_sql(
        queries.get_ikm_responden_query(),
        engine
    )

    if df_responden_raw.empty:
        st.warning("Data responden IKM tidak ditemukan di database.")
        return

    df_responden_raw['tanggal'] = pd.to_datetime(df_responden_raw['tanggal'])

    # Tentukan periode default dari data yang tersedia
    default_start = df_responden_raw['tanggal'].min().date()
    default_end = df_responden_raw['tanggal'].max().date()

    # HEADER & FILTER PERIODE (KANAN ATAS)
    col_L, col_R = st.columns([3, 1.2], gap="large")
    with col_L:
        st.title("Analisis Indeks Kepuasan Masyarakat (IKM)")
        st.caption("Dashboard Analitik Kepuasan Pasien Klinik Pratama • Data Sintetis Demonstrasi")
    with col_R:
        date_range = st.date_input(
            "Filter Periode",
            value=(default_start, default_end),
            format="YYYY/MM/DD",
            key="ikm_header_periode"
        )

    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = default_start, default_end

    df_responden = df_responden_raw.copy()

    # FILTER TANGGAL PERIODE (DARI HEADER ATAS)
    if start_date and end_date:
        df_responden = df_responden[
            (df_responden['tanggal'] >= pd.Timestamp(start_date)) &
            (df_responden['tanggal'] <= pd.Timestamp(end_date))
        ]

    # FILTER JENIS LAYANAN (DARI SIDEBAR)
    if filters:
        selected_services = filters.get("selected_services", [])
        is_semua = filters.get("is_semua", True)

        if not is_semua:
            if selected_services:
                df_responden = df_responden[df_responden['jenis_layanan'].isin(selected_services)]
            else:
                df_responden = df_responden.iloc[0:0]

    if df_responden.empty:
        st.warning("Data tidak ditemukan pada filter periode/layanan ini.")
        return

    # HITUNG METRIK IKM (Q1-Q16)
    q_cols = [f"q{i}" for i in range(1, 17)]
    df_responden['rata_responden'] = df_responden[q_cols].mean(axis=1)
    df_responden['ikm_konversi'] = df_responden['rata_responden'] * 25

    nilai_ikm = df_responden['rata_responden'].mean()
    ikm_konversi = nilai_ikm * 25
    total_responden = len(df_responden)
    mutu, kategori = calculate_mutu_kategori(ikm_konversi)

    # KPI
    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Nilai IKM",
        f"{nilai_ikm:.3f}"
    )

    c2.metric(
        "IKM Konversi",
        f"{ikm_konversi:.2f}"
    )

    c3.metric(
        "Total Responden",
        int(total_responden)
    )

    c4.metric(
        "Mutu Pelayanan",
        kategori
    )

    st.divider()

    # TREND
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Trend IKM Bulanan")

        df_responden['bulan'] = df_responden['tanggal'].dt.strftime('%Y-%m')
        df_trend = df_responden.groupby('bulan')['ikm_konversi'].mean().round(2).reset_index().rename(columns={'ikm_konversi': 'ikm'})

        fig = px.area(
            df_trend,
            x="bulan",
            y="ikm",
            markers=True,
            color_discrete_sequence=['#00C9A7']
        )
        fig.update_traces(
            line=dict(width=3, shape='spline'),
            marker=dict(size=8, color='#00C9A7', line=dict(width=2, color='#ffffff'))
        )

        fig.update_layout(
            height=380,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title="Bulan", showgrid=False, tickfont=dict(color='#a0aab9')),
            yaxis=dict(title="Nilai IKM", showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#a0aab9')),
            hovermode="x unified"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # LAYANAN
    with col2:
        st.subheader("IKM Berdasarkan Layanan")

        df_layanan = df_responden.groupby('jenis_layanan')['ikm_konversi'].mean().round(2).reset_index().rename(columns={'ikm_konversi': 'ikm'}).sort_values('ikm', ascending=True)

        fig = px.bar(
            df_layanan,
            x="ikm",
            y="jenis_layanan",
            orientation="h",
            text_auto=".2f",
            color="ikm",
            color_continuous_scale="Tealgrn"
        )

        fig.update_traces(
            textposition='inside',
            textfont=dict(color='white')
        )

        fig.update_layout(
            height=380,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            coloraxis_showscale=False,
            xaxis=dict(title="Nilai IKM", showgrid=False, tickfont=dict(color='#a0aab9')),
            yaxis=dict(title="", showgrid=False, tickfont=dict(size=12, color='#ffffff'))
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    # UNSUR
    unsur_list = []
    for i in range(1, 17):
        q_col = f"q{i}"
        total_val = df_responden[q_col].sum()
        avg_val = df_responden[q_col].mean()
        unsur_list.append({
            "unsur": f"Q{i}",
            "total_nilai": total_val,
            "rata_rata": round(avg_val, 2)
        })
    df_unsur = pd.DataFrame(unsur_list)

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Rata-rata Unsur Pelayanan")

        fig = px.bar(
            df_unsur,
            x="unsur",
            y="rata_rata",
            text_auto=".2f",
            color="rata_rata",
            color_continuous_scale="Viridis"
        )

        fig.update_traces(
            textposition='outside',
            textfont=dict(color='white')
        )

        fig.update_layout(
            yaxis_range=[0, 4.3],
            height=420,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            coloraxis_showscale=False,
            xaxis=dict(title="Unsur Pelayanan", showgrid=False, tickfont=dict(color='#ffffff')),
            yaxis=dict(title="Rata-rata Score", showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#a0aab9'))
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with c2:
        st.subheader("Ranking Unsur")

        ranking = df_unsur.sort_values(
            "rata_rata",
            ascending=True
        )

        fig = px.bar(
            ranking,
            x="rata_rata",
            y="unsur",
            orientation="h",
            text_auto=".2f",
            color="rata_rata",
            color_continuous_scale="Sunsetdark"
        )

        fig.update_traces(
            textposition='inside',
            textfont=dict(color='white')
        )

        fig.update_layout(
            height=420,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            coloraxis_showscale=False,
            xaxis=dict(title="Rata-rata Score", showgrid=False, tickfont=dict(color='#a0aab9')),
            yaxis=dict(title="Unsur", showgrid=False, tickfont=dict(size=12, color='#ffffff'))
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    # DETAIL DATA
    st.subheader("Data Responden")

    df_display = df_responden_raw[df_responden_raw['id'].isin(df_responden['id'])].copy()

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )