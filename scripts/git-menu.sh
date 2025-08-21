#!/usr/bin/env bash
# git-menu.sh — quick, menu-driven Git diagnostics
# Usage: ./git-menu.sh

set -uo pipefail

OK="[OK]"; WARN="[!]"; ERR="[X]"; INF="[*]"
note(){ echo "${INF} $*"; }
good(){ echo "${OK} $*"; }
warn(){ echo "${WARN} $*"; }
fail(){ echo "${ERR} $*"; exit 1; }

# Ensure we're inside a Git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  fail "Not inside a Git repository."
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT" || fail "Cannot cd to repo root: $REPO_ROOT"

press_enter(){ read -rp $'\nPress Enter to continue... '; }

detect_default_base(){
  # Try origin/HEAD first, then common fallbacks
  local ref base
  if ref="$(git symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null)"; then
    base="${ref#origin/}"
  elif git show-ref --verify --quiet refs/remotes/origin/main; then
    base="main"
  elif git show-ref --verify --quiet refs/remotes/origin/master; then
    base="master"
  elif git show-ref --verify --quiet refs/heads/main; then
    base="main"
  elif git show-ref --verify --quiet refs/heads/master; then
    base="master"
  else
    base="main"
  fi
  printf '%s' "$base"
}

BASE_DEFAULT="$(detect_default_base)"

ahead_behind(){
  # ahead_behind <upstream> prints "ahead behind" or "-" if none
  local up="$1"
  if [[ -z "$up" ]]; then
    printf -- "- -"
    return
  fi
  if git rev-parse -q --verify "$up" >/dev/null 2>&1; then
    # left=upstream, right=HEAD
    git rev-list --left-right --count "$up"...HEAD 2>/dev/null | awk '{print $2" "$1}'
  else
    printf -- "- -"
  fi
}

repo_overview(){
  echo "---- Repo Overview ----"
  echo "Root:       $REPO_ROOT"
  echo "Git dir:    $(git rev-parse --git-dir)"
  echo "Branch:     $(git rev-parse --abbrev-ref HEAD)"
  local up
  up="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
  if [[ -n "$up" ]]; then
    read -r A B < <(ahead_behind "$up")
    echo "Upstream:   $up (ahead $A / behind $B)"
  else
    echo "Upstream:   (none)"
  fi
  echo "Base:       ${BASE_DEFAULT} (guessed)"
  echo "User:       $(git config user.name) <$(git config user.email)>"
  echo "Remote URL: $(git config --get remote.origin.url)"
  echo "Conflict style: $(git config --get merge.conflictStyle 2>/dev/null || echo default)"
  echo "------------------------"
}

show_remotes(){
  echo "---- Remotes ----"
  git remote -v
  echo
  git remote show origin || true
}

show_branches(){
  echo "---- Local Branches (tracking & ahead/behind) ----"
  # -vv shows upstream; --sort puts most recent first
  git branch -vv --sort=-committerdate
}

fetch_prune(){
  echo "---- Fetch --all --prune ----"
  git fetch --all --prune
}

show_status(){
  echo "---- Status (short) ----"
  git status -sb
  echo
  echo "---- Changed since HEAD ----"
  git diff --name-status HEAD 2>/dev/null || true
  echo
  echo "---- Untracked files ----"
  git ls-files --others --exclude-standard
}

show_conflicts(){
  echo "---- Unmerged paths (if any) ----"
  if ! git diff --name-only --diff-filter=U | sed 's/^/  /'; then true; fi
  echo
  echo "---- Conflict markers in working tree ----"
  if ! git grep -nE '^(<<<<<<<|=======|>>>>>>>)' -- . 2>/dev/null; then
    echo "  (none found)"
  fi
}

diff_vs_base(){
  local base="${1:-$BASE_DEFAULT}"
  echo "---- Diff vs origin/${base} (name-only) ----"
  local target=""
  if git show-ref --verify --quiet "refs/remotes/origin/${base}"; then
    target="origin/${base}"
  elif git show-ref --verify --quiet "refs/heads/${base}"; then
    target="${base}"
  else
    warn "Base '${base}' not found locally; fetching..."
    git fetch origin "${base}" || true
    if git show-ref --verify --quiet "refs/remotes/origin/${base}"; then
      target="origin/${base}"
    fi
  fi
  if [[ -z "$target" ]]; then
    warn "Could not resolve base '${base}'."
    return 0
  fi
  git diff --name-only "$target"...HEAD
}

log_graph(){
  echo "---- Log graph (last 30) ----"
  git --no-pager log --oneline --graph --decorate -n 30
}

last_commit(){
  echo "---- Last commit ----"
  git --no-pager show --stat -1
}

show_stashes(){
  echo "---- Stashes ----"
  git stash list || true
}

choose_base_and_diff(){
  read -rp "Base branch to diff against [default: ${BASE_DEFAULT}]: " b
  b="${b:-$BASE_DEFAULT}"
  diff_vs_base "$b"
}

main_menu(){
  while true; do
    echo
    echo "========== Git Diagnostics Menu =========="
    echo "1) Repo overview"
    echo "2) Remotes & origin details"
    echo "3) Branches (tracking, ahead/behind)"
    echo "4) Fetch --all --prune"
    echo "5) Status & changed files"
    echo "6) Conflicts & conflict markers"
    echo "7) Diff vs base (default: ${BASE_DEFAULT})"
    echo "8) Choose base & diff"
    echo "9) Log graph (last 30)"
    echo "10) Show last commit"
    echo "11) Stashes"
    echo "0) Quit"
    echo "=========================================="
    read -rp "Select an option: " choice
    echo
    case "$choice" in
      1) repo_overview; press_enter ;;
      2) show_remotes; press_enter ;;
      3) show_branches; press_enter ;;
      4) fetch_prune; press_enter ;;
      5) show_status; press_enter ;;
      6) show_conflicts; press_enter ;;
      7) diff_vs_base "$BASE_DEFAULT"; press_enter ;;
      8) choose_base_and_diff; press_enter ;;
      9) log_graph; press_enter ;;
      10) last_commit; press_enter ;;
      11) show_stashes; press_enter ;;
      0) echo "Bye."; exit 0 ;;
      *) echo "Invalid option";;
    esac
  done
}

main_menu
