#!/usr/bin/env bash
# setup.sh - Simple setup script for mcp-github-repo-creator
set -e

if [ ! -f requirements.txt ]; then
  echo "requirements.txt not found!"
  exit 1
fi

# Create venv if not exists
echo "Creating virtual environment..."
python3 -m venv venv

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "Setup complete!"
