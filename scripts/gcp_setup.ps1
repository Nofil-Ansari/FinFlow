# scripts/gcp_setup.ps1
# Setup script for FinanceFlow on Google Cloud Platform (Cloud Run + Artifact Registry + Redis)
[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectId = $env:GCP_PROJECT_ID,
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1",

    [Parameter(Mandatory=$false)]
    [string]$RepoName = "financeflow-repo",

    [Parameter(Mandatory=$false)]
    [string]$ServiceName = "financeflow-app"
)

$ErrorActionPreference = "Stop"

Write-Host "=== FinanceFlow GCP Cloud Run Setup ===" -ForegroundColor Cyan

# 1. Check gcloud CLI
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Error "Google Cloud SDK (gcloud) is not installed or not in PATH. Please install it from https://cloud.google.com/sdk/docs/install"
    exit 1
}

# 2. Check & Set Project ID
if (-not $ProjectId) {
    $ProjectId = (gcloud config get-value project 2>$null).Trim()
}

if (-not $ProjectId) {
    Write-Host "No active GCP Project ID detected. Please run 'gcloud auth login' and 'gcloud config set project <PROJECT_ID>'." -ForegroundColor Yellow
    $ProjectId = Read-Host "Enter your GCP Project ID"
}

if (-not $ProjectId) {
    Write-Error "Project ID is required."
    exit 1
}

Write-Host "Target Project: $ProjectId" -ForegroundColor Green
Write-Host "Target Region:  $Region" -ForegroundColor Green
Write-Host "Artifact Repo:  $RepoName" -ForegroundColor Green
Write-Host "Service Name:   $ServiceName" -ForegroundColor Green

gcloud config set project $ProjectId
gcloud config set run/region $Region

# 3. Enable Required APIs
Write-Host "Enabling Cloud Run, Artifact Registry, and IAM APIs..." -ForegroundColor Cyan
gcloud services enable run.googleapis.com artifactregistry.googleapis.com iam.googleapis.com

# 4. Create Artifact Registry Repository if not exists
Write-Host "Ensuring Artifact Registry repository exists..." -ForegroundColor Cyan
$existingRepo = gcloud artifacts repositories describe $RepoName --location=$Region --format="value(name)" 2>$null
if (-not $existingRepo) {
    Write-Host "Creating Docker repository '$RepoName' in region '$Region'..." -ForegroundColor Yellow
    gcloud artifacts repositories create $RepoName `
        --repository-format=docker `
        --location=$Region `
        --description="Docker repository for FinanceFlow Cloud Run services"
} else {
    Write-Host "Artifact repository '$RepoName' already exists." -ForegroundColor Green
}

# 5. Output Configuration
Write-Host "`nSetup completed successfully!" -ForegroundColor Green
Write-Host "Artifact Registry URI: $Region-docker.pkg.dev/$ProjectId/$RepoName" -ForegroundColor Cyan
Write-Host "You can now configure .env.gcp or deploy using Cloud Run MCP." -ForegroundColor Cyan

