# 🚀 Deploy Notifications to Production (GCP Cloud Run)

This guide shows you how to deploy Firebase notification support to your production backend.

## 📋 What's Been Updated

✅ Backend code now uses `/secrets/firebase-key.json` in production
✅ Deployment script automatically uploads Firebase credentials
✅ Firebase key excluded from git
✅ Auto-subscription to 'all_races' topic enabled

---

## 🎯 Option 1: Automated Deployment (Recommended)

If you have `gcloud` CLI installed:

### Step 1: Install gcloud CLI (if not installed)

```bash
# macOS
brew install google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install
```

### Step 2: Deploy Everything

```bash
cd /Users/omkar/Documents/Naad/Repos/backend

# Make sure firebase-key.json is present
ls -la firebase-key.json

# Run deployment
./deploy-gcp.sh
```

**That's it!** The script will:
- ✅ Upload `firebase-key.json` to Secret Manager
- ✅ Configure Cloud Run to mount the secret
- ✅ Deploy your updated backend
- ✅ Test the deployment

---

## 🎯 Option 2: Manual Deployment via GCP Console

If you don't have `gcloud` CLI installed:

### Step 1: Upload Firebase Credentials to Secret Manager

1. **Go to Secret Manager**:
   ```
   https://console.cloud.google.com/security/secret-manager?project=naad-bailgada-480412
   ```

2. **Click "CREATE SECRET"**

3. **Configure the secret**:
   - **Name**: `firebase-credentials`
   - **Secret value**: Click "BROWSE" and select:
     ```
     /Users/omkar/Documents/Naad/Repos/backend/firebase-key.json
     ```
   - Click **"CREATE SECRET"**

### Step 2: Deploy Updated Code to Cloud Run

#### Option A: Deploy from Local Machine (requires gcloud)

```bash
cd /Users/omkar/Documents/Naad/Repos/backend

gcloud run deploy naad-bailgada-api \
    --source . \
    --region asia-south1 \
    --platform managed \
    --project naad-bailgada-480412 \
    --allow-unauthenticated \
    --set-secrets "/secrets/firebase-key.json=firebase-credentials:latest"
```

#### Option B: Deploy via GCP Console

1. **Commit and push your code** (firebase-key.json won't be included - it's in .gitignore):
   ```bash
   cd /Users/omkar/Documents/Naad/Repos/backend
   git add .
   git commit -m "Add Firebase notification support with production secrets"
   git push
   ```

2. **Go to Cloud Run**:
   ```
   https://console.cloud.google.com/run?project=naad-bailgada-480412
   ```

3. **Click your service** (naad-bailgada-api)

4. **Click "EDIT & DEPLOY NEW REVISION"**

5. **In "Container" section**, update the source:
   - **Source**: Select your repository
   - **Branch**: main (or your branch)

6. **Scroll to "VARIABLES & SECRETS"**

7. **Click "SECRETS" tab**

8. **Click "REFERENCE A SECRET"**:
   - **Secret**: `firebase-credentials`
   - **Reference method**: "Mounted as volume"
   - **Mount path**: `/secrets/firebase-key.json`

9. **Click "DEPLOY"**

---

## ✅ Verify Deployment

### Check 1: Cloud Run Logs

1. Go to Cloud Run service logs:
   ```
   https://console.cloud.google.com/run/detail/asia-south1/naad-bailgada-api/logs?project=naad-bailgada-480412
   ```

2. Look for this log on startup:
   ```
   ✅ Firebase Admin SDK initialized at startup (using /secrets/firebase-key.json)
   ```

### Check 2: Send Test Notification from Admin Panel

1. Open your admin panel
2. Go to Notifications section
3. Select a race
4. Send a notification
5. Check your mobile device - notification should arrive! 📱

### Check 3: Check Cloud Run Logs for Notification

After sending from admin panel, check logs for:
```
✅ Subscribed new token to 'all_races' topic: {'success': 1, 'failure': 0}
✅ Notification sent to topic 'all_races' (Message ID: ...)
```

---

## 🔧 Troubleshooting

### Issue: "Secret not found"

**Solution**: Make sure you created the secret in the correct project:
```bash
gcloud secrets list --project=naad-bailgada-480412
```

### Issue: "Permission denied" on secret

**Solution**: Grant access to Cloud Run service account:

1. Get your service account:
   ```bash
   gcloud run services describe naad-bailgada-api \
       --region=asia-south1 \
       --project=naad-bailgada-480412 \
       --format="value(spec.template.spec.serviceAccountName)"
   ```

2. Grant access:
   ```bash
   gcloud secrets add-iam-policy-binding firebase-credentials \
       --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
       --role="roles/secretmanager.secretAccessor" \
       --project=naad-bailgada-480412
   ```

### Issue: "Notifications still not working"

**Check**:
1. Firebase key is correct project (naad-bailgada, NOT naad-bailgada-480412)
2. Secret is mounted at `/secrets/firebase-key.json`
3. Mobile app is registered and subscribed to 'all_races' topic

---

## 📊 Production Checklist

- [ ] `firebase-key.json` uploaded to Secret Manager
- [ ] Secret mounted in Cloud Run at `/secrets/firebase-key.json`
- [ ] Backend deployed with updated code
- [ ] Startup logs show: "Firebase Admin SDK initialized at startup"
- [ ] Test notification sent from admin panel
- [ ] Mobile device receives notification
- [ ] `firebase-key.json` in .gitignore (not committed to git)

---

## 🎉 You're Done!

Notifications are now fully configured for production! Your users will receive notifications when you send them from the admin panel.

**Important**: Never commit `firebase-key.json` to git - it's a secret credential!
