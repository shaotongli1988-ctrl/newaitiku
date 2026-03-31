from __future__ import annotations

import json
import os
from pathlib import Path

from app.db import get_connection
from tests.support import INFO_TECH_POINT_ID, INFO_TECH_ROOT_ID, INFO_TECH_SECTION_ID, make_client, teacher_headers


def _bind_teacher_scope(client, user_id: str, exam_category_code: str, joint_exam_group_code: str) -> None:
    admin_password = str(os.environ.get("QUESTION_BANK_SUPER_ADMIN_PASSWORD", "")).strip()
    assert admin_password
    login_response = client.post(
        "/api/question-bank/auth/login/password",
        json={
            "phone": "15373326608",
            "password": admin_password,
        },
    )
    assert login_response.status_code == 200
    token = str((login_response.json().get("data") or {}).get("accessToken", "")).strip()
    assert token
    admin_headers = {"Authorization": f"Bearer {token}"}

    users_response = client.get("/api/question-bank/admin/users?page=1&size=200", headers=admin_headers)
    assert users_response.status_code == 200
    user_items = ((users_response.json().get("data") or {}).get("items") or [])
    target = next((item for item in user_items if str(item.get("userId", "")).strip() == user_id), None)
    assert target is not None

    save_response = client.post(
        "/api/question-bank/admin/users",
        headers=admin_headers,
        json={
            "userId": user_id,
            "role": str(target.get("role", "teacher")),
            "name": str(target.get("name", user_id)),
            "mobile": str(target.get("mobile", "")),
            "enabled": bool(target.get("enabled", True)),
            "permissions": target.get("permissions", []),
            "examCategoryCode": exam_category_code,
            "jointExamGroupCode": joint_exam_group_code,
            "vocationalMajor": str(target.get("vocationalMajor", "")),
            "prepStage": str(target.get("prepStage", "")),
        },
    )
    assert save_response.status_code == 200
    client.cookies.clear()


def test_question_list_is_forced_into_assigned_joint_group_scope(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    _bind_teacher_scope(client, "teacher-002", "SCIENCE_ENGINEERING", "SCIENCE_ENGINEERING_3")

    response = client.get(
        "/api/question-bank/questions?page=1&size=100",
        headers=teacher_headers("teacher-002"),
    )
    assert response.status_code == 200
    payload = response.json()
    items = (payload.get("data") or {}).get("items") or []
    assert isinstance(items, list)
    assert items

    for item in items:
        ext_json = item.get("extJson", {})
        if isinstance(ext_json, str):
            ext_json = json.loads(ext_json or "{}")
        assert str(ext_json.get("policyVersionCode", "")).strip() == "HB_ZSB_2026"
        if str(ext_json.get("subjectType", "")).strip() == "PUBLIC":
            assert "SCIENCE_ENGINEERING_3" in (ext_json.get("applicableGroups") or [])
            continue
        assert str(ext_json.get("jointExamGroupCode", "")).strip() == "SCIENCE_ENGINEERING_3"


def test_question_list_rejects_cross_joint_group_query_for_assigned_teacher(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    _bind_teacher_scope(client, "teacher-002", "SCIENCE_ENGINEERING", "SCIENCE_ENGINEERING_3")

    response = client.get(
        "/api/question-bank/questions?page=1&size=20&jointExamGroupCode=LITERATURE_1",
        headers=teacher_headers("teacher-002"),
    )
    assert response.status_code == 403


def test_cross_group_access_prevention(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    login_response = client.post(
        "/api/question-bank/auth/login/password",
        json={"phone": "13800000002", "password": "seed-password-teacher-001"},
    )
    assert login_response.status_code == 200
    token = str((login_response.json().get("data") or {}).get("accessToken", "")).strip()
    assert token

    response = client.get(
        "/api/question-bank/questions?page=1&size=20&subjectCode=MANAGEMENT_PRINCIPLES",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Joint-Group": "SCIENCE_ENGINEERING_3",
        },
    )
    assert response.status_code == 403
    payload = response.json()
    assert str(payload.get("code", "")).strip() == "QUESTION_FORBIDDEN"


def test_knowledge_tree_supports_subject_code_linkage_filter(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    response = client.get(
        "/api/question-bank/knowledge/tree?subjectCode=INFO_TECH_INTRO",
        headers=teacher_headers("teacher-002"),
    )
    assert response.status_code == 200
    payload = response.json()
    data = payload.get("data") or {}
    nodes = data.get("nodes") or []
    node_ids = {str(item.get("id", "")).strip() for item in nodes if isinstance(item, dict)}

    assert INFO_TECH_ROOT_ID in node_ids
    assert INFO_TECH_SECTION_ID in node_ids
    assert INFO_TECH_POINT_ID in node_ids
    assert "POLITICS-n00001" not in node_ids


def test_get_question_and_list_questions_by_ids_block_2025_payload_by_id(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    repository = client.app.state.service.repository

    with get_connection(repository.db_path) as connection:
        connection.execute(
            "UPDATE question "
            "SET extJson = json_set(extJson, '$.policyVersionCode', 'HB_ZSB_2025') "
            "WHERE id = ?",
            ("question-seed-001",),
        )
        connection.commit()

    assert repository.get_question("question-seed-001") is None

    selected = repository.list_questions_by_ids(["question-seed-001", "question-seed-002"])
    selected_ids = {str(item.get("id", "")).strip() for item in selected}
    assert "question-seed-001" not in selected_ids
    assert "question-seed-002" in selected_ids


def test_list_knowledge_enforces_2026_policy_without_subject_code_filter(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    repository = client.app.state.service.repository

    with get_connection(repository.db_path) as connection:
        connection.execute(
            "UPDATE knowledge "
            "SET extJson = json_set(extJson, '$.policyVersionCode', 'HB_ZSB_2025') "
            "WHERE id = ?",
            (INFO_TECH_ROOT_ID,),
        )
        connection.commit()

    knowledge_items = repository.list_knowledge(filters={})
    knowledge_ids = {str(item.get("id", "")).strip() for item in knowledge_items}
    assert INFO_TECH_ROOT_ID not in knowledge_ids


def test_list_student_records_uses_sql_policy_filter_for_question_scope(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    repository = client.app.state.service.repository

    with get_connection(repository.db_path) as connection:
        connection.execute(
            "UPDATE question "
            "SET extJson = json_set(extJson, '$.policyVersionCode', 'HB_ZSB_2025') "
            "WHERE id = ?",
            ("question-seed-001",),
        )
        connection.commit()

    items, total = repository.list_student_records(
        "student-001",
        {"subjectId": "", "chapter": "", "paperId": ""},
        1,
        100,
    )
    record_ids = {str(item.get("id", "")).strip() for item in items}

    assert total >= 1
    assert "question-seed-001" not in record_ids


def test_policy_version_expression_indexes_are_created_on_init(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    repository = client.app.state.service.repository

    with get_connection(repository.db_path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'index' "
            "AND name IN (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "idx_question_policy_version_expr",
                "idx_question_status_policy_version_expr",
                "idx_knowledge_policy_version_expr",
                "idx_knowledge_status_policy_version_expr",
                "idx_question_policy",
                "idx_question_joint_group",
                "idx_question_subject",
                "idx_question_chapter_code",
                "idx_question_point_code",
                "idx_question_policy_chapter_code",
                "idx_question_policy_point_code",
            ),
        ).fetchall()
    names = {str(row["name"]) for row in rows}

    assert "idx_question_policy_version_expr" in names
    assert "idx_knowledge_policy_version_expr" in names
    assert "idx_question_policy" in names
    assert "idx_question_joint_group" in names
    assert "idx_question_subject" in names
    assert "idx_question_chapter_code" in names
    assert "idx_question_point_code" in names
    assert "idx_question_policy_chapter_code" in names
    assert "idx_question_policy_point_code" in names
