# 🏥 Clinic Analytics Dashboard & AI Business Consultant

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-red.svg)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-5.0%2B-purple.svg)](https://plotly.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite%203-lightgrey.svg)](https://www.sqlite.org/)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini%203.5%20Flash%20Lite-orange.svg)](https://aistudio.google.com/)
[![Data: 100% Synthetic](https://img.shields.io/badge/Data-100%25%20Synthetic-teal.svg)](#-synthetic-data--portfolio-disclaimer)

An end-to-end Healthcare Analytics and Business Intelligence Dashboard featuring interactive KPI monitoring, operational workload heatmaps, standardized Patient Satisfaction Index (IKM Permenpan RB No. 14/2017) tracking, and an integrated **AI Business Consultant** powered by Google Gemini (`gemini-3.5-flash-lite`).

Designed as an enterprise-grade portfolio demonstrating applied Data Analysis, UI/UX storytelling, database querying, and secure LLM integration for business decision-making.

---

## 🛡️ Synthetic Data & Portfolio Disclaimer

> **IMPORTANT NOTICE:**  
> This application is a **public portfolio demonstration**.  
> - **100% Synthetic Data:** All patient records, transaction amounts, diagnosis codes, prescription details, staff accounts, and survey respondents were generated from scratch using a deterministic generator (`scripts/generate_synthetic_data.py`, seed = 42).  
> - **Zero Confidential Data:** No real patients, healthcare workers, medical records, or production databases were used. All clinic branding and names are generic (*"Klinik Pratama Demo"*).  
> - **Safe LLM Architecture:** The integrated AI Consultant operates under strict read-only analytical reasoning. Free-form code execution (`PythonAstREPLTool` / `allow_dangerous_code`) is completely eliminated to guarantee security.

---

## 📌 Business Problem & Overview

Outpatient healthcare clinics handle complex, multidisciplinary operations across clinical services, medical laboratories, and pharmacy fulfillment. Clinic administrators and executive leaders frequently face critical operational challenges:

1. **Fragmented Revenue Visibility:** Difficulties in tracking MoM growth, identifying high-performing clinical service categories versus pharmacy contributions, and detecting underperforming units.
2. **Target Tracking Gaps:** Lack of automated comparison between monthly targets and actual realization across specialized service departments.
3. **Staffing and Patient Flow Inefficiencies:** Bottlenecks during peak registration hours and shifting patient acquisition trends (New vs. Returning patients).
4. **Public Satisfaction Compliance:** Translating patient survey feedback into actionable quality improvements compliant with the Indonesian Ministry of Administrative and Bureaucratic Reform standard (*Permenpan RB No. 14 Tahun 2017*).
5. **Slow Analytical Insights:** Executive leaders needing instant, natural-language executive summaries of clinical performance without writing complex SQL queries.

This dashboard solves these challenges by combining interactive visual analytics with a sandboxed, AI-powered business advisor.

---

## ✨ Key Features & Dashboard Modules

### 1. Executive Overview
- **High-Level KPIs:** Real-time summary cards for Total Revenue (Rp 3.68B / Rp 3,677,363,000), Total Visits (4,264 visits), Average Revenue per Visit, and Global Patient Satisfaction Index (84.04 / Grade B - "Baik").
- **Monthly Revenue Trajectory:** Multi-year trend analysis (2023–2025) with dynamic MoM growth indicators.
- **Revenue Distribution:** Breakdown comparing Clinical Services versus Pharmacy / Prescription revenue streams.
- **Top Growth Drivers:** Ranking of top revenue-generating clinical services.

### 2. Service & Product Performance (Performance Monitor)
- **Target vs. Realization Tracking:** Dynamic comparison of monthly budget targets against actual revenue across 6 key clinic service categories (Poli Umum, Poli Gigi & Mulut, Tindakan Medis & Bedah Minor, Kebidanan & KIA, Laboratorium Klinis, and Fisioterapi & Rehab).
- **Achievement Status:** Color-coded achievement percentages (Achieved ≥ 100% vs. Below Target).
- **Category Volume & Contribution:** Visualizing high-margin service clusters versus high-volume transactions.

### 3. Operations & Clinical Insights
- **Patient Acquisition Dynamics:** Analysis of New Patients (*Pasien Baru*) vs. Returning Patients (*Pasien Lama*).
- **Registration Time Heatmap:** Day-of-week by hour-of-day visit distribution heatmap to optimize medical staff shift scheduling.
- **Clinical Disease Prevalence (Top 10 ICD-10):** Diagnosis frequency tracking (e.g., ISPA, Hipertensi, Dispepsia, Diabetes Mellitus) to inform preventive health initiatives.
- **Pharmacy & Product Analytics:** Top 10 pharmaceutical items by quantity sold and top revenue-generating medications.

### 4. Patient Satisfaction Index (Indeks Kepuasan Masyarakat - IKM)
- **Regulatory Standard Compliance:** Built strictly according to Indonesian *Permenpan RB No. 14 / 2017*.
- **9 Core Service Elements:** Comprehensive evaluation across 16 surveyed questions mapped to 9 public service pillars (Persyaratan, Prosedur, Waktu Pelayanan, Biaya/Tarif, Produk Pelayanan, Kompetensi Pelaksana, Perilaku Pelaksana, Penanganan Pengaduan, Sarana dan Prasarana).
- **Weighted Conversion & Quality Grading:** Automated calculation of average scores, 25x conversion scale, and qualitative grade assignment (Grade A: "Sangat Baik" through Grade D: "Tidak Baik").
- **Respondent Demographics:** Breakdown of feedback across service units, age cohorts, and gender.

### 5. AI Business Consultant
- **Executive Advisory:** Powered by Google Gemini (`gemini-3.5-flash-lite`), translates complex data into structured executive summaries, root cause diagnoses, and operational recommendations.
- **Preset Quick Prompts:** Single-click exploration for Revenue trends, Underperforming units, ICD disease trends, and IKM improvement strategies.
- **Grounded Context:** AI prompts are augmented with verified, real-time aggregated metrics from the local database.
- **Security Guardrails:** Enforces input sanitization, rejects destructive prompt injection attempts, and operates purely via text reasoning (read-only).

---

## 🏗️ System Architecture & Data Flow

```text
┌────────────────────────────────────────────────────────┐
│                   User Web Browser                     │
│                (Streamlit UI / 8501)                   │
└──────────────────────────┬─────────────────────────────┘
                           │ Interactive UI Actions
                           ▼
┌────────────────────────────────────────────────────────┐
│               Streamlit Presentation Layer             │
│   ├── Login / Auth (Timing-Safe Password Verification) │
│   ├── Executive Overview Module                        │
│   ├── Service & Target Performance Module              │
│   ├── Operational & Clinical Heatmap Module            │
│   ├── IKM Satisfaction Module                          │
│   └── AI Business Consultant Module                    │
└──────────────┬──────────────────────────┬──────────────┘
               │ Analytical Queries       │ Dynamic Business Context
               ▼                          ▼
┌──────────────────────────────┐ ┌──────────────────────────────┐
│  SQL Engine & Dialect Layer  │ │  Safe AI Consultant Engine   │
│  ├── SQLite Dialect (UDFs)   │ │  ├── Input Guardrails        │
│  ├── DATE_FORMAT, YEAR, etc. │ │  ├── Error Sanitizer         │
│  └── queries.py Aggregations │ │  └── ChatGoogleGenerativeAI  │
└──────────────┬───────────────┘ └──────────────┬───────────────┘
               │                                │ API Prompt
               ▼                                ▼
┌──────────────────────────────┐ ┌──────────────────────────────┐
│     Local SQLite Database    │ │ Google Gemini 3.5 Flash Lite │
│    (data/demo_klinik.db)     │ │        (Free-Tier API)       │
└──────────────────────────────┘ └──────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend & UI** | [Streamlit](https://streamlit.io/), HTML5, Vanilla CSS |
| **Interactive Visualizations** | [Plotly Express & Graph Objects](https://plotly.com/python/) |
| **Data Manipulation & Analytics** | [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/) |
| **Database & ORM** | [SQLite 3](https://www.sqlite.org/), [SQLAlchemy](https://www.sqlalchemy.org/) |
| **Dialect Emulation** | Custom Python UDFs (`YEAR`, `MONTH`, `HOUR`, `DATE_FORMAT`, `REGEXP`) |
| **AI / Large Language Model** | [Google Gemini 3.5 Flash Lite](https://aistudio.google.com/) via [LangChain](https://www.langchain.com/) |
| **Synthetic Data Engine** | [Faker (id_ID)](https://faker.readthedocs.io/), deterministic random generator |
| **Testing & Quality Assurance** | Python `unittest` (21 unit and integration tests) |

---

## 🚀 Getting Started & Installation

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12
- Git
- A free Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

### 2. Clone the Repository
```bash
git clone https://github.com/Ariq04/Dashboard-Analitik-Terintegrasi-AI.git
cd Dashboard-Analitik-Terintegrasi-AI
```

### 3. Create and Activate Virtual Environment
- **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
- **Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to create `.env`:
```bash
cp .env.example .env
```
Edit `.env` and insert your Gemini API Key:
```ini
APP_ENV=demo
DB_TYPE=sqlite
SQLITE_DB_PATH=data/demo_klinik.db

# Insert your Google AI Studio API key below:
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

### 6. Generate the Synthetic Demo Database
Run the deterministic synthetic data generator to build `data/demo_klinik.db`:
```bash
python scripts/generate_synthetic_data.py
```
*Output confirmation:*
```text
[INFO] Memulai pembuatan dataset sintetis demo...
[SUCCESS] Berhasil membuat database demo di: .../data/demo_klinik.db
   - demo_users: 2 baris
   - demo_service_categories: 6 baris
   - demo_services: 18 baris
   - demo_visits: 4,264 baris
   - demo_visit_services: 5,098 baris
   - demo_visit_diagnoses: 4,264 baris
   - demo_prescriptions: 4,126 baris
   - demo_satisfaction_respondents: 420 baris
   - demo_satisfaction_elements: 16 baris
   - demo_satisfaction_summary: 1 baris
```

### 7. Launch the Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🔑 Demo Access Credentials

The application includes pre-configured demo user accounts verified in the synthetic database:

| Username / Email | Password | Role | Permissions |
| :--- | :--- | :--- | :--- |
| **`admin`** | **`demo123`** | Executive Administrator | Full Dashboard & AI Access |
| **`user`** | **`demo123`** | Clinical Analyst | Standard View Access |

*Note: Passwords in the local database use cryptographic hashing with timing-safe string comparison (`hmac.compare_digest`).*

---

## 🧪 Automated Testing Suite

The project includes 21 comprehensive automated tests covering schema integrity, business logic, authentication security, and AI guardrails:

```bash
python -m unittest discover -s tests -v
```

### Test Coverage Highlights:
- **`tests/test_synthetic_generator.py` (9 tests):** Verifies table creation, required columns, Foreign Key integrity, PK uniqueness, volume adequacy, IKM formula consistency, revenue aggregation equality, reproducibility, and external connection blocking.
- **`tests/test_dashboard_modules.py` (6 tests):** Validates Executive KPIs, Performance Monitor target realization, Operational metrics, IKM conversion math, authentication flow, and absence of confidential branding.
- **`tests/test_ai_assistant_security.py` (6 tests):** Validates prompt injection blocking, credential error sanitization, empty API key handling, absence of dangerous REPL code, and dynamic KPI calculation accuracy.

---

## 📂 Project Structure

```text
├── assets/                          # Static UI assets and generic logo
│   └── gambar1.png                  # Generic "Klinik Pratama" branding logo
├── data/                            # Local database directory (git-ignored)
│   ├── .gitkeep                     # Preserves directory structure
│   └── demo_klinik.db               # SQLite database (generated locally)
├── scripts/                         # Automation & database generation scripts
│   └── generate_synthetic_data.py   # Deterministic synthetic data generator
├── src/                             # Application source code
│   ├── agents/                      # AI Assistant core logic
│   │   ├── agent_brain.py           # Safe LLM invoker & security guardrails
│   │   └── promts.py                # System instructions & context builder
│   ├── auth/                        # Authentication & session management
│   │   ├── auth.py                  # User credential verification (SHA-256)
│   │   └── login.py                 # Streamlit login interface
│   ├── components/                  # Reusable UI components
│   │   └── sidebar.py               # Sidebar navigation & clinic info
│   ├── database/                    # Database connection & query layer
│   │   ├── connection.py            # SQLite engine & MySQL UDF emulator
│   │   └── queries.py               # Optimized SQL aggregation queries
│   └── modules/                     # Core analytical dashboard views
│       ├── ai_assistant.py          # AI Business Consultant interface
│       ├── executive.py             # Executive Overview & MoM trends
│       ├── ikm.py                   # Patient Satisfaction (Permenpan RB)
│       ├── operational.py           # Patient & clinical workload heatmaps
│       └── targets.py               # Target vs Realization performance
├── tests/                           # Automated test suite (21 unit tests)
│   ├── test_ai_assistant_security.py
│   ├── test_dashboard_modules.py
│   └── test_synthetic_generator.py
├── utils/                           # Helper utilities
│   └── ikm_helper.py                # IKM statistical conversion helpers
├── .env.example                     # Environment template (safe for public)
├── .gitignore                       # Git exclusions (.env, *.db, cache, logs)
├── app.py                           # Application entry point & router
├── requirements.txt                 # Clean Python dependencies
└── README.md                        # Portfolio documentation
```

---

## 🔒 Security & Privacy Practices

1. **Secret Redaction:** No API keys, passwords, or tokens are committed or displayed in UI error toasts.
2. **Strict Git Ignores:** `.env`, `.venv/`, `*.db`, `*.sqlite`, `*.log`, and cache folders are explicitly blocked from git tracking.
3. **No Direct Production Fallbacks:** If `APP_ENV=demo`, any attempt to connect to external MySQL production hosts is blocked at the engine constructor level.
4. **Read-Only AI Boundaries:** The AI Business Consultant does not possess SQL `DROP`, `DELETE`, `UPDATE`, or `INSERT` tools, and cannot execute OS shell commands or write local files.

---

## 📄 License & Attribution

This project is developed and maintained by **Ariq04** for portfolio, educational, and analytical demonstration purposes. All rights reserved. For reuse, adaptation, or business inquiries, please contact the author or provide proper attribution.
