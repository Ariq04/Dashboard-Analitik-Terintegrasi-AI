# src/auth/auth.py

import streamlit as st
import pandas as pd
import hashlib
import hmac

from src.database.connection import get_db_engine


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifikasi password dengan proteksi timing-attack (hmac.compare_digest).
    Mendukung:
    1. Modern SHA-256 (format 'sha256$<hash>')
    2. MD5 legacy (32-character hex) untuk backward compatibility demo
    """
    if not plain_password or not hashed_password:
        return False

    # 1. Format Modern SHA-256
    if hashed_password.startswith("sha256$"):
        target_hash = hashed_password.split("$", 1)[1]
        calculated_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(calculated_hash, target_hash)

    # 2. Legacy MD5 Hash (32 karakter hex)
    if len(hashed_password) == 32:
        calculated_md5 = hashlib.md5(plain_password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(calculated_md5, hashed_password)

    return False


def login(email, password):
    """
    Autentikasi pengguna demo dari tabel md_user.
    """
    if not email or not password:
        return False

    engine = get_db_engine()

    query = """
    SELECT
        id_user,
        nama_lengkap,
        email,
        password
    FROM md_user
    WHERE email=%s
    LIMIT 1
    """

    df = pd.read_sql(
        query,
        engine,
        params=(email.strip(),)
    )

    if df.empty:
        return False

    db_password = str(df.iloc[0]["password"]).strip()

    if verify_password(password, db_password):
        st.session_state.logged_in = True
        st.session_state.user_id = df.iloc[0]["id_user"]
        st.session_state.nama = df.iloc[0]["nama_lengkap"]
        st.session_state.email = df.iloc[0]["email"]
        return True

    return False


def logout():
    keys = [
        "logged_in",
        "user_id",
        "nama",
        "email"
    ]

    for k in keys:
        if k in st.session_state:
            del st.session_state[k]

    st.rerun()