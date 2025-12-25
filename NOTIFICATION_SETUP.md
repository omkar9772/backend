# 🔔 Push Notification System Setup Guide

Complete guide for setting up Firebase Cloud Messaging (FCM) push notifications for race reminders.

## 📋 Overview

The notification system sends push notifications to users for:
1. **One day before race day** - Reminder that race is tomorrow
2. **On race day** - Notification that race is happening today

---

## 🏗️ Architecture

### Mobile App (Flutter)
- `NotificationService`: Handles FCM token registration and message receiving
- `NotificationProvider`: State management for notifications
- Auto-subscribes to `all_races` topic on app launch

### Backend (Python/FastAPI)
- `FirebaseService`: Sends push notifications via Firebase Admin SDK
- API Endpoints: Register/unregister device tokens
- Scheduler Script: Runs twice daily to send race notifications

### Database (Neon PostgreSQL)
- `device_tokens` table: Stores FCM tokens for all devices

---

## 🚀 Deployment Steps

### Step 1: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install `firebase-admin==6.5.0` and other dependencies.

---

### Step 2: Get Firebase Service Account Key

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: `naad-bailgada`
3. Click **Project Settings** (gear icon) → **Service Accounts**
4. Click **"Generate new private key"**
5. Download the JSON file
6. Save it as `gcp-key.json` in the `backend/` directory

**Security Note**: The `gcp-key.json` file should already be in your backend directory (I saw it in the file listing). Make sure it's added to `.gitignore` to prevent committing it to the repository.

---

### Step 3: Update Environment Variables

Add to your `backend/.env` file:

```env
# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=gcp-key.json
```

---

### Step 4: Run Database Migration

```bash
cd backend

# Run Alembic migration to create device_tokens table
alembic upgrade head
```

This will create the `device_tokens` table in your Neon DB.

---

### Step 5: Test Backend API

Start your backend server:

```bash
cd backend
python app/main.py
```

Test the notification endpoints:

```bash
# Register a test device token
curl -X POST "http://localhost:8000/api/v1/notifications/register-device" \
  -H "Content-Type: application/json" \
  -d '{
    "device_token": "test-token-123",
    "platform": "android"
  }'

# Check API docs
open http://localhost:8000/docs
```

---

### Step 6: Test Notification Scheduler

Run the scheduler script manually:

```bash
cd backend
python send_race_notifications.py
```

Check the output and logs in `race_notifications.log`.

---

### Step 7: Set Up Cron Job (Production)

#### Option A: Using the Setup Script

```bash
cd backend
./setup_notification_cron.sh
```

This sets up cron jobs to run:
- **8:00 AM daily**: Send notifications for tomorrow's races
- **7:00 PM daily**: Send notifications for today's races

#### Option B: Manual Cron Setup

```bash
crontab -e
```

Add these lines:

```cron
# Race notifications (8 AM daily)
0 8 * * * cd /path/to/backend && python3 send_race_notifications.py >> race_notifications.log 2>&1

# Race notifications (7 PM daily)
0 19 * * * cd /path/to/backend && python3 send_race_notifications.py >> race_notifications.log 2>&1
```

**For GCP Cloud Run / Cloud Scheduler:**

Since your backend is on GCP, you should use **Cloud Scheduler** instead of cron:

1. Go to [Cloud Scheduler Console](https://console.cloud.google.com/cloudscheduler)
2. Click **"Create Job"**
3. Configure:
   - **Name**: `race-notifications-morning`
   - **Frequency**: `0 8 * * *` (8 AM daily)
   - **Timezone**: Select your timezone
   - **Target**: HTTP
   - **URL**: `https://your-backend-url.run.app/api/v1/notifications/send-scheduled`
   - **HTTP method**: POST
   - **Auth header**: Add authentication if required

4. Create another job for evening (`0 19 * * *` at 7 PM)

**Note**: You'll need to create a new endpoint `/api/v1/notifications/send-scheduled` that calls the scheduler logic, or deploy the `send_race_notifications.py` script as a separate Cloud Function.

---

### Step 8: Deploy to GCP

#### Update Backend Deployment

1. **Build and deploy** your updated backend:

```bash
cd backend
./deploy-gcp.sh
```

2. **Upload Firebase credentials** to GCP Secret Manager:

```bash
# Create secret
gcloud secrets create firebase-credentials \
    --data-file=gcp-key.json \
    --replication-policy="automatic"

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding firebase-credentials \
    --member="serviceAccount:YOUR-SERVICE-ACCOUNT@PROJECT-ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

3. **Update Cloud Run service** to mount the secret:

```bash
gcloud run services update naad-bailgada-backend \
    --update-secrets=/secrets/firebase-credentials=firebase-credentials:latest
```

4. **Update code** to read from secret path:

In `app/main.py`, initialize Firebase on startup:

```python
from app.services.firebase_service import firebase_service

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # Initialize Firebase
    firebase_service.initialize("/secrets/firebase-credentials")
```

---

## 📱 Mobile App Testing

### Test on Android

1. Run the app on a physical device or emulator with Google Play Services:

```bash
cd mobile_app
flutter run
```

2. Check logs for FCM token:

```
flutter logs | grep "FCM Token"
```

3. The app will automatically:
   - Request notification permissions
   - Get FCM token
   - Subscribe to `all_races` topic

### Test on iOS

1. Run on a physical iOS device (simulator doesn't support notifications):

```bash
cd mobile_app
flutter run -d <device-id>
```

2. Grant notification permissions when prompted

3. Check logs for FCM token

---

## 🧪 Testing Notifications

### Send a Test Notification via Firebase Console

1. Go to [Firebase Console](https://console.firebase.google.com/project/naad-bailgada/notification)
2. Click **"Cloud Messaging"** → **"Send your first message"**
3. Fill in:
   - **Notification title**: "Test Race Tomorrow!"
   - **Notification text**: "Sangli Championship starts tomorrow"
   - **Target**: Topic → `all_races`
4. Click **"Send test message"**
5. Check your mobile device

### Send Test via Backend API

Create a test race for tomorrow:

```bash
# Create a race day for tomorrow
curl -X POST "https://your-backend-url.run.app/api/v1/races/..." \
  -H "Content-Type: application/json" \
  -d '{
    "race_date": "2025-12-26",
    ...
  }'

# Manually trigger scheduler
python send_race_notifications.py
```

---

## 📊 Monitoring

### Check Notification Logs

```bash
# View scheduler logs
tail -f backend/race_notifications.log

# View backend API logs
tail -f backend/api.log

# GCP Cloud Logging
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

### Firebase Console

- [Firebase Console - Cloud Messaging](https://console.firebase.google.com/project/naad-bailgada/notification)
- View delivery statistics, error rates, etc.

---

## 🔧 Troubleshooting

### Mobile app not receiving notifications

1. **Check permissions**:
   - Android: Settings → Apps → Naad Bailgada → Notifications (Enabled)
   - iOS: Settings → Naad Bailgada → Notifications (Allow)

2. **Check FCM token registration**:
   ```bash
   # Check if token is in database
   psql $DATABASE_URL -c "SELECT * FROM device_tokens;"
   ```

3. **Check logs**:
   ```bash
   flutter logs | grep "Notification"
   ```

### Backend not sending notifications

1. **Check Firebase credentials**:
   ```bash
   # Verify gcp-key.json exists
   ls -la backend/gcp-key.json
   ```

2. **Test Firebase connection**:
   ```python
   from app.services.firebase_service import firebase_service
   firebase_service.initialize("gcp-key.json")
   firebase_service.send_to_topic("all_races", "Test", "Testing notifications")
   ```

3. **Check scheduler logs**:
   ```bash
   cat backend/race_notifications.log
   ```

### No races found

1. **Verify race data**:
   ```bash
   # Check races in database
   psql $DATABASE_URL -c "SELECT * FROM race_days WHERE race_date >= NOW() ORDER BY race_date;"
   ```

2. **Check scheduler logic**:
   - Scheduler only sends for `status='scheduled'` races
   - Check date filters in `send_race_notifications.py`

---

## 📝 API Endpoints

### Register Device Token
```http
POST /api/v1/notifications/register-device
Content-Type: application/json

{
  "device_token": "fGhI...XyZ",
  "platform": "android"
}
```

### Unregister Device Token
```http
DELETE /api/v1/notifications/unregister-device
Content-Type: application/json

{
  "device_token": "fGhI...XyZ"
}
```

### Get My Devices (Authenticated)
```http
GET /api/v1/notifications/my-devices
Authorization: Bearer <token>
```

---

## 💰 Cost Summary

- **Firebase Cloud Messaging**: FREE (unlimited)
- **Cloud Scheduler**: $0.10 per job/month (~$0.20/month for 2 jobs)
- **Database storage**: ~1-2 GB for 100K users (within free tier)
- **Total**: ~₹0-20/month

---

## ✅ Checklist

- [ ] Firebase project created and FCM enabled
- [ ] Mobile app configured (Android + iOS)
- [ ] Flutter packages installed
- [ ] Backend dependencies installed (`firebase-admin`)
- [ ] Database migration run (`device_tokens` table created)
- [ ] Firebase service account key (`gcp-key.json`) in place
- [ ] Backend API endpoints tested
- [ ] Notification scheduler script tested
- [ ] Cron job / Cloud Scheduler set up
- [ ] Backend deployed to GCP with Firebase credentials
- [ ] Test notifications sent and received successfully

---

## 📞 Support

For issues or questions:
- Check logs: `race_notifications.log`, `api.log`
- Review Firebase Console for delivery stats
- Verify database has device tokens and race data

**Notification system is now fully implemented! 🎉**
