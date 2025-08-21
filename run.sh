#!/usr/bin/env bash
# run.sh - launcher for Android Tool

# run Python app, handle Ctrl+C gracefully
trap 'echo -e "\n\n⚠️  Interrupted. Exiting..."; exit 130' INT

python3 main.py
