#!/bin/bash

# EchoFix Rebuild Script
# Rebuild Docker images and restart services
# Use this after code changes

echo "🔨 Rebuilding EchoFix..."
echo "======================="
echo ""

echo "🛑 Stopping services..."
docker-compose stop

echo ""
echo "🏗️  Rebuilding Docker images (no cache)..."
docker-compose build --no-cache

echo ""
echo "🚀 Starting services with new images..."
docker-compose up -d

echo ""
echo "⏳ Waiting for backend to be healthy..."
sleep 5

MAX_RETRIES=20
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker-compose ps | grep -q "echofix-backend.*healthy"; then
        echo "✅ Backend is healthy!"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Attempt $RETRY_COUNT/$MAX_RETRIES..."
    sleep 2
done

echo ""
echo "✅ Rebuild complete!"
echo ""
echo "📍 Service URLs:"
echo "   Backend API: http://localhost:8000"
echo "   n8n:         http://localhost:5678"
echo ""
echo "📊 View logs: docker-compose logs -f"
echo ""
