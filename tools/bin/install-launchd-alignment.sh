#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNTIME_HOME="${HOME}/.newaitiku"
VENV_DIR="${RUNTIME_HOME}/.venv"
LAUNCH_AGENTS_DIR="${HOME}/Library/LaunchAgents"
LOG_DIR="${ROOT_DIR}/tools/logs"
LABEL="com.shaotongli.newaitiku.alignment-watcher"
PLIST_PATH="${LAUNCH_AGENTS_DIR}/${LABEL}.plist"
STDOUT_LOG="${LOG_DIR}/alignment-watcher.stdout.log"
STDERR_LOG="${LOG_DIR}/alignment-watcher.stderr.log"
DEBOUNCE="2"
INTERVAL="1"
FULL_MODE="false"
FORCE_PROTECTED_PATH="false"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --full)
      FULL_MODE="true"
      shift
      ;;
    --debounce)
      DEBOUNCE="${2:?missing value for --debounce}"
      shift 2
      ;;
    --interval)
      INTERVAL="${2:?missing value for --interval}"
      shift 2
      ;;
    --force-protected-path)
      FORCE_PROTECTED_PATH="true"
      shift
      ;;
    *)
      echo "Unsupported argument: $1" >&2
      echo "Usage: $0 [--full] [--debounce seconds] [--interval seconds] [--force-protected-path]" >&2
      exit 1
      ;;
  esac
done

case "${ROOT_DIR}" in
  "${HOME}/Documents"/*|"${HOME}/Desktop"/*|"${HOME}/Downloads"/*)
    if [ "${FORCE_PROTECTED_PATH}" != "true" ]; then
      echo "Refusing to install LaunchAgent from a macOS protected directory:" >&2
      echo "  ${ROOT_DIR}" >&2
      echo "" >&2
      echo "launchd background processes usually cannot read projects under Documents/Desktop/Downloads." >&2
      echo "Move the repository to a path such as ~/Code/newaitiku and rerun this script." >&2
      echo "If you still want to try anyway, rerun with --force-protected-path." >&2
      exit 1
    fi
    ;;
esac

if [ ! -x "${VENV_DIR}/bin/python" ]; then
  mkdir -p "${RUNTIME_HOME}"
  NEWAITIKU_VENV_DIR="${VENV_DIR}" "${ROOT_DIR}/tools/bin/bootstrap-python.sh"
fi

mkdir -p "${LAUNCH_AGENTS_DIR}" "${LOG_DIR}"

PROGRAM_ARGS=(
  "${VENV_DIR}/bin/python"
  "-u"
  "${ROOT_DIR}/tools/python/watch_alignment.py"
  "--debounce"
  "${DEBOUNCE}"
  "--interval"
  "${INTERVAL}"
)

if [ "${FULL_MODE}" = "true" ]; then
  PROGRAM_ARGS+=("--full")
fi

ARGS_XML=""
for arg in "${PROGRAM_ARGS[@]}"; do
  ARGS_XML="${ARGS_XML}    <string>${arg}</string>"$'\n'
done

cat > "${PLIST_PATH}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>${LABEL}</string>
    <key>ProgramArguments</key>
    <array>
${ARGS_XML}    </array>
    <key>WorkingDirectory</key>
    <string>${ROOT_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>ProcessType</key>
    <string>Background</string>
    <key>StandardOutPath</key>
    <string>${STDOUT_LOG}</string>
    <key>StandardErrorPath</key>
    <string>${STDERR_LOG}</string>
    <key>EnvironmentVariables</key>
    <dict>
      <key>PATH</key>
      <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
      <key>NEWAITIKU_VENV_DIR</key>
      <string>${VENV_DIR}</string>
      <key>PYTHONUNBUFFERED</key>
      <string>1</string>
    </dict>
  </dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)" "${PLIST_PATH}" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "${PLIST_PATH}"
launchctl kickstart -k "gui/$(id -u)/${LABEL}"

echo "Installed LaunchAgent: ${LABEL}"
echo "Plist: ${PLIST_PATH}"
echo "Stdout log: ${STDOUT_LOG}"
echo "Stderr log: ${STDERR_LOG}"
echo "Mode: $( [ "${FULL_MODE}" = "true" ] && echo "full" || echo "batch" )"
echo "Debounce: ${DEBOUNCE}s"
echo "Interval: ${INTERVAL}s"
echo "Runtime venv: ${VENV_DIR}"
