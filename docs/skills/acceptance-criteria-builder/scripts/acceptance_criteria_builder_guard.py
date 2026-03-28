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
    task_lower = task.lower()
    has_acceptance_text = any(token in task_lower for token in ("验收", "given", "when", "then", "uat")) or any(
        token in doc_text for token in ("验收", "given", "when", "then", "uat", "场景", "预期结果")
    )
    if not has_acceptance_text:
        warnings.append(WarningItem("acceptance-criteria-missing", "medium", "任务描述中未明显体现验收标准或 Given/When/Then 口径。"))
    if changed_files and not has_docs:
        warnings.append(WarningItem("acceptance-doc-missing", "medium", "检测到改动，但未发现验收说明或 UAT 文档更新。"))
    return dedupe_warnings(warnings)


def render_acceptance_template(story_title: str, owner: str, actors: str) -> str:
    actor_text = actors or "补充角色、使用者和参与验收的对象。"
    return f"""# Acceptance Criteria: {story_title}

## Metadata

- Story: {story_title}
- Owner: {owner}
- Actors: {actor_text}

## Given / When / Then

1. Given preconditions are satisfied
   When the user performs the primary action
   Then the expected result is visible and auditable

## Scenario Matrix

- Normal path:
- Error path:
- Boundary path:
- Permission path:
- State path:

## UAT Notes

- Entry conditions:
- Test data:
- Expected result:
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="验收标准构建守卫")
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--fail-on", choices=("auto", "none", "high", "medium", "low"), default="auto")
    parser.add_argument("--report-md", default="")
    parser.add_argument("--report-json", default="")
    parser.add_argument("--story-title", default="new-story")
    parser.add_argument("--owner", default="owner-to-fill")
    parser.add_argument("--actors", default="")
    parser.add_argument("--output-md", default="")
    args = parser.parse_args()

    if args.output_md:
        content = render_acceptance_template(args.story_title, args.owner, args.actors)
        write_report(args.output_md, content)
        print(content)
        return 0

    cwd = Path(args.cwd).resolve()
    changed_files = collect_changed_files(cwd, args.changed_file)
    threshold = compute_threshold(args.phase, args.fail_on)
    warnings = build_warnings(changed_files, args.task)
    report = render_guard_report("Acceptance Criteria Builder", args.phase, cwd, threshold, changed_files, warnings)
    print(report)
    write_report(args.report_md, report)
    write_json_report(
        args.report_json,
        standard_guard_payload(
            guard_name="acceptance-criteria-builder",
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
