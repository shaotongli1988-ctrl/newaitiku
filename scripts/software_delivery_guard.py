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
sys.path.insert(0, str(SKILL_SCRIPTS_DIR))

from software_delivery_guard import main


if __name__ == "__main__":
    sys.exit(main())
