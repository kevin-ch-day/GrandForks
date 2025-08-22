#!/bin/bash
# ---------------------------------------------------
# andro_apk_harvester.sh
# Harvests APKs from Android devices, collects metadata, and stores results
# ---------------------------------------------------

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

DEVICE=""
TARGET_PACKAGES=(
    "com.zhiliaoapp.musically"   # TikTok
    "com.facebook.katana"        # Facebook
    "com.facebook.orca"          # Messenger
    "com.snapchat.android"       # Snapchat
)

mkdir -p "$RESULTS_DIR"

LOGFILE="$RESULTS_DIR/harvest_log_$TIMESTAMP.txt"
REPORT="$RESULTS_DIR/apks_report_$TIMESTAMP.csv"
JSON_REPORT="$RESULTS_DIR/apks_report_$TIMESTAMP.json"

# -----------------------------
# Colors
# -----------------------------
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
NC="\033[0m" # reset

# -----------------------------
# Helpers
# -----------------------------
log() {
    echo -e "[$(date +'%H:%M:%S')] $*" | tee -a "$LOGFILE"
}

usage() {
    echo "Usage: $0 [-d DEVICE_ID]"
    exit 1
}

get_apk_path() {
    local pkg="$1"
    adb -s "$DEVICE" shell pm path "$pkg" 2>/dev/null | tr -d '\r' | sed 's/package://g'
}

pull_apk() {
    local pkg="$1"
    local apk_path="$2"
    local outfile="$DEVICE_DIR/${pkg##*.}.apk"

    if adb -s "$DEVICE" pull "$apk_path" "$outfile" >/dev/null 2>&1; then
        echo "$outfile"
    else
        echo ""
    fi
}

apk_metadata() {
    local pkg="$1"
    local outfile="$2"

    if [[ -f "$outfile" ]]; then
        local sha256=$(sha256sum "$outfile" | awk '{print $1}')
        local sha1=$(sha1sum "$outfile" | awk '{print $1}')
        local md5=$(md5sum "$outfile" | awk '{print $1}')
        local size=$(stat -c%s "$outfile")

        # Extract more info via dumpsys
        local info=$(adb -s "$DEVICE" shell dumpsys package "$pkg" 2>/dev/null)
        local version=$(echo "$info" | grep versionName | head -n1 | awk -F= '{print $2}')
        local versionCode=$(echo "$info" | grep versionCode | head -n1 | grep -o '[0-9]\+')
        local targetSdk=$(echo "$info" | grep targetSdk | head -n1 | awk -F= '{print $2}')
        local installer=$(echo "$info" | grep "installerPackageName" | awk -F= '{print $2}' | tr -d ' ')

        # Guess install type by path
        local installType="user"
        if [[ "$outfile" == *"/system/"* || "$outfile" == *"/product/"* || "$outfile" == *"/vendor/"* ]]; then
            installType="system"
        fi

        # Write to log
        log "${GREEN}✅ Metadata for $pkg${NC}"
        log "   APK file    : $outfile"
        log "   SHA256      : $sha256"
        log "   SHA1        : $sha1"
        log "   MD5         : $md5"
        log "   Size        : $size bytes"
        log "   Version     : ${version:-unknown} (code: ${versionCode:-unknown}, targetSdk: ${targetSdk:-unknown})"
        log "   Installer   : ${installer:-unknown}"
        log "   InstallType : $installType"

        # Append to CSV
        echo "$pkg,$outfile,$sha256,$sha1,$md5,$size,$version,$versionCode,$targetSdk,$installer,$installType" >> "$REPORT"

        # Append JSON object to array
        jq -n \
          --arg pkg "$pkg" \
          --arg file "$outfile" \
          --arg sha256 "$sha256" \
          --arg sha1 "$sha1" \
          --arg md5 "$md5" \
          --arg size "$size" \
          --arg version "${version:-unknown}" \
          --arg versionCode "${versionCode:-unknown}" \
          --arg targetSdk "${targetSdk:-unknown}" \
          --arg installer "${installer:-unknown}" \
          --arg installType "$installType" \
          '{package:$pkg,file:$file,sha256:$sha256,sha1:$sha1,md5:$md5,size:$size,version:$version,versionCode:$versionCode,targetSdk:$targetSdk,installer:$installer,installType:$installType}' \
          >> "$JSON_REPORT.tmp"
    fi
}

# -----------------------------
# Parse args
# -----------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--device) DEVICE="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) shift ;;
    esac
done

# Pick default device if none provided
if [[ -z "$DEVICE" ]]; then
    DEVICE=$(adb devices | awk 'NR==2 {print $1}')
    if [[ -z "$DEVICE" || "$DEVICE" == "List" ]]; then
        log "${RED}❌ No device found.${NC}"
        exit 1
    fi
fi

# Setup results folder per device
DEVICE_DIR="$RESULTS_DIR/$DEVICE"
mkdir -p "$DEVICE_DIR"
touch "$LOGFILE"
echo "package,file,sha256,sha1,md5,size,version,versionCode,targetSdk,installer,installType" > "$REPORT"
: > "$JSON_REPORT.tmp"

log "${BLUE}📱 Using device: $DEVICE${NC}"
log "📂 Output directory: $DEVICE_DIR"
log "📝 Log file: $LOGFILE"
log "📊 Report: $REPORT"

# -----------------------------
# Main Loop
# -----------------------------
for pkg in "${TARGET_PACKAGES[@]}"; do
    log "${YELLOW}🔍 Checking $pkg...${NC}"
    apk_path=$(get_apk_path "$pkg")

    if [[ -n "$apk_path" ]]; then
        log "   Found APK at $apk_path"
        outfile=$(pull_apk "$pkg" "$apk_path")
        if [[ -n "$outfile" ]]; then
            apk_metadata "$pkg" "$outfile"
        else
            log "${RED}   ⚠️ Failed to pull $pkg${NC}"
        fi
    else
        log "${RED}   ❌ Not installed.${NC}"
    fi
done

# Build JSON array properly
jq -s '.' "$JSON_REPORT.tmp" > "$JSON_REPORT"
rm -f "$JSON_REPORT.tmp"

log "${GREEN}🎉 Finished harvesting.${NC}"

# -----------------------------
# Final summary
# -----------------------------
echo -e "\n${BLUE}========= Summary =========${NC}"
column -t -s, "$REPORT"
echo -e "${BLUE}===========================${NC}\n"
