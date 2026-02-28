# AI-Based Predictive Maintenance System
## Architecture Document

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Next.js Dashboard (React)                                          │   │
│  │  - Real-time monitoring  - Alert management  - Analytics            │   │
│  │  - Equipment overview    - Maintenance scheduling                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ HTTPS / WebSocket
┌───────────────────────────────▼─────────────────────────────────────────────┐
│                           API GATEWAY LAYER                                │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Application                                                 │  │
│  │  - JWT Auth Middleware    - Rate Limiting    - Request Validation    │  │
│  │  - Tenant Isolation       - CORS             - Structured Logging   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└──────┬──────────┬──────────┬──────────┬──────────┬──────────┬───────────────┘
       │          │          │          │          │          │
┌──────▼───┐ ┌───▼────┐ ┌──▼───┐ ┌───▼────┐ ┌──▼───┐ ┌───▼──────┐
│Equipment │ │Predict │ │Alert │ │Sensor  │ │Auth  │ │Analytics │
│Service   │ │Service │ │Service│ │Service │ │Service│ │Service   │
└──────┬───┘ └───┬────┘ └──┬───┘ └───┬────┘ └──┬───┘ └───┬──────┘
       │         │         │         │         │         │
┌──────▼─────────▼─────────▼─────────▼─────────▼─────────▼───────────────────┐
│                          DATA LAYER                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                     │
│  │  PostgreSQL   │  │  Redis Cache │  │  ML Model    │                     │
│  │  (Primary DB) │  │  (Sessions/  │  │  Registry    │                     │
│  │              │  │   Pub-Sub)   │  │  (File Store)│                     │
│  └──────────────┘  └──────────────┘  └──────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────────┐
│                       ML PIPELINE LAYER                                    │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│  │ Data       │  │ Feature    │  │ Model      │  │ Inference  │          │
│  │ Ingestion  │──▶│ Engineering│──▶│ Training   │──▶│ Service    │          │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘          │
│  ┌────────────┐  ┌────────────┐                                           │
│  │ Model      │  │ Experiment │                                           │
│  │ Versioning │  │ Tracking   │                                           │
│  └────────────┘  └────────────┘                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow:
1. Sensor data streams from equipment → Ingestion Service → PostgreSQL
2. Feature engineering runs on raw sensor data → Generates ML features
3. Trained models loaded into Inference Service
4. Real-time predictions served via FastAPI endpoints
5. Alerts triggered when failure probability > threshold
6. Dashboard renders real-time equipment health via WebSocket

---

## 2. Detailed System Architecture

### 2.1 Data Pipeline
- **Ingestion**: REST endpoint + simulated MQTT-style streaming
- **Validation**: Pydantic schemas enforce data quality at ingestion
- **Feature Engineering**: Rolling statistics, lag features, rate-of-change
- **Storage**: Raw data → `sensor_readings` table; Features → `ml_features` table

### 2.2 ML System
- **Training**: Random Forest, XGBoost, LightGBM, Neural Network
- **Evaluation**: Precision, Recall, F1, AUC-ROC, Confusion Matrix
- **Versioning**: File-based model registry with metadata in PostgreSQL
- **Inference**: Pre-loaded model serving via FastAPI with sub-100ms latency

### 2.3 Multi-Tenant SaaS
- **Tenant Isolation**: Every DB row carries `organization_id`
- **Auth**: JWT tokens with tenant context; RBAC (Admin, Engineer)
- **Data Boundary**: Middleware enforces tenant scoping on every query

### 2.4 Real-Time Pipeline
- **Simulation Engine**: Generates realistic sensor data with degradation patterns
- **Prediction Loop**: Periodic batch inference on latest readings
- **WebSocket**: Push updates to connected dashboard clients
- **Alert Engine**: Threshold-based + ML-based alert generation

---

## 3. Database Schema

### Core Tables:
- `organizations` — Tenant registry
- `users` — Auth + RBAC
- `equipment` — Machine registry per tenant
- `equipment_types` — Compressor, Pump, Motor, HVAC
- `sensor_readings` — Time-series sensor data (partitioned by time)
- `ml_features` — Engineered features for ML
- `predictions` — Model prediction results
- `alerts` — Generated alerts with severity
- `maintenance_logs` — Maintenance records
- `ml_models` — Model registry with versions
- `ml_training_runs` — Experiment tracking

### Relationships:
- Organization 1:N Users, Equipment
- Equipment 1:N SensorReadings, Predictions, Alerts
- MLModel 1:N Predictions
- Equipment N:1 EquipmentType

---

## 4. Security Design

- JWT RS256 tokens with 15-min access / 7-day refresh
- Password hashing: bcrypt with salt
- Tenant isolation at middleware level (every query filtered by org_id)
- Input validation on all endpoints (Pydantic)
- Rate limiting per tenant
- CORS whitelist
- SQL injection prevention via SQLAlchemy ORM
- Secrets via environment variables (never in code)

---

## 5. Scaling Strategy

### Horizontal:
- Stateless API servers behind load balancer
- Read replicas for PostgreSQL
- Redis for session/cache layer

### Vertical:
- ML inference on GPU-capable nodes (optional)
- Database connection pooling

### Data:
- Sensor readings table partitioned by month
- Archival strategy for readings > 1 year
- Feature store for pre-computed ML features

---

## 6. Phase-wise Implementation Plan

### Phase 1 — MVP (Weeks 1-4)
- Data ingestion + PostgreSQL schema
- ML training pipeline (RF, XGBoost)
- Basic FastAPI with prediction endpoint
- Simple React dashboard
- Docker Compose setup

### Phase 2 — Production Hardening (Weeks 5-8)
- JWT auth + multi-tenant isolation
- Alert engine + email notifications
- Real-time simulation engine
- WebSocket real-time updates
- Model versioning + registry

### Phase 3 — Scale & Observe (Weeks 9-12)
- Monitoring (Prometheus + Grafana)
- Structured logging (JSON)
- Performance optimization
- Load testing
- CI/CD pipeline

### Phase 4 — Enterprise (Weeks 13-16)
- Advanced analytics dashboard
- Deep learning models
- Maintenance scheduling optimization
- Audit logging
- API documentation + SDK
