#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILLS_ROOT / "shared-guard-runtime" / "scripts"))

from change_set import collect_changed_files, read_text  # type: ignore
from guard_runtime import WarningItem, dedupe_warnings, render_guard_report, standard_guard_payload  # type: ignore
from report_writer import write_json_report, write_report  # type: ignore
from severity import compute_threshold, warning_meets_threshold  # type: ignore


def build_warnings(changed_files: list[Path], task: str) -> list[WarningItem]:
    warnings: list[WarningItem] = []
    normalized = [path.as_posix().lower() for path in changed_files]
    has_docs = any("/docs/" in item or item.endswith(".md") for item in normalized)
    doc_text = "\n".join(
        read_text(path, limit=20_000)
        for path in changed_files
        if path.suffix.lower() == ".md" or "/docs/" in path.as_posix().lower()
    ).lower()
    has_uat_handoff = any(token in doc_text for token in ("uat", "验收", "测试与验证", "预期结果", "入口", "环境"))
    if changed_files and not has_docs:
        warnings.append(WarningItem("uat-doc-missing", "medium", "检测到改动，但未发现 UAT 交接材料或验收说明。"))
    if task and "uat" not in task.lower() and "验收" not in task and not has_uat_handoff:
        warnings.append(WarningItem("uat-context-not-explicit", "low", "任务描述中未明显体现 UAT 或验收交接口径。"))
    return dedupe_warnings(warnings)


def render_uat_handoff_template(feature_name: str, owner: str, environment: str) -> str:
    env_text = environment or "补充 UAT 环境地址、入口路径和使用限制。"
    return f"""# UAT Handoff Pack: {feature_name}

## Metadata

- Feature: {feature_name}
- Owner: {owner}

## Access

{env_text}

## Test Accounts

- Primary account:
- Alternate account:
- Test data:

## Scenarios

- Primary scenario:
- Error / edge scenario:
- Expected result:

## Feedback

- Submission channel:
- Defect triage owner:
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="UAT 交接守卫")
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--fail-on", choices=("auto", "none", "high", "medium", "low"), default="auto")
    parser.add_argument("--report-md", default="")
    parser.add_argument("--report-json", default="")
    parser.add_argument("--feature-name", default="feature-to-fill")
    parser.add_argument("--owner", default="owner-to-fill")
    parser.add_argument("--environment", default="")
    parser.add_argument("--output-md", default="")
    args = parser.parse_args()

    if args.output_md:
        content = render_uat_handoff_template(args.feature_name, args.owner, args.environment)
        write_report(args.output_md, content)
        print(content)
        return 0

    cwd = Path(args.cwd).resolve()
    changed_files = collect_changed_files(cwd, args.changed_file)
    threshold = compute_threshold(args.phase, args.fail_on)
    warnings = build_warnings(changed_files, args.task)
    report = render_guard_report("UAT Handoff Guard", args.phase, cwd, threshold, changed_files, warnings)
    print(report)
    write_report(args.report_md, report)
    write_json_report(
        args.report_json,
        standard_guard_payload(
            guard_name="uat-handoff-guard",
            phase=args.phase,
            cwd=cwd,
            threshold=threshold,
            changed_files=changed_files,
            warnings=warnings,
            extra={"task": args.task},
        ),
    )
    return 1 if any(warning_meets_threshold(item.severity, threshold) for item in warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
