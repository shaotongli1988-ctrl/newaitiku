#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="${NEWAITIKU_VENV_DIR:-${ROOT_DIR}/.venv}"

if [ ! -x "${VENV_DIR}/bin/python" ]; then
  "${ROOT_DIR}/tools/bin/bootstrap-python.sh"
fi

if [ "$#" -eq 0 ]; then
  exec "${VENV_DIR}/bin/python" "${ROOT_DIR}/tools/python/unified_alignment_guard.py" --phase final --run-compile --run-pytest
fi

exec "${VENV_DIR}/bin/python" "${ROOT_DIR}/tools/python/unified_alignment_guard.py" "$@"
