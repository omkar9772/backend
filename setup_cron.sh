#!/bin/bash
# Setup cron job for expiring user bull listings
# This script adds a cron job to run daily at 2 AM

BACKEND_DIR="/Users/omkar/Documents/Naad/Repos/backend"
CRON_COMMAND="0 2 * * * cd $BACKEND_DIR && /usr/bin/python3 expire_user_bulls.py >> $BACKEND_DIR/expire_bulls.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "expire_user_bulls.py"; then
    echo "Cron job for expiring user bulls already exists."
    echo "Current cron jobs:"
    crontab -l | grep "expire_user_bulls.py"
else
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -
    echo "✓ Cron job added successfully!"
    echo "  Schedule: Daily at 2:00 AM"
    echo "  Script: $BACKEND_DIR/expire_user_bulls.py"
    echo "  Log file: $BACKEND_DIR/expire_bulls.log"
fi

echo ""
echo "To view all cron jobs: crontab -l"
echo "To remove this cron job: crontab -e (then delete the line)"
echo ""
echo "Manual test: cd $BACKEND_DIR && python3 expire_user_bulls.py"
