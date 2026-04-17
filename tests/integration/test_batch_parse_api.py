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


def _collapse_to_two_level_tags(labels: list[str]) -> list[str]:
    normalized = [str(item or "").strip() for item in labels if str(item or "").strip()]
    if not normalized:
        return []
    if len(normalized) <= 2:
        return normalized
    generic_labels = {
        "具体内容与要求",
        "科目简介",
        "考试说明",
        "考试要求",
        "课程简介",
        "课程说明",
        "复习建议",
    }
    root = normalized[0]
    second = next((item for item in normalized[1:] if item not in generic_labels), normalized[1])
    return [root] if second == root else [root, second]


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
    knowledge_points = first_item.get("knowledge_points") or []
    assert isinstance(knowledge_points, list) and len(knowledge_points) >= 1


def test_batch_parse_decodes_gb18030_txt_upload(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    unique_stem = "\u7f16\u7801\u56de\u5f52GB18030\u9898\u5e72\u6d4b\u8bd5"
    content = "\n".join(
        [
            "\u3010\u9898\u578b\u3011single_choice",
            f"\u3010\u9898\u5e72\u3011{unique_stem}",
            "\u3010\u9009\u9879\u3011A.\u652f\u6301|B.\u4e0d\u652f\u6301",
            "\u3010\u7b54\u6848\u3011A",
            "\u3010\u89e3\u6790\u3011GB18030 \u6587\u672c\u7f16\u7801\u89e3\u6790\u9a8c\u8bc1",
            "\u3010\u77e5\u8bc6\u70b9\u3011\u8ba1\u7b97\u673a\u57fa\u7840",
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
            "file": ("batch-parse.txt", content.encode("gb18030"), "text/plain"),
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("code") == "OK"
    data = payload.get("data", {})
    assert data.get("valid_count") == 1
    assert data.get("invalid_count") == 0
    first_item = (data.get("items") or [{}])[0]
    assert str(first_item.get("content", "")).strip() == unique_stem
    assert str(first_item.get("analysis", "")).strip().startswith("GB18030")


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


def test_batch_parse_maps_bracket_knowledge_hint_to_knowledge_path(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    svc = client.app.state.service
    scope = {
        "examCategoryCode": "SCIENCE_ENGINEERING",
        "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
        "subjectCode": "INFO_TECH_INTRO",
        "policyVersionCode": "HB_ZSB_2026",
    }
    semantic_pool = svc._build_question_semantic_pool(scope)
    target = next(
        (
            item
            for item in semantic_pool
            if int(item.get("level", 0) or 0) >= 5 and isinstance(item.get("path_levels", []), list)
        ),
        None,
    )
    assert target is not None
    hint_path = " -> ".join(
        str(level.get("label", "")).strip()
        for level in target.get("path_levels", [])
        if str(level.get("label", "")).strip()
    )
    assert hint_path

    content = "\n".join(
        [
            "[type] single_choice",
            "[content] Which component is the core of a computer system?",
            "[options] A.CPU|B.Display|C.Keyboard|D.Mouse",
            "[answer] A",
            "[analysis] CPU is responsible for instruction execution and data processing.",
            f"[knowledge] {hint_path}",
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
    payload = response.json().get("data", {})
    item = (payload.get("items") or [{}])[0]
    assert str(item.get("pointCode", "")).strip() == str(target.get("pointCode", "")).strip()
    assert len(item.get("knowledge_path") or []) >= 1
    assert bool(item.get("manual_review_required")) is False


def test_batch_parse_collapses_knowledge_path_and_tags_to_two_levels(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    svc = client.app.state.service
    scope = {
        "examCategoryCode": "LITERATURE",
        "jointExamGroupCode": "LITERATURE_1",
        "subjectCode": "ARTS_HISTORY_FOUNDATION",
        "policyVersionCode": "HB_ZSB_2026",
    }
    semantic_pool = svc._build_question_semantic_pool(scope)
    target = max(
        (
            item
            for item in semantic_pool
            if isinstance(item.get("path_levels", []), list) and len(item.get("path_levels", [])) >= 2
        ),
        key=lambda item: len(item.get("path_levels", [])),
        default=None,
    )
    assert target is not None
    hint_labels = [
        str(level.get("label", "")).strip()
        for level in target.get("path_levels", [])
        if str(level.get("label", "")).strip()
    ]
    assert len(hint_labels) >= 2
    expected_tags = _collapse_to_two_level_tags(hint_labels)
    assert 1 <= len(expected_tags) <= 2

    content = "\n".join(
        [
            "[type] single_choice",
            "[content] 距今约7000至5000年前，黄河中游地区粟为主要栽培作物的时期是（   ）",
            "[options] A.大汶口文化|B.仰韶文化|C.北京人|D.河姆渡文化",
            "[answer] B",
            "[analysis] 题干对应新石器时代黄河中游农业文化。",
            f"[knowledge] {' -> '.join(hint_labels)}",
        ]
    )
    response = client.post(
        "/api/question-bank/batch-parse",
        headers=teacher_headers("teacher-002"),
        data={
            "examCategoryCode": "LITERATURE",
            "jointExamGroupCode": "LITERATURE_1",
            "subjectCode": "ARTS_HISTORY_FOUNDATION",
        },
        files={
            "file": ("batch-parse.txt", content.encode("utf-8"), "text/plain"),
        },
    )
    assert response.status_code == 200
    payload = response.json().get("data", {})
    item = (payload.get("items") or [{}])[0]
    assert bool(item.get("manual_review_required")) is False
    assert 1 <= len(item.get("knowledge_path") or []) <= 2
    assert item.get("knowledge_tags") == expected_tags
    assert item.get("path_label") == " / ".join(expected_tags)
    ext_json = item.get("ext_json", {})
    assert isinstance(ext_json, dict)
    assert ext_json.get("knowledgeTags") == expected_tags


def test_batch_parse_fallback_subject_semantic_pool_for_shared_subject(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    content = "\n".join(
        [
            "[type] single_choice",
            "[content] 距今约7000至5000年前，黄河中游地区粟为主要栽培作物的时期是（   ）",
            "[options] A.大汶口文化|B.仰韶文化|C.北京人|D.河姆渡文化",
            "[answer] B",
            "[analysis] 题干对应史前文化相关内容。",
            "[knowledge] 文史基础 -> 具体内容与要求 -> 中国古代史 -> 史前文化 -> 了解仰韶文化",
        ]
    )
    # ARTS_HISTORY_FOUNDATION is shared across groups. Some seeded nodes are scoped
    # to EDUCATION_3; parser should still fallback by subject code when current group
    # has no direct semantic pool rows.
    response = client.post(
        "/api/question-bank/batch-parse",
        headers=teacher_headers("teacher-002"),
        data={
            "examCategoryCode": "LITERATURE",
            "jointExamGroupCode": "LITERATURE_1",
            "subjectCode": "ARTS_HISTORY_FOUNDATION",
        },
        files={
            "file": ("batch-parse.txt", content.encode("utf-8"), "text/plain"),
        },
    )
    assert response.status_code == 200
    payload = response.json().get("data", {})
    item = (payload.get("items") or [{}])[0]
    assert str(item.get("pointCode", "")).strip()
    assert len(item.get("knowledge_path") or []) >= 1
    assert bool(item.get("manual_review_required")) is False


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
