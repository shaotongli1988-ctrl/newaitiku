#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILLS_ROOT / "shared-guard-runtime" / "scripts"))

from change_set import collect_changed_files  # type: ignore
from guard_runtime import (  # type: ignore
    WarningItem,
    dedupe_warnings,
    render_guard_report,
    standard_guard_payload,
    warning_payload,
)
from report_writer import write_json_report, write_report  # type: ignore
from severity import compute_threshold, warning_meets_threshold  # type: ignore


def build_warnings(changed_files: list[Path]) -> list[WarningItem]:
    warnings: list[WarningItem] = []
    normalized = [path.as_posix().lower() for path in changed_files]
    has_env = any(".env" in item or "config" in item for item in normalized)
    has_deploy = any(token in item for item in normalized for token in ("docker", "deploy", "helm", "k8s", "compose"))
    has_docs = any("/docs/" in item or item.endswith(".md") for item in normalized)

    if has_deploy and not has_env:
        warnings.append(WarningItem("deploy-without-config", "medium", "检测到部署相关改动，但未发现配置/环境变量核对证据。"))
    if has_env and not has_docs:
        warnings.append(WarningItem("config-diff-doc-missing", "medium", "检测到配置相关改动，但未发现配置差异说明文档。"))
    return dedupe_warnings(warnings)


def render_config_matrix_template(service_name: str, owner: str, environments: str) -> str:
    envs = environments or "dev / test / prod"
    return f"""# Deployment Config Matrix: {service_name}

## Metadata

- Service: {service_name}
- Owner: {owner}
- Environments: {envs}

## Environment Matrix

| Config Item | Dev | Test | Prod | Expected Source | Risk |
| --- | --- | --- | --- | --- | --- |
| API_BASE_URL |  |  |  | env/config center |  |

## Notes

- Domain / callback differences:
- Secret management:
- Rollback / fallback notes:
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="环境配置对齐守卫")
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--fail-on", choices=("auto", "none", "high", "medium", "low"), default="auto")
    parser.add_argument("--report-md", default="")
    parser.add_argument("--report-json", default="")
    parser.add_argument("--service-name", default="service-to-fill")
    parser.add_argument("--owner", default="owner-to-fill")
    parser.add_argument("--environments", default="")
    parser.add_argument("--output-md", default="")
    args = parser.parse_args()

    if args.output_md:
        content = render_config_matrix_template(args.service_name, args.owner, args.environments)
        write_report(args.output_md, content)
        print(content)
        return 0

    cwd = Path(args.cwd).resolve()
    changed_files = collect_changed_files(cwd, args.changed_file)
    threshold = compute_threshold(args.phase, args.fail_on)
    warnings = build_warnings(changed_files)
    report = render_guard_report("Deployment Config Alignment", args.phase, cwd, threshold, changed_files, warnings)
    print(report)
    write_report(args.report_md, report)
    write_json_report(
        args.report_json,
        standard_guard_payload(
            guard_name="deployment-config-alignment",
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
