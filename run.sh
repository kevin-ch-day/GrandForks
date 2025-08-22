#!/usr/bin/env bash
# run.sh - launcher for Android Tool

# Fail fast on errors and unset variables
set -euo pipefail

# Ensure we're running from the script directory so relative paths work
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Allow overriding the Python binary via PYTHON_BIN env var
PYTHON_BIN="${PYTHON_BIN:-python3}"

# Verify that the Python interpreter exists before attempting to run
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "Error: '$PYTHON_BIN' not found. Please install Python 3." >&2
    exit 1
fi

# Run the Python application; allow Ctrl+C to be handled by Python
exec "$PYTHON_BIN" main.py "$@"
