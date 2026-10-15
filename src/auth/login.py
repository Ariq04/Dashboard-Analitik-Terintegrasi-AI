import streamlit as st
from src.auth.auth import login


def show_login():

    st.markdown("""
    <style>

    .stApp{
        background:#111827;
    }

    header{
        visibility:hidden;
    }

    footer{
        visibility:hidden;
    }

    [data-testid="stToolbar"]{
        display:none;
    }

    section.main > div{
        padding-top:2rem;
    }

    h1,h2,h3,h4,h5,h6{
        color:white;
    }

    p,label{
        color:#d1d5db;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]{
        background:#151d2e;
        border:1px solid #2d3748;
        border-radius:18px;
        padding:30px;
    }

    div[data-testid="stTextInput"] input{
        border-radius:10px;
    }

    div[data-testid="stButton"] button{
        border-radius:10px;
        height:48px;
        font-weight:600;
        font-size:16px;
    }

    .footer{
        text-align:center;
        color:#94a3b8;
        font-size:13px;
        margin-top:25px;
        line-height:1.8;
    }

    </style>
    """, unsafe_allow_html=True)

    logo_kiri, logo_tengah, logo_kanan = st.columns([1.3, 1, 1])

    with logo_tengah:
        st.image(
            "assets/gambar1.png",
            width=260
        )

    st.write("")

    # ==========================
    # Form Login
    # ==========================

    kiri, tengah, kanan = st.columns([1.2, 1, 1.2])

    with tengah:

        st.markdown(
            """
            <div style='background: rgba(14, 165, 233, 0.1); border: 1px solid #0284c7; border-radius: 10px; padding: 12px; margin-bottom: 18px; text-align: center; font-size: 13px; color: #bae6fd;'>
                🛡️ <b>Versi Portofolio Publik</b><br>
                Seluruh data adalah data sintetis untuk demonstrasi.
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.container(border=True):

            email = st.text_input(
                "Email",
                value="demo@klinikpratama.com",
                placeholder="Masukkan email demo"
            )

            password = st.text_input(
                "Password",
                value="demo123",
                type="password",
                placeholder="Masukkan password demo"
            )

            st.write("")

            if st.button(
                "LOGIN KE DASHBOARD",
                use_container_width=True,
                type="primary"
            ):
                if login(email, password):
                    st.success("Login berhasil")
                    st.rerun()
                else:
                    st.error("Email atau password salah.")

        with st.expander("🔑 Kredensial Akses Demo"):
            st.markdown("""
            - **Email:** `demo@klinikpratama.com`
            - **Password:** `demo123`
            - **Akun Cadangan:** `admin@klinikpratama.com` / `admin123`
            """)

        st.markdown(
            """
            <div class="footer">
                Dashboard Analitik Klinik Pratama (Demo Portfolio)<br>
                © 2026 Klinik Pratama • Data Sintetis
            </div>
            """,
            unsafe_allow_html=True
        )