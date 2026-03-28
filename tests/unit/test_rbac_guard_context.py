from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_rbac_guard():
    module_path = Path.home() / ".codex/skills/rbac-alignment-guard/scripts/rbac_alignment_guard.py"
    spec = importlib.util.spec_from_file_location("rbac_alignment_guard", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_detect_context_ignores_doc_and_test_support_only_changes() -> None:
    guard = load_rbac_guard()
    changed_files = [
        Path("/workspace/docs/contracts/current/contract.json"),
        Path("/workspace/docs/skills/software-development-readiness-governance/scripts/software_development_readiness_guard.py"),
        Path("/workspace/tests/unit/test_development_readiness_contract_package.py"),
    ]

    enabled, reason = guard.detect_context("", changed_files, False, set(), set())

    assert enabled is False
    assert reason == "no-rbac-evidence"


def test_scan_changed_files_skips_doc_and_test_support_paths(tmp_path: Path) -> None:
    guard = load_rbac_guard()
    contract_file = tmp_path / "docs" / "contracts" / "current" / "contract.json"
    contract_file.parent.mkdir(parents=True, exist_ok=True)
    contract_file.write_text('{"permissionKeys":["question:manage"]}', encoding="utf-8")

    scan = guard.scan_changed_files([contract_file])

    assert scan.scanned_backend_files == 0
    assert scan.scanned_frontend_files == 0
    assert scan.backend_permission_keys == set()
    assert scan.frontend_permission_keys == set()
