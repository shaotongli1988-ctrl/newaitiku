from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_unified_delivery_guard():
    module_path = Path.home() / ".codex/skills/fullstack-unified-development-standards/scripts/unified_delivery_guard.py"
    spec = importlib.util.spec_from_file_location("unified_delivery_guard", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_warnings_skips_core_cross_layer_warnings_for_test_only_updates() -> None:
    guard = load_unified_delivery_guard()
    changed_files = [
        Path("/workspace/tests/unit/test_api_schema_drift_guard_templates.py"),
        Path("/workspace/tests/unit/test_question_bank_contract_guard_context.py"),
        Path("/workspace/tests/unit/test_fullstack_test_matrix_guard_context.py"),
    ]
    domains = guard.detect_domains(changed_files)
    surfaces = guard.detect_surfaces(changed_files)

    warnings = guard.build_warnings(
        phase="final",
        matched_triggers=["开发中总技能"],
        changed_files=changed_files,
        had_raw_changes=True,
        domains=domains,
        surfaces=surfaces,
        task="继续收敛 unified delivery guard 顶层 core 告警误报",
    )

    assert warnings == []


def test_build_warnings_keeps_backend_validation_signal_for_real_impl_change(tmp_path: Path) -> None:
    guard = load_unified_delivery_guard()
    changed_file = tmp_path / "app" / "api" / "validation_service.py"
    changed_file.parent.mkdir(parents=True, exist_ok=True)
    changed_file.write_text("def validate_required_length(value):\n    return value\n", encoding="utf-8")
    changed_files = [changed_file]
    domains = guard.detect_domains(changed_files)
    surfaces = guard.detect_surfaces(changed_files)

    warnings = guard.build_warnings(
        phase="final",
        matched_triggers=["开发中总技能"],
        changed_files=changed_files,
        had_raw_changes=True,
        domains=domains,
        surfaces=surfaces,
        task="继续实现后端校验规则",
    )

    warning_codes = {item.code for item in warnings}
    assert "backend-api-without-frontend" in warning_codes
    assert "validation-cross-layer-evidence" in warning_codes


def test_recommend_execution_skills_skips_cutover_hint_for_test_only_schema_guard_updates() -> None:
    guard = load_unified_delivery_guard()
    changed_files = [
        Path("/workspace/tests/unit/test_api_schema_drift_guard_templates.py"),
        Path("/workspace/tests/unit/test_unified_delivery_guard_core_warnings.py"),
    ]

    recommendations = guard.recommend_execution_skills(
        changed_files=changed_files,
        task="继续收敛 unified delivery guard 顶层 core 告警误报",
        surfaces=guard.detect_surfaces(changed_files),
    )

    assert all("cutover-backfill-executor" not in item for item in recommendations)


def test_detect_domains_ignores_validation_signal_from_doc_and_test_support_only_changes() -> None:
    guard = load_unified_delivery_guard()
    changed_files = [
        Path("/workspace/docs/contracts/current/contract.json"),
        Path("/workspace/docs/skills/software-development-readiness-governance/scripts/software_development_readiness_guard.py"),
        Path("/workspace/tests/unit/test_development_readiness_contract_package.py"),
    ]

    domains = guard.detect_domains(changed_files)
    surfaces = guard.detect_surfaces(changed_files)
    warnings = guard.build_warnings(
        phase="final",
        matched_triggers=["开发中总技能"],
        changed_files=changed_files,
        had_raw_changes=True,
        domains=domains,
        surfaces=surfaces,
        task="单独清理 docs/skills 历史命名不一致的镜像脚本与退役目录",
    )

    warning_codes = {item.code for item in warnings}
    assert "validation-cross-layer-evidence" not in warning_codes
    assert "permission-cross-layer-evidence" not in warning_codes
