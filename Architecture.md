# FraudDNA — System Architecture

## 1. Architecture Style
Use a **modular monolith** for the MVP.

Prioritize a reliable vertical slice over distributed-system complexity.

## 2. Stack

### Frontend
- Next.js 15
- TypeScript
- Tailwind CSS
- shadcn/ui
- Recharts
- React Flow

### Backend
- Python 3.12
- FastAPI
- Pydantic
- Uvicorn
- SQLAlchemy
- Alembic

### ML
- Pandas
- NumPy
- scikit-learn
- LightGBM
- SHAP

### Graph
- NetworkX

### Agentic AI
- LangGraph
- LLM API
- Structured Outputs / JSON Schema

### RAG
- PostgreSQL
- pgvector
- embedding API/model

### Quality
- pytest
- Ruff
- mypy
- ESLint
- Zod
- httpx

### DevOps
- Docker
- Docker Compose
- GitHub Actions
- Vercel for frontend
- managed container platform for backend
- managed PostgreSQL + pgvector

## 3. Repository Structure
```text
FraudDNA/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── hooks/
│   ├── types/
│   └── public/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── risk/
│   │   ├── graph/
│   │   ├── agent/
│   │   ├── rag/
│   │   ├── simulation/
│   │   ├── policy/
│   │   ├── audit/
│   │   └── main.py
│   └── tests/
├── ml/
│   ├── data/
│   ├── features/
│   ├── training/
│   ├── evaluation/
│   ├── models/
│   └── notebooks/
├── knowledge/
│   ├── policies/
│   ├── historical_cases/
│   └── guidelines/
├── scripts/
├── docs/
├── .github/
│   └── workflows/
├── artifacts/
│   ├── PRD.md
│   ├── Architecture.md
│   ├── Rules.md
│   ├── Phases.md
│   └── Design.md
├── docker-compose.yml
├── Dockerfile
├── README.md
└── .env.example
```

## 4. Runtime Flow
1. Transaction enters API.
2. Features are generated deterministically.
3. ML model produces risk score.
4. Graph service connects related entities.
5. Cluster analysis finds coordinated patterns.
6. SHAP explains model risk.
7. Investigation agent gathers evidence using allowlisted tools.
8. RAG retrieves policies/cases.
9. Deterministic policy engine selects ALLOW/REVIEW/HOLD.
10. Audit service records the result.
11. Simulation service evaluates alternative thresholds.

## 5. Agent Boundary
The agent can read investigation data but cannot:
- mutate financial records
- execute transactions
- block payments
- issue refunds
- modify policies

## 6. Data Model
Core entities:
- transactions
- customers
- devices
- ip_addresses
- payment_instruments
- merchants
- risk_scores
- fraud_clusters
- investigations
- evidence
- policies
- decisions
- audit_events

## 7. Graph
Nodes:
Customer, Transaction, Device, IP, Card, Merchant

Relationships include:
- Customer → Transaction
- Transaction → Device
- Transaction → IP
- Transaction → Card
- Transaction → Merchant
- Customer → Device
- Customer → IP

## 8. ML Pipeline
1. Load/generate data.
2. Validate schema.
3. Engineer features.
4. Split train/validation/held-out test.
5. Train LightGBM.
6. Select threshold using validation only.
7. Evaluate held-out test.
8. Persist model and evaluation metadata.
9. Generate SHAP explanations.

## 9. API
- POST /api/v1/transactions
- GET /api/v1/transactions/{id}
- GET /api/v1/risk/{id}
- GET /api/v1/clusters
- GET /api/v1/clusters/{id}
- POST /api/v1/investigations
- GET /api/v1/investigations/{id}
- POST /api/v1/simulations
- GET /api/v1/evaluation
- GET /api/v1/audit/{id}
- GET /api/v1/health

## 10. Security
- Secrets through environment variables.
- .env excluded from Git.
- LLM tools explicitly allowlisted.
- Agent step limit.
- External-call timeouts.
- Structured output validation.
- No direct DB mutation by LLM.
- No direct payment action by LLM.

## 11. Deployment
For the MVP:
- frontend → Vercel
- backend → Dockerized managed container
- database → managed PostgreSQL + pgvector

Avoid unnecessary infrastructure during the buildathon.
