#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SKILL_GUARD = (
    Path.home()
    / ".codex"
    / "skills"
    / "fullstack-unified-development-standards"
    / "scripts"
    / "unified_delivery_guard.py"
)

DEFAULT_API_OPENAPI = ("docs/contracts/current/openapi.json",)
DEFAULT_API_PRODUCERS = (
    "app/contracts.py",
    "app/models.py",
    "app/main.py",
)
DEFAULT_API_CONSUMERS = ("frontend/src/api",)
DEFAULT_CHANGED_SCOPE_PREFIXES = (
    "docs/contracts/",
)
DEFAULT_CHANGED_SCOPE_FILES = (
    "README.md",
    "docs/alignment-self-check.md",
    "scripts/export_openapi.py",
    "app/contracts.py",
    "app/models.py",
    "app/main.py",
    "frontend/src/api/contracts.ts",
    "frontend/src/api/contractsAlignment.test.js",
    "frontend/src/api/questionBank.test.js",
)


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="Run the project-scoped unified delivery guard with stable API contract defaults."
    )
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=str(ROOT_DIR))
    parser.add_argument("--fail-on", choices=("auto", "none", "high", "medium", "low"), default="auto")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--report-md", default="")
    parser.add_argument("--report-json", default="")
    parser.add_argument("--api-openapi", action="append", default=[])
    parser.add_argument("--api-producer", action="append", default=[])
    parser.add_argument("--api-consumer", action="append", default=[])
    parser.add_argument("--api-alias-map", default="")
    parser.add_argument("--api-strip-prefix", action="append", default=[])
    parser.add_argument("--api-max-files", type=int, default=6000)
    parser.add_argument("--api-report-md", default="")
    parser.add_argument("--api-report-json", default="")
    return parser.parse_known_args()


def run_cmd(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, check=False)


def find_git_root(cwd: Path) -> Path:
    result = run_cmd(["git", "rev-parse", "--show-toplevel"], cwd)
    if result.returncode != 0 or not result.stdout.strip():
        return cwd.resolve()
    return Path(result.stdout.strip()).resolve()


def parse_git_changed_files(root: Path) -> list[Path]:
    result = run_cmd(["git", "-c", "core.quotepath=false", "status", "--porcelain", "--untracked-files=all"], root)
    if result.returncode != 0:
        return []
    changed_files: list[Path] = []
    for raw_line in result.stdout.splitlines():
        if not raw_line:
            continue
        payload = raw_line[3:] if len(raw_line) > 3 else raw_line
        if " -> " in payload:
            payload = payload.split(" -> ", 1)[1]
        changed_files.append((root / payload).resolve())
    return changed_files


def is_in_scope(path: Path, root: Path) -> bool:
    try:
        relative = path.resolve().relative_to(root).as_posix()
    except ValueError:
        return False
    return relative in DEFAULT_CHANGED_SCOPE_FILES or any(
        relative.startswith(prefix) for prefix in DEFAULT_CHANGED_SCOPE_PREFIXES
    )


def expand_scope_targets(root: Path, targets: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw_target in targets:
        target = (root / raw_target).resolve()
        if target.is_file():
            files.append(target)
            continue
        if target.is_dir():
            files.extend(path.resolve() for path in target.rglob("*") if path.is_file())
    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in files:
        if path in seen:
            continue
        seen.add(path)
        deduped.append(path)
    return deduped


def resolve_changed_files(root: Path, explicit_changed_files: list[str], fallback_targets: list[str]) -> list[Path]:
    if explicit_changed_files:
        return [Path(item).resolve() for item in explicit_changed_files]

    scoped_git_changes = [path for path in parse_git_changed_files(root) if is_in_scope(path, root)]
    if scoped_git_changes:
        return scoped_git_changes

    return expand_scope_targets(root, fallback_targets)


def main() -> int:
    args, passthrough = parse_args()
    cwd = Path(args.cwd).resolve()
    git_root = find_git_root(cwd)

    api_openapi = args.api_openapi or list(DEFAULT_API_OPENAPI)
    api_producers = args.api_producer or list(DEFAULT_API_PRODUCERS)
    api_consumers = args.api_consumer or list(DEFAULT_API_CONSUMERS)
    changed_files = resolve_changed_files(
        git_root,
        args.changed_file,
        list(api_openapi) + list(api_producers) + list(api_consumers),
    )

    cmd = [
        sys.executable,
        str(SKILL_GUARD),
        "--phase",
        args.phase,
        "--cwd",
        str(cwd),
        "--fail-on",
        args.fail_on,
        "--api-max-files",
        str(args.api_max_files),
    ]
    if args.task:
        cmd.extend(["--task", args.task])
    if args.report_md:
        cmd.extend(["--report-md", args.report_md])
    if args.report_json:
        cmd.extend(["--report-json", args.report_json])
    if args.api_alias_map:
        cmd.extend(["--api-alias-map", args.api_alias_map])
    if args.api_report_md:
        cmd.extend(["--api-report-md", args.api_report_md])
    if args.api_report_json:
        cmd.extend(["--api-report-json", args.api_report_json])
    for changed_file in changed_files:
        cmd.extend(["--changed-file", str(changed_file)])
    for item in api_openapi:
        cmd.extend(["--api-openapi", item])
    for item in api_producers:
        cmd.extend(["--api-producer", item])
    for item in api_consumers:
        cmd.extend(["--api-consumer", item])
    for item in args.api_strip_prefix:
        cmd.extend(["--api-strip-prefix", item])
    cmd.extend(passthrough)

    if not SKILL_GUARD.exists():
        print(f"Scoped guard script not found: {SKILL_GUARD}", file=sys.stderr)
        return 2

    result = subprocess.run(cmd, cwd=str(ROOT_DIR), check=False)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
