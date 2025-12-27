#!/bin/bash

# Complete deployment script with authentication
set -e

echo "╔════════════════════════════════════════════════════╗"
echo "║   Firebase Notifications - Production Deployment  ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ID="naad-bailgada-480412"

# Step 1: Check gcloud installation
echo -e "${BLUE}Step 1: Checking gcloud installation...${NC}"
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found${NC}"
    echo "Please run: brew install google-cloud-sdk"
    exit 1
fi
echo -e "${GREEN}✅ gcloud CLI found ($(gcloud --version | head -1))${NC}"
echo ""

# Step 2: Check authentication
echo -e "${BLUE}Step 2: Checking GCP authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q .; then
    echo -e "${YELLOW}⚠️  Not authenticated with GCP${NC}"
    echo ""
    echo "Opening browser for authentication..."
    echo "Please complete the authentication in your browser."
    echo ""

    if ! gcloud auth login; then
        echo -e "${RED}❌ Authentication failed${NC}"
        exit 1
    fi
else
    ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | head -1)
    echo -e "${GREEN}✅ Already authenticated as: $ACCOUNT${NC}"
fi
echo ""

# Step 3: Set project
echo -e "${BLUE}Step 3: Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID
echo -e "${GREEN}✅ Project set to: $PROJECT_ID${NC}"
echo ""

# Step 4: Check firebase-key.json
echo -e "${BLUE}Step 4: Checking Firebase credentials...${NC}"
if [ ! -f "firebase-key.json" ]; then
    echo -e "${RED}❌ firebase-key.json not found in current directory${NC}"
    echo "Please make sure you're in the backend directory and firebase-key.json exists"
    exit 1
fi
echo -e "${GREEN}✅ firebase-key.json found${NC}"
echo ""

# Step 5: Enable required APIs
echo -e "${BLUE}Step 5: Enabling required GCP APIs...${NC}"
echo "This may take a minute..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    containerregistry.googleapis.com \
    --quiet

echo -e "${GREEN}✅ APIs enabled${NC}"
echo ""

# Step 6: Deploy
echo -e "${BLUE}Step 6: Running deployment script...${NC}"
echo ""
echo "════════════════════════════════════════════════════"
echo ""

if [ -f "./deploy-gcp.sh" ]; then
    chmod +x ./deploy-gcp.sh
    ./deploy-gcp.sh
else
    echo -e "${RED}❌ deploy-gcp.sh not found${NC}"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Check Cloud Run logs for: 'Firebase Admin SDK initialized'"
echo "2. Send test notification from admin panel"
echo "3. Check your mobile device!"
echo ""
