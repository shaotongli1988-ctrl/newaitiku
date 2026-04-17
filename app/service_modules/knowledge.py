from __future__ import annotations

from difflib import SequenceMatcher
from threading import Lock

from app.db import KNOWLEDGE_TREE_PATH
from app.service_shared import *


PROMPT_TEMPLATE = (
    "请从以下课程大纲中提取“章节-考点”层级，输出 JSON。\n"
    "输出 JSON Schema：\n"
    "{{\n"
    '  "chapters": [\n'
    '    {{"chapter": "章节名称", "points": [{{"point": "考点1", "module_code": "模块编码"}}]}}\n'
    "  ]\n"
    "}}\n"
    "要求：\n"
    "1. chapter 保持简洁，不含编号前缀。\n"
    "2. points 仅保留可作为知识点节点的短语。\n"
    "3. 每个章节 points 至少 1 项，最多 30 项。\n"
    "4. 不要输出与章节无关的说明文字。\n"
    "5. 请将解析出的题目与以下【候选知识点清单】进行语义匹配。若匹配度高，请返回对应的 module_code；若不匹配，请按大纲逻辑建议一个新的 module_code。\n"
    "6. module_code 优先复用【候选知识点清单】中的既有编码，不要随意改写。\n"
    "7. 仅输出 JSON，不要附带 Markdown 或解释文本。\n"
    "当前科目代码：{subject_code}\n\n"
    "候选知识点清单（JSON）：\n{knowledge_points_list}\n\n"
    "大纲文本：\n{source_excerpt}"
)

SEMANTIC_MATCH_THRESHOLD = 0.85
QUESTION_BATCH_ALIGNMENT_THRESHOLD = 0.8
QUESTION_BATCH_TASK_THRESHOLD = 10
QUESTION_BATCH_PROMPT_TEMPLATE = (
    "请从以下 Word 题库文档中识别题目，并输出 JSON。\n"
    "要求：\n"
    "1. 识别每道题的题干、选项、答案、解析。\n"
    "2. 结合【候选语义池】为每道题返回最匹配的 chapter_code(L4) 与 point_code(L5)。\n"
    "3. 如果匹配置信度低于 0.8，point_code 和 chapter_code 返回 null，并写明“建议手动标注”。\n"
    "4. 每道题都返回完整路径 path_levels，包含 L1-L5 的 id/code/label。\n"
    "5. 仅输出 JSON，不输出 Markdown。\n"
    "JSON Schema:\n"
    "{\n"
    '  "items": [\n'
    "    {\n"
    '      "title": "题目标题",\n'
    '      "content": "题干",\n'
    '      "type": "single_choice",\n'
    '      "options": [{"key":"A","content":"选项"}],\n'
    '      "answer": "答案",\n'
    '      "analysis": "解析",\n'
    '      "chapterCode": "CH_001",\n'
    '      "pointCode": "PT_001_001",\n'
    '      "confidence": 0.91,\n'
    '      "review_message": "",\n'
    '      "path_levels": [{"level":"L1","id":"...","code":"...","label":"..."}]\n'
    "    }\n"
    "  ]\n"
    "}\n"
    "当前科目代码：{subject_code}\n"
    "候选语义池：\n{semantic_pool}\n"
    "文档内容：\n{source_excerpt}"
)
QUESTION_OPTION_LINE_PATTERN = re.compile(r"^[\(（]?([A-Z])(?:[\)）][\.\:：、．]?|[\.\:：、．])\s*(.*)$")


GENERIC_KNOWLEDGE_PATH_LABELS = {
    "具体内容与要求",
    "科目简介",
    "考试说明",
    "考试要求",
    "课程简介",
    "课程说明",
    "复习建议",
}


class KnowledgeServiceMixin:
    def get_student_syllabus_catalog(self) -> Dict[str, object]:
        if not KNOWLEDGE_TREE_PATH.exists():
            raise not_found("考试大纲数据不存在。")

        try:
            raw_payload = json.loads(KNOWLEDGE_TREE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise failed_dependency(f"考试大纲数据读取失败：{error}") from error

        subject_rows = raw_payload.get("subjects", [])
        normalized_subjects: List[Dict[str, object]] = []
        for item in subject_rows if isinstance(subject_rows, list) else []:
            if not isinstance(item, dict):
                continue
            subject_code = str(item.get("subject_code", "")).strip()
            subject_name = str(item.get("subject_name", "")).strip()
            if not subject_code or not subject_name:
                continue
            exam_category_code = str(item.get("exam_category_code", "")).strip()
            joint_exam_group_code = str(item.get("joint_exam_group_code", "")).strip()
            exam_category = get_exam_category(exam_category_code) if exam_category_code else {}
            joint_exam_group = get_joint_exam_group(joint_exam_group_code) if joint_exam_group_code else {}
            normalized_subjects.append(
                {
                    "subjectCode": subject_code,
                    "subjectName": subject_name,
                    "subjectType": str(item.get("subject_type", "")).strip().upper() or "PROFESSIONAL",
                    "examCategoryCode": exam_category_code,
                    "examCategoryName": str(exam_category.get("examCategoryName", "")).strip() if isinstance(exam_category, dict) else "",
                    "jointExamGroupCode": joint_exam_group_code,
                    "jointExamGroupName": str(joint_exam_group.get("jointExamGroupName", "")).strip() if isinstance(joint_exam_group, dict) else "",
                    "nodeCount": max(0, int(item.get("node_count", 0) or 0)),
                    "sourceFile": str(item.get("source_file", "")).strip(),
                    "tree": item.get("tree") if isinstance(item.get("tree"), dict) else {},
                    "nodes": item.get("nodes") if isinstance(item.get("nodes"), list) else [],
                }
            )

        normalized_subjects.sort(
            key=lambda item: (
                str(item.get("examCategoryCode", "")),
                str(item.get("jointExamGroupCode", "")),
                str(item.get("subjectType", "")) != "PUBLIC",
                str(item.get("subjectName", "")),
            )
        )

        exam_category_codes = {
            str(item.get("examCategoryCode", "")).strip()
            for item in normalized_subjects
            if str(item.get("examCategoryCode", "")).strip()
        }
        joint_exam_group_codes = {
            str(item.get("jointExamGroupCode", "")).strip()
            for item in normalized_subjects
            if str(item.get("jointExamGroupCode", "")).strip()
        }

        return {
            "generatedAt": str(raw_payload.get("generated_at", "")).strip(),
            "policyVersionCode": str(raw_payload.get("policy_version_code", "")).strip() or POLICY_VERSION_CODE,
            "subjectCount": len(normalized_subjects),
            "nodeCount": max(0, int(raw_payload.get("node_count", 0) or 0)),
            "examCategoryCount": len(exam_category_codes),
            "jointExamGroupCount": len(joint_exam_group_codes),
            "publicSubjectCount": sum(1 for item in normalized_subjects if str(item.get("subjectType", "")).strip() == "PUBLIC"),
            "professionalSubjectCount": sum(1 for item in normalized_subjects if str(item.get("subjectType", "")).strip() != "PUBLIC"),
            "subjects": normalized_subjects,
        }

    def _build_knowledge_display_labels(self, raw_label: object, level: object) -> Dict[str, str]:
        full_label = self._normalize_outline_label(raw_label)
        if not full_label:
            return {"fullLabel": "", "shortLabel": ""}

        try:
            normalized_level = int(level or 0)
        except (TypeError, ValueError):
            normalized_level = 0

        if normalized_level < 5:
            return {"fullLabel": full_label, "shortLabel": full_label}

        candidate = re.sub(
            r"^(理解并掌握|理解并运用|掌握并运用|理解|掌握|了解|熟悉|认识|学会|会用|会|能够|明白|知道)",
            "",
            full_label,
        ).strip("，。；：:、 ")
        if not candidate:
            candidate = full_label

        colon_parts = re.split(r"[：:]", candidate, maxsplit=1)
        if len(colon_parts) == 2 and len(colon_parts[0].strip()) <= 4 and colon_parts[1].strip():
            candidate = colon_parts[1].strip()
        else:
            candidate = colon_parts[0].strip()

        candidate = re.split(r"[，。；]", candidate, maxsplit=1)[0].strip() or full_label
        if len(candidate) > 24:
            candidate = f"{candidate[:24].rstrip('、，；：: ')}..."

        return {
            "fullLabel": full_label,
            "shortLabel": candidate or full_label,
        }

    def _knowledge_wrong_count_map(
        self,
        items: List[Dict[str, object]],
        viewer_student_user_id: str = "",
        subject_code: str = "",
    ) -> Dict[str, int]:
        normalized_student_user_id = str(viewer_student_user_id or "").strip()
        if not normalized_student_user_id:
            return {}

        point_wrong_count_by_code: Dict[str, int] = {}
        for row in self.repository.aggregate_student_analytics_rollups(
            {
                "studentUserId": normalized_student_user_id,
                "subjectCode": str(subject_code or "").strip(),
            }
        ):
            if str(row.get("rowType", "")).strip() != "point":
                continue
            point_code = str(row.get("pointCode", "")).strip()
            if not point_code:
                continue
            point_wrong_count_by_code[point_code] = point_wrong_count_by_code.get(point_code, 0) + max(0, int(row.get("wrongCount", 0) or 0))

        if not point_wrong_count_by_code:
            return {}

        item_by_id: Dict[str, Dict[str, object]] = {}
        level_by_id: Dict[str, int] = {}
        wrong_count_by_knowledge_id: Dict[str, int] = {}

        for item in items:
            knowledge_id = str(item.get("id", "")).strip()
            if not knowledge_id:
                continue
            ext_json = self._load_json_object(str(item.get("extJson", "{}")))
            try:
                level = int(ext_json.get("level", 0) or 0)
            except (TypeError, ValueError):
                level = 0
            parent_id = str(item.get("parentId", "") or "").strip()
            point_code = str(ext_json.get("pointCode", "") or "").strip()

            item_by_id[knowledge_id] = item
            level_by_id[knowledge_id] = level if level >= 0 else 0
            wrong_count_by_knowledge_id[knowledge_id] = point_wrong_count_by_code.get(point_code, 0) if point_code else 0

        for knowledge_id, _level in sorted(level_by_id.items(), key=lambda item: item[1], reverse=True):
            parent_id = str(item_by_id.get(knowledge_id, {}).get("parentId", "") or "").strip()
            if not parent_id:
                continue
            wrong_count_by_knowledge_id[parent_id] = wrong_count_by_knowledge_id.get(parent_id, 0) + wrong_count_by_knowledge_id.get(knowledge_id, 0)

        return wrong_count_by_knowledge_id

    def _normalize_question_block_text(self, value: str) -> str:
        normalized = str(value or "").replace("\r\n", "\n")
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        return normalized.strip()

    def _strip_question_number_prefix(self, line: str) -> str:
        normalized_line = str(line or "").strip()
        return re.sub(r"^(?:\d+[\.\)])\s*", "", normalized_line).strip()

    def _extract_marker_prefix(self, line: str) -> Tuple[str, str]:
        normalized_line = str(line or "").strip()
        if not normalized_line:
            return "", ""
        if normalized_line.startswith("【") and "】" in normalized_line:
            end_index = normalized_line.find("】")
            marker = normalized_line[1:end_index].strip().lower()
            remainder = normalized_line[end_index + 1 :].strip()
            if remainder.startswith(":") or remainder.startswith("："):
                remainder = remainder[1:].strip()
            return marker, remainder
        if normalized_line.startswith("[") and "]" in normalized_line:
            end_index = normalized_line.find("]")
            marker = normalized_line[1:end_index].strip().lower()
            remainder = normalized_line[end_index + 1 :].strip()
            if remainder.startswith(":") or remainder.startswith("："):
                remainder = remainder[1:].strip()
            return marker, remainder
        for separator in (":", "："):
            if separator in normalized_line:
                marker, remainder = normalized_line.split(separator, 1)
                return marker.strip().lower(), remainder.strip()
        return normalized_line.lower(), ""

    def _is_answer_marker_line(self, line: str) -> bool:
        marker, _ = self._extract_marker_prefix(line)
        return marker in {"答案", "参考答案", "answer"}

    def _strip_answer_marker(self, line: str) -> str:
        marker, remainder = self._extract_marker_prefix(line)
        if marker in {"答案", "参考答案", "answer"}:
            return remainder
        return str(line or "").strip()

    def _is_analysis_marker_line(self, line: str) -> bool:
        marker, _ = self._extract_marker_prefix(line)
        return marker in {
            "解析",
            "答案解析",
            "解析说明",
            "analysis",
            "explanation",
        }

    def _strip_analysis_marker(self, line: str) -> str:
        marker, remainder = self._extract_marker_prefix(line)
        if marker in {
            "解析",
            "答案解析",
            "解析说明",
            "analysis",
            "explanation",
        }:
            return remainder
        return str(line or "").strip()

    def _is_knowledge_marker_line(self, line: str) -> bool:
        marker, _ = self._extract_marker_prefix(line)
        return marker in {"知识点", "知識點", "knowledge"}

    def _strip_knowledge_marker(self, line: str) -> str:
        marker, remainder = self._extract_marker_prefix(line)
        if marker in {"知识点", "知識點", "knowledge"}:
            return remainder
        return str(line or "").strip()

    def _looks_like_question_start(self, line: str) -> bool:
        normalized_line = str(line or "").strip()
        if normalized_line.startswith("【题型】") or normalized_line.startswith("【题干】"):
            return True
        return bool(re.match(r"^(?:第?\d+题|\d+[\.．、\)])\s*\S+", normalized_line))

    def _current_question_block_complete(self, current_block: List[str]) -> bool:
        option_count = 0
        for raw_line in current_block:
            line = str(raw_line or "").strip()
            if not line:
                continue
            if self._is_answer_marker_line(line) or self._is_analysis_marker_line(line):
                return True
            if QUESTION_OPTION_LINE_PATTERN.match(line):
                option_count += 1
        return option_count >= 2

    def _ensure_knowledge_tree_snapshot_state(self) -> None:
        if hasattr(self, "_knowledge_snapshot_lock"):
            return
        self._knowledge_snapshot_lock = Lock()
        self._knowledge_snapshot_items: Optional[tuple[Dict[str, object], ...]] = None
        self._knowledge_tree_structure_cache: Dict[tuple[str, str, str, str], Dict[str, object]] = {}

    def preload_knowledge_tree_snapshot(self) -> None:
        self._load_knowledge_snapshot(force_reload=True)

    def _invalidate_knowledge_tree_snapshot(self) -> None:
        self._ensure_knowledge_tree_snapshot_state()
        with self._knowledge_snapshot_lock:
            self._knowledge_snapshot_items = None
            self._knowledge_tree_structure_cache = {}

    def _load_knowledge_snapshot(self, force_reload: bool = False) -> tuple[Dict[str, object], ...]:
        self._ensure_knowledge_tree_snapshot_state()
        if not force_reload and self._knowledge_snapshot_items is not None:
            return self._knowledge_snapshot_items
        with self._knowledge_snapshot_lock:
            if force_reload or self._knowledge_snapshot_items is None:
                # Service is a FastAPI singleton, so a single in-memory snapshot
                # removes repeated reads from the knowledge table on every GET.
                self._knowledge_snapshot_items = tuple(self.repository.list_knowledge(""))
                self._knowledge_tree_structure_cache = {}
            return self._knowledge_snapshot_items

    def _get_cached_knowledge_items(self, status: str, repository_filters: Dict[str, str]) -> List[Dict[str, object]]:
        normalized_status = str(status or "").strip()
        normalized_exam_category_code = str(repository_filters.get("examCategoryCode", "")).strip()
        normalized_joint_exam_group_code = str(repository_filters.get("jointExamGroupCode", "")).strip()
        normalized_subject_code = str(repository_filters.get("subjectCode", "")).strip()
        cache_key = (
            normalized_status,
            normalized_exam_category_code,
            normalized_joint_exam_group_code,
            normalized_subject_code,
        )

        self._ensure_knowledge_tree_snapshot_state()
        cached_structure = self._knowledge_tree_structure_cache.get(cache_key)
        if cached_structure is not None:
            cached_items = cached_structure.get("items", ())
            return [dict(item) for item in cached_items if isinstance(item, dict)]

        source_items = self._load_knowledge_snapshot()
        filtered_items: List[Dict[str, object]] = []
        for item in source_items:
            normalized_item = dict(item)
            item_status = str(normalized_item.get("status", "")).strip()
            if normalized_status and item_status != normalized_status:
                continue
            if not self._knowledge_item_matches_repository_filters(normalized_item, repository_filters):
                continue
            filtered_items.append(normalized_item)

        with self._knowledge_snapshot_lock:
            self._knowledge_tree_structure_cache[cache_key] = {"items": tuple(filtered_items)}
        return filtered_items

    def _knowledge_item_matches_repository_filters(self, item: Dict[str, object], repository_filters: Dict[str, str]) -> bool:
        item_ext = self._load_json_object(str(item.get("extJson", "{}")))
        subject_code = str(repository_filters.get("subjectCode", "")).strip()
        if subject_code and str(item_ext.get("subjectCode", "")).strip() != subject_code:
            return False

        item_group_codes = {
            str(group_code or "").strip()
            for group_code in (
                item_ext.get("applicableGroups", [])
                if isinstance(item_ext.get("applicableGroups", []), list)
                else []
            )
            if str(group_code or "").strip()
        }
        exam_category_code = str(repository_filters.get("examCategoryCode", "")).strip()
        if exam_category_code:
            item_exam_category_code = str(item_ext.get("examCategoryCode", "")).strip()
            item_subject_type = str(item_ext.get("subjectType", "")).strip()
            allowed_group_codes = {
                str(group_item.get("jointExamGroupCode", "")).strip()
                for group_item in list_joint_exam_groups(exam_category_code)
                if str(group_item.get("jointExamGroupCode", "")).strip()
            }
            has_exam_match = item_exam_category_code == exam_category_code
            has_group_match = bool(item_group_codes.intersection(allowed_group_codes))
            if item_subject_type != "PUBLIC" and not has_exam_match and not has_group_match:
                return False

        joint_exam_group_code = str(repository_filters.get("jointExamGroupCode", "")).strip()
        if joint_exam_group_code:
            item_joint_exam_group_code = str(item_ext.get("jointExamGroupCode", "")).strip()
            item_subject_type = str(item_ext.get("subjectType", "")).strip()
            has_group_match = (
                item_joint_exam_group_code == joint_exam_group_code
                or joint_exam_group_code in item_group_codes
            )
            if item_subject_type != "PUBLIC" and not has_group_match:
                return False
        return True

    def parse_question_batch_from_word(
        self,
        file_name: str,
        file_bytes: bytes,
        actor: Actor,
        exam_category_code: str,
        joint_exam_group_code: str,
        subject_code: str,
        policy_version: str = POLICY_VERSION_CODE,
    ) -> Dict[str, object]:
        normalized_file_name = str(file_name or "").strip() or "question-batch.docx"
        if len(file_bytes or b"") <= 0:
            raise validation_failed("上传文件不能为空。")
        if len(file_bytes) > SYLLABUS_AI_MAX_FILE_SIZE:
            raise validation_failed("上传文件不能超过 10MB。")
        if not any(normalized_file_name.lower().endswith(suffix) for suffix in (".doc", ".docx", ".txt")):
            raise validation_failed("批量上传仅支持 DOC、DOCX、TXT 文件。")

        scope_filters = self._resolve_knowledge_graph_scope_filters(
            actor=actor,
            exam_category_code=exam_category_code,
            joint_exam_group_code=joint_exam_group_code,
            subject_code=subject_code,
            policy_version=policy_version,
        )
        normalized_subject_code = str(scope_filters.get("subjectCode", "")).strip()
        if not normalized_subject_code:
            raise validation_failed("请先选择科目后再上传 Word。")

        if actor.role != ROLE_SUPER_ADMIN:
            target_exam_category_code = str(scope_filters.get("examCategoryCode", "")).strip() or str(exam_category_code or "").strip()
            target_joint_exam_group_code = str(scope_filters.get("jointExamGroupCode", "")).strip() or str(joint_exam_group_code or "").strip()
            if target_exam_category_code or target_joint_exam_group_code:
                self._assert_actor_scope_write_access(actor, target_exam_category_code, target_joint_exam_group_code)

        content_loader_with_meta = getattr(self, "_load_batch_parse_content_with_meta", None)
        content_loader = getattr(self, "_load_batch_parse_content", None)
        if callable(content_loader_with_meta):
            extracted_text, extraction_meta = content_loader_with_meta(normalized_file_name, file_bytes)
            extracted_text = str(extracted_text or "")
            extraction_meta = extraction_meta if isinstance(extraction_meta, dict) else {"method": "batch_parse_loader"}
        elif callable(content_loader):
            extracted_text = str(content_loader(normalized_file_name, file_bytes) or "")
            extraction_meta = {"method": "batch_parse_loader"}
        else:
            extracted_text = parse_word_content(file_bytes)
            extraction_meta = {"method": "python_docx"}

        normalized_text = str(extracted_text or "").strip()
        if not normalized_text:
            raise validation_failed("未能从上传文件中提取到有效题目内容。")

        semantic_pool = self._build_question_semantic_pool(scope_filters)
        question_blocks = self._extract_question_blocks_from_text(normalized_text)
        if not question_blocks:
            raise validation_failed("未识别到题目边界，请检查 Word 内容格式。")

        if len(question_blocks) > QUESTION_BATCH_TASK_THRESHOLD:
            task = self._create_task(
                actor.user_id,
                "QUESTION_BATCH_PARSE",
                {
                    "requestPayload": {
                        "blocks": question_blocks,
                        "scope": scope_filters,
                        "semanticPool": semantic_pool,
                    },
                    "result": {},
                    "resultSummary": "",
                    "errorMessage": "",
                    "queue": {
                        "queueName": "question-bank-word-batch",
                        "requestedAt": self._now_iso(),
                        "startedAt": "",
                        "completedAt": "",
                        "pollCount": 0,
                    },
                },
            )
            return {
                "taskId": str(task.get("id", "")).strip(),
                "deferred": True,
                "questionCount": len(question_blocks),
                "scope": {
                    "exam_category_code": str(scope_filters.get("examCategoryCode", "")).strip(),
                    "joint_exam_group_code": str(scope_filters.get("jointExamGroupCode", "")).strip(),
                    "subject_code": normalized_subject_code,
                    "policy_version": str(scope_filters.get("policyVersionCode", "")).strip() or POLICY_VERSION_CODE,
                },
                "parserReport": {
                    "sourceFileName": normalized_file_name,
                "sourceFileSize": len(file_bytes),
                "extractMethod": str(extraction_meta.get("method", "")),
                "imageFormulaOcrEngines": list(extraction_meta.get("imageFormulaOcrEngines", []))
                if isinstance(extraction_meta.get("imageFormulaOcrEngines", []), list)
                else [],
                "imageChemicalOcrEngines": list(extraction_meta.get("imageChemicalOcrEngines", []))
                if isinstance(extraction_meta.get("imageChemicalOcrEngines", []), list)
                else [],
                "imageChemicalOcrSamples": list(extraction_meta.get("imageChemicalOcrSamples", []))
                if isinstance(extraction_meta.get("imageChemicalOcrSamples", []), list)
                else [],
                "extractTextLength": len(normalized_text),
                "semanticPoolSize": len(semantic_pool),
                "questionBlockCount": len(question_blocks),
            },
        }

        return self._build_question_batch_parse_result(question_blocks, scope_filters, semantic_pool, normalized_file_name, len(file_bytes), extraction_meta)

    def list_knowledge_tree(
        self,
        status: str = "",
        actor: Optional[Actor] = None,
        exam_category_code: str = "",
        joint_exam_group_code: str = "",
        subject_code: str = "",
        policy_version: str = POLICY_VERSION_CODE,
    ) -> Dict[str, List[Dict[str, object]]]:
        scope_filters = self._resolve_knowledge_graph_scope_filters(
            actor=actor,
            exam_category_code=exam_category_code,
            joint_exam_group_code=joint_exam_group_code,
            subject_code=subject_code,
            policy_version=policy_version,
        )
        # The route layer still wraps this payload with the question-bank
        # standard envelope: { code, message, data }.
        repository_filters = self._build_knowledge_repository_filters(scope_filters)
        normalized_subject_code = str(scope_filters.get("subjectCode", "")).strip()
        normalized_joint_exam_group_code = str(scope_filters.get("jointExamGroupCode", "")).strip()

        items = self._get_cached_knowledge_items(status.strip(), repository_filters)
        knowledge_ids = {
            str(item.get("id", "")).strip()
            for item in items
            if str(item.get("id", "")).strip()
        }
        if not knowledge_ids:
            return {"nodes": [], "links": []}

        question_count_by_knowledge = self._knowledge_question_count_map(knowledge_ids)
        viewer_student_user_id = actor.user_id if actor and actor.role == ROLE_STUDENT else ""
        mastery_by_knowledge = self._knowledge_mastery_map(
            knowledge_ids,
            question_count_by_knowledge,
            viewer_student_user_id=viewer_student_user_id,
            subject_code=normalized_subject_code,
            joint_exam_group_code=normalized_joint_exam_group_code,
        )
        wrong_count_by_knowledge = self._knowledge_wrong_count_map(
            items,
            viewer_student_user_id=viewer_student_user_id,
            subject_code=normalized_subject_code,
        )

        links: List[Dict[str, object]] = []
        link_keys: set[tuple[str, str, str]] = set()
        nodes: List[Dict[str, object]] = []

        for item in items:
            knowledge_id = str(item.get("id", "")).strip()
            if not knowledge_id:
                continue
            question_count = int(question_count_by_knowledge.get(knowledge_id, 0))
            ext_json = self._load_json_object(str(item.get("extJson", "{}")))
            layout_position = self._knowledge_layout_position(ext_json)
            try:
                level = int(ext_json.get("level", 0) or 0)
            except (TypeError, ValueError):
                level = 0
            display_labels = self._build_knowledge_display_labels(item.get("name", ""), level)
            label = display_labels["fullLabel"] or knowledge_id
            parent_id = str(item.get("parentId", "") or "").strip()
            nodes.append(
                {
                    "id": knowledge_id,
                    "label": label,
                    "fullLabel": display_labels["fullLabel"] or label,
                    "shortLabel": display_labels["shortLabel"] or label,
                    "parentId": parent_id or None,
                    "level": level if level >= 0 else 0,
                    "sort": max(0, int(item.get("sort", 0) or 0)),
                    "createTime": str(item.get("createTime", "") or ""),
                    "moduleCode": str(ext_json.get("moduleCode", "")).strip(),
                    "mastery": float(mastery_by_knowledge.get(knowledge_id, 0.0)),
                    "wrongCount": max(0, int(wrong_count_by_knowledge.get(knowledge_id, 0))),
                    "size": self._knowledge_node_size(question_count),
                    "questionCount": question_count,
                    "x": layout_position[0] if layout_position else None,
                    "y": layout_position[1] if layout_position else None,
                }
            )

            if parent_id and parent_id in knowledge_ids:
                parent_key = (parent_id, knowledge_id, "parent")
                if parent_key not in link_keys:
                    links.append({"source": parent_id, "target": knowledge_id, "type": "parent"})
                    link_keys.add(parent_key)

            for prerequisite_id in self._knowledge_prerequisites(ext_json):
                if prerequisite_id not in knowledge_ids or prerequisite_id == knowledge_id:
                    continue
                prerequisite_key = (prerequisite_id, knowledge_id, "prerequisite")
                if prerequisite_key in link_keys:
                    continue
                links.append({"source": prerequisite_id, "target": knowledge_id, "type": "prerequisite"})
                link_keys.add(prerequisite_key)

        collapsed_nodes, collapsed_links = self._collapse_knowledge_graph_to_two_layers(nodes, links)
        return {"nodes": collapsed_nodes, "links": collapsed_links}

    def _is_generic_knowledge_label(self, label: object) -> bool:
        normalized_label = str(label or "").strip()
        if not normalized_label:
            return True
        return normalized_label in GENERIC_KNOWLEDGE_PATH_LABELS

    def _collapse_knowledge_graph_to_two_layers(
        self,
        nodes: List[Dict[str, object]],
        links: List[Dict[str, object]],
    ) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
        if not nodes:
            return [], []

        node_by_id: Dict[str, Dict[str, object]] = {}
        parent_by_id: Dict[str, str] = {}
        children_by_parent: Dict[str, List[str]] = {}
        for item in nodes:
            node_id = str(item.get("id", "")).strip()
            if not node_id:
                continue
            normalized_item = dict(item)
            normalized_item["id"] = node_id
            node_by_id[node_id] = normalized_item
            parent_id = str(item.get("parentId", "") or "").strip()
            if parent_id and parent_id in node_by_id:
                parent_by_id[node_id] = parent_id
                children_by_parent.setdefault(parent_id, []).append(node_id)
            elif parent_id:
                parent_by_id[node_id] = parent_id

        for link in links:
            if str(link.get("type", "")).strip() != "parent":
                continue
            source_id = str(link.get("source", "")).strip()
            target_id = str(link.get("target", "")).strip()
            if not source_id or not target_id:
                continue
            if source_id not in node_by_id or target_id not in node_by_id:
                continue
            parent_by_id[target_id] = source_id
            children_by_parent.setdefault(source_id, [])
            if target_id not in children_by_parent[source_id]:
                children_by_parent[source_id].append(target_id)

        def _node_sort_key(node_id: str) -> Tuple[int, str, str]:
            row = node_by_id.get(node_id, {})
            return (
                max(0, int(row.get("sort", 0) or 0)),
                str(row.get("createTime", "") or ""),
                str(node_id),
            )

        for parent_id in list(children_by_parent.keys()):
            children_by_parent[parent_id] = sorted(children_by_parent[parent_id], key=_node_sort_key)

        roots = sorted(
            [
                node_id
                for node_id in node_by_id
                if not str(parent_by_id.get(node_id, "")).strip() or str(parent_by_id.get(node_id, "")).strip() not in node_by_id
            ],
            key=_node_sort_key,
        )
        if not roots:
            roots = sorted(list(node_by_id.keys()), key=_node_sort_key)

        root_by_id: Dict[str, str] = {}
        second_by_id: Dict[str, str] = {}

        def _build_path_to_root(node_id: str) -> List[str]:
            path: List[str] = []
            seen: set[str] = set()
            cursor = str(node_id or "").strip()
            while cursor and cursor not in seen and cursor in node_by_id:
                path.append(cursor)
                seen.add(cursor)
                cursor = str(parent_by_id.get(cursor, "")).strip()
            path.reverse()
            return path

        for node_id in node_by_id:
            path = _build_path_to_root(node_id)
            if not path:
                continue
            root_id = path[0]
            root_by_id[node_id] = root_id
            if len(path) <= 1:
                continue
            second_id = ""
            for candidate_id in path[1:]:
                candidate_node = node_by_id.get(candidate_id, {})
                if not self._is_generic_knowledge_label(candidate_node.get("label", "")):
                    second_id = candidate_id
                    break
            if not second_id:
                second_id = path[1]
            second_by_id[node_id] = second_id

        collapsed_nodes: Dict[str, Dict[str, object]] = {}
        collapsed_parent_links: set[Tuple[str, str]] = set()
        second_to_root: Dict[str, str] = {}

        for root_id in roots:
            root_node = node_by_id.get(root_id, {})
            if not root_node:
                continue
            collapsed_nodes[root_id] = {
                **root_node,
                "id": root_id,
                "parentId": None,
                "level": 4,
                "questionCount": 0,
                "wrongCount": 0,
                "mastery": 0.0,
                "size": self._knowledge_node_size(0),
            }

        for node_id, second_id in second_by_id.items():
            root_id = root_by_id.get(node_id, "")
            if not second_id or not root_id or second_id == root_id:
                continue
            second_node = node_by_id.get(second_id, {})
            if not second_node:
                continue
            second_to_root[second_id] = root_id
            if second_id not in collapsed_nodes:
                collapsed_nodes[second_id] = {
                    **second_node,
                    "id": second_id,
                    "parentId": root_id,
                    "level": 5,
                    "questionCount": 0,
                    "wrongCount": 0,
                    "mastery": 0.0,
                    "size": self._knowledge_node_size(0),
                }
            collapsed_parent_links.add((root_id, second_id))

        mastery_sum_by_collapsed_id: Dict[str, float] = {}
        mastery_weight_by_collapsed_id: Dict[str, float] = {}

        def _accumulate_metrics(target_id: str, source_node: Dict[str, object]) -> None:
            if target_id not in collapsed_nodes:
                return
            question_count = max(0, int(source_node.get("questionCount", 0) or 0))
            wrong_count = max(0, int(source_node.get("wrongCount", 0) or 0))
            try:
                mastery_value = float(source_node.get("mastery", 0.0) or 0.0)
            except (TypeError, ValueError):
                mastery_value = 0.0
            mastery_value = min(1.0, max(0.0, mastery_value))
            weight = float(question_count if question_count > 0 else 1)
            collapsed_nodes[target_id]["questionCount"] = int(collapsed_nodes[target_id].get("questionCount", 0) or 0) + question_count
            collapsed_nodes[target_id]["wrongCount"] = int(collapsed_nodes[target_id].get("wrongCount", 0) or 0) + wrong_count
            mastery_sum_by_collapsed_id[target_id] = mastery_sum_by_collapsed_id.get(target_id, 0.0) + (mastery_value * weight)
            mastery_weight_by_collapsed_id[target_id] = mastery_weight_by_collapsed_id.get(target_id, 0.0) + weight

        for node_id, source_node in node_by_id.items():
            root_id = root_by_id.get(node_id, "")
            if root_id:
                _accumulate_metrics(root_id, source_node)
            second_id = second_by_id.get(node_id, "")
            if second_id and second_id != root_id:
                _accumulate_metrics(second_id, source_node)

        for collapsed_id, collapsed_node in collapsed_nodes.items():
            total_weight = mastery_weight_by_collapsed_id.get(collapsed_id, 0.0)
            collapsed_node["mastery"] = round(
                (mastery_sum_by_collapsed_id.get(collapsed_id, 0.0) / total_weight) if total_weight > 0 else 0.0,
                4,
            )
            question_count = max(0, int(collapsed_node.get("questionCount", 0) or 0))
            collapsed_node["size"] = self._knowledge_node_size(question_count)

        collapsed_links: List[Dict[str, object]] = [
            {"source": source_id, "target": target_id, "type": "parent"}
            for source_id, target_id in sorted(
                list(collapsed_parent_links),
                key=lambda item: (_node_sort_key(item[0]), _node_sort_key(item[1])),
            )
        ]

        prerequisite_seen: set[Tuple[str, str]] = set()
        for link in links:
            if str(link.get("type", "")).strip() != "prerequisite":
                continue
            source_id = str(link.get("source", "")).strip()
            target_id = str(link.get("target", "")).strip()
            if not source_id or not target_id:
                continue
            collapsed_source = second_by_id.get(source_id) or root_by_id.get(source_id, "")
            collapsed_target = second_by_id.get(target_id) or root_by_id.get(target_id, "")
            if not collapsed_source or not collapsed_target or collapsed_source == collapsed_target:
                continue
            if (collapsed_source, collapsed_target) in collapsed_parent_links:
                continue
            prerequisite_key = (collapsed_source, collapsed_target)
            if prerequisite_key in prerequisite_seen:
                continue
            prerequisite_seen.add(prerequisite_key)
            collapsed_links.append({"source": collapsed_source, "target": collapsed_target, "type": "prerequisite"})

        ordered_collapsed_nodes = sorted(
            collapsed_nodes.values(),
            key=lambda row: (
                max(0, int(row.get("level", 0) or 0)),
                max(0, int(row.get("sort", 0) or 0)),
                str(row.get("createTime", "") or ""),
                str(row.get("id", "") or ""),
            ),
        )
        return ordered_collapsed_nodes, collapsed_links

    def _resolve_knowledge_graph_scope_filters(
        self,
        actor: Optional[Actor],
        exam_category_code: str,
        joint_exam_group_code: str,
        subject_code: str,
        policy_version: str,
    ) -> Dict[str, str]:
        normalized = {
            "examCategoryCode": str(exam_category_code or "").strip(),
            "jointExamGroupCode": str(joint_exam_group_code or "").strip(),
            "subjectCode": str(subject_code or "").strip(),
            "policyVersionCode": str(policy_version or "").strip() or POLICY_VERSION_CODE,
        }
        if actor and hasattr(self, "_apply_required_list_scope"):
            scoped = self._apply_required_list_scope(  # type: ignore[attr-defined]
                {
                    "examCategoryCode": normalized["examCategoryCode"],
                    "jointExamGroupCode": normalized["jointExamGroupCode"],
                    "subjectCode": normalized["subjectCode"],
                },
                actor.role,
                actor.user_id,
            )
            normalized["examCategoryCode"] = str(scoped.get("examCategoryCode", "")).strip()
            normalized["jointExamGroupCode"] = str(scoped.get("jointExamGroupCode", "")).strip()
            normalized["subjectCode"] = str(scoped.get("subjectCode", "")).strip() or normalized["subjectCode"]

        if self._is_public_subject_code(normalized["subjectCode"]):
            # 公共课全员共享，不绑定单个专业组。
            normalized["examCategoryCode"] = ""
            normalized["jointExamGroupCode"] = ""
        elif normalized["jointExamGroupCode"] and not normalized["examCategoryCode"]:
            group = get_joint_exam_group(normalized["jointExamGroupCode"])
            if group:
                normalized["examCategoryCode"] = str(group.get("examCategoryCode", "")).strip()
        return normalized

    def _is_public_subject_code(self, subject_code: str) -> bool:
        normalized_subject_code = str(subject_code or "").strip()
        if not normalized_subject_code:
            return False
        public_subject_codes = {
            str(item.get("subjectCode", "")).strip()
            for item in PUBLIC_SUBJECTS
            if isinstance(item, dict) and str(item.get("subjectCode", "")).strip()
        }
        return normalized_subject_code in public_subject_codes

    def get_knowledge_tree(
        self,
        status: str = "",
        actor: Optional[Actor] = None,
        exam_category_code: str = "",
        joint_exam_group_code: str = "",
        subject_code: str = "",
        policy_version: str = POLICY_VERSION_CODE,
    ) -> Dict[str, List[Dict[str, object]]]:
        return self.list_knowledge_tree(
            status=status,
            actor=actor,
            exam_category_code=exam_category_code,
            joint_exam_group_code=joint_exam_group_code,
            subject_code=subject_code,
            policy_version=policy_version,
        )

    def parse_knowledge_graph_from_word(
        self,
        file_name: str,
        file_bytes: bytes,
        actor: Actor,
        exam_category_code: str,
        joint_exam_group_code: str,
        subject_code: str,
        policy_version: str = POLICY_VERSION_CODE,
    ) -> Dict[str, object]:
        normalized_file_name = str(file_name or "").strip() or "knowledge-graph.docx"
        if len(file_bytes or b"") <= 0:
            raise validation_failed("上传文件不能为空。")
        if len(file_bytes) > SYLLABUS_AI_MAX_FILE_SIZE:
            raise validation_failed("上传文件不能超过 10MB。")
        if not any(normalized_file_name.lower().endswith(suffix) for suffix in (".doc", ".docx")):
            raise validation_failed("知识图谱识别仅支持 DOC、DOCX 文件。")

        scope_filters = self._resolve_knowledge_graph_scope_filters(
            actor=actor,
            exam_category_code=exam_category_code,
            joint_exam_group_code=joint_exam_group_code,
            subject_code=subject_code,
            policy_version=policy_version,
        )
        normalized_subject_code = str(scope_filters.get("subjectCode", "")).strip()
        if not normalized_subject_code:
            raise validation_failed("请先通过三级联动选择科目，再上传大纲。")

        if actor.role != ROLE_SUPER_ADMIN:
            target_exam_category_code = str(scope_filters.get("examCategoryCode", "")).strip() or str(exam_category_code or "").strip()
            target_joint_exam_group_code = str(scope_filters.get("jointExamGroupCode", "")).strip() or str(joint_exam_group_code or "").strip()
            if target_exam_category_code or target_joint_exam_group_code:
                self._assert_actor_scope_write_access(actor, target_exam_category_code, target_joint_exam_group_code)

        extracted_text, extraction_meta = self._extract_syllabus_source_text(normalized_file_name, file_bytes)
        normalized_text = str(extracted_text or "").strip()
        if not normalized_text:
            raise validation_failed("未能从上传文件中提取有效文本，请检查文件内容。")

        knowledge_points_list = self._load_subject_knowledge_points_list(scope_filters)
        chapter_rows, parser_meta = self._parse_knowledge_outline_text(
            normalized_text,
            normalized_subject_code,
            knowledge_points_list,
        )
        if not chapter_rows:
            raise validation_failed("未识别到“章节-考点”结构，请检查文档格式后重试。")

        subject_name = self._resolve_subject_display_name(
            normalized_subject_code,
            str(scope_filters.get("jointExamGroupCode", "")).strip(),
        )
        point_bindings: List[Dict[str, object]] = []
        created_node_ids, recognized_node_ids = self._upsert_outline_to_knowledge_graph(
            chapter_rows,
            scope_filters,
            subject_name,
            knowledge_points_list,
            point_bindings=point_bindings,
        )
        auto_matched_points = [
            {
                "chapterName": str(item.get("chapterName", "")).strip(),
                "pointName": str(item.get("pointName", "")).strip(),
                "pointNodeId": str(item.get("pointNodeId", "")).strip(),
                "knowledgeId": str(item.get("knowledgeId", "")).strip(),
                "moduleCode": str(item.get("moduleCode", "")).strip(),
                "matchedName": str(item.get("matchedName", "")).strip(),
                "matchedLevel": int(item.get("matchedLevel", 0) or 0),
                "matchedParentName": str(item.get("matchedParentName", "")).strip(),
                "similarity": float(item.get("similarity", 0.0) or 0.0),
            }
            for item in point_bindings
            if bool(item.get("autoMatched", False))
        ]

        graph_payload = self.list_knowledge_tree(
            status="ENABLED",
            actor=actor,
            exam_category_code=str(scope_filters.get("examCategoryCode", "")).strip(),
            joint_exam_group_code=str(scope_filters.get("jointExamGroupCode", "")).strip(),
            subject_code=normalized_subject_code,
            policy_version=str(scope_filters.get("policyVersionCode", "")).strip() or POLICY_VERSION_CODE,
        )

        return {
            "scope": {
                "exam_category_code": str(scope_filters.get("examCategoryCode", "")).strip(),
                "joint_exam_group_code": str(scope_filters.get("jointExamGroupCode", "")).strip(),
                "subject_code": normalized_subject_code,
                "policy_version": str(scope_filters.get("policyVersionCode", "")).strip() or POLICY_VERSION_CODE,
            },
            "createdNodeIds": created_node_ids,
            "recognizedNodeIds": recognized_node_ids,
            "chapterCount": len(chapter_rows),
            "pointCount": sum(len(item.get("points", [])) for item in chapter_rows),
            "parserReport": {
                "sourceFileName": normalized_file_name,
                "sourceFileSize": len(file_bytes),
                "extractMethod": str(extraction_meta.get("method", "")),
                "extractTextLength": len(normalized_text),
                "extractTextPreview": normalized_text[:600],
                "parserMode": str(parser_meta.get("mode", "heuristic")),
                "model": str(parser_meta.get("model", "")),
                "knowledgePointCandidates": len(knowledge_points_list),
                "semanticPool": list(parser_meta.get("semanticPool", [])),
                "autoMatchedCount": int(parser_meta.get("autoMatchedCount", len(auto_matched_points)) or 0),
                "autoMatchedPoints": auto_matched_points,
            },
            "graph": graph_payload,
        }

    def _build_question_batch_parse_result(
        self,
        question_blocks: List[str],
        scope_filters: Dict[str, object],
        semantic_pool: List[Dict[str, object]],
        file_name: str = "",
        file_size: int = 0,
        extraction_meta: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        normalized_scope = {
            "exam_category_code": str(scope_filters.get("examCategoryCode", "")).strip(),
            "joint_exam_group_code": str(scope_filters.get("jointExamGroupCode", "")).strip(),
            "subject_code": str(scope_filters.get("subjectCode", "")).strip(),
            "policy_version": str(scope_filters.get("policyVersionCode", "")).strip() or POLICY_VERSION_CODE,
        }
        subject_type = self._resolve_batch_parse_subject_type(
            normalized_scope["exam_category_code"],
            normalized_scope["joint_exam_group_code"],
            normalized_scope["subject_code"],
        )
        semantic_pool_by_code = {
            str(item.get("pointCode", "")).strip(): item
            for item in semantic_pool
            if str(item.get("pointCode", "")).strip()
        }

        items: List[Dict[str, object]] = []
        errors: List[str] = []
        for index, block in enumerate(question_blocks, start=1):
            try:
                items.append(
                    self._build_question_batch_preview_item(
                        block,
                        normalized_scope,
                        semantic_pool,
                        semantic_pool_by_code,
                        subject_type,
                        index,
                    )
                )
            except Exception as exc:
                errors.append(f"第 {index} 题解析失败：{exc}")

        self._validate_question_batch_alignment(items, semantic_pool_by_code)
        return {
            **normalized_scope,
            "scope": normalized_scope,
            "deferred": False,
            "valid_count": len(items),
            "invalid_count": len(errors),
            "errors": errors,
            "items": items,
            "parserReport": {
                "sourceFileName": file_name,
                "sourceFileSize": file_size,
                "extractMethod": str((extraction_meta or {}).get("method", "")),
                "imageFormulaOcrEngines": list((extraction_meta or {}).get("imageFormulaOcrEngines", []))
                if isinstance((extraction_meta or {}).get("imageFormulaOcrEngines", []), list)
                else [],
                "imageChemicalOcrEngines": list((extraction_meta or {}).get("imageChemicalOcrEngines", []))
                if isinstance((extraction_meta or {}).get("imageChemicalOcrEngines", []), list)
                else [],
                "imageChemicalOcrSamples": list((extraction_meta or {}).get("imageChemicalOcrSamples", []))
                if isinstance((extraction_meta or {}).get("imageChemicalOcrSamples", []), list)
                else [],
                "semanticPoolSize": len(semantic_pool),
                "questionBlockCount": len(question_blocks),
            },
        }

    def _extract_question_blocks_from_text(self, source_text: str) -> List[str]:
        normalized_text = str(source_text or "").replace("\r\n", "\n")
        if "\n---\n" in normalized_text:
            return [block.strip() for block in normalized_text.split("\n---\n") if block.strip()]

        lines = [str(line or "").rstrip() for line in normalized_text.splitlines()]
        blocks: List[List[str]] = []
        current_block: List[str] = []
        blank_count = 0

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                if current_block and current_block[-1] != "":
                    current_block.append("")
                blank_count += 1
                continue
            
            # 检查是否是题目开始，即使前面没有空行
            if current_block and self._looks_like_question_start(line):
                # 检查当前块是否已经包含完整的题目内容
                if self._current_question_block_complete(current_block) or len(current_block) > 10:
                    blocks.append(current_block[:])
                    current_block = [line]
                    blank_count = 0
                    continue
            
            current_block.append(line)
            blank_count = 0

        if current_block:
            blocks.append(current_block[:])

        normalized_blocks = [
            "\n".join(line for line in block if line is not None).strip()
            for block in blocks
            if any(str(item or "").strip() for item in block)
        ]
        
        # 过滤掉太短的块，可能是标题或其他非题目内容
        filtered_blocks = []
        for block in normalized_blocks:
            # 检查块是否包含题目特征：选项和答案
            lines_in_block = block.splitlines()
            has_options = False
            has_answer = False
            
            for line in lines_in_block:
                if QUESTION_OPTION_LINE_PATTERN.match(line.strip()):
                    has_options = True
                elif self._is_answer_marker_line(line.strip()):
                    has_answer = True
            
            # 如果有选项或答案，或者块比较长，认为是题目
            if has_options or has_answer or len(lines_in_block) > 5:
                filtered_blocks.append(block)
        
        return filtered_blocks

    def _build_question_batch_preview_item(
        self,
        block: str,
        scope_filters: Dict[str, str],
        semantic_pool: List[Dict[str, object]],
        semantic_pool_by_code: Dict[str, Dict[str, object]],
        subject_type: str,
        index: int,
    ) -> Dict[str, object]:
        parsed = self._parse_question_block(block)
        alignment = self._align_question_block_to_semantic_pool(parsed, semantic_pool)
        aligned_knowledge_id = str(alignment.get("knowledgeId") or "").strip()
        point_code = str(alignment.get("pointCode") or "").strip()
        candidate = semantic_pool_by_code.get(point_code) if point_code else None
        knowledge_id = aligned_knowledge_id or (str(candidate.get("knowledgeId", "")).strip() if candidate else "")
        module_code = str(candidate.get("module_code", "")).strip() if candidate else ""
        chapter_code = str(alignment.get("chapterCode") or "").strip()
        raw_path_level_rows = alignment.get("path_levels", [])
        if not isinstance(raw_path_level_rows, list):
            raw_path_level_rows = []
        path_level_rows = self._collapse_path_levels_to_two_layers(raw_path_level_rows)
        if path_level_rows:
            knowledge_id = str(path_level_rows[-1].get("id", "")).strip() or knowledge_id
        knowledge_tags = self._build_two_level_knowledge_tags(path_level_rows)
        path_label = " / ".join(knowledge_tags) if knowledge_tags else " / ".join(
            [str(item.get("label", "")).strip() for item in path_level_rows if str(item.get("label", "")).strip()]
        )

        preview_item = {
            "preview_id": f"word-question-{index}",
            "title": str(parsed.get("title", "")).strip(),
            "content": str(parsed.get("content", "")).strip(),
            "type": str(parsed.get("type", "single_choice")).strip() or "single_choice",
            "options": parsed.get("options", []),
            "answer": str(parsed.get("answer", "")).strip(),
            "analysis": str(parsed.get("analysis", "")).strip(),
            "exam_category_code": scope_filters["exam_category_code"],
            "joint_exam_group_code": scope_filters["joint_exam_group_code"],
            "subject_code": scope_filters["subject_code"],
            "subject_type": subject_type,
            "policy_version": scope_filters["policy_version"],
            "knowledge_points": [knowledge_id] if knowledge_id else list(parsed.get("knowledge_points", [])),
            "knowledge_path": [str(item.get("id", "")).strip() for item in path_level_rows if str(item.get("id", "")).strip()],
            "knowledge_tags": knowledge_tags,
            "scope_path": [
                scope_filters["exam_category_code"],
                scope_filters["joint_exam_group_code"],
                scope_filters["subject_code"],
            ],
            "chapterCode": chapter_code or None,
            "pointCode": point_code or None,
            "module_code": module_code,
            "path_levels": path_level_rows,
            "path_label": path_label,
            "confidence": round(float(alignment.get("confidence", 0.0) or 0.0), 4),
            "manual_review_required": bool(alignment.get("manual_review_required", False)),
            "review_message": str(alignment.get("review_message", "")).strip(),
            "raw_block": block,
            "ext_json": {
                "chapterCode": chapter_code or "",
                "pointCode": point_code or "",
                "path_levels": path_level_rows,
                "path_label": path_label,
                "knowledgeTags": knowledge_tags,
            },
        }
        if knowledge_id:
            preview_item["ext_json"]["knowledgePointIds"] = [knowledge_id]
        return preview_item

    def _normalize_path_level_rows(self, rows: object) -> List[Dict[str, str]]:
        normalized_rows: List[Dict[str, str]] = []
        for item in rows if isinstance(rows, list) else []:
            if not isinstance(item, dict):
                continue
            node_id = str(item.get("id", "")).strip()
            label = str(item.get("label", "")).strip()
            if not node_id or not label:
                continue
            normalized_rows.append(
                {
                    "level": str(item.get("level", "")).strip(),
                    "id": node_id,
                    "code": str(item.get("code", "")).strip(),
                    "label": label,
                }
            )
        return normalized_rows

    def _is_generic_knowledge_path_label(self, label: str) -> bool:
        normalized_label = str(label or "").strip()
        if not normalized_label:
            return True
        return normalized_label in GENERIC_KNOWLEDGE_PATH_LABELS

    def _collapse_path_levels_to_two_layers(self, rows: object) -> List[Dict[str, str]]:
        normalized_rows = self._normalize_path_level_rows(rows)
        if not normalized_rows:
            return []
        if len(normalized_rows) <= 2:
            return normalized_rows
        root_row = normalized_rows[0]
        second_row = None
        for candidate in normalized_rows[1:]:
            if not self._is_generic_knowledge_path_label(str(candidate.get("label", ""))):
                second_row = candidate
                break
        if second_row is None:
            second_row = normalized_rows[1]
        if str(second_row.get("id", "")) == str(root_row.get("id", "")):
            return [root_row]
        return [root_row, second_row]

    def _build_two_level_knowledge_tags(self, rows: object) -> List[str]:
        tags: List[str] = []
        for item in self._collapse_path_levels_to_two_layers(rows):
            label = str(item.get("label", "")).strip()
            if label and label not in tags:
                tags.append(label)
        return tags[:2]

    def _select_question_batch_alignment_candidates(
        self,
        semantic_pool: List[Dict[str, object]],
    ) -> List[Dict[str, object]]:
        candidates: List[Dict[str, object]] = []
        for item in semantic_pool:
            knowledge_id = str(item.get("knowledgeId", "")).strip()
            if not knowledge_id:
                continue
            level = int(item.get("level", 0) or 0)
            if level < 2:
                continue
            candidates.append(item)
        return candidates

    def _parse_question_block(self, block: str) -> Dict[str, object]:
        text = str(block or "").strip()
        if not text:
            raise validation_failed("题目块为空。")

        stem_key = "题干"
        option_key = "选项"
        type_key = "题型"
        answer_key = "答案"
        analysis_key = "解析"
        title_key = "标题"
        knowledge_key = "知识点"

        fields = {}
        parse_fields = getattr(self, "_parse_template_block_fields", None)
        if callable(parse_fields):
            fields = parse_fields(text)

        if fields.get(stem_key):
            options = parse_question_option_lines(str(fields.get(option_key, "")).strip())
            inferred_type = self._infer_question_type(
                str(fields.get(type_key, "")).strip(),
                options,
                str(fields.get(answer_key, "")).strip(),
            )
            content = self._normalize_question_block_text(str(fields.get(stem_key, "")).strip())
            analysis = self._normalize_question_block_text(str(fields.get(analysis_key, "")).strip())
            answer = self._normalize_question_block_text(str(fields.get(answer_key, "")).strip())
            return {
                "title": str(fields.get(title_key, "")).strip() or content.splitlines()[0][:60],
                "content": content,
                "type": inferred_type,
                "options": options,
                "answer": answer,
                "analysis": analysis,
                "knowledge_points": self._parse_batch_knowledge_point_hints(str(fields.get(knowledge_key, ""))),
            }

        lines = [str(line or "").strip() for line in text.splitlines() if str(line or "").strip()]
        if not lines:
            raise validation_failed("题目块为空。")

        stem_lines: List[str] = []
        analysis_lines: List[str] = []
        answer_lines: List[str] = []
        knowledge_lines: List[str] = []
        options: List[Dict[str, str]] = []
        current_section = "stem"
        current_option: Optional[Dict[str, str]] = None

        for index, line in enumerate(lines):
            normalized_line = self._strip_question_number_prefix(line) if index == 0 else line
            if self._is_answer_marker_line(normalized_line):
                answer_value = self._strip_answer_marker(normalized_line)
                answer_lines = [answer_value] if answer_value else []
                current_section = "answer"
                current_option = None
                continue
            if self._is_analysis_marker_line(normalized_line):
                analysis_value = self._strip_analysis_marker(normalized_line)
                if analysis_value:
                    analysis_lines.append(analysis_value)
                current_section = "analysis"
                current_option = None
                continue
            if self._is_knowledge_marker_line(normalized_line):
                knowledge_value = self._strip_knowledge_marker(normalized_line)
                if knowledge_value:
                    knowledge_lines.append(knowledge_value)
                current_section = "knowledge"
                current_option = None
                continue
            option_match = QUESTION_OPTION_LINE_PATTERN.match(normalized_line)
            if option_match and current_section != "analysis":
                current_option = {
                    "key": option_match.group(1).strip().upper(),
                    "content": option_match.group(2).strip(),
                }
                options.append(current_option)
                current_section = "option"
                continue
            if current_section == "option" and current_option is not None:
                current_option["content"] = f"{str(current_option.get('content', '')).strip()}\n{normalized_line}".strip()
                continue
            if current_section == "answer":
                answer_lines.append(normalized_line)
                continue
            if current_section == "analysis":
                analysis_lines.append(normalized_line)
                continue
            if current_section == "knowledge":
                knowledge_lines.append(normalized_line)
                continue
            stem_lines.append(normalized_line)

        content = self._normalize_question_block_text("\n".join(stem_lines).strip()) or text[:500]
        answer = self._normalize_question_block_text("\n".join(answer_lines).strip())
        if not answer:
            answer = self._extract_marker_value_from_block(
                text,
                marker_aliases=("答案", "参考答案", "answer"),
                multiline=False,
            )
            answer = self._normalize_question_block_text(answer)
        analysis_text = self._normalize_question_block_text("\n".join(analysis_lines).strip())
        if not analysis_text:
            analysis_text = self._extract_marker_value_from_block(
                text,
                marker_aliases=("解析", "答案解析", "analysis", "explanation"),
                multiline=True,
            )
            analysis_text = self._normalize_question_block_text(analysis_text)
        knowledge_hint_text = "\n".join(knowledge_lines)
        if not str(knowledge_hint_text or "").strip():
            knowledge_hint_text = self._extract_marker_value_from_block(
                text,
                marker_aliases=("知识点", "knowledge"),
                multiline=True,
            )
        inferred_type = self._infer_question_type("", options, answer)
        return {
            "title": content.splitlines()[0][:60],
            "content": content,
            "type": inferred_type,
            "options": options,
            "answer": answer.strip(),
            "analysis": analysis_text,
            "knowledge_points": self._parse_batch_knowledge_point_hints(knowledge_hint_text),
        }

    def _extract_marker_value_from_block(
        self,
        block_text: str,
        marker_aliases: Tuple[str, ...],
        multiline: bool = False,
    ) -> str:
        text = str(block_text or "")
        if not text:
            return ""
        aliases = [re.escape(str(item or "").strip()) for item in marker_aliases if str(item or "").strip()]
        if not aliases:
            return ""
        marker_pattern = "|".join(aliases)
        bracket_pattern = rf"(?:【\s*(?:{marker_pattern})\s*】|\[\s*(?:{marker_pattern})\s*\]|(?:{marker_pattern})\s*[:：])"
        if multiline:
            pattern = re.compile(rf"{bracket_pattern}\s*(.+?)(?=\n\s*(?:【|\[|(?:{marker_pattern})\s*[:：])|\Z)", re.IGNORECASE | re.DOTALL)
        else:
            pattern = re.compile(rf"{bracket_pattern}\s*([^\r\n]+)", re.IGNORECASE)
        matched = pattern.search(text)
        if not matched:
            return ""
        return str(matched.group(1) or "").strip()

    def _parse_batch_knowledge_point_hints(self, raw_text: str) -> List[str]:
        normalized_text = str(raw_text or "").replace("\r\n", "\n").strip()
        if not normalized_text:
            return []
        chunks = [item.strip() for item in re.split(r"[\n;\uFF1B]+", normalized_text) if str(item or "").strip()]
        hints: List[str] = []
        for chunk in chunks:
            normalized_chunk = str(chunk or "").strip()
            if not normalized_chunk:
                continue
            # Keep full path expressions as one hint.
            if "->" in normalized_chunk or "=>" in normalized_chunk or "\u2192" in normalized_chunk or "\uFF0C" in normalized_chunk:
                hints.append(normalized_chunk)
                continue
            # Backward-compatible support: split multiple tags separated by ASCII comma.
            if "," in normalized_chunk:
                split_items = [item.strip() for item in normalized_chunk.split(",") if str(item or "").strip()]
                hints.extend(split_items)
                continue
            hints.append(normalized_chunk)

        deduped: List[str] = []
        seen: set[str] = set()
        for item in hints:
            key = str(item or "").strip()
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(key)
        return deduped[:20]

    def _normalize_knowledge_hint_token(self, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if not normalized:
            return ""
        normalized = re.sub(r"(\.{3,}|\u2026+)$", "", normalized)
        normalized = "".join(normalized.split())
        normalized = normalized.replace('"', "").replace("'", "").replace("`", "")
        normalized = (
            normalized.replace("\uFF0C", ",")
            .replace("\u3001", ",")
            .replace("\uFF1B", ";")
            .replace("\uFF1A", ":")
            .replace("\u3002", ".")
        )
        normalized = normalized.replace(",", "").replace(";", "").replace(":", "").replace(".", "")
        return normalized.strip("|")

    def _split_knowledge_hint_segments(self, raw_hint: str) -> List[str]:
        normalized_hint = str(raw_hint or "").strip()
        if not normalized_hint:
            return []
        normalized_hint = (
            normalized_hint.replace("\u2192", "->")
            .replace("\u279C", "->")
            .replace("\u27F6", "->")
            .replace("\uFF0C", ",")
            .replace("\u3001", ",")
            .replace("\uFF1B", ";")
            .replace(chr(0xFF1F), "?")
        )
        has_path_separator = any(token in normalized_hint for token in ("->", "=>", ">", "/", "\\", "|"))
        if has_path_separator:
            segments = re.split(r"\s*(?:->|=>|>|/|\\|\|)\s*", normalized_hint)
        else:
            segments = re.split(r"\s*(?:,|;|\?)\s*", normalized_hint)
        return [
            token
            for token in (self._normalize_knowledge_hint_token(item) for item in segments)
            if token
        ]

    def _count_suffix_label_matches(self, hint_segments: List[str], label_segments: List[str]) -> int:
        if not hint_segments or not label_segments:
            return 0
        matched = 0
        left_index = len(hint_segments) - 1
        right_index = len(label_segments) - 1
        while left_index >= 0 and right_index >= 0:
            if hint_segments[left_index] != label_segments[right_index]:
                break
            matched += 1
            left_index -= 1
            right_index -= 1
        return matched

    def _align_question_block_by_knowledge_hints(
        self,
        parsed_question: Dict[str, object],
        semantic_pool: List[Dict[str, object]],
    ) -> Optional[Dict[str, object]]:
        raw_hints = parsed_question.get("knowledge_points", [])
        if not isinstance(raw_hints, list):
            return None

        point_candidates = self._select_question_batch_alignment_candidates(semantic_pool)
        if not point_candidates:
            return None

        best_candidate: Optional[Dict[str, object]] = None
        best_rank: Tuple[int, int, int, int, float] = (0, 0, 0, 0, 0.0)
        best_hint_length = 0

        for raw_hint in raw_hints:
            hint_segments = self._split_knowledge_hint_segments(str(raw_hint or ""))
            if not hint_segments:
                continue
            best_hint_length = max(best_hint_length, len(hint_segments))
            hint_leaf_candidates = [hint_segments[-1]]
            max_tail_length = min(len(hint_segments), 6)
            for tail_length in range(2, max_tail_length + 1):
                hint_leaf_candidates.append("".join(hint_segments[-tail_length:]))

            for candidate in point_candidates:
                candidate_name = self._normalize_knowledge_hint_token(str(candidate.get("name", "")))
                if not candidate_name:
                    continue
                path_levels = candidate.get("path_levels", [])
                if not isinstance(path_levels, list):
                    path_levels = []
                candidate_path_segments = [
                    self._normalize_knowledge_hint_token(str(row.get("label", "")))
                    for row in path_levels
                    if self._normalize_knowledge_hint_token(str(row.get("label", "")))
                ]
                suffix_match_count = self._count_suffix_label_matches(hint_segments, candidate_path_segments)
                parent_suffix_match_count = self._count_suffix_label_matches(
                    hint_segments[:-1],
                    candidate_path_segments[:-1],
                )
                leaf_similarity = max(
                    (SequenceMatcher(None, leaf_candidate, candidate_name).ratio() for leaf_candidate in hint_leaf_candidates),
                    default=0.0,
                )
                exact_leaf = int(any(leaf_candidate == candidate_name for leaf_candidate in hint_leaf_candidates))
                contains_leaf = int(
                    any(
                        bool(leaf_candidate) and (leaf_candidate in candidate_name or candidate_name in leaf_candidate)
                        for leaf_candidate in hint_leaf_candidates
                    )
                )
                rank = (
                    exact_leaf,
                    suffix_match_count,
                    parent_suffix_match_count,
                    contains_leaf,
                    round(float(leaf_similarity), 4),
                )
                if rank > best_rank:
                    best_rank = rank
                    best_candidate = candidate

        if not best_candidate:
            return None

        exact_leaf, suffix_match_count, parent_suffix_match_count, contains_leaf, leaf_similarity = best_rank
        is_strong_match = (
            (exact_leaf == 1 and suffix_match_count >= 1)
            or suffix_match_count >= 2
            or parent_suffix_match_count >= 3
            or (contains_leaf == 1 and parent_suffix_match_count >= 2)
            or leaf_similarity >= 0.97
            or (contains_leaf == 1 and leaf_similarity >= 0.92)
        )
        if not is_strong_match:
            return None

        confidence = min(0.9999, 0.92 + min(0.06, suffix_match_count * 0.015) + max(0.0, leaf_similarity - 0.9))
        path_levels = best_candidate.get("path_levels", [])
        if not isinstance(path_levels, list):
            path_levels = []
        return {
            "knowledgeId": str(best_candidate.get("knowledgeId", "")).strip() or None,
            "chapterCode": str(best_candidate.get("chapterCode", "")).strip() or None,
            "pointCode": str(best_candidate.get("pointCode", "")).strip() or None,
            "confidence": round(float(confidence), 4),
            "manual_review_required": False,
            "review_message": "",
            "path_levels": list(path_levels),
        }

    def _infer_question_type(self, raw_type: str, options: List[Dict[str, str]], answer: str) -> str:
        normalized_type = str(raw_type or "").strip()
        if normalized_type in {"single_choice", "multiple_choice", "judge", "subjective"}:
            return normalized_type
        normalized_answer = re.sub(r"\s+", "", str(answer or "").strip().upper())
        option_text = " ".join(str(item.get("content", "")).strip() for item in options)
        if "正确" in option_text and "错误" in option_text:
            return "judge"
        if normalized_answer in {"正确", "错误", "对", "错"}:
            return "judge"
        if options and len(normalized_answer) > 1 and all(character in {"A", "B", "C", "D", "E", "F"} for character in normalized_answer):
            return "multiple_choice"
        if options:
            return "single_choice"
        return "subjective"

    def _align_question_block_to_semantic_pool(
        self,
        parsed_question: Dict[str, object],
        semantic_pool: List[Dict[str, object]],
    ) -> Dict[str, object]:
        hint_alignment = self._align_question_block_by_knowledge_hints(parsed_question, semantic_pool)
        if hint_alignment:
            return hint_alignment

        content = str(parsed_question.get("content", "")).strip()
        analysis = str(parsed_question.get("analysis", "")).strip()
        semantic_text = f"{content}\n{analysis}".strip()
        point_candidates = self._select_question_batch_alignment_candidates(semantic_pool)
        best_candidate = self._best_outline_semantic_candidate(semantic_text, point_candidates)
        if not best_candidate or float(best_candidate.get("similarity", 0.0) or 0.0) < QUESTION_BATCH_ALIGNMENT_THRESHOLD:
            return {
                "knowledgeId": None,
                "chapterCode": None,
                "pointCode": None,
                "confidence": round(float(best_candidate.get("similarity", 0.0) or 0.0), 4) if best_candidate else 0.0,
                "manual_review_required": True,
                "review_message": "建议手动标注",
                "path_levels": [],
            }

        return {
            "knowledgeId": str(best_candidate.get("knowledgeId", "")).strip() or None,
            "chapterCode": str(best_candidate.get("chapterCode", "")).strip() or None,
            "pointCode": str(best_candidate.get("pointCode", "")).strip() or None,
            "confidence": round(float(best_candidate.get("similarity", 0.0) or 0.0), 4),
            "manual_review_required": False,
            "review_message": "",
            "path_levels": list(best_candidate.get("path_levels", [])) if isinstance(best_candidate.get("path_levels", []), list) else [],
        }

    def _validate_question_batch_alignment(
        self,
        items: List[Dict[str, object]],
        semantic_pool_by_code: Dict[str, Dict[str, object]],
    ) -> None:
        for item in items:
            point_code = str(item.get("pointCode") or "").strip()
            if point_code.lower() == "none":
                continue
            if not point_code:
                continue
            if point_code not in semantic_pool_by_code:
                raise validation_failed("解析出的 point_code 不存在于 HB_ZSB_2026 知识树中。")

    def _build_question_semantic_pool(self, scope_filters: Dict[str, str]) -> List[Dict[str, object]]:
        repository_filters = self._build_knowledge_repository_filters(scope_filters)
        items = self.repository.list_knowledge("", repository_filters)
        if not items:
            normalized_subject_code = str(scope_filters.get("subjectCode", "")).strip()
            normalized_policy_version = str(scope_filters.get("policyVersionCode", "")).strip() or POLICY_VERSION_CODE
            if normalized_subject_code:
                fallback_filters = {
                    "subject_code": normalized_subject_code,
                    "subjectCode": normalized_subject_code,
                    "policy_version": normalized_policy_version,
                }
                items = self.repository.list_knowledge("", fallback_filters)
        if not items:
            return []

        node_map: Dict[str, Dict[str, object]] = {}
        children_by_parent: Dict[str, List[str]] = {}
        for item in items:
            knowledge_id = str(item.get("id", "")).strip()
            if not knowledge_id:
                continue
            ext_json = self._load_json_object(str(item.get("extJson", "{}")))
            parent_id = str(item.get("parentId", "") or "").strip()
            node_map[knowledge_id] = {
                "id": knowledge_id,
                "name": str(item.get("name", "")).strip() or knowledge_id,
                "parent_id": parent_id,
                "level": int(ext_json.get("level", 0) or 0),
                "sort": int(item.get("sort", 0) or 0),
                "create_time": str(item.get("createTime", "") or ""),
                "module_code": str(ext_json.get("moduleCode", "")).strip() or knowledge_id,
            }
            children_by_parent.setdefault(parent_id, []).append(knowledge_id)

        def sort_key(node_id: str) -> Tuple[int, str, str]:
            row = node_map.get(node_id, {})
            return (
                int(row.get("sort", 0) or 0),
                str(row.get("create_time", "")),
                str(row.get("id", "")),
            )

        for parent_id in list(children_by_parent.keys()):
            children_by_parent[parent_id] = sorted(children_by_parent[parent_id], key=sort_key)

        path_by_id: Dict[str, List[str]] = {}

        def build_path(node_id: str) -> List[str]:
            if node_id in path_by_id:
                return path_by_id[node_id]
            row = node_map.get(node_id, {})
            parent_id = str(row.get("parent_id", "")).strip()
            if not parent_id or parent_id not in node_map:
                path_by_id[node_id] = [node_id]
                return path_by_id[node_id]
            path_by_id[node_id] = build_path(parent_id) + [node_id]
            return path_by_id[node_id]

        chapter_code_by_id: Dict[str, str] = {}
        point_code_by_id: Dict[str, str] = {}
        chapter_ids = sorted(
            [node_id for node_id, row in node_map.items() if int(row.get("level", 0) or 0) == 4],
            key=sort_key,
        )
        for chapter_index, chapter_id in enumerate(chapter_ids, start=1):
            chapter_code_by_id[chapter_id] = f"CH_{chapter_index:03d}"
            point_ids = sorted(
                [
                    node_id
                    for node_id, row in node_map.items()
                    if int(row.get("level", 0) or 0) >= 5
                    and chapter_id in build_path(node_id)
                ],
                key=sort_key,
            )
            for point_index, point_id in enumerate(point_ids, start=1):
                point_code_by_id[point_id] = f"PT_{chapter_index:03d}_{point_index:03d}"

        semantic_pool: List[Dict[str, object]] = []
        for node_id, row in node_map.items():
            level = int(row.get("level", 0) or 0)
            if level < 2:
                continue
            full_path_ids = build_path(node_id)
            full_path_rows = [node_map[path_id] for path_id in full_path_ids if path_id in node_map]
            chapter_id = next((path_id for path_id in full_path_ids if int(node_map.get(path_id, {}).get("level", 0) or 0) == 4), "")
            semantic_pool.append(
                {
                    "knowledgeId": node_id,
                    "module_code": str(row.get("module_code", "")).strip() or node_id,
                    "name": str(row.get("name", "")).strip(),
                    "parent_name": str(node_map.get(str(row.get("parent_id", "")).strip(), {}).get("name", "")).strip(),
                    "level": level,
                    "chapterCode": chapter_code_by_id.get(chapter_id, ""),
                    "pointCode": point_code_by_id.get(node_id, "") if level >= 5 else "",
                    "path_levels": [
                        {
                            "level": f"L{int(path_row.get('level', 0) or 0)}",
                            "id": str(path_row.get("id", "")).strip(),
                            "code": (
                                point_code_by_id.get(str(path_row.get("id", "")).strip(), "")
                                if int(path_row.get("level", 0) or 0) >= 5
                                else chapter_code_by_id.get(str(path_row.get("id", "")).strip(), "")
                            ),
                            "label": str(path_row.get("name", "")).strip(),
                        }
                        for path_row in full_path_rows
                    ],
                }
            )
        semantic_pool.sort(key=lambda item: (int(item.get("level", 0) or 0), str(item.get("chapterCode", "")), str(item.get("pointCode", "")), str(item.get("name", ""))))
        return semantic_pool

    def _resolve_subject_display_name(self, subject_code: str, joint_exam_group_code: str = "") -> str:
        normalized_subject_code = str(subject_code or "").strip()
        if not normalized_subject_code:
            return "未命名科目"
        for item in PUBLIC_SUBJECTS:
            if not isinstance(item, dict):
                continue
            if str(item.get("subjectCode", "")).strip() == normalized_subject_code:
                return str(item.get("subjectName", normalized_subject_code)).strip() or normalized_subject_code
        joint_group = get_joint_exam_group(str(joint_exam_group_code or "").strip())
        if joint_group:
            for item in joint_group.get("professionalSubjects", []):
                if not isinstance(item, dict):
                    continue
                if str(item.get("subjectCode", "")).strip() == normalized_subject_code:
                    return str(item.get("subjectName", normalized_subject_code)).strip() or normalized_subject_code
        return normalized_subject_code

    def _build_knowledge_repository_filters(self, scope_filters: Dict[str, str]) -> Dict[str, str]:
        repository_filters: Dict[str, str] = {}
        normalized_subject_code = str(scope_filters.get("subjectCode", "")).strip()
        if not normalized_subject_code:
            return repository_filters

        normalized_policy_version = str(scope_filters.get("policyVersionCode", "")).strip() or POLICY_VERSION_CODE
        normalized_exam_category_code = str(scope_filters.get("examCategoryCode", "")).strip()
        normalized_joint_exam_group_code = str(scope_filters.get("jointExamGroupCode", "")).strip()

        repository_filters["subject_code"] = normalized_subject_code
        repository_filters["subjectCode"] = normalized_subject_code
        repository_filters["policy_version"] = normalized_policy_version
        repository_filters["policyVersion"] = normalized_policy_version
        repository_filters["policyVersionCode"] = normalized_policy_version
        if normalized_exam_category_code:
            repository_filters["exam_category_code"] = normalized_exam_category_code
            repository_filters["examCategoryCode"] = normalized_exam_category_code
        if normalized_joint_exam_group_code:
            repository_filters["joint_exam_group_code"] = normalized_joint_exam_group_code
            repository_filters["jointExamGroupCode"] = normalized_joint_exam_group_code
        return repository_filters

    def _load_subject_knowledge_points_list(self, scope_filters: Dict[str, str]) -> List[Dict[str, object]]:
        repository_filters = self._build_knowledge_repository_filters(scope_filters)
        items = self.repository.list_knowledge("", repository_filters)
        name_by_id: Dict[str, str] = {
            str(item.get("id", "")).strip(): str(item.get("name", "")).strip()
            for item in items
            if str(item.get("id", "")).strip()
        }
        knowledge_points_list: List[Dict[str, object]] = []
        for item in items:
            knowledge_id = str(item.get("id", "")).strip()
            if not knowledge_id:
                continue
            parent_id = str(item.get("parentId", "") or "").strip()
            ext_json = self._load_json_object(str(item.get("extJson", "{}")))
            module_code = str(ext_json.get("moduleCode", "")).strip() or knowledge_id
            knowledge_points_list.append(
                {
                    "id": knowledge_id,
                    "module_code": module_code,
                    "name": str(item.get("name", "")).strip(),
                    "parent_id": parent_id,
                    "parent_name": name_by_id.get(parent_id, ""),
                    "level": int(ext_json.get("level", 0) or 0),
                }
            )
        return knowledge_points_list

    def _parse_knowledge_outline_text(
        self,
        source_text: str,
        subject_code: str,
        knowledge_points_list: Optional[List[Dict[str, object]]] = None,
    ) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
        semantic_candidates = knowledge_points_list or []
        llm_rows, llm_meta = self._try_parse_knowledge_outline_with_llm(
            source_text,
            subject_code,
            semantic_candidates,
        )
        if llm_rows:
            aligned_rows, semantic_meta = self._align_outline_rows_with_semantic_pool(
                llm_rows,
                semantic_candidates,
                threshold=SEMANTIC_MATCH_THRESHOLD,
            )
            merged_meta = {
                "mode": str(llm_meta.get("mode", "llm") or "llm"),
                "model": str(llm_meta.get("model", "")),
                **semantic_meta,
            }
            return aligned_rows, merged_meta
        heuristic_rows = self._heuristic_parse_knowledge_outline(source_text)
        aligned_rows, semantic_meta = self._align_outline_rows_with_semantic_pool(
            heuristic_rows,
            semantic_candidates,
            threshold=SEMANTIC_MATCH_THRESHOLD,
        )
        merged_meta = {
            "mode": "heuristic",
            "model": str(llm_meta.get("model", "")),
            **semantic_meta,
        }
        return aligned_rows, merged_meta

    def _try_parse_knowledge_outline_with_llm(
        self,
        source_text: str,
        subject_code: str,
        knowledge_points_list: List[Dict[str, object]],
    ) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
        api_key = str(os.getenv("QB_OPENAI_API_KEY", "")).strip()
        if not api_key:
            return [], {"mode": "heuristic", "model": ""}
        base_url = str(os.getenv("QB_OPENAI_BASE_URL", "https://api.openai.com/v1")).strip().rstrip("/")
        model = str(os.getenv("QB_OPENAI_MODEL", "gpt-4o-mini")).strip() or "gpt-4o-mini"
        prompt = self._build_knowledge_outline_llm_prompt(source_text, subject_code, knowledge_points_list)
        try:
            response = httpx.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是知识图谱大纲解析助手，只输出 JSON，不要输出多余说明。",
                        },
                        {"role": "user", "content": prompt},
                    ],
                },
                timeout=45.0,
            )
            if response.status_code >= 400:
                return [], {"mode": "heuristic", "model": model}
            payload = response.json() if response.content else {}
            content = (
                payload.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                if isinstance(payload, dict)
                else ""
            )
            json_payload = self._extract_json_payload_from_text(str(content or ""))
            rows = self._normalize_knowledge_outline_payload(json_payload)
            if rows:
                return rows, {"mode": "llm", "model": model}
        except Exception:
            return [], {"mode": "heuristic", "model": model}
        return [], {"mode": "heuristic", "model": model}

    def _build_knowledge_outline_llm_prompt(
        self,
        source_text: str,
        subject_code: str,
        knowledge_points_list: List[Dict[str, object]],
    ) -> str:
        source_excerpt = str(source_text or "")[:20000]
        knowledge_points_payload = json.dumps(knowledge_points_list, ensure_ascii=False)
        return PROMPT_TEMPLATE.format(
            subject_code=str(subject_code or "").strip(),
            knowledge_points_list=knowledge_points_payload,
            source_excerpt=source_excerpt,
        )

    def _normalize_knowledge_outline_payload(self, payload: Dict[str, object]) -> List[Dict[str, object]]:
        rows = payload.get("chapters", []) if isinstance(payload, dict) else []
        if not isinstance(rows, list):
            return []
        normalized_rows: List[Dict[str, object]] = []
        seen_chapters: set[str] = set()
        for item in rows:
            if not isinstance(item, dict):
                continue
            chapter_name = self._normalize_outline_label(item.get("chapter", ""))
            if not chapter_name:
                continue
            chapter_key = chapter_name.lower()
            if chapter_key in seen_chapters:
                continue
            seen_chapters.add(chapter_key)
            raw_points = item.get("points", [])
            points = self._normalize_outline_point_entries(raw_points)
            if not points:
                continue
            normalized_rows.append({"chapter": chapter_name, "points": points})
        return normalized_rows[:120]

    def _heuristic_parse_knowledge_outline(self, source_text: str) -> List[Dict[str, object]]:
        lines = [str(line or "").strip() for line in str(source_text or "").splitlines()]
        lines = [line for line in lines if line]
        if not lines:
            return []

        rows: List[Dict[str, object]] = []
        current: Optional[Dict[str, object]] = None
        for line in lines:
            chapter_name = self._extract_chapter_heading(line)
            if chapter_name:
                current = {"chapter": chapter_name, "points": []}
                rows.append(current)
                continue

            point_name = self._normalize_outline_label(line)
            if not point_name:
                continue
            if self._is_outline_noise(point_name):
                continue
            if current is None:
                current = {"chapter": "导论", "points": []}
                rows.append(current)
            current["points"].append(point_name)

        normalized_rows: List[Dict[str, object]] = []
        for item in rows:
            chapter_name = self._normalize_outline_label(item.get("chapter", ""))
            if not chapter_name:
                continue
            points = self._normalize_outline_point_entries(item.get("points", []))
            if not points:
                continue
            normalized_rows.append({"chapter": chapter_name, "points": points})
        return normalized_rows[:120]

    def _extract_chapter_heading(self, line: str) -> str:
        normalized_line = self._normalize_outline_label(line)
        if not normalized_line:
            return ""
        chapter_patterns = (
            r"^第[一二三四五六七八九十百0-9]+章",
            r"^chapter\s*[0-9ivxlcdm]+",
        )
        lowered = normalized_line.lower()
        for pattern in chapter_patterns:
            if re.match(pattern, lowered if pattern.startswith("^chapter") else normalized_line, flags=re.IGNORECASE):
                return re.sub(r"^(第[一二三四五六七八九十百0-9]+章\s*|chapter\s*[0-9ivxlcdm]+\s*)", "", normalized_line, flags=re.IGNORECASE).strip() or normalized_line
        return ""

    def _normalize_outline_label(self, value: object) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        text = re.sub(r"^[\-•●■◆◇○\*\s]+", "", text)
        text = re.sub(r"^[0-9]+(?:\.[0-9]+)*[、.\s]+", "", text)
        text = re.sub(r"\s+", " ", text)
        return text[:100]

    def _normalize_outline_points(self, points: object) -> List[str]:
        return [item.get("name", "") for item in self._normalize_outline_point_entries(points)]

    def _normalize_outline_point_entries(self, points: object) -> List[Dict[str, object]]:
        if not isinstance(points, list):
            return []
        normalized_points: List[Dict[str, object]] = []
        seen: set[str] = set()
        for item in points:
            module_code = ""
            matched_name = ""
            knowledge_id = ""
            matched_level = 0
            matched_parent_name = ""
            similarity = 0.0
            auto_matched = False
            point_value: object = item
            if isinstance(item, dict):
                point_value = item.get("point", item.get("name", ""))
                # Keep core identifiers in camelCase during normalization.
                module_code = str(item.get("moduleCode") or item.get("module_code") or "").strip()
                matched_name = str(item.get("matchedName") or item.get("matched_name") or "").strip()
                knowledge_id = str(item.get("knowledgeId") or "").strip()
                matched_parent_name = str(item.get("matchedParentName") or item.get("matched_parent_name") or "").strip()
                try:
                    matched_level = int(item.get("matchedLevel") or item.get("matched_level") or 0)
                except (TypeError, ValueError):
                    matched_level = 0
                try:
                    similarity = float(item.get("similarity", 0.0) or item.get("similarity_score", 0.0) or 0.0)
                except (TypeError, ValueError):
                    similarity = 0.0
                auto_matched = bool(item.get("autoMatched") or item.get("auto_matched"))
            point_name = self._normalize_outline_label(point_value)
            if not point_name or self._is_outline_noise(point_name):
                continue
            point_key = point_name.lower()
            if point_key in seen:
                continue
            seen.add(point_key)
            point_entry: Dict[str, object] = {"name": point_name, "module_code": module_code[:128]}
            if matched_name:
                point_entry["matched_name"] = matched_name[:128]
            if knowledge_id:
                point_entry["knowledgeId"] = knowledge_id[:128]
            if matched_parent_name:
                point_entry["matched_parent_name"] = matched_parent_name[:128]
            if matched_level > 0:
                point_entry["matched_level"] = matched_level
            if similarity > 0:
                point_entry["similarity"] = round(min(1.0, max(0.0, similarity)), 4)
            if auto_matched:
                point_entry["auto_matched"] = True
            normalized_points.append(point_entry)
            if len(normalized_points) >= 200:
                break
        return normalized_points

    def _align_outline_rows_with_semantic_pool(
        self,
        chapter_rows: List[Dict[str, object]],
        knowledge_points_list: List[Dict[str, object]],
        threshold: float = SEMANTIC_MATCH_THRESHOLD,
    ) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
        semantic_pool = self._build_outline_semantic_pool(knowledge_points_list)
        if not semantic_pool:
            return chapter_rows, {"semanticPoolSize": 0, "autoMatchedCount": 0, "semanticPool": []}

        normalized_threshold = min(1.0, max(0.0, float(threshold or 0.0)))
        semantic_pool_by_code = {
            str(item.get("module_code", "")).strip(): item
            for item in semantic_pool
            if str(item.get("module_code", "")).strip()
        }
        aligned_rows: List[Dict[str, object]] = []
        auto_matched_points: List[Dict[str, object]] = []

        for chapter in chapter_rows:
            chapter_name = self._normalize_outline_label(chapter.get("chapter", ""))
            if not chapter_name:
                continue
            aligned_points: List[Dict[str, object]] = []
            for point_entry in self._normalize_outline_point_entries(chapter.get("points", [])):
                point_name = self._normalize_outline_label(point_entry.get("name", ""))
                if not point_name:
                    continue
                module_code = str(point_entry.get("module_code", "")).strip()
                matched_name = str(point_entry.get("matched_name", "")).strip()
                try:
                    similarity = float(point_entry.get("similarity", 0.0) or 0.0)
                except (TypeError, ValueError):
                    similarity = 0.0
                auto_matched = bool(point_entry.get("auto_matched", False))
                known_candidate = semantic_pool_by_code.get(module_code) if module_code else None
                matched_candidate = known_candidate
                if known_candidate and not matched_name:
                    matched_name = str(known_candidate.get("name", "")).strip()
                    similarity = max(similarity, self._semantic_similarity_score(point_name, matched_name))
                    matched_candidate = known_candidate

                best_candidate = self._best_outline_semantic_candidate(point_name, semantic_pool)
                if best_candidate:
                    best_score = float(best_candidate.get("similarity", 0.0) or 0.0)
                    candidate_module_code = str(best_candidate.get("module_code", "")).strip()
                    if (
                        best_score >= normalized_threshold
                        and (not module_code or module_code not in semantic_pool_by_code or best_score >= similarity)
                    ):
                        module_code = candidate_module_code
                        matched_name = str(best_candidate.get("name", "")).strip()
                        similarity = best_score
                        auto_matched = True
                        matched_candidate = best_candidate

                merged_entry: Dict[str, object] = {
                    "name": point_name,
                    "module_code": module_code[:128],
                }
                if matched_name:
                    merged_entry["matched_name"] = matched_name[:128]
                if matched_candidate:
                    merged_entry["knowledgeId"] = str(matched_candidate.get("knowledgeId", "")).strip()[:128]
                    merged_entry["matched_level"] = int(matched_candidate.get("level", 0) or 0)
                    merged_entry["matched_parent_name"] = str(matched_candidate.get("parent_name", "")).strip()[:128]
                if similarity > 0:
                    merged_entry["similarity"] = round(min(1.0, max(0.0, similarity)), 4)
                if auto_matched:
                    merged_entry["auto_matched"] = True
                    auto_matched_points.append(
                        {
                            "chapterName": chapter_name,
                            "pointName": point_name,
                            "knowledgeId": str(best_candidate.get("knowledgeId", "")).strip() if best_candidate else "",
                            "moduleCode": module_code[:128],
                            "matchedName": matched_name[:128],
                            "matchedLevel": int(best_candidate.get("level", 0) or 0) if best_candidate else 0,
                            "matchedParentName": str(best_candidate.get("parent_name", "")).strip()[:128] if best_candidate else "",
                            "similarity": round(min(1.0, max(0.0, similarity)), 4),
                        }
                    )
                aligned_points.append(merged_entry)
            if aligned_points:
                aligned_rows.append({"chapter": chapter_name, "points": aligned_points})

        return (
            aligned_rows,
            {
                "semanticPoolSize": len(semantic_pool),
                "autoMatchedCount": len(auto_matched_points),
                "semanticPool": semantic_pool,
                "autoMatchedPoints": auto_matched_points,
            },
        )

    def _build_outline_semantic_pool(self, knowledge_points_list: List[Dict[str, object]]) -> List[Dict[str, object]]:
        rows = list(knowledge_points_list or [])
        if not rows:
            return []
        available_levels = {
            int(item.get("level", 0) or 0)
            for item in rows
            if int(item.get("level", 0) or 0) > 0
        }
        if 4 in available_levels or 5 in available_levels:
            target_levels = {level for level in (4, 5) if level in available_levels}
        else:
            fallback_level = max(available_levels) if available_levels else 0
            target_levels = {fallback_level} if fallback_level > 0 else set()
        scoped_rows = [
            item
            for item in rows
            if str(item.get("name", "")).strip()
            and (
                not target_levels
                or int(item.get("level", 0) or 0) in target_levels
            )
        ]
        normalized_pool: List[Dict[str, object]] = []
        seen_keys: set[str] = set()
        for item in scoped_rows:
            knowledge_id = str(item.get("id", "")).strip()
            module_code = str(item.get("moduleCode") or "").strip() or knowledge_id
            name = str(item.get("name", "")).strip()
            if not module_code or not name:
                continue
            dedupe_key = f"{module_code}::{name}"
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            normalized_pool.append(
                {
                    "knowledgeId": knowledge_id,
                    "module_code": module_code,
                    "name": name,
                    "parent_name": str(item.get("parent_name", "")).strip(),
                    "level": int(item.get("level", 0) or 0),
                }
            )
        normalized_pool.sort(
            key=lambda item: (
                int(item.get("level", 0) or 0),
                str(item.get("parent_name", "")),
                str(item.get("name", "")),
                str(item.get("module_code", "")),
            )
        )
        return normalized_pool[:800]

    def _best_outline_semantic_candidate(
        self,
        point_name: str,
        semantic_pool: List[Dict[str, object]],
    ) -> Optional[Dict[str, object]]:
        normalized_point_name = self._normalize_outline_label(point_name)
        if not normalized_point_name:
            return None
        best: Optional[Dict[str, object]] = None
        best_score = 0.0
        for candidate in semantic_pool:
            candidate_name = str(candidate.get("name", "")).strip()
            if not candidate_name:
                continue
            score = self._semantic_similarity_score(normalized_point_name, candidate_name)
            parent_name = str(candidate.get("parent_name", "")).strip()
            if parent_name:
                score = max(
                    score,
                    self._semantic_similarity_score(normalized_point_name, f"{parent_name}{candidate_name}"),
                )
            if score > best_score:
                best_score = score
                best = candidate
        if not best:
            return None
        return {**best, "similarity": round(best_score, 4)}

    def _semantic_similarity_score(self, left: str, right: str) -> float:
        normalized_left = self._semantic_normalize_text(left)
        normalized_right = self._semantic_normalize_text(right)
        if not normalized_left or not normalized_right:
            return 0.0
        if normalized_left == normalized_right:
            return 1.0
        contains_score = 0.97 if normalized_left in normalized_right or normalized_right in normalized_left else 0.0
        seq_ratio = SequenceMatcher(None, normalized_left, normalized_right).ratio()
        jaccard = self._semantic_jaccard(normalized_left, normalized_right)
        prefix_bonus = 0.03 if normalized_left[:2] == normalized_right[:2] else 0.0
        blended = min(1.0, (seq_ratio * 0.64) + (jaccard * 0.33) + prefix_bonus)
        return round(max(contains_score, blended), 4)

    def _semantic_normalize_text(self, value: object) -> str:
        normalized = str(value or "").strip().lower()
        normalized = re.sub(r"\s+", "", normalized)
        normalized = re.sub(r"[\W_]+", "", normalized)
        return normalized

    def _semantic_jaccard(self, left: str, right: str) -> float:
        left_grams = self._semantic_ngrams(left)
        right_grams = self._semantic_ngrams(right)
        if not left_grams or not right_grams:
            return 0.0
        intersection = len(left_grams & right_grams)
        union = len(left_grams | right_grams)
        if union <= 0:
            return 0.0
        return intersection / union

    def _semantic_ngrams(self, value: str) -> set[str]:
        normalized = str(value or "")
        if not normalized:
            return set()
        if len(normalized) <= 2:
            return set(normalized)
        return {normalized[index:index + 2] for index in range(len(normalized) - 1)}

    def _is_outline_noise(self, text: str) -> bool:
        if not text:
            return True
        if len(text) <= 1:
            return True
        if len(text) > 100:
            return True
        if re.search(r"(附录|参考文献|目录|版权|声明|页码)", text):
            return True
        return False

    def _upsert_outline_to_knowledge_graph(
        self,
        chapter_rows: List[Dict[str, object]],
        scope_filters: Dict[str, str],
        subject_name: str,
        knowledge_points_list: Optional[List[Dict[str, object]]] = None,
        point_bindings: Optional[List[Dict[str, object]]] = None,
    ) -> Tuple[List[str], List[str]]:
        root_id, _ = self._ensure_subject_root_node(scope_filters, subject_name)
        created_node_ids: List[str] = []
        recognized_node_ids: List[str] = []
        module_code_to_id: Dict[str, str] = {}
        for item in knowledge_points_list or []:
            knowledge_id = str(item.get("id", "")).strip()
            if not knowledge_id:
                continue
            module_code_to_id.setdefault(knowledge_id, knowledge_id)
            module_code = str(item.get("moduleCode") or "").strip()
            if module_code:
                module_code_to_id.setdefault(module_code, knowledge_id)

        previous_last_point_id = ""
        for chapter in chapter_rows:
            chapter_name = self._normalize_outline_label(chapter.get("chapter", ""))
            if not chapter_name:
                continue
            chapter_id, chapter_created = self._ensure_scoped_knowledge_node(
                parent_id=root_id,
                name=chapter_name,
                scope_filters=scope_filters,
                status="ENABLED",
            )
            if chapter_created:
                created_node_ids.append(chapter_id)
            recognized_node_ids.append(chapter_id)

            point_ids: List[str] = []
            for point_entry in self._normalize_outline_point_entries(chapter.get("points", [])):
                point_name = point_entry.get("name", "")
                module_code = str(point_entry.get("module_code", "")).strip()
                matched_name = str(point_entry.get("matched_name", "")).strip()
                knowledge_id = str(point_entry.get("knowledgeId", "")).strip()
                matched_level = int(point_entry.get("matched_level", 0) or 0)
                matched_parent_name = str(point_entry.get("matched_parent_name", "")).strip()
                try:
                    similarity = float(point_entry.get("similarity", 0.0) or 0.0)
                except (TypeError, ValueError):
                    similarity = 0.0
                auto_matched = bool(point_entry.get("auto_matched", False))
                point_id, point_created = self._ensure_scoped_knowledge_node(
                    parent_id=chapter_id,
                    name=point_name,
                    scope_filters=scope_filters,
                    status="ENABLED",
                    module_code=module_code,
                    preferred_existing_id=module_code_to_id.get(module_code, ""),
                )
                point_ids.append(point_id)
                recognized_node_ids.append(point_id)
                if point_created:
                    created_node_ids.append(point_id)
                module_code_to_id.setdefault(point_id, point_id)
                if module_code:
                    module_code_to_id[module_code] = point_id
                if isinstance(point_bindings, list):
                    point_bindings.append(
                        {
                            "chapterName": chapter_name,
                            "pointName": point_name,
                            "pointNodeId": point_id,
                            "knowledgeId": knowledge_id,
                            "moduleCode": module_code or point_id,
                            "matchedName": matched_name,
                            "matchedLevel": matched_level,
                            "matchedParentName": matched_parent_name,
                            "similarity": round(min(1.0, max(0.0, similarity)), 4),
                            "autoMatched": auto_matched,
                            "created": bool(point_created),
                        }
                    )

            self._ensure_prerequisite_chain(point_ids)
            if previous_last_point_id and point_ids:
                self._append_prerequisite(point_ids[0], previous_last_point_id)
            if point_ids:
                previous_last_point_id = point_ids[-1]

        return (
            [item for item in dict.fromkeys(created_node_ids)],
            [item for item in dict.fromkeys(recognized_node_ids)],
        )

    def _ensure_subject_root_node(self, scope_filters: Dict[str, str], subject_name: str) -> Tuple[str, bool]:
        subject_code = str(scope_filters.get("subjectCode", "")).strip()
        if not subject_code:
            raise validation_failed("subject_code 不能为空。")
        roots = self.repository.list_knowledge_children(None, "")
        for item in roots:
            if self._knowledge_item_matches_scope(item, scope_filters):
                item_ext = self._load_json_object(str(item.get("extJson", "{}")))
                if int(item_ext.get("level", 1) or 1) == 1:
                    return str(item.get("id", "")).strip(), False

        payload = {
            "parentId": None,
            "name": str(subject_name or subject_code).strip() or subject_code,
            "sort": self.repository.get_max_knowledge_sort(None) + 10,
            "status": "ENABLED",
            "policyVersionCode": str(scope_filters.get("policyVersionCode", "")).strip() or POLICY_VERSION_CODE,
            "examCategoryCode": str(scope_filters.get("examCategoryCode", "")).strip(),
            "jointExamGroupCode": str(scope_filters.get("jointExamGroupCode", "")).strip(),
            "subjectCode": subject_code,
            "extJson": {
                "level": 1,
            },
        }
        record = self._build_knowledge_payload(payload)
        self.repository.create_knowledge(record)
        return str(record.get("id", "")).strip(), True

    def _ensure_scoped_knowledge_node(
        self,
        parent_id: str,
        name: str,
        scope_filters: Dict[str, str],
        status: str,
        module_code: str = "",
        preferred_existing_id: str = "",
    ) -> Tuple[str, bool]:
        normalized_parent_id = str(parent_id or "").strip() or None
        normalized_name = str(name or "").strip()
        normalized_module_code = str(module_code or "").strip()
        if not normalized_name:
            raise validation_failed("知识点名称不能为空。")

        if preferred_existing_id:
            preferred_existing = self.repository.get_knowledge(preferred_existing_id)
            if preferred_existing and self._knowledge_item_matches_scope(preferred_existing, scope_filters):
                self._sync_existing_knowledge_node_for_upsert(preferred_existing, status, normalized_module_code)
                return str(preferred_existing.get("id", "")).strip(), False

        if normalized_module_code:
            existing_by_id = self.repository.get_knowledge(normalized_module_code)
            if existing_by_id and self._knowledge_item_matches_scope(existing_by_id, scope_filters):
                self._sync_existing_knowledge_node_for_upsert(existing_by_id, status, normalized_module_code)
                return str(existing_by_id.get("id", "")).strip(), False

        siblings = self.repository.list_knowledge_children(normalized_parent_id, "")
        for item in siblings:
            if not self._knowledge_item_matches_scope(item, scope_filters):
                continue
            item_ext = self._load_json_object(str(item.get("extJson", "{}")))
            item_module_code = str(item_ext.get("moduleCode", "")).strip()
            if normalized_module_code and item_module_code and item_module_code == normalized_module_code:
                self._sync_existing_knowledge_node_for_upsert(item, status, normalized_module_code)
                return str(item.get("id", "")).strip(), False
            if str(item.get("name", "")).strip() == normalized_name:
                self._sync_existing_knowledge_node_for_upsert(item, status, normalized_module_code)
                return str(item.get("id", "")).strip(), False

        ext_json: Dict[str, object] = {
            "level": 2,
        }
        if normalized_module_code:
            ext_json["moduleCode"] = normalized_module_code
        payload = {
            "parentId": normalized_parent_id,
            "name": normalized_name,
            "sort": self.repository.get_max_knowledge_sort(normalized_parent_id) + 10,
            "status": status,
            "policyVersionCode": str(scope_filters.get("policyVersionCode", "")).strip() or POLICY_VERSION_CODE,
            "examCategoryCode": str(scope_filters.get("examCategoryCode", "")).strip(),
            "jointExamGroupCode": str(scope_filters.get("jointExamGroupCode", "")).strip(),
            "subjectCode": str(scope_filters.get("subjectCode", "")).strip(),
            "extJson": ext_json,
        }
        record = self._build_knowledge_payload(payload)
        self.repository.create_knowledge(record)
        return str(record.get("id", "")).strip(), True

    def _sync_existing_knowledge_node_for_upsert(self, node: Dict[str, object], status: str, module_code: str) -> None:
        normalized_module_code = str(module_code or "").strip()
        normalized_status = str(status or "").strip()
        ext_json = self._load_json_object(str(node.get("extJson", "{}")))
        updated = dict(node)
        dirty = False

        if normalized_status and str(node.get("status", "")).strip() != normalized_status:
            updated["status"] = normalized_status
            dirty = True

        if normalized_module_code and str(ext_json.get("moduleCode", "")).strip() != normalized_module_code:
            ext_json["moduleCode"] = normalized_module_code
            updated["extJson"] = ext_json
            dirty = True

        if not dirty:
            return
        updated["updateTime"] = self._now_iso()
        self.repository.update_knowledge(updated)

    def _knowledge_item_matches_scope(self, item: Dict[str, object], scope_filters: Dict[str, str]) -> bool:
        item_ext = self._load_json_object(str(item.get("extJson", "{}")))
        subject_code = str(scope_filters.get("subjectCode", "")).strip()
        if subject_code and str(item_ext.get("subjectCode", "")).strip() != subject_code:
            return False

        policy_version = str(scope_filters.get("policyVersionCode", "")).strip()
        if policy_version and str(item_ext.get("policyVersionCode", "")).strip() != policy_version:
            return False

        if self._is_public_subject_code(subject_code):
            return True

        joint_exam_group_code = str(scope_filters.get("jointExamGroupCode", "")).strip()
        item_joint_exam_group_code = str(item_ext.get("jointExamGroupCode", "")).strip()
        item_group_codes = {
            str(group_code or "").strip()
            for group_code in (
                item_ext.get("applicableGroups", [])
                if isinstance(item_ext.get("applicableGroups", []), list)
                else []
            )
            if str(group_code or "").strip()
        }
        if (
            joint_exam_group_code
            and item_joint_exam_group_code != joint_exam_group_code
            and joint_exam_group_code not in item_group_codes
        ):
            return False
        return True

    def _ensure_prerequisite_chain(self, node_ids: List[str]) -> None:
        if len(node_ids) < 2:
            return
        for index in range(1, len(node_ids)):
            self._append_prerequisite(node_ids[index], node_ids[index - 1])

    def _append_prerequisite(self, target_id: str, source_id: str) -> None:
        normalized_target_id = str(target_id or "").strip()
        normalized_source_id = str(source_id or "").strip()
        if not normalized_target_id or not normalized_source_id or normalized_target_id == normalized_source_id:
            return
        target = self.repository.get_knowledge(normalized_target_id)
        if not target:
            return
        ext_json = self._load_json_object(target.get("extJson", {}))
        prerequisites = self._knowledge_prerequisites(ext_json)
        if normalized_source_id in prerequisites:
            return
        prerequisites.append(normalized_source_id)
        ext_json["prerequisites"] = prerequisites

        updated = dict(target)
        updated["extJson"] = ext_json
        updated["updateTime"] = self._now_iso()
        self.repository.update_knowledge(updated)

    def list_knowledge_children(self, parent_id: str = "", status: str = "") -> List[Dict[str, object]]:
        normalized_parent_id = parent_id.strip() or None
        return self.repository.list_knowledge_children(normalized_parent_id, status.strip())

    def get_knowledge(self, knowledge_id: str) -> Dict[str, object]:
        knowledge = self.repository.get_knowledge(knowledge_id)
        if not knowledge:
            raise not_found("知识点不存在。")
        return knowledge

    def create_knowledge(self, payload: Dict[str, object]) -> Dict[str, object]:
        record = self._build_knowledge_payload(payload)
        self.repository.create_knowledge(record)
        return record

    def update_knowledge(self, knowledge_id: str, payload: Dict[str, object]) -> Dict[str, object]:
        existing = self.get_knowledge(knowledge_id)
        merged = dict(payload)
        merged["id"] = knowledge_id
        merged["createTime"] = existing["createTime"]
        record = self._build_knowledge_payload(merged, existing_id=knowledge_id)
        self.repository.update_knowledge(record)
        return record

    def update_knowledge_prerequisites(self, knowledge_id: str, payload: Dict[str, object]) -> Dict[str, object]:
        target = self.get_knowledge(knowledge_id)
        source_id = str(payload.get("sourceId", "")).strip()
        if not source_id:
            raise validation_failed("sourceId 不能为空。")
        if source_id == knowledge_id:
            raise validation_failed("sourceId 不能与目标知识点相同。")
        if not self.repository.get_knowledge(source_id):
            raise validation_failed("sourceId 不存在。")

        ext_json = self._load_json_object(target.get("extJson", {}))
        prerequisites = self._knowledge_prerequisites(ext_json)
        if source_id not in prerequisites:
            prerequisites.append(source_id)
        ext_json["prerequisites"] = prerequisites

        updated = dict(target)
        updated["extJson"] = ext_json
        updated["updateTime"] = self._now_iso()
        self.repository.update_knowledge(updated)
        return self.get_knowledge(knowledge_id)

    def save_knowledge_layout(self, payload: Dict[str, object]) -> Dict[str, object]:
        raw_nodes = payload.get("nodes")
        if not isinstance(raw_nodes, list) or not raw_nodes:
            raise validation_failed("nodes 不能为空。")

        updated_ids: List[str] = []
        for item in raw_nodes:
            if not isinstance(item, dict):
                raise validation_failed("nodes 内元素必须是对象。")
            knowledge_id = str(item.get("id", "")).strip()
            if not knowledge_id:
                raise validation_failed("nodes[].id 不能为空。")
            target = self.repository.get_knowledge(knowledge_id)
            if not target:
                raise validation_failed(f"知识点不存在：{knowledge_id}")

            x = self._normalize_graph_coordinate(item.get("x"), "nodes[].x")
            y = self._normalize_graph_coordinate(item.get("y"), "nodes[].y")

            ext_json = self._load_json_object(target.get("extJson", {}))
            ext_json["graphLayout"] = {"x": x, "y": y}

            updated = dict(target)
            updated["extJson"] = ext_json
            updated["updateTime"] = self._now_iso()
            self.repository.update_knowledge(updated)
            updated_ids.append(knowledge_id)

        return {
            "updatedCount": len(updated_ids),
            "updatedIds": updated_ids,
        }

    def delete_knowledge(self, knowledge_id: str, actor: Actor) -> Dict[str, object]:
        knowledge = self.get_knowledge(knowledge_id)
        if self.repository.count_knowledge_children(knowledge_id) > 0:
            raise validation_failed("存在子节点，不能直接删除。")
        snapshot_id = self._create_undo_snapshot(
            "knowledge_delete",
            {"knowledge": knowledge},
            actor,
        )
        self.repository.delete_knowledge(knowledge_id)
        return {"id": knowledge_id, "undoSnapshotId": snapshot_id, "undoExpireSec": 600}

    def restore_deleted_knowledge(self, snapshot_id: str, actor: Actor) -> Dict[str, object]:
        snapshot = self._consume_undo_snapshot(snapshot_id, "knowledge_delete", actor)
        payload = snapshot.get("payload", {})
        knowledge = payload.get("knowledge", {}) if isinstance(payload, dict) else {}
        if not isinstance(knowledge, dict) or not knowledge.get("id"):
            raise validation_failed("撤销快照数据损坏，无法恢复知识点。")
        knowledge_id = str(knowledge["id"])
        if self.repository.get_knowledge(knowledge_id):
            raise validation_failed("知识点已存在，无法重复恢复。")
        self.repository.create_knowledge(knowledge)
        return {"id": knowledge_id, "restored": True}

    def move_knowledge(self, knowledge_id: str, direction: str) -> Dict[str, object]:
        normalized_direction = direction.strip().lower()
        if normalized_direction not in {"up", "down"}:
            raise validation_failed("direction 仅支持 up 或 down。")
        current = self.get_knowledge(knowledge_id)
        siblings = self.repository.list_knowledge_children(current["parentId"], "")
        siblings.sort(key=lambda item: (int(item["sort"]), str(item["createTime"]), str(item["id"])))
        current_index = next((index for index, item in enumerate(siblings) if item["id"] == knowledge_id), -1)
        if current_index < 0:
            raise not_found("知识点不存在。")
        target_index = current_index - 1 if normalized_direction == "up" else current_index + 1
        if target_index < 0 or target_index >= len(siblings):
            boundary = "最前" if normalized_direction == "up" else "最后"
            raise validation_failed(f"当前节点已在{boundary}，无需继续移动。")
        reordered = list(siblings)
        moved = reordered.pop(current_index)
        reordered.insert(target_index, moved)
        self._reindex_knowledge_siblings(reordered)
        return self.get_knowledge(knowledge_id)
