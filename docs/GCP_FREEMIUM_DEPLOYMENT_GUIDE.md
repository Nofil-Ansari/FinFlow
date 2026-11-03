# Google Cloud Platform (GCP) Deployment Options: Freemium & Free-Tier Analysis for FinanceFlow

## Executive Summary
For **FinanceFlow** (Flask + Gunicorn + Flask-SocketIO WebSockets + ML/Scikit-learn + PostgreSQL/SQLite), Google Cloud Platform provides two legitimate permanent **Free Tier** compute options and one initial trial option:

1. **Google Cloud Run (Serverless Container)** — *Best for cost, scalability, and zero-maintenance.*
2. **Compute Engine Free Tier (`e2-micro` VM)** — *Best for standard EC2-like continuous runtime and in-memory SQLite.*
3. **GCP 90-Day $300 Credit Trial** — *Full infrastructure access (Cloud SQL, GKE, Load Balancers).*

---

## 1. Option Comparison Matrix

| Deployment Target | GCP Free Tier Allowance | WebSocket Support (`/ws/ledger`) | Database Pairing | Suitability for FinanceFlow |
| :--- | :--- | :---: | :--- | :---: |
| **Cloud Run** *(Serverless Container)* | **2 Million requests/mo**<br>360,000 vCPU-seconds<br>180 GiB-seconds RAM | ✅ Yes (HTTP/1.1 & HTTP/2 WebSockets up to 60-min timeouts) | Hosted external PostgreSQL (Supabase / Neon free tier) | ⭐⭐⭐⭐⭐ **(Recommended)** |
| **Compute Engine** *(e2-micro VM)* | **1 non-preemptible `e2-micro` VM**<br>(0.25 vCPU, 1 GB RAM)<br>30 GB HDD Standard persistent disk<br>1 GB network egress to Americas/most regions | ✅ Yes (Standard persistent daemon) | SQLite on local 30 GB disk OR hosted PostgreSQL (Supabase) | ⭐⭐⭐⭐ *(Great if keeping current SQLite or single-VM setup)* |
| **App Engine Standard** | **28 instance-hours/day**<br>(F1 instance) | ⚠️ Limited / Fallback polling only | Cloud SQL (No free tier for Cloud SQL) | ⭐⭐ *(Not recommended due to WebSocket & disk limitations)* |

---

## 2. In-Depth Architectural Evaluation

### Option A: Google Cloud Run (Recommended Serverless Architecture)
- **How it works**: Build a Docker image containing FinanceFlow (`Flask + Gunicorn + Flask-SocketIO`), push it to Artifact Registry (first 0.5 GB/mo free), and deploy directly to Cloud Run.
- **WebSocket Compatibility**: Cloud Run natively supports WebSockets. A single connection can remain open for up to **3,600 seconds (60 minutes)**. When no WebSockets or requests are active, instances scale to zero (0 cost).
- **Free Tier Quota**:
  - 2,000,000 requests per month free.
  - 360,000 vCPU-seconds and 180,000 GiB-seconds per month free.
- **Storage / Database Constraint**: Cloud Run instances have ephemeral filesystems. You cannot rely on local `finance_tracker.db` SQLite persisting across restarts.
  - **Solution**: Pair with **Supabase free tier** (500 MB hosted PostgreSQL) or **Neon.tech free tier** (serverless Postgres with connection pooling).

### Option B: Compute Engine `e2-micro` Always-Free VM
- **How it works**: Provisions a real, dedicated Linux virtual machine in free regions (`us-central1`, `us-west1`, or `us-east1`).
- **Specifications**:
  - `e2-micro` (2 shared vCPUs, 1.0 GB memory).
  - 30 GB standard persistent disk.
- **Why it fits FinanceFlow**:
  - Exactly replicates the planned **AWS EC2** architecture.
  - You can run Docker Compose (`Gunicorn + Nginx`) on port 80/443.
  - You can keep using the local SQLite database on the persistent disk without needing external DB provisioning immediately.
- **Memory Consideration**: With 1 GB RAM, ensure you configure a 2 GB Linux Swap file so that dependencies like `pandas`, `scikit-learn`, and `reportlab` install and run without Out-Of-Memory (OOM) issues.

---

## 3. Database Strategy: The GCP Free-Tier Reality
> ⚠️ **Important Cloud Fact**: **Google Cloud SQL (managed PostgreSQL/MySQL) has NO permanent free tier.** After the 90-day $300 trial, Cloud SQL costs ~$10–$15/month minimum.

To keep your deployment **100% free forever**, use one of these database architectures:
1. **Compute Engine VM + Local SQLite / Local PostgreSQL Container**: 100% free under the `e2-micro` 30 GB persistent disk quota.
2. **Cloud Run + Supabase Free Tier**: Cloud Run handles the stateless web/websocket compute; Supabase provides hosted PostgreSQL with automated backups.

---

## 4. Recommended Migration Path
If switching Milestone v2.0 from AWS to GCP:
- **Fastest 1:1 Match**: Deploy to **GCP Compute Engine (`e2-micro`)** in `us-central1` via Docker Compose + Nginx.
- **Modern Cloud-Native**: Deploy container to **Google Cloud Run** connected to **Supabase PostgreSQL**.
