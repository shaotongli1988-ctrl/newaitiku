#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILLS_ROOT / "shared-guard-runtime" / "scripts"))

from change_set import collect_changed_files  # type: ignore
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
    normalized = [path.as_posix().lower() for path in changed_files]
    has_db = any(token in item for item in normalized for token in ("migration", "schema", "sql", "prisma"))
    has_config = any(token in item for item in normalized for token in ("config", ".env", "deploy", "docker", "helm"))
    has_flag = any(token in item for item in normalized for token in ("feature", "toggle", "flag", "switch"))
    has_doc = any("/docs/" in item or item.endswith(".md") for item in normalized)

    if has_db and not has_doc:
        warnings.append(WarningItem("rollback-doc-missing", "high", "存在数据库改动，但未发现回滚步骤或回滚说明。"))
    if has_config and not has_doc:
        warnings.append(WarningItem("config-rollback-missing", "medium", "存在配置/部署改动，但未发现配置回滚说明。"))
    if (has_db or has_config) and not has_flag:
        warnings.append(WarningItem("kill-switch-missing", "medium", "发布涉及数据库或配置变更，但未发现功能开关/止血手段证据。"))
    return dedupe_warnings(warnings)


def render_rollback_template(application: str, owner: str, release_scope: str) -> str:
    return f"""# Rollback Readiness: {application}

## Metadata

- Application: {application}
- Owner: {owner}
- Release scope: {release_scope}

## Application Rollback

- Previous stable version:
- Rollback trigger:
- Rollback execution command:

## Config Rollback

- Config keys or manifests involved:
- Safe fallback values:
- Config verification steps:

## Database Strategy

- Schema compatibility window:
- Data backfill rollback or compensation path:
- Irreversible change check:

## Kill Switch

- Feature flag / switch:
- Degrade action:
- Traffic stop condition:

## Verification

- Health checks:
- Business checks:
- Owner approval:
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="回滚就绪性守卫")
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--fail-on", choices=("auto", "none", "high", "medium", "low"), default="auto")
    parser.add_argument("--report-md", default="")
    parser.add_argument("--report-json", default="")
    parser.add_argument("--application", default="critical-application")
    parser.add_argument("--owner", default="owner-to-fill")
    parser.add_argument("--release-scope", default="main release")
    parser.add_argument("--output-md", default="")
    args = parser.parse_args()

    output_md = getattr(args, "output_md", "")
    if output_md:
        content = render_rollback_template(
            getattr(args, "application", "critical-application"),
            getattr(args, "owner", "owner-to-fill"),
            getattr(args, "release_scope", "main release"),
        )
        write_report(output_md, content)
        print(content)
        return 0

    cwd = Path(args.cwd).resolve()
    changed_files = collect_changed_files(cwd, args.changed_file)
    threshold = compute_threshold(args.phase, args.fail_on)
    warnings = build_warnings(changed_files)
    report = render_guard_report("Rollback Readiness Guard", args.phase, cwd, threshold, changed_files, warnings)
    print(report)
    write_report(args.report_md, report)
    write_json_report(
        args.report_json,
        standard_guard_payload(
            guard_name="rollback-readiness-guard",
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
