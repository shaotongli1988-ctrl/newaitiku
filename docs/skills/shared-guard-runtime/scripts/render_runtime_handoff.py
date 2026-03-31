#!/usr/bin/env python3
# Shared guard runtime helpers used by stage guard scripts for change collection, warning rendering, and report writing.
from __future__ import annotations

import argparse
from pathlib import Path

from report_writer import write_template_report


SCRIPT_PATH = Path(__file__).resolve()
TEMPLATE_PATH = SCRIPT_PATH.parent.parent / "references" / "runtime-handoff-template.md"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a shared-guard-runtime handoff markdown file")
    parser.add_argument("--module-name", required=True, help="Runtime module or helper name")
    parser.add_argument("--used-by", action="append", default=[], help="Skill that depends on this runtime helper")
    parser.add_argument("--input", action="append", default=[], help="Input contract line")
    parser.add_argument("--output", action="append", default=[], help="Output contract line")
    parser.add_argument("--compatibility-note", action="append", default=[], help="Compatibility note")
    parser.add_argument("--failure-mode", action="append", default=[], help="Known failure mode")
    parser.add_argument("--output-md", required=True, help="Markdown output path")
    return parser.parse_args(argv)


def render_sections(args: argparse.Namespace) -> list[tuple[str, list[str]]]:
    return [
        (
            "Runtime Surface",
            [
                f"Module / helper: {args.module_name}",
                "Owner: platform",
                f"Used by skills: {', '.join(args.used_by) or 'none'}",
            ],
        ),
        (
            "Contract",
            [
                f"Inputs: {', '.join(args.input) or 'none'}",
                f"Outputs: {', '.join(args.output) or 'none'}",
                "Severity behavior: shared severity ranking and fail-threshold logic",
                "Report writer behavior: writes markdown and json artifacts to requested paths",
            ],
        ),
        (
            "Compatibility",
            [
                f"Backward-compatible expectations: {', '.join(args.compatibility_note) or 'keep current consumer contracts stable'}",
                "Known assumptions: downstream guards use the shared runtime path layout",
                "Required regression tests: shared runtime + downstream core-chain tests",
            ],
        ),
        (
            "Operational Notes",
            [
                f"Common failure modes: {', '.join(args.failure_mode) or 'missing changed-file context, bad report paths'}",
                "Upgrade guidance: update runtime helper and regenerate dependent outputs together",
                "Downstream consumers to verify: three-stage, readiness, implementation, delivery",
            ],
        ),
    ]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    write_template_report(
        args.output_md,
        str(TEMPLATE_PATH),
        render_sections(args),
        title="Shared Guard Runtime Output",
    )
    print(f"Wrote runtime handoff output to {Path(args.output_md).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
