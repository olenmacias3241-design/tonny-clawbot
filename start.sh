#!/bin/bash

# Claw Bot AI - Quick Start Script

echo "🤖 Starting Claw Bot AI..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys before running the bot!"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Start the server
echo "🚀 Starting Claw Bot AI server..."
python3 main.py
