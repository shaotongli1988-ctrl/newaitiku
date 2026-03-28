#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}
NOISE_DIR_PARTS = {
    ".codex-runtime",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".screenshots",
    ".shared-deps",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "tmp",
}
NOISE_SUFFIXES = {
    ".log",
    ".pid",
    ".tmp",
    ".cache",
    ".bak",
    ".swp",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".lock",
    ".dylib",
    ".so",
    ".pyc",
}
NOISE_PATH_PATTERNS = (
    "/tmp/development-readiness-",
    "/tmp/software-delivery-",
    "/tmp/release-",
    "/.shared-deps/",
)


@dataclass
class WarningItem:
    code: str
    severity: str
    message: str
    file: str = ""


def run_cmd(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, check=False)


def find_git_root(cwd: Path) -> Path | None:
    result = run_cmd(["git", "rev-parse", "--show-toplevel"], cwd)
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def parse_git_status(root: Path) -> list[Path]:
    result = run_cmd(["git", "status", "--porcelain", "--untracked-files=all"], root)
    if result.returncode != 0:
        return []
    changed: list[Path] = []
    for raw_line in result.stdout.splitlines():
        if not raw_line:
            continue
        line = raw_line[3:] if len(raw_line) > 3 else raw_line
        if " -> " in line:
            line = line.split(" -> ", 1)[1]
        changed.append((root / line).resolve())
    return changed


def is_noise_path(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    if any(part in parts for part in NOISE_DIR_PARTS):
        return True
    normalized = path.as_posix().lower()
    if any(pattern in normalized for pattern in NOISE_PATH_PATTERNS):
        return True
    if path.suffix.lower() in NOISE_SUFFIXES:
        return True
    if path.name.startswith("tmp_test") or path.name.endswith("_test.db"):
        return True
    return False


def read_text(path: Path, limit: int = 120_000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def compute_threshold(phase: str, fail_on: str) -> str:
    if fail_on != "auto":
        return fail_on
    return "none" if phase == "start" else "high"


def warning_meets_threshold(severity: str, threshold: str) -> bool:
    if threshold == "none":
        return False
    return SEVERITY_RANK[severity] <= SEVERITY_RANK[threshold]


def dedupe_warnings(items: list[WarningItem]) -> list[WarningItem]:
    seen: set[tuple[str, str, str, str]] = set()
    result: list[WarningItem] = []
    for item in items:
        key = (item.code, item.severity, item.message, item.file)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def summarize_warnings(items: list[WarningItem]) -> dict[str, int]:
    return {
        "high": sum(1 for item in items if item.severity == "high"),
        "medium": sum(1 for item in items if item.severity == "medium"),
        "low": sum(1 for item in items if item.severity == "low"),
        "total": len(items),
    }


def collect_changed_files(cwd: Path, changed_file_args: list[str]) -> list[Path]:
    raw_changed_files = [Path(item).resolve() for item in changed_file_args]
    if not raw_changed_files:
        git_root = find_git_root(cwd)
        if git_root:
            raw_changed_files = parse_git_status(git_root)
    return [path for path in raw_changed_files if not is_noise_path(path)]


def render_guard_report(
    name: str,
    phase: str,
    cwd: Path,
    threshold: str,
    changed_files: list[Path],
    warnings: list[WarningItem],
) -> str:
    summary = summarize_warnings(warnings)
    lines = [
        f"{name}: {phase}",
        f"Working directory: {cwd}",
        f"Changed files: {len(changed_files)}",
        f"Fail threshold: {threshold}",
        f"Summary: {summary['high']} high, {summary['medium']} medium, {summary['low']} low",
    ]
    for path in changed_files[:20]:
        lines.append(f"  - {path}")
    if warnings:
        lines.append("Warnings:")
        for item in warnings:
            suffix = f" [{item.file}]" if item.file else ""
            lines.append(f"  - [{item.severity.upper()}] {item.message}{suffix}")
    else:
        lines.append("Warnings: none")
    return "\n".join(lines)


def write_report(path_str: str, content: str) -> None:
    if not path_str:
        return
    path = Path(path_str).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json_report(path_str: str, payload: dict) -> None:
    if not path_str:
        return
    write_report(path_str, json.dumps(payload, ensure_ascii=False, indent=2))


def warning_payload(items: list[WarningItem]) -> list[dict]:
    return [asdict(item) for item in items]


def standard_guard_payload(
    *,
    guard_name: str,
    phase: str,
    cwd: Path,
    threshold: str,
    changed_files: list[Path],
    warnings: list[WarningItem],
    extra: dict | None = None,
) -> dict:
    payload = {
        "guard": guard_name,
        "phase": phase,
        "cwd": str(cwd),
        "failThreshold": threshold,
        "changedFiles": [str(path) for path in changed_files],
        "summary": summarize_warnings(warnings),
        "warnings": warning_payload(warnings),
    }
    if extra:
        payload["extra"] = extra
    return payload
