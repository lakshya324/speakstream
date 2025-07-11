#!/bin/bash

# SpeakStream Startup Script
echo "🚀 Starting SpeakStream - Real-time Streaming Chatbot"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if models need to be downloaded
echo "🔍 Checking model availability..."

# Start the backend server
echo "🖥️ Starting FastAPI backend server..."
cd backend
python main.py
