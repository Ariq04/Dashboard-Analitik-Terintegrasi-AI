# src/utils/ikm_helper.py

import pandas as pd


QUESTION_COLUMNS = [f"Q{i}" for i in range(1, 17)]


def get_ikm_category(score):
    if score >= 81:
        return "Sangat Baik"
    elif score >= 62:
        return "Baik"
    elif score >= 43:
        return "Kurang Baik"
    else:
        return "Tidak Baik"


def load_ikm_data(file_path="data/dummy_kuesioner_IKM.csv"):
    if file_path.endswith(".xlsx") or file_path.endswith(".xls"):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path)

    required_cols = ["ID_Responden", "Tanggal_Kunjungan", "Jenis_Layanan"] + QUESTION_COLUMNS
    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        raise ValueError(f"Kolom IKM belum lengkap: {missing}")

    df["Tanggal_Kunjungan"] = pd.to_datetime(df["Tanggal_Kunjungan"])

    for col in QUESTION_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Rata_Rata"] = df[QUESTION_COLUMNS].mean(axis=1)
    df["IKM_Konversi"] = df["Rata_Rata"] * 25
    df["Kategori_IKM"] = df["IKM_Konversi"].apply(get_ikm_category)

    return df


def get_ikm_summary(df):
    nilai_ikm = df["IKM_Konversi"].mean()
    total_responden = len(df)
    kategori = get_ikm_category(nilai_ikm)

    layanan_terendah = (
        df.groupby("Jenis_Layanan")["IKM_Konversi"]
        .mean()
        .sort_values()
        .head(1)
    )

    return {
        "nilai_ikm": nilai_ikm,
        "total_responden": total_responden,
        "kategori": kategori,
        "layanan_terendah": layanan_terendah.index[0] if not layanan_terendah.empty else "-",
        "nilai_layanan_terendah": layanan_terendah.iloc[0] if not layanan_terendah.empty else 0,
    }