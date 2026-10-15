import streamlit as st

from src.auth.login import show_login

from src.components import sidebar
from src.modules import (
    executive,
    operational,
    targets,
    ikm,
    ai_assistant
)

st.set_page_config(
    page_title="Dashboard Analitik Klinik Pratama (Demo Portfolio)",
    layout="wide"
)

# Session login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# =============================
# LOGIN
# =============================
if not st.session_state.logged_in:

    show_login()

# =============================
# DASHBOARD
# =============================
else:

    selected_menu = sidebar.render()

    if selected_menu == "Executive Overview":
        executive.run()

    elif selected_menu == "Layanan & Produk":
        targets.run()

    elif selected_menu == "Operasional":
        operational.run()

    elif selected_menu == "Kepuasan Pasien":
        ikm.run()

    elif selected_menu == "AI Assistant":
        ai_assistant.run()