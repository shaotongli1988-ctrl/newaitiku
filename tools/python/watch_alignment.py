#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


WATCH_PATHS = (
    "app",
    "frontend",
    "docs",
    "tests",
    "tools",
    "scripts",
    ".github",
    "README.md",
    "data/schema.sql",
    "requirements.txt",
    "pytest.ini",
)

IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "tools/logs",
    "tools/packages",
}

IGNORE_PATTERNS = (
    "*.db",
    "*.backup-*",
    "*.pyc",
    ".DS_Store",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass
class ChangeSet:
    added: list[str]
    modified: list[str]
    removed: list[str]

    def all_paths(self) -> list[str]:
        return sorted(set(self.added + self.modified + self.removed))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Watch repository files and trigger alignment checks automatically.")
    parser.add_argument("--debounce", type=float, default=2.0, help="Seconds to wait after the last change before running checks.")
    parser.add_argument("--interval", type=float, default=1.0, help="Polling interval in seconds.")
    parser.add_argument("--full", action="store_true", help="Run full alignment checks including pytest on each trigger.")
    return parser.parse_args()


def should_ignore(path: Path, root: Path) -> bool:
    relative = path.relative_to(root).as_posix()
    parts = relative.split("/")
    for ignored in IGNORE_DIRS:
        if ignored in relative or ignored in parts:
            return True
    return any(fnmatch.fnmatch(path.name, pattern) for pattern in IGNORE_PATTERNS)


def scan_paths(root: Path) -> dict[str, tuple[int, int]]:
    snapshot: dict[str, tuple[int, int]] = {}
    for watch_path in WATCH_PATHS:
        path = root / watch_path
        if not path.exists():
            continue
        if path.is_file():
            if not should_ignore(path, root):
                stat = path.stat()
                snapshot[path.relative_to(root).as_posix()] = (stat.st_mtime_ns, stat.st_size)
            continue
        for child in path.rglob("*"):
            if not child.is_file() or should_ignore(child, root):
                continue
            stat = child.stat()
            snapshot[child.relative_to(root).as_posix()] = (stat.st_mtime_ns, stat.st_size)
    return snapshot


def diff_paths(previous: dict[str, tuple[int, int]], current: dict[str, tuple[int, int]]) -> ChangeSet:
    previous_paths = set(previous)
    current_paths = set(current)
    added = sorted(current_paths - previous_paths)
    removed = sorted(previous_paths - current_paths)
    modified = sorted(path for path in previous_paths & current_paths if previous[path] != current[path])
    return ChangeSet(added=added, modified=modified, removed=removed)


def merge_paths(existing: list[str], incoming: list[str]) -> list[str]:
    return sorted(set(existing) | set(incoming))


def run_check(root: Path, full: bool, changed_paths: list[str]) -> int:
    command = [str(root / "tools/bin/check-alignment.sh"), "--phase", "batch", "--run-compile"]
    result = subprocess.run(command, cwd=str(root), check=False)
    if result.returncode != 0:
        return result.returncode

    test_command = [str(root / "tools/bin/run-tests.sh"), "--suite", "all" if full else "auto"]
    if not full and changed_paths:
        test_command.extend(["--paths", *changed_paths])
    result = subprocess.run(test_command, cwd=str(root), check=False)
    return result.returncode


def main() -> int:
    args = parse_args()
    root = repo_root()
    previous = scan_paths(root)

    print(f"Watching alignment paths in {root}")
    print(f"Debounce: {args.debounce:.1f}s, interval: {args.interval:.1f}s, full mode: {'on' if args.full else 'off'}")
    print("Waiting for added, modified, or removed files...")

    pending_since: float | None = None
    pending_paths: list[str] = []

    try:
        while True:
            current = scan_paths(root)
            changes = diff_paths(previous, current)
            changed_paths = changes.all_paths()
            if changed_paths:
                pending_since = time.time()
                pending_paths = merge_paths(pending_paths, changed_paths)
                print("")
                print(f"Detected {len(changed_paths)} file event(s):")
                for label, paths in (("added", changes.added), ("modified", changes.modified), ("removed", changes.removed)):
                    if not paths:
                        continue
                    for path in paths[:10]:
                        print(f"  - {label}: {path}")
                    if len(paths) > 10:
                        print(f"  - {label}: ... {len(paths) - 10} more")
                print("Waiting for changes to settle...")
                previous = current

            if pending_since is not None and (time.time() - pending_since) >= args.debounce:
                print("")
                print("Running automatic alignment check...")
                print(f"Triggered by: {pending_paths}")
                exit_code = run_check(root, args.full, pending_paths)
                status = "passed" if exit_code == 0 else f"failed with exit code {exit_code}"
                print(f"Automatic alignment check {status}.")
                print("Watching for the next change...")
                pending_since = None
                pending_paths = []

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("")
        print("Stopped alignment watcher.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
