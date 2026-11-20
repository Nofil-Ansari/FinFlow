# FinanceFlow — AI-Powered Personal Finance Advisor & BI Analytics

> An intelligent, localized personal finance management ecosystem built for the Pakistani economy. Combines a full multi-account ledger with an ultra-fast LLM financial advisor powered by Groq, a Retrieval-Augmented Generation (RAG) engine grounded in verified Pakistani statutory knowledge, predictive ML spending analytics, real-time WebSocket ledger sync,   and dual-format executive reporting.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.13+](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![Flask: 3.1.1](https://img.shields.io/badge/Flask-3.1.1-green.svg)](https://flask.palletsprojects.com/)
[![Tests: 48 Passing](https://img.shields.io/badge/Tests-48%20Passing-brightgreen.svg)]()
[![CI: GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-blue.svg)](.github/workflows/ci.yml)
[![Milestone: v2.1](https://img.shields.io/badge/Milestone-v2.1%20RAG%20Engine-orange.svg)](.gsd/ROADMAP.md)

---

## 🏗 System Architecture

The platform is organized into four distinct layers: a Flask-based web layer, an intelligence and service layer, an external integrations layer, and a data persistence layer.

```mermaid
graph TD
    User([User / Browser])

    subgraph WebLayer["Flask Web Layer (Blueprints)"]
        Auth[Auth & Security]
        Dashboard[Overview Dashboard]
        Accounts[Account Lifecycle]
        Transactions[Ledger & CSV Import]
        Budgets[Budgets & Thresholds]
        Savings[Savings Goals]
        Investments[Investments]
        Recurring[Recurring Transactions]
        AIAdvisor["AI Command Center /ai"]
        Reports["Reporting & Analytics /reports"]
        API["REST API /api/v1"]
    end

    subgraph ServiceLayer["Intelligence & Service Layer"]
        GroqMW["GroqMiddleware\n(GPT-OSS 120B / Qwen3.8-27B / Compound)"]
        Recommender["Pakistani Product Substitutions\n(recommender.py)"]
        MLPredictor["ML Spending Predictor\n(GradientBoostingRegressor — 15 features)"]
        Leakage["Subscription Leakage Scanner\n(28-32 day cadence & price creep >5%)"]
        LedgerStream["Ledger Stream Service\n(Flask-SocketIO /ws/ledger)"]
        PDFExport["PDF Engine (ReportLab)"]
        ExcelExport["Excel Engine (OpenPyXL)"]
        Crypto["Fernet Credential Manager"]
        AuditLog["Audit Log Service"]
        TransferSvc["Fund Transfer Service\n(Atomic, FOR UPDATE lock)"]
        subgraph RAGLayer["RAG Knowledge Engine (v2.1)"]
            Loader["Document Loader & Chunker\n(Markdown + JSON corpus)"]
            Embedder["768-dim Embedding Engine\n(Gemini gemini-embedding-001 + TF-IDF fallback)"]
            Cache["Two-Tier Cache\n(L1: Redis | L2: Disk JSON)"]
            VectorStore["Dual-Mode Vector Store\n(NumPy local | pgvector PostgreSQL)"]
        end
    end

    subgraph External["External Integrations"]
        GroqAPI[("Groq API Cloud")]
        GeminiAPI[("Google Gemini API\n(text-embedding-001)")]
        OXR[("Open Exchange Rates")]
        GoogleOAuth[("Google OAuth 2.0")]
        BIConsumers[("Excel / Sheets / BigQuery")]
        Redis[("Redis Cache Server")]
    end

    subgraph StorageLayer["Data Layer (SQLAlchemy ORM)"]
        DB[("SQLite (dev)\ninstance/finance_tracker.db")]
        PG[("PostgreSQL + pgvector (prod)\nSupabase / Cloud Run")]
    end

    User --> WebLayer
    WebLayer --> ServiceLayer
    ServiceLayer --> StorageLayer

    GroqMW <--> GroqAPI
    Embedder <--> GeminiAPI
    Cache <--> Redis
    Reports --> PDFExport
    Reports --> ExcelExport
    Transactions --> LedgerStream
    LedgerStream -.->|"WebSocket /ws/ledger"| BIConsumers
    Auth --> GoogleOAuth
    Dashboard --> OXR

    Loader --> Embedder
    Embedder --> Cache
    Cache --> VectorStore
    VectorStore --> GroqMW
```

---

## 🚀 Key Features

### 1. Complete Ledger & Multi-Account Wealth Tracking

Full double-entry ledger supporting Checking, Savings, Cash, and digital wallets (JazzCash, Easypaisa, Nayapay, Sadapay). Transactions are categorized, tagged, and soft-deleted. Multi-currency support with live conversion via Open Exchange Rates.

### 2. AI Financial Advisor with Groq LLM

High-speed conversational AI using five supported models over the Groq API:

| Model | Badge | Strength |
| :--- | :---: | :--- |
| `openai/gpt-oss-120b` | **Default** | Deep reasoning & rich Pakistani market analysis |
| `qwen/qwen3.8-27b` | Fast & Smart | Financial budgeting and mathematical accuracy |
| `groq/compound` | Compound | Multi-step compound reasoning at real-time speed |
| `groq/compound-mini` | Ultra Fast | Ultra-low latency for rapid, simple Q&A |
| `openai/gpt-oss-20b` | Lightweight | Efficient 20B model for quick financial queries |

Credentials are encrypted at rest using **AES-128-CBC Fernet**. Users bring their own Groq API keys through a live-ping verification modal.

### 3. RAG Knowledge Engine — Grounded in Pakistani Statute (v2.1)

The advisor is grounded in a curated, versioned knowledge corpus of verified Pakistani financial regulations, eliminating hallucinated tax rates and investment figures:

- **FBR Income Tax 2024–2025**: Complete salaried and non-salaried slabs, withholding tax (WHT) rates for filers vs. non-filers, and high-income surcharge rules.
- **SBP Banking Regulations**: State Bank monetary policy, banking product rules, and regulatory compliance guidelines.
- **National Savings Schemes**: Rates and terms for all active NS instruments.
- **Zakat & Nisab Rules**: Current nisab thresholds, Zakat calculation methodology, and declaration procedures.
- **Pakistani Consumer Substitutions**: Local alternatives for transportation, digital streaming, healthcare, and dining.

The RAG pipeline uses a **768-dimensional embedding engine** (Google Gemini `gemini-embedding-001` with a zero-dependency local TF-IDF fallback), a **two-tier Redis L1 + Disk L2 cache**, and a **dual-mode vector store** (NumPy for local dev, PostgreSQL `pgvector` for production).

### 4. Pakistani Market Context & Financial Health Scoring

Financial health scoring (0–100) with automated category spending flags, localized inflation guidance, emergency fund recommendations, and a rule-based Pakistani product substitution engine that maps detected merchant patterns to affordable local alternatives.

### 5. ML Predictive Spending Analytics

A 15-feature `GradientBoostingRegressor` pipeline with chronological 80/20 split (preventing temporal data leakage) projects end-of-month expenditure per category against actual income. Features include categorical encoding, Fourier seasonality components (`month_sin`, `month_cos`), 3-month rolling statistics, lag features, z-score anomalies, and category share momentum.

### 6. Real-Time WebSocket Ledger Sync

`/ws/ledger` (Flask-SocketIO) broadcasts authenticated live transaction lifecycle events (create, update, delete) to connected web clients, Microsoft Excel Power Query add-ins, Google Sheets, and BigQuery streaming ingest pipelines.

### 7. Executive Dual-Format Reporting

One-click export of comprehensive monthly statements:

- **ReportLab PDF**: High-resolution reports with income/expense breakdowns, budget adherence, and savings progress.
- **OpenPyXL Excel**: Power Query-ready spreadsheets compatible with downstream BI pipelines.

### 8. Subscription Leakage Scanner

Heuristic detection of 28–32 day billing cycles identifying zombie subscriptions and silent price creep (>5%). Returns `active_subscriptions`, `price_creeps`, estimated `potential_annual_leakage_pkr`, and `total_monthly_commitment_pkr`.

### 9. Google OAuth & Secure Authentication

Passwordless sign-in via Google OAuth 2.0 (Authlib) alongside traditional email/password registration with CSRF protection (Flask-WTF), session management (Flask-Login), and transactional email notifications (Flask-Mail).

---

## 🔄 Core Workflows

### Fund Transfer Flow

```mermaid
flowchart TD
    A([User initiates transfer]) --> B{Valid accounts?}
    B -->|No| Z1[Raise ValueError]
    B -->|Yes| C["Lock both accounts\nSELECT FOR UPDATE\nasc by account_id"]
    C --> D{Sufficient balance\nafter lock?}
    D -->|No| Z2[Raise InsufficientFunds]
    D -->|Yes| E[Debit source account\nTransaction: expense]
    E --> F[Credit destination account\nTransaction: income]
    F --> G[Record Transfer row]
    G --> H[Write Audit Log]
    H --> I[db.session.commit]
    I --> J([Transfer complete])
```

### RAG Query Pipeline (v2.1)

```mermaid
flowchart LR
    Q([User question\nin AI advisor]) --> QE[Generate query embedding\n768-dim Gemini / TF-IDF fallback]
    QE --> L1{L1 Redis cache\nhit?}
    L1 -->|Yes| VS
    L1 -->|No| L2{L2 Disk cache\nhit?}
    L2 -->|Yes| PW[Promote to Redis L1] --> VS
    L2 -->|No| EMB[Call Gemini API\nor local TF-IDF] --> SC[SHA-256 hash\n→ store L2 & L1] --> VS
    VS["Vector Store\ncosine similarity search\n(NumPy local / pgvector prod)"] --> RR[Re-rank top-k chunks\nby score threshold]
    RR --> PA[Prompt augmentation\nGroq system prompt\n+ retrieved context]
    PA --> GROQ[("Groq API\nGPT-OSS 120B / Qwen 3.8 27B")]
    GROQ --> R([Grounded response\nwith source citations])
```

### Account Balance Computation

```mermaid
flowchart LR
    A([balance property called]) --> B["Query transactions\nWHERE account_id = X\nAND is_deleted = FALSE"]
    B --> C{transaction_type}
    C -->|income| D[+amount]
    C -->|expense| E[-amount]
    D --> F["COALESCE(SUM, 0)"]
    E --> F
    F --> G([Return live balance\nPKR — same currency assumed])
```

---

## 📂 Repository Structure

```
Project/
├── .github/
│   └── workflows/
│       └── ci.yml                      # GitHub Actions CI: lint, format, test (Py 3.10–3.12)
├── .gsd/                               # Project management & memory (GSD framework)
│   ├── ARCHITECTURE.md                 # Detailed system component mapping
│   ├── ROADMAP.md                      # Active milestone roadmap (v2.1 RAG Engine)
│   ├── SPEC.md                         # Finalized project specification
│   ├── STACK.md                        # Complete technology inventory
│   ├── STATE.md                        # Live project state & current phase
│   ├── TODO.md                         # Backlog & completed items
│   └── phases/
│       ├── 01-rag/01-PLAN.md           # Phase 1: Corpus curation & ingestion pipeline
│       └── 02-rag/
│           ├── 01-PLAN.md              # Phase 2: Embedding engine & vector store
│           └── 02-SUMMARY.md          # Phase 2 completion summary & verification
├── finance_app/
│   ├── app/
│   │   ├── __init__.py                 # Application factory (create_app)
│   │   ├── extensions.py              # Flask extensions (db, migrate, login, csrf, mail, oauth, socketio)
│   │   ├── config.py                  # Config classes (Development, Production, Testing)
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── account.py             # balance hybrid property (soft-delete aware, same-currency)
│   │   │   ├── category.py
│   │   │   ├── transaction.py         # TransactionTag with UniqueConstraint(transaction_id, tag_id)
│   │   │   ├── transfer.py
│   │   │   ├── budget.py
│   │   │   ├── savings_goal.py
│   │   │   ├── investment.py
│   │   │   ├── recurring.py
│   │   │   ├── tag.py
│   │   │   ├── financial_profile.py
│   │   │   ├── ai_chat.py
│   │   │   ├── notification.py
│   │   │   ├── audit_log.py
│   │   │   └── rag_chunk.py           # RagKnowledgeChunk — pgvector embedding storage
│   │   ├── services/
│   │   │   ├── groq_middleware.py     # Groq API middleware, model routing, context injection
│   │   │   ├── groq_client.py         # Low-level Groq API client & history management
│   │   │   ├── recommender.py         # Pakistani product substitution engine
│   │   │   ├── spending_predictor.py  # GradientBoosting ML predictor (15 features)
│   │   │   ├── subscription_leakage.py # 28-32 day recurring billing scanner
│   │   │   ├── ledger_stream.py       # WebSocket namespace (/ws/ledger)
│   │   │   ├── pdf_export.py          # ReportLab PDF statement generator
│   │   │   ├── excel_export.py        # OpenPyXL Excel statement generator
│   │   │   ├── balance.py             # get_balance() service
│   │   │   ├── transfer.py            # fund_transfer() — atomic, FOR UPDATE locked
│   │   │   ├── budget.py              # Budget status & alert engine
│   │   │   ├── savings.py             # Savings goal contribution & progress
│   │   │   ├── auto_categorizer.py    # Transaction auto-categorization
│   │   │   ├── ai_alerts.py           # Overspending detection & alert metadata
│   │   │   ├── audit.py               # Audit log service
│   │   │   └── rag/                   # RAG Knowledge Engine (v2.1)
│   │   │       ├── __init__.py
│   │   │       ├── models.py          # KnowledgeDocument, KnowledgeChunk dataclasses
│   │   │       ├── loader.py          # Markdown frontmatter & JSON document loader
│   │   │       ├── chunker.py         # MarkdownHeaderChunker — semantic section splitter
│   │   │       ├── pipeline.py        # CorpusPipeline — end-to-end ingestion orchestrator
│   │   │       ├── embeddings.py      # LocalTfidfEmbedding, GeminiEmbeddingService,
│   │   │       │                      #   DiskCache, TwoTierCachedEmbeddingService
│   │   │       └── vector_store.py    # LocalVectorStore (NumPy), PgVectorStore (pgvector),
│   │   │                              #   get_vector_store() factory
│   │   ├── auth/                      # Authentication blueprint (login, register, Google OAuth)
│   │   ├── dashboard/                 # Overview dashboard blueprint
│   │   ├── transactions/              # Ledger, CSV import & fund transfer blueprint
│   │   ├── accounts/                  # Account lifecycle management blueprint
│   │   ├── budgets/                   # Monthly budget limit tracking blueprint
│   │   ├── savings/                   # Savings goal tracking blueprint
│   │   ├── investments/               # Investment portfolio blueprint
│   │   ├── recurring/                 # Recurring transaction management blueprint
│   │   ├── tags/                      # Transaction tag blueprint
│   │   ├── imports/                   # CSV bulk import blueprint
│   │   ├── reports/                   # Analytics, heatmaps & export blueprint
│   │   ├── api/                       # REST API blueprint (/api/v1)
│   │   ├── ai/                        # AI advisor command center blueprint
│   │   ├── static/                    # CSS, JavaScript & client assets
│   │   └── templates/                 # Jinja2 HTML templates
│   ├── data/
│   │   └── knowledge/
│   │       ├── raw/                   # Curated Pakistani financial knowledge corpus
│   │       │   ├── 01_fbr_income_tax_2024_2025.md
│   │       │   ├── 02_national_savings_schemes_rates.md
│   │       │   ├── 03_sbp_banking_regulations_monetary.md
│   │       │   ├── 04_zakat_nisab_and_declarations.md
│   │       │   └── 05_pakistan_consumer_substitutions.json
│   │       └── processed/             # Chunked corpus, embeddings cache, vector index
│   │           ├── chunks.jsonl
│   │           ├── manifest.json      # 8 docs, 30 chunks across 5 categories
│   │           ├── vector_index.json  # Local NumPy cosine index
│   │           └── cache/
│   │               └── embeddings_cache.json  # L2 disk embedding cache
│   ├── tests/
│   │   ├── test_finance_app.py        # Core ledger suite (transfer, balance, budget, savings)
│   │   ├── test_ai_advisor.py         # AI advisor suite (Groq, recommender, ML predictor)
│   │   └── test_rag_vector_store.py   # RAG suite (embeddings, caching, vector search)
│   ├── manage_rag.py                  # RAG CLI management tool (ingest, embed, query, warm-cache)
│   ├── run.py                         # Application bootstrap runner
│   └── requirements.txt               # Production & development dependencies
├── Stacked markdowns/                 # Implementation plans & walkthrough documentation
├── LICENSE                            # MIT License
└── README.md                          # This file
```

---

## 🛠 Quickstart Guide

### 1. Prerequisites

- Python 3.13+
- Git
- *(Optional)* Redis server for L1 embedding cache
- *(Optional)* PostgreSQL with `pgvector` extension for production vector storage

### 2. Installation & Virtual Environment Setup

```powershell
# Clone the repository
git clone https://github.com/Mujtaba-Zahid/Project.git
cd Project/finance_app

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux / macOS

# Install all dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file inside `finance_app/`:

```env
# --- Core Flask ---
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# --- Database ---
# SQLite (default, local development)
DATABASE_URL=sqlite:///instance/finance_tracker.db
# PostgreSQL + pgvector (production)
# DATABASE_URL=postgresql://user:password@host:5432/financeflow

# --- Groq AI Advisor ---
GROQ_API_KEY=optional_fallback_groq_api_key   # Users can also set their own key via UI

# --- Google OAuth ---
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# --- Currency Conversion ---
OXR_APP_ID=optional_open_exchange_rates_key

# --- Credential Encryption ---
ENCRYPTION_KEY=32_urlsafe_base64_encryption_key

# --- RAG Engine (v2.1) ---
GEMINI_API_KEY=your_google_gemini_api_key     # For 768-dim embeddings (falls back to local TF-IDF if unset)
REDIS_URL=redis://localhost:6379/0            # Optional: L1 Redis embedding cache (falls back to disk cache)
```

### 4. Run the Application

```powershell
cd finance_app
python run.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## 🧠 RAG Knowledge Engine — CLI Reference

The `manage_rag.py` CLI manages the Pakistani financial knowledge corpus and vector index:

```powershell
cd finance_app

# Step 1: Ingest & chunk the raw knowledge corpus
python manage_rag.py ingest

# Step 2: View corpus statistics (documents, chunks, categories)
python manage_rag.py stats

# Step 3: Generate embeddings & build the vector index
python manage_rag.py embed

# Step 4: Warm Redis L1 cache from disk (optional, for production)
python manage_rag.py warm-cache

# Step 5: Run a semantic search query
python manage_rag.py query "tax slab for salaried income 1.5 million PKR"
python manage_rag.py query "National Savings Certificate current profit rate"
python manage_rag.py query "Zakat calculation on gold holdings"
```

**Current corpus**: 8 documents → 30 chunks across 5 categories: Taxation, Investments, Banking, Zakat & Charity, Consumer Substitutions.

---

## 🧪 Running the Test Suite

```powershell
cd finance_app
$env:PYTHONPATH = "."
python -m unittest discover -s tests -p "test_*.py"
```

**Current test status: 48/48 tests passing.**

| Suite | File | Tests | Coverage |
| :--- | :--- | :---: | :--- |
| Core Ledger | `test_finance_app.py` | 23 | Accounts, transactions, transfer atomicity, budgets, savings goals |
| AI Advisor | `test_ai_advisor.py` | 20 | Groq middleware, recommender, auto-categorizer, spending predictor, overspending alerts |
| RAG Engine | `test_rag_vector_store.py` | 5 | 768-dim normalization, L2 disk cache, Redis degradation, vector search ranking |

---

## 🔁 CI/CD Pipeline

GitHub Actions runs on every push to `main` and every pull request:

```mermaid
flowchart LR
    PR([Push / Pull Request\nto main]) --> TRG[Trigger GitHub Actions]
    TRG --> M["Matrix Build\nPython 3.10 | 3.11 | 3.12"]
    M --> CO[Checkout Code\n& Restore Pip Cache]
    CO --> INS[Install requirements.txt\n+ flake8 + black]
    INS --> FL["Flake8\nSyntax & Error Check\n(E9, F63, F7, F82)"]
    FL --> BK["Black\nCode Formatting Check"]
    BK --> TS["python -m unittest discover\n-s tests -t .\n(FLASK_ENV=testing)"]
    TS --> PASS([Pass / Fail Report])
```

---

## 🗺 Milestone Roadmap

```mermaid
flowchart TD
    V10["✅ v1.0 — Core Platform\n(Shipped)"]
    V10 --> V11["✅ Groq AI Integration\n(LLM_pilot_branch → main)"]
    V11 --> V12["✅ Phase 4 — Advanced Analytics\nReporting, WebSocket Sync\n(Shipped)"]
    V12 --> V20["⏸️ v2.0 — Production Deployment\nGCP Cloud Run + Supabase + Redis\n(Paused)"]
    V12 --> V21["🚀 v2.1 — RAG Knowledge Engine\n(Active Milestone)"]

    subgraph RAGPhases["Milestone v2.1 Phases"]
        P1["✅ Phase 1\nCorpus Curation & Ingestion Pipeline\n(Completed 2026-11-10)"]
        P2["✅ Phase 2\nEmbedding Engine, Dual-Mode Vector Store\n& Two-Tier Redis Cache\n(Completed 2026-11-10)"]
        P3["🔜 Phase 3\nSemantic Retrieval & Re-ranking Layer\n(Next Up)"]
        P4["⏳ Phase 4\nGroq Advisor RAG Integration\n& Prompt Synthesis\n(Queued)"]
        P5["⏳ Phase 5\nUI Citation Display, Verification\n& Benchmark Testing\n(Queued)"]
        P1 --> P2 --> P3 --> P4 --> P5
    end

    V21 --> RAGPhases
```

---

## 📸 Application Walkthrough

### 1. Executive Dashboard & Financial Health Overview

Live net-worth tracking, multi-account liquid balances, cash flow metrics, and localized ML spending predictions.

![Executive Dashboard Overview](docs/assets/screenshots/dashboard_overview.png)

---

### 2. AI Financial Advisor & Pakistani Localization

Financial health scoring (0–100), localized inflation guidance, emergency fund recommendations, and Pakistani product substitution engine — now grounded in verified FBR, SBP, and National Savings data via RAG.

![AI Advisor Command Center](docs/assets/screenshots/ai_advisor_hub.png)

---

### 3. High-Speed LLM Chat via Groq

Direct multi-turn conversational advice tailored to the Pakistani macroeconomic context, with actionable asset allocation and inflation hedging strategies.

![Live AI Chat Response](docs/assets/screenshots/groq_chat_response.png)

---

### 4. Zero-Friction BYO-Key Modal & Fernet Encryption

Users insert and verify their personal Groq API keys with live ping diagnostics. Credentials are encrypted at rest using AES-128-CBC Fernet.

![Groq API Key Configuration Modal](docs/assets/screenshots/groq_key_config.png)

---

### 5. Multi-Account Portfolio Management

Track bank accounts (Meezan, HBL, Nayapay, Sadapay), physical cash wallets, credit lines, and real-time PKR balances.

![Account Portfolio Management](docs/assets/screenshots/accounts_portfolio.png)

---

### 6. Analytics, Monthly Reports & Dual-Format Export

Comprehensive monthly income vs. expense breakdown, subscription leakage scanner, and single-click in-memory ReportLab PDF and OpenPyXL Excel statement exports.

![Monthly Financial Reporting](docs/assets/screenshots/monthly_reporting.png)

---

## 🛡 Security Design

| Concern | Implementation |
| :--- | :--- |
| Groq API Key Storage | Fernet AES-128-CBC encryption at rest in database |
| Session Management | Flask-Login with server-side session cookies |
| Form Security | Flask-WTF CSRF protection on all state-changing forms |
| Password Hashing | Werkzeug `generate_password_hash` / `check_password_hash` |
| OAuth | Authlib + Google OAuth 2.0 with PKCE |
| SQL Injection | SQLAlchemy ORM with parameterized queries throughout |
| Soft Deletes | `is_deleted` + `deleted_at` flags on all sensitive models (User, Account, Transaction, SavingsGoal) |
| Transfer Atomicity | `SELECT ... FOR UPDATE` with deterministic ascending-ID lock ordering to prevent deadlocks |

---

## 📦 Technology Stack

| Layer | Technology | Version |
| :--- | :--- | :---: |
| Runtime | Python | 3.13+ |
| Web Framework | Flask | 3.1.1 |
| ORM | SQLAlchemy / Flask-SQLAlchemy | 2.0.36 / 3.1.1 |
| Database (Dev) | SQLite | 3.x |
| Database (Prod) | PostgreSQL + pgvector | — |
| Migrations | Flask-Migrate | 4.1.0 |
| Auth | Flask-Login + Authlib | 0.6.3 / 1.4.1 |
| Forms | Flask-WTF | 1.2.2 |
| Real-Time | Flask-SocketIO + simple-websocket | ≥5.3.6 / ≥1.0.0 |
| ML | scikit-learn (GradientBoostingRegressor) | ≥1.3.0 |
| Data Processing | pandas + numpy | ≥2.0.0 / ≥1.24.0 |
| PDF Export | ReportLab | ≥4.1.0 |
| Excel Export | OpenPyXL | ≥3.1.2 |
| Embeddings | Google Gemini `gemini-embedding-001` | — |
| Vector DB (Dev) | NumPy + JSON | — |
| Vector DB (Prod) | pgvector | 0.5.1 |
| Embedding Cache L1 | Redis | ≥5.0.0 |
| LLM Provider | Groq API | — |
| CI | GitHub Actions | — |
| WSGI (Prod) | Gunicorn | 23.0.0 |

---

## 📜 License

Distributed under the [MIT License](LICENSE). Copyright (c) 2026 Mujtaba Zahid.
