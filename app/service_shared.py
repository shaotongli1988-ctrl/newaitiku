from __future__ import annotations

import csv
import io
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
import zipfile
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union
from xml.etree import ElementTree as ET

import httpx

from app.auth import Actor
from app.content_baseline import (
    PUBLIC_SUBJECTS,
    JOINT_EXAM_GROUPS,
    POLICY_VERSION_CODE,
    all_joint_exam_group_codes,
    build_content_baseline,
    get_exam_category,
    get_joint_exam_group,
    level_code_from_level,
    level_path_from_level,
    list_joint_exam_groups,
    subject_applicable_group_codes,
    subject_id_from_subject_code,
)
from app.contracts import (
    ALL_ROLES,
    AdaptivePracticeRequest,
    MANAGED_PERMISSION_KEYS,
    MESSAGE_CATEGORIES,
    ROLE_TEACHER,
    ROLE_STUDENT,
    ROLE_SUPER_ADMIN,
    TASK_STATUSES,
    TASK_TYPES,
    normalize_role,
)
from app.exceptions import (
    failed_dependency,
    forbidden,
    invalid_status,
    not_found,
    profile_incomplete,
    task_forbidden,
    task_not_found,
    task_validation_failed,
    validation_failed,
)
from app.models import (
    parse_knowledge_model,
    parse_auth_login_password_model,
    parse_auth_login_sms_model,
    parse_auth_password_reset_model,
    parse_auth_register_model,
    parse_sms_code_request_model,
    parse_managed_user_model,
    parse_ai_marking_submit_model,
    parse_ai_tutor_ask_model,
    parse_message_settings_model,
    parse_batch_question_delete_model,
    parse_batch_question_status_model,
    parse_paper_auto_model,
    parse_paper_manual_model,
    parse_paper_template_model,
    parse_paper_submit_model,
    parse_practice_submit_model,
    parse_question_model,
    parse_send_message_model,
    parse_status_transition_payload_model,
    parse_student_profile_model,
    parse_student_submit_model,
    parse_syllabus_version_create_model,
    parse_syllabus_weights_save_model,
    parse_system_settings_model,
)
from app.repository import QuestionRepository

QUESTION_ALLOWED_TRANSITIONS = {
    "DRAFT": ["QA_IN_PROGRESS", "REVIEW_PENDING", "REJECTED"],
    "QA_IN_PROGRESS": ["REVIEW_PENDING", "REJECTED"],
    "REVIEW_PENDING": ["PUBLISHED", "REJECTED"],
    "REJECTED": ["DRAFT"],
    "PUBLISHED": [],
}

ALLOWED_TRANSITIONS = {
    "DRAFT": {"QA_IN_PROGRESS", "REVIEW_PENDING", "REJECTED"},
    "QA_IN_PROGRESS": {"REVIEW_PENDING", "REJECTED"},
    "REVIEW_PENDING": {"PUBLISHED", "REJECTED"},
    "REJECTED": {"DRAFT"},
    "PUBLISHED": set(),
}


def canTransitionQuestionStatus(current_status: str, target_status: str) -> bool:
    normalized_current_status = str(current_status or "").strip()
    normalized_target_status = str(target_status or "").strip()
    return normalized_target_status in QUESTION_ALLOWED_TRANSITIONS.get(normalized_current_status, [])

PAPER_ALLOWED_STATUSES = {"DRAFT", "REVIEW_PENDING", "PUBLISHED", "OFFLINE"}
PAPER_STATUS_TRANSITIONS = {
    "DRAFT": {"REVIEW_PENDING"},
    "REVIEW_PENDING": {"DRAFT", "PUBLISHED"},
    "PUBLISHED": {"OFFLINE"},
    "OFFLINE": {"REVIEW_PENDING"},
}
SYSTEM_RECORD_USER_ID = "__system__"
PUBLIC_SUBJECT_CODE_BY_SUBJECT_ID = {
    "subject-politics": "POLITICS",
    "subject-english": "ENGLISH",
}
QUESTION_IMPORT_SUFFIXES = (".txt", ".docx")
PAPER_EXPORT_FORMATS = {"txt", "pdf", "word"}
ANALYTICS_EXPORT_FORMATS = {"csv", "pdf"}
PERSONAL_BANK_EXPORT_FORMATS = {"csv", "pdf"}
STUDENT_DIRECTORY_EXPORT_FORMATS = {"csv", "pdf"}
PASSWORD_LOGIN_FAIL_WINDOW_SEC = 600
PASSWORD_LOGIN_FAIL_LOCK_SEC = 600
PASSWORD_LOGIN_MAX_FAIL_PER_PHONE = 5
PASSWORD_LOGIN_MAX_FAIL_PER_IP = 20
SYLLABUS_WEIGHT_SCALE = 1_000_000
SYLLABUS_AI_IMPORT_SUFFIXES = (".pdf", ".doc", ".docx")
SYLLABUS_AI_MAX_FILE_SIZE = 10 * 1024 * 1024

_DOCX_MISSING_MESSAGE = (
    "当前环境缺少 python-docx 依赖，无法解析 Word 文件。"
    "请先安装 python-docx 后重试。"
)
_DOCX_XML_NAMESPACES = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}
_QUESTION_OPTION_LINE_PATTERN = re.compile(r"^[\(（]?([A-Z])(?:[\)）][\.\:：、．]?|[\.\:：、．])\s*(.*)$")
_FORMULA_SUPERSCRIPT_CHAR_MAP = {
    "⁰": "0",
    "¹": "1",
    "²": "2",
    "³": "3",
    "⁴": "4",
    "⁵": "5",
    "⁶": "6",
    "⁷": "7",
    "⁸": "8",
    "⁹": "9",
    "⁺": "+",
    "⁻": "-",
    "⁼": "=",
    "⁽": "(",
    "⁾": ")",
    "ⁿ": "n",
    "ᵃ": "a",
    "ᵇ": "b",
    "ᶜ": "c",
    "ᵈ": "d",
    "ᵉ": "e",
    "ᶠ": "f",
    "ᵍ": "g",
    "ʰ": "h",
    "ᶦ": "i",
    "ʲ": "j",
    "ᵏ": "k",
    "ˡ": "l",
    "ᵐ": "m",
    "ᵒ": "o",
    "ᵖ": "p",
    "ʳ": "r",
    "ˢ": "s",
    "ᵗ": "t",
    "ᵘ": "u",
    "ᵛ": "v",
    "ʷ": "w",
    "ˣ": "x",
    "ʸ": "y",
    "ᶻ": "z",
}
_FORMULA_SUBSCRIPT_CHAR_MAP = {
    "₀": "0",
    "₁": "1",
    "₂": "2",
    "₃": "3",
    "₄": "4",
    "₅": "5",
    "₆": "6",
    "₇": "7",
    "₈": "8",
    "₉": "9",
    "₊": "+",
    "₋": "-",
    "₌": "=",
    "₍": "(",
    "₎": ")",
    "ₐ": "a",
    "ₑ": "e",
    "ₕ": "h",
    "ᵢ": "i",
    "ⱼ": "j",
    "ₖ": "k",
    "ₗ": "l",
    "ₘ": "m",
    "ₙ": "n",
    "ₒ": "o",
    "ₚ": "p",
    "ᵣ": "r",
    "ₛ": "s",
    "ₜ": "t",
    "ᵤ": "u",
    "ᵥ": "v",
    "ₓ": "x",
}
_FORMULA_SUPERSCRIPT_PATTERN = re.compile(
    "[" + re.escape("".join(_FORMULA_SUPERSCRIPT_CHAR_MAP.keys())) + "]+"
)
_FORMULA_SUBSCRIPT_PATTERN = re.compile(
    "[" + re.escape("".join(_FORMULA_SUBSCRIPT_CHAR_MAP.keys())) + "]+"
)
_FORMULA_SYMBOL_REPLACEMENTS = {
    "→": "->",
    "⟶": "->",
    "⟹": "=>",
    "←": "<-",
    "⇌": "<->",
    "⇄": "<->",
    "↔": "<->",
    "−": "-",
    "—": "-",
    "–": "-",
    "×": "*",
    "÷": "/",
    "∶": ":",
    "·": "·",
    "•": "·",
    "⋅": "·",
    "\u00a0": " ",
    "\u200b": "",
    "\ufeff": "",
}


def is_docx_available() -> bool:
    try:
        from docx import Document as _Document  # type: ignore
    except Exception:
        return False
    return callable(_Document)


def _xml_local_name(tag: str) -> str:
    return str(tag or "").rsplit("}", 1)[-1]


def _collect_docx_element_text(element: ET.Element) -> str:
    fragments: List[str] = []
    for node in element.iter():
        local_name = _xml_local_name(str(node.tag))
        if local_name in {"t", "instrText", "delText"}:
            text = str(node.text or "")
            if text:
                fragments.append(text)
            continue
        if local_name == "tab":
            fragments.append("\t")
            continue
        if local_name in {"br", "cr"}:
            if not fragments or fragments[-1] != "\n":
                fragments.append("\n")
    text = "".join(fragments)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_docx_document_text(file_bytes: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
            document_xml = archive.read("word/document.xml")
    except Exception as exc:
        raise validation_failed("DOCX 文件解析失败，请检查文件格式后重试。") from exc

    try:
        root = ET.fromstring(document_xml)
    except Exception as exc:
        raise validation_failed("DOCX 文件解析失败，请检查文件格式后重试。") from exc

    body = root.find("w:body", _DOCX_XML_NAMESPACES)
    if body is None:
        return ""

    blocks: List[str] = []
    for child in list(body):
        local_name = _xml_local_name(str(child.tag))
        if local_name == "p":
            paragraph_text = _collect_docx_element_text(child)
            if paragraph_text:
                blocks.append(paragraph_text)
            continue
        if local_name != "tbl":
            continue
        rows: List[str] = []
        for row in child.findall(".//w:tr", _DOCX_XML_NAMESPACES):
            cells: List[str] = []
            for cell in row.findall("./w:tc", _DOCX_XML_NAMESPACES):
                cell_text = _collect_docx_element_text(cell)
                if cell_text:
                    cells.append(cell_text)
            if cells:
                rows.append(" | ".join(cells))
        if rows:
            blocks.extend(rows)
    return "\n".join(blocks)


def parse_word_content(file_bytes: bytes) -> str:
    if not is_docx_available():
        raise failed_dependency(_DOCX_MISSING_MESSAGE)
    try:
        from docx import Document as _Document  # type: ignore
    except Exception as exc:
        raise failed_dependency(_DOCX_MISSING_MESSAGE) from exc
    _ = _Document

    return _extract_docx_document_text(file_bytes)


def normalize_formula_source_text(source_text: str) -> str:
    normalized = str(source_text or "")
    for source, target in _FORMULA_SYMBOL_REPLACEMENTS.items():
        normalized = normalized.replace(source, target)
    normalized = _FORMULA_SUPERSCRIPT_PATTERN.sub(
        lambda match: "^" + "".join(_FORMULA_SUPERSCRIPT_CHAR_MAP.get(char, char) for char in match.group(0)),
        normalized,
    )
    normalized = _FORMULA_SUBSCRIPT_PATTERN.sub(
        lambda match: "".join(_FORMULA_SUBSCRIPT_CHAR_MAP.get(char, char) for char in match.group(0)),
        normalized,
    )
    normalized = re.sub(r"[ \t]+\n", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def parse_question_option_lines(raw_options: str) -> List[Dict[str, str]]:
    normalized_text = str(raw_options or "").replace("\r\n", "\n")
    options: List[Dict[str, str]] = []
    current_option: Optional[Dict[str, str]] = None

    for raw_line in normalized_text.splitlines() or [normalized_text]:
        segments = raw_line.split("|") if "|" in raw_line else [raw_line]
        for segment in segments:
            line = str(segment or "").strip()
            if not line:
                continue
            option_match = _QUESTION_OPTION_LINE_PATTERN.match(line)
            if option_match:
                current_option = {
                    "key": option_match.group(1).strip().upper(),
                    "content": option_match.group(2).strip(),
                }
                options.append(current_option)
                continue
            if current_option is not None:
                current_content = str(current_option.get("content", "")).strip()
                current_option["content"] = f"{current_content}\n{line}".strip()

    return [item for item in options if str(item.get("key", "")).strip() and str(item.get("content", "")).strip()]
