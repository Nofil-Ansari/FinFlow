#!/usr/bin/env bash
# scripts/gcp_setup.sh
# Setup script for FinanceFlow on Google Cloud Platform (Cloud Run + Artifact Registry + Redis)
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo "")}"
REGION="${GCP_REGION:-us-central1}"
REPO_NAME="${GCP_REPO_NAME:-financeflow-repo}"
SERVICE_NAME="${GCP_SERVICE_NAME:-financeflow-app}"

echo "=== FinanceFlow GCP Cloud Run Setup ==="

# 1. Check gcloud CLI
if ! command -v gcloud &> /dev/null; then
    echo "Error: Google Cloud SDK (gcloud) is not installed. Please install it from https://cloud.google.com/sdk/docs/install" >&2
    exit 1
fi

# 2. Check Project ID
if [ -z "$PROJECT_ID" ]; then
    echo "No active GCP Project ID detected."
    read -rp "Enter your GCP Project ID: " PROJECT_ID
fi

if [ -z "$PROJECT_ID" ]; then
    echo "Error: Project ID is required." >&2
    exit 1
fi

echo "Target Project: $PROJECT_ID"
echo "Target Region:  $REGION"
echo "Artifact Repo:  $REPO_NAME"
echo "Service Name:   $SERVICE_NAME"

gcloud config set project "$PROJECT_ID"
gcloud config set run/region "$REGION"

# 3. Enable Required APIs
echo "Enabling Cloud Run, Artifact Registry, and IAM APIs..."
gcloud services enable run.googleapis.com artifactregistry.googleapis.com iam.googleapis.com

# 4. Create Artifact Registry Repository if not exists
echo "Ensuring Artifact Registry repository exists..."
if ! gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" &>/dev/null; then
    echo "Creating Docker repository '$REPO_NAME' in region '$REGION'..."
    gcloud artifacts repositories create "$REPO_NAME" \
        --repository-format=docker \
        --location="$REGION" \
        --description="Docker repository for FinanceFlow Cloud Run services"
else
    echo "Artifact repository '$REPO_NAME' already exists."
fi

echo ""
echo "Setup completed successfully!"
echo "Artifact Registry URI: ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}"

