from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_fullstack_test_matrix_guard():
    module_path = Path.home() / ".codex/skills/fullstack-test-matrix/scripts/fullstack_test_matrix_guard.py"
    spec = importlib.util.spec_from_file_location("fullstack_test_matrix_guard", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_scan_does_not_infer_impl_surfaces_from_test_only_changes() -> None:
    guard = load_fullstack_test_matrix_guard()
    changed_files = [
        Path("/workspace/tests/unit/test_api_schema_drift_guard_templates.py"),
        Path("/workspace/tests/unit/test_question_bank_contract_guard_context.py"),
    ]

    scan = guard.build_scan(changed_files)

    assert scan.changed_impl_files == []
    assert len(scan.changed_test_files) == 2
    assert scan.touched_backend is False
    assert scan.touched_api is False
    assert scan.touched_data is False
    assert scan.touched_permission is False


def test_build_scan_keeps_impl_surface_inference_for_real_code_changes(tmp_path: Path) -> None:
    guard = load_fullstack_test_matrix_guard()
    api_file = tmp_path / "app" / "api" / "schema_guard.py"
    api_file.parent.mkdir(parents=True, exist_ok=True)
    api_file.write_text("def save():\n    return {'ok': True}\n", encoding="utf-8")

    scan = guard.build_scan([api_file])

    assert scan.changed_test_files == []
    assert scan.changed_impl_files == [api_file]
    assert scan.touched_backend is True
    assert scan.touched_api is True
    assert scan.touched_data is True


def test_skill_support_only_changes_do_not_trigger_context_or_impl_surfaces() -> None:
    guard = load_fullstack_test_matrix_guard()
    changed_files = [
        Path("/workspace/docs/skills/software-delivery-unified-governance/scripts/software_delivery_guard.py"),
        Path("/workspace/.codex/skills/fullstack-test-matrix/scripts/fullstack_test_matrix_guard.py"),
    ]

    enabled, reason = guard.detect_context("", changed_files, set(), False)
    scan = guard.build_scan(changed_files)

    assert enabled is False
    assert reason == "no-test-matrix-evidence"
    assert scan.changed_test_files == []
    assert scan.changed_impl_files == []
    assert scan.touched_backend is False
    assert scan.touched_frontend is False
    assert scan.touched_api is False
    assert scan.touched_data is False
