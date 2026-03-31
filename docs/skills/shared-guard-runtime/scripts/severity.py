#!/usr/bin/env python3
# Shared guard runtime helpers used by stage guard scripts for change collection, warning rendering, and report writing.
from __future__ import annotations


SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}


def compute_threshold(phase: str, fail_on: str) -> str:
    if fail_on != "auto":
        return fail_on
    return "none" if phase == "start" else "medium"


def warning_meets_threshold(severity: str, threshold: str) -> bool:
    if threshold == "none":
        return False
    return SEVERITY_RANK[severity] <= SEVERITY_RANK[threshold]
