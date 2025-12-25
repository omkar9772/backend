#!/bin/bash

# Setup cron job for race notifications
# This script sets up a cron job to run race notifications twice daily

echo "Setting up race notification cron job..."

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Python path (adjust if needed)
PYTHON_PATH=$(which python3)

# Cron job commands
# Run at 8:00 AM daily (for tomorrow's races)
CRON_CMD_MORNING="0 8 * * * cd $DIR && $PYTHON_PATH send_race_notifications.py >> race_notifications.log 2>&1"

# Run at 7:00 PM daily (for today's races reminder)
CRON_CMD_EVENING="0 19 * * * cd $DIR && $PYTHON_PATH send_race_notifications.py >> race_notifications.log 2>&1"

# Add cron jobs
(crontab -l 2>/dev/null; echo "$CRON_CMD_MORNING") | crontab -
(crontab -l 2>/dev/null; echo "$CRON_CMD_EVENING") | crontab -

echo "✅ Cron jobs added successfully!"
echo ""
echo "Scheduled jobs:"
echo "  - 8:00 AM daily: Send notifications for tomorrow's races"
echo "  - 7:00 PM daily: Send notifications for today's races"
echo ""
echo "To view cron jobs: crontab -l"
echo "To remove cron jobs: crontab -e (then delete the lines)"
echo ""
echo "Logs will be written to: $DIR/race_notifications.log"
