#!/usr/bin/env python3
# Shared guard runtime helpers used by stage guard scripts for change collection, warning rendering, and report writing.
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


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


def _normalize_template_content(content: str | Iterable[str]) -> list[str]:
    if isinstance(content, str):
        return [content] if content else ["none"]
    lines = [str(item) for item in content if str(item)]
    return lines or ["none"]


def render_template_output(
    template_path_str: str,
    sections: list[tuple[str, str | Iterable[str]]],
    *,
    title: str = "",
) -> str:
    template_path = Path(template_path_str).resolve()
    template_body = template_path.read_text(encoding="utf-8").strip() if template_path.exists() else ""
    lines: list[str] = []
    if title:
        lines.extend([f"# {title}", ""])
    lines.append(f"_Template Source: {template_path}_")
    for heading, content in sections:
        lines.extend(["", f"## {heading}"])
        normalized = _normalize_template_content(content)
        if len(normalized) == 1 and normalized[0] == "none":
            lines.append("- none")
            continue
        for item in normalized:
            if "\n" in item:
                lines.append(item)
            else:
                lines.append(f"- {item}")
    if template_body:
        lines.extend(["", "## Template Reference", "", template_body])
    lines.append("")
    return "\n".join(lines)


def write_template_report(
    path_str: str,
    template_path_str: str,
    sections: list[tuple[str, str | Iterable[str]]],
    *,
    title: str = "",
) -> None:
    if not path_str:
        return
    content = render_template_output(template_path_str, sections, title=title)
    write_report(path_str, content)
