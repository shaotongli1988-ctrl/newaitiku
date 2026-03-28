from __future__ import annotations

from app.service_shared import *


class InternalQuestionPaperServiceMixin:
    def _knowledge_question_count_map(self, knowledge_ids: set[str]) -> Dict[str, int]:
        counts: Dict[str, int] = {knowledge_id: 0 for knowledge_id in knowledge_ids}
        if not knowledge_ids:
            return counts
        for question in self._list_all_questions():
            knowledge_id = str(question.get("knowledgeId", "")).strip()
            if not knowledge_id or knowledge_id not in counts:
                continue
            counts[knowledge_id] = counts.get(knowledge_id, 0) + 1
        return counts

    def _knowledge_mastery_map(
        self,
        knowledge_ids: set[str],
        question_count_by_knowledge: Dict[str, int],
        viewer_student_user_id: str = "",
        subject_code: str = "",
        joint_exam_group_code: str = "",
    ) -> Dict[str, float]:
        mastery_map: Dict[str, float] = {knowledge_id: 0.0 for knowledge_id in knowledge_ids}
        history_rows = self._collect_graph_history_rows(
            viewer_student_user_id,
            subject_code=subject_code,
            joint_exam_group_code=joint_exam_group_code,
        )
        if not history_rows:
            return mastery_map

        history_by_knowledge: Dict[str, List[Dict[str, object]]] = {}
        for row in history_rows:
            knowledge_id = str(row.get("knowledgeId", "")).strip()
            if not knowledge_id or knowledge_id not in knowledge_ids:
                continue
            history_by_knowledge.setdefault(knowledge_id, []).append(row)

        global_average_duration = (
            sum(int(item.get("answerDurationSec", 0)) for item in history_rows) / len(history_rows)
            if history_rows
            else 60.0
        )
        if global_average_duration <= 0:
            global_average_duration = 60.0

        for knowledge_id in knowledge_ids:
            rows = history_by_knowledge.get(knowledge_id, [])
            answered = len(rows)
            correct = len([item for item in rows if item.get("isCorrect")])
            pool_total = max(1, int(question_count_by_knowledge.get(knowledge_id, 0)))
            if answered > 0:
                accuracy = correct / answered
                average_duration = sum(int(item.get("answerDurationSec", 0)) for item in rows) / answered
                speed = 1.0 if average_duration <= 0 else min(1.0, global_average_duration / average_duration)
                frequency = min(1.0, answered / pool_total)
            else:
                accuracy = 0.0
                speed = 0.0
                frequency = 0.0
            mastery_map[knowledge_id] = round((accuracy * 0.6) + (speed * 0.2) + (frequency * 0.2), 4)
        return mastery_map

    def _collect_graph_history_rows(
        self,
        viewer_student_user_id: str = "",
        subject_code: str = "",
        joint_exam_group_code: str = "",
    ) -> List[Dict[str, object]]:
        normalized_student_user_id = str(viewer_student_user_id or "").strip()
        normalized_subject_code = str(subject_code or "").strip()
        normalized_joint_exam_group_code = str(joint_exam_group_code or "").strip()
        public_subject_codes = {
            str(item.get("subjectCode", "")).strip()
            for item in PUBLIC_SUBJECTS
            if isinstance(item, dict) and str(item.get("subjectCode", "")).strip()
        }
        records = self._list_all_analytics_records({})
        history_rows: List[Dict[str, object]] = []
        for question in records:
            knowledge_id = str(question.get("knowledgeId", "")).strip()
            if not knowledge_id:
                continue
            analytics_payload = self._extract_analytics_payload(question)
            submitted_at = str(analytics_payload.get("submittedAt", "")).strip()
            if not submitted_at:
                continue
            if normalized_student_user_id:
                if str(analytics_payload.get("studentUserId", "")).strip() != normalized_student_user_id:
                    continue
            record_subject_code = str(analytics_payload.get("subjectCode", "")).strip()
            if normalized_subject_code and record_subject_code != normalized_subject_code:
                continue
            if (
                normalized_joint_exam_group_code
                and record_subject_code not in public_subject_codes
                and str(analytics_payload.get("jointExamGroupCode", "")).strip() != normalized_joint_exam_group_code
            ):
                continue
            history_rows.append(
                {
                    "knowledgeId": knowledge_id,
                    "isCorrect": bool(analytics_payload.get("isCorrect", False)),
                    "answerDurationSec": max(0, int(analytics_payload.get("answerDurationSec", 0))),
                }
            )
        return history_rows

    def _list_all_questions(self) -> List[Dict[str, str]]:
        filters = {"knowledgeId": "", "userId": "", "type": "", "status": "", "keyword": ""}
        _, total = self.repository.list_questions(filters, 1, 1, ROLE_SUPER_ADMIN, "")
        if total <= 0:
            return []
        items, _ = self.repository.list_questions(filters, 1, max(total, 1), ROLE_SUPER_ADMIN, "")
        return items

    def _knowledge_node_size(self, question_count: int) -> int:
        normalized = max(0, int(question_count))
        return int(round(20 + (math.log(normalized + 1) * 10)))

    def _knowledge_prerequisites(self, ext_json: Dict[str, object]) -> List[str]:
        raw_prerequisites = ext_json.get("prerequisites", [])
        normalized: List[str] = []
        if isinstance(raw_prerequisites, list):
            for item in raw_prerequisites:
                if isinstance(item, dict):
                    candidate = str(
                        item.get("id")
                        or item.get("knowledgeId")
                        or item.get("source")
                        or item.get("target")
                        or ""
                    ).strip()
                else:
                    candidate = str(item).strip()
                if candidate:
                    normalized.append(candidate)
        elif isinstance(raw_prerequisites, str):
            text = raw_prerequisites.strip()
            if text:
                try:
                    loaded = json.loads(text)
                except json.JSONDecodeError:
                    loaded = [segment.strip() for segment in text.split(",") if segment.strip()]
                if isinstance(loaded, list):
                    normalized.extend([str(item).strip() for item in loaded if str(item).strip()])
                elif isinstance(loaded, str) and loaded.strip():
                    normalized.append(loaded.strip())
        deduped: List[str] = []
        seen: set[str] = set()
        for item in normalized:
            if item in seen:
                continue
            deduped.append(item)
            seen.add(item)
        return deduped

    def _knowledge_layout_position(self, ext_json: Dict[str, object]) -> Optional[Tuple[float, float]]:
        layout = ext_json.get("graphLayout")
        if not isinstance(layout, dict):
            return None
        raw_x = layout.get("x")
        raw_y = layout.get("y")
        try:
            x = float(raw_x)
            y = float(raw_y)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(x) or not math.isfinite(y):
            return None
        return (x, y)

    def _normalize_graph_coordinate(self, value: object, field_name: str) -> float:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            raise validation_failed(f"{field_name} 必须是合法数字。")
        if not math.isfinite(numeric_value):
            raise validation_failed(f"{field_name} 必须是合法数字。")
        return round(numeric_value, 4)

    def _select_preview_items(self, items: List[Dict[str, str]], selected_indexes: Optional[List[int]]) -> List[Dict[str, str]]:
        if selected_indexes is None:
            return list(items)
        if not selected_indexes:
            raise validation_failed("请至少勾选 1 道预览题目。")
        normalized_indexes = sorted(set(selected_indexes))
        max_index = len(items) - 1
        for index in normalized_indexes:
            if index < 0 or index > max_index:
                raise validation_failed("所选预览题目不存在，请重新预览后再导入。")
        return [items[index] for index in normalized_indexes]

    def _import_error_log_file_name(self) -> str:
        return f"question-import-errors-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.log"

    def _build_import_error_log(self, errors: List[str]) -> str:
        if not errors:
            return ""
        lines = [
            "question-bank import error log",
            f"generatedAt={self._now_iso()}",
            f"errorCount={len(errors)}",
            "",
        ]
        for index, error in enumerate(errors, start=1):
            lines.append(f"{index}. {error}")
        return "\n".join(lines)

    def _assert_question_visible(self, question: Dict[str, str], actor: Actor) -> None:
        if (
            actor.role == ROLE_TEACHER
            and self._question_owner_user_id(question) != actor.user_id
            and question["status"] not in {"QA_IN_PROGRESS", "REVIEW_PENDING"}
        ):
            raise forbidden("教师只能查看自己的题目。")

    def _extract_review_reason(self, target_status: str, payload: Optional[Dict[str, object]]) -> str:
        request = parse_status_transition_payload_model(dict(payload or {})).model_dump()
        reason = str(request.get("reason", "")).strip()
        if target_status == "REJECTED" and not reason:
            raise validation_failed("驳回时必须填写原因。")
        return reason

    def _build_review_remark(
        self,
        actor_user_id: str,
        from_status: str,
        to_status: str,
        reason: str,
    ) -> str:
        base = f"{actor_user_id} 将状态从 {from_status} 更新为 {to_status}"
        if reason:
            return f"{base}，原因：{reason}"
        return base

    def _public_question(self, question: Dict[str, str]) -> Dict[str, str]:
        return {
            "id": question["id"],
            "knowledgeId": question["knowledgeId"],
            "userId": question["userId"],
            "type": question["type"],
            "stem": question["stem"],
            "optionsJson": question["optionsJson"],
            "answer": question["answer"],
            "status": question["status"],
            "extJson": question["extJson"],
            "createTime": question["createTime"],
            "updateTime": question["updateTime"],
        }

    def _build_question_record(
        self,
        payload: Dict[str, object],
        existing: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        payload = dict(payload)
        knowledge_id = str(payload.get("knowledgeId") or (existing["knowledgeId"] if existing else "")).strip()
        knowledge = self.repository.get_knowledge(knowledge_id)
        if not knowledge:
            raise validation_failed("knowledgeId 不存在。")
        if knowledge["status"] != "ENABLED":
            raise validation_failed("knowledgeId 对应知识点不可用。")
        now = self._now_iso()
        incoming_ext_json = self._load_json_object(str(payload.get("extJson") or (existing["extJson"] if existing else "{}")))
        ext_json = dict(incoming_ext_json)
        existing_ext = self._load_json_object(existing["extJson"]) if existing else {}
        question_context = self._build_question_context(knowledge)
        knowledge_changed = bool(existing and existing["knowledgeId"] != knowledge_id)

        ext_json["subjectId"] = question_context["subjectId"]
        ext_json["chapter"] = question_context["chapter"]
        ext_json["chapterCode"] = question_context["chapterCode"]
        ext_json["pointCode"] = question_context["pointCode"]
        ext_json["difficulty"] = str(ext_json.get("difficulty") or existing_ext.get("difficulty") or "medium")
        ext_json["analysis"] = str(ext_json.get("analysis") or existing_ext.get("analysis") or "")

        provided_knowledge_tags = ext_json.get("knowledgeTags")
        if knowledge_changed:
            ext_json["knowledgeTags"] = question_context["knowledgeTags"]
        elif isinstance(provided_knowledge_tags, list) and provided_knowledge_tags:
            ext_json["knowledgeTags"] = provided_knowledge_tags
        elif not existing_ext.get("knowledgeTags"):
            ext_json["knowledgeTags"] = question_context["knowledgeTags"]
        else:
            ext_json["knowledgeTags"] = existing_ext.get("knowledgeTags")

        ext_json.setdefault("paperBindings", existing_ext.get("paperBindings", []))
        ext_json.setdefault("practiceConfig", existing_ext.get("practiceConfig", {"timeLimitSec": 60}))
        ext_json.setdefault("reviewRemark", existing_ext.get("reviewRemark", ""))
        ext_json.setdefault("policyVersionCode", existing_ext.get("policyVersionCode", POLICY_VERSION_CODE))
        ext_json.setdefault("sourceType", existing_ext.get("sourceType", "manual"))
        self._normalize_question_content_tags(ext_json, incoming_ext_json, existing_ext, question_context, knowledge_changed)
        record = parse_question_model(
            {
                "id": str(payload.get("id") or (existing["id"] if existing else "")),
                "knowledgeId": knowledge_id,
                "userId": str(payload.get("userId") or (existing["userId"] if existing else "")).strip(),
                "type": str(payload.get("type") or (existing["type"] if existing else "")).strip(),
                "stem": str(payload.get("stem") or (existing["stem"] if existing else "")).strip(),
                "optionsJson": str(payload.get("optionsJson") or (existing["optionsJson"] if existing else "[]")),
                "answer": str(payload.get("answer") or (existing["answer"] if existing else "")).strip(),
                "status": str(payload.get("status") or (existing["status"] if existing else "")).strip(),
                "extJson": self._dump_json(ext_json),
                "createTime": str(payload.get("createTime") or (existing["createTime"] if existing else now)),
                "updateTime": now,
            }
        ).model_dump()
        return record

    def _normalize_question_content_tags(
        self,
        ext_json: Dict[str, object],
        incoming_ext_json: Dict[str, object],
        existing_ext: Dict[str, object],
        question_context: Dict[str, object],
        knowledge_changed: bool,
    ) -> None:
        subject_id = str(question_context.get("subjectId", "")).strip()
        module_code = self._resolve_question_module_code(incoming_ext_json, existing_ext, knowledge_changed)

        if self._is_public_subject_id(subject_id):
            ext_json["examCategoryCode"] = ""
            ext_json["jointExamGroupCode"] = ""
            ext_json["subjectCode"] = PUBLIC_SUBJECT_CODE_BY_SUBJECT_ID[subject_id]
            ext_json["subjectType"] = "PUBLIC"
            ext_json["moduleCode"] = module_code
            ext_json["applicableGroups"] = all_joint_exam_group_codes()
            return

        has_identity_change = any(
            self._was_question_ext_field_changed(incoming_ext_json, existing_ext, key)
            for key in ("subjectCode", "subjectType", "jointExamGroupCode")
        )
        is_create = not existing_ext

        if has_identity_change or is_create:
            candidate_exam_category_code = str(incoming_ext_json.get("examCategoryCode", "")).strip()
            candidate_subject_code = str(incoming_ext_json.get("subjectCode", "")).strip()
            candidate_subject_type = str(incoming_ext_json.get("subjectType", "")).strip()
            candidate_group_code = str(incoming_ext_json.get("jointExamGroupCode", "")).strip()

            if candidate_exam_category_code or candidate_subject_code or candidate_subject_type or candidate_group_code:
                professional_tags = self._resolve_professional_question_tags(
                    candidate_exam_category_code,
                    candidate_subject_code,
                    candidate_subject_type,
                    candidate_group_code,
                )
                ext_json.update(professional_tags)
            else:
                self._clear_question_professional_tags(ext_json)
        elif knowledge_changed:
            self._clear_question_professional_tags(ext_json)
        else:
            ext_json["examCategoryCode"] = str(existing_ext.get("examCategoryCode", "")).strip()
            ext_json["jointExamGroupCode"] = str(existing_ext.get("jointExamGroupCode", "")).strip()
            ext_json["subjectCode"] = str(existing_ext.get("subjectCode", "")).strip()
            ext_json["subjectType"] = str(existing_ext.get("subjectType", "")).strip()
            ext_json["applicableGroups"] = self._normalize_question_group_codes(existing_ext.get("applicableGroups", []))

        ext_json["moduleCode"] = module_code

    def _is_public_subject_id(self, subject_id: str) -> bool:
        return subject_id in PUBLIC_SUBJECT_CODE_BY_SUBJECT_ID

    def _resolve_question_module_code(
        self,
        incoming_ext_json: Dict[str, object],
        existing_ext: Dict[str, object],
        knowledge_changed: bool,
    ) -> str:
        existing_module_code = str(existing_ext.get("moduleCode", "")).strip()
        if "moduleCode" in incoming_ext_json:
            incoming_module_code = str(incoming_ext_json.get("moduleCode", "")).strip()
            if knowledge_changed and incoming_module_code == existing_module_code:
                return ""
            return incoming_module_code
        if knowledge_changed:
            return ""
        return existing_module_code

    def _was_question_ext_field_changed(
        self,
        incoming_ext_json: Dict[str, object],
        existing_ext: Dict[str, object],
        key: str,
    ) -> bool:
        if key not in incoming_ext_json:
            return False
        return str(incoming_ext_json.get(key, "")).strip() != str(existing_ext.get(key, "")).strip()

    def _clear_question_professional_tags(self, ext_json: Dict[str, object]) -> None:
        ext_json["examCategoryCode"] = ""
        ext_json["jointExamGroupCode"] = ""
        ext_json["subjectCode"] = ""
        ext_json["subjectType"] = ""
        ext_json["applicableGroups"] = []

    def _resolve_professional_question_tags(
        self,
        exam_category_code: str,
        subject_code: str,
        subject_type: str,
        joint_exam_group_code: str,
    ) -> Dict[str, object]:
        if not exam_category_code or not subject_code or not joint_exam_group_code:
            raise validation_failed("题目标签需同时提供 examCategoryCode、subjectCode、jointExamGroupCode。")
        joint_exam_group = get_joint_exam_group(joint_exam_group_code)
        if not joint_exam_group:
            raise validation_failed("jointExamGroupCode 不存在。")
        normalized_exam_category_code = str(joint_exam_group.get("examCategoryCode", "")).strip()
        if normalized_exam_category_code != exam_category_code:
            raise validation_failed("jointExamGroupCode 与 examCategoryCode 不匹配。")

        public_subject_codes = {str(item.get("subjectCode", "")).strip() for item in PUBLIC_SUBJECTS}
        if subject_code in public_subject_codes:
            return {
                "examCategoryCode": exam_category_code,
                "jointExamGroupCode": joint_exam_group_code,
                "subjectCode": subject_code,
                "subjectType": "PUBLIC",
                "applicableGroups": all_joint_exam_group_codes(),
            }

        normalized_subject_type = subject_type
        if not normalized_subject_type:
            matched_by_code = [
                item
                for item in joint_exam_group["professionalSubjects"]
                if item["subjectCode"] == subject_code
            ]
            if not matched_by_code:
                raise validation_failed("subjectCode 与 jointExamGroupCode 不匹配。")
            normalized_subject_type = str(matched_by_code[0].get("subjectType", "")).strip()

        matched_subject = next(
            (
                item
                for item in joint_exam_group["professionalSubjects"]
                if item["subjectCode"] == subject_code and item["subjectType"] == normalized_subject_type
            ),
            None,
        )
        if not matched_subject:
            raise validation_failed("subjectCode、subjectType 与 jointExamGroupCode 不匹配。")

        applicable_groups: List[str] = []
        for group in JOINT_EXAM_GROUPS:
            if any(
                item["subjectCode"] == subject_code and item["subjectType"] == normalized_subject_type
                for item in group["professionalSubjects"]
            ):
                applicable_groups.append(str(group["jointExamGroupCode"]))
        return {
            "examCategoryCode": normalized_exam_category_code,
            "jointExamGroupCode": joint_exam_group_code,
            "subjectCode": subject_code,
            "subjectType": normalized_subject_type,
            "applicableGroups": applicable_groups,
        }

    def _normalize_question_group_codes(self, value: object) -> List[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if str(item).strip()]

    def _question_ext_json(self, question: Dict[str, str]) -> Dict[str, object]:
        return self._load_json_object(question.get("extJson", "{}"))

    def _question_subject_id(self, question: Dict[str, str]) -> str:
        return str(self._question_ext_json(question).get("subjectId", ""))

    def _question_chapter(self, question: Dict[str, str]) -> str:
        return str(self._question_ext_json(question).get("chapter", ""))

    def _question_difficulty(self, question: Dict[str, str]) -> str:
        return str(self._question_ext_json(question).get("difficulty", ""))

    def _question_analysis(self, question: Dict[str, str]) -> str:
        return str(self._question_ext_json(question).get("analysis", ""))

    def _question_knowledge_tags(self, question: Dict[str, str]) -> List[str]:
        raw_tags = self._question_ext_json(question).get("knowledgeTags", [])
        return [str(item) for item in raw_tags] if isinstance(raw_tags, list) else []

    def _question_owner_user_id(self, question: Dict[str, str]) -> str:
        return str(question.get("userId", ""))

    def _build_question_context(self, knowledge: Dict[str, object]) -> Dict[str, object]:
        knowledge_chain = [knowledge]
        parent_id = knowledge.get("parentId")
        knowledge_id = str(knowledge.get("id", "")).strip()
        while parent_id:
            parent = self.repository.get_knowledge(str(parent_id))
            if not parent:
                break
            knowledge_chain.append(parent)
            parent_id = parent.get("parentId")
        knowledge_chain.reverse()
        subject_id = ""
        subject_code = ""
        policy_version_code = POLICY_VERSION_CODE
        exam_category_code = ""
        joint_exam_group_code = ""
        for item in reversed(knowledge_chain):
            item_ext = self._load_json_object(str(item.get("extJson", "{}")))
            subject_id = str(item_ext.get("subjectId", "")).strip() or subject_id
            subject_code = str(item_ext.get("subjectCode", "")).strip() or subject_code
            policy_version_code = str(item_ext.get("policyVersionCode", "")).strip() or policy_version_code
            exam_category_code = str(item_ext.get("examCategoryCode", "")).strip() or exam_category_code
            joint_exam_group_code = str(item_ext.get("jointExamGroupCode", "")).strip() or joint_exam_group_code
        chapter, chapter_code, point_code = self._resolve_question_chapter_point_codes(
            knowledge_chain,
            subject_code=subject_code,
            policy_version_code=policy_version_code,
            exam_category_code=exam_category_code,
            joint_exam_group_code=joint_exam_group_code,
        )
        knowledge_tags = [item["name"] for item in knowledge_chain[-2:]] if len(knowledge_chain) > 1 else [knowledge_chain[0]["name"]]
        seeded_context = self._seeded_question_context_for_knowledge(knowledge_id)
        if seeded_context.get("chapter"):
            chapter = str(seeded_context.get("chapter", "")).strip() or chapter
        if seeded_context.get("chapterCode"):
            chapter_code = str(seeded_context.get("chapterCode", "")).strip() or chapter_code
        if seeded_context.get("pointCode"):
            point_code = str(seeded_context.get("pointCode", "")).strip() or point_code
        if seeded_context.get("knowledgeTags"):
            knowledge_tags = list(seeded_context.get("knowledgeTags") or []) or knowledge_tags
        return {
            "subjectId": subject_id,
            "chapter": chapter,
            "chapterCode": chapter_code,
            "pointCode": point_code,
            "knowledgeTags": knowledge_tags[:3],
        }

    def _seeded_question_context_for_knowledge(self, knowledge_id: str) -> Dict[str, object]:
        normalized_knowledge_id = str(knowledge_id or "").strip()
        if not normalized_knowledge_id:
            return {}
        items, _ = self.repository.list_questions(
            {
                "knowledgeId": normalized_knowledge_id,
                "policyVersion": POLICY_VERSION_CODE,
            },
            1,
            20,
            ROLE_SUPER_ADMIN,
            "system-seeded-context",
        )
        for item in items:
            ext_json = self._load_json_object(str(item.get("extJson", "{}")))
            chapter = str(ext_json.get("chapter", "")).strip()
            chapter_code = str(ext_json.get("chapterCode", "")).strip()
            point_code = str(ext_json.get("pointCode", "")).strip()
            knowledge_tags = ext_json.get("knowledgeTags")
            if chapter or chapter_code or point_code or (isinstance(knowledge_tags, list) and knowledge_tags):
                return {
                    "chapter": chapter,
                    "chapterCode": chapter_code,
                    "pointCode": point_code,
                    "knowledgeTags": knowledge_tags if isinstance(knowledge_tags, list) else [],
                }
        return {}

    def _resolve_question_chapter_point_codes(
        self,
        knowledge_chain: List[Dict[str, object]],
        subject_code: str,
        policy_version_code: str,
        exam_category_code: str,
        joint_exam_group_code: str,
    ) -> Tuple[str, str, str]:
        if not knowledge_chain:
            return "", "", ""
        scoped_filters: Dict[str, str] = {}
        normalized_subject_code = str(subject_code or "").strip()
        normalized_policy_version = str(policy_version_code or "").strip() or POLICY_VERSION_CODE
        normalized_exam_category_code = str(exam_category_code or "").strip()
        normalized_joint_exam_group_code = str(joint_exam_group_code or "").strip()

        if normalized_subject_code:
            scoped_filters["subject_code"] = normalized_subject_code
            scoped_filters["subjectCode"] = normalized_subject_code
        scoped_filters["policy_version"] = normalized_policy_version
        scoped_filters["policyVersion"] = normalized_policy_version
        if normalized_exam_category_code:
            scoped_filters["exam_category_code"] = normalized_exam_category_code
            scoped_filters["examCategoryCode"] = normalized_exam_category_code
        if normalized_joint_exam_group_code:
            scoped_filters["joint_exam_group_code"] = normalized_joint_exam_group_code
            scoped_filters["jointExamGroupCode"] = normalized_joint_exam_group_code

        scoped_items = self.repository.list_knowledge("", scoped_filters) if normalized_subject_code else list(knowledge_chain)
        if not scoped_items:
            scoped_items = list(knowledge_chain)

        chain_levels = {self._knowledge_level(item) for item in knowledge_chain if self._knowledge_level(item) > 0}
        scoped_levels = {self._knowledge_level(item) for item in scoped_items if self._knowledge_level(item) > 0}

        if 4 in chain_levels:
            chapter_level_target = 4
        elif 3 in chain_levels:
            chapter_level_target = 3
        elif 2 in chain_levels:
            chapter_level_target = 2
        else:
            chapter_level_target = min(chain_levels) if chain_levels else (min(scoped_levels) if scoped_levels else 1)

        if 5 in chain_levels:
            point_level_target = 5
        elif (chapter_level_target + 1) in chain_levels:
            point_level_target = chapter_level_target + 1
        else:
            point_level_target = max(chain_levels) if chain_levels else (max(scoped_levels) if scoped_levels else chapter_level_target)

        chapter_node = self._select_chain_node_by_level(knowledge_chain, chapter_level_target)
        if not chapter_node and len(knowledge_chain) > 1:
            chapter_node = knowledge_chain[1]
        if not chapter_node:
            chapter_node = knowledge_chain[-1]
        chapter_name = str(chapter_node.get("name", "")).strip() if isinstance(chapter_node, dict) else ""
        chapter_id = str(chapter_node.get("id", "")).strip() if isinstance(chapter_node, dict) else ""

        chapter_candidates = self._sorted_knowledge_nodes(
            [item for item in scoped_items if self._knowledge_level(item) == chapter_level_target]
        )
        chapter_index_map = {str(item.get("id", "")).strip(): index for index, item in enumerate(chapter_candidates, start=1)}
        chapter_index = int(chapter_index_map.get(chapter_id, 0))
        chapter_code = f"CH_{chapter_index:03d}" if chapter_index > 0 else ""

        point_node = self._select_chain_node_by_level(knowledge_chain, point_level_target) or knowledge_chain[-1]
        point_id = str(point_node.get("id", "")).strip() if isinstance(point_node, dict) else ""
        point_level = self._knowledge_level(point_node) if isinstance(point_node, dict) else 0
        if point_level < point_level_target:
            return chapter_name, chapter_code, ""

        point_candidates = self._sorted_knowledge_nodes(
            [
                item
                for item in scoped_items
                if self._knowledge_level(item) == point_level_target
                and str(item.get("parentId", "") or "").strip() == chapter_id
            ]
        )
        if not point_candidates:
            fallback_parent_id = str(point_node.get("parentId", "") or "").strip() if isinstance(point_node, dict) else ""
            point_candidates = self._sorted_knowledge_nodes(
                [
                    item
                    for item in scoped_items
                    if self._knowledge_level(item) == point_level_target
                    and str(item.get("parentId", "") or "").strip() == fallback_parent_id
                ]
            )

        point_index_map = {str(item.get("id", "")).strip(): index for index, item in enumerate(point_candidates, start=1)}
        point_index = int(point_index_map.get(point_id, 0))
        point_code = f"PT_{chapter_index:03d}_{point_index:03d}" if chapter_index > 0 and point_index > 0 else ""
        return chapter_name, chapter_code, point_code

    def _select_chain_node_by_level(
        self,
        knowledge_chain: List[Dict[str, object]],
        target_level: int,
    ) -> Optional[Dict[str, object]]:
        normalized_target_level = max(1, int(target_level))
        for item in reversed(knowledge_chain):
            if self._knowledge_level(item) == normalized_target_level:
                return item
        return None

    def _knowledge_level(self, knowledge: Dict[str, object]) -> int:
        ext_json = self._load_json_object(str(knowledge.get("extJson", "{}")))
        try:
            level = int(ext_json.get("level", 0) or 0)
        except (TypeError, ValueError):
            return 0
        return level if level >= 0 else 0

    def _sorted_knowledge_nodes(self, items: List[Dict[str, object]]) -> List[Dict[str, object]]:
        return sorted(
            list(items),
            key=lambda item: (
                int(item.get("sort", 0) or 0),
                str(item.get("createTime", "")),
                str(item.get("id", "")),
            ),
        )

    def _build_knowledge_payload(self, payload: Dict[str, object], existing_id: str = "") -> Dict[str, object]:
        payload = dict(payload)
        now = self._now_iso()
        payload["id"] = str(payload.get("id") or f"knowledge-{uuid.uuid4().hex[:8]}")
        payload["parentId"] = str(payload.get("parentId") or "").strip() or None
        payload["createTime"] = str(payload.get("createTime") or now)
        payload["updateTime"] = now
        if "sort" not in payload or payload["sort"] in {"", None}:
            payload["sort"] = self.repository.get_max_knowledge_sort(payload["parentId"]) + 10
        payload["extJson"] = self._load_json_object(payload.get("extJson", {}))
        record = parse_knowledge_model(payload).model_dump()
        existing = self.repository.get_knowledge(existing_id) if existing_id else None
        parent = self._resolve_knowledge_parent(record["parentId"], existing_id)
        ext_json = dict(record["extJson"])
        existing_ext = self._load_json_object(str(existing.get("extJson", "{}"))) if existing else {}
        parent_ext = self._load_json_object(str(parent.get("extJson", "{}"))) if parent else {}

        policy_version_code = (
            str(record.get("policyVersionCode", "")).strip()
            or str(ext_json.get("policyVersionCode", "")).strip()
            or str(existing_ext.get("policyVersionCode", "")).strip()
            or POLICY_VERSION_CODE
        )
        subject_code = (
            str(record.get("subjectCode", "")).strip()
            or str(ext_json.get("subjectCode", "")).strip()
            or str(existing_ext.get("subjectCode", "")).strip()
            or str(parent_ext.get("subjectCode", "")).strip()
        )
        exam_category_code = (
            str(record.get("examCategoryCode", "")).strip()
            or str(ext_json.get("examCategoryCode", "")).strip()
            or str(existing_ext.get("examCategoryCode", "")).strip()
            or str(parent_ext.get("examCategoryCode", "")).strip()
        )
        joint_exam_group_code = (
            str(record.get("jointExamGroupCode", "")).strip()
            or str(ext_json.get("jointExamGroupCode", "")).strip()
            or str(existing_ext.get("jointExamGroupCode", "")).strip()
            or str(parent_ext.get("jointExamGroupCode", "")).strip()
        )

        public_subject_codes = {
            str(item.get("subjectCode", "")).strip()
            for item in PUBLIC_SUBJECTS
            if isinstance(item, dict) and str(item.get("subjectCode", "")).strip()
        }
        is_public_subject = bool(subject_code and subject_code in public_subject_codes)
        if joint_exam_group_code and not exam_category_code:
            joint_group = get_joint_exam_group(joint_exam_group_code)
            if joint_group:
                exam_category_code = str(joint_group.get("examCategoryCode", "")).strip()

        level = 1 if not parent else int(self._load_json_object(str(parent["extJson"])).get("level", 1)) + 1
        if level > 5:
            raise validation_failed("知识点层级仅支持 L1-L5。")
        ext_json["level"] = level
        ext_json["levelCode"] = level_code_from_level(level)
        ext_json["levelPath"] = level_path_from_level(level)
        ext_json["policyVersionCode"] = policy_version_code
        ext_json["subjectId"] = (
            str(ext_json.get("subjectId", "")).strip()
            or str(existing_ext.get("subjectId", "")).strip()
            or str(parent_ext.get("subjectId", "")).strip()
            or subject_id_from_subject_code(subject_code)
        )
        ext_json["subjectCode"] = subject_code
        ext_json["subjectType"] = "PUBLIC" if is_public_subject else str(ext_json.get("subjectType", "PROFESSIONAL")).strip() or "PROFESSIONAL"
        ext_json["examCategoryCode"] = "" if is_public_subject else exam_category_code
        ext_json["jointExamGroupCode"] = "" if is_public_subject else joint_exam_group_code
        if is_public_subject:
            ext_json["applicableGroups"] = subject_applicable_group_codes(subject_code) or all_joint_exam_group_codes()
        elif subject_code:
            ext_json["applicableGroups"] = subject_applicable_group_codes(subject_code) or ([joint_exam_group_code] if joint_exam_group_code else [])
        elif joint_exam_group_code:
            ext_json["applicableGroups"] = [joint_exam_group_code]
        else:
            ext_json["applicableGroups"] = []
        record["extJson"] = ext_json
        record.pop("policyVersionCode", None)
        record.pop("examCategoryCode", None)
        record.pop("jointExamGroupCode", None)
        record.pop("subjectCode", None)
        sibling = self.repository.get_knowledge_sibling_by_name(record["parentId"], record["name"], existing_id)
        if sibling:
            raise validation_failed("同级节点名称不能重复。")
        return record

    def _resolve_knowledge_parent(self, parent_id: Optional[str], existing_id: str = "") -> Optional[Dict[str, object]]:
        if not parent_id:
            return None
        if existing_id and parent_id == existing_id:
            raise validation_failed("parentId 不能指向自身。")
        parent = self.repository.get_knowledge(parent_id)
        if not parent:
            raise validation_failed("parentId 不存在。")
        if existing_id:
            current = parent
            while current and current.get("parentId"):
                if current["parentId"] == existing_id:
                    raise validation_failed("不能将节点移动到自己的子孙节点下。")
                current = self.repository.get_knowledge(str(current["parentId"]))
        return parent

    def _reindex_knowledge_siblings(self, siblings: List[Dict[str, object]]) -> None:
        now = self._now_iso()
        for index, item in enumerate(siblings, start=1):
            target_sort = index * 10
            if int(item["sort"]) == target_sort:
                continue
            payload = dict(item)
            payload["sort"] = target_sort
            payload["updateTime"] = now
            self.repository.update_knowledge(payload)

    def _assert_transition_allowed(
        self,
        question: Dict[str, str],
        current_status: str,
        target_status: str,
        actor: Actor,
    ) -> None:
        owner_user_id = self._question_owner_user_id(question)
        if current_status == "DRAFT" and target_status == "QA_IN_PROGRESS":
            if actor.role == ROLE_TEACHER and actor.user_id != owner_user_id:
                raise forbidden("只有题目拥有者才能提交 QA。")
            return
        if current_status == "DRAFT" and target_status == "REVIEW_PENDING":
            if actor.role == ROLE_TEACHER and actor.user_id != owner_user_id:
                raise forbidden("只有题目拥有者才能提交待审核。")
            return
        if current_status == "QA_IN_PROGRESS" and target_status == "REVIEW_PENDING":
            if actor.role == ROLE_SUPER_ADMIN:
                return
            if actor.role == ROLE_TEACHER and actor.user_id == owner_user_id:
                raise forbidden("QA 互审必须由另一名教师完成。")
            return
        if current_status == "REVIEW_PENDING" and target_status in {"PUBLISHED", "REJECTED"}:
            if actor.role != ROLE_TEACHER:
                raise forbidden("仅教师可执行终审发布或驳回。")
            if actor.user_id == owner_user_id:
                raise forbidden("终审发布或驳回必须由非题目所有者教师执行。")
            return
        if current_status == "REJECTED" and target_status == "DRAFT":
            if actor.role == ROLE_TEACHER and actor.user_id != owner_user_id:
                raise forbidden("驳回后的题目仅拥有者可重新编辑。")
            return

    def _assert_paper_status_allowed(self, paper_status: str) -> None:
        if paper_status not in PAPER_ALLOWED_STATUSES:
            raise validation_failed("paperStatus 仅支持 DRAFT、REVIEW_PENDING、PUBLISHED、OFFLINE。")

    def _assert_paper_transition_allowed(self, current_status: str, target_status: str) -> None:
        if current_status == target_status:
            raise invalid_status(f"试卷已处于 {target_status} 状态，无需重复流转。")
        allowed_statuses = PAPER_STATUS_TRANSITIONS.get(current_status, set())
        if target_status not in allowed_statuses:
            raise invalid_status(f"{current_status} 不能流转到 {target_status}。")

    def _paper_current_statuses(self, paper_id: str, actor: Actor) -> List[str]:
        status_set = set()
        for question in self.repository.list_visible_published_questions({}, actor.role, actor.user_id):
            for binding in self._paper_bindings(question):
                if binding.get("paperId") != paper_id:
                    continue
                status_set.add(str(binding.get("paperStatus", "")))
        return sorted(status_set)

    def _paper_bindings(self, question: Dict[str, str]) -> List[Dict[str, object]]:
        ext_json = self._load_json_object(question["extJson"])
        return list(ext_json.get("paperBindings", []))

    def _with_paper_bindings(self, question: Dict[str, str], paper_bindings: List[Dict[str, object]]) -> Dict[str, str]:
        enriched = dict(question)
        ext_json = self._load_json_object(enriched["extJson"])
        ext_json["paperBindings"] = paper_bindings
        enriched["extJson"] = self._dump_json(ext_json)
        return enriched

    def _filtered_paper_bindings(
        self,
        question: Dict[str, str],
        paper_id: str = "",
        paper_status: str = "",
    ) -> List[Dict[str, object]]:
        bindings = self._paper_bindings(question)
        if paper_id:
            bindings = [binding for binding in bindings if binding.get("paperId") == paper_id]
        if paper_status:
            bindings = [binding for binding in bindings if binding.get("paperStatus") == paper_status]
        return bindings

    def _visible_student_paper_bindings(self, question: Dict[str, str], student_user_id: str) -> List[Dict[str, object]]:
        return [
            binding
            for binding in self._paper_bindings(question)
            if binding.get("paperStatus") == "PUBLISHED"
            and binding.get("visibleToStudents", False)
            and (not binding.get("ownerStudentUserId") or binding.get("ownerStudentUserId") == student_user_id)
        ]

    def _build_manual_paper_question_scores(
        self,
        question_ids: List[str],
        total_score: int,
        question_scores: Optional[Dict[str, int]] = None,
    ) -> Dict[str, int]:
        if not question_ids:
            raise validation_failed("手动组卷至少选择一题。")

        if question_scores:
            normalized_scores: Dict[str, int] = {}
            for question_id in question_ids:
                if question_id not in question_scores:
                    raise validation_failed("questionScores 缺少已选题目的分值。")
                score = int(question_scores[question_id])
                if score < 1:
                    raise validation_failed("题目分值必须 >= 1。")
                normalized_scores[question_id] = score

            if sum(normalized_scores.values()) != total_score:
                raise validation_failed("totalScore 必须等于题目分值总和。")
            return normalized_scores

        question_score = total_score // len(question_ids)
        if question_score * len(question_ids) != total_score:
            raise validation_failed("总分必须能被题目数量整除，确保单题分值对齐。")
        return {question_id: question_score for question_id in question_ids}

    def _list_auto_paper_candidates(
        self,
        subject_id: str,
        chapter: str,
        difficulty: str,
        actor: Actor,
    ) -> List[Dict[str, str]]:
        return self.repository.list_visible_published_questions(
            {
                "subjectId": subject_id,
                "chapter": chapter.strip(),
                "difficulty": difficulty.strip(),
                "type": "",
            },
            actor.role,
            actor.user_id,
        )

    def _select_auto_paper_questions(
        self,
        available_questions: List[Dict[str, str]],
        type_rules: List[object],
        total_score: int,
    ) -> Tuple[List[str], Dict[str, int]]:
        selected_ids: List[str] = []
        question_score_map: Dict[str, int] = {}
        for rule in type_rules:
            candidates = [
                question
                for question in available_questions
                if question["type"] == rule.type and question["id"] not in selected_ids
            ]
            if len(candidates) < rule.count:
                raise validation_failed(f"{rule.type} 可匹配题目不足，无法自动组卷。")
            for question in candidates[: rule.count]:
                selected_ids.append(question["id"])
                question_score_map[question["id"]] = rule.questionScore
        if sum(question_score_map.values()) != total_score:
            raise validation_failed("自动组卷的题型分值总和必须与 totalScore 一致。")
        return selected_ids, question_score_map

    def _map_ai_difficulty_level(self, difficulty_level: int) -> str:
        if difficulty_level <= 2:
            return "easy"
        if difficulty_level == 3:
            return "medium"
        return "hard"

    def _with_updated_paper_status(
        self,
        bindings: List[Dict[str, object]],
        paper_id: str,
        paper_status: str,
    ) -> List[Dict[str, object]]:
        updated: List[Dict[str, object]] = []
        for binding in bindings:
            if binding.get("paperId") != paper_id:
                updated.append(binding)
                continue
            next_binding = dict(binding)
            next_binding["paperStatus"] = paper_status
            next_binding["visibleToStudents"] = paper_status == "PUBLISHED"
            updated.append(next_binding)
        return updated

    def _update_paper_bindings(
        self,
        paper_id: str,
        actor: Actor,
        binding_transform: Callable[[List[Dict[str, object]]], List[Dict[str, object]]],
    ) -> List[str]:
        touched_question_ids: List[str] = []
        for question in self.repository.list_visible_published_questions({}, actor.role, actor.user_id):
            paper_bindings = self._paper_bindings(question)
            updated_bindings = binding_transform(paper_bindings)
            if updated_bindings == paper_bindings:
                continue
            self.repository.update_question(self._with_paper_bindings(question, updated_bindings))
            touched_question_ids.append(question["id"])
        if not touched_question_ids:
            raise not_found("试卷不存在。")
        return touched_question_ids

    def _collect_paper_delete_snapshot(self, paper_id: str, actor: Actor) -> List[Dict[str, object]]:
        snapshot_rows: List[Dict[str, object]] = []
        for question in self.repository.list_visible_published_questions({}, actor.role, actor.user_id):
            matched = [binding for binding in self._paper_bindings(question) if binding.get("paperId") == paper_id]
            if not matched:
                continue
            snapshot_rows.append(
                {
                    "questionId": question["id"],
                    "paperBindings": [dict(binding) for binding in matched],
                }
            )
        return snapshot_rows

    def _save_paper_bindings(
        self,
        paper_id: str,
        paper_name: str,
        subject_id: str,
        paper_type: str,
        paper_status: str,
        duration_minutes: int,
        total_score: int,
        visible_to_students: bool,
        target_class_ids: List[str],
        question_ids: List[str],
        question_score_map: Dict[str, int],
        rule_mode: str,
        actor: Actor,
        exam_category_code: str = "",
        joint_exam_group_code: str = "",
        subject_code: str = "",
        owner_student_user_id: str = "",
    ) -> None:
        selected_questions = {question["id"]: question for question in self.repository.list_questions_by_ids(question_ids)}
        if len(selected_questions) != len(question_ids):
            raise validation_failed("存在不存在的题目，无法组卷。")
        if actor.role == ROLE_TEACHER:
            for question in selected_questions.values():
                if self._question_owner_user_id(question) != actor.user_id:
                    raise forbidden("教师只能组本人已发布题目。")
        for question in selected_questions.values():
            if question["status"] != "PUBLISHED":
                raise validation_failed("试卷管理仅允许已发布题目进入试卷。")
        visible_questions = self.repository.list_visible_published_questions({}, actor.role, actor.user_id)
        for question in visible_questions:
            paper_bindings = [binding for binding in self._paper_bindings(question) if binding.get("paperId") != paper_id]
            if question["id"] in selected_questions:
                paper_bindings.append(
                    {
                        "paperId": paper_id,
                        "paperName": paper_name,
                        "subjectId": subject_id,
                        "examCategoryCode": exam_category_code,
                        "jointExamGroupCode": joint_exam_group_code,
                        "subjectCode": subject_code,
                        "paperType": paper_type,
                        "paperStatus": paper_status,
                        "durationMinutes": duration_minutes,
                        "totalScore": total_score,
                        "questionScore": question_score_map[question["id"]],
                        "questionScoreMap": dict(question_score_map),
                        "targetClassIds": list(target_class_ids),
                        "orderNo": question_ids.index(question["id"]) + 1,
                        "ownerUserId": actor.user_id,
                        "ownerStudentUserId": owner_student_user_id,
                        "visibleToStudents": visible_to_students,
                        "ruleMode": rule_mode,
                    }
                )
            self.repository.update_question(self._with_paper_bindings(question, paper_bindings))

    def _list_questions_for_paper(self, paper_id: str, actor: Actor, visible_to_students: bool) -> List[Dict[str, str]]:
        questions = self.repository.list_visible_published_questions({}, ROLE_SUPER_ADMIN, actor.user_id)
        matched: List[Tuple[int, Dict[str, str]]] = []
        for question in questions:
            binding = self._get_binding_by_paper_id(question, paper_id, actor.user_id if visible_to_students else "")
            if not binding:
                continue
            if visible_to_students and (binding.get("paperStatus") != "PUBLISHED" or not binding.get("visibleToStudents", False)):
                continue
            if visible_to_students and not self._is_question_visible_to_student(question, actor.user_id):
                continue
            matched.append((int(binding.get("orderNo", 0)), self._with_paper_bindings(question, [binding])))
        matched.sort(key=lambda item: item[0])
        return [item[1] for item in matched]

    def _get_binding_by_paper_id(self, question: Dict[str, str], paper_id: str, student_user_id: str = "") -> Optional[Dict[str, object]]:
        for binding in self._paper_bindings(question):
            if binding.get("paperId") == paper_id:
                owner_student_user_id = binding.get("ownerStudentUserId", "")
                if student_user_id and owner_student_user_id and owner_student_user_id != student_user_id:
                    continue
                return binding
        return None

    def _load_template_content(self, file_name: str, file_bytes: bytes) -> str:
        if file_name.endswith(".docx"):
            return parse_word_content(file_bytes)
        return file_bytes.decode("utf-8")

    def _parse_template_questions(
        self,
        file_name: str,
        file_bytes: bytes,
        knowledge_id: str,
        actor: Actor,
    ) -> Tuple[List[Dict[str, str]], List[str]]:
        if not knowledge_id.strip():
            raise validation_failed("批量导入必须指定 knowledgeId。")
        if not any(file_name.lower().endswith(suffix) for suffix in QUESTION_IMPORT_SUFFIXES):
            raise validation_failed("模板导入仅支持 txt 或 docx 文件。")
        content = self._load_template_content(file_name, file_bytes)
        blocks = [block.strip() for block in content.split("\n---\n") if block.strip()]
        if not blocks:
            raise validation_failed("导入模板中没有可识别的题目块。")
        items: List[Dict[str, str]] = []
        errors: List[str] = []
        for index, block in enumerate(blocks, start=1):
            try:
                payload = self._build_question_from_block(block, knowledge_id, actor)
                items.append(self._build_question_record(payload))
            except Exception as exc:
                errors.append(f"第 {index} 题校对失败：{exc}")
        return items, errors

    def _build_question_from_block(
        self,
        block: str,
        knowledge_id: str,
        actor: Actor,
    ) -> Dict[str, str]:
        fields: Dict[str, str] = {}
        for line in block.splitlines():
            line = line.strip()
            if not line or not line.startswith("【") or "】" not in line:
                continue
            key, value = line.split("】", 1)
            fields[key[1:]] = value.strip()
        if "题干" not in fields or "答案" not in fields or "解析" not in fields:
            raise validation_failed("模板必须包含【题干】【答案】【解析】。")
        raw_tags = [item.strip() for item in fields.get("知识点", "").split(",") if item.strip()]
        if not raw_tags:
            raise validation_failed("模板中的【知识点】不能为空。")
        if len(raw_tags) > 3:
            raise validation_failed("模板中的【知识点】最多支持 3 个。")
        raw_options = fields.get("选项", "")
        if raw_options:
            options = []
            for option_line in raw_options.split("|"):
                option_line = option_line.strip()
                if not option_line:
                    continue
                if "." in option_line:
                    key, content = option_line.split(".", 1)
                elif "：" in option_line:
                    key, content = option_line.split("：", 1)
                else:
                    raise validation_failed("选项格式必须为 A.内容 或 A：内容。")
                options.append({"key": key.strip(), "content": content.strip()})
        else:
            options = []
        question_type = fields.get("题型", "single_choice")
        if question_type in {"single_choice", "multiple_choice", "judge"} and not options:
            raise validation_failed("客观题模板必须包含【选项】。")
        return {
            "id": f"question-{uuid.uuid4().hex[:8]}",
            "knowledgeId": knowledge_id,
            "userId": actor.user_id,
            "type": question_type,
            "stem": fields["题干"],
            "optionsJson": self._dump_json(options if options else []),
            "answer": fields["答案"],
            "status": "DRAFT",
            "extJson": self._dump_json(
                {
                    "source": "word_template_import",
                    "difficulty": fields.get("难度", "medium"),
                    "analysis": fields["解析"],
                    "knowledgeTags": raw_tags,
                    "rawTemplate": block,
                    "paperBindings": [],
                }
            ),
        }
