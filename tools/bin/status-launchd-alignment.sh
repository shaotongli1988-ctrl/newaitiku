#!/usr/bin/env bash

set -euo pipefail

LABEL="com.shaotongli.newaitiku.alignment-watcher"
PLIST_PATH="${HOME}/Library/LaunchAgents/${LABEL}.plist"

if [ ! -f "${PLIST_PATH}" ]; then
  echo "LaunchAgent plist not found: ${PLIST_PATH}"
  exit 1
fi

echo "Plist: ${PLIST_PATH}"
echo ""
launchctl print "gui/$(id -u)/${LABEL}"
