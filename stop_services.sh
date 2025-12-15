#!/bin/bash
# Script to stop the webhook backend service

echo " Stopping Webhook Backend Service..."
echo ""

# Stop Flask app
if pgrep -f "python3 run.py" > /dev/null; then
    pkill -f "python3 run.py"
    echo " Flask app stopped"
else
    echo "ℹ  Flask app was not running"
fi

echo ""
echo " Service stopped"
echo ""
echo "Note: Background threads stop automatically when Flask app stops"

