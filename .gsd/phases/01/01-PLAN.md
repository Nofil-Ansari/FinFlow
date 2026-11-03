---
phase: 1
plan: 01
type: standard
autonomous: false
wave: 1
depends_on: []
---

# Plan 01-01: GCP Environment, Cloud Run & Artifact Registry Setup

<objective>
Configure, authorize, and verify the Google Cloud Platform environment and project profile for FinanceFlow, ensuring Cloud Run readiness (Cloud Run API, Artifact Registry API, IAM), Redis configuration parameters, and generating cross-platform provisioning automation scripts.
</objective>

<context>
- `.gsd/ROADMAP.md`
- `.gsd/STATE.md`
- `finance_app/app/config.py`
</context>

<tasks>

<task type="auto" name="Create GCP Environment Scripts & Config Template">
<files>
- `scripts/gcp_setup.ps1`
- `scripts/gcp_setup.sh`
- `.env.gcp.example`
</files>
<action>
Author cross-platform setup automation scripts (`scripts/gcp_setup.ps1` and `scripts/gcp_setup.sh`) and `.env.gcp.example` specifying `GCP_PROJECT_ID`, default region (`us-central1`), Artifact Registry repository name (`financeflow-repo`), Cloud Run service name (`financeflow-app`), and Redis connection configuration variables (`REDIS_URL`).
</action>
<verify>
Ensure scripts exist and pass syntax validation:
- PowerShell: `powershell -Command "Get-Command ./scripts/gcp_setup.ps1"`
- Bash: `bash -n ./scripts/gcp_setup.sh`
</verify>
<done>
Scripts and `.env.gcp.example` are created with correct syntax and documented usage instructions for Cloud Run + Redis.
</done>
</task>

<task type="checkpoint:human-action" name="GCP Authentication & Project Selection">
<action>
Authorize `gcloud` CLI with active Google Cloud account and set/select target project ID.
</action>
<verify>
Run `gcloud auth list` and `gcloud config get-value project` to verify authorized account and active project ID.
</verify>
<done>
User confirms `gcloud` is logged in and active GCP project has billing enabled.
</done>
</task>

<task type="auto" name="Enable Cloud Run & Artifact Registry APIs & Generate GCP Configuration Metadata">
<files>
- `.gsd/phases/01/GCP_CONFIG.json`
- `.gsd/STATE.md`
</files>
<action>
Execute API enablement verification for `run.googleapis.com`, `artifactregistry.googleapis.com`, and `iam.googleapis.com`, store project parameters in `.gsd/phases/01/GCP_CONFIG.json`, and update `.gsd/STATE.md`.
</action>
<verify>
Verify `.gsd/phases/01/GCP_CONFIG.json` contains valid project ID, region, Artifact Registry repository, and enabled services status.
</verify>
<done>
Cloud Run and Artifact Registry APIs verified enabled and `.gsd/phases/01/GCP_CONFIG.json` created.
</done>
</task>

</tasks>

<success_criteria>
- [ ] `scripts/gcp_setup.ps1` and `scripts/gcp_setup.sh` ready for Cloud Run and Artifact Registry automation.
- [ ] `.env.gcp.example` created with Cloud Run specifications and `REDIS_URL`.
- [ ] GCP authentication and project setup validated.
- [ ] `run.googleapis.com` and `artifactregistry.googleapis.com` active for the project.
</success_criteria>

