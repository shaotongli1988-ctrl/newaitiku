from __future__ import annotations

# Observability note: system endpoints should retain log/trace/metric evidence for release readiness.
from app.service_shared import *


class SystemServiceMixin:
    def _resolve_teacher_managed_scope(self, actor_user_id: str) -> Dict[str, set[str]]:
        managed_user = self._get_managed_user(actor_user_id) if hasattr(self, "_get_managed_user") else None
        if not isinstance(managed_user, dict):
            return {
                "student_ids": set(),
                "joint_group_codes": set(),
            }
        return {
            "student_ids": set(self._normalize_scope_id_list(managed_user.get("managedStudentIds", []))),
            "joint_group_codes": set(
                self._normalize_scope_id_list(managed_user.get("managedJointExamGroupCodes", []))
            ),
        }

    def list_tasks(self, filters: Dict[str, str], page: int, size: int, actor: Actor) -> Tuple[List[Dict[str, object]], int]:
        normalized = self._validate_task_filters(filters)
        user_scope = "" if actor.role == ROLE_SUPER_ADMIN else actor.user_id
        items, total = self.repository.list_tasks(normalized, page, size, user_scope)
        return [self._refresh_task(item, actor) for item in items], total

    def get_actor_task_ai_quota(self, actor: Actor) -> Dict[str, int]:
        if actor.role != ROLE_STUDENT:
            return {"dailyLimit": 0, "usedCount": 0}
        _, _, profile = self._load_student_profile_bundle(actor.user_id)
        self._assert_student_profile_complete(profile)
        ai_quota = self._current_ai_quota(profile)
        if profile.get("aiQuota") != ai_quota:
            self.repository.set_student_profile_ai_quota(actor.user_id, ai_quota, self._now_iso())
        return {
            "dailyLimit": int(ai_quota.get("dailyLimit", 0)),
            "usedCount": int(ai_quota.get("usedCount", 0)),
        }

    def get_task(self, task_id: str, actor: Actor) -> Dict[str, object]:
        task = self.repository.get_task(task_id)
        if not task:
            raise task_not_found("任务不存在。")
        self._assert_task_access(task, actor)
        return self._refresh_task(task, actor)

    def cancel_task(self, task_id: str, actor: Actor) -> Dict[str, object]:
        task = self.repository.get_task(task_id)
        if not task:
            raise task_not_found("任务不存在。")
        self._assert_task_access(task, actor)
        if task["status"] in {"COMPLETED", "FAILED", "CANCELLED"}:
            raise task_validation_failed("任务已结束，不能重复取消。")
        now = self._now_iso()
        ext_json = self._load_json_object(str(task["extJson"]))
        queue = dict(ext_json.get("queue", {}))
        queue["cancelledAt"] = now
        ext_json["queue"] = queue
        ext_json["errorMessage"] = "任务已由用户取消。"
        ext_json["resultSummary"] = "任务已取消。"
        task["status"] = "CANCELLED"
        task["progress"] = 100
        task["extJson"] = self._dump_json(ext_json)
        task["updateTime"] = now
        self.repository.update_task(task)
        return task

    def list_questions(self, filters: Dict[str, str], page: int, size: int, actor: Actor):
        db_filters = self._pick_filters(
            filters,
            (
                "knowledgeId",
                "questionIds",
                "question_ids",
                "userId",
                "type",
                "status",
                "keyword",
                "chapterCode",
                "chapter_code",
                "pointCode",
                "point_code",
            ),
        )
        return self._list_questions_with_optional_content_filter(db_filters, filters, page, size, actor)

    def get_content_baseline(self) -> Dict[str, object]:
        baseline = build_content_baseline()
        questions = self.repository.list_visible_published_questions({}, ROLE_SUPER_ADMIN, "system")
        coverage_by_group: Dict[str, int] = {}
        coverage_by_subject: Dict[str, int] = {}
        for question in questions:
            ext_json = self._load_json_object(question["extJson"])
            subject_code = str(ext_json.get("subjectCode", ""))
            if subject_code:
                coverage_by_subject[subject_code] = coverage_by_subject.get(subject_code, 0) + 1
            for group_code in ext_json.get("applicableGroups", []):
                coverage_by_group[group_code] = coverage_by_group.get(group_code, 0) + 1
        for category in baseline["examCategories"]:
            for group in category["jointExamGroups"]:
                group["questionCount"] = coverage_by_group.get(group["jointExamGroupCode"], 0)
                for subject in group["subjects"]:
                    subject["questionCount"] = coverage_by_subject.get(subject["subjectCode"], 0)
        return baseline

    def get_system_console(self) -> Dict[str, object]:
        directory = sorted(self._managed_users(), key=lambda item: (item["role"], item["userId"]))
        preview_size = 20
        return {
            "systemSettings": self._system_settings(),
            "managedUsers": directory[:preview_size],
            "managedUsersPagination": {"page": 1, "size": preview_size, "total": len(directory)},
            "summary": self._build_system_console_summary(directory),
        }

    def get_system_settings(self) -> Dict[str, object]:
        return self._system_settings()

    def save_system_settings(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        settings = parse_system_settings_model(payload).model_dump()
        self._save_system_settings_value(settings)
        self._notify_system_settings_updated(actor.user_id)
        return settings

    def list_syllabus_versions(self) -> Dict[str, object]:
        versions = self._sorted_syllabus_versions(self._syllabus_versions())
        selected_version_id = str(versions[0]["versionId"]) if versions else ""
        return {
            "versions": [self._serialize_syllabus_version(version) for version in versions],
            "selectedVersionId": selected_version_id,
        }

    def get_paper_target_weight_profile(self, knowledge_ids: Optional[List[str]] = None) -> Dict[str, object]:
        normalized_ids = []
        seen_ids: set[str] = set()
        for knowledge_id in (knowledge_ids or []):
            normalized_id = str(knowledge_id or "").strip()
            if not normalized_id or normalized_id in seen_ids:
                continue
            seen_ids.add(normalized_id)
            normalized_ids.append(normalized_id)

        versions = self._sorted_syllabus_versions(self._syllabus_versions())
        if not versions:
            return {
                "selectedVersionId": "",
                "selectedVersionName": "",
                "knowledgeWeights": [],
                "targetWeightMap": {},
            }

        selected_version = self._serialize_syllabus_version(versions[0])
        source_weights = selected_version.get("knowledgeWeights", [])
        if not isinstance(source_weights, list):
            source_weights = []
        if normalized_ids:
            selected_id_set = set(normalized_ids)
            source_weights = [
                weight_item
                for weight_item in source_weights
                if str(weight_item.get("knowledgeId", "")).strip() in selected_id_set
            ]

        target_weight_map = {}
        for weight_item in source_weights:
            knowledge_id = str(weight_item.get("knowledgeId", "")).strip()
            if not knowledge_id:
                continue
            target_weight_map[knowledge_id] = float(weight_item.get("targetWeight", 0))

        return {
            "selectedVersionId": str(selected_version.get("versionId", "")),
            "selectedVersionName": str(selected_version.get("versionName", "")),
            "knowledgeWeights": source_weights,
            "targetWeightMap": target_weight_map,
        }

    def create_syllabus_version(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        request = parse_syllabus_version_create_model(payload).model_dump()
        version_name = str(request.get("versionName", "")).strip()
        copy_from_version_id = str(request.get("copyFromVersionId", "")).strip()
        if not version_name:
            raise validation_failed("versionName 不能为空。")
        system_state = self._load_system_state()
        versions = self._normalize_syllabus_versions(system_state.get("syllabusVersions", []))
        existing_names = {str(item.get("versionName", "")).strip().lower() for item in versions}
        if version_name.lower() in existing_names:
            raise validation_failed("大纲版本名称已存在，请使用其他名称。")
        base_weights: List[Dict[str, object]] = []
        if copy_from_version_id:
            source = next((item for item in versions if str(item.get("versionId", "")) == copy_from_version_id), None)
            if not source:
                raise validation_failed("copyFromVersionId 不存在。")
            base_weights = [
                {
                    "knowledgeId": str(weight["knowledgeId"]),
                    "knowledgeName": str(weight["knowledgeName"]),
                    "targetWeight": float(weight["targetWeight"]),
                    "sort": int(weight["sort"]),
                }
                for weight in source.get("knowledgeWeights", [])
                if isinstance(weight, dict)
            ]
        else:
            base_weights = self._default_syllabus_knowledge_weights()
        if not base_weights:
            raise validation_failed("当前没有可用知识点，无法创建大纲版本。")
        now = self._now_iso()
        version_id = f"syllabus-{uuid.uuid4().hex[:8]}"
        new_version = {
            "versionId": version_id,
            "versionName": version_name,
            "knowledgeWeights": base_weights,
            "createTime": now,
            "updateTime": now,
            "operatorUserId": actor.user_id,
        }
        versions.append(new_version)
        system_state["syllabusVersions"] = versions[-100:]
        self._save_system_state(system_state)
        return {
            "version": self._serialize_syllabus_version(new_version),
            "selectedVersionId": version_id,
            "versions": [self._serialize_syllabus_version(item) for item in self._sorted_syllabus_versions(versions)],
        }

    def save_syllabus_weights(self, version_id: str, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        normalized_version_id = str(version_id or "").strip()
        if not normalized_version_id:
            raise validation_failed("versionId 不能为空。")
        request = parse_syllabus_weights_save_model(payload).model_dump()
        raw_weights = request.get("knowledgeWeights", [])
        if not isinstance(raw_weights, list) or not raw_weights:
            raise validation_failed("knowledgeWeights 不能为空。")
        system_state = self._load_system_state()
        versions = self._normalize_syllabus_versions(system_state.get("syllabusVersions", []))
        target_index = next(
            (index for index, item in enumerate(versions) if str(item.get("versionId", "")) == normalized_version_id),
            -1,
        )
        if target_index < 0:
            raise not_found("大纲版本不存在。")

        existing_version = versions[target_index]
        existing_weights = existing_version.get("knowledgeWeights", [])
        if not isinstance(existing_weights, list) or not existing_weights:
            raise validation_failed("该大纲版本没有可编辑的知识点。")

        incoming_weight_map: Dict[str, Decimal] = {}
        for item in raw_weights:
            if not isinstance(item, dict):
                continue
            knowledge_id = str(item.get("knowledgeId", "")).strip()
            if not knowledge_id:
                continue
            if knowledge_id in incoming_weight_map:
                raise validation_failed(f"knowledgeWeights 中存在重复 knowledgeId：{knowledge_id}")
            incoming_weight_map[knowledge_id] = self._to_syllabus_weight_decimal(item.get("targetWeight", 0))

        existing_ids = [str(weight.get("knowledgeId", "")).strip() for weight in existing_weights if isinstance(weight, dict)]
        if len(incoming_weight_map) != len(existing_ids):
            raise validation_failed("knowledgeWeights 必须覆盖当前版本全部知识点。")
        if set(incoming_weight_map.keys()) != set(existing_ids):
            raise validation_failed("knowledgeWeights 与当前版本知识点不一致，请刷新后重试。")

        total_weight = sum(incoming_weight_map.values(), Decimal("0"))
        if abs(total_weight - Decimal("1")) > Decimal("0.000001"):
            raise validation_failed(f"targetWeight 总和必须等于 1.0，当前为 {total_weight:.6f}。")

        knowledge_lookup = self._syllabus_knowledge_lookup()
        updated_weights: List[Dict[str, object]] = []
        for order_index, existing in enumerate(existing_weights):
            if not isinstance(existing, dict):
                continue
            knowledge_id = str(existing.get("knowledgeId", "")).strip()
            if not knowledge_id:
                continue
            lookup_item = knowledge_lookup.get(knowledge_id, {})
            knowledge_name = str(existing.get("knowledgeName", "")).strip() or str(lookup_item.get("name", knowledge_id))
            updated_weights.append(
                {
                    "knowledgeId": knowledge_id,
                    "knowledgeName": knowledge_name,
                    "targetWeight": float(incoming_weight_map[knowledge_id]),
                    "sort": int(existing.get("sort", int(lookup_item.get("sort", (order_index + 1) * 10)))),
                }
            )

        now = self._now_iso()
        updated_version = {
            **existing_version,
            "knowledgeWeights": updated_weights,
            "updateTime": now,
            "operatorUserId": actor.user_id,
        }
        versions[target_index] = updated_version
        system_state["syllabusVersions"] = versions
        self._save_system_state(system_state)
        return {
            "version": self._serialize_syllabus_version(updated_version),
            "selectedVersionId": normalized_version_id,
            "versions": [self._serialize_syllabus_version(item) for item in self._sorted_syllabus_versions(versions)],
        }

    def ai_parse_syllabus_document(
        self,
        version_id: str,
        file_name: str,
        file_bytes: bytes,
        actor: Actor,
    ) -> Dict[str, object]:
        normalized_version_id = str(version_id or "").strip()
        if not normalized_version_id:
            raise validation_failed("versionId 不能为空。")
        normalized_file_name = str(file_name or "").strip() or "syllabus.txt"
        if len(file_bytes or b"") <= 0:
            raise validation_failed("上传文件不能为空。")
        if len(file_bytes) > SYLLABUS_AI_MAX_FILE_SIZE:
            raise validation_failed("上传文件不能超过 10MB。")
        if not any(normalized_file_name.lower().endswith(suffix) for suffix in SYLLABUS_AI_IMPORT_SUFFIXES):
            raise validation_failed("大纲解析仅支持 PDF、DOC、DOCX 文件。")

        versions = self._normalize_syllabus_versions(self._load_system_state().get("syllabusVersions", []))
        version = next((item for item in versions if str(item.get("versionId", "")) == normalized_version_id), None)
        if not version:
            raise not_found("大纲版本不存在。")

        extracted_text, extraction_meta = self._extract_syllabus_source_text(normalized_file_name, file_bytes)
        normalized_text = str(extracted_text or "").strip()
        if not normalized_text:
            raise validation_failed("未能从上传文件中提取有效文本，请检查文件内容。")

        current_rows = [
            item
            for item in version.get("knowledgeWeights", [])
            if isinstance(item, dict) and str(item.get("knowledgeId", "")).strip()
        ]
        if not current_rows:
            raise validation_failed("当前大纲版本没有可编辑知识点。")

        suggestions, parser_meta = self._parse_syllabus_text_with_ai(normalized_text, current_rows)
        prefilled_rows, match_meta = self._build_syllabus_prefill_rows(current_rows, suggestions)

        return {
            "versionId": normalized_version_id,
            "knowledgeWeights": prefilled_rows,
            "parserReport": {
                "sourceFileName": normalized_file_name,
                "sourceFileSize": len(file_bytes),
                "extractMethod": str(extraction_meta.get("method", "")),
                "extractTextLength": len(normalized_text),
                "extractTextPreview": normalized_text[:600],
                "parserMode": str(parser_meta.get("mode", "heuristic")),
                "model": str(parser_meta.get("model", "")),
                "matchedCount": int(match_meta.get("matchedCount", 0)),
                "unmatchedCount": int(match_meta.get("unmatchedCount", 0)),
                "weightTotal": float(
                    round(sum(float(item.get("targetWeight", 0.0)) for item in prefilled_rows), 6)
                ),
            },
        }

    def list_managed_users(self, filters: Dict[str, str], page: int, size: int, actor: Optional[Actor] = None) -> Tuple[List[Dict[str, object]], int]:
        users = self._filter_managed_users(self._managed_users(), filters)
        if actor and actor.role != ROLE_SUPER_ADMIN:
            users = [item for item in users if str(item.get("role", "")) == ROLE_STUDENT]
            scope_filters = self._resolve_actor_scope_filters(actor.role, actor.user_id)
            scoped_exam_category_code = str(scope_filters.get("exam_category_code", "")).strip()
            scoped_joint_exam_group_code = str(scope_filters.get("joint_exam_group_code", "")).strip()
            if scoped_exam_category_code:
                users = [item for item in users if str(item.get("examCategoryCode", "")).strip() == scoped_exam_category_code]
            if scoped_joint_exam_group_code:
                users = [item for item in users if str(item.get("jointExamGroupCode", "")).strip() == scoped_joint_exam_group_code]
            teacher_scope = self._resolve_teacher_managed_scope(actor.user_id)
            if teacher_scope["joint_group_codes"]:
                users = [
                    item
                    for item in users
                    if str(item.get("jointExamGroupCode", "")).strip() in teacher_scope["joint_group_codes"]
                ]
            if teacher_scope["student_ids"]:
                users = [item for item in users if str(item.get("userId", "")).strip() in teacher_scope["student_ids"]]
        users = sorted(users, key=lambda item: (item["role"], item["userId"]))
        paged, total = self._paginate_items(users, page, size)
        return paged, total

    def _assert_student_account_scope(self, user: Dict[str, object], actor: Actor) -> None:
        if actor.role == ROLE_SUPER_ADMIN:
            return
        if str(user.get("role", "")).strip() != ROLE_STUDENT:
            raise forbidden("教师端仅可维护学生账号。")
        scope_filters = self._resolve_actor_scope_filters(actor.role, actor.user_id)
        scoped_exam_category_code = str(scope_filters.get("exam_category_code", "")).strip()
        scoped_joint_exam_group_code = str(scope_filters.get("joint_exam_group_code", "")).strip()
        user_exam_category_code = str(user.get("examCategoryCode", "")).strip()
        user_joint_exam_group_code = str(user.get("jointExamGroupCode", "")).strip()
        if scoped_exam_category_code and user_exam_category_code != scoped_exam_category_code:
            raise forbidden("当前账号仅可维护所在学科门类下的学生。")
        if scoped_joint_exam_group_code and user_joint_exam_group_code != scoped_joint_exam_group_code:
            raise forbidden("当前账号仅可维护所在联考专业组下的学生。")
        teacher_scope = self._resolve_teacher_managed_scope(actor.user_id)
        if teacher_scope["joint_group_codes"] and user_joint_exam_group_code not in teacher_scope["joint_group_codes"]:
            raise forbidden("当前账号仅可维护配置范围内的联考专业组学生。")
        target_user_id = str(user.get("userId", "")).strip()
        existing_target = self._get_managed_user(target_user_id) if target_user_id else None
        if teacher_scope["student_ids"] and existing_target and target_user_id not in teacher_scope["student_ids"]:
            raise forbidden("当前账号仅可维护配置范围内的学生。")

    def export_managed_students(self, export_format: str = "csv", actor: Optional[Actor] = None) -> Dict[str, str]:
        export_format = self._normalize_export_format(export_format, STUDENT_DIRECTORY_EXPORT_FORMATS, "考生目录导出", "csv")
        students = [item for item in self._filter_managed_users(self._managed_users(), {"role": ROLE_STUDENT, "keyword": ""}) if item.get("enabled", True)]
        if actor and actor.role != ROLE_SUPER_ADMIN:
            scope_filters = self._resolve_actor_scope_filters(actor.role, actor.user_id)
            scoped_exam_category_code = str(scope_filters.get("exam_category_code", "")).strip()
            scoped_joint_exam_group_code = str(scope_filters.get("joint_exam_group_code", "")).strip()
            if scoped_exam_category_code:
                students = [item for item in students if str(item.get("examCategoryCode", "")).strip() == scoped_exam_category_code]
            if scoped_joint_exam_group_code:
                students = [item for item in students if str(item.get("jointExamGroupCode", "")).strip() == scoped_joint_exam_group_code]
            teacher_scope = self._resolve_teacher_managed_scope(actor.user_id)
            if teacher_scope["joint_group_codes"]:
                students = [
                    item
                    for item in students
                    if str(item.get("jointExamGroupCode", "")).strip() in teacher_scope["joint_group_codes"]
                ]
            if teacher_scope["student_ids"]:
                students = [
                    item
                    for item in students
                    if str(item.get("userId", "")).strip() in teacher_scope["student_ids"]
                ]
        return {"format": export_format, "content": "\n".join(self._build_managed_students_export_lines(students, export_format))}

    def get_question_import_template_example(self) -> Dict[str, str]:
        return {
            "format": "txt",
            "fileName": "question-batch-template.txt",
            "content": "\n".join(
                [
                    "【题型】single_choice",
                    "【难度】medium",
                    "【题干】Read the passage and choose the best answer.",
                    "This line continues the same stem, and the formula f(x)=x^2+1 should stay in the same question block.",
                    "【选项】A.The derivative is always positive",
                    "and the function keeps increasing when x > 0",
                    "B.The function is a constant",
                    "C.The function has no formula",
                    "D.None of the above",
                    "【答案】B",
                    "【解析】Long English lines and formulas can continue on the next line.",
                    "For editable Word formulas, keep them as text or Word equations instead of screenshots.",
                    "【知识点】函数基础,导数初步",
                    "---",
                    "【题型】single_choice",
                    "【难度】medium",
                    "【题干】下列离子方程式中，哪个更适合表示硫酸与氢氧化钠发生中和反应？",
                    "【选项】A.H2SO4 + 2NaOH -> Na2SO4 + 2H2O",
                    "B.2H+ + 2OH- -> 2H2O",
                    "C.SO4^2- + Na+ -> Na2SO4",
                    "D.H2 + O2 -> H2O",
                    "【答案】B",
                    "【解析】上传化学式时建议使用线性文本，例如 H2SO4、SO4^2-、->、<->，避免只贴截图。",
                    "【知识点】离子反应,化学方程式",
                    "---",
                    "【题型】subjective",
                    "【难度】medium",
                    "【题干】已知数列满足 a_n = 2n + 1，请写出 a_3 并说明推导过程。",
                    "公式较多时建议单独成行，避免把不同题目连在一起。",
                    "【答案】a_3 = 7。",
                    "【解析】将 n=3 代入公式即可得到 a_3 = 2*3 + 1 = 7。",
                    "【知识点】数列基础",
                ]
            ),
        }

    def save_managed_user(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        user = parse_managed_user_model(payload).model_dump()
        user = self._normalize_managed_user_payload_for_save(user)
        self._assert_student_account_scope(user, actor)
        self._validate_managed_user_payload(user)
        existing = self._get_managed_user(user["userId"])
        system_state = self._load_system_state()
        self._assert_managed_user_mobile_unique(system_state["managedUsers"], user)
        user = self._prepare_managed_user_for_save(user, existing)
        system_state["managedUsers"] = self._upsert_managed_user_list(system_state["managedUsers"], user, existing)
        self._save_system_state(system_state)
        self._after_managed_user_saved(user)
        return user

    def import_students_csv(self, csv_text: str, actor: Actor) -> Dict[str, object]:
        rows = self._parse_student_import_rows(csv_text)
        expected = self._student_import_header()
        imported_users: List[Dict[str, object]] = []
        errors: List[Dict[str, object]] = []
        batch_user_ids = set()
        batch_mobiles = set()
        system_state = self._load_system_state()
        managed_users = list(system_state["managedUsers"])
        for index, values in enumerate(rows[1:], start=2):
            row, row_error = self._parse_student_import_row(values, index, expected, batch_user_ids, batch_mobiles)
            if row_error:
                errors.append(row_error)
                continue
            try:
                user = parse_managed_user_model(
                    {
                        **row,
                        "role": ROLE_STUDENT,
                        "enabled": True,
                        "permissions": [],
                    },
                ).model_dump()
                self._assert_student_account_scope(user, actor)
                self._validate_managed_user_payload(user)
                existing = next((item for item in managed_users if item["userId"] == user["userId"]), None)
                self._assert_managed_user_mobile_unique(managed_users, user)
                saved_user = self._prepare_managed_user_for_save(user, existing)
                managed_users = self._upsert_managed_user_list(managed_users, saved_user, existing)
                batch_user_ids.add(row["userId"])
                batch_mobiles.add(row["mobile"])
                imported_users.append(saved_user)
            except Exception as exc:
                errors.append(
                    self._build_import_error_detail(
                        index,
                        "ROW_VALIDATION_FAILED",
                        f"第 {index} 行导入失败：{exc}",
                    )
                )
        if imported_users:
            system_state["managedUsers"] = managed_users
            self._save_system_state(system_state)
            for user in imported_users:
                self._sync_student_directory_profile(user)
            self._push_message(
                user_ids=[actor.user_id],
                category="SYSTEM_NOTICE",
                title="考生批量导入完成",
                content=f"本次共导入 {len(imported_users)} 条，失败 {len(errors)} 条。",
            )
        return {
            "imported": len(imported_users),
            "failed": len(errors),
            "errors": [str(item["errorMessage"]) for item in errors],
            "errorDetails": errors,
        }
