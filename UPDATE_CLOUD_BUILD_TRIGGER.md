# Update Cloud Build Trigger to Use Regional Builder

## Issue
Cloud Build is running in "global" region, which takes ~3 minutes to deploy.
When building in "asia-south1" region, it only takes ~2 minutes.

## Solution
Update your Cloud Build trigger to use the asia-south1 region.

## Steps to Update:

### Option 1: Via GCP Console (Easiest)

1. **Go to Cloud Build Triggers**:
   ```
   https://console.cloud.google.com/cloud-build/triggers?project=naad-bailgada-480412
   ```

2. **Find your trigger** (should be named something like `rmgpgab-naad-bailgada-api-asia-south1-...`)

3. **Click the trigger name** to edit it

4. **Scroll to "Configuration"** section

5. **Look for "Region" setting** and change from:
   - ❌ `global` or `Global (default)`

   To:
   - ✅ `asia-south1 (Mumbai)`

6. **Click "SAVE"**

### Option 2: Via gcloud CLI

```bash
# List triggers to find the trigger name
gcloud builds triggers list --project=naad-bailgada-480412

# Update the trigger region (replace TRIGGER_NAME with your trigger name)
gcloud builds triggers update TRIGGER_NAME \
    --region=asia-south1 \
    --project=naad-bailgada-480412
```

## Verification

After updating, push a test commit and check the build history:
- The "Region" column should show "asia-south1" instead of "global"
- Build time should reduce from ~3min to ~2min

## Why This Matters

**Global builds:**
- Run in multi-region infrastructure
- Slower because they can start anywhere
- Take ~3+ minutes

**Regional builds (asia-south1):**
- Run in Mumbai data center
- Closer to your Cloud Run service
- Take ~2 minutes
- **~33% faster!**

## After Update

Your next git push will automatically use the asia-south1 builder and complete faster.
