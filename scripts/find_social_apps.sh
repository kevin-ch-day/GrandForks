#!/usr/bin/env bash
# Wrapper for relocated social app finder.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/social/find_social_apps.sh" "$@"
