#!/bin/bash

# Kubernetes Log Explorer Installation Script

set -e

echo "🚀 Installing Kubernetes Log Explorer..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed."
    exit 1
fi

# Check if kubectl is installed and configured
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is required but not installed."
    exit 1
fi

# Check kubectl connection
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ kubectl is not configured or cannot connect to cluster."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Make scripts executable
chmod +x logexplorer.py
chmod +x scripts/*.sh

# Create symlink for global access (optional)
read -p "Create global symlink for 'logexplorer' command? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo ln -sf "$(pwd)/logexplorer.py" /usr/local/bin/logexplorer
    echo "✅ Global 'logexplorer' command created"
fi

echo "🎉 Installation completed successfully!"
echo ""
echo "📋 Quick Start:"
echo "  CLI: ./logexplorer.py pods"
echo "  Web: python3 webapp.py"
echo ""
echo "📖 For more information, see README.md"