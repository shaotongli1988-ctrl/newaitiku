from __future__ import annotations

import io
import zipfile
from pathlib import Path

import app.service_shared as service_shared
from tests.support import make_client, teacher_headers


def _batch_parse_template_text() -> str:
    return "\n".join(
        [
            "【题型】single_choice",
            "【题干】计算机系统中最核心的组成部分是什么？",
            "【选项】A.CPU|B.显示器|C.键盘|D.鼠标",
            "【答案】A",
            "【解析】CPU 负责指令执行与数据处理。",
            "【知识点】计算机基础",
        ]
    )


def _build_docx_with_embedded_image_bytes() -> bytes:
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p />
  </w:body>
</w:document>
"""
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/word/document.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""
    relationships = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="word/document.xml"/>
</Relationships>
"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/media/image1.png", b"fake-png-bytes")
    return buffer.getvalue()


def test_batch_parse_returns_2026_structured_payload(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    response = client.post(
        "/api/question-bank/batch-parse",
        headers=teacher_headers("teacher-002"),
        data={
            "examCategoryCode": "SCIENCE_ENGINEERING",
            "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
            "subjectCode": "INFO_TECH_INTRO",
        },
        files={
            "file": ("batch-parse.txt", _batch_parse_template_text().encode("utf-8"), "text/plain"),
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("code") == "OK"
    data = payload.get("data", {})
    assert data.get("policy_version") == "HB_ZSB_2026"
    assert data.get("exam_category_code") == "SCIENCE_ENGINEERING"
    assert data.get("joint_exam_group_code") == "SCIENCE_ENGINEERING_3"
    assert data.get("subject_code") == "INFO_TECH_INTRO"
    assert data.get("valid_count") == 1
    assert data.get("invalid_count") == 0

    items = data.get("items", [])
    assert isinstance(items, list) and len(items) == 1
    first_item = items[0]
    assert first_item.get("policy_version") == "HB_ZSB_2026"
    assert first_item.get("joint_exam_group_code") == "SCIENCE_ENGINEERING_3"
    assert first_item.get("subject_code") == "INFO_TECH_INTRO"
    assert str(first_item.get("subject_type", "")).startswith("PROFESSIONAL")
    assert first_item.get("knowledge_points") == ["计算机基础"]


def test_batch_parse_normalizes_math_and_chem_formula_text(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    content = "\n".join(
        [
            "【题型】subjective",
            "【题干】已知 x² + 1 = 0，且溶液中含有 H₂SO₄ 与 SO₄²⁻，请写出反应方向：2H₂ + O₂ → 2H₂O。",
            "【答案】x = ±i，化学方程式可线性书写。",
            "【解析】系统应将上标、下标和箭头统一成更稳定的文本形式。",
            "【知识点】计算机基础",
        ]
    )
    response = client.post(
        "/api/question-bank/batch-parse",
        headers=teacher_headers("teacher-002"),
        data={
            "examCategoryCode": "SCIENCE_ENGINEERING",
            "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
            "subjectCode": "INFO_TECH_INTRO",
        },
        files={
            "file": ("batch-parse.txt", content.encode("utf-8"), "text/plain"),
        },
    )
    assert response.status_code == 200
    item = response.json()["data"]["items"][0]
    assert "x^2" in str(item.get("content", ""))
    assert "H2SO4" in str(item.get("content", ""))
    assert "SO4^2-" in str(item.get("content", ""))
    assert "2H2 + O2 -> 2H2O" in str(item.get("content", ""))


def test_batch_parse_keeps_multiline_english_stem_and_long_options(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    content = "\n".join(
        [
            "【题型】single_choice",
            "【题干】Read the passage and choose the best answer.",
            "This line continues the same English stem with f(x)=x^2+1.",
            "【选项】A.The function keeps increasing on x > 0",
            "because f'(x)=2x remains positive in this interval.",
            "B.The function is a constant.",
            "C.The function has no derivative.",
            "D.None of the above.",
            "【答案】A",
            "【解析】The parser should keep multiline English content in the same question.",
            "【知识点】计算机基础",
        ]
    )
    response = client.post(
        "/api/question-bank/batch-parse",
        headers=teacher_headers("teacher-002"),
        data={
            "examCategoryCode": "SCIENCE_ENGINEERING",
            "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
            "subjectCode": "INFO_TECH_INTRO",
        },
        files={
            "file": ("batch-parse.txt", content.encode("utf-8"), "text/plain"),
        },
    )
    assert response.status_code == 200
    item = response.json()["data"]["items"][0]
    assert "f(x)=x^2+1" in str(item.get("content", ""))
    assert "\nThis line continues the same English stem" in str(item.get("content", ""))
    options = item.get("options", [])
    assert len(options) == 4
    assert "f'(x)=2x" in str(options[0].get("content", ""))


def test_batch_parse_uses_docx_image_ocr_fallback_for_formula_content(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path)
    monkeypatch.setattr(
        client.app.state.service,
        "_run_ocr_tesseract",
        lambda _image_path, _lang: "\n".join(
            [
                "【题型】subjective",
                "【题干】若 x² + 1 = 0，请写出复数根，并补充化学式 H₂O。",
                "【答案】x = ±i，H2O 为水。",
                "【解析】当 Word 中只有截图公式时，OCR 应提供兜底文本。",
                "【知识点】计算机基础",
            ]
        ),
        raising=False,
    )
    response = client.post(
        "/api/question-bank/batch-parse",
        headers=teacher_headers("teacher-002"),
        data={
            "examCategoryCode": "SCIENCE_ENGINEERING",
            "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
            "subjectCode": "INFO_TECH_INTRO",
        },
        files={
            "file": (
                "batch-parse.docx",
                _build_docx_with_embedded_image_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        },
    )
    assert response.status_code == 200
    item = response.json()["data"]["items"][0]
    assert "x^2" in str(item.get("content", ""))
    assert "H2O" in str(item.get("content", ""))


def test_batch_parse_prefers_local_formula_engine_when_available(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path)
    monkeypatch.setattr(
        client.app.state.service,
        "_run_local_formula_ocr",
        lambda _image_path: (
            "\n".join(
                [
                    "【题型】subjective",
                    "【题干】求极限 lim x->0 (sin x)/x，并补充化学式 SO₄²⁻。",
                    "【答案】极限为 1，离子写作 SO4^2-。",
                    "【解析】本地公式引擎应优先识别公式图片，再统一做公式文本规范化。",
                    "【知识点】计算机基础",
                ]
            ),
            "pix2tex",
        ),
        raising=False,
    )
    monkeypatch.setattr(
        client.app.state.service,
        "_run_ocr_tesseract",
        lambda _image_path, _lang: "",
        raising=False,
    )
    response = client.post(
        "/api/question-bank/batch-parse",
        headers=teacher_headers("teacher-002"),
        data={
            "examCategoryCode": "SCIENCE_ENGINEERING",
            "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
            "subjectCode": "INFO_TECH_INTRO",
        },
        files={
            "file": (
                "batch-parse.docx",
                _build_docx_with_embedded_image_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        },
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    item = payload["items"][0]
    assert "SO4^2-" in str(item.get("content", ""))
    parser_report = payload.get("parserReport", {})
    assert parser_report.get("extractMethod") == "python-docx+pix2tex"
    assert parser_report.get("imageFormulaOcrEngines") == ["pix2tex"]


def test_batch_parse_collects_cloud_and_local_chemistry_engine_results(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path)
    monkeypatch.setattr(
        client.app.state.service,
        "_run_local_formula_ocr",
        lambda _image_path: ("", ""),
        raising=False,
    )
    monkeypatch.setattr(
        client.app.state.service,
        "_run_mathpix_chem_ocr",
        lambda _image_path: ("SMILES: O=S(=O)(O)O", "mathpix"),
        raising=False,
    )
    monkeypatch.setattr(
        client.app.state.service,
        "_run_local_chem_structure_ocr",
        lambda _image_path: ("Molvec molfile preview", "molvec"),
        raising=False,
    )
    monkeypatch.setattr(
        client.app.state.service,
        "_run_ocr_tesseract",
        lambda _image_path, _lang: "",
        raising=False,
    )
    response = client.post(
        "/api/question-bank/batch-parse",
        headers=teacher_headers("teacher-002"),
        data={
            "examCategoryCode": "SCIENCE_ENGINEERING",
            "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
            "subjectCode": "INFO_TECH_INTRO",
        },
        files={
            "file": (
                "batch-parse.docx",
                _build_docx_with_embedded_image_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        },
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    item = payload["items"][0]
    assert "SMILES: O=S(=O)(O)O" in str(item.get("content", ""))
    parser_report = payload.get("parserReport", {})
    assert parser_report.get("imageChemicalOcrEngines") == ["mathpix", "molvec"]
    assert parser_report.get("extractMethod") == "python-docx+mathpix/molvec"
    samples = parser_report.get("imageChemicalOcrSamples", [])
    assert isinstance(samples, list) and len(samples) == 2


def test_batch_parse_rejects_mismatched_scope(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    response = client.post(
        "/api/question-bank/batch-parse",
        headers=teacher_headers("teacher-002"),
        data={
            "examCategoryCode": "SCIENCE_ENGINEERING",
            "jointExamGroupCode": "LITERATURE_1",
            "subjectCode": "INFO_TECH_INTRO",
        },
        files={
            "file": ("batch-parse.txt", _batch_parse_template_text().encode("utf-8"), "text/plain"),
        },
    )
    assert response.status_code == 422


def test_batch_parse_returns_424_when_docx_dependency_missing(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path)
    monkeypatch.setattr(service_shared, "is_docx_available", lambda: False)
    response = client.post(
        "/api/question-bank/batch-parse",
        headers=teacher_headers("teacher-002"),
        data={
            "examCategoryCode": "SCIENCE_ENGINEERING",
            "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
            "subjectCode": "INFO_TECH_INTRO",
        },
        files={
            "file": (
                "batch-parse.docx",
                b"fake-docx-content",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        },
    )
    assert response.status_code == 424
    payload = response.json()
    assert str(payload.get("code", "")).strip() == "QUESTION_DEPENDENCY_FAILED"
