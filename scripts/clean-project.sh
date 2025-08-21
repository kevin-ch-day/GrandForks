#!/usr/bin/env bash
# File: scripts/clean-project.sh
# Cleaner for Android_Tool project (Fedora only)

set -euo pipefail
OK="[OK]"; INF="[*]"; ERR="[X]"

say(){ echo -e "${INF} $*"; }
good(){ echo -e "\033[32m${OK}\033[0m $*"; }
fail(){ echo -e "\033[31m${ERR}\033[0m $*"; exit 1; }

usage(){
  cat <<EOF
Usage: $0 [options]

Options:
  -n, --dry-run     Show what would be removed without deleting
  -f, --full        Also remove database files (*.db) and all logs/
  --venv            Remove .venv/ (virtual environment)
  -h, --help        Show this help
EOF
}

# Defaults
DRY_RUN=0
FULL=0
WIPE_VENV=0

# Parse args
while (($#)); do
  case "$1" in
    -n|--dry-run) DRY_RUN=1 ;;
    -f|--full) FULL=1 ;;
    --venv) WIPE_VENV=1 ;;
    -h|--help) usage; exit 0 ;;
    *) usage; fail "Unknown option: $1" ;;
  esac
  shift
done

# Fedora guard
if [[ -r /etc/os-release ]]; then
  . /etc/os-release
  [[ "${ID:-}" == "fedora" || "${ID_LIKE:-}" == *"fedora"* ]] || fail "This script is restricted to Fedora."
else
  fail "Cannot detect OS (missing /etc/os-release)."
fi

# Resolve project root
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(realpath "${SCRIPT_DIR}/..")"
cd "$PROJECT_ROOT" || fail "Cannot cd to project root: $PROJECT_ROOT"

# Validate project
[[ -f "main.py" ]] || fail "main.py not found—are you in the project root?"
[[ -f "requirements.txt" ]] || fail "requirements.txt missing—are you in the repo root?"

say "Cleaning project at: $PROJECT_ROOT"

# Helper to run or preview deletions
remove() {
  local msg="$1"; shift
  if (( DRY_RUN )); then
    say "Would remove $msg"
    find "$@" -print
  else
    find "$@" -print -delete
    good "Removed $msg"
  fi
}

remove_dir() {
  local dir="$1"
  if [[ -d "$dir" ]]; then
    if (( DRY_RUN )); then
      say "Would remove directory $dir"
    else
      rm -rf -- "$dir"
      good "Removed directory $dir"
    fi
  fi
}

# Standard cleanup targets
remove "*.pyc/pyo" . -type f \( -name '*.pyc' -o -name '*.pyo' \)
remove "__pycache__ dirs" . -type d -name '__pycache__'
remove ".pytest_cache dirs" . -type d -name '.pytest_cache'
remove ".mypy_cache dirs" . -type d -name '.mypy_cache'
remove ".ruff_cache dirs" . -type d -name '.ruff_cache'
remove "coverage files" . -type f \( -name '.coverage' -o -name '.coverage.*' -o -name 'coverage.xml' \)

remove_dir "htmlcov"
remove_dir "dist"
remove_dir "build"

# Logs handling
if (( FULL )); then
  remove "log files" . -type f -name '*.log'
  remove_dir "logs"
else
  if [[ -f logs/android_tool.log ]]; then
    if (( DRY_RUN )); then
      say "Would truncate logs/android_tool.log"
    else
      : > logs/android_tool.log
      good "Truncated logs/android_tool.log"
    fi
  fi
fi

# Optional database cleanup
if (( FULL )); then
  remove "database files" database -type f -name '*.db'
fi

# Virtual environment cleanup
if (( WIPE_VENV )); then
  remove_dir ".venv"
fi

good "Cleanup complete."
