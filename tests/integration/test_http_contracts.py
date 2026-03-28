from __future__ import annotations

from pathlib import Path

from tests.support import make_client, student_headers, teacher_headers


def test_subjects_endpoint_returns_success_envelope(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    response = client.get("/api/question-bank/subjects", headers=teacher_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "OK"
    assert body["message"] == "success"
    assert body["data"]


def test_student_endpoints_share_same_actor_scope(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    dashboard = client.get("/api/question-bank/student/dashboard", headers=student_headers())
    assert dashboard.status_code == 200
    dashboard_payload = dashboard.json()
    assert dashboard_payload["code"] == "OK"
    assert dashboard_payload["message"] == "success"
    assert dashboard_payload["data"]

    api = client.get("/api/question-bank/student/practice/questions", headers=student_headers())
    assert api.status_code == 200
    payload = api.json()
    assert payload["code"] == "OK"
    assert payload["message"] == "success"
    assert set(payload["data"].keys()) >= {"items", "page", "size", "total"}
