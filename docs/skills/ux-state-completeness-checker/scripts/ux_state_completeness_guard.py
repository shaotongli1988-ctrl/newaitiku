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


def build_warnings(changed_files: list[Path]) -> list[WarningItem]:
    warnings: list[WarningItem] = []
    for path in changed_files:
        if path.suffix.lower() != ".vue":
            continue
        text = read_text(path).lower()
        if "<el-table" in text or "<el-form" in text or "<el-dialog" in text:
            if "loading" not in text:
                warnings.append(WarningItem("loading-state-missing", "medium", "复杂页面/组件未明显体现 loading 状态。", str(path)))
            if "empty" not in text and "error" not in text:
                warnings.append(WarningItem("empty-error-state-missing", "medium", "复杂页面/组件未明显体现空状态或错误态。", str(path)))
    return dedupe_warnings(warnings)


def render_ux_state_template(page_name: str, owner: str) -> str:
    return f"""# UX State Matrix: {page_name}

## Metadata

- Page: {page_name}
- Owner: {owner}

## States

| State | Covered | Notes |
| --- | --- | --- |
| Loading |  |  |
| Empty |  |  |
| Error |  |  |
| Disabled / Permission |  |  |
| Confirm / Success |  |  |
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="页面状态完整性守卫")
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--fail-on", choices=("auto", "none", "high", "medium", "low"), default="auto")
    parser.add_argument("--report-md", default="")
    parser.add_argument("--report-json", default="")
    parser.add_argument("--page-name", default="page-to-fill")
    parser.add_argument("--owner", default="owner-to-fill")
    parser.add_argument("--output-md", default="")
    args = parser.parse_args()

    if args.output_md:
        content = render_ux_state_template(args.page_name, args.owner)
        write_report(args.output_md, content)
        print(content)
        return 0

    cwd = Path(args.cwd).resolve()
    changed_files = collect_changed_files(cwd, args.changed_file)
    threshold = compute_threshold(args.phase, args.fail_on)
    warnings = build_warnings(changed_files)
    report = render_guard_report("UX State Completeness Checker", args.phase, cwd, threshold, changed_files, warnings)
    print(report)
    write_report(args.report_md, report)
    write_json_report(
        args.report_json,
        standard_guard_payload(
            guard_name="ux-state-completeness-checker",
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
