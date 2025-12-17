#!/bin/bash
# GCP Cloud Run Deployment Script for Naad Bailgada Backend

set -e

echo "🚀 Deploying Naad Bailgada Backend to GCP Cloud Run"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"naad-admin"}
REGION="asia-south1"
SERVICE_NAME="naad-bailgada-api"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found${NC}"
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo -e "${GREEN}✅ gcloud CLI found${NC}"

# Set project
echo ""
echo "Setting GCP project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}🔐 Please login to GCP${NC}"
    gcloud auth login
fi

echo -e "${GREEN}✅ Authenticated${NC}"

# Enable required APIs
echo ""
echo "📦 Enabling required GCP APIs..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    containerregistry.googleapis.com

echo -e "${GREEN}✅ APIs enabled${NC}"

# Load environment variables
if [ -f .env ]; then
    echo ""
    echo "📋 Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
fi

# Create secrets in Secret Manager
echo ""
echo "🔒 Setting up secrets in GCP Secret Manager..."

# Database URL
echo "Creating DATABASE_URL secret..."
echo -n "$DATABASE_URL" | gcloud secrets create DATABASE_URL \
    --data-file=- \
    --replication-policy="automatic" 2>/dev/null || \
echo -n "$DATABASE_URL" | gcloud secrets versions add DATABASE_URL \
    --data-file=-

# JWT Secret
echo "Creating JWT_SECRET_KEY secret..."
echo -n "$JWT_SECRET_KEY" | gcloud secrets create JWT_SECRET_KEY \
    --data-file=- \
    --replication-policy="automatic" 2>/dev/null || \
echo -n "$JWT_SECRET_KEY" | gcloud secrets versions add JWT_SECRET_KEY \
    --data-file=-

echo -e "${GREEN}✅ Secrets configured${NC}"

# Deploy to Cloud Run
echo ""
echo "🚢 Deploying to Cloud Run..."
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo ""

gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --min-instances 0 \
    --max-instances 10 \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --set-env-vars "ENVIRONMENT=production,DEBUG=False,API_V1_PREFIX=/api/v1,ADMIN_PREFIX=/api/v1/admin,GCP_BUCKET_NAME=naad-bailgada-media,GCP_PROJECT_ID=$PROJECT_ID" \
    --set-secrets "DATABASE_URL=DATABASE_URL:latest,JWT_SECRET_KEY=JWT_SECRET_KEY:latest" \
    --set-env-vars "CORS_ORIGINS=https://naad-admin.web.app,https://naad-admin.firebaseapp.com,http://localhost:9000"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    echo ""

    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
        --region $REGION \
        --format="value(status.url)")

    echo "=================================================="
    echo "🎉 Backend is now live!"
    echo "=================================================="
    echo ""
    echo "Service URL: $SERVICE_URL"
    echo "API Base URL: $SERVICE_URL/api/v1"
    echo "Health Check: $SERVICE_URL/health"
    echo ""
    echo "📝 Next Steps:"
    echo "1. Test the API: curl $SERVICE_URL/health"
    echo "2. Add this to GitHub Secrets as PRODUCTION_API_URL:"
    echo "   $SERVICE_URL/api/v1"
    echo "3. Update admin-web CORS if needed"
    echo ""

    # Test health endpoint
    echo "🏥 Testing health endpoint..."
    if curl -f -s "$SERVICE_URL/health" > /dev/null; then
        echo -e "${GREEN}✅ Health check passed!${NC}"
    else
        echo -e "${YELLOW}⚠️  Health check failed (might be normal if /health endpoint doesn't exist)${NC}"
    fi

else
    echo ""
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi
