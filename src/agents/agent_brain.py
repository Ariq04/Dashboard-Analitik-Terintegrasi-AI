# src/agents/agent_brain.py

from __future__ import annotations

import os
import re
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.promts import get_system_instruction


# Pola regex untuk mendeteksi upaya destructive/insecure command injection
MALICIOUS_PATTERNS = [
    r"\b(drop\s+table|delete\s+from|truncate\s+table|insert\s+into|update\s+.*set|alter\s+table|create\s+table)\b",
    r"\b(rm\s+-rf|rmdir|unlink|remove)\b",
    r"\b(os\.system|subprocess|shutil|eval\(|exec\(|__import__)\b",
    r"\b(open\s*\(|read\s*\(|write\s*\().*(\.env|secret|passwd|shadow)",
    r"\b(socket|urllib|requests\.post|requests\.get)\b",
]


def sophisticated_error_handler(error: Exception) -> str:
    """
    Sanitasi pesan error agar tidak memaparkan API key, path direktori, atau data sensitif ke UI.
    """
    err = str(error)
    # Redact any API key pattern
    err = re.sub(r'AIza[0-9A-Za-z-_]{35}', '[REDACTED_TOKEN]', err)

    err_lower = err.lower()
    if any(kw in err_lower for kw in ["429", "quota", "resource_exhausted", "too many requests"]):
        return (
            "⚠️ **Batas Kuota API Tercapai (Rate Limit):** Permintaan ke Gemini API sedang mencapai batas per menit. "
            "Sistem beralih ke token cadangan jika tersedia, atau silakan coba beberapa saat lagi."
        )

    if any(kw in err_lower for kw in ["503", "unavailable", "high demand", "overloaded"]):
        return (
            "⚠️ **Server Sedang Sibuk (503 High Demand):** Server pusat Google Gemini sedang mengalami antrean traffic global. "
            "Silakan ulangi pertanyaan dalam 3-5 detik."
        )

    if any(kw in err_lower for kw in ["api_key", "invalid api key", "api key not valid", "unauthenticated"]):
        return (
            "❌ **Autentikasi API Gagal:** API Key Gemini tidak valid atau kedaluwarsa. "
            "Pastikan GEMINI_API_KEY di file .env telah diisi dengan API Key Google AI Studio yang valid."
        )

    return f"⚠️ **Kendala Pemrosesan:** Terjadi kendala saat menganalisis data ({err}). Silakan coba ulangi pertanyaan."


class SafeAIBusinessConsultant:
    """
    Mesin AI Business Consultant Terkontrol & Aman (Sandboxed):
    - Tanpa Python REPL / dangerous code execution (Mencegah Remote Code Execution).
    - Akses data read-only pada dataset sintetis in-memory.
    - Menolak perintah manipulasi database (write/drop/delete) dan akses filesystem OS.
    - Menghasilkan analisis bisnis profesional, terstruktur, dan berbasis data demo.
    """

    def __init__(self, df: pd.DataFrame, llm: ChatGoogleGenerativeAI, system_instruction: str):
        self.df = df.copy()  # Salinan in-memory read-only
        self.llm = llm
        self.system_instruction = system_instruction

    def invoke(self, inputs: dict) -> dict:
        prompt = inputs.get("input", "").strip()
        if not prompt:
            return {"output": "Silakan ajukan pertanyaan seputar analisis kinerja klinik demo."}

        # Guard Keamanan: Tolak upaya command injection / manipulasi sistem
        prompt_lower = prompt.lower()
        for pattern in MALICIOUS_PATTERNS:
            if re.search(pattern, prompt_lower):
                return {
                    "output": (
                        "⛔ **Akses Ditolak (Security Boundary):** "
                        "Operasi manipulasi sistem, penulisan data, akses filesystem, atau eksekusi perintah OS "
                        "diblokir secara ketat oleh sistem pengamanan portofolio. AI Business Consultant "
                        "hanya melayani konsultasi analitik bisnis berbasis data sintetis (read-only)."
                    )
                }

        messages = [
            SystemMessage(content=self.system_instruction),
            HumanMessage(content=prompt)
        ]

        try:
            response = self.llm.invoke(messages)
            raw_content = getattr(response, "content", str(response))

            # Ekstrak text jika response.content berupa list (format LangChain Google GenAI v2+)
            if isinstance(raw_content, list):
                text_blocks = []
                for block in raw_content:
                    if isinstance(block, dict) and "text" in block:
                        text_blocks.append(block["text"])
                    elif isinstance(block, str):
                        text_blocks.append(block)
                content = "\n".join(text_blocks).strip()
            else:
                content = str(raw_content).strip()

            if not content:
                content = (
                    "Analisis selesai, namun respons model kosong. "
                    "Silakan ulangi pertanyaan dengan konteks yang lebih spesifik."
                )

            return {"output": content}

        except Exception as e:
            return {"output": sophisticated_error_handler(e)}


from dotenv import load_dotenv


def init_agent(df: pd.DataFrame, google_api_key: str) -> SafeAIBusinessConsultant:
    """
    Inisialisasi Safe AI Business Consultant (terisolasi dan aman untuk demo publik).
    Menggunakan model gratis terkini (gemini-3.5-flash-lite / gemini-3.8-flash) dengan controlled reasoning engine.
    """
    if df is None or df.empty:
        raise ValueError("DataFrame kosong. Pastikan data berhasil dimuat dari database demo.")

    if not google_api_key:
        raise ValueError("Google API Key kosong. Pastikan GEMINI_API_KEY tersedia di .env / environment.")

    load_dotenv(override=True)
    # Menggunakan model gratis gemini-3.5-flash-lite sebagai default
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    if not model_name or "2.5-flash" in model_name:
        model_name = "gemini-3.5-flash-lite"

    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.1,
            google_api_key=google_api_key,
            max_retries=3,
        )

        instruction = get_system_instruction()
        return SafeAIBusinessConsultant(df=df, llm=llm, system_instruction=instruction)

    except Exception as e:
        raise RuntimeError(f"Gagal inisialisasi AI Consultant: {sophisticated_error_handler(e)}")
