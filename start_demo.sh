#!/bin/bash
# EchoFix Demo Startup Script

echo "🚀 Starting EchoFix for CruzHacks 2026 Demo"
echo "=========================================="
echo ""

# Start backend and n8n with Docker
echo "📦 Starting backend services (Docker)..."
docker-compose up -d backend n8n

echo "⏳ Waiting for backend to be healthy..."
sleep 5

# Start frontend in dev mode
echo "🎨 Starting frontend with frosted glass UI..."
cd frontend && npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ EchoFix is starting up!"
echo ""
echo "📍 Services:"
echo "   - Frontend: http://localhost:3000 (Frosted Glass UI)"
echo "   - Backend API: http://localhost:8000"
echo "   - n8n Automation: http://localhost:5678"
echo ""
echo "💡 To stop: Press Ctrl+C, then run: docker-compose down"
echo ""

# Wait for frontend process
wait $FRONTEND_PID
