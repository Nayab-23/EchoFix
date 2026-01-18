#!/bin/bash

# EchoFix Logs Viewer
# View logs from running services

SERVICE=${1:-all}

echo "📊 EchoFix Logs Viewer"
echo "====================="
echo ""

if [ "$SERVICE" = "all" ]; then
    echo "Showing logs from all services (press Ctrl+C to exit)..."
    echo ""
    docker-compose logs -f
elif [ "$SERVICE" = "backend" ]; then
    echo "Showing backend logs (press Ctrl+C to exit)..."
    echo ""
    docker-compose logs -f backend
elif [ "$SERVICE" = "frontend" ]; then
    echo "Showing frontend logs (press Ctrl+C to exit)..."
    echo ""
    docker-compose logs -f frontend
elif [ "$SERVICE" = "n8n" ]; then
    echo "Showing n8n logs (press Ctrl+C to exit)..."
    echo ""
    docker-compose logs -f n8n
else
    echo "❌ Unknown service: $SERVICE"
    echo ""
    echo "Usage:"
    echo "   ./logs.sh             - Show all logs"
    echo "   ./logs.sh backend     - Show backend logs only"
    echo "   ./logs.sh frontend    - Show frontend logs only"
    echo "   ./logs.sh n8n         - Show n8n logs only"
    echo ""
    exit 1
fi
