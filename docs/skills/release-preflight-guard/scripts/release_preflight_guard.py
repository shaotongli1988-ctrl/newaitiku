#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILLS_ROOT / "shared-guard-runtime" / "scripts"))

from change_set import collect_changed_files, read_text  # type: ignore
from guard_runtime import (  # type: ignore
    WarningItem,
    dedupe_warnings,
    render_guard_report,
    standard_guard_payload,
    warning_payload,
)
from report_writer import write_json_report, write_report  # type: ignore
from severity import compute_threshold, warning_meets_threshold  # type: ignore


def build_warnings(changed_files: list[Path]) -> list[WarningItem]:
    warnings: list[WarningItem] = []
    changed_text = " ".join(path.as_posix().lower() for path in changed_files)
    has_impl = any(token in changed_text for token in ("frontend/", "backend/", "/app/", "/src/"))
    has_frontend = any(token in changed_text for token in ("frontend/", "/src/"))
    has_backend = any(token in changed_text for token in ("backend/", "/app/"))
    has_deploy = any(token in changed_text for token in ("docker", "k8s", "deploy", "helm", ".github/workflows", "scripts/"))
    has_docs = any(path.suffix.lower() == ".md" or "/docs/" in path.as_posix().lower() for path in changed_files)
    has_env = any(".env" in path.name.lower() or "config" in path.as_posix().lower() for path in changed_files)
    has_db = any(token in path.as_posix().lower() for path in changed_files for token in ("migration", "schema", "sql", "prisma"))
    doc_text = "\n".join(
        read_text(path, limit=20_000)
        for path in changed_files
        if path.suffix.lower() == ".md" or "/docs/" in path.as_posix().lower()
    ).lower()
    has_release_runbook = any(token in doc_text for token in ("发布", "上线", "部署", "验证", "测试与验证", "风险说明"))
    has_config_note = any(token in doc_text for token in ("环境", "配置", "只读接口", "不涉及数据库", "不新增后端写接口", "不修改接口结构"))
    frontend_only_batch = has_frontend and not has_backend and not has_db

    if has_impl and not has_deploy and not (frontend_only_batch and has_docs and has_release_runbook):
        warnings.append(WarningItem("deploy-evidence-missing", "medium", "实现改动存在，但未发现部署/发布相关证据。"))
    if has_impl and not has_docs:
        warnings.append(WarningItem("release-doc-missing", "medium", "实现改动存在，但未发现上线说明或发布文档更新。"))
    if has_impl and not has_env and not (frontend_only_batch and has_docs and has_config_note):
        warnings.append(WarningItem("config-check-missing", "medium", "实现改动存在，但未发现配置/环境差异核对证据。"))
    if has_db and not has_docs:
        warnings.append(WarningItem("db-change-without-runbook", "high", "数据库变更存在，但未发现对应的上线/回滚说明。"))
    return dedupe_warnings(warnings)


def main() -> int:
    parser = argparse.ArgumentParser(description="发布前检查守卫")
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--fail-on", choices=("auto", "none", "high", "medium", "low"), default="auto")
    parser.add_argument("--report-md", default="")
    parser.add_argument("--report-json", default="")
    args = parser.parse_args()

    cwd = Path(args.cwd).resolve()
    changed_files = collect_changed_files(cwd, args.changed_file)
    threshold = compute_threshold(args.phase, args.fail_on)
    warnings = build_warnings(changed_files)
    report = render_guard_report("Release Preflight Guard", args.phase, cwd, threshold, changed_files, warnings)
    print(report)
    write_report(args.report_md, report)
    write_json_report(
        args.report_json,
        standard_guard_payload(
            guard_name="release-preflight-guard",
            phase=args.phase,
            cwd=cwd,
            threshold=threshold,
            changed_files=changed_files,
            warnings=warnings,
        ),
    )
    return 1 if any(warning_meets_threshold(item.severity, threshold) for item in warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
