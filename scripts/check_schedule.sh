#!/bin/zsh
set -eu

LABEL="com.kp.crypto-analyst"

if launchctl list | grep -q "$LABEL"; then
  echo "$LABEL is loaded."
else
  echo "$LABEL is not loaded."
  echo "Run ./scripts/install_schedule.sh to install it."
fi
