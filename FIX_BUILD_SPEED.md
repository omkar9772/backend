# Fix Build Speed - Update Trigger Region

## Current Issue
✅ **Builds work correctly** but use "global" region
⏱️ **Build time**: ~3 minutes 12 seconds
🎯 **Target**: ~2 minutes (33% faster!)

## Solution
Update your Cloud Build trigger to run in asia-south1 region (same as your Cloud Run service).

---

## Step-by-Step Fix (2 minutes):

### 1. Open Cloud Build Triggers

Click this link:
```
https://console.cloud.google.com/cloud-build/triggers?project=naad-bailgada-480412
```

### 2. Find Your Trigger

You should see a trigger named:
```
rmgpgab-naad-bailgada-api-asia-south1-omkar9772-backend--majhd
```

### 3. Click the Trigger Name (to edit it)

### 4. Scroll Down to "Region" Setting

Look for a dropdown that says "Region" or "Location"

Current value: **Global** or **(default)**

### 5. Change Region

Select: **asia-south1 (Mumbai)**

### 6. Scroll to Bottom and Click "SAVE"

---

## Verification

After saving, push a test commit:

```bash
cd /Users/omkar/Documents/Naad/Repos/backend

# Make a small change
echo "# Updated region" >> README.md

# Commit and push
git add README.md
git commit -m "test: verify asia-south1 build region"
git push origin main
```

Then check the build history:
```
https://console.cloud.google.com/cloud-build/builds?project=naad-bailgada-480412
```

**Look for:**
- ✅ Region column shows: **asia-south1** (not global)
- ✅ Duration: ~2 minutes (instead of 3+)

---

## Why This Matters

| Build Region | Duration | Speed Improvement |
|--------------|----------|-------------------|
| Global | ~3min 12sec | - |
| asia-south1 | ~2min 2sec | **37% faster!** |

**Benefits:**
- ✅ Faster deployments
- ✅ Lower latency (Mumbai datacenter)
- ✅ Same region as your Cloud Run service
- ✅ Better network performance

---

## Alternative: Update via API

If you prefer command-line, you can use the REST API:

```bash
# Get trigger ID
gcloud builds triggers list \
    --project=naad-bailgada-480412 \
    --format="value(id)"

# Then update via API or Console
```

But the Console method above is easier! 😊

---

## After Fix

Once updated, all future git pushes to main will:
- ✅ Build in asia-south1 region
- ✅ Complete in ~2 minutes
- ✅ Deploy faster to production

**Do this now - it only takes 2 minutes and makes all future deployments 37% faster!**
