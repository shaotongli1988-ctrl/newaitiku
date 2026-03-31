#!/usr/bin/env python3
# Shared guard runtime helpers used by stage guard scripts for change collection, warning rendering, and report writing.
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class WarningItem:
    code: str
    severity: str
    message: str
    file: str = ""


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


def render_guard_report(name: str, phase: str, cwd: Path, threshold: str, changed_files: list[Path], warnings: list[WarningItem]) -> str:
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
