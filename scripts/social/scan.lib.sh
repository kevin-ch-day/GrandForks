#!/usr/bin/env bash
# scan.lib.sh - per-user scanning routines for find_social_apps.sh

set -Eeuo pipefail

# Scan a single Android user for packages in PKGS
# Uses globals: ADB, PKGS, CSV, REPORT, TXT_DIR, APKS_DIR, DATA_DIR,
# FINDINGS_FILE, RULESETS, PROBE_EXPORTED, TEST_LAUNCH, TIMEOUT_S,
# OPSEC_FILES, OPSEC_ACTIONS, FOUND_PKGS, ANY_FOUND
# shellcheck disable=SC2154 # globals defined in caller
aaf_scan_user() {
  local u="$1" p paths meta probes hs
    printf '\n== User %s ==\n' "$u"
    printf '%-8s %-45s %s\n' "STATUS" "PACKAGE" "APK PATHS"
  for p in "${PKGS[@]}"; do
    aaf_sleep_jitter "$JITTER_MIN_MS" "$JITTER_MAX_MS"
    paths="$(aaf_pm_path "$ADB" "$u" "$p")"
    if [[ -n "$paths" ]]; then
        printf '%-8s %-45s %s\n' "$(aaf_fmt_status FOUND)" "$p" "$paths"
      ANY_FOUND=1
      FOUND_PKGS+=("$p")
      meta="$(aaf_pkg_meta "$ADB" "$p")"
      [[ -n "$CSV"    ]] && aaf_csv_line "$u" "$p" "FOUND" "$paths" "$meta" >> "$CSV"
        [[ -n "$REPORT" ]] && printf '%-5s %-40s %-7s %s\n' "$u" "$p" "FOUND" "$paths" >> "$REPORT"
      if [[ -n "$TXT_DIR" ]]; then
        while IFS= read -r f; do OPSEC_FILES+=("$f"); done < <(aaf_collect_text "$ADB" "$TXT_DIR" "$p")
        OPSEC_ACTIONS+=(collect-text)
      fi
      if [[ -n "$APKS_DIR" ]]; then
        while IFS= read -r f; do
          OPSEC_FILES+=("$f")
          hs="$(aaf_apk_heuristics "$f")"
          [[ -n "$FINDINGS_FILE" ]] && printf '%s,%s,,%s\n' "$p" "$hs" "$meta" >> "$FINDINGS_FILE"
        done < <(aaf_collect_apks "$ADB" "$APKS_DIR" "$p" "$u")
        OPSEC_ACTIONS+=(collect-apks)
      else
        [[ -n "$FINDINGS_FILE" ]] && printf '%s,,,%s\n' "$p" "$meta" >> "$FINDINGS_FILE"
      fi
      if [[ -n "$DATA_DIR" ]]; then
        while IFS= read -r f; do
          OPSEC_FILES+=("$f")
          aaf_scan_rulesets "$f" "$p" "$DATA_DIR/grep" "${RULESETS[@]}"
        done < <(aaf_collect_sdcard_data "$ADB" "$DATA_DIR" "$p")
        OPSEC_ACTIONS+=(collect-sdcard)
      fi
      if [[ $PROBE_EXPORTED -eq 1 ]]; then
        probes="$(aaf_probe_exported "$ADB" "$p")"
        [[ -n "$FINDINGS_FILE" ]] && printf '%s,,%s,%s\n' "$p" "$probes" "$meta" >> "$FINDINGS_FILE"
        OPSEC_ACTIONS+=(probe-exported)
      fi
      if [[ $TEST_LAUNCH -eq 1 ]]; then
        aaf_log INFO "Test-launching $p …"
        aaf_test_launch "$ADB" "$u" "$p" "$TIMEOUT_S" || true
        OPSEC_ACTIONS+=(test-launch)
      fi
    else
        printf '%-8s %-45s -\n' "$(aaf_fmt_status MISSING)" "$p"
      local empty_meta="||||||||" # 8 pipes → 9 fields (empty) for csv consistency
      [[ -n "$CSV"    ]] && aaf_csv_line "$u" "$p" "MISSING" "" "$empty_meta" >> "$CSV"
        [[ -n "$REPORT" ]] && printf '%-5s %-40s %-7s -\n' "$u" "$p" "MISSING" >> "$REPORT"
      [[ -n "$FINDINGS_FILE" ]] && printf '%s,,,,\n' "$p" >> "$FINDINGS_FILE"
    fi
  done
  printf '\n'
}

