#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS_DIR = (
    ROOT_DIR
    / "docs"
    / "skills"
    / "software-delivery-unified-governance"
    / "scripts"
)
SHARED_RUNTIME_SCRIPTS_DIR = (
    ROOT_DIR
    / "docs"
    / "skills"
    / "shared-guard-runtime"
    / "scripts"
)
FALLBACK_SHARED_RUNTIME_SCRIPTS_DIR = (
    Path.home()
    / ".codex"
    / "skills"
    / "shared-guard-runtime"
    / "scripts"
)
sys.path.insert(0, str(SKILL_SCRIPTS_DIR))
if SHARED_RUNTIME_SCRIPTS_DIR.exists():
    sys.path.insert(0, str(SHARED_RUNTIME_SCRIPTS_DIR))
if FALLBACK_SHARED_RUNTIME_SCRIPTS_DIR.exists():
    sys.path.insert(0, str(FALLBACK_SHARED_RUNTIME_SCRIPTS_DIR))

from software_delivery_guard import main


if __name__ == "__main__":
    sys.exit(main())
