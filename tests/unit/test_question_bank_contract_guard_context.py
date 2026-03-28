from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_question_bank_contract_guard():
    module_path = Path.home() / ".codex/skills/question-bank-contract-enforcer/scripts/question_bank_contract_guard.py"
    spec = importlib.util.spec_from_file_location("question_bank_contract_guard", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_detect_context_does_not_treat_repo_name_tiku_as_question_bank_path() -> None:
    guard = load_question_bank_contract_guard()

    context_enabled, reason = guard.detect_context(
        task="继续收敛 schema drift 告警",
        changed_files=[Path("/Users/demo/Code/newaitiku/tests/unit/test_api_schema_drift_guard_templates.py")],
        explicit_modules=set(),
        force=False,
    )

    assert context_enabled is False
    assert reason == "no-question-bank-evidence"


def test_looks_like_question_bank_path_keeps_real_business_paths() -> None:
    guard = load_question_bank_contract_guard()

    assert guard.looks_like_question_bank_path(
        Path("/workspace/frontend/src/question-bank/student/catalogService.ts")
    )


def test_looks_like_question_bank_path_ignores_non_product_docs_skill_paths() -> None:
    guard = load_question_bank_contract_guard()

    assert not guard.looks_like_question_bank_path(
        Path("/workspace/docs/skills/question-bank-contract-enforcer/scripts/question_bank_contract_guard.py")
    )
