#!/bin/bash
# Script to start the webhook backend service
# Uses Python threads for background processing (no Redis/Celery needed)

echo "🚀 Starting Webhook Backend Service..."
echo ""

# Check if Flask app is running
if ! curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "Flask app is not running"
    echo "Starting Flask app..."
    
    cd "$(dirname "$0")"
    source venv/bin/activate
    
    # Start Flask app in background
    python3 run.py > flask.log 2>&1 &
    FLASK_PID=$!
    echo " Flask app started (PID: $FLASK_PID)"
    echo "   Logs: backend/flask.log"
    sleep 2
else
    echo "Flask app is already running"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Service is running!"
echo ""
echo " Flask API: http://localhost:8000"
echo " Health Check: http://localhost:8000/"
echo " Webhook: http://localhost:8000/v1/webhooks/transactions"
echo ""
echo ""
echo "To stop the service:"
echo "  pkill -f 'python3 run.py'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

