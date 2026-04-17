from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from tests.support import POLITICS_POINT_ID, make_client, payload, teacher_headers


def test_batch_create_is_idempotent_for_same_source_task_and_preview_ids(tmp_path: Path):
    client = make_client(tmp_path)
    marker = f"idempotency-{uuid4().hex[:8]}"
    source_task_id = f"task-{marker}"

    item_a = payload()
    item_a["title"] = f"{marker}-A"
    item_a["content"] = f"{marker} content A"
    item_a["extJson"] = {"batchPreviewId": "preview-a"}

    item_b = payload()
    item_b["title"] = f"{marker}-B"
    item_b["content"] = f"{marker} content B"
    item_b["extJson"] = {"batchPreviewId": "preview-b"}

    request_payload = {
        "items": [item_a, item_b],
        "sourceTaskId": source_task_id,
    }

    first_response = client.post(
        "/api/question-bank/batch-create",
        headers=teacher_headers(),
        json=request_payload,
    )
    assert first_response.status_code == 200
    first_data = first_response.json()["data"]
    assert int(first_data["failedCount"]) == 0
    first_ids = sorted(str(item.get("id", "")).strip() for item in first_data["items"] if str(item.get("id", "")).strip())
    assert len(first_ids) == 2

    second_response = client.post(
        "/api/question-bank/batch-create",
        headers=teacher_headers(),
        json=request_payload,
    )
    assert second_response.status_code == 200
    second_data = second_response.json()["data"]
    assert int(second_data["failedCount"]) == 0
    second_ids = sorted(str(item.get("id", "")).strip() for item in second_data["items"] if str(item.get("id", "")).strip())
    assert second_ids == first_ids

    list_response = client.get(
        "/api/question-bank/questions",
        headers=teacher_headers(),
        params={"keyword": marker, "userId": "teacher-001", "size": 100},
    )
    assert list_response.status_code == 200
    items = list_response.json()["data"]["items"]
    matched_ids = {str(item.get("id", "")).strip() for item in items if marker in str(item.get("stem", ""))}
    assert matched_ids == set(first_ids)


def test_batch_create_auto_creates_knowledge_from_text_hints(tmp_path: Path):
    client = make_client(tmp_path)
    marker = f"auto-knowledge-{uuid4().hex[:8]}"
    request_item = payload()
    request_item["title"] = f"{marker}-title"
    request_item["content"] = f"{marker} content"
    request_item["knowledgePoints"] = ["文史基础 -> 中国古代史"]
    request_item["extJson"] = {
        "batchPreviewId": f"{marker}-preview",
        "pathLabel": "文史基础 / 中国古代史",
        "batchKnowledgeHints": ["文史基础 -> 中国古代史"],
    }

    response = client.post(
        "/api/question-bank/batch-create",
        headers=teacher_headers(),
        json={"items": [request_item], "sourceTaskId": f"task-{marker}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert int(data["failedCount"]) == 0
    assert int(data["createdCount"]) == 1

    created_item = data["items"][0]
    ext_json = created_item.get("extJson")
    if isinstance(ext_json, str):
        ext_json = json.loads(ext_json)
    assert isinstance(ext_json, dict)

    knowledge_id = str(created_item.get("knowledgeId", "")).strip()
    assert knowledge_id
    assert isinstance(ext_json.get("knowledgePointIds"), list)
    assert ext_json.get("knowledgePointIds")[0] == knowledge_id
    assert ext_json.get("autoResolvedKnowledge") is True
    assert isinstance(ext_json.get("autoCreatedKnowledgePath"), list)

    knowledge = client.app.state.service.repository.get_knowledge(knowledge_id)
    assert knowledge is not None
    assert str(knowledge.get("status", "")).strip() == "ENABLED"


def test_batch_create_reuses_existing_knowledge_when_hint_matches_existing_path(tmp_path: Path):
    client = make_client(tmp_path)
    marker = f"reuse-knowledge-{uuid4().hex[:8]}"
    svc = client.app.state.service
    point = svc.repository.get_knowledge(POLITICS_POINT_ID)
    assert point is not None
    chapter = svc.repository.get_knowledge(str(point.get("parentId", "")).strip())
    assert chapter is not None
    hint_path = f"{chapter['name']} -> {point['name']}"

    request_item = payload()
    request_item["title"] = f"{marker}-title"
    request_item["content"] = f"{marker} content"
    request_item["knowledgePoints"] = [hint_path]
    request_item["extJson"] = {
        "batchPreviewId": f"{marker}-preview",
        "batchKnowledgeHints": [hint_path],
    }

    response = client.post(
        "/api/question-bank/batch-create",
        headers=teacher_headers(),
        json={"items": [request_item], "sourceTaskId": f"task-{marker}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert int(data["failedCount"]) == 0
    assert int(data["createdCount"]) == 1
    created_item = data["items"][0]
    assert str(created_item.get("knowledgeId", "")).strip() == POLITICS_POINT_ID
