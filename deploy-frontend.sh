#!/bin/bash
set -e

# EchoFix Frontend Deployment Script
# Deploy frontend separately or rebuild it

echo "🎨 EchoFix Frontend Deployment"
echo "================================"

cd "$(dirname "$0")"

# Check if backend is running
if ! docker ps | grep -q "echofix-backend.*healthy"; then
    echo "⚠️  Backend is not running or not healthy!"
    echo "Please deploy backend first with: ./deploy.sh"
    exit 1
fi

echo ""
echo "🏗️  Building frontend Docker image..."
docker-compose build frontend

echo ""
echo "🚀 Starting frontend..."
docker-compose up -d frontend

echo ""
echo "⏳ Waiting for frontend to start..."
sleep 5

# Check if frontend is accessible
MAX_RETRIES=20
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend is accessible!"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Attempt $RETRY_COUNT/$MAX_RETRIES - Waiting for frontend..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Frontend failed to start. Check logs with: docker-compose logs frontend"
    exit 1
fi

echo ""
echo "=============================="
echo "🎉 Frontend is now running!"
echo "=============================="
echo ""
echo "📍 Access Dashboard:"
echo "   http://localhost:3000"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f frontend"
echo ""
echo "🛑 Stop frontend:"
echo "   docker-compose stop frontend"
echo ""
