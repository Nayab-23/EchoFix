#!/bin/bash
set -e

# EchoFix Deployment Script
# Brings up the entire stack (Backend + n8n)

echo "🚀 EchoFix Deployment Script"
echo "=============================="

# Check if .env exists
if [ ! -f backend/.env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp backend/.env.example backend/.env
    echo ""
    echo "📝 IMPORTANT: Please edit backend/.env and add your API keys:"
    echo "   - GEMINI_API_KEY (required for AI features)"
    echo "   - GITHUB_TOKEN (required for GitHub integration)"
    echo "   - SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (required for database)"
    echo ""
    echo "After updating .env, run this script again."
    exit 1
fi

# Load environment variables to check configuration
source backend/.env

# Check critical environment variables
echo "🔍 Checking configuration..."

MISSING_VARS=()

if [ "$DEMO_MODE" != "true" ]; then
    if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" = "your_gemini_api_key" ]; then
        MISSING_VARS+=("GEMINI_API_KEY")
    fi

    if [ -z "$GITHUB_TOKEN" ] || [ "$GITHUB_TOKEN" = "your_github_personal_access_token" ]; then
        MISSING_VARS+=("GITHUB_TOKEN")
    fi

    if [ -z "$SUPABASE_URL" ] || [ "$SUPABASE_URL" = "https://your-project.supabase.co" ]; then
        MISSING_VARS+=("SUPABASE_URL")
    fi

    if [ -z "$SUPABASE_SERVICE_ROLE_KEY" ] || [ "$SUPABASE_SERVICE_ROLE_KEY" = "your_service_role_key" ]; then
        MISSING_VARS+=("SUPABASE_SERVICE_ROLE_KEY")
    fi
fi

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo ""
    echo "❌ Missing required environment variables in backend/.env:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please update backend/.env with your credentials."
    echo ""
    echo "💡 Running in DEMO_MODE? Set DEMO_MODE=true in backend/.env to skip API requirements."
    exit 1
fi

echo "✅ Configuration looks good!"
echo ""

# Generate n8n encryption key if not set
if ! grep -q "N8N_ENCRYPTION_KEY" backend/.env 2>/dev/null || grep -q "change-this-to-random-string" backend/.env 2>/dev/null; then
    echo "🔐 Generating n8n encryption key..."
    N8N_KEY=$(openssl rand -hex 32)
    echo "N8N_ENCRYPTION_KEY=$N8N_KEY" >> backend/.env
    echo "✅ n8n encryption key generated"
fi

# Build and start services
echo ""
echo "🏗️  Building Docker images..."
docker-compose build --no-cache

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."

# Wait for backend health check
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker-compose ps | grep -q "echofix-backend.*healthy"; then
        echo "✅ Backend is healthy!"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Attempt $RETRY_COUNT/$MAX_RETRIES - Waiting for backend..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Backend failed to become healthy. Check logs with: docker-compose logs backend"
    exit 1
fi

# Check n8n
sleep 5
if docker-compose ps | grep -q "echofix-n8n.*Up"; then
    echo "✅ n8n is running!"
else
    echo "⚠️  n8n may not be running properly. Check logs with: docker-compose logs n8n"
fi

echo ""
echo "=============================="
echo "🎉 EchoFix is now running!"
echo "=============================="
echo ""
echo "📍 Service URLs:"
echo "   Backend API:  http://localhost:8000"
echo "   Health Check: http://localhost:8000/health"
echo "   n8n:          http://localhost:5678"
echo ""
echo "📊 View logs:"
echo "   All services: docker-compose logs -f"
echo "   Backend only: docker-compose logs -f backend"
echo "   n8n only:     docker-compose logs -f n8n"
echo ""
echo "🛑 Stop services:"
echo "   ./stop.sh"
echo ""
echo "🔄 Restart services:"
echo "   ./restart.sh"
echo ""
echo "🗑️  Remove everything:"
echo "   ./teardown.sh"
echo ""

# Run health check
echo "🏥 Running health check..."
sleep 2

HEALTH_RESPONSE=$(curl -s http://localhost:8000/health || echo "failed")

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✅ Health check passed!"
    echo ""
    echo "Response:"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    echo "⚠️  Health check returned unexpected response:"
    echo "$HEALTH_RESPONSE"
fi

echo ""
echo "🎯 Next Steps:"
echo "   1. Open http://localhost:5678 to access n8n workflows"
echo "   2. Check backend/README.md for API documentation"
echo "   3. Import workflows from workflows/ directory into n8n"
echo ""
