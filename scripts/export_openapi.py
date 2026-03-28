from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import create_app


DEFAULT_OUTPUT_PATH = Path("docs/contracts/current/openapi.json")
DEFAULT_FULL_OUTPUT_PATH = Path("docs/contracts/current/api-contract-full.json")
NON_STRUCTURAL_OPENAPI_KEYS = {"description", "operationId", "summary", "title"}


def compact_openapi_schema(node, *, parent_key: str = ""):
    if isinstance(node, dict):
        if parent_key == "properties":
            return {
                key: compact_openapi_schema(value, parent_key=key)
                for key, value in node.items()
            }
        return {
            key: compact_openapi_schema(value, parent_key=key)
            for key, value in node.items()
            if key not in NON_STRUCTURAL_OPENAPI_KEYS
        }
    if isinstance(node, list):
        return [compact_openapi_schema(item, parent_key=parent_key) for item in node]
    return node


def _write_json(output_path: Path, payload: dict) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return output_path


def export_openapi(
    output_path: Path = DEFAULT_OUTPUT_PATH,
    *,
    full_output_path: Path = DEFAULT_FULL_OUTPUT_PATH,
) -> Path:
    app = create_app()
    full_openapi_schema = app.openapi()
    compact_openapi = compact_openapi_schema(full_openapi_schema)
    _write_json(full_output_path, full_openapi_schema)
    _write_json(output_path, compact_openapi)
    return output_path


if __name__ == "__main__":
    target_path = export_openapi(DEFAULT_OUTPUT_PATH, full_output_path=DEFAULT_FULL_OUTPUT_PATH)
    print(DEFAULT_FULL_OUTPUT_PATH)
    print(target_path)
