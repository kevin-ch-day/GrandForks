#!/usr/bin/env bash
# find_social_apps.sh — robust finder for Twitter/Facebook/Snapchat/TikTok (+variants)
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=social/android_app_finder.lib.sh
source "$SCRIPT_DIR/social/android_app_finder.lib.sh"
# shellcheck source=social/opsec.lib.sh
source "$SCRIPT_DIR/social/opsec.lib.sh"
# shellcheck source=social/scan.lib.sh
source "$SCRIPT_DIR/social/scan.lib.sh"

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
  --profile NAME            Predefined package groups (e.g. social-extended).
  --filter REGEX            Filter package list with grep -E.

Output:
  --csv FILE                Write CSV inventory (default: social_apps.csv).
  --report FILE             Write plain-text summary (default: social_apps_report.txt).
  --outdir DIR              Collect artifacts (dumpsys/appops; optional APKs/data).

Actions:
  --test-launch             Attempt to launch found apps with `monkey` (best-effort).
  --collect-apks            Pull base/split APKs for found apps into DIR/apks/.
  --collect-sdcard          Tar & pull /sdcard/Android/{data,media}/<pkg> into DIR/data/.
  --probe-exported          Enumerate & lightly touch exported components.
  --timeout SEC             Snapshot timeout for activity top (default: 5).

OPSEC / Noise:
  --stealth                 Inventory only; disables probes that write or emit noise.
  --jitter MIN-MAXms        Random sleep between package scans.
  --noise-budget LEVEL      low|med|high footprint budget (default: high).
  --exfil MODE              local|smb|https (data exfil profile; default local).
  --require-found           Exit non-zero if nothing matched.

Logging:
  --quiet                   Errors only.
  --verbose                 Info-level logs.
  --debug                   Debug logs.
  --no-color                Disable colored output.

Examples:
  ./find_social_apps.sh
  ./find_social_apps.sh --serial ZY22JK89DR --csv my.csv --report report.txt
  ./find_social_apps.sh --keywords "facebook twitter tiktok snap" --include-disabled
  ./find_social_apps.sh --outdir artifacts --collect-apks --collect-sdcard --test-launch

Fedora prerequisites:
  sudo dnf install -y android-tools   # adb
EOF
}

# ------------ Defaults ------------
SERIAL=""; IP=""
CSV="social_apps.csv"; REPORT="social_apps_report.txt"; OUTDIR=""
USER_ID=""; ALL_USERS=1
TIMEOUT_S=5
INCLUDE_DISABLED=0
TEST_LAUNCH=0
COLLECT_APKS=0
COLLECT_SDCARD=0
PROBE_EXPORTED=0
STEALTH=0
JITTER_MIN_MS=0
JITTER_MAX_MS=0
NOISE_BUDGET="high"
EXFIL="local"
REQUIRE_FOUND=0
PROFILE=""
FILTER_RE=""
RULESETS=()

declare -a OPSEC_ACTIONS OPSEC_SUPPRESSED OPSEC_FILES FOUND_PKGS

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
    --report) REPORT="${2:-}"; shift 2;;
    --outdir) OUTDIR="${2:-}"; shift 2;;
    --user) USER_ID="${2:-}"; ALL_USERS=0; shift 2;;
    --all-users) ALL_USERS=1; shift;;
    --packages) read -r -a PKGS_OVERRIDE <<<"${2:-}"; shift 2;;
    --keywords) read -r -a KEYWORDS <<<"${2:-}"; shift 2;;
    --include-disabled) INCLUDE_DISABLED=1; shift;;
    --profile) PROFILE="${2:-}"; shift 2;;
    --filter) FILTER_RE="${2:-}"; shift 2;;
    --test-launch) TEST_LAUNCH=1; shift;;
    --collect-apks) COLLECT_APKS=1; shift;;
    --collect-sdcard) COLLECT_SDCARD=1; shift;;
    --probe-exported) PROBE_EXPORTED=1; shift;;
    --timeout) TIMEOUT_S="${2:-5}"; shift 2;;
    --stealth) STEALTH=1; shift;;
    --jitter) JITTER_RANGE="${2:-}"; JITTER_RANGE="${JITTER_RANGE%%ms}"; JITTER_MIN_MS="${JITTER_RANGE%-*}"; JITTER_MAX_MS="${JITTER_RANGE#*-}"; shift 2;;
    --noise-budget) NOISE_BUDGET="${2:-low}"; shift 2;;
    --exfil) EXFIL="${2:-local}"; shift 2;;
    --require-found) REQUIRE_FOUND=1; shift;;
    --rulesets) RULESETS+=("${2:-}"); shift 2;;
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

# ------------ OPSEC Modes ------------
if [[ $STEALTH -eq 1 && "$NOISE_BUDGET" == "high" ]]; then
  NOISE_BUDGET="low"
fi

if [[ $STEALTH -eq 1 ]]; then
  TEST_LAUNCH=0
  COLLECT_APKS=0
  COLLECT_SDCARD=0
  PROBE_EXPORTED=0
fi

case "$NOISE_BUDGET" in
  low)
    if [[ $COLLECT_APKS -eq 1 ]]; then OPSEC_SUPPRESSED+=(collect-apks); fi
    COLLECT_APKS=0
    if [[ $COLLECT_SDCARD -eq 1 ]]; then OPSEC_SUPPRESSED+=(collect-sdcard); fi
    COLLECT_SDCARD=0
    if [[ $PROBE_EXPORTED -eq 1 ]]; then OPSEC_SUPPRESSED+=(probe-exported); fi
    PROBE_EXPORTED=0
    ;;
  med)
    if [[ $COLLECT_SDCARD -eq 1 ]]; then OPSEC_SUPPRESSED+=(collect-sdcard); fi
    COLLECT_SDCARD=0
    if [[ $PROBE_EXPORTED -eq 1 ]]; then OPSEC_SUPPRESSED+=(probe-exported); fi
    PROBE_EXPORTED=0
    ;;
  high) ;;
  *) aaf_die "Invalid --noise-budget: $NOISE_BUDGET";;
esac

DEFENSE_FINDINGS=()
if [[ $STEALTH -eq 1 ]]; then
  mapfile -t DEFENSE_FINDINGS < <(aaf_defense_scan "$ADB")
  if [[ ${#DEFENSE_FINDINGS[@]} -gt 0 ]]; then
    aaf_log WARN "Defense sensors detected: ${DEFENSE_FINDINGS[*]}"
    AAF_ALLOW_NOISY=0
  fi
fi

# ------------ Users ------------
if [[ $ALL_USERS -eq 1 ]]; then
  USERS="$(aaf_get_users "$ADB")"
else
  USERS="$USER_ID"
fi
aaf_log DEBUG "Users: $USERS"

# ------------ Packages ------------
PKGS=("${PKGS_OVERRIDE[@]:-${PKGS_DEFAULT[@]}}")

if [[ "$PROFILE" == "social-extended" ]]; then
  PKGS+=(
    com.instagram.android
    com.whatsapp
    org.telegram.messenger
    com.tinder
  )
fi

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
if [[ -n "$FILTER_RE" ]]; then
  mapfile -t PKGS < <(printf '%s\n' "${PKGS[@]}" | grep -E "$FILTER_RE" || true)
fi
mapfile -t PKGS < <(aaf_shuffle_array "${PKGS[@]}")
aaf_log DEBUG "Final package set (#${#PKGS[@]}): ${PKGS[*]}"

# ------------ Outputs ------------
if [[ -n "$CSV" ]]; then
  aaf_csv_header > "$CSV"
  OPSEC_FILES+=("$CSV")
fi
  if [[ -n "$REPORT" ]]; then
    printf '%-5s %-40s %-7s %s\n' "USER" "PACKAGE" "STATUS" "APK_PATHS" > "$REPORT"
    OPSEC_FILES+=("$REPORT")
  fi

APKS_DIR=""; DATA_DIR=""; TXT_DIR=""; FINDINGS_FILE=""
if [[ -n "$OUTDIR" ]]; then
  TXT_DIR="$OUTDIR/text"; mkdir -p "$TXT_DIR"
  if [[ $COLLECT_APKS -eq 1 ]]; then APKS_DIR="$OUTDIR/apks"; mkdir -p "$APKS_DIR"; fi
  if [[ $COLLECT_SDCARD -eq 1 ]]; then DATA_DIR="$OUTDIR/data"; mkdir -p "$DATA_DIR"; fi
  FINDINGS_FILE="$OUTDIR/findings.csv"
  printf 'package,risk_signals,probes,meta\n' > "$FINDINGS_FILE"
fi

# ------------ Scan ------------
ANY_FOUND=0

for u in $USERS; do
  aaf_scan_user "$u"
done

  if [[ ${#FOUND_PKGS[@]} -gt 0 ]]; then
    aaf_log INFO "Found ${#FOUND_PKGS[@]} package(s): ${FOUND_PKGS[*]}"
  else
    aaf_log WARN "No target packages detected"
  fi

  # ------------ Summary ------------
  aaf_log INFO "Output files:"
  [[ -n "$CSV"    ]] && aaf_log INFO "  CSV inventory : $(readlink -f "$CSV")"
  [[ -n "$REPORT" ]] && aaf_log INFO "  Text report   : $(readlink -f "$REPORT")"
  [[ -n "$OUTDIR" ]] && aaf_log INFO "  Artifacts dir : $(readlink -f "$OUTDIR")"
  printf '\n=== OPSEC SUMMARY ===\n'
  printf 'Noise budget : %s\n' "$NOISE_BUDGET"
  printf 'Exfil profile: %s\n' "$EXFIL"
  if [[ ${#DEFENSE_FINDINGS[@]} -gt 0 ]]; then
    printf 'Defense sensors: %s\n' "${DEFENSE_FINDINGS[*]}"
  fi
  printf 'Actions taken : %s\n' "${OPSEC_ACTIONS[*]:-none}"
  printf 'Suppressed    : %s\n' "${OPSEC_SUPPRESSED[*]:-none}"
  printf 'Files created (%d):\n' "${#OPSEC_FILES[@]}"
  for f in "${OPSEC_FILES[@]}"; do printf '  %s\n' "$f"; done

if [[ $REQUIRE_FOUND -eq 1 && $ANY_FOUND -eq 0 ]]; then
  aaf_die "No packages matched"
fi

exit $ANY_FOUND
