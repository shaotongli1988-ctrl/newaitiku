from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def load_guard_module():
    root = Path(__file__).resolve().parents[2]
    module_path = root / "docs/skills/software-development-readiness-governance/scripts/software_development_readiness_guard.py"
    spec = importlib.util.spec_from_file_location("software_development_readiness_guard", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_contract_package_uses_questionbank_mode(tmp_path: Path) -> None:
    guard = load_guard_module()
    cwd = tmp_path
    (cwd / "app").mkdir()
    (cwd / "docs").mkdir()
    (cwd / "frontend").mkdir()
    (cwd / "frontend/package.json").write_text(
        json.dumps({"dependencies": {"vue": "^3.0.0"}, "devDependencies": {"vite": "^8.0.0"}}),
        encoding="utf-8",
    )
    (cwd / "requirements.txt").write_text("fastapi==0.115.12\npydantic==2.10.6\n", encoding="utf-8")
    (cwd / "app/contracts.py").write_text(
        """
ROLE_SUPER_ADMIN = "super_admin"
ROLE_TEACHER = "teacher"
ROLE_STUDENT = "student"
MANAGED_PERMISSION_KEYS = ("question:manage", "analytics:view")
QUESTION_ERROR_CODES = {"NOT_FOUND": "QUESTION_NOT_FOUND"}
QUESTION_FIELDS = ("id", "knowledgeId")
TASK_FIELDS = ("id", "userId")
""",
        encoding="utf-8",
    )
    payload = {
        "extra": {
            "status": "READY_TO_START",
            "action": "READY_TO_START",
            "reason": "ok",
            "subguards": [],
        }
    }
    package = guard.build_contract_package(
        mode="questionBank",
        task="冻结题库模块实现基线",
        cwd=cwd,
        changed_files=[],
        payload=payload,
        in_scope_modules=["question", "knowledge"],
    )
    assert package["mode"] == "questionBank"
    assert package["scope"]["inScopeModules"] == ["question", "knowledge"]
    assert package["contracts"]["api"]["responseEnvelope"] == ["code", "message", "data"]
    assert len(package["contracts"]["questionBankModules"]) == 5


def test_emit_contract_package_writes_expected_files(tmp_path: Path) -> None:
    guard = load_guard_module()
    contract_dir = tmp_path / "docs/contracts/current"
    package = {
        "contractId": "dr-1",
        "generatedAt": "2026-03-21T10:00:00+08:00",
        "mode": "questionBank",
        "scope": {
            "businessGoal": "demo",
            "inScopeModules": ["question"],
            "outOfScopeModules": ["knowledge"],
            "affectedLayers": ["backend"],
        },
        "contracts": {
            "permissions": {"roles": ["teacher"], "permissionKeys": ["question:manage"]},
            "errorSemantics": {"questionErrorCodes": ["QUESTION_NOT_FOUND"]},
            "uiStandards": {"feedback": ["Toast"]},
            "questionBankModules": [
                {
                    "module": "question",
                    "scope": "IN_SCOPE",
                    "responseEnvelope": ["code", "message", "data"],
                    "extJsonPolicy": "contract-outside-fields-go-to-extJson",
                    "idOnlyRelations": True,
                }
            ],
        },
        "governance": {
            "readinessStatus": "READY_TO_START",
            "action": "READY_TO_START",
            "reason": "ok",
        },
        "testPlan": {
            "categories": ["normal"],
            "automationTargets": ["pytest-unit"],
            "mustCoverModules": ["question"],
        },
    }
    guard.emit_contract_package(tmp_path, package, contract_dir)
    assert (contract_dir / "contract.json").exists()
    assert (contract_dir / "contract.md").exists()
    assert (contract_dir / "test-plan.md").exists()
    assert (contract_dir / "module-summary.md").exists()
    assert (contract_dir / "waivers.json").exists()

    payload = json.loads((contract_dir / "contract.json").read_text(encoding="utf-8"))
    assert payload["contractId"] == "dr-1"
    assert payload["mode"] == "questionBank"


def test_current_sequence_excludes_retired_doc_only_guards() -> None:
    guard = load_guard_module()

    assert "database-schema-alignment-guard" not in guard.GUARD_SPECS
    assert "scope-and-data-permission-guard" not in guard.GUARD_SPECS
    assert "business-boundary-alignment-guard" not in guard.GUARD_SPECS
    assert "validation-semantics-alignment-guard" not in guard.GUARD_SPECS
    assert "visual-interaction-standard-guard" not in guard.GUARD_SPECS
    assert "nonfunctional-baseline-guard" not in guard.GUARD_SPECS
    assert guard.GUARD_SPECS["architecture-decision-recorder"].script_name == "architecture_decision_recorder_guard.py"
