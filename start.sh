#!/bin/bash
cd /home/pi/iot-kiosk-project

# Kill any old ngrok instances
pkill -f ngrok 2>/dev/null
sleep 1

# Start ngrok in background
ngrok http 5000 --log=stdout > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!
echo "[STARTUP] ngrok started (PID $NGROK_PID)"

# Wait for ngrok to get a URL
sleep 3

# Get the ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
data = json.load(sys.stdin)
tunnels = data.get('tunnels', [])
for t in tunnels:
    if t.get('proto') == 'https':
        print(t['public_url'])
        break
" 2>/dev/null)

if [ -z "$NGROK_URL" ]; then
    echo "[STARTUP] ngrok URL not found, using local IP"
    NGROK_URL="http://172.20.10.2:5000"
else
    echo "[STARTUP] ngrok URL: $NGROK_URL"
fi

# Export so Flask can use it
export BASE_URL=$NGROK_URL

# Update QR code base URL in Firebase so it's accessible
python3 -c "
import sys, os
sys.path.insert(0, '.')
from services.firebase_config import db
db.child('config').set({'base_url': '$NGROK_URL'})
print('[STARTUP] Base URL saved to Firebase:', '$NGROK_URL')
"

# Update fcm_service icon URL
sed -i "s|https://.*ngrok.*\.dev/static|$NGROK_URL/static|g" services/fcm_service.py
sed -i "s|https://YOUR_PI_IP/static|$NGROK_URL/static|g" services/fcm_service.py

echo "[STARTUP] Starting Flask app..."
python app.py
