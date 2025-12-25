#!/bin/bash

# Setup local cron job for race notifications on Mac
# This will run automatically every day at 8 AM and 7 PM

echo "Setting up automated race notifications..."

# Get the absolute path to the backend directory
BACKEND_DIR="/Users/omkar/Documents/Naad/Repos/backend"

# Get Python3 path
PYTHON_PATH=$(which python3)

echo "Backend directory: $BACKEND_DIR"
echo "Python path: $PYTHON_PATH"

# Create cron job entries
CRON_MORNING="0 8 * * * cd $BACKEND_DIR && $PYTHON_PATH send_race_notifications.py >> race_notifications.log 2>&1"
CRON_EVENING="0 19 * * * cd $BACKEND_DIR && $PYTHON_PATH send_race_notifications.py >> race_notifications.log 2>&1"

# Check if cron jobs already exist
if crontab -l 2>/dev/null | grep -q "send_race_notifications.py"; then
    echo "⚠️  Cron jobs already exist!"
    echo ""
    echo "Current cron jobs:"
    crontab -l | grep "send_race_notifications.py"
    echo ""
    read -p "Do you want to replace them? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Cancelled. Cron jobs not modified."
        exit 0
    fi
    # Remove existing jobs
    crontab -l | grep -v "send_race_notifications.py" | crontab -
fi

# Add new cron jobs
(crontab -l 2>/dev/null; echo "$CRON_MORNING") | crontab -
(crontab -l 2>/dev/null; echo "$CRON_EVENING") | crontab -

echo ""
echo "✅ Cron jobs added successfully!"
echo ""
echo "📅 Schedule:"
echo "   - 8:00 AM daily: Check and send notifications for tomorrow's races"
echo "   - 7:00 PM daily: Check and send notifications for today's races"
echo ""
echo "📋 To view your cron jobs:"
echo "   crontab -l"
echo ""
echo "📝 Logs will be saved to:"
echo "   $BACKEND_DIR/race_notifications.log"
echo ""
echo "🗑️  To remove cron jobs:"
echo "   crontab -e (then delete the lines with send_race_notifications.py)"
echo ""
echo "⚠️  IMPORTANT: Your Mac must be awake at 8 AM and 7 PM for this to work!"
echo "   To keep Mac awake: System Settings → Energy Saver → Prevent automatic sleeping"
echo ""
echo "✅ Setup complete!"
