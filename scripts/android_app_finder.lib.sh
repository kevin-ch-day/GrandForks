#!/usr/bin/env bash
# android_app_finder.lib.sh
# Shared helpers for ADB app discovery & reporting

set -Eeuo pipefail

# --------------- Config / Logging ---------------
: "${AAF_LOG_LEVEL:=2}"      # 0=ERROR,1=WARN,2=INFO,3=DEBUG
: "${AAF_NO_COLOR:=0}"       # 1 to disable colors
: "${AAF_SHELL_TIMEOUT:=12}" # seconds for single adb shell ops when 'timeout' exists

# Colors
if [[ "$AAF_NO_COLOR" -eq 0 ]]; then
  AAF_C_ERR=$'\e[31m'; AAF_C_WRN=$'\e[33m'; AAF_C_INF=$'\e[36m'; AAF_C_DBG=$'\e[90m'; AAF_C_RST=$'\e[0m'
else
  AAF_C_ERR=""; AAF_C_WRN=""; AAF_C_INF=""; AAF_C_DBG=""; AAF_C_RST=""
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
  # If SERIAL is empty and multiple devices are present, fail with a hint.
  local devices
  devices="$(adb devices -l | awk 'NR>1 && $1!="" {print $1 ":" $2}')" || true
  local count
  count="$(printf '%s\n' "$devices" | grep -c . || true)"
  if [[ "$count" -eq 0 ]]; then
    aaf_die "No ADB devices. Plug in a phone and run: adb devices"
  elif [[ "$count" -gt 1 ]]; then
    aaf_log WARN "Multiple devices detected:"
    printf '%s\n' "$devices" 1>&2
    aaf_die "Specify one with --serial SERIAL or --ip HOST:PORT"
  fi
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
  aaf_shell "$adb" "pm list packages --user $user | cut -d: -f2 | grep -i -- $(printf %q "$keyword")" 2>/dev/null | tr -d '\r' || true
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
  installer="$(aaf_shell "$adb" "pm list packages -i | awk -F\"[ :]\" '\$1==\"package\" && \$2==\"$pkg\" {for(i=1;i<=NF;i++) if(\$i ~ /^installer=/){sub(\"installer=\",\"\",\$i); print \$i; break}}'")" || true
  enabled="$(aaf_shell "$adb" "cmd package dump $pkg 2>/dev/null | awk '/Packages:/{f=1} f && /enabled=/ {print; exit}'")" || true
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

aaf_json_line() {
  local user="$1" pkg="$2" status="$3" paths="$4" meta="$5"
  IFS='|' read -r vn vc sdk uid finst lupd installer enabled <<<"$meta"
  if aaf_have jq; then
    jq -nc --arg user "$user" --arg pkg "$pkg" --arg status "$status" \
      --arg paths "$paths" --arg vn "$vn" --arg vc "$vc" --arg sdk "$sdk" \
      --arg uid "$uid" --arg finst "$finst" --arg lupd "$lupd" \
      --arg installer "$installer" --arg enabled "$enabled" \
      '{user:$user, package:$pkg, status:$status, apk_paths:$paths, versionName:$vn, versionCode:$vc, targetSdk:$sdk, uid:$uid, firstInstallTime:$finst, lastUpdateTime:$lupd, installer:$installer, enabled:$enabled}'
  else
    printf '{"user":"%s","package":"%s","status":"%s","apk_paths":"%s","versionName":"%s","versionCode":"%s","targetSdk":"%s","uid":"%s","firstInstallTime":"%s","lastUpdateTime":"%s","installer":"%s","enabled":"%s"}\n' \
      "$user" "$pkg" "$status" "$paths" "${vn:-}" "${vc:-}" "${sdk:-}" "${uid:-}" "${finst:-}" "${lupd:-}" "${installer:-}" "${enabled:-}"
  fi
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
  aaf_shell "$adb" "appops get $pkg" >"$outdir/$pkg.appops.txt" 2>/dev/null || true
}

aaf_collect_apks() {
  local adb="$1" outdir="$2" pkg="$3" user="${4:-0}"
  mkdir -p "$outdir"
  aaf_shell "$adb" "pm path --user $user $pkg | sed 's/^package://'" | tr -d '\r' | while read -r ap; do
    [[ -z "$ap" ]] && continue
    local name="${pkg}_$(basename "$ap")"
    adb pull "$ap" "$outdir/$name" >/dev/null 2>&1 || aaf_log WARN "Pull failed: $ap"
  done
}

aaf_collect_sdcard_data() {
  local adb="$1" outdir="$2" pkg="$3"
  mkdir -p "$outdir"
  for base in /sdcard/Android/data /sdcard/Android/media; do
    if aaf_shell "$adb" "[ -d $base/$pkg ]"; then
      local tarname="${pkg}_$(basename "$base").tar"
      aaf_shell "$adb" "tar -cf /sdcard/$tarname -C $base $pkg" || true
      adb pull "/sdcard/$tarname" "$outdir/$tarname" >/dev/null 2>&1 || aaf_log WARN "Pull failed: $tarname"
    fi
  done
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
