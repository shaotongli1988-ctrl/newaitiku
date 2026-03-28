#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.contracts import KnowledgeWriteRequest, QuestionCreateRequest
from app.db import DEFAULT_DB_PATH, get_connection


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
LOGGER = logging.getLogger("data_contract_cleanup")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def recursive_json_loads(data: Any) -> Any:
    """
    Deep decode for nested escaped JSON strings.
    Example: '"{\\"a\\": 1}"' -> {"a": 1}
    """
    if isinstance(data, str):
        try:
            return recursive_json_loads(json.loads(data))
        except (json.JSONDecodeError, TypeError):
            return data
    return data


def _first_level_json(raw_text: Any) -> Any:
    if not isinstance(raw_text, str):
        return None
    try:
        return json.loads(raw_text)
    except (json.JSONDecodeError, TypeError):
        return None


def _is_storage_canonical(raw_text: Any, expected_kind: type) -> bool:
    first = _first_level_json(raw_text)
    return isinstance(first, expected_kind)


def _safe_json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False)


def migrate_question_table(db_path: Path, dry_run: bool) -> dict[str, int]:
    LOGGER.info("开始审计 [question] 表...")
    counters = {"scanned": 0, "would_update": 0, "updated": 0, "failed": 0}

    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, knowledgeId, userId, stem, type, answer, status, optionsJson, extJson
            FROM question
            """
        ).fetchall()
        counters["scanned"] = len(rows)

        for row in rows:
            row_id = str(row["id"])
            try:
                raw_options = recursive_json_loads(row["optionsJson"])
                raw_ext = recursive_json_loads(row["extJson"])
                if not isinstance(raw_ext, dict):
                    raw_ext = {}

                legacy_payload = {
                    "id": row["id"],
                    "userId": row["userId"],
                    "knowledgeId": row["knowledgeId"],
                    "stem": row["stem"],
                    "type": row["type"],
                    "answer": row["answer"],
                    "status": row["status"],
                    "optionsJson": raw_options,
                    "extJson": raw_ext,
                }

                request_obj = QuestionCreateRequest.model_validate(legacy_payload)
                clean_payload = request_obj.to_service_payload()

                clean_options_obj = recursive_json_loads(clean_payload["optionsJson"])
                clean_ext_obj = recursive_json_loads(clean_payload["extJson"])
                old_first_options = _first_level_json(row["optionsJson"])
                old_first_ext = _first_level_json(row["extJson"])

                needs_update = (
                    (not _is_storage_canonical(row["optionsJson"], list))
                    or (not _is_storage_canonical(row["extJson"], dict))
                    or (old_first_options != clean_options_obj)
                    or (old_first_ext != clean_ext_obj)
                )
                if not needs_update:
                    continue

                counters["would_update"] += 1
                if dry_run:
                    continue

                conn.execute(
                    """
                    UPDATE question
                    SET optionsJson = ?, extJson = ?, updateTime = ?
                    WHERE id = ?
                    """,
                    (
                        _safe_json_dumps(clean_options_obj),
                        _safe_json_dumps(clean_ext_obj),
                        _now_iso(),
                        row_id,
                    ),
                )
                counters["updated"] += 1
            except Exception as exc:  # noqa: BLE001 - migration must continue
                counters["failed"] += 1
                LOGGER.error("[question] id=%s 清洗失败: %s", row_id, exc)

        if dry_run:
            conn.rollback()
        else:
            conn.commit()

    LOGGER.info(
        "[question] 扫描=%s, 待更新=%s, 已更新=%s, 失败=%s",
        counters["scanned"],
        counters["would_update"],
        counters["updated"],
        counters["failed"],
    )
    return counters


def migrate_knowledge_table(db_path: Path, dry_run: bool) -> dict[str, int]:
    LOGGER.info("开始审计 [knowledge] 表...")
    counters = {"scanned": 0, "would_update": 0, "updated": 0, "failed": 0}

    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, parentId, name, sort, status, extJson
            FROM knowledge
            """
        ).fetchall()
        counters["scanned"] = len(rows)

        for row in rows:
            row_id = str(row["id"])
            try:
                clean_ext = recursive_json_loads(row["extJson"])
                if not isinstance(clean_ext, dict):
                    clean_ext = {}

                KnowledgeWriteRequest.model_validate(
                    {
                        "id": row["id"],
                        "parentId": row["parentId"],
                        "name": row["name"],
                        "sort": row["sort"],
                        "status": row["status"],
                        "extJson": clean_ext,
                    }
                )

                old_first_ext = _first_level_json(row["extJson"])
                needs_update = (not _is_storage_canonical(row["extJson"], dict)) or (old_first_ext != clean_ext)
                if not needs_update:
                    continue

                counters["would_update"] += 1
                if dry_run:
                    continue

                conn.execute(
                    """
                    UPDATE knowledge
                    SET extJson = ?, updateTime = ?
                    WHERE id = ?
                    """,
                    (_safe_json_dumps(clean_ext), _now_iso(), row_id),
                )
                counters["updated"] += 1
            except Exception as exc:  # noqa: BLE001 - migration must continue
                counters["failed"] += 1
                LOGGER.error("[knowledge] id=%s 清洗失败: %s", row_id, exc)

        if dry_run:
            conn.rollback()
        else:
            conn.commit()

    LOGGER.info(
        "[knowledge] 扫描=%s, 待更新=%s, 已更新=%s, 失败=%s",
        counters["scanned"],
        counters["would_update"],
        counters["updated"],
        counters["failed"],
    )
    return counters


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean legacy JSON encoding drift for question/knowledge tables.")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("--dry-run", action="store_true", help="Read-only mode. No DB write will be committed.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db_path)
    if not db_path.exists():
        LOGGER.error("数据库不存在: %s", db_path)
        return 2

    LOGGER.info("--- 启动数据契约清洗 ---")
    LOGGER.info("数据库: %s", db_path)
    LOGGER.info("模式: %s", "dry-run(只读)" if args.dry_run else "write(回写)")

    question_summary = migrate_question_table(db_path, args.dry_run)
    knowledge_summary = migrate_knowledge_table(db_path, args.dry_run)

    LOGGER.info("--- 清洗结束 ---")
    LOGGER.info(
        "汇总: question(扫描=%s, 待更新=%s, 失败=%s), knowledge(扫描=%s, 待更新=%s, 失败=%s)",
        question_summary["scanned"],
        question_summary["would_update"],
        question_summary["failed"],
        knowledge_summary["scanned"],
        knowledge_summary["would_update"],
        knowledge_summary["failed"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
