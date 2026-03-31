from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi.testclient import TestClient

from app.db import SEED_KNOWLEDGE_IDS
from app.main import create_app

POLITICS_ROOT_ID = SEED_KNOWLEDGE_IDS["POLITICS_ROOT"]
POLITICS_SECTION_ID = SEED_KNOWLEDGE_IDS["POLITICS_SECTION"]
POLITICS_CHAPTER_ID = SEED_KNOWLEDGE_IDS["POLITICS_CHAPTER"]
POLITICS_POINT_ID = SEED_KNOWLEDGE_IDS["POLITICS_POINT"]
POLITICS_POINT_ALT_ID = SEED_KNOWLEDGE_IDS["POLITICS_POINT_ALT"]
ENGLISH_POINT_ID = SEED_KNOWLEDGE_IDS["ENGLISH_POINT"]
INFO_TECH_ROOT_ID = SEED_KNOWLEDGE_IDS["INFO_TECH_ROOT"]
INFO_TECH_SECTION_ID = SEED_KNOWLEDGE_IDS["INFO_TECH_SECTION"]
INFO_TECH_CHAPTER_ID = SEED_KNOWLEDGE_IDS["INFO_TECH_CHAPTER"]
INFO_TECH_POINT_ID = SEED_KNOWLEDGE_IDS["INFO_TECH_POINT"]
ADVANCED_MATH_POINT_ID = SEED_KNOWLEDGE_IDS["ADVANCED_MATH_POINT"]

os.environ.setdefault("QB_ENV", "test")
os.environ.setdefault("QUESTION_BANK_SUPER_ADMIN_PASSWORD", "TestOnly-Global-Super-Admin-001")

_LATEST_CLIENT: TestClient | None = None
_AUTH_HEADER_CACHE: dict[tuple[int, str, str], dict[str, str]] = {}
_SEED_PHONE_BY_USER_ID = {
    "admin-001": "13800000001",
    "teacher-001": "13800000002",
    "teacher-002": "13800000003",
    "academic-001": "13800000004",
    "student-001": "13800000005",
    "student-002": "13800000006",
}


def make_client(tmp_path: Path) -> TestClient:
    app = create_app(tmp_path / "question_bank.db")
    client = TestClient(app)
    global _LATEST_CLIENT
    _LATEST_CLIENT = client
    _AUTH_HEADER_CACHE.clear()
    return client


def _injected_actor_headers(role: str, user_id: str) -> dict[str, str]:
    return {"X-Role": role, "X-User-Id": user_id}


def _resolve_user_phone(client: TestClient, user_id: str) -> str:
    fallback_phone = str(_SEED_PHONE_BY_USER_ID.get(user_id, "")).strip()
    repository = getattr(getattr(client.app.state, "service", None), "repository", None)
    if not repository or not hasattr(repository, "get_user_by_id"):
        return fallback_phone
    try:
        row = repository.get_user_by_id(user_id)
    except Exception:
        row = None
    if row and str(row.get("phone", "")).strip():
        return str(row["phone"]).strip()
    return fallback_phone


def _seed_password(user_id: str) -> str:
    return f"seed-password-{user_id}"


def _token_headers(role: str, user_id: str) -> dict[str, str]:
    client = _LATEST_CLIENT
    if client is None:
        raise RuntimeError("Auth helper requires make_client() before requesting token headers.")
    client.cookies.clear()
    cache_key = (id(client), role, user_id)
    cached = _AUTH_HEADER_CACHE.get(cache_key)
    if cached:
        return dict(cached)
    phone = _resolve_user_phone(client, user_id)
    if not phone:
        raise RuntimeError(f"Cannot resolve phone for user {user_id}.")
    login = client.post(
        "/api/question-bank/auth/login/password",
        json={"phone": phone, "password": _seed_password(user_id)},
    )
    if login.status_code != 200:
        client.cookies.clear()
        raise RuntimeError(
            f"Token login failed for {role}/{user_id}: status={login.status_code}, body={login.text[:200]}"
        )
    token = str(login.json()["data"]["accessToken"]).strip()
    client.cookies.clear()
    headers = {"Authorization": f"Bearer {token}"}
    _AUTH_HEADER_CACHE[cache_key] = headers
    return dict(headers)


def teacher_headers(user_id: str = "teacher-001") -> dict[str, str]:
    return _token_headers("teacher", user_id)


def super_admin_headers() -> dict[str, str]:
    return _token_headers("super_admin", "admin-001")


def academic_headers() -> dict[str, str]:
    return _token_headers("teacher", "teacher-001")


def student_headers(user_id: str = "student-001") -> dict[str, str]:
    return _token_headers("student", user_id)


def injected_actor_headers(role: str, user_id: str) -> dict[str, str]:
    """Explicitly return injected actor headers for local integration-mode tests only."""
    return _injected_actor_headers(role, user_id)


def create_question_payload(user_id: str = "teacher-001") -> dict[str, object]:
    return {
        "id": "",
        "userId": user_id,
        "title": "马克思主义认识论题目",
        "content": "马克思主义认识论的核心观点是什么？",
        "type": "single_choice",
        "examCategoryCode": "SCIENCE_ENGINEERING",
        "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
        "subjectCode": "POLITICS",
        "knowledgePoints": [POLITICS_POINT_ID],
        "options": [
            {"key": "A", "content": "认识来源于权威"},
            {"key": "B", "content": "认识源于实践"},
        ],
        "answer": "B",
        "analysis": "实践是认识的来源。",
        "score": 5,
        "difficulty": "medium",
        "sourceType": "test",
        "status": "DRAFT",
    }


def payload(user_id: str = "teacher-001") -> dict[str, object]:
    return create_question_payload(user_id=user_id)


def poll_task(client: TestClient, task_id: str, headers: dict[str, str]) -> dict[str, object]:
    latest: dict[str, object] = {}
    for _ in range(4):
        response = client.get(f"/api/question-bank/tasks/{task_id}", headers=headers)
        assert response.status_code == 200
        latest = response.json()["data"]
        if latest["status"] == "COMPLETED":
            return latest
    return latest


def knowledge_payload(parent_id: str = "") -> dict[str, object]:
    return {
        "id": "",
        "parentId": parent_id,
        "name": "新建知识点",
        "sort": 30,
        "status": "ENABLED",
        "extJson": json.dumps({"weight": "HIGH"}, ensure_ascii=False),
    }
