#!/usr/bin/env bash
# android_app_finder.lib.sh
# Shared helpers for ADB app discovery & reporting

set -Eeuo pipefail

# --------------- Config / Logging ---------------
: "${AAF_LOG_LEVEL:=2}"      # 0=ERROR,1=WARN,2=INFO,3=DEBUG
: "${AAF_NO_COLOR:=0}"       # 1 to disable colors
: "${AAF_SHELL_TIMEOUT:=12}" # seconds for single adb shell ops when 'timeout' exists
: "${AAF_ALLOW_NOISY:=1}"     # 0 to skip probes that may create log noise

# Colors
if [[ "$AAF_NO_COLOR" -eq 0 ]]; then
  AAF_C_ERR=$'\e[31m'; AAF_C_WRN=$'\e[33m'; AAF_C_OK=$'\e[32m'; AAF_C_INF=$'\e[36m'; AAF_C_DBG=$'\e[90m'; AAF_C_RST=$'\e[0m'
else
  AAF_C_ERR=""; AAF_C_WRN=""; AAF_C_OK=""; AAF_C_INF=""; AAF_C_DBG=""; AAF_C_RST=""
fi

aaf_log() {
  local lvl="$1"; shift || true
  local prefix=""       # <— init avoids "unbound variable" under set -u
  case "$lvl" in
    ERROR) [[ ${AAF_LOG_LEVEL:-2} -ge 0 ]] && prefix="${AAF_C_ERR}[ERR]${AAF_C_RST}";;
    WARN)  [[ ${AAF_LOG_LEVEL:-2} -ge 1 ]] && prefix="${AAF_C_WRN}[WRN]${AAF_C_RST}";;
    INFO)  [[ ${AAF_LOG_LEVEL:-2} -ge 2 ]] && prefix="${AAF_C_INF}[INF]${AAF_C_RST}";;
    DEBUG) [[ ${AAF_LOG_LEVEL:-2} -ge 3 ]] && prefix="${AAF_C_DBG}[DBG]${AAF_C_RST}";;
    *) prefix="";;
  esac
  [[ -n "$prefix" ]] && printf '%s %s\n' "$prefix" "$*" 1>&2
}


aaf_die() { aaf_log ERROR "$*"; exit 1; }
aaf_have() { command -v "$1" >/dev/null 2>&1; }

# Format status labels with optional color. Usage: aaf_fmt_status FOUND
aaf_fmt_status() {
  local s="$1"
  case "$s" in
    FOUND)
      if [[ "$AAF_NO_COLOR" -eq 0 ]]; then
        printf '%s%s%s' "$AAF_C_OK" "$s" "$AAF_C_RST"
      else
        printf '%s' "$s"
      fi
      ;;
    MISSING)
      if [[ "$AAF_NO_COLOR" -eq 0 ]]; then
        printf '%s%s%s' "$AAF_C_ERR" "$s" "$AAF_C_RST"
      else
        printf '%s' "$s"
      fi
      ;;
    *)
      printf '%s' "$s"
      ;;
  esac
}

# --------------- ADB Resolution ---------------
aaf_adb_cmd() {
  local serial="${1:-}"
  if [[ -n "$serial" ]]; then
    printf 'adb -s %q' "$serial"
  else
    printf 'adb'
  fi
}

aaf_select_device() {
  # Prompt the operator to choose a device when multiple are attached.
  local devs=( )
  mapfile -t devs < <(adb devices -l | awk 'NR>1 && $1!="" {print $1}') || true
  local count=${#devs[@]}
  if [[ $count -eq 0 ]]; then
    aaf_die "No ADB devices. Plug in a phone and run: adb devices"
  elif [[ $count -eq 1 ]]; then
    SERIAL="${devs[0]}"
    return
  fi

  aaf_log INFO "Select a device to scan:" 
  local i=1
  for d in "${devs[@]}"; do
    local model
    model="$(adb -s "$d" shell getprop ro.product.model 2>/dev/null | tr -d '\r')"
    printf ' %d) %s (%s)\n' "$i" "$d" "$model" 1>&2
    ((i++))
  done
  local choice
  read -rp "Enter choice [1-${count}]: " choice
  if ! [[ "$choice" =~ ^[0-9]+$ ]] || (( choice < 1 || choice > count )); then
    aaf_die "Invalid selection"
  fi
  SERIAL="${devs[$((choice-1))]}"
}

aaf_get_state() { eval "$1 get-state 2>/dev/null || true"; }

aaf_check_authorization() {
  # Warn if device shows as 'unauthorized'
  if adb devices | awk 'NR>1 && $2=="unauthorized"{exit 0} END{exit 1}'; then
    aaf_die "Device is unauthorized. Check the phone for the RSA prompt and tap 'Allow'. Then re-run."
  fi
}

# --------------- Shell Helpers ---------------
aaf_shell() {
  # Run "adb shell ..." with optional timeout if available
  local adb="$1"; shift
  if aaf_have timeout; then
    eval "timeout ${AAF_SHELL_TIMEOUT}s $adb shell \"$*\""
  else
    eval "$adb shell \"$*\""
  fi
}

# --------------- Users / Packages ---------------
aaf_get_users() {
  local adb="$1" users
  users="$(aaf_shell "$adb" "pm list users | sed -n 's/.*{\\([0-9][0-9]*\\):.*/\\1/p'")" || true
  users="${users//$'\r'/}"
  [[ -z "$users" ]] && users="0"
  printf '%s\n' "$users"
}

aaf_pm_path() {
  local adb="$1" user="$2" pkg="$3" out
  out="$(aaf_shell "$adb" "pm path --user $user $pkg" 2>/dev/null | tr -d '\r' | sed 's/^package://g' | tr '\n' ' ')" || true
  out="${out%"${out##*[![:space:]]}"}"
  printf '%s' "$out"
}

aaf_is_present() {
  local adb="$1" user="$2" pkg="$3"
  [[ -n "$(aaf_pm_path "$adb" "$user" "$pkg")" ]]
}

aaf_search_keywords() {
  local adb="$1" user="$2" keyword="$3"
  aaf_shell "$adb" \
    "pm list packages --user $user | cut -d: -f2 | grep -i -- $(printf %q \"$keyword\")" \
    2>/dev/null | tr -d '\r' || true
}

aaf_list_disabled() {
  local adb="$1" user="$2"
  aaf_shell "$adb" "pm list packages -d --user $user | cut -d: -f2" | tr -d '\r' || true
}

aaf_pkg_meta() {
  # Single dumpsys parse for speed
  local adb="$1" pkg="$2" ds vn vc sdk uid finst lupd installer enabled
  ds="$(aaf_shell "$adb" "dumpsys package $pkg" 2>/dev/null | tr -d '\r')" || true
  vn="$(awk -F= '/versionName=/{print $2; exit}' <<<"$ds")"
  vc="$(awk -F= '/versionCode=/{print $2; exit}' <<<"$ds" | awk '{print $1}')"
  sdk="$(awk -F= '/targetSdk=/{print $2; exit}' <<<"$ds")"
  uid="$(awk '/userId=/{sub(/userId=/,""); print $1; exit}' <<<"$ds")"
  finst="$(awk -F= '/firstInstallTime=/{print $2; exit}' <<<"$ds")"
  lupd="$(awk -F= '/lastUpdateTime=/{print $2; exit}' <<<"$ds")"
  installer="$(
    aaf_shell "$adb" \
      "pm list packages -i | awk -F\\\"[ :]\\\" '\$1==\\\"package\\\" && \$2==\\\"$pkg\\\" {for(i=1;i<=NF;i++) if(\$i ~ /^installer=/){sub(\\\"installer=\\\",\\\"\\\",\$i); print \$i; break}}'"
  )" || true
  enabled="$(
    aaf_shell "$adb" \
      "cmd package dump $pkg 2>/dev/null | awk '/Packages:/{f=1} f && /enabled=/ {print; exit}'"
  )" || true
  printf '%s|%s|%s|%s|%s|%s|%s|%s\n' "${vn:-}" "${vc:-}" "${sdk:-}" "${uid:-}" "${finst:-}" "${lupd:-}" "${installer//$'\r'/}" "${enabled//$'\r'/}"
}

# --------------- Reporting ---------------
aaf_csv_escape() { local s="${1//\"/\"\"}"; printf '\"%s\"' "$s"; }

aaf_csv_header() {
  printf 'user,package,status,apk_paths,versionName,versionCode,targetSdk,uid,firstInstallTime,lastUpdateTime\n'
}

aaf_csv_line() {
  local user="$1" pkg="$2" status="$3" paths="$4" meta="$5"
  IFS='|' read -r vn vc sdk uid finst lupd _installer _enabled <<<"$meta"
  printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
    "$user" "$pkg" "$status" \
    "$(aaf_csv_escape "$paths")" \
    "$(aaf_csv_escape "${vn:-}")" "${vc:-}" "${sdk:-}" "${uid:-}" \
    "$(aaf_csv_escape "${finst:-}")" "$(aaf_csv_escape "${lupd:-}")"
}

# --------------- Actions ---------------
aaf_test_launch() {
  local adb="$1" user="$2" pkg="$3" timeout_s="${4:-5}"
  aaf_shell "$adb" "monkey --pct-syskeys 0 -p $pkg -c android.intent.category.LAUNCHER 1" >/dev/null 2>&1 || true
  aaf_shell "$adb" "timeout ${timeout_s}s cmd activity top | head -20" 2>/dev/null || true
}

aaf_collect_text() {
  local adb="$1" outdir="$2" pkg="$3"
  mkdir -p "$outdir"
  aaf_shell "$adb" "dumpsys package $pkg" >"$outdir/$pkg.dumpsys.txt" 2>/dev/null || true
  printf '%s/%s.dumpsys.txt\n' "$outdir" "$pkg"
  if [[ "${AAF_ALLOW_NOISY:-1}" -eq 1 ]]; then
    aaf_shell "$adb" "appops get $pkg" >"$outdir/$pkg.appops.txt" 2>/dev/null || true
    printf '%s/%s.appops.txt\n' "$outdir" "$pkg"
  fi
}

aaf_collect_apks() {
  local adb="$1" outdir="$2" pkg="$3" user="${4:-0}"
  mkdir -p "$outdir"
  aaf_shell "$adb" "pm path --user $user $pkg | sed 's/^package://'" | tr -d '\r' | while read -r ap; do
    [[ -z "$ap" ]] && continue
    local name="${pkg}_$(basename "$ap")"
    if adb pull "$ap" "$outdir/$name" >/dev/null 2>&1; then
      printf '%s/%s\n' "$outdir" "$name"
    else
      aaf_log WARN "Pull failed: $ap"
    fi
  done
}

aaf_collect_sdcard_data() {
  local adb="$1" outdir="$2" pkg="$3"
  mkdir -p "$outdir"
  for base in /sdcard/Android/data /sdcard/Android/media; do
    if aaf_shell "$adb" "[ -d $base/$pkg ]"; then
      local tarname="${pkg}_$(basename "$base").tar"
      aaf_shell "$adb" "tar -cf /sdcard/$tarname -C $base $pkg" || true
      if adb pull "/sdcard/$tarname" "$outdir/$tarname" >/dev/null 2>&1; then
        printf '%s/%s\n' "$outdir" "$tarname"
      else
        aaf_log WARN "Pull failed: $tarname"
      fi
    fi
  done
}

aaf_probe_exported() {
  # Enumerate exported components and attempt benign opens
  local adb="$1" pkg="$2" ds comp results=()
  ds="$(aaf_shell "$adb" "dumpsys package $pkg" 2>/dev/null | tr -d '\r')" || true
  while read -r comp; do
    local uri="content://$comp"
    aaf_shell "$adb" "content query --uri $uri --limit 1" >/dev/null 2>&1 || true
    results+=("provider:$comp")
  done < <(awk '/Providers:/{f=1;next}/^[A-Z]/{f=0}f && /name=/ && /exported=true/ {print $2}' <<<"$ds")
  while read -r comp; do
    aaf_shell "$adb" "am start -W -n $comp" >/dev/null 2>&1 || true
    results+=("activity:$comp")
  done < <(awk '/Activities:/{f=1;next}/^[A-Z]/{f=0}f && /name=/ && /exported=true/ {print $2}' <<<"$ds")
  printf '%s\n' "${results[*]}"
}

aaf_apk_heuristics() {
  # Basic static risk heuristics on APKs
  local apk="$1" hs=()
  if aaf_have apkanalyzer; then
    [[ "$(apkanalyzer manifest application-debuggable "$apk" 2>/dev/null)" == "true" ]] && hs+=("debuggable")
    [[ "$(apkanalyzer manifest application-allow-backup "$apk" 2>/dev/null)" == "true" ]] && hs+=("allowBackup")
  elif aaf_have aapt; then
    local badging
    badging="$(aapt dump badging "$apk" 2>/dev/null)" || true
    grep -q "application-debuggable" <<<"$badging" && hs+=("debuggable")
    grep -q "allowBackup='true'" <<<"$badging" && hs+=("allowBackup")
  fi
  printf '%s\n' "${hs[*]}"
}

aaf_scan_rulesets() {
  # Scan extracted SD card data for operator-supplied patterns
  local tarfile="$1" pkg="$2" outdir="$3"; shift 3
  local rulesets=("$@")
  [[ ${#rulesets[@]} -eq 0 ]] && return 0
  mkdir -p "$outdir"
  local tmp
  tmp="$(mktemp -d)"
  tar -xf "$tarfile" -C "$tmp" || return 0
  for rs in "${rulesets[@]}"; do
    local base="$(basename "$rs")"
    grep -R -n -a -E -f "$rs" "$tmp" >"$outdir/${pkg}_${base}.grep" 2>/dev/null || true
  done
  rm -rf "$tmp"
}

# --------------- Utilities ---------------
aaf_dedupe_array() {
  # usage: new=($(aaf_dedupe_array "${arr[@]}"))
  declare -A seen=()
  for x in "$@"; do
    [[ -z "$x" ]] && continue
    if [[ -z "${seen[$x]:-}" ]]; then
      printf '%s\n' "$x"
      seen["$x"]=1
    fi
  done
}

