# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
# pyrefly: ignore [missing-import]
import plotly.graph_objects as go
from datetime import date
from src.database.connection import get_db_engine
from src.database.queries import get_realisasi_pendapatan_per_kategori_query

# --- 1. CONFIGURATION & CSS ---
def apply_style():
    st.markdown("""
        <style>
        .stApp { background-color: #0e1117; }
        .block-container { padding: 1.5rem 2rem; }
        
        /* Card Styling */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #161920; 
            border: 1px solid #30363d; 
            border-radius: 12px; 
            padding: 15px;
            margin-bottom: 10px;
            transition: all 0.3s ease;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: #5865F2;
        }
        
        /* Metric Styling */
        div[data-testid="stMetric"] {
            background-color: #1c202a; 
            padding: 15px; 
            border-radius: 8px;
            border-left: 4px solid #5865F2;
        }
        div[data-testid="stMetricLabel"] { font-size: 13px; color: #a0aab9; }
        div[data-testid="stMetricValue"] { font-size: 24px; color: white; font-weight: 700; }
        
        /* Judul Grafik */
        .chart-title {
            font-size: 16px; font-weight: 600; color: white; margin-bottom: 5px;
        }
        .chart-subtitle {
            font-size: 12px; color: #a0aab9; margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 2. HELPER: FORMAT RUPIAH PINTAR (Juta vs Miliar) ---
def format_currency_indo(value):
    """
    Otomatis ubah format dengan menangani angka NEGATIF juga.
    Menggunakan abs() agar -4 Miliar tetap terdeteksi sebagai Miliar.
    """
    # Tentukan tanda (Negatif atau Positif)
    sign = "-" if value < 0 else ""
    
    # Ambil nilai absolut (tanpa minus) untuk pengecekan logika
    val = abs(value)
    
    if val >= 1_000_000_000:
        # Format Miliar (misal: 1.25 M)
        return f"Rp {sign}{val / 1_000_000_000:.2f} M"
    elif val >= 1_000_000:
        # Format Juta (misal: 850.5 Jt)
        return f"Rp {sign}{val / 1_000_000:.1f} Jt"
    else:
        # Format Ribuan biasa
        return f"Rp {sign}{val:,.0f}"

# --- 3. LOAD DATA ---
def load_data():
    try:
        engine = get_db_engine()
        df = pd.read_sql(get_realisasi_pendapatan_per_kategori_query(), engine)
        return df, None
    except Exception as e:
        return None, str(e)

# --- 4. CHART FUNCTION ---
def plot_category_chart(df_filtered, category_name):
    df_cat = df_filtered[df_filtered['kategori'] == category_name].copy()
    
    if df_cat.empty:
        return None

    target_val = df_cat['target_bulanan'].max() 
    colors = ['#00CC96' if val >= target_val else '#EF553B' for val in df_cat['aktual_pendapatan']]

    fig = go.Figure()

    # Bar Chart (Aktual)
    fig.add_trace(go.Bar(
        x=df_cat['bulan'], 
        y=df_cat['aktual_pendapatan'],
        name='Aktual',
        marker_color=colors, 
        # Label di grafik tetap Juta agar ringkas (karena per bulan biasanya Juta)
        text=df_cat['aktual_pendapatan'] / 1_000_000, 
        texttemplate='%{text:.1f}',
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>Rev: %{y:,.0f}<br>Target: ' + f'{target_val:,.0f}' + '<extra></extra>'
    ))

    # Line Chart (Target)
    fig.add_trace(go.Scatter(
        x=df_cat['bulan'], 
        y=[target_val] * len(df_cat),
        name='Target',
        mode='lines',
        line=dict(color='white', width=2, dash='dot') 
    ))

    fig.update_layout(
        height=250, 
        margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis=dict(showgrid=False, type='category', tickfont=dict(size=10, color='#8b949e')),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', showticklabels=False),
        barmode='overlay'
    )
    
    return fig, df_cat['aktual_pendapatan'].sum(), target_val

# --- 5. MAIN PROGRAM ---
def run():
    apply_style()
    
    df_raw, error = load_data()
    if error:
        st.error(f"Database Error: {error}")
        return

    df_raw['date_temp'] = pd.to_datetime(df_raw['bulan'] + '-01')

    # Tentukan periode default dari data yang tersedia di DB
    if not df_raw.empty:
        default_start = df_raw['date_temp'].min().date()
        default_end = df_raw['date_temp'].max().date()
    else:
        today = date.today()
        default_start = date(today.year, 1, 1)
        default_end = today

    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Performance Monitor")
        st.caption("Analisis Pencapaian Target per Departemen Klinik Pratama • Data Sintetis Demonstrasi")
    with col2:
        date_range = st.date_input("Periode", value=(default_start, default_end), format="YYYY/MM/DD")

    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = default_start, default_end

    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)
    
    df_filtered = df_raw[(df_raw['date_temp'] >= start_ts) & (df_raw['date_temp'] <= end_ts)].copy()

    if df_filtered.empty:
        st.info("Data tidak tersedia pada periode ini.")
        return

    # --- KPI CALCULATIONS ---
    total_rev_all = df_filtered['aktual_pendapatan'].sum()
    
    df_rank = df_filtered.groupby('kategori').agg({
        'aktual_pendapatan': 'sum',
        'target_bulanan': 'max'
    }).reset_index()
    
    num_months = df_filtered['bulan'].nunique()
    df_rank['total_target_period'] = df_rank['target_bulanan'] * num_months
    
    total_target_global = df_rank['total_target_period'].sum()
    achievement_rate = (total_rev_all / total_target_global * 100) if total_target_global > 0 else 0
    gap_global = total_rev_all - total_target_global

    # --- KPI DISPLAY (DENGAN FORMAT BARU) ---
    k1, k2, k3, k4 = st.columns(4)
    
    # Gunakan fungsi format_currency_indo di sini
    k1.metric("Total Revenue", format_currency_indo(total_rev_all), "Actual")
    k2.metric("Total Target", format_currency_indo(total_target_global), "Expected")
    gap_str = format_currency_indo(gap_global).replace("Rp -"   , "- Rp ")
    k3.metric("Achievement Rate", f"{achievement_rate:.1f}%", f"{gap_str} Gap")
    k4.metric("Jml. Kategori", f"{len(df_rank)}", "Active Depts")

    st.markdown("---")

    # --- GRID CHART ---
    df_rank = df_rank.sort_values(by='aktual_pendapatan', ascending=False)
    sorted_categories = df_rank['kategori'].tolist()

    cols = st.columns(3)
    
    for i, category in enumerate(sorted_categories):
        col_idx = i % 3
        
        with cols[col_idx]:
            with st.container(border=True):
                result = plot_category_chart(df_filtered, category)
                
                if result:
                    fig, total_act, target_monthly = result
                    
                    target_period = target_monthly * num_months
                    persen = (total_act / target_period * 100) if target_period > 0 else 0
                    emoji = "🟢" if persen >= 100 else "🔴"
                    
                    # Format angka di subtitle kartu juga menggunakan format pintar
                    txt_act = format_currency_indo(total_act).replace("Rp ", "") # Hilangkan Rp biar hemat tempat
                    txt_trg = format_currency_indo(target_period).replace("Rp ", "")
                    
                    st.markdown(f"""
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div class='chart-title'>{category}</div>
                        <div style='background:rgba(255,255,255,0.1); padding:2px 8px; border-radius:4px; font-size:12px;'>
                            {emoji} {persen:.0f}%
                        </div>
                    </div>
                    <div class='chart-subtitle'>
                        Rev: {txt_act} / Trg: {txt_trg}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})