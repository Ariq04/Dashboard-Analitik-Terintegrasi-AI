import streamlit as st


def render():

    with st.sidebar:

        try:
            st.image("assets/gambar1.png", use_container_width=True)
        except Exception:
            st.warning("Logo tidak ditemukan")

        st.title("Menu Utama")

        st.caption("🛡️ Demo Data Sintetis")

        st.write("---")

        choice = st.radio(
            "Pilih Dashboard Analisis:",
            [
                "Executive Overview",
                "Layanan & Produk",
                "Operasional",
                "Kepuasan Pasien",
                "AI Assistant",
            ],
            index=0
        )

        st.write("---")

        st.info("💡 Gunakan menu AI Assistant untuk analisis cerdas berbasis data demo.")

        st.success("Database: SQLite Demo (Sintetis)")

        # ===========================
        # LOGIN USER
        # ===========================

        st.write("---")

        st.write("Login sebagai")

        if "nama" in st.session_state:
            st.success(st.session_state["nama"])

        if "email" in st.session_state:
            st.caption(st.session_state["email"])

        # ===========================
        # LOGOUT
        # ===========================

        if st.button("Logout", use_container_width=True):
            from src.auth.auth import logout
            logout()

        # RETURN HARUS PALING BAWAH
        return choice