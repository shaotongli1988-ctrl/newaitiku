from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_state_machine_guard():
    module_path = Path.home() / ".codex/skills/state-machine-alignment/scripts/state_machine_guard.py"
    spec = importlib.util.spec_from_file_location("state_machine_guard", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_detect_context_ignores_skill_support_only_changes() -> None:
    guard = load_state_machine_guard()
    changed_files = [
        Path("/workspace/docs/skills/software-delivery-unified-governance/scripts/software_delivery_guard.py"),
        Path("/workspace/.codex/skills/three-stage-skill-orchestrator/scripts/three_stage_orchestrator.py"),
    ]

    enabled, reason = guard.detect_context("", changed_files, set(), set(), False)

    assert enabled is False
    assert reason == "no-state-machine-evidence"


def test_scan_changed_files_skips_skill_support_paths(tmp_path: Path) -> None:
    guard = load_state_machine_guard()
    skill_script = tmp_path / "docs" / "skills" / "state-machine-alignment" / "scripts" / "state_machine_guard.py"
    skill_script.parent.mkdir(parents=True, exist_ok=True)
    skill_script.write_text("STATE = 'draft'\\nTRANSITION = 'draft -> published'\\n", encoding="utf-8")

    scan = guard.scan_changed_files([skill_script])

    assert scan.scanned_backend_files == 0
    assert scan.scanned_frontend_files == 0
    assert scan.backend_states == set()
    assert scan.backend_transitions == set()
