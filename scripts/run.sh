#!/usr/bin/env bash
# Run script for Streamlit app

set -e

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please create it from .env.example and add your API keys"
    exit 1
fi

echo "🚀 Starting Algorand AI Contract Creator..."
streamlit run src/algorand_ai_contractor/ui/streamlit_app.py
