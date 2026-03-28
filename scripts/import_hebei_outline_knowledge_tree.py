#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.content_baseline import (
    JOINT_EXAM_GROUPS,
    POLICY_VERSION_CODE,
    PUBLIC_SUBJECTS,
    SUBJECT_CODE_MAP,
    all_joint_exam_group_codes,
    level_code_from_level,
    level_path_from_level,
    subject_applicable_group_codes,
    subject_id_from_subject_code,
)
from app.db import get_connection
from app.service_shared import parse_word_content


L2_PATTERN = re.compile(r"^([一二三四五六七八九十百]+)[、.．]\s*(.+)$")
L3_PATTERN = re.compile(r"^[（(]([一二三四五六七八九十百]+)[)）]\s*(.+)$")
L4_PATTERN = re.compile(r"^([0-9]{1,2})[、.．]\s*(.+)$")
L5_PATTERN = re.compile(r"^[（(]([0-9]{1,2})[)）]\s*(.+)$")

SKIP_LINE_PATTERNS = (
    re.compile(r"^河北省普通高等学校专升本考试$"),
    re.compile(r"^《.+》考试说明$"),
    re.compile(r"^[0-9]+$"),
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_text_line(line: str) -> str:
    cleaned = str(line or "").replace("\x0c", " ").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def is_skip_line(line: str) -> bool:
    if not line:
        return True
    for pattern in SKIP_LINE_PATTERNS:
        if pattern.match(line):
            return True
    return False


def normalize_heading_name(name: str) -> str:
    text = normalize_text_line(name)
    text = re.sub(r"[：:；;。]+$", "", text).strip()
    if len(text) > 120:
        text = text[:120].rstrip()
    return text


def normalize_key(name: str) -> str:
    return re.sub(r"[\s\W_]+", "", str(name or "").strip().lower())


@dataclass
class OutlineNode:
    name: str
    level: int
    children: List["OutlineNode"] = field(default_factory=list)
    _child_index: Dict[str, "OutlineNode"] = field(default_factory=dict, repr=False)

    def ensure_child(self, name: str, level: int) -> "OutlineNode":
        normalized = normalize_heading_name(name)
        if not normalized:
            return self
        key = normalize_key(normalized)
        existing = self._child_index.get(key)
        if existing:
            return existing
        node = OutlineNode(name=normalized, level=level)
        self.children.append(node)
        self._child_index[key] = node
        return node


def extract_pdf_text(path: Path) -> str:
    if shutil.which("pdftotext"):
        proc = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0 and str(proc.stdout or "").strip():
            return str(proc.stdout)

    # OCR fallback for scanned PDFs.
    if shutil.which("pdftoppm") and shutil.which("tesseract"):
        with tempfile.TemporaryDirectory(prefix="outline-pdf-ocr-") as temp_dir:
            temp_path = Path(temp_dir)
            image_prefix = temp_path / "page"
            render = subprocess.run(
                ["pdftoppm", "-f", "1", "-l", "80", "-png", str(path), str(image_prefix)],
                capture_output=True,
                text=True,
                check=False,
            )
            if render.returncode != 0:
                return ""
            chunks: List[str] = []
            for image_path in sorted(temp_path.glob("page-*.png")):
                ocr = subprocess.run(
                    ["tesseract", str(image_path), "stdout", "-l", "chi_sim+eng"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if ocr.returncode == 0 and str(ocr.stdout or "").strip():
                    chunks.append(str(ocr.stdout))
            return "\n".join(chunks)

    return ""


def extract_word_text(path: Path) -> str:
    if shutil.which("textutil"):
        proc = subprocess.run(
            ["textutil", "-convert", "txt", "-stdout", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0 and str(proc.stdout or "").strip():
            return str(proc.stdout)
    if path.suffix.lower() == ".docx":
        return parse_word_content(path.read_bytes())
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_document_text(path: Path) -> str:
    suffix = path.suffix.lower().strip()
    if suffix == ".pdf":
        return extract_pdf_text(path)
    if suffix in {".doc", ".docx"}:
        return extract_word_text(path)
    raise ValueError(f"Unsupported file suffix: {suffix}")


def parse_subject_name(path: Path) -> str:
    name = str(path.stem or "").strip()
    name = re.sub(r"考试说明.*$", "", name).strip()
    return name.strip("《》 ").strip()


def parse_outline_tree(subject_name: str, text: str) -> OutlineNode:
    root = OutlineNode(name=subject_name, level=1)
    current_l2: Optional[OutlineNode] = None
    current_l3: Optional[OutlineNode] = None
    current_l4: Optional[OutlineNode] = None
    last_l5_node: Optional[OutlineNode] = None
    pending_freeform_node: Optional[OutlineNode] = None
    pending_freeform_parent: Optional[OutlineNode] = None

    for raw_line in str(text or "").splitlines():
        line = normalize_text_line(raw_line)
        if is_skip_line(line):
            continue

        l2_match = L2_PATTERN.match(line)
        if l2_match:
            title = normalize_heading_name(l2_match.group(2))
            if title:
                current_l2 = root.ensure_child(title, 2)
                current_l3 = None
                current_l4 = None
                last_l5_node = None
                pending_freeform_node = None
                pending_freeform_parent = None
            continue

        l3_match = L3_PATTERN.match(line)
        if l3_match:
            title = normalize_heading_name(l3_match.group(2))
            if title:
                parent = current_l2 or root
                current_l3 = parent.ensure_child(title, 3)
                current_l4 = None
                last_l5_node = None
                pending_freeform_node = None
                pending_freeform_parent = None
            continue

        l4_match = L4_PATTERN.match(line)
        if l4_match:
            title = normalize_heading_name(l4_match.group(2))
            if title:
                parent = current_l3 or current_l2 or root
                current_l4 = parent.ensure_child(title, 4)
                last_l5_node = None
                pending_freeform_node = None
                pending_freeform_parent = None
            continue

        l5_match = L5_PATTERN.match(line)
        if l5_match:
            title = normalize_heading_name(l5_match.group(2))
            if title:
                if current_l4:
                    last_l5_node = current_l4.ensure_child(title, 5)
                else:
                    # No L4 context in source text: normalize this item as L4
                    # so all L5 nodes keep strict L4 -> L5 parent linkage.
                    parent = current_l3 or current_l2 or root
                    current_l4 = parent.ensure_child(title, 4)
                    last_l5_node = None
                pending_freeform_node = None
                pending_freeform_parent = None
            continue

        if last_l5_node and len(line) <= 60 and not line.startswith(("一、", "二、", "三、", "四、", "五、")):
            merged = normalize_heading_name(f"{last_l5_node.name}{line}")
            if merged:
                last_l5_node.name = merged
            continue

        freeform_parent = current_l4 or current_l3
        if freeform_parent:
            freeform_level = 5 if current_l4 else 4
            if pending_freeform_node and pending_freeform_parent is freeform_parent:
                merged = normalize_heading_name(f"{pending_freeform_node.name}{line}")
                if merged:
                    pending_freeform_node.name = merged
                continue

            normalized_line = normalize_heading_name(line)
            if normalized_line:
                pending_freeform_node = freeform_parent.ensure_child(normalized_line, freeform_level)
                pending_freeform_parent = freeform_parent
            continue

        pending_freeform_node = None
        pending_freeform_parent = None

    return root


def resolve_subject_scope(subject_name: str) -> Dict[str, object]:
    public_map = {
        str(item.get("subjectName", "")).strip(): str(item.get("subjectCode", "")).strip()
        for item in PUBLIC_SUBJECTS
        if isinstance(item, dict)
    }
    subject_code = public_map.get(subject_name) or str(SUBJECT_CODE_MAP.get(subject_name, "")).strip()
    if not subject_code:
        raise ValueError(f"未找到科目编码映射: {subject_name}")

    public_codes = set(public_map.values())
    is_public = subject_code in public_codes
    if is_public:
        return {
            "subject_code": subject_code,
            "subject_type": "PUBLIC",
            "exam_category_code": "",
            "joint_exam_group_code": "",
            "applicable_groups": all_joint_exam_group_codes(),
        }

    matched_groups: List[str] = []
    exam_category_code = ""
    for group in JOINT_EXAM_GROUPS:
        if not isinstance(group, dict):
            continue
        professional_subjects = group.get("professionalSubjects", [])
        if not isinstance(professional_subjects, list):
            continue
        for subject in professional_subjects:
            if not isinstance(subject, dict):
                continue
            if str(subject.get("subjectCode", "")).strip() == subject_code:
                group_code = str(group.get("jointExamGroupCode", "")).strip()
                if group_code:
                    matched_groups.append(group_code)
                if not exam_category_code:
                    exam_category_code = str(group.get("examCategoryCode", "")).strip()
                break

    matched_groups = sorted(set(matched_groups))
    return {
        "subject_code": subject_code,
        "subject_type": "PROFESSIONAL",
        "exam_category_code": exam_category_code,
        "joint_exam_group_code": matched_groups[0] if matched_groups else "",
        "applicable_groups": matched_groups,
    }


def flatten_tree_for_json(root: OutlineNode, scope: Dict[str, object]) -> List[Dict[str, object]]:
    counter = 0
    rows: List[Dict[str, object]] = []

    def walk(node: OutlineNode, parent_id: Optional[str], sort: int) -> str:
        nonlocal counter
        counter += 1
        node_id = f"{scope['subject_code']}-n{counter:05d}"
        rows.append(
            {
                "id": node_id,
                "parent_id": parent_id,
                "name": node.name,
                "level": node.level,
                "level_code": level_code_from_level(node.level),
                "level_path": level_path_from_level(node.level),
                "sort": sort,
                "subject_code": str(scope["subject_code"]),
                "subject_type": str(scope["subject_type"]),
                "exam_category_code": str(scope["exam_category_code"]),
                "joint_exam_group_code": str(scope["joint_exam_group_code"]),
            }
        )
        for index, child in enumerate(node.children, start=1):
            walk(child, node_id, index * 10)
        return node_id

    walk(root, None, 10)
    return rows


def tree_to_dict(node: OutlineNode) -> Dict[str, object]:
    return {
        "name": node.name,
        "level": node.level,
        "children": [tree_to_dict(child) for child in node.children],
    }


def load_json_object(raw: object) -> Dict[str, object]:
    if isinstance(raw, dict):
        return dict(raw)
    if not raw:
        return {}
    try:
        parsed = json.loads(str(raw))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def build_ext_json(level: int, scope: Dict[str, object]) -> Dict[str, object]:
    subject_code = str(scope["subject_code"])
    subject_type = str(scope["subject_type"])
    return {
        "level": level,
        "levelCode": level_code_from_level(level),
        "levelPath": level_path_from_level(level),
        "policyVersionCode": POLICY_VERSION_CODE,
        "subjectId": subject_id_from_subject_code(subject_code),
        "subjectCode": subject_code,
        "subjectType": subject_type,
        "examCategoryCode": "" if subject_type == "PUBLIC" else str(scope["exam_category_code"]),
        "jointExamGroupCode": "" if subject_type == "PUBLIC" else str(scope["joint_exam_group_code"]),
        "applicableGroups": subject_applicable_group_codes(subject_code) or list(scope.get("applicable_groups", [])),
    }


def find_existing_node(
    connection,
    parent_id: Optional[str],
    name: str,
    scope: Dict[str, object],
) -> Optional[Dict[str, object]]:
    row = connection.execute(
        """
        SELECT id, parentId, name, sort, status, extJson, createTime, updateTime
        FROM knowledge
        WHERE
          ((parentId IS NULL AND :parent_id IS NULL) OR parentId = :parent_id)
          AND name = :name
          AND COALESCE(json_extract(extJson, '$.policyVersionCode'), '') = :policy_version
          AND COALESCE(json_extract(extJson, '$.subjectCode'), '') = :subject_code
          AND COALESCE(json_extract(extJson, '$.jointExamGroupCode'), '') = :joint_exam_group_code
        LIMIT 1
        """,
        {
            "parent_id": parent_id,
            "name": name,
            "policy_version": POLICY_VERSION_CODE,
            "subject_code": str(scope["subject_code"]),
            "joint_exam_group_code": str(scope["joint_exam_group_code"]),
        },
    ).fetchone()
    return dict(row) if row else None


def upsert_nodes_to_knowledge_table(
    db_path: Path,
    rows: List[Dict[str, object]],
    scope_by_subject_code: Dict[str, Dict[str, object]],
) -> Dict[str, int]:
    created = 0
    updated = 0
    id_map: Dict[str, str] = {}

    with get_connection(db_path) as connection:
        for row in rows:
            temp_id = str(row["id"])
            temp_parent_id = row.get("parent_id")
            parent_db_id = id_map.get(str(temp_parent_id)) if temp_parent_id else None

            subject_code = str(row.get("subject_code", ""))
            scope = scope_by_subject_code[subject_code]
            desired_ext = build_ext_json(int(row["level"]), scope)
            now = now_iso()

            existing = find_existing_node(
                connection,
                parent_id=parent_db_id,
                name=str(row["name"]),
                scope=scope,
            )

            if existing:
                merged_ext = load_json_object(existing.get("extJson"))
                merged_ext.update(desired_ext)
                needs_update = (
                    int(existing.get("sort", 0)) != int(row["sort"])
                    or str(existing.get("status", "")) != "ENABLED"
                    or merged_ext != load_json_object(existing.get("extJson"))
                )
                db_id = str(existing["id"])
                if needs_update:
                    connection.execute(
                        """
                        UPDATE knowledge
                        SET parentId = :parent_id,
                            name = :name,
                            sort = :sort,
                            status = 'ENABLED',
                            extJson = :ext_json,
                            updateTime = :update_time
                        WHERE id = :id
                        """,
                        {
                            "id": db_id,
                            "parent_id": parent_db_id,
                            "name": str(row["name"]),
                            "sort": int(row["sort"]),
                            "ext_json": json.dumps(merged_ext, ensure_ascii=False),
                            "update_time": now,
                        },
                    )
                    updated += 1
                id_map[temp_id] = db_id
                continue

            db_id = f"knowledge-{uuid.uuid4().hex[:8]}"
            connection.execute(
                """
                INSERT INTO knowledge (id, parentId, name, sort, status, extJson, createTime, updateTime)
                VALUES (:id, :parent_id, :name, :sort, 'ENABLED', :ext_json, :create_time, :update_time)
                """,
                {
                    "id": db_id,
                    "parent_id": parent_db_id,
                    "name": str(row["name"]),
                    "sort": int(row["sort"]),
                    "ext_json": json.dumps(desired_ext, ensure_ascii=False),
                    "create_time": now,
                    "update_time": now,
                },
            )
            created += 1
            id_map[temp_id] = db_id
        connection.commit()

    return {"created": created, "updated": updated}


def parse_documents(source_dir: Path) -> Dict[str, object]:
    files = sorted(
        [
            item
            for item in source_dir.iterdir()
            if item.is_file() and item.suffix.lower() in {".pdf", ".doc", ".docx"}
        ],
        key=lambda item: item.name,
    )
    if not files:
        raise ValueError(f"目录中未找到 PDF/DOC/DOCX 文件: {source_dir}")

    subjects: List[Dict[str, object]] = []
    all_rows: List[Dict[str, object]] = []
    scope_by_subject_code: Dict[str, Dict[str, object]] = {}

    for file_path in files:
        subject_name = parse_subject_name(file_path)
        scope = resolve_subject_scope(subject_name)
        scope_by_subject_code[str(scope["subject_code"])] = scope
        text = extract_document_text(file_path)
        tree_root = parse_outline_tree(subject_name, text)
        flat_rows = flatten_tree_for_json(tree_root, scope)
        subjects.append(
            {
                "source_file": file_path.name,
                "subject_name": subject_name,
                "subject_code": str(scope["subject_code"]),
                "subject_type": str(scope["subject_type"]),
                "exam_category_code": str(scope["exam_category_code"]),
                "joint_exam_group_code": str(scope["joint_exam_group_code"]),
                "node_count": len(flat_rows),
                "tree": tree_to_dict(tree_root),
                "nodes": flat_rows,
            }
        )
        all_rows.extend(flat_rows)

    return {
        "generated_at": now_iso(),
        "policy_version_code": POLICY_VERSION_CODE,
        "source_dir": str(source_dir),
        "subject_count": len(subjects),
        "node_count": len(all_rows),
        "subjects": subjects,
        "nodes": all_rows,
        "scope_by_subject_code": scope_by_subject_code,
    }


def parse_args() -> argparse.Namespace:
    workspace_dir = Path.cwd()
    parser = argparse.ArgumentParser(
        description="Parse Hebei exam outlines into knowledge_tree.json and import into knowledge table."
    )
    parser.add_argument(
        "--source-dir",
        default=str(workspace_dir / "2026专升本考试大纲"),
        help="Outline directory containing PDF/DOC/DOCX files.",
    )
    parser.add_argument(
        "--output-json",
        default=str(workspace_dir / "data" / "knowledge_tree.json"),
        help="Output JSON path.",
    )
    parser.add_argument(
        "--db-path",
        default=str(workspace_dir / "data" / "question_bank.db"),
        help="SQLite database path.",
    )
    parser.add_argument(
        "--skip-import",
        action="store_true",
        help="Only generate knowledge_tree.json, do not write database.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source_dir).resolve()
    output_json = Path(args.output_json).resolve()
    db_path = Path(args.db_path).resolve()

    if not source_dir.exists() or not source_dir.is_dir():
        raise SystemExit(f"source-dir 不存在或不是目录: {source_dir}")

    parsed = parse_documents(source_dir)
    scope_by_subject_code = parsed.pop("scope_by_subject_code")

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")

    import_summary = {"created": 0, "updated": 0}
    if not args.skip_import:
        import_summary = upsert_nodes_to_knowledge_table(
            db_path=db_path,
            rows=list(parsed.get("nodes", [])),
            scope_by_subject_code=scope_by_subject_code,
        )

    print(
        json.dumps(
            {
                "output_json": str(output_json),
                "db_path": str(db_path),
                "subject_count": int(parsed.get("subject_count", 0)),
                "node_count": int(parsed.get("node_count", 0)),
                "import_summary": import_summary,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
