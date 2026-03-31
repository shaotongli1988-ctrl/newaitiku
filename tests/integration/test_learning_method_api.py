from __future__ import annotations

import json
from pathlib import Path

from app.db import get_connection
from tests.support import make_client, student_headers, teacher_headers


def _csrf_headers() -> dict[str, str]:
    return {"X-CSRF-Token": "test-csrf-token"}


def test_student_learning_methods_list_detail_start_complete_flow(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    listing = client.get("/api/question-bank/learning-methods", headers=student_headers())
    assert listing.status_code == 200
    listing_payload = listing.json()["data"]
    assert listing_payload["total"] >= 12
    assert listing_payload["items"]

    detail = client.get("/api/question-bank/learning-methods/M01", headers=student_headers())
    assert detail.status_code == 200
    detail_payload = detail.json()["data"]
    assert detail_payload["method"]["methodCode"] == "M01"
    assert detail_payload["progress"]["status"] in {"NOT_STARTED", "IN_PROGRESS", "COMPLETED"}

    start = client.post(
        "/api/question-bank/learning-methods/M01/start",
        headers=student_headers(),
        json={"practiceStrategy": "INTERLEAVE"},
    )
    assert start.status_code == 200
    start_payload = start.json()["data"]
    assert str(start_payload["sessionId"]).strip()
    assert start_payload["updatedProgress"]["status"] == "IN_PROGRESS"

    complete = client.post(
        "/api/question-bank/learning-methods/M01/complete",
        headers=student_headers(),
        json={
            "sessionId": start_payload["sessionId"],
            "accuracy": 0.8,
            "reviewSummary": "完成一次练习",
            "durationSec": 300,
        },
    )
    assert complete.status_code == 200
    complete_payload = complete.json()["data"]
    assert complete_payload["updatedProgress"]["status"] == "COMPLETED"
    assert float(complete_payload["updatedProgress"]["lastAccuracy"]) == 0.8


def test_student_cannot_access_admin_learning_methods(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    response = client.get("/api/question-bank/admin/learning-methods", headers=student_headers())
    assert response.status_code == 403


def test_teacher_admin_learning_method_write_requires_csrf(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    login_response = client.post(
        "/api/question-bank/auth/login/password",
        json={"phone": "13800000002", "password": "seed-password-teacher-001"},
    )
    assert login_response.status_code == 200
    payload = {
        "methodCode": "M99",
        "methodName": "测试方法",
        "oneLineIntro": "测试介绍",
        "useWhen": ["测试场景"],
        "steps": ["步骤1"],
        "commonMistakes": ["误区1"],
        "questionBankActions": ["动作1"],
        "starterTask": "任务1",
        "difficultyLevel": "L1",
        "estimatedMinutes": 10,
        "status": "ACTIVE",
    }
    forbidden_write = client.post(
        "/api/question-bank/admin/learning-methods",
        json=payload,
    )
    assert forbidden_write.status_code == 403


def test_teacher_admin_learning_method_invalid_payload_returns_400(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    headers = {**teacher_headers(), **_csrf_headers()}
    client.cookies.set("qbCsrfToken", "test-csrf-token")
    invalid_payload = {"methodCode": "M98"}
    invalid_response = client.post(
        "/api/question-bank/admin/learning-methods",
        headers=headers,
        json=invalid_payload,
    )
    assert invalid_response.status_code in {400, 422}


def test_teacher_admin_learning_method_crud_and_sort(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    headers = {**teacher_headers(), **_csrf_headers()}
    client.cookies.set("qbCsrfToken", "test-csrf-token")

    create_payload = {
        "methodCode": "M99",
        "methodName": "测试方法",
        "oneLineIntro": "测试介绍",
        "useWhen": ["测试场景"],
        "steps": ["步骤1"],
        "commonMistakes": ["误区1"],
        "questionBankActions": ["动作1"],
        "starterTask": "任务1",
        "difficultyLevel": "L1",
        "estimatedMinutes": 10,
        "status": "ACTIVE",
    }
    created = client.post(
        "/api/question-bank/admin/learning-methods",
        headers=headers,
        json=create_payload,
    )
    assert created.status_code == 200
    created_payload = created.json()["data"]
    assert created_payload["methodCode"] == "M99"

    updated = client.put(
        "/api/question-bank/admin/learning-methods/M99",
        headers=headers,
        json={"oneLineIntro": "更新后的介绍", "estimatedMinutes": 12},
    )
    assert updated.status_code == 200
    updated_payload = updated.json()["data"]
    assert updated_payload["oneLineIntro"] == "更新后的介绍"
    assert int(updated_payload["estimatedMinutes"]) == 12

    sorted_response = client.post(
        "/api/question-bank/admin/learning-methods/sort",
        headers=headers,
        json={"methodCodes": ["M99", "M01", "M02"]},
    )
    assert sorted_response.status_code == 200
    sorted_payload = sorted_response.json()["data"]
    assert sorted_payload["items"][0]["methodCode"] == "M99"
    assert sorted_payload["total"] >= 13


def test_teacher_admin_learning_method_profile_and_question_match_feature_auto_generation(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    headers = {**teacher_headers(), **_csrf_headers()}
    client.cookies.set("qbCsrfToken", "test-csrf-token")

    profile_response = client.post(
        "/api/question-bank/admin/learning-methods/M01/profile/auto-generate",
        headers=headers,
        json={"profileVersion": "v1", "forceRegenerate": True},
    )
    assert profile_response.status_code == 200
    profile_payload = profile_response.json()["data"]
    assert profile_payload["methodCode"] == "M01"
    assert str(profile_payload["profileVersion"]).strip()
    assert isinstance(profile_payload.get("profile", {}).get("methodTags", []), list)

    feature_response = client.post(
        "/api/question-bank/admin/questions/match-features/auto-batch",
        headers=headers,
        json={"limit": 20, "forceRefresh": True},
    )
    assert feature_response.status_code == 200
    feature_payload = feature_response.json()["data"]
    assert int(feature_payload.get("totalQuestions", 0)) >= 0
    assert int(feature_payload.get("processed", 0)) >= 0


def test_student_learning_method_recommend_and_feedback_flow(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    recommend_response = client.post(
        "/api/question-bank/learning-methods/M01/question-pack/recommend",
        headers=student_headers(),
        json={
            "questionCount": 8,
            "practiceStrategy": "SPRINT_BREAKTHROUGH",
            "difficultyPreference": "hard",
            "strategySource": "SUGGESTED",
        },
    )
    assert recommend_response.status_code == 200
    recommend_payload = recommend_response.json()["data"]
    assert str(recommend_payload.get("recommendationId", "")).strip()
    assert int(recommend_payload.get("questionCount", 0)) > 0
    assert isinstance(recommend_payload.get("questions", []), list)
    assert isinstance(recommend_payload.get("scoreSummary", {}).get("studentProfile", {}), dict)
    assert isinstance(recommend_payload.get("scoreSummary", {}).get("studentProfile", {}).get("tags", []), list)
    assert "studentProfileFit" in recommend_payload["questions"][0].get("scoreBreakdown", {})
    assert "studentProfileFit" in recommend_payload["questions"][0].get("scoreBreakdown", {}).get("weights", {})
    assert recommend_payload.get("practiceStrategy") == "SPRINT_BREAKTHROUGH"
    assert recommend_payload.get("recommendationStrategyCode") == "SPRINT"
    assert recommend_payload.get("recommendationStrategySource") == "SUGGESTED"
    assert recommend_payload.get("recommendationLog", {}).get("practiceStrategy") == "SPRINT_BREAKTHROUGH"
    assert recommend_payload.get("recommendationLog", {}).get("recommendationStrategyCode") == "SPRINT"
    assert recommend_payload.get("recommendationLog", {}).get("strategySource") == "SUGGESTED"

    feedback_response = client.post(
        "/api/question-bank/learning-methods/M01/question-pack/feedback",
        headers=student_headers(),
        json={
            "recommendationId": recommend_payload["recommendationId"],
            "feedbackStatus": "ACCEPTED",
            "isHelpful": True,
            "completedQuestionIds": [recommend_payload["questions"][0]["questionId"]],
            "skippedQuestionIds": [recommend_payload["questions"][-1]["questionId"]],
        },
    )
    assert feedback_response.status_code == 200
    feedback_payload = feedback_response.json()["data"]
    assert feedback_payload["recommendationId"] == recommend_payload["recommendationId"]
    assert feedback_payload["feedbackStatus"] == "ACCEPTED"

    history_response = client.get(
        "/api/question-bank/learning-methods/M01/question-pack/recommendations",
        headers=student_headers(),
        params={"limit": 10},
    )
    assert history_response.status_code == 200
    history_payload = history_response.json()["data"]
    assert int(history_payload.get("total", 0)) >= 1
    assert str(history_payload["items"][0].get("recommendationId", "")).strip()
    assert isinstance(history_payload["items"][0].get("questionIds", []), list)
    assert isinstance(history_payload["items"][0].get("completedQuestionIds", []), list)
    assert isinstance(history_payload["items"][0].get("skippedQuestionIds", []), list)
    assert isinstance(history_payload["items"][0].get("studentProfile", {}), dict)
    assert isinstance(history_payload["items"][0].get("studentProfile", {}).get("tags", []), list)
    assert isinstance(history_payload["items"][0].get("studentProfileFitAverage", 0.0), float)
    assert history_payload["items"][0].get("practiceStrategy") == "SPRINT_BREAKTHROUGH"
    assert history_payload["items"][0].get("recommendationStrategyCode") == "SPRINT"
    assert history_payload["items"][0].get("recommendationStrategySource") == "SUGGESTED"


def test_cutover_regression_wrong_book_read_path_prefers_formal_columns_over_legacy_fallback(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    repository = client.app.state.service.repository

    record = repository.get_student_question_bank("question-seed-008", "student-001")
    assert record is not None
    stale_ext = json.loads(record["extJson"])
    stale_ext["wrongBook"] = {
        "isCollected": False,
        "wrongCount": 0,
        "reviewCount": 0,
    }
    repository.upsert_student_question_bank(
        {
            **record,
            "extJson": json.dumps(stale_ext, ensure_ascii=False),
        }
    )

    with get_connection(repository.db_path) as connection:
        connection.execute(
            """
            UPDATE student_question_record
            SET wrongBookFlag = 1,
                wrongCount = 5,
                wrongBookReviewCount = 2,
                wrongBookCollectedAt = '2026-03-20T09:00:00Z',
                wrongBookReviewedAt = '2026-03-22T08:30:00Z',
                wrongBookLastReasonCode = 'KNOWLEDGE_GAP',
                wrongBookLastReasonLabel = '知识点掌握不牢'
            WHERE studentUserId = ? AND questionId = ?
            """,
            ("student-001", "question-seed-008"),
        )
        connection.commit()

    wrong_book_response = client.get(
        "/api/question-bank/student/wrong-book/questions",
        headers=student_headers(),
    )
    assert wrong_book_response.status_code == 200
    wrong_book_items = wrong_book_response.json()["data"]["items"]
    target = next(item for item in wrong_book_items if item["id"] == "question-seed-008")

    target_ext = json.loads(target["extJson"])
    wrong_state = target_ext["studentState"]["wrongBook"]
    assert wrong_state["isCollected"] is True
    assert wrong_state["wrongCount"] == 5
    assert wrong_state["reviewCount"] == 2
    assert wrong_state["reviewedAt"] == "2026-03-22T08:30:00Z"


def test_single_entry_regression_legacy_student_routes_redirect_to_single_entry_shell(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    wrong_book_redirect = client.get(
        "/student/wrong-book",
        headers=student_headers(),
        follow_redirects=False,
    )
    assert wrong_book_redirect.status_code == 307
    assert wrong_book_redirect.headers["location"] == "/student/question-bank/repair"

    personal_bank_redirect = client.get(
        "/student/personal-bank",
        headers=student_headers(),
        follow_redirects=False,
    )
    assert personal_bank_redirect.status_code == 307
    assert personal_bank_redirect.headers["location"] == "/student/question-bank/archive"
