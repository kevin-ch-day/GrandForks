#!/usr/bin/env bash
# find_social_apps.sh — robust finder for Twitter/Facebook/Snapchat/TikTok (+variants)
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=android_app_finder.lib.sh
source "$SCRIPT_DIR/android_app_finder.lib.sh"

usage() {
  cat <<'EOF'
Usage: find_social_apps.sh [options]

Connection:
  --serial SERIAL           Use specific adb serial (from `adb devices`).
  --ip HOST[:PORT]          Connect over TCP/IP (device must be in tcpip mode).

Scope:
  --all-users               Scan all Android users (default).
  --user ID                 Scan a specific user only.
  --packages "p1 p2 ..."    Space-separated package list (override defaults).
  --keywords "kw1 kw2"      Also search package names by keywords (CI).
  --include-disabled        Include disabled/hidden packages as candidates.

Output:
  --csv FILE                Write CSV inventory.
  --json FILE               Write NDJSON (one JSON object per line).
  --outdir DIR              Collect artifacts (dumpsys/appops; optional APKs/data).

Actions:
  --test-launch             Attempt to launch found apps with `monkey` (best-effort).
  --collect-apks            Pull base/split APKs for found apps into DIR/apks/.
  --collect-sdcard          Tar & pull /sdcard/Android/{data,media}/<pkg> into DIR/data/.
  --timeout SEC             Snapshot timeout for activity top (default: 5).

Logging:
  --quiet                   Errors only.
  --verbose                 Info-level logs.
  --debug                   Debug logs.
  --no-color                Disable colored output.

Examples:
  ./find_social_apps.sh
  ./find_social_apps.sh --serial ZY22JK89DR --csv social.csv --json social.jsonl
  ./find_social_apps.sh --keywords "facebook twitter tiktok snap" --include-disabled
  ./find_social_apps.sh --outdir artifacts --collect-apks --collect-sdcard --test-launch

Fedora prerequisites:
  sudo dnf install -y android-tools   # adb
  sudo dnf install -y jq              # optional (prettier JSON)
EOF
}

# ------------ Defaults ------------
SERIAL=""; IP=""
CSV=""; JSON=""; OUTDIR=""
USER_ID=""; ALL_USERS=1
TIMEOUT_S=5
INCLUDE_DISABLED=0
TEST_LAUNCH=0
COLLECT_APKS=0
COLLECT_SDCARD=0

# Defaults: requested families (Twitter/X, Facebook, Snapchat, TikTok variants)
PKGS_DEFAULT=(
  com.twitter.android
  com.twitter.android.lite
  com.facebook.katana
  com.snapchat.android
  com.zhiliaoapp.musically
  com.ss.android.ugc.tiktok
  com.zhiliaoapp.musically.go
  com.ss.android.ugc.trill
)

PKGS_OVERRIDE=()
KEYWORDS=()

# ------------ Parse args ------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --serial) SERIAL="${2:-}"; shift 2;;
    --ip) IP="${2:-}"; shift 2;;
    --csv) CSV="${2:-}"; shift 2;;
    --json) JSON="${2:-}"; shift 2;;
    --outdir) OUTDIR="${2:-}"; shift 2;;
    --user) USER_ID="${2:-}"; ALL_USERS=0; shift 2;;
    --all-users) ALL_USERS=1; shift;;
    --packages) read -r -a PKGS_OVERRIDE <<<"${2:-}"; shift 2;;
    --keywords) read -r -a KEYWORDS <<<"${2:-}"; shift 2;;
    --include-disabled) INCLUDE_DISABLED=1; shift;;
    --test-launch) TEST_LAUNCH=1; shift;;
    --collect-apks) COLLECT_APKS=1; shift;;
    --collect-sdcard) COLLECT_SDCARD=1; shift;;
    --timeout) TIMEOUT_S="${2:-5}"; shift 2;;
    --quiet)   AAF_LOG_LEVEL=0; shift;;
    --verbose) AAF_LOG_LEVEL=2; shift;;
    --debug)   AAF_LOG_LEVEL=3; shift;;
    --no-color) AAF_NO_COLOR=1; shift;;
    -h|--help) usage; exit 0;;
    *) aaf_die "Unknown arg: $1 (use --help)";;
  esac
done

# ------------ Error trap ------------
aaf_on_error() {
  aaf_log ERROR "Failed at line $1: $2"
  aaf_log INFO  "Re-run with --debug for verbose logs. Set AAF_SHELL_TIMEOUT=<sec> to tune timeouts."
}
trap 'aaf_on_error "${LINENO}" "${BASH_COMMAND}"' ERR

# ------------ Preconditions ------------
aaf_have adb || aaf_die "adb not found. Fedora: sudo dnf install -y android-tools"

if [[ -z "$SERIAL" && -z "$IP" ]]; then
  aaf_select_device
fi

if [[ -n "$IP" ]]; then
  aaf_log INFO "Connecting to $IP ..."
  adb connect "$IP" >/dev/null 2>&1 || aaf_log WARN "adb connect returned non-zero (continuing)."
  SERIAL="$IP"
fi

ADB="$(aaf_adb_cmd "$SERIAL")"
aaf_check_authorization

STATE="$(aaf_get_state "$ADB")"
[[ "$STATE" == "device" ]] || aaf_die "Device not ready (state: ${STATE:-none}). Try: adb devices -l"

# ------------ Users ------------
if [[ $ALL_USERS -eq 1 ]]; then
  USERS="$(aaf_get_users "$ADB")"
else
  USERS="$USER_ID"
fi
aaf_log DEBUG "Users: $USERS"

# ------------ Packages ------------
PKGS=("${PKGS_OVERRIDE[@]:-${PKGS_DEFAULT[@]}}")

# Keywords expand
if [[ ${#KEYWORDS[@]} -gt 0 ]]; then
  aaf_log INFO "Searching keywords: ${KEYWORDS[*]}"
  for u in $USERS; do
    for k in "${KEYWORDS[@]}"; do
      while IFS= read -r found; do
        [[ -n "$found" ]] && PKGS+=("$found")
      done < <(aaf_search_keywords "$ADB" "$u" "$k")
    done
  done
fi

# Include disabled
if [[ $INCLUDE_DISABLED -eq 1 ]]; then
  for u in $USERS; do
    while IFS= read -r dp; do
      [[ -n "$dp" ]] && PKGS+=("$dp")
    done < <(aaf_list_disabled "$ADB" "$u")
  done
fi

# De-duplicate
mapfile -t PKGS < <(aaf_dedupe_array "${PKGS[@]}")
aaf_log DEBUG "Final package set (#${#PKGS[@]}): ${PKGS[*]}"

# ------------ Outputs ------------
if [[ -n "$CSV" ]]; then
  aaf_csv_header > "$CSV"
fi
if [[ -n "$JSON" ]]; then
  : > "$JSON"
fi

APKS_DIR=""; DATA_DIR=""; TXT_DIR=""
if [[ -n "$OUTDIR" ]]; then
  TXT_DIR="$OUTDIR/text"; mkdir -p "$TXT_DIR"
  if [[ $COLLECT_APKS -eq 1 ]]; then APKS_DIR="$OUTDIR/apks"; mkdir -p "$APKS_DIR"; fi
  if [[ $COLLECT_SDCARD -eq 1 ]]; then DATA_DIR="$OUTDIR/data"; mkdir -p "$DATA_DIR"; fi
fi

# ------------ Scan ------------
ANY_FOUND=0
for u in $USERS; do
  printf '=== USER %s ===\n' "$u"
  for p in "${PKGS[@]}"; do
    paths="$(aaf_pm_path "$ADB" "$u" "$p")"
    if [[ -n "$paths" ]]; then
      printf 'FOUND   %s    %s\n' "$p" "$paths"
      ANY_FOUND=1
      meta="$(aaf_pkg_meta "$ADB" "$p")"
      [[ -n "$CSV"  ]] && aaf_csv_line  "$u" "$p" "FOUND"  "$paths" "$meta" >> "$CSV"
      [[ -n "$JSON" ]] && aaf_json_line "$u" "$p" "FOUND"  "$paths" "$meta" >> "$JSON"
      [[ -n "$TXT_DIR"  ]] && aaf_collect_text "$ADB" "$TXT_DIR" "$p"
      [[ -n "$APKS_DIR" ]] && aaf_collect_apks "$ADB" "$APKS_DIR" "$p" "$u"
      [[ -n "$DATA_DIR" ]] && aaf_collect_sdcard_data "$ADB" "$DATA_DIR" "$p"
      if [[ $TEST_LAUNCH -eq 1 ]]; then
        aaf_log INFO "Test-launching $p …"
        aaf_test_launch "$ADB" "$u" "$p" "$TIMEOUT_S" || true
      fi
    else
      printf 'MISSING %s\n' "$p"
      empty_meta="||||||||" # 8 pipes → 9 fields (empty) for csv/json consistency
      [[ -n "$CSV"  ]] && aaf_csv_line  "$u" "$p" "MISSING" "" "$empty_meta" >> "$CSV"
      [[ -n "$JSON" ]] && aaf_json_line "$u" "$p" "MISSING" "" "$empty_meta" >> "$JSON"
    fi
  done
done

# ------------ Summary ------------
[[ -n "$CSV"  ]] && aaf_log INFO "CSV:  $(readlink -f "$CSV")"
[[ -n "$JSON" ]] && aaf_log INFO "JSON: $(readlink -f "$JSON")"
[[ -n "$OUTDIR" ]] && aaf_log INFO "Artifacts in: $(readlink -f "$OUTDIR")"

exit $ANY_FOUND
