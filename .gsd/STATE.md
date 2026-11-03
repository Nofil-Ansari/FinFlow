# STATE.md - Project Memory

## Active Milestone
**Milestone**: v2.0 - Production Deployment & Continuous Delivery (GCP Cloud Run + Supabase + Redis)
**Active Branch**: main
**Last Updated**: 2026-11-04

## Current Position
- **Milestone**: v2.0
- **Phase**: Phase 1: GCP Environment, Cloud Project Provisioning & API Setup
- **Status**: Plan 01-01 updated for Cloud Run + Redis and awaiting execution
- **Active Plan**: `.gsd/phases/01/01-PLAN.md`

## Key Requirements & Inputs (from Prompts)
- **Target Host**: Google Cloud Run (Serverless container runtime, automatic HTTPS, revision rollouts, auto-scaling)
- **GCP Region**: Default region (e.g. `us-central1`) with Artifact Registry
- **Caching & Backplane**: Redis (Upstash Redis or Cloud Memorystore for caching expensive analytics/substitutions & Flask-SocketIO pub/sub message queue)
- **Database Strategy**: Hosted PostgreSQL (Supabase with connection pooling / Transaction Pooler)
- **Deployment Trigger**: Automated GitHub Actions CD pipeline upon passing CI on main
- **WebSocket & Networking**: Cloud Run with Session Affinity enabled and HTTP/2 or WebSockets enabled; container listens on dynamic `$PORT`

## Next Steps
1. Run Plan 01-01: Author GCP environment scripts for Cloud Run + Artifact Registry, authorize `gcloud`, and enable required APIs (`run.googleapis.com`, `artifactregistry.googleapis.com`, `iam.googleapis.com`).

## Gap Closure Mode
Addressing 2 technical debt gap closure plans identified in Milestone v2.0 Audit:
- **Plan 6.1 (fix-deprecations-and-teardown)**: Modernize UTC timestamps & SQLite connection cleanup.
- **Plan 6.2 (fix-dependencies-and-lockfile)**: Audit vulnerable dependencies & pin production packages.
