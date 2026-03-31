#!/usr/bin/env python3
# Shared guard runtime helpers used by stage guard scripts for change collection, warning rendering, and report writing.
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import re
import subprocess
from pathlib import Path


NOISE_DIR_PARTS = {
    ".codex-runtime",
    ".pdfdeps",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".screenshots",
    ".shared-deps",
    ".venv",
    "venv",
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
    ".wal",
    ".shm",
    ".dylib",
    ".so",
    ".pyc",
    ".pdf",
    ".ttf",
    ".otf",
    ".pfb",
    ".afm",
    ".sfd",
}

NOISE_PATH_PATTERNS = (
    "/.pdfdeps/",
    "/tmp/reuse-blueprints/",
    "/tmp/skill-sync/",
    "/tmp/component-reuse-",
    "/tmp/software-delivery-",
    "/tmp/release-",
    "/tmp/reuse-patch-plan",
    "/.shared-deps/",
)

HIGH_SIGNAL_PATH_PATTERNS = (
    "/frontend/src/",
    "/app/",
    "/tests/",
    "/docs/release/",
    "/docs/contracts/",
    "/scripts/",
    "/readme",
    "/readme.md",
    "/package.json",
    "/package-lock.json",
    "/pnpm-lock.yaml",
    "/yarn.lock",
    "/requirements",
    "/pytest.ini",
    "/vite.config",
    "/vitest.config",
)

LOW_SIGNAL_PATH_PATTERNS = (
    "/data/",
    "/docs/skills/",
    "/docs/screenshots/",
    "/docs/student-step-",
    "/docs/teacher-step-",
    "/2026",
)

FOCUSABLE_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".vue",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".md",
    ".sql",
}
FOCUSABLE_FILENAMES = {
    "dockerfile",
    "makefile",
    "readme",
    "readme.md",
}

AUTO_FOCUS_MIN_CHANGED_FILES = 300
AUTO_FOCUS_MIN_UNTRACKED_RATIO = 0.9
AUTO_FOCUS_RECENT_SCAN_LIMIT = 80
AUTO_FOCUS_MAX_FILES = 48
AUTO_FOCUS_TOPIC_LIMIT = 4
AUTO_FOCUS_MIN_TOPIC_OCCURRENCES = 2
AUTO_FOCUS_FALLBACK_MAX_FILES = 24

TOKEN_STOPWORDS = {
    "admin",
    "analytics",
    "api",
    "app",
    "auth",
    "backend",
    "bank",
    "build",
    "cache",
    "checker",
    "client",
    "component",
    "components",
    "config",
    "contracts",
    "core",
    "data",
    "delivery",
    "development",
    "docs",
    "document",
    "drawer",
    "echarts",
    "frontend",
    "flow",
    "guard",
    "graph",
    "helpers",
    "implementation",
    "index",
    "internal",
    "knowledge",
    "layout",
    "main",
    "mindmap",
    "module",
    "modules",
    "meta",
    "notes",
    "openapi",
    "page",
    "pages",
    "plan",
    "practice",
    "question",
    "questions",
    "release",
    "remediation",
    "repository",
    "router",
    "routes",
    "runtime",
    "schema",
    "script",
    "scripts",
    "service",
    "services",
    "skill",
    "skills",
    "src",
    "state",
    "student",
    "subject",
    "system",
    "tasks",
    "teacher",
    "test",
    "tests",
    "types",
    "unified",
    "utils",
    "view",
    "views",
    "acceptance",
    "analysis",
    "composables",
    "copy",
    "drift",
    "exam",
    "home",
    "model",
    "navigation",
}


@dataclass(frozen=True)
class GitStatusEntry:
    status: str
    path: Path


def run_cmd(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, check=False)


def find_git_root(cwd: Path) -> Path | None:
    result = run_cmd(["git", "rev-parse", "--show-toplevel"], cwd)
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip()).resolve()


def parse_git_status_entries(root: Path) -> list[GitStatusEntry]:
    result = run_cmd(["git", "-c", "core.quotepath=false", "status", "--porcelain", "--untracked-files=all"], root)
    if result.returncode != 0:
        return []
    entries: list[GitStatusEntry] = []
    for raw_line in result.stdout.splitlines():
        if not raw_line:
            continue
        status = raw_line[:2]
        line = raw_line[3:] if len(raw_line) > 3 else raw_line
        if " -> " in line:
            line = line.split(" -> ", 1)[1]
        entries.append(GitStatusEntry(status=status, path=(root / line).resolve()))
    return entries


def parse_git_status(root: Path) -> list[Path]:
    return [entry.path for entry in parse_git_status_entries(root)]


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


def is_within_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def path_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def is_focusable_text_path(path: Path) -> bool:
    if path.suffix.lower() in FOCUSABLE_SUFFIXES:
        return True
    return path.name.lower() in FOCUSABLE_FILENAMES


def split_path_tokens(path: Path, root: Path) -> set[str]:
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError:
        relative = path.name
    relative = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", relative)
    tokens = re.split(r"[^A-Za-z0-9]+", relative)
    return {
        token.lower()
        for token in tokens
        if len(token) >= 4 and not token.isdigit() and token.lower() not in TOKEN_STOPWORDS
    }


def collect_changed_files(cwd: Path, changed_file_args: list[str]) -> list[Path]:
    root = find_git_root(cwd) or cwd.resolve()
    if changed_file_args:
        raw_changed_files = [Path(item).resolve() for item in changed_file_args]
        return [
            path
            for path in raw_changed_files
            if is_within_root(path, root) and not is_noise_path(path)
        ]

    entries = parse_git_status_entries(root)
    filtered_entries: list[GitStatusEntry] = []
    seen: set[Path] = set()
    for entry in entries:
        normalized = entry.path.resolve()
        if normalized in seen:
            continue
        seen.add(normalized)
        if not is_within_root(normalized, root):
            continue
        if is_noise_path(normalized):
            continue
        filtered_entries.append(GitStatusEntry(status=entry.status, path=normalized))

    if should_focus_current_batch(filtered_entries):
        focused_paths = focus_current_batch(filtered_entries, root)
        if focused_paths:
            return focused_paths
    return [entry.path for entry in filtered_entries]


def should_focus_current_batch(entries: list[GitStatusEntry]) -> bool:
    if len(entries) < AUTO_FOCUS_MIN_CHANGED_FILES:
        return False
    status_counter = Counter(entry.status for entry in entries)
    untracked_ratio = status_counter.get("??", 0) / len(entries)
    return untracked_ratio >= AUTO_FOCUS_MIN_UNTRACKED_RATIO


def focus_current_batch(entries: list[GitStatusEntry], root: Path) -> list[Path]:
    candidates = [entry.path for entry in entries if is_focusable_text_path(entry.path)]
    if not candidates:
        candidates = [entry.path for entry in entries]
    if not candidates:
        return []

    recent_candidates = sorted(candidates, key=path_mtime, reverse=True)[:AUTO_FOCUS_RECENT_SCAN_LIMIT]
    token_counter: Counter[str] = Counter()
    path_tokens: dict[Path, set[str]] = {}
    for path in recent_candidates:
        tokens = split_path_tokens(path, root)
        path_tokens[path] = tokens
        token_counter.update(tokens)

    topical_tokens = [
        token
        for token, count in token_counter.most_common()
        if count >= AUTO_FOCUS_MIN_TOPIC_OCCURRENCES
    ][:AUTO_FOCUS_TOPIC_LIMIT]
    topical_paths = [
        path
        for path in recent_candidates
        if any(token in path_tokens.get(path, set()) for token in topical_tokens)
    ]
    if len(topical_paths) >= 3:
        return sorted(topical_paths, key=changed_file_priority)[:AUTO_FOCUS_MAX_FILES]
    return sorted(recent_candidates, key=changed_file_priority)[:AUTO_FOCUS_FALLBACK_MAX_FILES]


def changed_file_priority(path: Path) -> tuple[int, float, int, str]:
    normalized = path.as_posix().lower()
    score = 100

    if any(pattern in normalized for pattern in HIGH_SIGNAL_PATH_PATTERNS):
        score -= 70
    if any(pattern in normalized for pattern in LOW_SIGNAL_PATH_PATTERNS):
        score += 25
    if "/src/" in normalized or normalized.endswith((".py", ".js", ".ts", ".vue")):
        score -= 20
    if "/tests/" in normalized or ".test." in normalized or ".spec." in normalized:
        score -= 15
    if normalized.endswith(".md"):
        score -= 10

    modified_at = -path_mtime(path)
    return (score, modified_at, len(normalized), normalized)


def prepare_changed_files_for_subguards(
    changed_files: list[Path],
    cwd: Path,
    max_files: int = 200,
    placeholder_name: str = ".shared_guard_empty_change_set",
) -> tuple[list[Path], list[str]]:
    warnings: list[str] = []
    if not changed_files:
        return [cwd / placeholder_name], warnings
    prioritized_files = sorted(changed_files, key=changed_file_priority)
    if len(prioritized_files) > max_files:
        warnings.append(f"Sub-guard changed-file list was truncated to {max_files} items to keep execution stable.")
    return prioritized_files[:max_files], warnings
