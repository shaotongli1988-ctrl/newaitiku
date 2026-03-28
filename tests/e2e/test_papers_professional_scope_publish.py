from __future__ import annotations

import json
from pathlib import Path

from tests.support import make_client, teacher_headers


def _expect_envelope(response) -> dict[str, object]:
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, dict)
    assert set(payload.keys()) == {"code", "message", "data"}
    return payload["data"]


def _find_science_engineering_3_subjects(tree_payload: object) -> list[dict[str, object]]:
    exam_categories = tree_payload
    assert isinstance(exam_categories, list) and exam_categories

    science_category = next(
        (
            item
            for item in exam_categories
            if str(item.get("code", "")).strip() == "SCIENCE_ENGINEERING"
        ),
        None,
    )
    assert science_category is not None
    assert str(science_category.get("name", "")).strip() == "理工类"

    groups = science_category.get("children", [])
    assert isinstance(groups, list) and groups
    science_group_3 = next(
        (
            item
            for item in groups
            if str(item.get("code", "")).strip() == "SCIENCE_ENGINEERING_3"
        ),
        None,
    )
    assert science_group_3 is not None
    assert str(science_group_3.get("name", "")).strip() == "理工 3"

    subjects = science_group_3.get("children", [])
    assert isinstance(subjects, list) and subjects
    return subjects


def test_e2e_paper_publish_scope_for_science_engineering_3(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    teacher_002_headers = teacher_headers("teacher-002")

    tree_response = client.get(
        "/api/question-bank/professional-tree",
        headers=teacher_002_headers,
    )
    tree_payload = _expect_envelope(tree_response)
    assert isinstance(tree_payload, list)

    subjects = _find_science_engineering_3_subjects(tree_payload)
    subject_code_set = {str(item.get("code", "")).strip() for item in subjects}
    subject_name_set = {str(item.get("name", "")).strip() for item in subjects}

    assert subject_code_set == {"POLITICS", "ENGLISH", "INFO_TECH_INTRO", "ADVANCED_MATH_1"}
    assert subject_name_set == {"政治", "英语", "信息技术概论", "高等数学（一）"}

    question_query_response = client.get(
        "/api/question-bank/papers/questions",
        headers=teacher_002_headers,
        params={
            "page": 1,
            "size": 100,
            "examCategoryCode": "SCIENCE_ENGINEERING",
            "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
            "subjectCode": "INFO_TECH_INTRO",
        },
    )
    question_query_payload = _expect_envelope(question_query_response)
    question_items = question_query_payload.get("items", [])
    assert isinstance(question_items, list)
    assert question_items
    for item in question_items:
        ext_json = json.loads(item["extJson"])
        assert str(ext_json.get("subjectCode", "")).strip() == "INFO_TECH_INTRO"
        assert "SCIENCE_ENGINEERING_3" in list(ext_json.get("applicableGroups", []))

    save_response = client.post(
        "/api/question-bank/papers/manual",
        headers=teacher_002_headers,
        json={
            "paperName": "E2E-理工3-信息技术概论-精准发布",
            "subjectId": "subject-computer",
            "examCategoryCode": "SCIENCE_ENGINEERING",
            "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
            "subjectCode": "INFO_TECH_INTRO",
            "paperType": "chapter",
            "paperStatus": "PUBLISHED",
            "durationMinutes": 45,
            "totalScore": 10,
            "visibleToStudents": True,
            "publishClassIds": ["SCIENCE_ENGINEERING_3"],
            "questionIds": ["question-seed-008"],
            "questionScores": {"question-seed-008": 10},
        },
    )
    saved_payload = _expect_envelope(save_response)
    paper_id = str(saved_payload.get("paperId", "")).strip()
    assert paper_id

    paper_question_response = client.get(
        "/api/question-bank/papers/questions",
        headers=teacher_002_headers,
        params={
            "page": 1,
            "size": 100,
            "paperId": paper_id,
            "examCategoryCode": "SCIENCE_ENGINEERING",
            "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
            "subjectCode": "INFO_TECH_INTRO",
        },
    )
    paper_question_payload = _expect_envelope(paper_question_response)
    paper_question_items = paper_question_payload.get("items", [])
    assert isinstance(paper_question_items, list) and paper_question_items

    target_question = next((item for item in paper_question_items if item["id"] == "question-seed-008"), None)
    assert target_question is not None
    target_ext_json = json.loads(target_question["extJson"])
    paper_bindings = target_ext_json.get("paperBindings", [])
    assert isinstance(paper_bindings, list) and paper_bindings
    matched_binding = next((item for item in paper_bindings if str(item.get("paperId", "")).strip() == paper_id), None)
    assert matched_binding is not None
    assert str(matched_binding.get("examCategoryCode", "")).strip() == "SCIENCE_ENGINEERING"
    assert str(matched_binding.get("jointExamGroupCode", "")).strip() == "SCIENCE_ENGINEERING_3"
    assert str(matched_binding.get("subjectCode", "")).strip() == "INFO_TECH_INTRO"


def test_e2e_manual_paper_rejects_mismatched_joint_exam_group_code(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    teacher_002_headers = teacher_headers("teacher-002")

    response = client.post(
        "/api/question-bank/papers/manual",
        headers=teacher_002_headers,
        json={
            "paperName": "E2E-理工3-错误专业组-应拒绝",
            "subjectId": "subject-computer",
            "examCategoryCode": "SCIENCE_ENGINEERING",
            "jointExamGroupCode": "LITERATURE_1",
            "subjectCode": "INFO_TECH_INTRO",
            "paperType": "chapter",
            "paperStatus": "PUBLISHED",
            "durationMinutes": 45,
            "totalScore": 10,
            "visibleToStudents": True,
            "publishClassIds": ["SCIENCE_ENGINEERING_3"],
            "questionIds": ["question-seed-008"],
            "questionScores": {"question-seed-008": 10},
        },
    )
    assert response.status_code == 422
    payload = response.json()
    assert isinstance(payload, dict)
    detail = payload.get("detail", [])
    assert isinstance(detail, list) and detail
    detail_text = json.dumps(detail, ensure_ascii=False)
    assert "jointExamGroupCode" in detail_text or "joint_exam_group_code" in detail_text
