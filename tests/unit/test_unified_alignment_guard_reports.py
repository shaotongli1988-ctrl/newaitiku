from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def load_guard_module():
    root = Path(__file__).resolve().parents[2]
    module_path = root / "tools/python/unified_alignment_guard.py"
    spec = importlib.util.spec_from_file_location("unified_alignment_guard", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_load_waiver_payload_supports_checks_and_domains(tmp_path: Path) -> None:
    guard = load_guard_module()
    waiver_path = tmp_path / "waivers.json"
    waiver_path.write_text(
        json.dumps(
            {
                "checks": [{"name": "contracts:question-fields", "reason": "legacy bridge"}],
                "domains": [{"name": "documentation", "reason": "doc freeze"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = guard.load_waiver_payload(str(waiver_path))
    assert payload["checks"]["contracts:question-fields"] == "legacy bridge"
    assert payload["domains"]["documentation"] == "doc freeze"


def test_classify_results_applies_exact_and_domain_waivers() -> None:
    guard = load_guard_module()
    results = [
        guard.CheckResult(domain="field", name="contracts:question-fields", ok=False, detail="drift"),
        guard.CheckResult(domain="documentation", name="docs:readme", ok=False, detail="stale"),
        guard.CheckResult(domain="page", name="frontend:ok", ok=True, detail="pass"),
    ]
    waiver_payload = {
        "checks": {"contracts:question-fields": "legacy window"},
        "domains": {"documentation": "docs follow-up"},
    }

    failed, waived, missing = guard.classify_results(results, waiver_payload)
    assert not failed
    assert {(item.name, reason) for item, reason in waived} == {
        ("contracts:question-fields", "legacy window"),
        ("docs:readme", "docs follow-up"),
    }
    assert "api" in missing


def test_extract_question_bank_module_report_reads_schema_and_contract(tmp_path: Path) -> None:
    guard = load_guard_module()
    (tmp_path / "data").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "data/schema.sql").write_text(
        """
        CREATE TABLE IF NOT EXISTS "user" (
          id TEXT PRIMARY KEY,
          phone TEXT NOT NULL,
          password TEXT NOT NULL,
          status TEXT NOT NULL,
          extJson TEXT NOT NULL,
          createTime TEXT NOT NULL,
          updateTime TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS question (
          id TEXT PRIMARY KEY,
          knowledgeId TEXT NOT NULL,
          userId TEXT NOT NULL,
          type TEXT NOT NULL,
          stem TEXT NOT NULL,
          optionsJson TEXT NOT NULL,
          answer TEXT NOT NULL,
          status TEXT NOT NULL,
          extJson TEXT NOT NULL,
          createTime TEXT NOT NULL,
          updateTime TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS task (
          id TEXT PRIMARY KEY,
          userId TEXT NOT NULL,
          type TEXT NOT NULL,
          status TEXT NOT NULL,
          progress TEXT NOT NULL,
          extJson TEXT NOT NULL,
          createTime TEXT NOT NULL,
          updateTime TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS knowledge (
          id TEXT PRIMARY KEY,
          parentId TEXT,
          name TEXT NOT NULL,
          sort INTEGER NOT NULL,
          status TEXT NOT NULL,
          extJson TEXT NOT NULL,
          createTime TEXT NOT NULL,
          updateTime TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS userAuth (
          id TEXT PRIMARY KEY,
          userId TEXT NOT NULL,
          type TEXT NOT NULL,
          openid TEXT NOT NULL,
          unionid TEXT NOT NULL,
          extJson TEXT NOT NULL,
          createTime TEXT NOT NULL,
          updateTime TEXT NOT NULL
        );
        """,
        encoding="utf-8",
    )
    contract_lines = []
    for module_name, fields in guard.EXPECTED_QUESTION_BANK_MODULE_FIELDS.items():
        contract_lines.append(f"- `{module_name}`")
        contract_lines.append("  - " + ", ".join(f"`{field}`" for field in fields))
    (tmp_path / "docs/question-bank-contract.md").write_text("\n".join(contract_lines), encoding="utf-8")

    report = guard.extract_question_bank_module_report(tmp_path)
    assert len(report) == 5
    assert all(item["status"] == "PASS" for item in report)


def test_render_markdown_report_includes_question_bank_and_waivers() -> None:
    guard = load_guard_module()
    payload = {
        "phase": "final",
        "task": "demo",
        "mode": "questionBank",
        "summary": {"totalChecks": 3, "failedChecks": 0, "waivedChecks": 1, "missingDomains": [], "status": "PASS"},
        "failedChecks": [],
        "waivedChecks": [{"domain": "documentation", "name": "docs:readme", "detail": "stale", "reason": "approved"}],
        "domainSummary": [{"domain": "field", "label": "Field Standards", "configuredChecks": 1, "failedChecks": 0, "waivedChecks": 0, "status": "PASS"}],
        "questionBankModules": [{"module": "question", "schemaOk": True, "contractDocOk": True, "extJsonOk": True, "status": "PASS"}],
    }

    markdown = guard.render_markdown_report(payload)
    assert "## Waived Checks" in markdown
    assert "## questionBank Module Summary" in markdown
    assert "`question`" in markdown
