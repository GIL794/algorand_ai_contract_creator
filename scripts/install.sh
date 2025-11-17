#!/usr/bin/env bash
# Installation script for Unix-based systems

set -e

echo "🔗 Algorand AI Contract Creator - Installation"
echo "=============================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install package in editable mode
echo "📥 Installing package in editable mode..."
pip install -e .

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if we should install dev dependencies
if [ "$1" == "--dev" ]; then
    echo "📥 Installing development dependencies..."
    pip install -r requirements-dev.txt
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "To activate the environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To start the Streamlit app, run:"
echo "  ./scripts/run.sh"
echo "  OR: python main.py"
