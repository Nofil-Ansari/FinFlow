# ROADMAP.md

> **Current Milestone**: v2.0 - Production Deployment & Continuous Delivery (GCP Cloud Run + Supabase + Redis)
> **Goal**: Establish a production-grade automated Continuous Deployment (CD) pipeline deploying FinanceFlow to Google Cloud Run with serverless container scaling, Upstash/GCP Memorystore Redis for caching & session/socket backplane, hosted PostgreSQL (Supabase) database, and live WebSocket support.

## Must-Haves
- [ ] Google Cloud SDK (gcloud CLI) environment configuration & project authorization with Cloud Run & Artifact Registry APIs enabled.
- [ ] Production-ready Docker containerization for Flask + Gunicorn + eventlet/gevent worker architecture supporting WebSockets.
- [ ] Redis caching & pub/sub integration (Flask-Caching / Redis message queue for Flask-SocketIO & caching frequently accessed financial analytics/substitutions).
- [ ] Hosted PostgreSQL (Supabase) integration with automated Alembic migrations on deploy.
- [ ] Automated GitHub Actions Continuous Deployment (CD) pipeline to build container images, push to Google Artifact Registry, and deploy revisions to Google Cloud Run with zero downtime.
- [ ] Production hardening, secret management via Cloud Run environment secrets, custom domain/SSL mapping, and live health check verification.

## Phases

### Phase 1: GCP Environment, Cloud Project Provisioning & API Setup
**Status**: ⏳ Not Started  
**Objective**: Install & configure Google Cloud SDK (gcloud CLI), authorize GCP project, enable Cloud Run (`run.googleapis.com`), Artifact Registry (`artifactregistry.googleapis.com`), and IAM APIs, and generate automation scripts.

### Phase 2: Production Containerization & Redis Caching Layer Architecture
**Status**: ⏳ Not Started  
**Objective**: Build and optimize a production multi-stage Dockerfile for Cloud Run execution (listening on `$PORT`, supporting WebSockets/gunicorn), integrate Redis client/Flask-Caching layer for recommendation/analytics caching and SocketIO message queue, and verify local container execution.

### Phase 3: Hosted PostgreSQL Database Setup & Migration Automation
**Status**: ⏳ Not Started  
**Objective**: Configure Supabase PostgreSQL connection string, verify Alembic/Flask-Migrate automated execution during container deployment or release job, and validate schema integrity with connection pooling (e.g. pgBouncer / Supabase transaction pooler).

### Phase 4: Google Cloud Run Service Configuration & Artifact Registry Setup
**Status**: ⏳ Not Started  
**Objective**: Provision Google Artifact Registry repository, configure Cloud Run service specs (CPU allocation, memory, concurrency, session affinity for WebSockets, min/max instances, and environment secrets for DB & Redis), and verify direct container deployment.

### Phase 5: GitHub Actions Continuous Deployment (CD) Pipeline for Cloud Run
**Status**: ⏳ Not Started  
**Objective**: Extend `.github/workflows/ci.yml` or add `cd.yml` with automated Workload Identity Federation / Service Account deployment to build Docker image, push to Artifact Registry, execute Alembic migrations, deploy new revision to Cloud Run, and perform health check verification.

### Phase 6: Production Hardening & Technical Debt Resolution (Gap Closure)
**Status**: ⏳ Not Started  
**Objective**: Resolve technical debt items identified in milestone audit: modernize deprecated timestamps, fix SQLite connection cleanup in test tearDown, and resolve Dependabot package vulnerability warnings.

**Gaps to Close:**
- [ ] Migrate `datetime.utcnow()` across models and services to `datetime.now(timezone.utc)`.
- [ ] Implement explicit engine/connection close in test harness tearDown (`test_ai_advisor.py`).
- [ ] Perform dependency vulnerability bump and generate container-pinned requirements lock.
