#!/usr/bin/env bash
# setup.sh - Simple setup script for mcp-github-repo-creator
set -e

if [ ! -f requirements.txt ]; then
  echo "requirements.txt not found!"
  exit 1
fi

echo "Delegating setup to setup.py..."
python3 setup.py "$@"
