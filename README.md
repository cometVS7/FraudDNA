# FraudDNA

> **AI-Powered Fraud Defense & Risk-Intelligence Platform**
> Uncovering coordinated fraud operations, hidden entity networks, and cross-transaction abuse.

---

## 📌 Project Status: Phase 0 (Foundation) Completed

> [!NOTE]
> **Phase 0 (Foundation)** is currently implemented. The repository contains the modular monolith scaffold, FastAPI backend with health monitoring, Next.js 15 frontend shell with Inter and JetBrains Mono typography, Docker Compose infrastructure (PostgreSQL + pgvector), and CI automation. **Phase 1+ functionality (ML models, relationship graphs, AI investigation agents, RAG, and policy simulation) is scheduled for subsequent phases.**

---

## 🏗️ Architecture & Stack

FraudDNA follows a **modular monolith** architecture designed for operational reliability, grounded reasoning, and deterministic risk control:

* **Backend**: Python 3.12, FastAPI, Pydantic v2, Uvicorn, SQLAlchemy, Alembic
* **Frontend**: Next.js 15 (App Router), TypeScript (Strict), Tailwind CSS, shadcn/ui foundation
* **Database & Vector**: PostgreSQL 16 + `pgvector`
* **ML & Explainability (Upcoming Phase 1)**: LightGBM, scikit-learn, SHAP
* **Graph Intelligence (Upcoming Phase 2)**: NetworkX
* **Agentic AI & RAG (Upcoming Phase 4 & 5)**: LangGraph, Structured Output Schemas, pgvector
* **Code Quality & CI**: pytest, pytest-asyncio, Ruff, mypy, ESLint, GitHub Actions

---

## 📁 Repository Structure

```text
FraudDNA/
├── frontend/                 # Next.js 15 TypeScript application
│   ├── app/                  # App Router pages & layout
│   ├── components/           # UI components
│   ├── lib/                  # Shared utilities
│   ├── hooks/                # Custom React hooks
│   ├── types/                # TypeScript type definitions
│   └── public/               # Static assets
├── backend/                  # FastAPI modular backend
│   ├── app/
│   │   ├── api/              # API router & v1 endpoints
│   │   ├── core/             # Configuration & security settings
│   │   ├── models/           # SQLAlchemy database models
│   │   ├── schemas/          # Pydantic v2 data contracts
│   │   ├── services/         # Application business logic
│   │   ├── risk/             # ML risk inference engine
│   │   ├── graph/            # FraudDNA entity relationship graph
│   │   ├── agent/            # LangGraph investigation agent
│   │   ├── rag/              # Policy & historical case RAG retrieval
│   │   ├── simulation/       # Risk threshold simulation engine
│   │   ├── policy/           # Deterministic policy engine (ALLOW/REVIEW/HOLD)
│   │   ├── audit/            # Immutable audit logging service
│   │   └── main.py           # FastAPI entrypoint
│   ├── tests/                # Backend test suite
│   ├── Dockerfile            # Container definition
│   └── pyproject.toml        # Python project configuration & linters
├── ml/                       # Machine learning workspace
│   ├── data/                 # Dataset storage
│   ├── features/             # Feature engineering pipelines
│   ├── training/             # Training scripts
│   ├── evaluation/           # Held-out evaluation & metrics
│   ├── models/               # Serialized model artifacts
│   └── notebooks/            # Exploratory research notebooks
├── knowledge/                # Curated RAG knowledge documents
│   ├── policies/             # Merchant risk policies
│   ├── historical_cases/     # Known fraud attack cases
│   └── guidelines/           # Escalation & risk guidelines
├── scripts/                  # Development & seeding scripts
├── docs/                     # Documentation & specifications
├── .github/                  # GitHub Actions CI workflows
├── docker-compose.yml        # Multi-container local orchestration
├── Dockerfile                # Root container definition
├── .env.example              # Environment variables template
├── PRD.md                    # Product Requirements Document (Source of Truth)
├── Architecture.md           # System Architecture (Source of Truth)
├── Rules.md                  # Engineering Rules (Source of Truth)
├── Phases.md                 # Implementation Roadmap (Source of Truth)
├── Design.md                 # Design System & UI Specs (Source of Truth)
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

* Python >= 3.12
* Node.js >= 20.x and npm >= 10.x
* Docker & Docker Compose

### 1. Clone & Configure Environment

```bash
# Clone the repository
git clone https://github.com/cometVS7/FraudDNA.git
cd FraudDNA

# Create local environment configuration
cp .env.example .env
```

---

### 2. Infrastructure Setup (Docker Compose)

Start the PostgreSQL + pgvector database:

```bash
docker compose up -d postgres
```

To run the complete stack in containers:

```bash
docker compose up --build
```

---

### 3. Backend Local Development

```bash
# Create and activate Python virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install backend in editable mode with development dependencies
pip install -e "backend[dev]"

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

* API Base URL: `http://localhost:8000/api/v1`
* Interactive OpenAPI Docs (Swagger): `http://localhost:8000/docs`
* Health Endpoint: `http://localhost:8000/api/v1/health`

---

### 4. Frontend Local Development

```bash
cd frontend
npm install
npm run dev
```

* Frontend Web App: `http://localhost:3000`

---

## 🧪 Quality Assurance & Testing

### Backend Checks

```bash
# Run pytest test suite
pytest backend/tests -v

# Run Ruff linter and formatter checks
ruff check backend
ruff format --check backend

# Run Mypy static type analysis
mypy backend/app
```

### Frontend Checks

```bash
cd frontend

# Run TypeScript type check
npm run type-check

# Run Next.js production build
npm run build
```

---

## 🛡️ Core Engineering Invariants

1. **AI Boundaries**: ML scores risk, Graph discovers connections, SHAP explains, RAG grounds, LangGraph investigates.
2. **Deterministic Financial Control**: Deterministic policies enforce `ALLOW`, `REVIEW`, and `HOLD`. LLMs never directly execute financial transactions or modify payment states.
3. **Honest Evaluation**: Strictly separated train/val/held-out test splits, zero label leakage, and monetary false-positive cost accounting.
4. **Light-First Analytics Design**: Clean, high-density fintech dashboard aesthetic powered by Inter and JetBrains Mono.
