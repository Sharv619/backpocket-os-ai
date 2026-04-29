#!/bin/bash

echo "🚀 Starting Docker containers (BackPocket OS, Postgres, Paperless)..."
docker-compose up -d

echo "🌐 Opening workflow.html..."
# Try xdg-open on Linux
if command -v xdg-open &> /dev/null; then
    xdg-open docs/workflow.html
elif command -v open &> /dev/null; then
    open docs/workflow.html
else
    echo "Could not open browser automatically. Please open docs/workflow.html manually."
fi

echo "📱 Starting Flutter App on Chrome..."
if [ -d "flutter_prototype" ]; then
    cd flutter_prototype
    flutter run -d chrome
else
    echo "flutter_prototype directory not found. Please ensure it exists."
fi
