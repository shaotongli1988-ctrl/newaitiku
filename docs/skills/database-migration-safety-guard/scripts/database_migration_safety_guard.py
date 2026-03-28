#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
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
    migration_files = [
        path for path in changed_files
        if any(token in path.as_posix().lower() for token in ("migration", "schema", "sql", "prisma"))
    ]
    if not migration_files:
        return []

    for path in migration_files:
        text = read_text(path).lower()
        sanitized = re.sub(r"--.*?$", "", text, flags=re.MULTILINE)
        if re.search(r"\bdrop\s+table\b|\bdrop\s+column\b", sanitized):
            warnings.append(WarningItem("destructive-ddl", "high", "检测到破坏性 DDL，请确认灰度与回滚方案。", str(path)))
        if re.search(r"\balter\s+table\b", sanitized) and "rollback" not in sanitized:
            warnings.append(WarningItem("alter-without-rollback", "high", "检测到 ALTER TABLE，但未发现回滚说明。", str(path)))
        if "create index" in sanitized and "concurrently" not in sanitized and "online" not in sanitized:
            warnings.append(WarningItem("index-build-risk", "medium", "检测到索引构建，但未发现在线/并发构建说明。", str(path)))
    return dedupe_warnings(warnings)


def main() -> int:
    parser = argparse.ArgumentParser(description="数据库迁移安全守卫")
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
    report = render_guard_report("Database Migration Safety Guard", args.phase, cwd, threshold, changed_files, warnings)
    print(report)
    write_report(args.report_md, report)
    write_json_report(
        args.report_json,
        standard_guard_payload(
            guard_name="database-migration-safety-guard",
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
