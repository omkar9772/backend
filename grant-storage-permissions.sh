#!/bin/bash

# Grant Cloud Run service account permissions to access Cloud Storage

# Get the Cloud Run service account
SERVICE_ACCOUNT=$(gcloud run services describe naad-bailgada-api \
  --region asia-south1 \
  --format 'value(spec.template.spec.serviceAccountName)' 2>/dev/null)


# If no custom service account, use the default compute service account
if [ -z "$SERVICE_ACCOUNT" ]; then
  PROJECT_ID=$(gcloud config get-value project)
  SERVICE_ACCOUNT="${PROJECT_ID}-compute@developer.gserviceaccount.com"
fi

echo "Granting permissions to service account: $SERVICE_ACCOUNT"

# Grant Storage Object Admin role for the bucket
gcloud storage buckets add-iam-policy-binding gs://naad-bailgada-media \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/storage.objectAdmin"

echo "✓ Permissions granted successfully!"
