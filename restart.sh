#!/bin/bash

# EchoFix Restart Script
# Restart all services (preserves data)

echo "🔄 Restarting EchoFix services..."
echo ""

echo "🛑 Stopping services..."
docker-compose stop

echo ""
echo "🚀 Starting services..."
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
echo "✅ Services restarted!"
echo ""
echo "📍 Service URLs:"
echo "   Backend API: http://localhost:8000"
echo "   n8n:         http://localhost:5678"
echo ""
echo "📊 View logs: docker-compose logs -f"
echo ""
