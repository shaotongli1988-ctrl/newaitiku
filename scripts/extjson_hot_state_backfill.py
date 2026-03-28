#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.db import DEFAULT_DB_PATH, get_connection
from app.repository import QuestionRepository, SYSTEM_USER_ID
from app.shared.codecs import load_json_object


def _build_readonly_repository(db_path: Path) -> QuestionRepository:
    repo = QuestionRepository.__new__(QuestionRepository)
    repo.db_path = Path(db_path)
    repo._knowledge_change_listener = None
    return repo


def _normalize_scalar(value: object) -> object:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, float):
        return round(value, 6)
    return value


def _normalize_json_text(raw: object) -> str:
    payload = load_json_object(raw if isinstance(raw, str) else {})
    if not isinstance(payload, dict):
        payload = {}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _canonicalize_row(row: dict[str, object]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, value in row.items():
        if key == "extJson":
            normalized[key] = _normalize_json_text(value)
            continue
        if key == "subjectIdsJson":
            payload = load_json_object(value if isinstance(value, str) else "[]")
            if not isinstance(payload, list):
                payload = []
            normalized[key] = json.dumps(payload, ensure_ascii=False, sort_keys=True)
            continue
        normalized[key] = _normalize_scalar(value)
    return normalized


def _load_formal_student_rows(db_path: Path) -> dict[tuple[str, str], dict[str, object]]:
    with get_connection(db_path) as connection:
        rows = connection.execute("SELECT * FROM student_question_record").fetchall()
    return {
        (str(row["studentUserId"]), str(row["questionId"])): _canonicalize_row(dict(row))
        for row in rows
    }


def _load_formal_paper_rows(db_path: Path) -> dict[str, dict[str, object]]:
    with get_connection(db_path) as connection:
        rows = connection.execute("SELECT * FROM paper_report").fetchall()
    return {str(row["reportId"]): _canonicalize_row(dict(row)) for row in rows}


def _load_formal_message_rows(db_path: Path) -> dict[str, dict[str, object]]:
    with get_connection(db_path) as connection:
        rows = connection.execute("SELECT * FROM message_send_history").fetchall()
    return {str(row["traceId"]): _canonicalize_row(dict(row)) for row in rows}


def _load_legacy_student_rows(repo: QuestionRepository, db_path: Path) -> dict[tuple[str, str], dict[str, object]]:
    result: dict[tuple[str, str], dict[str, object]] = {}
    with get_connection(db_path) as connection:
        rows = connection.execute('SELECT id, extJson FROM "user" WHERE id != ?', (SYSTEM_USER_ID,)).fetchall()
        for row in rows:
            student_user_id = str(row["id"])
            ext_json = load_json_object(str(row["extJson"]))
            records = ext_json.get("studentRecords", {})
            if not isinstance(records, dict):
                continue
            for question_id, stored in records.items():
                normalized = repo._normalize_student_question_record_row(student_user_id, str(question_id), stored)  # noqa: SLF001
                if normalized:
                    result[(student_user_id, str(question_id))] = _canonicalize_row(normalized)
    return result


def _load_legacy_paper_rows(repo: QuestionRepository, db_path: Path) -> dict[str, dict[str, object]]:
    with get_connection(db_path) as connection:
        row = connection.execute('SELECT extJson FROM "user" WHERE id = ?', (SYSTEM_USER_ID,)).fetchone()
    if not row:
        return {}
    ext_json = load_json_object(str(row["extJson"]))
    reports = ext_json.get("paperReports", [])
    if not isinstance(reports, list):
        return {}
    result: dict[str, dict[str, object]] = {}
    for report in reports:
        normalized = repo._normalize_paper_report_row(report)  # noqa: SLF001
        if normalized:
            result[str(normalized["reportId"])] = _canonicalize_row(normalized)
    return result


def _load_legacy_message_rows(repo: QuestionRepository, db_path: Path) -> dict[str, dict[str, object]]:
    with get_connection(db_path) as connection:
        row = connection.execute('SELECT extJson FROM "user" WHERE id = ?', (SYSTEM_USER_ID,)).fetchone()
    if not row:
        return {}
    ext_json = load_json_object(str(row["extJson"]))
    history = ext_json.get("messageSendHistory", [])
    if not isinstance(history, list):
        return {}
    result: dict[str, dict[str, object]] = {}
    for item in history:
        normalized = repo._normalize_message_send_history_row(item)  # noqa: SLF001
        if normalized:
            result[str(normalized["traceId"])] = _canonicalize_row(normalized)
    return result


def _diff_rows(
    legacy_rows: dict[Any, dict[str, object]],
    formal_rows: dict[Any, dict[str, object]],
) -> dict[str, Any]:
    missing_in_formal = sorted(str(key) for key in legacy_rows.keys() - formal_rows.keys())
    extra_in_formal = sorted(str(key) for key in formal_rows.keys() - legacy_rows.keys())
    mismatched_keys: list[str] = []
    for key in sorted(legacy_rows.keys() & formal_rows.keys(), key=str):
        if legacy_rows[key] != formal_rows[key]:
            mismatched_keys.append(str(key))
    return {
        "legacyCount": len(legacy_rows),
        "formalCount": len(formal_rows),
        "missingInFormal": missing_in_formal,
        "extraInFormal": extra_in_formal,
        "mismatched": mismatched_keys,
        "ok": not missing_in_formal and not extra_in_formal and not mismatched_keys,
    }


def audit_hot_state_consistency(db_path: Path) -> dict[str, Any]:
    repo = _build_readonly_repository(db_path)
    student_diff = _diff_rows(
        _load_legacy_student_rows(repo, db_path),
        _load_formal_student_rows(db_path),
    )
    paper_diff = _diff_rows(
        _load_legacy_paper_rows(repo, db_path),
        _load_formal_paper_rows(db_path),
    )
    message_diff = _diff_rows(
        _load_legacy_message_rows(repo, db_path),
        _load_formal_message_rows(db_path),
    )
    report = {
        "dbPath": str(db_path),
        "studentQuestionRecord": student_diff,
        "paperReport": paper_diff,
        "messageSendHistory": message_diff,
    }
    report["ok"] = all(
        bool(report[name]["ok"])
        for name in ("studentQuestionRecord", "paperReport", "messageSendHistory")
    )
    return report


def run_backfill(db_path: Path) -> dict[str, Any]:
    repo = QuestionRepository(db_path)
    with get_connection(db_path) as connection:
        rows = connection.execute('SELECT id, extJson FROM "user"').fetchall()
        for row in rows:
            user_id = str(row["id"])
            ext_json = load_json_object(str(row["extJson"]))
            if user_id == SYSTEM_USER_ID:
                continue
            records = ext_json.get("studentRecords", {})
            if not isinstance(records, dict):
                continue
            for question_id, stored in records.items():
                normalized = repo._normalize_student_question_record_row(user_id, str(question_id), stored)  # noqa: SLF001
                if normalized:
                    repo._upsert_student_question_record_row(connection, normalized)  # noqa: SLF001
        connection.commit()

    with get_connection(db_path) as connection:
        system_row = connection.execute('SELECT extJson FROM "user" WHERE id = ?', (SYSTEM_USER_ID,)).fetchone()
    if system_row:
        system_ext_json = load_json_object(str(system_row["extJson"]))
        reports = system_ext_json.get("paperReports", [])
        if isinstance(reports, list):
            for report in reports:
                normalized_report = repo._normalize_paper_report_row(report)  # noqa: SLF001
                if normalized_report:
                    repo.upsert_paper_report_payload(report)
        history_rows = system_ext_json.get("messageSendHistory", [])
        if isinstance(history_rows, list):
            for item in history_rows:
                normalized_history = repo._normalize_message_send_history_row(item)  # noqa: SLF001
                if normalized_history:
                    repo.upsert_message_send_history_payload(item)
    return audit_hot_state_consistency(db_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Offline legacy hot-state import/audit tool. Only use when migrating historical extJson snapshots into formal tables."
    )
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument(
        "--mode",
        choices=("audit", "backfill"),
        default="audit",
        help="audit: compare legacy extJson snapshots with formal tables; backfill: import historical legacy snapshots into formal tables before auditing.",
    )
    parser.add_argument("--report-json", default="", help="Optional path to write the audit report as JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db_path)
    if not db_path.exists():
        print(json.dumps({"ok": False, "error": f"数据库不存在: {db_path}"}, ensure_ascii=False, indent=2))
        return 2

    report = run_backfill(db_path) if args.mode == "backfill" else audit_hot_state_consistency(db_path)
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    print(payload)
    if args.report_json:
        Path(args.report_json).write_text(payload + "\n", encoding="utf-8")
    return 0 if bool(report.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
