# STATE.md - Project Memory

## Active Milestone
**Milestone**: v2.0 - Production Deployment & Continuous Delivery (GCP e2-micro + Supabase)
**Active Branch**: main
**Last Updated**: 2026-10-24

## Current Position
- **Milestone**: v2.0
- **Phase**: Not started (Ready for Phase 1: GCP Environment & Cloud Project Provisioning)
- **Status**: Milestone planned

## Key Requirements & Inputs (from Prompts)
- **Target Host**: Google Compute Engine (GCE) e2-micro Always-Free VM
- **GCP Region**: us-central1, us-east1, or us-west1 (Always-Free tier eligible)
- **RAM Optimization**: 2GB Linux swapfile (/swapfile) for memory safety (1GB physical RAM constraint)
- **Database Strategy**: Hosted PostgreSQL (Supabase)
- **Deployment Trigger**: Automated GitHub Actions CD pipeline upon passing CI on main
- **Reverse Proxy**: Nginx with WebSocket upgrade (/ws/ledger) and automated Let's Encrypt SSL

## Next Steps
1. Run \/plan 1\ or start Phase 1: Install & configure Google Cloud SDK (gcloud CLI), authorize project profile, and select Always-Free region.

## Gap Closure Mode
Addressing 2 technical debt gap closure plans identified in Milestone v2.0 Audit:
- **Plan 6.1 (fix-deprecations-and-teardown)**: Modernize UTC timestamps & SQLite connection cleanup.
- **Plan 6.2 (fix-dependencies-and-lockfile)**: Audit vulnerable dependencies & pin production packages.
