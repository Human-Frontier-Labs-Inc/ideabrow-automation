#!/bin/bash
"""
Enhanced Webhook Server Startup Script
Starts the webhook server with virtual environment
"""

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/../venv"

echo "Starting Enhanced Webhook Server..."
echo "Script directory: $SCRIPT_DIR"
echo "Virtual environment: $VENV_DIR"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please run: cd $(dirname "$SCRIPT_DIR") && python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install/update requirements
echo "Installing requirements..."
pip install -r "$SCRIPT_DIR/requirements.txt"

# Set environment variables
export WEBHOOK_PORT=${WEBHOOK_PORT:-8090}
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

echo "Starting webhook server on port $WEBHOOK_PORT..."
echo "Features enabled:"
echo "  - Request deduplication"
echo "  - State management"
echo "  - 5-minute project cooldown"
echo "  - Enhanced error handling"
echo "  - Admin endpoints"
echo ""

# Start the server
cd "$SCRIPT_DIR"
python3 webhook_server.py