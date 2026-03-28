#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILLS_ROOT / "shared-guard-runtime" / "scripts"))

from guard_runtime import WarningItem, dedupe_warnings, render_guard_report, standard_guard_payload  # type: ignore
from report_writer import write_json_report, write_report  # type: ignore
from severity import compute_threshold, warning_meets_threshold  # type: ignore


def current_branch(cwd: Path) -> str:
    result = subprocess.run(["git", "branch", "--show-current"], cwd=str(cwd), capture_output=True, text=True, check=False)
    return result.stdout.strip()


def build_warnings(branch_name: str) -> list[WarningItem]:
    warnings: list[WarningItem] = []
    if branch_name in {"main", "master"}:
        warnings.append(WarningItem("on-main-branch", "high", "当前直接位于主分支，请确认是否违反分支保护规范。"))
    if branch_name and not re.match(r"^(develop|release/|feature/|fix/|hotfix/|codex/)", branch_name):
        warnings.append(WarningItem("branch-naming", "medium", f"分支命名 `{branch_name}` 不符合推荐规范。"))
    return dedupe_warnings(warnings)


def render_git_policy_template(branch_policy: str, owner: str) -> str:
    policy_text = branch_policy or "feature/* -> develop -> release/* -> main，并要求 PR 审核后合并。"
    return f"""# Git Flow Policy

## Metadata

- Owner: {owner}
- Branch policy: {policy_text}

## Branch Rules

- Main / master protection:
- Develop / release strategy:
- Feature / fix branch naming:

## Merge Rules

- PR / MR requirement:
- Review requirement:
- Release branch cut / merge-back rule:
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Git 流程规范守卫")
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--fail-on", choices=("auto", "none", "high", "medium", "low"), default="auto")
    parser.add_argument("--report-md", default="")
    parser.add_argument("--report-json", default="")
    parser.add_argument("--branch-policy", default="")
    parser.add_argument("--owner", default="owner-to-fill")
    parser.add_argument("--output-md", default="")
    args = parser.parse_args()

    if args.output_md:
        content = render_git_policy_template(args.branch_policy, args.owner)
        write_report(args.output_md, content)
        print(content)
        return 0

    cwd = Path(args.cwd).resolve()
    threshold = compute_threshold(args.phase, args.fail_on)
    branch_name = current_branch(cwd)
    warnings = build_warnings(branch_name)
    report = render_guard_report("Git Flow Enforcer", args.phase, cwd, threshold, [], warnings)
    print(report)
    write_report(args.report_md, report)
    write_json_report(
        args.report_json,
        standard_guard_payload(
            guard_name="git-flow-enforcer",
            phase=args.phase,
            cwd=cwd,
            threshold=threshold,
            changed_files=[],
            warnings=warnings,
            extra={"branch": branch_name},
        ),
    )
    return 1 if any(warning_meets_threshold(item.severity, threshold) for item in warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
