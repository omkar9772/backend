#!/bin/bash

# Grant the service account permission to sign URLs using IAM signBlob API

SERVICE_ACCOUNT="backend-uploader@naad-bailgada-480412.iam.gserviceaccount.com"

echo "Granting Service Account Token Creator role to ${SERVICE_ACCOUNT}..."

# Grant the service account permission to impersonate itself for signing
gcloud iam service-accounts add-iam-policy-binding ${SERVICE_ACCOUNT} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/iam.serviceAccountTokenCreator"

echo "✓ Permissions granted successfully!"
echo ""
echo "The service account can now sign URLs using the IAM signBlob API."
