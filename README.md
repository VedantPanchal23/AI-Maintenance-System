# AI-Based Predictive Maintenance System

## Zydus Pharma Oncology Pvt. Ltd.

A production-grade, AI-powered predictive maintenance platform for pharmaceutical manufacturing equipment. Uses **real-time sensor monitoring**, **GPU-accelerated deep learning**, and **multi-model ensemble predictions** to prevent unplanned downtime.

---

## Architecture

```
┌─────────────────┐    ┌─────────────────────────┐    ┌──────────────────┐
│   Next.js 14    │◄──►│     FastAPI Backend      │◄──►│  PostgreSQL 16   │
│   React + JSX   │    │  (async, multi-tenant)   │    │   (primary DB)   │
│   Tailwind CSS  │    │                           │    └──────────────────┘
│   Recharts      │    │  ┌─────────────────────┐ │    ┌──────────────────┐
└─────────────────┘    │  │   ML Engine          │ │◄──►│   Redis 7        │
                       │  │  • Random Forest     │ │    │  (cache/pubsub)  │
   WebSocket ◄────────►│  │  • XGBoost           │ │    └──────────────────┘
   (real-time)         │  │  • LightGBM          │ │
                       │  │  • PyTorch DNN (GPU) │ │
                       │  └─────────────────────┘ │
                       └─────────────────────────┘
                                   │
                           ┌───────┴───────┐
                           │  NVIDIA CUDA   │
                           │  RTX 3050 6GB  │
                           └───────────────┘
```

## Features

- **Real-Time Equipment Monitoring** — Live sensor data ingestion via WebSocket
- **Multi-Model ML Predictions** — Random Forest, XGBoost, LightGBM, PyTorch Deep NN
- **GPU-Accelerated Training** — CUDA 12.1 on NVIDIA RTX 3050 (6GB VRAM)
- **Intelligent Alerting** — Severity-based alerts with auto-escalation
- **Multi-Tenant Architecture** — Organization-scoped data isolation
- **Role-Based Access Control** — Admin, Engineer, Viewer roles with JWT auth
- **Equipment Simulation** — Realistic degradation models for testing
- **Interactive Dashboard** — Rich charts, gauges, and real-time feeds

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, Tailwind CSS, Recharts, Zustand |
| Backend | FastAPI 0.109, Python 3.11, SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16, Redis 7 |
| ML/AI | PyTorch (CUDA), scikit-learn, XGBoost, LightGBM |
| Auth | JWT (HS256), bcrypt, RBAC |
| DevOps | Docker, Docker Compose |

## ML Models

| Model | Type | Device | Notes |
|-------|------|--------|-------|
| Random Forest | Ensemble | CPU | 300 trees, balanced class weights |
| XGBoost | Gradient Boosting | CPU | 500 rounds, regularized |
| LightGBM | Gradient Boosting | CPU | 500 rounds, leaf-wise |
| Deep Neural Network | PyTorch DNN | **GPU (CUDA)** | 256→128→64→32, BatchNorm, Dropout, early stopping |

The DNN architecture:
- 4 hidden layers: 256 → 128 → 64 → 32
- BatchNorm + ReLU + Dropout after each layer
- Class-weighted BCE loss for imbalanced data
- AdamW optimizer with ReduceLROnPlateau scheduler
- Early stopping on validation F1 score

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16
- Redis 7
- NVIDIA GPU with CUDA 12.1 (optional, for GPU training)

### 1. Backend Setup

```bash
cd backend

# Option A: Use setup script (Windows)
setup_env.bat

# Option B: Manual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt

# Install PyTorch with CUDA 12.1 (for RTX 3050)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### 2. Database Setup

```bash
# Create PostgreSQL database
createdb predictive_maintenance

# Copy environment file
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
alembic upgrade head

# Seed demo data
python -m scripts.seed_database
```

### 3. Train ML Models

```bash
# Train all models (uses GPU for neural network)
python -m scripts.train_models --algorithm all

# Train specific model
python -m scripts.train_models --algorithm neural_network_deep
python -m scripts.train_models --algorithm xgboost
```

### 4. Start Backend

```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 6. Access the Application

- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Login**: admin@zydus.com / admin123

---

## Docker Deployment

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

---

## Project Structure

```
AI Maintenance System/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # REST API endpoints
│   │   │   ├── endpoints/    # auth, equipment, sensors, predictions, alerts, analytics, ml_admin
│   │   │   ├── schemas.py    # Pydantic request/response models
│   │   │   ├── deps.py       # Auth & pagination dependencies
│   │   │   └── router.py     # Route aggregator
│   │   ├── core/             # Security, logging, exceptions
│   │   ├── db/               # Database session, base models, ORM models
│   │   │   └── models/       # organization, equipment, sensor, prediction, alert
│   │   ├── middleware/        # Tenant isolation, request logging
│   │   ├── ml/               # ML pipeline
│   │   │   ├── preprocessing.py   # Data loading & synthetic generation
│   │   │   ├── features.py        # Feature engineering (20+ features)
│   │   │   ├── training.py        # Training pipeline (RF, XGB, LGBM, PyTorch DNN)
│   │   │   └── inference.py       # Production inference service
│   │   ├── services/          # Alert service, simulation engine, WebSocket
│   │   ├── config.py          # Pydantic Settings
│   │   └── main.py           # FastAPI application factory
│   ├── alembic/              # Database migrations
│   ├── scripts/              # seed_database, train_models
│   ├── setup_env.bat         # Windows venv + CUDA setup
│   ├── setup_env.sh          # Linux/Mac venv + CUDA setup
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js App Router pages (JSX)
│   │   │   ├── dashboard/    # Main dashboard with live charts
│   │   │   ├── equipment/    # Equipment list & detail views
│   │   │   ├── alerts/       # Alert management
│   │   │   ├── analytics/    # Advanced analytics charts
│   │   │   ├── ml-admin/     # ML model training UI
│   │   │   ├── maintenance/  # Maintenance tracking
│   │   │   ├── settings/     # User & system settings
│   │   │   └── login/        # Authentication
│   │   ├── components/       # Reusable UI components
│   │   └── lib/              # API client, Zustand store, utils
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── ARCHITECTURE.md
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | User login |
| POST | `/api/v1/auth/register` | User registration |
| GET | `/api/v1/equipment` | List equipment (paginated) |
| GET | `/api/v1/equipment/{id}` | Equipment details |
| POST | `/api/v1/sensors/ingest` | Ingest sensor reading |
| POST | `/api/v1/predictions/predict` | Run ML prediction |
| GET | `/api/v1/alerts` | List alerts |
| GET | `/api/v1/analytics/dashboard` | Dashboard summary |
| POST | `/api/v1/ml/train` | Train an ML model |
| WS | `/ws/sensors` | Real-time sensor stream |

Full API docs available at `http://localhost:8000/docs` (Swagger UI).

---

## Environment Variables

See `.env.example` for all configurable settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `JWT_SECRET_KEY` | — | Secret for JWT signing |
| `ML_MODEL_DIR` | `./ml_models` | Where trained models are saved |
| `ML_DEFAULT_MODEL` | `xgboost` | Default algorithm for inference |
| `ML_PREDICTION_THRESHOLD` | `0.5` | Failure probability threshold |

---

## License

Proprietary — Zydus Pharma Oncology Pvt. Ltd.
