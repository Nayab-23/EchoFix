#!/bin/bash

# EchoFix Status Script
# Shows the current status of all services

echo "📊 EchoFix Status"
echo "================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

echo "🐳 Docker Status: ✅ Running"
echo ""

# Show container status
echo "📦 Container Status:"
echo ""
docker-compose ps

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check backend health
echo "🏥 Backend Health Check:"
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health 2>/dev/null)

if [ $? -eq 0 ] && echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✅ Backend is healthy and responding"
    echo ""
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    echo "❌ Backend is not responding or unhealthy"
    echo ""
    if docker-compose ps | grep -q "echofix-backend"; then
        echo "Container is running but not healthy. Check logs with:"
        echo "   ./logs.sh backend"
    else
        echo "Container is not running. Start with:"
        echo "   ./deploy.sh"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check n8n
echo "🔄 n8n Status:"
if curl -s http://localhost:5678 > /dev/null 2>&1; then
    echo "✅ n8n is accessible at http://localhost:5678"
else
    echo "❌ n8n is not responding"
    echo ""
    if docker-compose ps | grep -q "echofix-n8n"; then
        echo "Container is running but not accessible. Check logs with:"
        echo "   ./logs.sh n8n"
    else
        echo "Container is not running. Start with:"
        echo "   ./deploy.sh"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Show resource usage
echo "💾 Resource Usage:"
echo ""
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker-compose ps -q 2>/dev/null) 2>/dev/null || echo "No containers running"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Quick commands
echo "🛠️  Quick Commands:"
echo ""
echo "   View logs:    ./logs.sh [backend|n8n]"
echo "   Restart:      ./restart.sh"
echo "   Stop:         ./stop.sh"
echo "   Teardown:     ./teardown.sh"
echo ""
