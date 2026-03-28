from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import patch

import httpx
import pytest

from tests.support import POLITICS_POINT_ID


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def _question_payload(
    *,
    stem: str = "测试题：实践是检验真理的唯一标准。",
    question_type: str = "single_choice",
    answer: str = "B",
) -> dict[str, str]:
    options = []
    if question_type != "subjective":
        options = [
            {"key": "A", "content": "实践来源于权威"},
            {"key": "B", "content": "真理需要实践检验"},
            {"key": "C", "content": "实践不重要"},
            {"key": "D", "content": "认识与实践无关"},
        ]
    return {
        "userId": "teacher-001",
        "title": "实践与认识测验题",
        "content": stem,
        "type": question_type,
        "examCategoryCode": "SCIENCE_ENGINEERING",
        "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
        "subjectCode": "POLITICS",
        "knowledgePoints": [POLITICS_POINT_ID],
        "options": options,
        "answer": answer,
        "analysis": "测试解析",
        "score": 5,
        "difficulty": "medium",
        "sourceType": "pytest-core-suite",
        "status": "DRAFT",
    }


async def _create_question(async_client: httpx.AsyncClient, headers: dict[str, str], stem: str) -> dict[str, object]:
    response = await async_client.post(
        "/api/question-bank/questions",
        headers=headers,
        json=_question_payload(stem=stem),
    )
    assert response.status_code == 200
    return response.json()["data"]


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/question-bank/admin/console",
        "/api/question-bank/admin/settings",
        "/api/question-bank/admin/users",
    ],
)
async def test_case_1_unauthorized_without_token(async_client: httpx.AsyncClient, endpoint: str) -> None:
    response = await async_client.get(endpoint)
    assert response.status_code in {401, 403}


async def test_case_2_teacher_forbidden_on_admin_settings(
    async_client: httpx.AsyncClient,
    teacher_auth_headers: dict[str, str],
) -> None:
    response = await async_client.get("/api/question-bank/admin/settings", headers=teacher_auth_headers)
    assert response.status_code == 403


async def test_case_3_student_cannot_delete_question(
    async_client: httpx.AsyncClient,
    student_auth_headers: dict[str, str],
) -> None:
    response = await async_client.delete(
        "/api/question-bank/questions/question-seed-001",
        headers=student_auth_headers,
    )
    assert response.status_code == 403


async def test_case_4_owner_cannot_publish_directly_from_qa(
    async_client: httpx.AsyncClient,
    teacher_auth_headers: dict[str, str],
) -> None:
    created = await _create_question(
        async_client,
        teacher_auth_headers,
        stem="Case4: 所有者不可从 QA 直接发布。",
    )
    question_id = str(created["id"])

    qa_response = await async_client.post(
        f"/api/question-bank/questions/{question_id}/status/QA_IN_PROGRESS",
        headers=teacher_auth_headers,
    )
    assert qa_response.status_code == 200

    direct_publish = await async_client.post(
        f"/api/question-bank/questions/{question_id}/status/PUBLISHED",
        headers=teacher_auth_headers,
    )
    assert direct_publish.status_code == 422


async def test_case_5_mutual_review_only_other_teacher_can_pass(
    async_client: httpx.AsyncClient,
    teacher_auth_headers: dict[str, str],
    teacher_b_auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    created = await _create_question(
        async_client,
        teacher_auth_headers,
        stem="Case5: 互审逻辑验证。",
    )
    question_id = str(created["id"])

    qa_response = await async_client.post(
        f"/api/question-bank/questions/{question_id}/status/QA_IN_PROGRESS",
        headers=teacher_auth_headers,
    )
    assert qa_response.status_code == 200

    owner_review = await async_client.post(
        f"/api/question-bank/questions/{question_id}/status/REVIEW_PENDING",
        headers=teacher_auth_headers,
    )
    assert owner_review.status_code == 403

    other_review = await async_client.post(
        f"/api/question-bank/questions/{question_id}/status/REVIEW_PENDING",
        headers=teacher_b_auth_headers,
    )
    assert other_review.status_code == 200

    admin_publish = await async_client.post(
        f"/api/question-bank/questions/{question_id}/status/PUBLISHED",
        headers=admin_auth_headers,
    )
    assert admin_publish.status_code in {200, 403}


async def test_case_6_rejected_question_rolls_back_to_draft_after_update(
    async_client: httpx.AsyncClient,
    teacher_auth_headers: dict[str, str],
    teacher_b_auth_headers: dict[str, str],
) -> None:
    created = await _create_question(
        async_client,
        teacher_auth_headers,
        stem="Case6: 驳回后修改回转草稿。",
    )
    question_id = str(created["id"])

    qa_response = await async_client.post(
        f"/api/question-bank/questions/{question_id}/status/QA_IN_PROGRESS",
        headers=teacher_auth_headers,
    )
    assert qa_response.status_code == 200

    review_pending = await async_client.post(
        f"/api/question-bank/questions/{question_id}/status/REVIEW_PENDING",
        headers=teacher_b_auth_headers,
    )
    assert review_pending.status_code == 200

    rejected = await async_client.post(
        f"/api/question-bank/questions/{question_id}/status/REJECTED",
        headers=teacher_b_auth_headers,
        json={"reason": "审核驳回，需补充关键步骤。"},
    )
    assert rejected.status_code == 200

    created_ext = created.get("extJson")
    if isinstance(created_ext, str):
        created_ext = json.loads(created_ext)

    update_payload = {
        "title": created_ext.get("title", "Case6: 驳回后修订"),
        "content": "Case6: 驳回后已修订题干。",
        "type": created["type"],
        "knowledgePoints": [created["knowledgeId"]],
        "options": json.loads(created["optionsJson"]),
        "answer": created["answer"],
        "status": "DRAFT",
    }
    updated = await async_client.put(
        f"/api/question-bank/questions/{question_id}",
        headers=teacher_auth_headers,
        json=update_payload,
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["status"] == "DRAFT"


async def test_case_7_student_filter_only_matches_science_engineering_scope(
    async_client: httpx.AsyncClient,
    student_auth_headers: dict[str, str],
) -> None:
    response = await async_client.get(
        "/api/question-bank/student/practice/questions",
        headers=student_auth_headers,
        params={"page": 1, "size": 100},
    )
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert items

    for item in items:
        ext_json = json.loads(item["extJson"])
        assert str(ext_json.get("examCategoryCode", "")) != "ART"
        if str(ext_json.get("examCategoryCode", "")):
            assert str(ext_json["examCategoryCode"]) == "SCIENCE_ENGINEERING"


@pytest.mark.parametrize(
    ("exam_category_code", "joint_exam_group_code"),
    [
        ("SCIENCE_ENGINEERING", "LITERATURE_11"),
        ("ART", "SCIENCE_ENGINEERING_3"),
        ("LITERATURE", "SCIENCE_ENGINEERING_1"),
    ],
)
async def test_case_8_student_profile_invalid_group_mapping_returns_422(
    async_client: httpx.AsyncClient,
    student_auth_headers: dict[str, str],
    exam_category_code: str,
    joint_exam_group_code: str,
) -> None:
    response = await async_client.post(
        "/api/question-bank/student/profile",
        headers=student_auth_headers,
        json={
            "examCategoryCode": exam_category_code,
            "jointExamGroupCode": joint_exam_group_code,
        },
    )
    assert response.status_code == 422


async def test_case_9_ai_quota_exhaustion_returns_error(
    async_client: httpx.AsyncClient,
    app,
    student_auth_headers: dict[str, str],
) -> None:
    service = app.state.service
    today = datetime.now(timezone.utc).date().isoformat()
    service.repository.set_student_profile_ai_quota(
        "student-001",
        {"dailyLimit": 1, "usedCount": 0, "quotaDate": today},
        service._now_iso(),  # noqa: SLF001
    )

    first = await async_client.post(
        "/api/question-bank/student/practice/questions/question-seed-005/ai-tutor",
        headers=student_auth_headers,
        json={"prompt": "第一次 AI 请求"},
    )
    assert first.status_code == 200

    second = await async_client.post(
        "/api/question-bank/student/practice/questions/question-seed-005/ai-tutor",
        headers=student_auth_headers,
        json={"prompt": "第二次 AI 请求"},
    )
    assert second.status_code == 422


async def test_case_10_ai_task_queue_visible_as_pending_or_processing(
    async_client: httpx.AsyncClient,
    student_auth_headers: dict[str, str],
) -> None:
    with patch(
        "app.service.QuestionBankService._build_ai_marking_result",
        return_value={
            "totalScore": 88.0,
            "correctnessScore": 55.0,
            "stepsScore": 25.0,
            "formatScore": 8.0,
            "comments": ["mocked"],
            "sampleAnswer": "mocked answer",
        },
    ):
        submit = await async_client.post(
            "/api/question-bank/student/practice/questions/question-seed-005/ai-marking",
            headers=student_auth_headers,
            json={"answer": "异步任务队列可观测性验证"},
        )
    assert submit.status_code == 200
    task_id = str(submit.json()["data"]["id"])

    tasks = await async_client.get(
        "/api/question-bank/tasks",
        headers=student_auth_headers,
        params={"page": 1, "size": 50},
    )
    assert tasks.status_code == 200
    task_items = tasks.json()["data"]["items"]
    target = next(item for item in task_items if str(item["id"]) == task_id)
    assert str(target["status"]) in {"PENDING", "PROCESSING", "QUEUED", "RUNNING"}


async def test_case_11_pagination_overflow_returns_empty_items(
    async_client: httpx.AsyncClient,
    teacher_auth_headers: dict[str, str],
) -> None:
    response = await async_client.get(
        "/api/question-bank/questions",
        headers=teacher_auth_headers,
        params={"page": 99999, "size": 20},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["page"] == 99999
    assert data["items"] == []


async def test_case_12_sql_injection_like_keyword_does_not_break_query_layer(
    async_client: httpx.AsyncClient,
    teacher_auth_headers: dict[str, str],
) -> None:
    attack_keyword = "'; DROP TABLE question; --"
    response = await async_client.get(
        "/api/question-bank/questions",
        headers=teacher_auth_headers,
        params={"keyword": attack_keyword, "page": 1, "size": 20},
    )
    assert response.status_code == 200

    follow_up = await async_client.get(
        "/api/question-bank/questions",
        headers=teacher_auth_headers,
        params={"page": 1, "size": 20},
    )
    assert follow_up.status_code == 200


async def test_case_13_student_conversion_journey_updates_onboarding_and_admin_overview(
    async_client: httpx.AsyncClient,
    app,
    student_auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    def _summary_counter(summary: dict[str, object], key: str) -> int:
        return int(summary.get(key, 0) or 0)

    def _event_counter_map(counters: list[dict[str, object]]) -> dict[str, int]:
        return {str(item.get("eventType", "")): int(item.get("eventCount", 0) or 0) for item in counters}

    baseline_overview = await async_client.get(
        "/api/question-bank/admin/conversion/overview",
        headers=admin_auth_headers,
        params={"startDate": "2000-01-01", "endDate": "2099-12-31"},
    )
    assert baseline_overview.status_code == 200
    baseline_data = baseline_overview.json()["data"]
    baseline_summary = baseline_data["summary"]
    baseline_event_map = _event_counter_map(baseline_data["eventTypeCounters"])

    start_response = await async_client.post(
        "/api/question-bank/student/diagnosis/quick/start",
        headers=student_auth_headers,
        json={"questionCount": 3, "sourceType": "ONBOARDING"},
    )
    assert start_response.status_code == 200
    start_data = start_response.json()["data"]
    session_id = str(start_data["sessionId"])
    question_ids = [str(question_id) for question_id in start_data["questionIds"]]
    question_previews = start_data.get("questions", [])
    assert session_id
    assert len(question_ids) == 3
    assert isinstance(question_previews, list)
    assert len(question_previews) == 3
    assert all("answer" not in item for item in question_previews if isinstance(item, dict))

    question_rows = {
        str(row["id"]): row for row in app.state.service.repository.list_questions_by_ids(question_ids)
    }
    submit_response = await async_client.post(
        f"/api/question-bank/student/diagnosis/quick/{session_id}/submit",
        headers=student_auth_headers,
        json={
            "answers": [
                {
                    "questionId": question_id,
                    "answer": str(question_rows[question_id]["answer"]),
                    "elapsedSec": 10,
                }
                for question_id in question_ids
            ],
            "sourceType": "ONBOARDING",
        },
    )
    assert submit_response.status_code == 200
    submit_data = submit_response.json()["data"]
    assert submit_data["idempotent"] is False
    assert submit_data["status"] == "COMPLETED"
    assert submit_data["answeredCount"] == 3

    dashboard_after_diagnosis = await async_client.get(
        "/api/question-bank/student/dashboard",
        headers=student_auth_headers,
    )
    assert dashboard_after_diagnosis.status_code == 200
    onboarding_after_diagnosis = dashboard_after_diagnosis.json()["data"]["onboarding"]
    assert onboarding_after_diagnosis["quickDiagnosisCompleted"] is True
    assert onboarding_after_diagnosis["subscriptionActive"] is False
    assert onboarding_after_diagnosis["completed"] is True
    assert onboarding_after_diagnosis["completionSource"] == "QUICK_DIAGNOSIS"

    mock_order_response = await async_client.post(
        "/api/question-bank/student/subscription/mock-orders",
        headers=student_auth_headers,
        json={"planCode": "AI_SCORE_BOOST_30D", "sourceType": "ONBOARDING", "sessionId": session_id},
    )
    assert mock_order_response.status_code == 200
    order_id = str(mock_order_response.json()["data"]["order"]["orderId"])
    assert order_id

    transaction_no = f"MOCK-TXN-CASE13-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    confirm_response = await async_client.post(
        f"/api/question-bank/student/subscription/mock-orders/{order_id}/confirm",
        headers=student_auth_headers,
        json={"transactionNo": transaction_no},
    )
    assert confirm_response.status_code == 200
    confirm_data = confirm_response.json()["data"]
    assert confirm_data["idempotent"] is False
    assert confirm_data["order"]["status"] == "PAID"
    assert confirm_data["subscription"]["status"] == "ACTIVE"
    assert confirm_data["subscription"]["subscriptionActive"] is True

    dashboard_after_subscription = await async_client.get(
        "/api/question-bank/student/dashboard",
        headers=student_auth_headers,
    )
    assert dashboard_after_subscription.status_code == 200
    onboarding_after_subscription = dashboard_after_subscription.json()["data"]["onboarding"]
    assert onboarding_after_subscription["quickDiagnosisCompleted"] is True
    assert onboarding_after_subscription["subscriptionActive"] is True
    assert onboarding_after_subscription["completed"] is True
    assert onboarding_after_subscription["completionSource"] == "SUBSCRIPTION"

    overview_response = await async_client.get(
        "/api/question-bank/admin/conversion/overview",
        headers=admin_auth_headers,
        params={"startDate": "2000-01-01", "endDate": "2099-12-31"},
    )
    assert overview_response.status_code == 200
    overview_data = overview_response.json()["data"]
    summary = overview_data["summary"]
    event_map = _event_counter_map(overview_data["eventTypeCounters"])

    assert _summary_counter(summary, "quickDiagnosisStartCount") >= _summary_counter(
        baseline_summary,
        "quickDiagnosisStartCount",
    ) + 1
    assert _summary_counter(summary, "quickDiagnosisCompleteCount") >= _summary_counter(
        baseline_summary,
        "quickDiagnosisCompleteCount",
    ) + 1
    assert _summary_counter(summary, "mockOrderCreatedCount") >= _summary_counter(
        baseline_summary,
        "mockOrderCreatedCount",
    ) + 1
    assert _summary_counter(summary, "mockPaymentSuccessCount") >= _summary_counter(
        baseline_summary,
        "mockPaymentSuccessCount",
    ) + 1
    assert _summary_counter(summary, "subscriptionActivatedCount") >= _summary_counter(
        baseline_summary,
        "subscriptionActivatedCount",
    ) + 1

    assert event_map.get("QUICK_DIAGNOSIS_START", 0) >= baseline_event_map.get("QUICK_DIAGNOSIS_START", 0) + 1
    assert event_map.get("QUICK_DIAGNOSIS_COMPLETE", 0) >= baseline_event_map.get("QUICK_DIAGNOSIS_COMPLETE", 0) + 1
    assert event_map.get("MOCK_ORDER_CREATED", 0) >= baseline_event_map.get("MOCK_ORDER_CREATED", 0) + 1
    assert event_map.get("MOCK_PAYMENT_SUCCESS", 0) >= baseline_event_map.get("MOCK_PAYMENT_SUCCESS", 0) + 1
    assert event_map.get("SUBSCRIPTION_ACTIVATED", 0) >= baseline_event_map.get("SUBSCRIPTION_ACTIVATED", 0) + 1
