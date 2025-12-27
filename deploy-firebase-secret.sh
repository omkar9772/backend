#!/bin/bash

# Script to deploy Firebase credentials to GCP Secret Manager
# and configure Cloud Run to use them

set -e

PROJECT_ID="naad-bailgada-480412"
SECRET_NAME="firebase-credentials"
REGION="asia-south1"
SERVICE_NAME="naad-bailgada-api"  # Replace with your actual Cloud Run service name

echo "🔐 Deploying Firebase Credentials to GCP Secret Manager"
echo "======================================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed"
    echo ""
    echo "To install gcloud CLI:"
    echo "  brew install google-cloud-sdk"
    echo ""
    echo "Or download from: https://cloud.google.com/sdk/docs/install"
    echo ""
    exit 1
fi

# Check if firebase-key.json exists
if [ ! -f "firebase-key.json" ]; then
    echo "❌ firebase-key.json not found in current directory"
    exit 1
fi

echo "✅ firebase-key.json found"
echo ""

# Set project
echo "📌 Setting GCP project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable Secret Manager API
echo "📌 Enabling Secret Manager API..."
gcloud services enable secretmanager.googleapis.com

# Create or update secret
echo "📌 Creating/updating secret: $SECRET_NAME"
if gcloud secrets describe $SECRET_NAME --project=$PROJECT_ID &> /dev/null; then
    echo "   Secret already exists, adding new version..."
    gcloud secrets versions add $SECRET_NAME \
        --data-file=firebase-key.json \
        --project=$PROJECT_ID
else
    echo "   Creating new secret..."
    gcloud secrets create $SECRET_NAME \
        --data-file=firebase-key.json \
        --replication-policy="automatic" \
        --project=$PROJECT_ID
fi

echo "✅ Secret uploaded successfully"
echo ""

# Get Cloud Run service account
echo "📌 Getting Cloud Run service account..."
SERVICE_ACCOUNT=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(spec.template.spec.serviceAccountName)" 2>/dev/null || echo "")

if [ -z "$SERVICE_ACCOUNT" ]; then
    # Use default compute service account
    PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
    SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
    echo "   Using default service account: $SERVICE_ACCOUNT"
else
    echo "   Found service account: $SERVICE_ACCOUNT"
fi

# Grant access to secret
echo "📌 Granting Secret Manager access to Cloud Run service account..."
gcloud secrets add-iam-policy-binding $SECRET_NAME \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID

echo "✅ Access granted"
echo ""

echo "📌 Next steps:"
echo "   1. Update your Cloud Run service to mount the secret"
echo "   2. Use the following command:"
echo ""
echo "   gcloud run services update $SERVICE_NAME \\"
echo "       --update-secrets=/secrets/firebase-key.json=$SECRET_NAME:latest \\"
echo "       --region=$REGION \\"
echo "       --project=$PROJECT_ID"
echo ""
echo "   OR update via Console at:"
echo "   https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/revisions?project=$PROJECT_ID"
echo ""
echo "✅ Done!"
