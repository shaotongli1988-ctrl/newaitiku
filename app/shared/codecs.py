from __future__ import annotations

# Observability note: codec changes should not break downstream log/trace/metric payload assumptions.
import hashlib
import json
from typing import Any

PASSWORD_HASH_NAMESPACE = "question-bank::"
PASSWORD_HASH_PREFIX = "sha256$"


def dump_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False)


def load_json_object(payload: object) -> dict[str, object]:
    if isinstance(payload, dict):
        return dict(payload)
    if not payload:
        return {}
    try:
        parsed = json.loads(str(payload))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def load_json_list(payload: object) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not payload:
        return []
    try:
        parsed = json.loads(str(payload))
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


def hash_password(password: str) -> str:
    digest = hashlib.sha256(f"{PASSWORD_HASH_NAMESPACE}{password}".encode("utf-8")).hexdigest()
    return f"{PASSWORD_HASH_PREFIX}{digest}"
