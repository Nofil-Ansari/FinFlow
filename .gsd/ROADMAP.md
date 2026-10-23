# ROADMAP.md

> **Current Milestone**: v2.0 - Production Deployment & Continuous Delivery (AWS EC2 + Supabase)
> **Goal**: Establish a production-grade automated Continuous Deployment (CD) pipeline deploying FinanceFlow to AWS EC2 with hosted PostgreSQL (Supabase) database and live WebSocket support.

## Must-Haves
- [ ] AWS Agent Toolkit & AWS CLI environment configuration for Region ap-southeast-2.
- [ ] Production-ready Docker containerization for Flask + Gunicorn + Flask-SocketIO.
- [ ] Hosted PostgreSQL (Supabase) integration with automated Alembic migrations on deploy.
- [ ] Automated GitHub Actions Continuous Deployment (CD) pipeline triggered on verified main merge.
- [ ] Production EC2 provisioning, Nginx reverse proxy with SSL, and live health check verification.

## Phases

### Phase 1: AWS Environment & Agent Toolkit Provisioning
**Status**: ⬜ Not Started  
**Objective**: Install prerequisites (uv, AWS CLI v2), configure Region ap-southeast-2 and project profile via browser authentication, and set up the AWS Agent Toolkit.

### Phase 2: Production Containerization & Gunicorn WebSocket Architecture
**Status**: ⬜ Not Started  
**Objective**: Build and optimize a production Dockerfile and Compose setup supporting Gunicorn gevent/eventlet workers for Flask-SocketIO and environment-based runtime configuration.

### Phase 3: Hosted PostgreSQL Database Setup & Migration Automation
**Status**: ⬜ Not Started  
**Objective**: Configure Supabase PostgreSQL connection string, verify Alembic/Flask-Migrate automated execution, and validate schema integrity.

### Phase 4: EC2 Host Provisioning & Reverse Proxy Setup
**Status**: ⬜ Not Started  
**Objective**: Provision the target AWS EC2 instance, configure security groups (ports 80, 443, 22), set up Docker runtime, and configure Nginx reverse proxy with WebSocket upgrade support.

### Phase 5: GitHub Actions Continuous Deployment (CD) Pipeline
**Status**: ⬜ Not Started  
**Objective**: Extend .github/workflows/ci.yml with an automated deployment job to build, push container images, deploy to EC2 with zero-downtime, and run automated post-deploy health checks.
