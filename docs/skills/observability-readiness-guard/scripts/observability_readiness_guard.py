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


def is_runtime_observability_target(path: Path) -> bool:
    normalized = path.as_posix().lower()
    if any(token in normalized for token in ("/app/", "/frontend/src/api/", "/frontend/src/stores/", "/app/service")):
        if any(token in normalized for token in ("/docs/skills/", "/tests/", "/tools/logs/", "/tmp/")):
            return False
        return True
    return False


def build_warnings(changed_files: list[Path]) -> list[WarningItem]:
    warnings: list[WarningItem] = []
    for path in changed_files:
        if not is_runtime_observability_target(path):
            continue
        text = read_text(path).lower()
        if "log" not in text and "trace" not in text and "metric" not in text:
            warnings.append(WarningItem("observability-missing", "medium", "关键服务改动未明显体现日志/trace/metrics 证据。", str(path)))
    return dedupe_warnings(warnings)


def render_observability_template(service_name: str, owner: str, critical_paths: str) -> str:
    paths_text = critical_paths or "补充关键用户路径、后台任务链路和外部依赖调用。"
    return f"""# Observability Readiness: {service_name}

## Metadata

- Service: {service_name}
- Owner: {owner}

## Signals

- Logs:
- Metrics:
- Traces:
- Alerts:
- Dashboards:

## Critical Paths

{paths_text}

## Gaps

- Missing fields / tags:
- Missing alerts:
- Missing dashboards:
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="可观测性就绪守卫")
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--fail-on", choices=("auto", "none", "high", "medium", "low"), default="auto")
    parser.add_argument("--report-md", default="")
    parser.add_argument("--report-json", default="")
    parser.add_argument("--service-name", default="service-to-fill")
    parser.add_argument("--owner", default="owner-to-fill")
    parser.add_argument("--critical-paths", default="")
    parser.add_argument("--output-md", default="")
    args = parser.parse_args()

    if args.output_md:
        content = render_observability_template(args.service_name, args.owner, args.critical_paths)
        write_report(args.output_md, content)
        print(content)
        return 0

    cwd = Path(args.cwd).resolve()
    changed_files = collect_changed_files(cwd, args.changed_file)
    threshold = compute_threshold(args.phase, args.fail_on)
    warnings = build_warnings(changed_files)
    report = render_guard_report("Observability Readiness Guard", args.phase, cwd, threshold, changed_files, warnings)
    print(report)
    write_report(args.report_md, report)
    write_json_report(
        args.report_json,
        standard_guard_payload(
            guard_name="observability-readiness-guard",
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
