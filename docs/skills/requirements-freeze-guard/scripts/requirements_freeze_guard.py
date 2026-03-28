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


def build_warnings(changed_files: list[Path], task: str) -> list[WarningItem]:
    warnings: list[WarningItem] = []
    normalized = [path.as_posix().lower() for path in changed_files]
    has_docs = any("/docs/" in item or item.endswith(".md") for item in normalized)
    has_impl = any(token in item for item in normalized for token in ("frontend/", "backend/", "/app/", "/src/"))
    task_lower = task.lower()
    doc_text = "\n".join(
        read_text(path, limit=20_000)
        for path in changed_files
        if path.suffix.lower() == ".md" or "/docs/" in path.as_posix().lower()
    ).lower()
    has_freeze_evidence = any(token in doc_text for token in ("冻结", "验收标准", "given", "when", "then", "实施边界", "当前结论"))

    if has_impl and not has_docs:
        warnings.append(WarningItem("impl-without-requirement-doc", "medium", "检测到实现改动，但未发现需求/说明文档更新。"))
    if task and not any(token in task_lower for token in ("需求", "验收", "原型", "prd", "用户故事")) and not has_freeze_evidence:
        warnings.append(WarningItem("acceptance-not-explicit", "low", "任务描述中未明显体现需求或验收口径，请确认需求已冻结。"))
    return dedupe_warnings(warnings)


def render_freeze_template(requirement_title: str, owner: str, scope: str, assumptions: str) -> str:
    scope_text = scope or "补充本次需求范围、明确不做什么，以及涉及的角色和页面。"
    assumptions_text = assumptions or "补充依赖前提、约束条件、接口口径和待确认项。"
    return f"""# Requirements Freeze Record: {requirement_title}

## Metadata

- Requirement: {requirement_title}
- Owner: {owner}
- Status: Frozen

## Scope

{scope_text}

## Acceptance Baseline

- Core acceptance criteria:
- Boundary / exception criteria:

## Assumptions and Constraints

{assumptions_text}

## Change Control

- Pending changes:
- Impact assessment:
- Final decision owner:

## Risks

- Delivery risks:
- Dependency risks:
- Mitigation / rollback notes:
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="需求冻结守卫")
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--fail-on", choices=("auto", "none", "high", "medium", "low"), default="auto")
    parser.add_argument("--report-md", default="")
    parser.add_argument("--report-json", default="")
    parser.add_argument("--requirement-title", default="new-requirement")
    parser.add_argument("--owner", default="owner-to-fill")
    parser.add_argument("--scope", default="")
    parser.add_argument("--assumptions", default="")
    parser.add_argument("--output-md", default="")
    args = parser.parse_args()

    if args.output_md:
        content = render_freeze_template(args.requirement_title, args.owner, args.scope, args.assumptions)
        write_report(args.output_md, content)
        print(content)
        return 0

    cwd = Path(args.cwd).resolve()
    changed_files = collect_changed_files(cwd, args.changed_file)
    threshold = compute_threshold(args.phase, args.fail_on)
    warnings = build_warnings(changed_files, args.task)
    report = render_guard_report("Requirements Freeze Guard", args.phase, cwd, threshold, changed_files, warnings)
    print(report)
    write_report(args.report_md, report)
    write_json_report(
        args.report_json,
        standard_guard_payload(
            guard_name="requirements-freeze-guard",
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
