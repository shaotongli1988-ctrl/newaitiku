from __future__ import annotations

import re
from pathlib import Path


STALE_PASSED_COUNT_RE = re.compile(r"\b\d+\s+passed\b", re.IGNORECASE)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_docs_do_not_hardcode_pass_counts() -> None:
    root = _repo_root()
    readme_text = (root / "README.md").read_text(encoding="utf-8")
    self_check_text = (root / "docs/alignment-self-check.md").read_text(encoding="utf-8")

    assert STALE_PASSED_COUNT_RE.search(readme_text) is None
    assert STALE_PASSED_COUNT_RE.search(self_check_text) is None
