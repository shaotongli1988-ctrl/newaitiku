from __future__ import annotations

import json
from pathlib import Path

from tests.support import make_client, poll_task, student_headers, teacher_headers


def parse_page_bootstrap(raw: str) -> dict[str, object]:
    payload = json.loads(raw)
    assert isinstance(payload, dict)
    assert "route" in payload
    assert "viewKey" in payload
    assert "pageTitle" in payload
    return payload


def test_student_pages_keep_navigation_isolated(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    pages = [
        "/student/home",
        "/student/practice",
        "/student/analysis",
        "/student/analysis/overview",
        "/student/analysis/tasks",
        "/student/analysis/points",
    ]

    for path in pages:
        response = client.get(path, headers=student_headers())
        assert response.status_code == 200
        payload = parse_page_bootstrap(response.text)
        assert payload["route"] == path
        assert payload["actor"] == {"role": "student", "userId": "student-001"}

    home_page = client.get("/student/home", headers=student_headers())
    assert home_page.status_code == 200
    home_payload = parse_page_bootstrap(home_page.text)
    assert home_payload["viewKey"] == "student-home"
    assert home_payload["pageTitle"] == "专属学习台"

    practice_page = client.get("/student/practice", headers=student_headers())
    assert practice_page.status_code == 200
    practice_payload = parse_page_bootstrap(practice_page.text)
    assert practice_payload["viewKey"] == "student-practice"
    assert practice_payload["pageTitle"] == "学生端刷题页"

    wrong_book_redirect = client.get("/student/wrong-book", headers=student_headers(), follow_redirects=False)
    assert wrong_book_redirect.status_code == 307
    assert wrong_book_redirect.headers["location"] == "/student/question-bank/repair"

    personal_bank_redirect = client.get("/student/personal-bank", headers=student_headers(), follow_redirects=False)
    assert personal_bank_redirect.status_code == 307
    assert personal_bank_redirect.headers["location"] == "/student/question-bank/archive"


def test_message_center_layout_isolated_for_student_and_teacher(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    student_page = client.get("/messages", params={"role": "student", "userId": "student-001"})
    assert student_page.status_code == 200
    student_payload = parse_page_bootstrap(student_page.text)
    assert student_payload["route"] == "/messages"
    assert student_payload["actor"] == {"role": "student", "userId": "student-001"}
    assert "message:send" not in student_payload["permissions"]

    teacher_page = client.get("/messages", params={"role": "teacher", "userId": "teacher-001"})
    assert teacher_page.status_code == 200
    teacher_payload = parse_page_bootstrap(teacher_page.text)
    assert teacher_payload["route"] == "/messages"
    assert teacher_payload["actor"] == {"role": "teacher", "userId": "teacher-001"}
    assert "message:send" in teacher_payload["permissions"]


def test_student_interaction_round_acceptance(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    practice_page = client.get("/student/practice", headers=student_headers())
    assert practice_page.status_code == 200
    practice_payload = parse_page_bootstrap(practice_page.text)
    assert practice_payload["route"] == "/student/practice"
    assert practice_payload["actor"] == {"role": "student", "userId": "student-001"}

    practice = client.get(
        "/api/question-bank/student/practice/questions",
        headers=student_headers(),
        params={"subjectId": "subject-politics", "chapter": "导论"},
    )
    assert practice.status_code == 200
    practice_items = practice.json()["data"]["items"]
    assert practice_items

    submit_wrong = client.post(
        "/api/question-bank/student/practice/questions/question-seed-001/submit",
        headers=student_headers(),
        json={"answer": "A", "elapsedSec": 45},
    )
    assert submit_wrong.status_code == 200

    collect_wrong = client.post(
        "/api/question-bank/student/practice/questions/question-seed-001/wrong-book",
        headers=student_headers(),
    )
    assert collect_wrong.status_code == 200

    wrong_book = client.get("/api/question-bank/student/wrong-book/questions?page=1&size=100", headers=student_headers())
    assert wrong_book.status_code == 200
    wrong_items = wrong_book.json()["data"]["items"]
    assert any(item["id"] == "question-seed-001" for item in wrong_items)

    reasoned = client.post(
        "/api/question-bank/student/wrong-book/papers/reasoned",
        headers=student_headers(),
        params={"reasonCode": "KNOWLEDGE_GAP", "questionCount": 10},
    )
    assert reasoned.status_code == 200
    reasoned_data = reasoned.json()["data"]
    assert reasoned_data["reasonCode"] == "KNOWLEDGE_GAP"
    assert len(reasoned_data["questionIds"]) >= 5

    tutor = client.post(
        "/api/question-bank/student/practice/questions/question-seed-005/ai-tutor",
        headers=student_headers(),
        json={"prompt": "请给出标准答题步骤与采分点。", "promptImageUrl": ""},
    )
    assert tutor.status_code == 200
    tutor_task = tutor.json()["data"]
    done = poll_task(client, str(tutor_task["id"]), student_headers())
    assert done["status"] in {"COMPLETED", "RUNNING", "QUEUED"}

    send_message = client.post(
        "/api/question-bank/messages/send",
        headers=teacher_headers(),
        json={
            "userIds": ["student-001"],
            "category": "STUDY_REMINDER",
            "title": "验收提醒",
            "content": "请完成今日章节刷题并及时交卷。",
        },
    )
    assert send_message.status_code == 200

    unread = client.get("/api/question-bank/messages?readStatus=unread&page=1&size=20", headers=student_headers())
    assert unread.status_code == 200
    unread_items = unread.json()["data"]["items"]
    assert unread_items
    message_id = unread_items[0]["messageId"]

    batch_read = client.post(
        "/api/question-bank/messages/read/batch",
        headers=student_headers(),
        json={"messageIds": [message_id]},
    )
    assert batch_read.status_code == 200
    assert batch_read.json()["data"]["markedCount"] >= 1

    available = client.get("/api/question-bank/student/papers/questions?page=1&size=100", headers=student_headers())
    assert available.status_code == 200
    available_items = available.json()["data"]["items"]
    assert available_items
    first_ext = json.loads(available_items[0]["extJson"])
    first_bindings = first_ext.get("paperBindings", [])
    assert first_bindings
    paper_id = first_bindings[0]["paperId"]

    paper_questions = client.get(f"/api/question-bank/student/papers/{paper_id}/questions?page=1&size=100", headers=student_headers())
    assert paper_questions.status_code == 200
    questions = paper_questions.json()["data"]["items"]
    assert questions
    answers = []
    for question in questions[:3]:
        if question["type"] == "subjective":
            answer = "这是用于验收的主观题答案，内容长度超过二十字。"
        else:
            answer = str(question["answer"] or "A")
        answers.append({"questionId": question["id"], "answer": answer, "elapsedSec": 40, "marked": False})
    submit_paper = client.post(
        f"/api/question-bank/student/papers/{paper_id}/submit",
        headers=student_headers(),
        json={"answers": answers, "totalElapsedSec": 360},
    )
    assert submit_paper.status_code == 200
    report = submit_paper.json()["data"]
    assert report["paperId"] == paper_id
    assert report["reportId"].startswith("paper-report-")
    assert "pendingSubjectiveTaskIds" in report


def test_student_personal_bank_round_acceptance(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    headers = student_headers()

    for question_id in ("question-seed-001", "question-seed-002"):
        toggle = client.post(
            f"/api/question-bank/student/practice/questions/{question_id}/personal-bank",
            headers=headers,
            json={"isCollected": True},
        )
        assert toggle.status_code == 200

    for question_id in ("question-seed-001", "question-seed-002"):
        wrong_submit = client.post(
            f"/api/question-bank/student/practice/questions/{question_id}/submit",
            headers=headers,
            json={"answer": "A", "elapsedSec": 30},
        )
        assert wrong_submit.status_code == 200

    listed = client.get(
        "/api/question-bank/student/personal-bank/questions",
        headers=headers,
        params={"page": 1, "size": 100},
    )
    assert listed.status_code == 200
    listed_ids = {item["id"] for item in listed.json()["data"]["items"]}
    assert {"question-seed-001", "question-seed-002"}.issubset(listed_ids)

    summary = client.get("/api/question-bank/student/personal-bank/summary", headers=headers)
    assert summary.status_code == 200
    summary_data = summary.json()["data"]
    assert summary_data["totalCount"] >= 2
    due_plan_summary = next(item for item in summary_data["reviewPlan"] if item["planKey"] == "todayDue")
    assert {"question-seed-001", "question-seed-002"}.issubset(set(due_plan_summary["questionIds"]))

    review_plans = client.get("/api/question-bank/student/personal-bank/review-plans", headers=headers)
    assert review_plans.status_code == 200
    due_plan = next(item for item in review_plans.json()["data"] if item["planKey"] == "todayDue")
    assert due_plan["questionCount"] >= 2

    review_detail = client.get(
        f"/api/question-bank/student/personal-bank/review-plans/{due_plan['planId']}",
        headers=headers,
    )
    assert review_detail.status_code == 200
    detail_data = review_detail.json()["data"]
    assert {"question-seed-001", "question-seed-002"}.issubset(set(detail_data["questionIds"]))

    started = client.post(
        f"/api/question-bank/student/personal-bank/review-plans/{due_plan['planId']}/start",
        headers=headers,
    )
    assert started.status_code == 200
    assert started.json()["data"]["status"] == "IN_PROGRESS"

    completed = client.post(
        f"/api/question-bank/student/personal-bank/review-plans/{due_plan['planId']}/questions/question-seed-001/complete",
        headers=headers,
    )
    assert completed.status_code == 200
    completed_data = completed.json()["data"]
    completed_item = next(item for item in completed_data["items"] if item["questionId"] == "question-seed-001")
    assert completed_item["status"] == "COMPLETED"

    exported = client.get(
        "/api/question-bank/student/personal-bank/export",
        headers=headers,
        params={"format": "csv"},
    )
    assert exported.status_code == 200
    exported_content = exported.json()["data"]["content"]
    assert "question-seed-001" in exported_content
    assert "question-seed-002" in exported_content

    for _ in range(3):
        correct_submit = client.post(
            "/api/question-bank/student/practice/questions/question-seed-001/submit",
            headers=headers,
            json={"answer": "B", "elapsedSec": 20},
        )
        assert correct_submit.status_code == 200

    archived = client.post(
        "/api/question-bank/student/wrong-book/archive-harvested",
        headers=headers,
        json={"questionIds": ["question-seed-001"], "subjectCode": "POLITICS"},
    )
    assert archived.status_code == 200
    assert archived.json()["data"]["archivedCount"] == 1

    archived_list = client.get(
        "/api/question-bank/student/personal-bank/questions",
        headers=headers,
        params={"archiveWindow": "ARCHIVED", "page": 1, "size": 100},
    )
    assert archived_list.status_code == 200
    archived_ids = {item["id"] for item in archived_list.json()["data"]["items"]}
    assert "question-seed-001" in archived_ids

    restored = client.post(
        "/api/question-bank/student/wrong-book/restore-archived",
        headers=headers,
        json={"questionIds": ["question-seed-001"]},
    )
    assert restored.status_code == 200
    assert restored.json()["data"]["restoredCount"] == 1

    restored_summary = client.get(
        "/api/student/error-book/summary",
        headers=headers,
        params={"subjectCode": "POLITICS"},
    )
    assert restored_summary.status_code == 200
    restored_ids = {
        item["questionId"]
        for item in restored_summary.json()["data"]["questionInsights"]
    }
    assert "question-seed-001" in restored_ids
