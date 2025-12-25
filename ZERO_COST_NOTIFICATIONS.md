# 🎉 Zero-Cost Push Notifications - Complete Guide

## 💰 Total Cost: ₹0 (FREE!)

This guide shows you how to send race notifications **completely free** using Firebase topic-based messaging.

---

## ✅ What's Set Up (All Free!)

1. ✅ Firebase Cloud Messaging (FREE - unlimited notifications)
2. ✅ Mobile app auto-subscribes to `all_races` topic
3. ✅ Backend API with Firebase Admin SDK
4. ✅ Device tokens stored in Neon DB (free tier)

---

## 📱 How It Works

1. **User opens app** → Auto-subscribes to `all_races` topic
2. **You send notification** → Firebase delivers to ALL subscribed users
3. **100% FREE** → No Cloud Scheduler, no cron jobs needed!

---

## 🚀 How to Send Notifications (3 Free Methods)

### Method 1: Firebase Console (Easiest - Click & Send)

**Perfect for**: Manual notifications, testing

1. Go to: https://console.firebase.google.com/project/naad-bailgada/notification/compose
2. Click **"New notification"**
3. Fill in:
   ```
   Title: 🏁 Race Tomorrow!
   Text: Sangli Championship starts tomorrow at Sangli Stadium
   ```
4. Click **"Next"**
5. **Target**: Topic → `all_races`
6. **Scheduling**: (optional) Set send time
7. Click **"Review"** → **"Publish"**

✅ **Done! All users with the app will get the notification.**

---

### Method 2: Backend API Call (For Automation)

**Perfect for**: Integrating with admin panel, automated scripts

#### Send Notification for a Race

```bash
curl -X POST "http://localhost:8000/api/v1/notifications/send-race-notification?race_id=YOUR-RACE-ID&notification_type=one_day_before"
```

**Parameters:**
- `race_id`: UUID of the race (from your database)
- `notification_type`:
  - `one_day_before` → "Race Tomorrow!" message
  - `race_day` → "Race Today!" message

**Example:**

```bash
# Tomorrow's race notification
curl -X POST "http://localhost:8000/api/v1/notifications/send-race-notification?race_id=123e4567-e89b-12d3-a456-426614174000&notification_type=one_day_before"

# Today's race notification
curl -X POST "http://localhost:8000/api/v1/notifications/send-race-notification?race_id=123e4567-e89b-12d3-a456-426614174000&notification_type=race_day"
```

---

### Method 3: Python Script (Run Manually)

**Perfect for**: Running from your local machine or server

The script `/backend/send_race_notifications.py` is already created. Just run:

```bash
cd /Users/omkar/Documents/Naad/Repos/backend
python3 send_race_notifications.py
```

**What it does:**
- Checks for races happening tomorrow → Sends "Race Tomorrow!" notification
- Checks for races happening today → Sends "Race Today!" notification
- Uses Firebase topic messaging (FREE)
- Logs everything to `race_notifications.log`

**When to run it:**
- Manually: Whenever you want to send notifications
- Scheduled: Add to your computer's crontab (free)
- Server: Run on GCP VM instance (if you have one)

---

## 📋 API Documentation

### Endpoint: Send Race Notification

```http
POST /api/v1/notifications/send-race-notification
Query Parameters:
  - race_id: string (UUID)
  - notification_type: string ("one_day_before" | "race_day")

Response:
{
  "status": "success",
  "message": "Notification sent to all_races topic",
  "race": "Sangli Championship 2025",
  "notification_type": "one_day_before"
}
```

### Test in Swagger UI

1. Start your backend: `python app/main.py`
2. Open: http://localhost:8000/docs
3. Find: **POST /api/v1/notifications/send-race-notification**
4. Click **"Try it out"**
5. Enter race_id and notification_type
6. Click **"Execute"**

---

## 🧪 Testing End-to-End

### Step 1: Run Mobile App

```bash
cd /Users/omkar/Documents/Naad/Repos/mobile_app
flutter run
```

**Check logs for:**
```
✅ Subscribed to race notifications
📱 FCM Token: fGhI...XyZ
```

### Step 2: Send Test Notification

**Option A: Via Firebase Console**
1. Go to Firebase Console → Cloud Messaging
2. Send to topic: `all_races`
3. Check your mobile device

**Option B: Via API**
```bash
# Get a race ID from your database first
# Then send notification
curl -X POST "http://localhost:8000/api/v1/notifications/send-race-notification?race_id=YOUR-RACE-ID&notification_type=race_day"
```

**Option C: Via Python Script**
```bash
python3 send_race_notifications.py
```

### Step 3: Verify on Mobile

- Notification should appear on device
- Tap notification → App opens to race detail

---

## 📊 Monitoring (Free!)

### Firebase Console

View notification statistics:
- Go to: https://console.firebase.google.com/project/naad-bailgada/notification
- See delivery rates, opened rates, etc.

### Backend Logs

```bash
# View notification sending logs
tail -f /Users/omkar/Documents/Naad/Repos/backend/race_notifications.log

# View API logs
tail -f /Users/omkar/Documents/Naad/Repos/backend/api.log
```

### Database

Check subscribed devices:
```sql
SELECT COUNT(*) as total_devices FROM device_tokens;
SELECT platform, COUNT(*) as count FROM device_tokens GROUP BY platform;
```

---

## 🔧 Optional: Manual Scheduling (Still FREE!)

If you want to automate sending notifications without Cloud Scheduler:

### Option 1: Local Cron Job (Your Computer)

```bash
# Edit crontab
crontab -e

# Add these lines (adjust path as needed)
0 8 * * * cd /Users/omkar/Documents/Naad/Repos/backend && python3 send_race_notifications.py >> race_notifications.log 2>&1
0 19 * * * cd /Users/omkar/Documents/Naad/Repos/backend && python3 send_race_notifications.py >> race_notifications.log 2>&1
```

**Runs:**
- 8:00 AM daily
- 7:00 PM daily

**Cost: ₹0** (runs on your computer)

### Option 2: GCP VM Instance (Free Tier)

If you have a GCP VM (e1-micro is FREE tier):

```bash
# SSH into VM
gcloud compute ssh your-vm-instance

# Copy script to VM
# Setup cron job same as above
```

**Cost: ₹0** (within GCP free tier)

---

## 📝 Recommended Workflow

### Daily Workflow (Manual - FREE)

**Morning (8 AM):**
1. Open Firebase Console
2. Send notification to `all_races` topic
3. Message: "Race Tomorrow!" for tomorrow's races

**Evening (7 PM):**
1. Open Firebase Console
2. Send notification to `all_races` topic
3. Message: "Race Today!" for today's races

**Time required:** 2 minutes/day
**Cost:** ₹0

---

## 🎯 Summary

| Feature | Cost | Notes |
|---------|------|-------|
| Firebase Cloud Messaging | ₹0 | Unlimited notifications |
| Topic-based messaging | ₹0 | Broadcast to all users |
| Mobile app subscriptions | ₹0 | Auto-subscribe on app launch |
| Backend API | ₹0 | Deployed on GCP free tier |
| Database storage | ₹0 | Neon DB free tier |
| Manual notifications | ₹0 | Firebase Console / API |
| **TOTAL MONTHLY COST** | **₹0** | 🎉 |

---

## 🔐 Security Notes

- Firebase credentials (`gcp-key.json`) already in place
- Endpoint is public (no auth required for sending notifications)
- **Recommendation**: Add admin authentication if deploying to production

---

## ✅ You're All Set!

**Everything is ready to go:**

1. ✅ Mobile app auto-subscribes users to `all_races` topic
2. ✅ Backend can send notifications via API
3. ✅ Firebase Console ready for manual sends
4. ✅ Python script ready for automated sends
5. ✅ All components deployed and tested
6. ✅ **Total cost: ₹0**

**To send a notification right now:**

1. Go to: https://console.firebase.google.com/project/naad-bailgada/notification/compose
2. Click "New notification"
3. Fill in title and message
4. Select Topic: `all_races`
5. Click "Publish"

**Done! 🎉**

---

## 🆘 Support

- Firebase Console: https://console.firebase.google.com/project/naad-bailgada
- API Docs: http://localhost:8000/docs (when backend is running)
- Logs: `/backend/race_notifications.log`

**Happy notifying! 📱✨**
