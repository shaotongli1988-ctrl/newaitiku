from __future__ import annotations

import json
from pathlib import Path

from tests.support import make_client, payload, student_headers, teacher_headers


def test_teacher_publish_student_complete_question_journey(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    create_response = client.post(
        "/api/question-bank/questions",
        headers=teacher_headers(),
        json=payload(),
    )
    assert create_response.status_code == 200
    question = create_response.json()["data"]

    qa_response = client.post(
        f"/api/question-bank/questions/{question['id']}/status/QA_IN_PROGRESS",
        headers=teacher_headers(),
    )
    assert qa_response.status_code == 200

    review_response = client.post(
        f"/api/question-bank/questions/{question['id']}/status/REVIEW_PENDING",
        headers=teacher_headers("teacher-002"),
    )
    assert review_response.status_code == 200

    publish_response = client.post(
        f"/api/question-bank/questions/{question['id']}/status/PUBLISHED",
        headers=teacher_headers("teacher-002"),
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["data"]["status"] == "PUBLISHED"

    practice_response = client.get(
        "/api/question-bank/student/practice/questions",
        headers=student_headers(),
        params={"status": "PUBLISHED"},
    )
    assert practice_response.status_code == 200
    items = practice_response.json()["data"]["items"]
    matched_question = next(item for item in items if item["id"] == question["id"])
    assert matched_question["status"] == "PUBLISHED"

    submit_response = client.post(
        f"/api/question-bank/student/practice/questions/{question['id']}/submit",
        headers=student_headers(),
        json={"answer": "B", "elapsedSec": 18},
    )
    assert submit_response.status_code == 200
    result = submit_response.json()["data"]
    assert result["id"] == question["id"]
    ext = json.loads(result["extJson"])
    assert ext["studentState"]["chapterPractice"]["isCorrect"] is True
    assert ext["studentState"]["chapterPractice"]["lastAnswer"] == "B"


def test_teacher_student_submit_and_teacher_analytics_record_linked(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    create_response = client.post(
        "/api/question-bank/questions",
        headers=teacher_headers(),
        json=payload(),
    )
    assert create_response.status_code == 200
    question = create_response.json()["data"]

    qa_response = client.post(
        f"/api/question-bank/questions/{question['id']}/status/QA_IN_PROGRESS",
        headers=teacher_headers(),
    )
    assert qa_response.status_code == 200

    review_response = client.post(
        f"/api/question-bank/questions/{question['id']}/status/REVIEW_PENDING",
        headers=teacher_headers("teacher-002"),
    )
    assert review_response.status_code == 200

    publish_response = client.post(
        f"/api/question-bank/questions/{question['id']}/status/PUBLISHED",
        headers=teacher_headers("teacher-002"),
    )
    assert publish_response.status_code == 200

    practice_response = client.get(
        "/api/question-bank/student/practice/questions",
        headers=student_headers(),
        params={"status": "PUBLISHED"},
    )
    assert practice_response.status_code == 200
    items = practice_response.json()["data"]["items"]
    assert any(item["id"] == question["id"] for item in items)

    submit_response = client.post(
        f"/api/question-bank/student/practice/questions/{question['id']}/submit",
        headers=student_headers(),
        json={"answer": "B", "elapsedSec": 21},
    )
    assert submit_response.status_code == 200

    analytics_records = client.get(
        "/api/question-bank/analytics/records",
        headers=teacher_headers(),
        params={"studentUserId": "student-001", "page": 1, "size": 200},
    )
    assert analytics_records.status_code == 200
    analytics_items = analytics_records.json()["data"]["items"]
    linked = next((item for item in analytics_items if item["id"] == question["id"]), None)
    assert linked is not None
    ext_json = json.loads(linked["extJson"])
    analytics = ext_json["analytics"]
    assert analytics["studentUserId"] == "student-001"
    assert analytics["isCorrect"] is True
    assert int(analytics["answerDurationSec"]) > 0
    assert str(analytics["submittedAt"]).strip()
