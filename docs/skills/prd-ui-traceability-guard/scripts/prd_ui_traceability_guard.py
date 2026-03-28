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


def build_warnings(changed_files: list[Path]) -> list[WarningItem]:
    warnings: list[WarningItem] = []
    normalized = [path.as_posix().lower() for path in changed_files]
    has_page = any(token in item for item in normalized for token in ("frontend/src/views", "frontend/src/components"))
    has_prd = any("/docs/" in item or "prd" in item or "prototype" in item or item.endswith(".md") for item in normalized)
    if has_page and not has_prd:
        warnings.append(WarningItem("page-without-prd-trace", "medium", "检测到页面/交互改动，但未发现 PRD/原型追踪证据。"))
    return dedupe_warnings(warnings)


def render_traceability_template(feature_name: str, owner: str) -> str:
    return f"""# PRD UI Traceability Matrix: {feature_name}

## Metadata

- Feature: {feature_name}
- Owner: {owner}

## Mapping Matrix

| PRD Item | Prototype | Page / Component | Action / Dialog | Copy / State | Status |
| --- | --- | --- | --- | --- | --- |
| Primary flow |  |  |  |  | todo |

## Missing Items

- Unimplemented pages:
- Unimplemented dialogs or flows:
- Copy / empty / error states not aligned:
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="PRD 与页面追踪守卫")
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--fail-on", choices=("auto", "none", "high", "medium", "low"), default="auto")
    parser.add_argument("--report-md", default="")
    parser.add_argument("--report-json", default="")
    parser.add_argument("--feature-name", default="new-feature")
    parser.add_argument("--owner", default="owner-to-fill")
    parser.add_argument("--output-md", default="")
    args = parser.parse_args()

    if args.output_md:
        content = render_traceability_template(args.feature_name, args.owner)
        write_report(args.output_md, content)
        print(content)
        return 0

    cwd = Path(args.cwd).resolve()
    changed_files = collect_changed_files(cwd, args.changed_file)
    threshold = compute_threshold(args.phase, args.fail_on)
    warnings = build_warnings(changed_files)
    report = render_guard_report("PRD UI Traceability Guard", args.phase, cwd, threshold, changed_files, warnings)
    print(report)
    write_report(args.report_md, report)
    write_json_report(
        args.report_json,
        standard_guard_payload(
            guard_name="prd-ui-traceability-guard",
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
