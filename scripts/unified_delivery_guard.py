#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

# Guard implementation lives in tools/python/unified_alignment_guard.py,
# including cross-group access prevention checks.
from tools.python.unified_alignment_guard import main


if __name__ == "__main__":
    sys.exit(main())
