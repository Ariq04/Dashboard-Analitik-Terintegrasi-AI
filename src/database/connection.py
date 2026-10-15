# src/database/connection.py

import os
import re
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, event

# Memuat variabel dari file .env
load_dotenv(override=True)


def _register_sqlite_functions(dbapi_connection, connection_record):
    """
    Mendaftarkan fungsi-fungsi kustom pada SQLite agar kompatibel dengan dialek query MySQL.
    """
    def _parse_dt(val):
        if val is None:
            return None
        val_str = str(val).strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
            try:
                return datetime.strptime(val_str, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(val_str)
        except Exception:
            return None

    def _year(val):
        dt = _parse_dt(val)
        return dt.year if dt else None

    def _month(val):
        dt = _parse_dt(val)
        return dt.month if dt else None

    def _hour(val):
        dt = _parse_dt(val)
        return dt.hour if dt else None

    def _date_format(val, fmt):
        dt = _parse_dt(val)
        if not dt:
            return None
        # Normalisasi %% dari dialek PyMySQL/DBAPI menjadi % untuk strftime Python
        py_fmt = str(fmt).replace("%%", "%")
        py_fmt = py_fmt.replace("%i", "%M").replace("%s", "%S")
        return dt.strftime(py_fmt)

    def _regexp(expr, item):
        if item is None or expr is None:
            return False
        try:
            return bool(re.search(str(expr), str(item), re.IGNORECASE))
        except Exception:
            return False

    # Registrasi UDF ke SQLite connection
    dbapi_connection.create_function("YEAR", 1, _year)
    dbapi_connection.create_function("MONTH", 1, _month)
    dbapi_connection.create_function("HOUR", 1, _hour)
    dbapi_connection.create_function("DATE_FORMAT", 2, _date_format)
    dbapi_connection.create_function("REGEXP", 2, _regexp)


def _intercept_params(conn, cursor, statement, parameters, context, executemany):
    """
    Menerjemahkan parameter placeholder MySQL (%s) ke parameter SQLite (?)
    agar query dengan parameter binding (seperti di src/auth/auth.py) berjalan di SQLite.
    """
    if statement and "%s" in statement:
        statement = re.sub(r'(?<!%)%s', '?', statement)
    return statement, parameters


def get_db_engine():
    """
    Menyediakan database engine dengan isolasi ketat:
    - Default mode: Demo Portofolio (SQLite Lokal).
    - Blokir total: Percobaan koneksi ke MySQL produksi pada mode demo akan ditolak seketika.
    - Zero fallback: Jika database lokal belum tersedia, sistem TIDAK AKAN PERNAH mencoba beralih ke produksi.
    """
    app_env = os.getenv("APP_ENV", "demo").strip().lower()
    db_type = os.getenv("DB_TYPE", "sqlite").strip().lower()

    # Guard ketat: Jika mode portofolio / demo aktif, tolak segala upaya koneksi ke database produksi
    if app_env == "demo" and db_type != "sqlite":
        raise PermissionError(
            "[SECURITY ALERT] Mode Portofolio Demo aktif! "
            "Koneksi ke database produksi diblokir secara permanen untuk mencegah kebocoran data."
        )

    # 1. MODE DEMO / PORTOFOLIO (SQLite Lokal)
    if app_env == "demo" or db_type == "sqlite":
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        rel_path = os.getenv("SQLITE_DB_PATH", "data/demo_klinik.db").strip()
        db_path = os.path.normpath(os.path.join(base_dir, rel_path))

        # Pastikan direktori folder database lokal sudah ada
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        # Gunakan format URL SQLite cross-platform dengan forward slash
        db_url_path = db_path.replace("\\", "/")
        engine = create_engine(f"sqlite:///{db_url_path}", echo=False)

        # Pasang listener fungsi kompatibilitas dialek dan parameter binding
        event.listen(engine, "connect", _register_sqlite_functions)
        event.listen(engine, "before_cursor_execute", _intercept_params, retval=True)
        return engine

    # 2. MODE PRODUKSI (Hanya berlaku di lingkungan produksi sebenarnya, BUKAN di folder portofolio)
    raise RuntimeError(
        "[BLOCKED] Konfigurasi produksi dinonaktifkan pada salinan portofolio ini."
    )