#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STDOUT_LOG="${ROOT_DIR}/tools/logs/alignment-watcher.stdout.log"
STDERR_LOG="${ROOT_DIR}/tools/logs/alignment-watcher.stderr.log"

mkdir -p "${ROOT_DIR}/tools/logs"
touch "${STDOUT_LOG}" "${STDERR_LOG}"

echo "Stdout: ${STDOUT_LOG}"
echo "Stderr: ${STDERR_LOG}"
echo ""

tail -n 50 -f "${STDOUT_LOG}" "${STDERR_LOG}"
