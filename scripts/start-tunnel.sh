#!/bin/bash
# BackPocket OS — Cloudflare Tunnel Startup Script
# Run this to expose your backend to the world

cd /home/lade/Hackathons/.git/backpocket-mvp

# Check if backend is running
if ! pgrep -f "uvicorn main:app" > /dev/null; then
    echo "🚀 Starting backend..."
    source venv/bin/activate
    nohup python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
    sleep 3
fi

# Start cloudflared tunnel
echo "🌐 Starting Cloudflare Tunnel..."
nohup ~/cloudflared tunnel --url http://127.0.0.1:8000 > /tmp/tunnel.log 2>&1 &

# Wait for tunnel
sleep 5

# Get the URL
TUNNEL_URL=$(grep -o 'https://[^ ]*trycloudflare.com' /tmp/tunnel.log | head -1)

echo "✅ Your backend is live at: $TUNNEL_URL"
echo ""
echo "Test the API:"
echo "  curl $TUNNEL_URL/api/mobile/pending"
echo ""
echo "Frontend: https://os.backpocketsystem.io (already live)"
echo ""
echo "Logs:"
echo "  Backend: tail /tmp/backend.log"
echo "  Tunnel:  tail /tmp/tunnel.log"