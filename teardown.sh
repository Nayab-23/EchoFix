#!/bin/bash

# EchoFix Teardown Script
# Completely removes all containers, volumes, and images

echo "🗑️  EchoFix Complete Teardown"
echo "=============================="
echo ""
echo "⚠️  WARNING: This will:"
echo "   - Stop all running containers"
echo "   - Remove all containers"
echo "   - Remove all volumes (n8n data will be lost)"
echo "   - Remove Docker images"
echo ""

read -p "Are you sure you want to continue? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "❌ Teardown cancelled."
    exit 0
fi

echo "🛑 Stopping all services..."
docker-compose down

echo ""
echo "🗑️  Removing containers and networks..."
docker-compose down --remove-orphans

echo ""
echo "📦 Removing volumes (n8n data, etc.)..."
docker-compose down -v

echo ""
echo "🖼️  Removing Docker images..."
docker-compose down --rmi all -v

echo ""
echo "✅ Complete teardown finished!"
echo ""
echo "All EchoFix containers, volumes, and images have been removed."
echo ""
echo "🚀 To deploy again: ./deploy.sh"
echo ""
