#!/bin/bash

# EchoFix Demo - Open Everything
# Opens all necessary URLs for the demo

echo "🚀 Opening EchoFix Demo..."
echo ""

# Check if services are running
if ! docker ps | grep -q echofix-backend; then
    echo "⚠️  Services not running. Starting them..."
    ./deploy.sh
fi

echo "📊 Opening Dashboard..."
sleep 1
open http://localhost:3000

echo "🔄 Opening n8n Workflow Editor..."
sleep 1
open http://localhost:5678

echo "📝 Opening GitHub Repository..."
sleep 1
open https://github.com/Nayab-23/Resume_Analyzer

echo "🗨️  Opening Reddit Feedback Thread..."
sleep 1
open https://www.reddit.com/r/Resume_Analyszer/comments/1qfzivr/userfeedback/

echo ""
echo "✅ All demo URLs opened!"
echo ""
echo "📍 n8n Login:"
echo "   Email: severin.spagnola@sjsu.edu"
echo "   Password: c08-832mkdsxgxhmp7-a5b4-"
echo ""
echo "📖 Setup Guide: See N8N_SETUP.md"
echo ""
