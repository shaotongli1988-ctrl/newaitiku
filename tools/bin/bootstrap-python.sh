#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="${NEWAITIKU_VENV_DIR:-${ROOT_DIR}/.venv}"
PACKAGES_DIR="${ROOT_DIR}/tools/packages"
REQUIREMENTS_FILE="${ROOT_DIR}/tools/python/requirements-dev.txt"
PYTHON_BIN="${NEWAITIKU_PYTHON_BIN:-}"

mkdir -p "${PACKAGES_DIR}"

is_openssl_python() {
  local bin="$1"
  [ -x "$bin" ] || return 1
  "$bin" -c "import ssl; raise SystemExit(0 if 'OpenSSL' in ssl.OPENSSL_VERSION else 1)" >/dev/null 2>&1
}

pick_python_bin() {
  if [ -n "${PYTHON_BIN}" ] && [ -x "${PYTHON_BIN}" ]; then
    echo "${PYTHON_BIN}"
    return 0
  fi

  local candidates=(
    "/opt/homebrew/bin/python3.13"
    "/opt/homebrew/opt/python@3.13/bin/python3.13"
    "/opt/homebrew/bin/python3"
    "/usr/local/bin/python3"
    "python3"
  )

  local candidate
  for candidate in "${candidates[@]}"; do
    if is_openssl_python "${candidate}"; then
      echo "${candidate}"
      return 0
    fi
  done

  for candidate in "${candidates[@]}"; do
    if [ -x "${candidate}" ] || command -v "${candidate}" >/dev/null 2>&1; then
      echo "${candidate}"
      return 0
    fi
  done

  return 1
}

SELECTED_PYTHON="$(pick_python_bin)"
echo "Using Python interpreter: ${SELECTED_PYTHON}"
echo "Interpreter SSL backend: $("${SELECTED_PYTHON}" -c 'import ssl; print(ssl.OPENSSL_VERSION)')"

if [ ! -x "${VENV_DIR}/bin/python" ]; then
  "${SELECTED_PYTHON}" -m venv "${VENV_DIR}"
else
  VENV_SSL_VERSION="$("${VENV_DIR}/bin/python" -c 'import ssl; print(ssl.OPENSSL_VERSION)' 2>/dev/null || true)"
  if echo "${VENV_SSL_VERSION}" | grep -q "LibreSSL"; then
    echo "Detected LibreSSL-based virtualenv, recreating ${VENV_DIR} with ${SELECTED_PYTHON}..."
    "${SELECTED_PYTHON}" -m venv --clear "${VENV_DIR}"
  fi
fi

"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/python" -m pip install -r "${REQUIREMENTS_FILE}"
"${VENV_DIR}/bin/python" -m pip download -r "${REQUIREMENTS_FILE}" -d "${PACKAGES_DIR}"

echo "Python environment is ready at ${VENV_DIR}"
echo "Dependency cache is available at ${PACKAGES_DIR}"
