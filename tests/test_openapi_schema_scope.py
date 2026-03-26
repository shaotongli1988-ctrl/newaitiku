from __future__ import annotations

import json
from pathlib import Path

from app.main import create_app
from scripts.export_openapi import compact_openapi_schema
from tests.support import make_client


def test_openapi_excludes_page_bootstrap_routes_but_keeps_spa_api_endpoints(tmp_path: Path):
    client = make_client(tmp_path)

    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]

    excluded_page_routes = {
        "/",
        "/teacher/home",
        "/teacher/questions",
        "/teacher/student-accounts",
        "/login",
        "/student/practice",
        "/student/practice/chapter",
        "/student/practice/free",
        "/student/practice/mock",
        "/student/practice/tasks",
        "/student/home",
        "/student/analysis",
        "/student/analysis/overview",
        "/student/analysis/tasks",
        "/student/analysis/points",
        "/student/points",
        "/student/wrong-book",
        "/student/personal-bank",
        "/teacher/papers",
        "/teacher/exam-tasks",
        "/teacher/analytics",
        "/teacher/content-system",
        "/teacher/knowledge",
        "/admin/home",
        "/admin/control-center",
        "/admin/syllabus",
        "/messages",
    }
    for path in excluded_page_routes:
        assert path not in paths

    assert "/api/knowledge-tree" in paths
    assert "/api/question-bank/admin/console" in paths
    assert "/api/question-bank/knowledge/{knowledgeId}" in paths
    assert "/api/question-bank/papers/templates/{templateId}" in paths
    assert "/api/question-bank/papers/{paperId}" in paths
    assert "/api/question-bank/questions/{questionId}" in paths
    assert "/api/question-bank/learning-methods" in paths
    assert "/api/question-bank/learning-methods/{methodCode}" in paths
    assert "/api/question-bank/learning-methods/{methodCode}/start" in paths
    assert "/api/question-bank/learning-methods/{methodCode}/complete" in paths
    assert "/api/question-bank/admin/learning-methods" in paths
    assert "/api/question-bank/admin/learning-methods/{methodCode}" in paths
    assert "/api/question-bank/admin/learning-methods/sort" in paths


def test_compacted_openapi_stays_within_guard_parse_budget(tmp_path: Path):
    app = create_app(tmp_path / "question-bank.db")
    compact_schema = compact_openapi_schema(app.openapi())
    compact_payload = json.dumps(compact_schema, ensure_ascii=False, separators=(",", ":")) + "\n"

    assert len(compact_payload) < 300_000


def test_openapi_invalid_route_returns_404_error(tmp_path: Path):
    client = make_client(tmp_path)

    invalid_response = client.get("/openapi-invalid-route")
    assert invalid_response.status_code == 404
