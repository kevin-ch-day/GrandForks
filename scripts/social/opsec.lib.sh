#!/usr/bin/env bash
# opsec.lib.sh - OPSEC helpers for Android app finder

set -Eeuo pipefail

# Randomize array order to reduce signature patterns
# usage: new=( $(aaf_shuffle_array "${arr[@]}") )
aaf_shuffle_array() {
  printf '%s\n' "$@" | shuf
}

# Sleep for a random jitter between MIN and MAX milliseconds
# e.g. aaf_sleep_jitter 200 800
aaf_sleep_jitter() {
  local min_ms="$1" max_ms="$2"
  [[ -z "$max_ms" || "$max_ms" -eq 0 ]] && return 0
  local span=$((max_ms - min_ms))
  [[ $span -lt 0 ]] && span=0
  local delay_ms=$((RANDOM % (span + 1) + min_ms))
  local delay_s
  delay_s="$(awk "BEGIN{printf '%.3f', $delay_ms/1000}")"
  sleep "$delay_s"
}

# Sweep for common defense sensors; prints findings as an array
# relies on aaf_shell from android_app_finder.lib.sh
aaf_defense_scan() {
  local adb="$1" findings=() pkgs device_owner
  local sensors=(
    com.microsoft.intune
    com.mobileiron
    com.sentinelone
    com.zimperium.zips
    com.citrix.emea.mdmdiff
  )
  pkgs="$(aaf_shell "$adb" "pm list packages" 2>/dev/null | cut -d: -f2 | tr -d '\r' || true)"
  for s in "${sensors[@]}"; do
    if grep -q "^$s$" <<<"$pkgs"; then findings+=("pkg:$s"); fi
  done
  device_owner="$(aaf_shell "$adb" "settings get global device_owner" 2>/dev/null | tr -d '\r')"
  [[ -n "$device_owner" && "$device_owner" != "null" ]] && findings+=("device_owner:$device_owner")
  if aaf_shell "$adb" "dumpsys devicepolicy" 2>/dev/null | grep -q 'Device Owner'; then
    findings+=("devicepolicy")
  fi
  printf '%s\n' "${findings[@]}"
}

