#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILLS_ROOT / "shared-guard-runtime" / "scripts"))

from change_set import collect_changed_files  # type: ignore
from guard_runtime import WarningItem, dedupe_warnings, render_guard_report, standard_guard_payload  # type: ignore
from report_writer import write_json_report, write_report  # type: ignore
from severity import compute_threshold, warning_meets_threshold  # type: ignore


def git_status_summary(cwd: Path) -> str:
    result = subprocess.run(["git", "-c", "core.quotepath=false", "status", "--short"], cwd=str(cwd), capture_output=True, text=True, check=False)
    return result.stdout.strip()


def build_warnings(status_output: str, focused_changed_files: list[Path]) -> list[WarningItem]:
    warnings: list[WarningItem] = []
    status_lines = [line for line in status_output.splitlines() if line.strip()]
    if not status_lines:
        return warnings
    if focused_changed_files and all(line.startswith("?? ") for line in status_lines):
        return warnings
    if status_lines:
        warnings.append(WarningItem("dirty-release-branch", "medium", "当前工作区存在未提交或未跟踪改动，请确认 release 分支是否干净。"))
    return dedupe_warnings(warnings)


def render_release_branch_template(release_name: str, owner: str) -> str:
    return f"""# Release Branch Readiness: {release_name}

## Metadata

- Release: {release_name}
- Owner: {owner}

## Branch Status

- Clean working tree:
- Pending merges:
- Cherry-pick notes:

## Release Notes

- Included changes:
- Excluded changes:
- Risks / rollback notes:
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="发布分支就绪守卫")
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--fail-on", choices=("auto", "none", "high", "medium", "low"), default="auto")
    parser.add_argument("--report-md", default="")
    parser.add_argument("--report-json", default="")
    parser.add_argument("--release-name", default="release-to-fill")
    parser.add_argument("--owner", default="owner-to-fill")
    parser.add_argument("--output-md", default="")
    args = parser.parse_args()

    if args.output_md:
        content = render_release_branch_template(args.release_name, args.owner)
        write_report(args.output_md, content)
        print(content)
        return 0

    cwd = Path(args.cwd).resolve()
    changed_files = collect_changed_files(cwd, args.changed_file)
    threshold = compute_threshold(args.phase, args.fail_on)
    status_output = git_status_summary(cwd)
    warnings = build_warnings(status_output, changed_files)
    report = render_guard_report("Release Branch Readiness Checker", args.phase, cwd, threshold, [], warnings)
    print(report)
    write_report(args.report_md, report)
    write_json_report(
        args.report_json,
        standard_guard_payload(
            guard_name="release-branch-readiness-checker",
            phase=args.phase,
            cwd=cwd,
            threshold=threshold,
            changed_files=changed_files,
            warnings=warnings,
            extra={"gitStatus": status_output},
        ),
    )
    return 1 if any(warning_meets_threshold(item.severity, threshold) for item in warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
