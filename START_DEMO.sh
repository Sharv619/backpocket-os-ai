#!/usr/bin/env bash
# BackPocket OS - One-command demo launcher
# Usage: ./START_DEMO.sh
set -e

cd "$(dirname "$0")"

echo "🚀 BackPocket OS - Demo Launcher"
echo "================================"

# 1. Seed fresh demo data
echo ""
echo "📦 Seeding demo data..."
python3 scripts/demo_seed.py

# 2. Check .env exists
if [ ! -f ".env" ]; then
  echo ""
  echo "⚠️  WARNING: .env file not found!"
  echo "   Copy .env.example → .env and fill in your API keys"
  echo "   Running in demo mode (no real sends)..."
fi

# 3. Start server
echo ""
echo "🖥️  Starting BackPocket server on http://127.0.0.1:8000"
echo "   Dashboard: http://127.0.0.1:8000/static/index.html"
echo "   Press Ctrl+C to stop"
echo ""
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
