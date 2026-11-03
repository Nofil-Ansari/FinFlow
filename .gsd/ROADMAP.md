# ROADMAP.md

> **Current Milestone**: v2.0 - Production Deployment & Continuous Delivery (GCP e2-micro + Supabase)
> **Goal**: Establish a production-grade automated Continuous Deployment (CD) pipeline deploying FinanceFlow to a Google Compute Engine e2-micro Always-Free VM with hosted PostgreSQL (Supabase) database, Nginx reverse proxy, and live WebSocket support.

## Must-Haves
- [ ] Google Cloud SDK (gcloud CLI) environment configuration & project authorization (Region us-central1/us-east1/us-west1).
- [ ] Production-ready Docker containerization for Flask + Gunicorn + Flask-SocketIO.
- [ ] Hosted PostgreSQL (Supabase) integration with automated Alembic migrations on deploy.
- [ ] Automated GitHub Actions Continuous Deployment (CD) pipeline triggered on verified main merge.
- [ ] Production GCE e2-micro VM provisioning, 2GB swapfile configuration, Nginx reverse proxy with SSL, and live health check verification.

## Phases

### Phase 1: GCP Environment & Cloud Project Provisioning
**Status**: ⏳ Not Started  
**Objective**: Install prerequisites (Google Cloud SDK / gcloud CLI), authorize GCP project, configure Always-Free eligible region (`us-central1`, `us-east1`, or `us-west1`), and verify project billing & API readiness.

### Phase 2: Production Containerization & Gunicorn WebSocket Architecture
**Status**: ⏳ Not Started  
**Objective**: Build and optimize a production Dockerfile and Docker Compose setup supporting Gunicorn gevent/eventlet workers for Flask-SocketIO and environment-based runtime configuration.

### Phase 3: Hosted PostgreSQL Database Setup & Migration Automation
**Status**: ⏳ Not Started  
**Objective**: Configure Supabase PostgreSQL connection string, verify Alembic/Flask-Migrate automated execution, and validate schema integrity.

### Phase 4: GCE e2-micro VM Host Provisioning & Reverse Proxy Setup
**Status**: ⏳ Not Started  
**Objective**: Provision the target Google Compute Engine `e2-micro` Always-Free instance, configure 30GB persistent disk, allocate a 2GB Linux swapfile, set up firewall rules (ports 80, 443, 22), install Docker runtime, and configure Nginx reverse proxy with WebSocket upgrade support.

### Phase 5: GitHub Actions Continuous Deployment (CD) Pipeline
**Status**: ⏳ Not Started  
**Objective**: Extend .github/workflows/ci.yml with an automated deployment job to build, push container images (or SSH deploy), deploy to GCE `e2-micro` with zero-downtime, and run automated post-deploy health checks.

### Phase 6: Production Hardening & Technical Debt Resolution (Gap Closure)
**Status**: ⏳ Not Started  
**Objective**: Resolve technical debt items identified in the milestone audit: modernize deprecated timestamps, fix SQLite connection cleanup in test tearDown, and resolve Dependabot package vulnerability warnings.

**Gaps to Close:**
- [ ] Migrate datetime.utcnow() across models and services to datetime.now(timezone.utc).
- [ ] Implement explicit engine/connection close in test harness tearDown (test_ai_advisor.py).
- [ ] Perform dependency vulnerability bump and generate container-pinned requirements lock.
