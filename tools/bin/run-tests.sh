#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="${NEWAITIKU_VENV_DIR:-${ROOT_DIR}/.venv}"

if [ ! -x "${VENV_DIR}/bin/pytest" ]; then
  "${ROOT_DIR}/tools/bin/bootstrap-python.sh"
fi

exec "${VENV_DIR}/bin/python" "${ROOT_DIR}/tools/python/test_suite_runner.py" "$@"
