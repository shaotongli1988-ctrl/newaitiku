#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


CANONICAL_SUITES = ("unit", "integration", "regression", "e2e")
SUITE_TARGETS = {
    "unit": ("tests/unit",),
    "integration": ("tests/integration",),
    "regression": ("tests/regression", "tests/test_question_bank.py"),
    "e2e": ("tests/e2e",),
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run canonical test suites for the repository.")
    parser.add_argument("--suite", choices=(*CANONICAL_SUITES, "all", "auto"), default="all")
    parser.add_argument("--paths", nargs="*", default=[], help="Changed repository paths used when --suite auto is selected.")
    parser.add_argument("--no-quiet", action="store_true", help="Do not pass -q to pytest.")
    return parser.parse_args()


def normalize_path(root: Path, raw_path: str) -> str:
    path = Path(raw_path)
    if path.is_absolute():
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            return path.as_posix()
    return path.as_posix()


def classify_path(relative_path: str) -> set[str]:
    normalized = relative_path.replace("\\", "/").lstrip("./")
    if not normalized:
        return set()

    if normalized.startswith("tests/unit/"):
        return {"unit"}
    if normalized.startswith("tests/integration/"):
        return {"integration"}
    if normalized.startswith("tests/e2e/"):
        return {"e2e"}
    if normalized.startswith("tests/regression/") or normalized == "tests/test_question_bank.py":
        return {"regression"}

    if normalized.startswith(("tools/", "scripts/", ".github/")) or normalized in {"requirements.txt", "pytest.ini"}:
        return set(CANONICAL_SUITES)

    if normalized.startswith("frontend/"):
        return {"regression", "e2e"}

    if normalized.startswith("docs/") or normalized == "README.md":
        return {"regression"}

    if normalized == "data/schema.sql" or normalized.startswith(("app/db.py", "app/repository.py", "app/service.py", "app/main.py", "app/models.py")):
        return {"integration", "regression", "e2e"}

    if normalized.startswith(("app/auth.py", "app/contracts.py", "app/content_baseline.py", "app/exceptions.py")):
        return {"unit", "integration", "regression"}

    if normalized.startswith("app/"):
        return set(CANONICAL_SUITES)

    if normalized.startswith("tests/"):
        return set(CANONICAL_SUITES)

    return set(CANONICAL_SUITES)


def infer_suites(root: Path, raw_paths: list[str]) -> list[str]:
    suites: set[str] = set()
    for raw_path in raw_paths:
        suites.update(classify_path(normalize_path(root, raw_path)))
    return [suite for suite in CANONICAL_SUITES if suite in suites]


def existing_targets(root: Path, suite: str) -> list[str]:
    targets: list[str] = []
    for target in SUITE_TARGETS[suite]:
        if (root / target).exists():
            targets.append(target)
    return targets


def run_suite(root: Path, suite: str, quiet: bool) -> int:
    targets = existing_targets(root, suite)
    if not targets:
        print(f"[skip] {suite}: no matching test targets found.")
        return 0

    command = [sys.executable, "-m", "pytest"]
    if quiet:
        command.append("-q")
    command.extend(targets)

    print(f"[run] {suite}: {' '.join(targets)}")
    result = subprocess.run(command, cwd=str(root), check=False)
    return result.returncode


def main() -> int:
    args = parse_args()
    root = repo_root()
    quiet = not args.no_quiet

    if args.suite == "all":
        suites = list(CANONICAL_SUITES)
    elif args.suite == "auto":
        suites = infer_suites(root, args.paths)
        changed = [normalize_path(root, path) for path in args.paths]
        print(f"[auto] changed paths: {changed or ['<none>']}")
        print(f"[auto] selected suites: {suites or ['<none>']}")
    else:
        suites = [args.suite]

    if not suites:
        print("No test suites matched the current change set.")
        return 0

    for suite in suites:
        exit_code = run_suite(root, suite, quiet)
        if exit_code != 0:
            print(f"[fail] {suite} exited with code {exit_code}")
            return exit_code

    print(f"[pass] completed suites: {', '.join(suites)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
