#!/bin/bash

# EchoFix Stop Script
# Gracefully stops all services without removing data

echo "🛑 Stopping EchoFix services..."
echo ""

docker-compose stop

echo ""
echo "✅ All services stopped!"
echo ""
echo "Services are stopped but data is preserved."
echo ""
echo "🚀 Start again with: ./deploy.sh (or docker-compose up -d)"
echo "🗑️  Remove everything: ./teardown.sh"
echo ""
