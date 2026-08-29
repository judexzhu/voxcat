#!/bin/bash
set -e

echo "=== Voxcat Setup ==="

# Check prerequisites
command -v uv >/dev/null 2>&1 || { echo "uv not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }

# Python dependencies
echo "Installing Python dependencies..."
uv sync

# Rebuild frontend (optional — only if Node.js is available and you changed client/src)
if command -v node >/dev/null 2>&1 && [ -f client/package.json ]; then
    echo "Node.js found — rebuilding frontend..."
    cd client && npm ci --silent && npm run build && cd ..
else
    echo "Using pre-built frontend (client/dist/)"
fi

# Copy client/dist into package for `uv run voxcat` to find it
if [ -d client/dist ]; then
    mkdir -p src/voxcat/client
    cp -r client/dist src/voxcat/client/dist
fi

# Configuration files
if [ ! -f config.yaml ]; then
    cp config.yaml.example config.yaml
    echo "Created config.yaml from template."
fi

if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "Created .env from template. Edit it with your API keys:"
    echo "  GOOGLE_API_KEY (required)"
    echo "  TAVILY_API_KEY (optional — web search)"
    echo ""
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "Run:  uv run voxcat"
echo "Open: http://localhost:7860"
