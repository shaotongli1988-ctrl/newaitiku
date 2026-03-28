from __future__ import annotations

from decimal import Decimal
import io

import httpx
import pytest
from docx import Document


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def _weight_total(version: dict[str, object]) -> Decimal:
    weights = version.get("knowledgeWeights", []) if isinstance(version, dict) else []
    total = Decimal("0")
    for item in weights:
        if not isinstance(item, dict):
            continue
        total += Decimal(str(item.get("targetWeight", 0)))
    return total.quantize(Decimal("0.000001"))


def _build_equal_weight_payload(version: dict[str, object]) -> list[dict[str, object]]:
    weights = version.get("knowledgeWeights", []) if isinstance(version, dict) else []
    rows = [item for item in weights if isinstance(item, dict) and str(item.get("knowledgeId", "")).strip()]
    count = len(rows)
    if count <= 0:
        return []
    total_units = 1_000_000
    base_units = total_units // count
    remainder = total_units - (base_units * count)
    payload: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        payload.append(
            {
                "knowledgeId": str(row["knowledgeId"]),
                "targetWeight": (base_units + (1 if index < remainder else 0)) / total_units,
            }
        )
    return payload


def _build_syllabus_docx_bytes(lines: list[str]) -> bytes:
    document = Document()
    for line in lines:
        document.add_paragraph(line)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


async def test_admin_syllabus_requires_super_admin(
    async_client: httpx.AsyncClient,
    teacher_auth_headers: dict[str, str],
) -> None:
    unauthorized = await async_client.get("/api/question-bank/admin/syllabus")
    assert unauthorized.status_code in {401, 403}

    teacher_denied = await async_client.get(
        "/api/question-bank/admin/syllabus",
        headers=teacher_auth_headers,
    )
    assert teacher_denied.status_code == 403


async def test_admin_syllabus_default_version_weight_total_is_one(
    async_client: httpx.AsyncClient,
    admin_auth_headers: dict[str, str],
) -> None:
    response = await async_client.get("/api/question-bank/admin/syllabus", headers=admin_auth_headers)
    assert response.status_code == 200
    payload = response.json()["data"]

    versions = payload.get("versions", [])
    assert isinstance(versions, list)
    assert versions

    first_version = versions[0]
    assert isinstance(first_version, dict)
    assert first_version.get("knowledgeWeights")
    assert _weight_total(first_version) == Decimal("1.000000")
    assert str(payload.get("selectedVersionId", "")).strip()


async def test_admin_syllabus_create_version_and_save_weights(
    async_client: httpx.AsyncClient,
    admin_auth_headers: dict[str, str],
) -> None:
    list_response = await async_client.get("/api/question-bank/admin/syllabus", headers=admin_auth_headers)
    assert list_response.status_code == 200
    source_versions = list_response.json()["data"]["versions"]
    source_version_id = str(source_versions[0]["versionId"])

    create_response = await async_client.post(
        "/api/question-bank/admin/syllabus/versions",
        headers=admin_auth_headers,
        json={
            "versionName": "pytest-大纲版本",
            "copyFromVersionId": source_version_id,
        },
    )
    assert create_response.status_code == 200
    created_data = create_response.json()["data"]
    created_version = created_data["version"]
    created_version_id = str(created_version["versionId"])
    assert created_version_id

    invalid_weights_payload = [
        {
            "knowledgeId": str(item["knowledgeId"]),
            "targetWeight": 0,
        }
        for item in created_version["knowledgeWeights"]
    ]
    invalid_response = await async_client.post(
        f"/api/question-bank/admin/syllabus/{created_version_id}/weights",
        headers=admin_auth_headers,
        json={"knowledgeWeights": invalid_weights_payload},
    )
    assert invalid_response.status_code == 422
    assert "targetWeight 总和必须等于 1.0" in invalid_response.json()["message"]

    valid_payload = _build_equal_weight_payload(created_version)
    save_response = await async_client.post(
        f"/api/question-bank/admin/syllabus/{created_version_id}/weights",
        headers=admin_auth_headers,
        json={"knowledgeWeights": valid_payload},
    )
    assert save_response.status_code == 200
    saved_version = save_response.json()["data"]["version"]
    assert _weight_total(saved_version) == Decimal("1.000000")


async def test_admin_syllabus_ai_parse_requires_super_admin(
    async_client: httpx.AsyncClient,
    teacher_auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    list_response = await async_client.get("/api/question-bank/admin/syllabus", headers=admin_auth_headers)
    assert list_response.status_code == 200
    version_id = str(list_response.json()["data"]["versions"][0]["versionId"])

    docx_bytes = _build_syllabus_docx_bytes(["测试大纲：仅用于权限校验。"])
    teacher_response = await async_client.post(
        f"/api/question-bank/admin/syllabus/{version_id}/ai-parse",
        headers=teacher_auth_headers,
        files={
            "file": (
                "syllabus.docx",
                docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert teacher_response.status_code == 403


async def test_admin_syllabus_ai_parse_prefills_weights_by_docx(
    async_client: httpx.AsyncClient,
    admin_auth_headers: dict[str, str],
) -> None:
    list_response = await async_client.get("/api/question-bank/admin/syllabus", headers=admin_auth_headers)
    assert list_response.status_code == 200
    first_version = list_response.json()["data"]["versions"][0]
    version_id = str(first_version["versionId"])
    knowledge_rows = first_version["knowledgeWeights"]
    assert len(knowledge_rows) >= 2

    name_a = str(knowledge_rows[0]["knowledgeName"])
    name_b = str(knowledge_rows[1]["knowledgeName"])
    docx_bytes = _build_syllabus_docx_bytes(
        [
            "2026 专升本大纲（测试样例）",
            f"{name_a}：60%",
            f"{name_b}：40%",
            "其余知识点按课程占比作为补充。",
        ]
    )
    parse_response = await async_client.post(
        f"/api/question-bank/admin/syllabus/{version_id}/ai-parse",
        headers=admin_auth_headers,
        files={
            "file": (
                "syllabus.docx",
                docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert parse_response.status_code == 200
    payload = parse_response.json()["data"]
    assert str(payload.get("versionId", "")) == version_id
    prefilled_rows = payload.get("knowledgeWeights", [])
    assert isinstance(prefilled_rows, list)
    assert len(prefilled_rows) == len(knowledge_rows)

    total = sum(Decimal(str(item.get("targetWeight", 0))) for item in prefilled_rows if isinstance(item, dict))
    assert total.quantize(Decimal("0.000001")) == Decimal("1.000000")

    prefilled_map = {
        str(item.get("knowledgeId", "")): Decimal(str(item.get("targetWeight", 0)))
        for item in prefilled_rows
        if isinstance(item, dict)
    }
    assert prefilled_map[str(knowledge_rows[0]["knowledgeId"])] > prefilled_map[str(knowledge_rows[1]["knowledgeId"])]
    report = payload.get("parserReport", {})
    assert report.get("extractTextLength", 0) > 0
    assert str(report.get("parserMode", "")).strip()


async def test_admin_syllabus_ai_parse_rejects_invalid_suffix(
    async_client: httpx.AsyncClient,
    admin_auth_headers: dict[str, str],
) -> None:
    list_response = await async_client.get("/api/question-bank/admin/syllabus", headers=admin_auth_headers)
    assert list_response.status_code == 200
    version_id = str(list_response.json()["data"]["versions"][0]["versionId"])

    response = await async_client.post(
        f"/api/question-bank/admin/syllabus/{version_id}/ai-parse",
        headers=admin_auth_headers,
        files={"file": ("syllabus.txt", b"plain text", "text/plain")},
    )
    assert response.status_code == 422
    assert "仅支持 PDF、DOC、DOCX" in response.json()["message"]
