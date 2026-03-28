#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.db import DEFAULT_DB_PATH, get_connection


LOGGER = logging.getLogger("knowledge_graph_data_generator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_path(path: str) -> str:
    text = str(path or "").strip()
    if not text:
        return "/"
    if text.startswith("http://") or text.startswith("https://"):
        return text
    return text if text.startswith("/") else f"/{text}"


def _build_url(base_url: str, path: str) -> str:
    normalized_base = str(base_url or "").strip().rstrip("/")
    normalized_path = _normalize_path(path)
    if normalized_path.startswith("http://") or normalized_path.startswith("https://"):
        return normalized_path
    return f"{normalized_base}{normalized_path}"


def generate_knowledge_records(
    count: int,
    run_id: str,
    rng: random.Random,
    max_prereq_per_node: int,
    prerequisite_probability: float,
) -> tuple[list[dict[str, Any]], int]:
    if count < 2:
        raise ValueError("count must be >= 2")
    if max_prereq_per_node < 0:
        raise ValueError("max_prereq_per_node must be >= 0")

    inserted_ids: list[str] = []
    rows: list[dict[str, Any]] = []
    prerequisite_edge_count = 0
    timestamp = _now_iso()

    for index in range(count):
        node_id = f"knowledge-graph-seed-{run_id}-{index + 1:03d}"
        parent_id = None if index == 0 else rng.choice(inserted_ids)

        candidate_prerequisites = [item for item in inserted_ids if item != parent_id]
        prerequisites: list[str] = []
        if candidate_prerequisites and max_prereq_per_node > 0 and rng.random() < prerequisite_probability:
            pick_count = rng.randint(1, min(max_prereq_per_node, len(candidate_prerequisites)))
            prerequisites = sorted(rng.sample(candidate_prerequisites, pick_count))

        prerequisite_edge_count += len(prerequisites)
        ext_json = {
            "level": min(3, 1 + (index // max(1, (count // 3)))),
            "subjectId": "subject-graph-seed",
            "seedRunId": run_id,
            "prerequisites": prerequisites,
        }
        rows.append(
            {
                "id": node_id,
                "parentId": parent_id,
                "name": f"Graph Seed Node {index + 1:03d}",
                "sort": (index + 1) * 10,
                "status": "ENABLED",
                "extJson": json.dumps(ext_json, ensure_ascii=False),
                "createTime": timestamp,
                "updateTime": timestamp,
            }
        )
        inserted_ids.append(node_id)

    return rows, prerequisite_edge_count


def insert_knowledge_records(rows: list[dict[str, Any]], db_path: Path) -> None:
    with get_connection(db_path) as connection:
        connection.executemany(
            """
            INSERT INTO knowledge (id, parentId, name, sort, status, extJson, createTime, updateTime)
            VALUES (:id, :parentId, :name, :sort, :status, :extJson, :createTime, :updateTime)
            """,
            rows,
        )
        connection.commit()


def cleanup_records(rows: list[dict[str, Any]], db_path: Path) -> None:
    if not rows:
        return
    with get_connection(db_path) as connection:
        for row in reversed(rows):
            connection.execute("DELETE FROM knowledge WHERE id = ?", (row["id"],))
        connection.commit()


def fetch_graph_payload(
    base_url: str,
    graph_path: str,
    headers: dict[str, str],
    timeout_sec: float,
) -> dict[str, Any]:
    url = _build_url(base_url, graph_path)
    request = urllib.request.Request(url=url, method="GET")
    for key, value in headers.items():
        request.add_header(key, value)

    with urllib.request.urlopen(request, timeout=timeout_sec) as response:  # noqa: S310
        body = response.read().decode("utf-8")
    return json.loads(body)


def fetch_graph_with_fallback(
    base_url: str,
    graph_path: str,
    fallback_graph_path: str,
    headers: dict[str, str],
    timeout_sec: float,
) -> tuple[dict[str, Any], str]:
    tried_paths = [graph_path]
    if fallback_graph_path and fallback_graph_path not in tried_paths:
        tried_paths.append(fallback_graph_path)

    last_error: Exception | None = None
    for path in tried_paths:
        try:
            payload = fetch_graph_payload(base_url, path, headers, timeout_sec)
            return payload, path
        except urllib.error.HTTPError as exc:
            if exc.code == 404 and path != tried_paths[-1]:
                LOGGER.warning("Graph endpoint not found at %s, trying fallback.", _build_url(base_url, path))
                last_error = exc
                continue
            raise
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            raise
    if last_error:
        raise last_error
    raise RuntimeError("No graph endpoint path available.")


def normalize_graph_response(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidate = payload
    if isinstance(payload, dict) and "data" in payload:
        candidate = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    if not isinstance(candidate, dict):
        raise ValueError("Graph response must be an object with nodes and links.")
    nodes = candidate.get("nodes", [])
    links = candidate.get("links", [])
    if not isinstance(nodes, list) or not isinstance(links, list):
        raise ValueError("Graph response must contain list fields: nodes, links.")
    return nodes, links


def validate_graph(
    nodes: list[dict[str, Any]],
    links: list[dict[str, Any]],
    inserted_node_ids: list[str],
    expected_prerequisite_edges: int,
) -> dict[str, int]:
    node_ids = {str(item.get("id", "")).strip() for item in nodes if str(item.get("id", "")).strip()}
    inserted_set = set(inserted_node_ids)

    missing_inserted_nodes = sorted(inserted_set - node_ids)
    if missing_inserted_nodes:
        raise AssertionError(f"Inserted nodes missing from graph response: {missing_inserted_nodes[:5]}")

    dangling_targets = [
        str(link.get("target", "")).strip()
        for link in links
        if str(link.get("target", "")).strip() not in node_ids
    ]
    if dangling_targets:
        raise AssertionError(
            f"Found links pointing to non-existent target nodes, sample={dangling_targets[:5]}"
        )

    subset_links = [
        link
        for link in links
        if str(link.get("source", "")).strip() in inserted_set
        and str(link.get("target", "")).strip() in inserted_set
    ]
    subset_parent_count = sum(1 for link in subset_links if str(link.get("type", "")).strip() == "parent")
    subset_prereq_count = sum(1 for link in subset_links if str(link.get("type", "")).strip() == "prerequisite")

    expected_parent_count = max(0, len(inserted_node_ids) - 1)
    expected_total_count = expected_parent_count + expected_prerequisite_edges
    actual_total_count = len(subset_links)

    if subset_parent_count != expected_parent_count:
        raise AssertionError(
            f"Parent link count mismatch: expected={expected_parent_count}, actual={subset_parent_count}"
        )
    if subset_prereq_count != expected_prerequisite_edges:
        raise AssertionError(
            f"Prerequisite link count mismatch: expected={expected_prerequisite_edges}, actual={subset_prereq_count}"
        )
    if actual_total_count != expected_total_count:
        raise AssertionError(
            f"Total link count mismatch: expected={expected_total_count}, actual={actual_total_count}"
        )

    return {
        "node_count": len(inserted_node_ids),
        "expected_parent_links": expected_parent_count,
        "expected_prerequisite_links": expected_prerequisite_edges,
        "expected_total_links": expected_total_count,
        "actual_total_links": actual_total_count,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Insert random knowledge graph data and validate graph API links."
    )
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL.")
    parser.add_argument(
        "--graph-path",
        default="/api/knowledge/graph",
        help="Preferred graph endpoint path (requested path).",
    )
    parser.add_argument(
        "--fallback-graph-path",
        default="",
        help="Optional fallback graph endpoint path used when preferred path returns 404.",
    )
    parser.add_argument("--count", type=int, default=50, help="Number of knowledge nodes to insert.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible generation.")
    parser.add_argument("--run-id", default="", help="Optional run id suffix for generated ids.")
    parser.add_argument("--max-prereq-per-node", type=int, default=2, help="Max prerequisites per node.")
    parser.add_argument(
        "--prereq-probability",
        type=float,
        default=0.35,
        help="Probability to add prerequisite edges for each non-root node.",
    )
    parser.add_argument("--role", default="teacher", help="X-Role header value.")
    parser.add_argument("--user-id", default="teacher-001", help="X-User-Id header value.")
    parser.add_argument("--timeout-sec", type=float, default=10.0, help="HTTP timeout seconds.")
    parser.add_argument("--cleanup", action="store_true", help="Delete generated rows after validation.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db_path).resolve()
    if not db_path.exists():
        LOGGER.error("Database does not exist: %s", db_path)
        return 2
    if args.count < 2:
        LOGGER.error("--count must be >= 2")
        return 2

    if args.seed is None:
        seed = int(time.time() * 1000) % (2**31 - 1)
    else:
        seed = int(args.seed)
    rng = random.Random(seed)
    run_id = str(args.run_id or f"{int(time.time())}-{seed}")
    headers = {
        "X-Role": str(args.role).strip(),
        "X-User-Id": str(args.user_id).strip(),
    }

    LOGGER.info("DB path: %s", db_path)
    LOGGER.info("Graph endpoint: %s", _build_url(args.base_url, args.graph_path))
    if str(args.fallback_graph_path or "").strip():
        LOGGER.info("Graph endpoint fallback: %s", _build_url(args.base_url, args.fallback_graph_path))
    LOGGER.info("Count=%s, seed=%s, run_id=%s", args.count, seed, run_id)

    rows: list[dict[str, Any]] = []
    inserted_ids: list[str] = []
    try:
        rows, prerequisite_count = generate_knowledge_records(
            count=args.count,
            run_id=run_id,
            rng=rng,
            max_prereq_per_node=args.max_prereq_per_node,
            prerequisite_probability=args.prereq_probability,
        )
        inserted_ids = [str(item["id"]) for item in rows]
        insert_knowledge_records(rows, db_path)
        LOGGER.info("Inserted %s knowledge nodes.", len(rows))

        payload, used_path = fetch_graph_with_fallback(
            base_url=args.base_url,
            graph_path=args.graph_path,
            fallback_graph_path=args.fallback_graph_path,
            headers=headers,
            timeout_sec=args.timeout_sec,
        )
        nodes, links = normalize_graph_response(payload)
        summary = validate_graph(
            nodes=nodes,
            links=links,
            inserted_node_ids=inserted_ids,
            expected_prerequisite_edges=prerequisite_count,
        )
        LOGGER.info("Validation endpoint used: %s", used_path)
        LOGGER.info(
            "Validation passed: nodes=%s, expected_links=%s, actual_links=%s, prerequisites=%s",
            summary["node_count"],
            summary["expected_total_links"],
            summary["actual_total_links"],
            summary["expected_prerequisite_links"],
        )
        return 0
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("Knowledge graph generation/validation failed: %s", exc)
        return 1
    finally:
        if args.cleanup and rows:
            try:
                cleanup_records(rows, db_path)
                LOGGER.info("Cleanup complete. Deleted %s generated nodes.", len(rows))
            except Exception as cleanup_error:  # noqa: BLE001
                LOGGER.error("Cleanup failed: %s", cleanup_error)


if __name__ == "__main__":
    raise SystemExit(main())
