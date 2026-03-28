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


MANIFEST_NAMES = {
    "package.json": "node",
    "package-lock.json": "node",
    "pnpm-lock.yaml": "node",
    "yarn.lock": "node",
    "go.mod": "go",
    "go.sum": "go",
    "Cargo.toml": "rust",
    "Cargo.lock": "rust",
    "requirements.txt": "python",
    "poetry.lock": "python",
    "pyproject.toml": "python",
    "Pipfile": "python",
    "Pipfile.lock": "python",
    "Gemfile": "ruby",
    "Gemfile.lock": "ruby",
}

INFRA_TOKENS = ("dockerfile", "docker-compose", "helm", "terraform", ".tf", "k8s", "kubernetes", ".github/workflows")
DOC_TOKENS = ("/docs/", "adr", "architecture", "design", "decision", "readme", "release", "changelog")


def detect_ecosystem(path: Path) -> str | None:
    if path.name in MANIFEST_NAMES:
        return MANIFEST_NAMES[path.name]
    normalized = path.as_posix().lower()
    if "pom.xml" in normalized or "build.gradle" in normalized or "settings.gradle" in normalized:
        return "jvm"
    if any(token in normalized for token in ("vite.config", "webpack", "rollup", "tsconfig", "eslint", "babel")):
        return "frontend-tooling"
    if any(token in normalized for token in INFRA_TOKENS):
        return "infrastructure"
    return None


def build_warnings(changed_files: list[Path]) -> list[WarningItem]:
    warnings: list[WarningItem] = []
    docs_changed = any(any(token in path.as_posix().lower() for token in DOC_TOKENS) or path.suffix.lower() == ".md" for path in changed_files)
    ecosystems = {ecosystem for path in changed_files if (ecosystem := detect_ecosystem(path))}
    infra_files = [path for path in changed_files if detect_ecosystem(path) == "infrastructure"]

    manifest_files = [path for path in changed_files if path.name in MANIFEST_NAMES]
    lock_files = [path for path in manifest_files if "lock" in path.name.lower() or path.name.endswith(".sum")]

    if manifest_files and not docs_changed:
        warnings.append(WarningItem("stack-change-without-doc", "medium", "检测到依赖或技术栈清单变更，但未发现 ADR / README / 发布说明同步。"))
    if len(ecosystems - {"frontend-tooling"}) >= 2:
        warnings.append(WarningItem("multi-ecosystem-drift", "medium", f"本次改动同时触及多个技术域：{', '.join(sorted(ecosystems))}，需确认不是临时叠加技术栈。"))
    if infra_files and not docs_changed:
        warnings.append(WarningItem("infra-change-without-rationale", "high", "检测到基础设施或交付链路变更，但未发现方案说明或风险评审证据。"))
    if any(path.name == "package.json" for path in manifest_files) and not any(path.name in {"package-lock.json", "pnpm-lock.yaml", "yarn.lock"} for path in lock_files):
        warnings.append(WarningItem("node-manifest-without-lock", "low", "检测到 Node 依赖清单变更，但未看到锁文件同步变更。"))
    return dedupe_warnings(warnings)


def main() -> int:
    parser = argparse.ArgumentParser(description="技术栈漂移守卫")
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
    report = render_guard_report("Tech Stack Drift Guard", args.phase, cwd, threshold, changed_files, warnings)
    print(report)
    write_report(args.report_md, report)
    write_json_report(
        args.report_json,
        standard_guard_payload(
            guard_name="tech-stack-drift-guard",
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
