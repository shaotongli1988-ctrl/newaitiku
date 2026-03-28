#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

SCRIPT_PATH = Path(__file__).resolve()
SHARED_RUNTIME_SCRIPTS = SCRIPT_PATH.parents[2] / "shared-guard-runtime" / "scripts"
if str(SHARED_RUNTIME_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SHARED_RUNTIME_SCRIPTS))

from change_set import collect_changed_files, find_git_root, is_noise_path, parse_git_status, prepare_changed_files_for_subguards, read_text, run_cmd  # type: ignore
from guard_runtime import WarningItem, dedupe_warnings, render_guard_report, standard_guard_payload, summarize_warnings, warning_payload  # type: ignore
from report_writer import write_json_report, write_report  # type: ignore
from severity import SEVERITY_RANK, compute_threshold, warning_meets_threshold  # type: ignore
