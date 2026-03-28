#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILLS_ROOT / "shared-guard-runtime" / "scripts"))

from change_set import collect_changed_files  # type: ignore
from guard_runtime import WarningItem, dedupe_warnings, render_guard_report, standard_guard_payload  # type: ignore
from report_writer import write_json_report, write_report  # type: ignore
from severity import compute_threshold, warning_meets_threshold  # type: ignore


def build_warnings(changed_files: list[Path], task: str) -> list[WarningItem]:
    warnings: list[WarningItem] = []
    normalized = [path.as_posix().lower() for path in changed_files]
    has_arch_changes = any(
        token in item
        for item in normalized
        for token in ("schema", "migration", "prisma", "package.json", "pnpm-lock", "go.mod", "docker", "helm", "k8s", "/api/", "/backend/", "/frontend/")
    )
    has_docs = any("/docs/" in item or item.endswith(".md") or "adr" in item for item in normalized)
    task_lower = task.lower()

    if has_arch_changes and not has_docs:
        warnings.append(WarningItem("adr-missing", "medium", "检测到可能影响架构或技术选型的改动，但未发现 ADR 或方案文档更新。"))
    if task and not any(token in task_lower for token in ("架构", "方案", "选型", "adr", "技术")):
        warnings.append(WarningItem("decision-context-weak", "low", "任务描述中未明显体现架构/方案/选型背景，请确认关键决策已记录。"))
    return dedupe_warnings(warnings)


def render_adr(
    *,
    title: str,
    owner: str,
    status: str,
    context: str,
    decision: str,
    alternatives: str,
) -> str:
    context_text = context or "补充触发原因、约束、目标和非目标。"
    decision_text = decision or "补充最终决策，以及为何在当前阶段采用该方案。"
    alternatives_text = alternatives or "方案 A：\n- 优点\n- 缺点\n\n方案 B：\n- 优点\n- 缺点"
    return f"""# ADR: {title}

## Metadata

- Status: {status}
- Owner: {owner}

## Context

{context_text}

## Decision

{decision_text}

## Alternatives Considered

{alternatives_text}

## Consequences

- Positive impact:
- Risk / tradeoff:
- Rollback or exit condition:

## Scope

- Modules / services:
- Data / interface impact:
- Delivery / operation impact:

## Follow-up Actions

1. Document and review
2. Implementation and validation
3. Rollout and fallback verification
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="架构决策记录守卫")
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--fail-on", choices=("auto", "none", "high", "medium", "low"), default="auto")
    parser.add_argument("--report-md", default="")
    parser.add_argument("--report-json", default="")
    parser.add_argument("--decision-title", default="new-architecture-decision")
    parser.add_argument("--owner", default="owner-to-fill")
    parser.add_argument("--status", default="Proposed")
    parser.add_argument("--context", default="")
    parser.add_argument("--decision", default="")
    parser.add_argument("--alternatives", default="")
    parser.add_argument("--output-md", default="")
    args = parser.parse_args()

    if args.output_md:
        adr = render_adr(
            title=args.decision_title,
            owner=args.owner,
            status=args.status,
            context=args.context,
            decision=args.decision,
            alternatives=args.alternatives,
        )
        write_report(args.output_md, adr)
        print(adr)
        return 0

    cwd = Path(args.cwd).resolve()
    changed_files = collect_changed_files(cwd, args.changed_file)
    threshold = compute_threshold(args.phase, args.fail_on)
    warnings = build_warnings(changed_files, args.task)
    report = render_guard_report("Architecture Decision Recorder", args.phase, cwd, threshold, changed_files, warnings)
    print(report)
    write_report(args.report_md, report)
    write_json_report(
        args.report_json,
        standard_guard_payload(
            guard_name="architecture-decision-recorder",
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
