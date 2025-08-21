#!/usr/bin/env bash
# setup.sh - install dependencies for Android Tool

set -e  # stop if any command fails

if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found!"
    exit 1
fi

echo "📦 Installing dependencies from requirements.txt..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "✅ Setup complete. You can now run ./run.sh"
