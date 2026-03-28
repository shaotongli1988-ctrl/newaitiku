from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parents[1]
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

from app import db as db_module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="导入学习方法种子数据。")
    parser.add_argument(
        "--db-path",
        default=str(WORKSPACE_DIR / "data" / "question_bank.db"),
        help="目标数据库路径。",
    )
    parser.add_argument(
        "--seed-path",
        default=str(WORKSPACE_DIR / "data" / "learning_method_seed_v1.json"),
        help="学习方法 seed JSON 路径。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db_path).resolve()
    seed_path = Path(args.seed_path).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if not seed_path.exists():
        print(json.dumps({"ok": False, "error": f"seed 文件不存在: {seed_path}"}, ensure_ascii=False))
        return 1

    db_module.LEARNING_METHOD_SEED_PATH = seed_path
    with db_module.get_connection(db_path) as connection:
        connection.executescript(db_module.SCHEMA_PATH.read_text(encoding="utf-8"))
        before_total = int(
            connection.execute("SELECT COUNT(*) AS total FROM learning_method").fetchone()["total"]
        )
        db_module.seed_learning_methods(connection)
        connection.commit()
        after_total = int(
            connection.execute("SELECT COUNT(*) AS total FROM learning_method").fetchone()["total"]
        )
    print(
        json.dumps(
            {
                "ok": True,
                "dbPath": str(db_path),
                "seedPath": str(seed_path),
                "beforeTotal": before_total,
                "afterTotal": after_total,
                "inserted": max(0, after_total - before_total),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
