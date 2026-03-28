from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from app.db import get_connection
from tests.support import make_client


def load_backfill_module():
    root = Path(__file__).resolve().parents[2]
    module_path = root / "scripts/extjson_hot_state_backfill.py"
    spec = importlib.util.spec_from_file_location("extjson_hot_state_backfill", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_audit_hot_state_consistency_detects_missing_formal_rows(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    repo = client.app.state.service.repository
    record = repo.get_student_question_bank("question-seed-001", "student-001")
    assert record is not None
    record_ext = json.loads(record["extJson"])
    record_ext["chapterPractice"] = {
        "lastAnswer": "B",
        "isCorrect": True,
        "answerDurationSec": 60,
        "submitCount": 1,
        "correctCount": 1,
        "submittedAt": "2026-03-22T08:00:00Z",
    }
    repo.upsert_student_question_bank({**record, "extJson": json.dumps(record_ext, ensure_ascii=False)})

    with get_connection(repo.db_path) as connection:
        row = connection.execute('SELECT extJson FROM "user" WHERE id = ?', ("student-001",)).fetchone()
        assert row is not None
        student_ext_json = json.loads(str(row["extJson"]))
        student_ext_json["studentRecords"] = {
            "question-seed-001": {
                "id": record["id"],
                "status": record["status"],
                "extJson": record_ext,
            }
        }
        connection.execute(
            'UPDATE "user" SET extJson = ? WHERE id = ?',
            (json.dumps(student_ext_json, ensure_ascii=False), "student-001"),
        )
        connection.execute("DELETE FROM student_question_record")
        connection.commit()

    backfill = load_backfill_module()
    report = backfill.audit_hot_state_consistency(repo.db_path)
    assert report["ok"] is False
    assert report["studentQuestionRecord"]["missingInFormal"]


def test_run_backfill_restores_consistency_after_formal_rows_are_deleted(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    repo = client.app.state.service.repository

    sent = client.post(
        "/api/question-bank/messages/send",
        headers={"X-Role": "teacher", "X-User-Id": "teacher-001"},
        json={
            "targetMode": "userIds",
            "userIds": ["student-001"],
            "category": "SYSTEM_NOTICE",
            "title": "回填校验",
            "content": "需要补回发送历史。",
        },
    )
    assert sent.status_code == 200

    submit = client.post(
        "/api/question-bank/student/papers/paper-demo-001/submit",
        headers={"X-Role": "student", "X-User-Id": "student-001"},
        json={
            "answers": [
                {"questionId": "question-seed-001", "answer": "B", "elapsedSec": 35, "marked": False},
                {"questionId": "question-seed-002", "answer": "ABC", "elapsedSec": 45, "marked": True},
            ],
            "totalElapsedSec": 80,
        },
    )
    assert submit.status_code == 200
    report_id = submit.json()["data"]["reportId"]

    student_record = repo.get_student_question_bank("question-seed-001", "student-001")
    assert student_record is not None
    paper_report = repo.get_paper_report_payload(report_id)
    assert paper_report is not None
    history_item = repo.get_message_send_history_payload(sent.json()["data"]["traceId"])
    assert history_item is not None

    with get_connection(repo.db_path) as connection:
        student_row = connection.execute('SELECT extJson FROM "user" WHERE id = ?', ("student-001",)).fetchone()
        assert student_row is not None
        student_ext_json = json.loads(str(student_row["extJson"]))
        student_ext_json["studentRecords"] = {
            "question-seed-001": {
                "id": student_record["id"],
                "status": student_record["status"],
                "extJson": json.loads(student_record["extJson"]),
            }
        }
        connection.execute(
            'UPDATE "user" SET extJson = ? WHERE id = ?',
            (json.dumps(student_ext_json, ensure_ascii=False), "student-001"),
        )

        system_row = connection.execute('SELECT extJson FROM "user" WHERE id = ?', ("__system__",)).fetchone()
        assert system_row is not None
        system_ext_json = json.loads(str(system_row["extJson"]))
        system_ext_json["paperReports"] = [paper_report]
        system_ext_json["messageSendHistory"] = [history_item]
        connection.execute(
            'UPDATE "user" SET extJson = ? WHERE id = ?',
            (json.dumps(system_ext_json, ensure_ascii=False), "__system__"),
        )
        connection.execute("DELETE FROM student_question_record")
        connection.execute("DELETE FROM paper_report")
        connection.execute("DELETE FROM message_send_history")
        connection.commit()

    backfill = load_backfill_module()
    report = backfill.run_backfill(repo.db_path)
    assert report["ok"] is True
    assert report["studentQuestionRecord"]["legacyCount"] >= 1
    assert report["paperReport"]["legacyCount"] >= 1
    assert report["messageSendHistory"]["legacyCount"] >= 1
