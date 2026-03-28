#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
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


SECRET_PATTERNS = (
    r"password\s*[:=]\s*['\"][^'\"]{4,}['\"]",
    r"secret\s*[:=]\s*['\"][^'\"]{4,}['\"]",
    r"token\s*[:=]\s*['\"][^'\"]{8,}['\"]",
    r"apikey\s*[:=]\s*['\"][^'\"]{8,}['\"]",
)


def is_runtime_security_target(path: Path) -> bool:
    normalized = path.as_posix().lower()
    if any(token in normalized for token in ("/app/", "/frontend/src/", "/frontend/public/", "/static/", "/templates/")):
        if any(token in normalized for token in ("/docs/skills/", "/tests/", "/tools/logs/", "/tmp/")):
            return False
        return True
    return False


def build_warnings(changed_files: list[Path]) -> list[WarningItem]:
    warnings: list[WarningItem] = []
    for path in changed_files:
        if not is_runtime_security_target(path):
            continue
        text = read_text(path)
        lowered = text.lower()
        if any(re.search(pattern, lowered) for pattern in SECRET_PATTERNS):
            warnings.append(WarningItem("secret-hardcoded", "high", "检测到疑似敏感信息硬编码。", str(path)))
        if "select *" in lowered:
            warnings.append(WarningItem("select-star", "medium", "检测到 SELECT *，请确认是否存在越权/性能风险。", str(path)))
        if re.search(r"\.innerhtml\s*=", lowered):
            warnings.append(WarningItem("xss-sink", "medium", "检测到 innerHTML 直写，请确认 XSS 防护。", str(path)))
    return dedupe_warnings(warnings)


def main() -> int:
    parser = argparse.ArgumentParser(description="应用安全基线守卫")
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--fail-on", choices=("auto", "none", "high", "medium", "low"), default="auto")
    parser.add_argument("--report-md", default="")
    parser.add_argument("--report-json", default="")
    args = parser.parse_args()

    cwd = Path(args.cwd).resolve()
    changed_files = collect_changed_files(cwd, args.changed_file)
    threshold = compute_threshold(args.phase, args.fail_on)
    warnings = build_warnings(changed_files)
    report = render_guard_report("App Security Baseline Guard", args.phase, cwd, threshold, changed_files, warnings)
    print(report)
    write_report(args.report_md, report)
    write_json_report(
        args.report_json,
        standard_guard_payload(
            guard_name="app-security-baseline-guard",
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
