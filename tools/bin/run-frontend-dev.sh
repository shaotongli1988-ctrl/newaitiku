#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"

if [ ! -d "${FRONTEND_DIR}/node_modules" ]; then
  echo "frontend dependencies are missing. Run 'cd frontend && npm ci' first." >&2
  exit 1
fi

exec npm --prefix "${FRONTEND_DIR}" run dev -- --host 127.0.0.1 --port 5173
