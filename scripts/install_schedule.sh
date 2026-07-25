#!/bin/zsh
set -eu

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
LABEL="com.kp.crypto-analyst"
SOURCE_PLIST="$PROJECT_DIR/launchd/$LABEL.plist"
TARGET_DIR="$HOME/Library/LaunchAgents"
TARGET_PLIST="$TARGET_DIR/$LABEL.plist"

mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$TARGET_DIR"
chmod +x "$PROJECT_DIR/scripts/run_crypto_analyst.sh"
sed "s#__PROJECT_DIR__#$PROJECT_DIR#g" "$SOURCE_PLIST" > "$TARGET_PLIST"

launchctl unload "$TARGET_PLIST" >/dev/null 2>&1 || true
launchctl load "$TARGET_PLIST"

echo "Installed $LABEL"
echo "Schedule: daily at 12:00 and 18:00 local time"
echo "Logs:"
echo "- $PROJECT_DIR/logs/launchd.out.log"
echo "- $PROJECT_DIR/logs/launchd.err.log"
