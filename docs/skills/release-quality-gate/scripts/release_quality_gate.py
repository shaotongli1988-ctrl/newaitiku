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
    has_impl = any(token in item for item in normalized for token in ("frontend/", "backend/", "/app/", "/src/"))
    has_tests = any(token in item for item in normalized for token in ("test", "spec", "__tests__"))
    if has_impl and not has_tests:
        warnings.append(WarningItem("quality-gate-test-missing", "medium", "检测到实现改动，但未发现测试或用例更新。"))
    return dedupe_warnings(warnings)


def render_quality_gate_template(release_name: str, owner: str, quality_bar: str) -> str:
    quality_text = quality_bar or "补充单测、集成、回归、冒烟、覆盖率和 UAT 的通过标准。"
    return f"""# Release Quality Gate: {release_name}

## Metadata

- Release: {release_name}
- Owner: {owner}

## Quality Bar

{quality_text}

## Test Results

- Unit tests:
- Integration tests:
- Regression tests:
- Smoke tests:

## Defect Status

- Blocking defects:
- Accepted risks:

## UAT

- UAT result:
- Follow-up issues:
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="发布质量门禁守卫")
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--fail-on", choices=("auto", "none", "high", "medium", "low"), default="auto")
    parser.add_argument("--report-md", default="")
    parser.add_argument("--report-json", default="")
    parser.add_argument("--release-name", default="release-to-fill")
    parser.add_argument("--owner", default="owner-to-fill")
    parser.add_argument("--quality-bar", default="")
    parser.add_argument("--output-md", default="")
    args = parser.parse_args()

    if args.output_md:
        content = render_quality_gate_template(args.release_name, args.owner, args.quality_bar)
        write_report(args.output_md, content)
        print(content)
        return 0

    cwd = Path(args.cwd).resolve()
    changed_files = collect_changed_files(cwd, args.changed_file)
    threshold = compute_threshold(args.phase, args.fail_on)
    warnings = build_warnings(changed_files)
    report = render_guard_report("Release Quality Gate", args.phase, cwd, threshold, changed_files, warnings)
    print(report)
    write_report(args.report_md, report)
    write_json_report(
        args.report_json,
        standard_guard_payload(
            guard_name="release-quality-gate",
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
