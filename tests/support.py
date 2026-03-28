from __future__ import annotations

import json
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


def make_client(tmp_path: Path) -> TestClient:
    app = create_app(tmp_path / "question_bank.db")
    return TestClient(app)


def teacher_headers(user_id: str = "teacher-001") -> dict[str, str]:
    return {"X-Role": "teacher", "X-User-Id": user_id}


def super_admin_headers() -> dict[str, str]:
    return {"X-Role": "super_admin", "X-User-Id": "admin-001"}


def academic_headers() -> dict[str, str]:
    return {"X-Role": "teacher", "X-User-Id": "teacher-001"}


def student_headers(user_id: str = "student-001") -> dict[str, str]:
    return {"X-Role": "student", "X-User-Id": user_id}


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
