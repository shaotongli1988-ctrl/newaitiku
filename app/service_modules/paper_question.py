from __future__ import annotations

from app.service_shared import *


class PaperQuestionServiceMixin:
    def _run_mathpix_chem_ocr(self, image_path: Path) -> Tuple[str, str]:
        app_id = str(os.getenv("QB_MATHPIX_APP_ID", "")).strip()
        app_key = str(os.getenv("QB_MATHPIX_APP_KEY", "")).strip()
        if not app_id or not app_key:
            return "", ""
        base_url = str(os.getenv("QB_MATHPIX_BASE_URL", "https://api.mathpix.com")).strip().rstrip("/")
        payload_options = {
            "formats": ["text"],
            "include_smiles": True,
            "include_inchi": True,
            "include_diagram_text": True,
            "rm_spaces": True,
        }
        try:
            with image_path.open("rb") as handle:
                response = httpx.post(
                    f"{base_url}/v3/text",
                    files={"file": (image_path.name, handle, "application/octet-stream")},
                    data={"options_json": dump_json(payload_options)},
                    headers={"app_id": app_id, "app_key": app_key},
                    timeout=45.0,
                )
        except Exception:
            return "", ""
        try:
            payload = response.json() if response.content else {}
        except Exception:
            payload = {}
        if response.status_code >= 400 or not isinstance(payload, dict) or payload.get("error"):
            return "", ""

        text = str(payload.get("text", "")).strip()
        smiles_matches = [
            normalize_formula_source_text(item).strip()
            for item in re.findall(r"<smiles[^>]*>(.*?)</smiles>", text, flags=re.IGNORECASE | re.DOTALL)
            if str(item or "").strip()
        ]
        if smiles_matches:
            return "\n".join(f"SMILES: {item}" for item in smiles_matches), "mathpix"

        normalized_text = normalize_formula_source_text(re.sub(r"</?smiles[^>]*>", "", text, flags=re.IGNORECASE)).strip()
        return (normalized_text, "mathpix") if normalized_text else ("", "")

    def _run_local_chem_structure_ocr(self, image_path: Path) -> Tuple[str, str]:
        configured_jar = str(os.getenv("QB_MOLVEC_JAR", "")).strip()
        default_jar = Path(__file__).resolve().parents[2] / "tools" / "chemistry" / "molvec-runner" / "target" / "molvec-runner-1.0.0-jar-with-dependencies.jar"
        jar_path = Path(configured_jar) if configured_jar else default_jar
        if not jar_path.exists() or not shutil.which("java"):
            return "", ""
        try:
            proc = subprocess.run(
                ["java", "-Djava.awt.headless=true", "-jar", str(jar_path), str(image_path)],
                capture_output=True,
                text=True,
                check=False,
                timeout=45.0,
            )
        except Exception:
            return "", ""
        if proc.returncode != 0:
            return "", ""
        try:
            payload = json.loads(str(proc.stdout or "").strip() or "{}")
        except Exception:
            return "", ""
        molfile = str(payload.get("molfile", "")).strip() if isinstance(payload, dict) else ""
        return (molfile, "molvec") if molfile else ("", "")

    def _run_local_formula_ocr(self, image_path: Path) -> Tuple[str, str]:
        engine = str(os.getenv("QB_FORMULA_OCR_ENGINE", "auto") or "auto").strip().lower()
        if engine not in {"auto", "pix2tex"}:
            return "", ""
        try:
            from PIL import Image  # type: ignore
            from pix2tex.cli import LatexOCR  # type: ignore
        except Exception:
            return "", ""
        try:
            model = getattr(self, "_pix2tex_formula_ocr_model", None)
            if model is None:
                model = LatexOCR()
                self._pix2tex_formula_ocr_model = model
            with Image.open(image_path) as image:
                result = str(model(image) or "").strip()
        except Exception:
            return "", ""
        return normalize_formula_source_text(result), "pix2tex"

    def _extract_docx_image_ocr_text(self, file_bytes: bytes) -> Tuple[str, Dict[str, object]]:
        ocr_runner = getattr(self, "_run_ocr_tesseract", None)
        has_tesseract = callable(ocr_runner) and bool(shutil.which("tesseract"))
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
                media_names = [
                    name
                    for name in archive.namelist()
                    if name.startswith("word/media/")
                    and Path(name).suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
                ]
                if not media_names:
                    return "", {"imageFormulaOcrEngines": []}
                with tempfile.TemporaryDirectory(prefix="qb-batch-docx-ocr-") as temp_dir:
                    temp_path = Path(temp_dir)
                    chunks: List[str] = []
                    used_engines: List[str] = []
                    chemical_engines: List[str] = []
                    chemical_samples: List[Dict[str, str]] = []
                    for index, media_name in enumerate(sorted(media_names), start=1):
                        image_suffix = Path(media_name).suffix.lower() or ".png"
                        image_path = temp_path / f"docx-media-{index}{image_suffix}"
                        image_path.write_bytes(archive.read(media_name))
                        seen_texts: set[str] = set()

                        formula_text, formula_engine = self._run_local_formula_ocr(image_path)
                        if formula_text:
                            chunks.append(formula_text)
                            seen_texts.add(formula_text)
                            if formula_engine and formula_engine not in used_engines:
                                used_engines.append(formula_engine)

                        chem_cloud_text, chem_cloud_engine = self._run_mathpix_chem_ocr(image_path)
                        chem_cloud_text = normalize_formula_source_text(chem_cloud_text)
                        if chem_cloud_text and chem_cloud_text not in seen_texts:
                            chunks.append(chem_cloud_text)
                            seen_texts.add(chem_cloud_text)
                        if chem_cloud_engine:
                            if chem_cloud_engine not in chemical_engines:
                                chemical_engines.append(chem_cloud_engine)
                            chemical_samples.append({
                                "engine": chem_cloud_engine,
                                "content": chem_cloud_text[:240],
                            })

                        local_chem_text, local_chem_engine = self._run_local_chem_structure_ocr(image_path)
                        if local_chem_engine:
                            if local_chem_engine not in chemical_engines:
                                chemical_engines.append(local_chem_engine)
                            chemical_samples.append({
                                "engine": local_chem_engine,
                                "content": local_chem_text[:240],
                            })

                        if has_tesseract:
                            ocr_text = str(ocr_runner(image_path, "chi_sim+eng") or "").strip()
                            if not ocr_text:
                                ocr_text = str(ocr_runner(image_path, "eng") or "").strip()
                            ocr_text = normalize_formula_source_text(ocr_text)
                            if ocr_text and ocr_text not in seen_texts:
                                chunks.append(ocr_text)
                                seen_texts.add(ocr_text)
                                if "tesseract" not in used_engines:
                                    used_engines.append("tesseract")
        except Exception:
            return "", {"imageFormulaOcrEngines": [], "imageChemicalOcrEngines": [], "imageChemicalOcrSamples": []}
        return "\n".join(chunks).strip(), {
            "imageFormulaOcrEngines": used_engines,
            "imageChemicalOcrEngines": chemical_engines,
            "imageChemicalOcrSamples": chemical_samples[:6],
        }

    def _normalize_batch_parse_text(self, source_text: str) -> str:
        return normalize_formula_source_text(source_text)

    def _load_batch_parse_content_with_meta(self, file_name: str, file_bytes: bytes) -> Tuple[str, Dict[str, object]]:
        normalized_name = str(file_name or "").lower()
        if normalized_name.endswith(".docx"):
            docx_text = parse_word_content(file_bytes)
            image_ocr_text, image_meta = self._extract_docx_image_ocr_text(file_bytes)
            merged_text = "\n".join(item for item in (docx_text, image_ocr_text) if str(item or "").strip())
            if merged_text.strip():
                engines = list(image_meta.get("imageFormulaOcrEngines", [])) if isinstance(image_meta, dict) else []
                chem_engines = list(image_meta.get("imageChemicalOcrEngines", [])) if isinstance(image_meta, dict) else []
                method = "python-docx"
                if engines:
                    method = f"{method}+{'/'.join(engines)}"
                if chem_engines:
                    method = f"{method}+{'/'.join(chem_engines)}"
                return self._normalize_batch_parse_text(merged_text), {"method": method, **(image_meta or {})}
        text = self._load_batch_parse_content(file_name, file_bytes)
        return text, {"method": "batch_parse_loader"}

    def _assert_actor_scope_write_access(
        self,
        actor: Actor,
        exam_category_code: str,
        joint_exam_group_code: str,
    ) -> None:
        if actor.role == ROLE_SUPER_ADMIN:
            return
        actor_scope = self._resolve_actor_scope_filters(actor.role, actor.user_id)
        actor_exam_category_code = str(actor_scope.get("exam_category_code", "")).strip()
        actor_joint_exam_group_code = str(actor_scope.get("joint_exam_group_code", "")).strip()
        target_exam_category_code = str(exam_category_code or "").strip()
        target_joint_exam_group_code = str(joint_exam_group_code or "").strip()
        if actor_joint_exam_group_code and target_joint_exam_group_code and target_joint_exam_group_code != actor_joint_exam_group_code:
            raise forbidden("当前账号禁止跨联考专业组提交。")
        if actor_exam_category_code and target_exam_category_code and target_exam_category_code != actor_exam_category_code:
            raise forbidden("当前账号禁止跨学科门类提交。")

    def list_paper_templates(self) -> List[Dict[str, object]]:
        templates = self._paper_templates()
        templates.sort(key=lambda item: item["updateTime"], reverse=True)
        return templates

    def save_paper_template(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        template = parse_paper_template_model(payload).model_dump()
        template_id = template.get("templateId") or f"template-{uuid.uuid4().hex[:8]}"
        template["templateId"] = template_id
        template["updateTime"] = self._now_iso()
        template["updatedBy"] = actor.user_id
        system_state = self._load_system_state()
        replaced = False
        updated_templates = []
        for item in system_state["paperTemplates"]:
            if item["templateId"] == template_id:
                template["createTime"] = item.get("createTime", template["updateTime"])
                updated_templates.append(template)
                replaced = True
            else:
                updated_templates.append(item)
        if not replaced:
            template["createTime"] = template["updateTime"]
            updated_templates.append(template)
        system_state["paperTemplates"] = updated_templates
        self._save_system_state(system_state)
        return template

    def delete_paper_template(self, template_id: str, actor: Actor) -> Dict[str, object]:
        system_state = self._load_system_state()
        template = next((item for item in system_state["paperTemplates"] if item["templateId"] == template_id), None)
        if not template:
            raise not_found("模板不存在。")
        snapshot_id = self._create_undo_snapshot(
            "paper_template_delete",
            {"template": template},
            actor,
        )
        system_state = self._load_system_state()
        system_state["paperTemplates"] = [item for item in system_state["paperTemplates"] if item["templateId"] != template_id]
        self._save_system_state(system_state)
        return {"templateId": template_id, "undoSnapshotId": snapshot_id, "undoExpireSec": 600}

    def restore_deleted_paper_template(self, snapshot_id: str, actor: Actor) -> Dict[str, object]:
        snapshot = self._consume_undo_snapshot(snapshot_id, "paper_template_delete", actor)
        payload = snapshot.get("payload", {})
        template = payload.get("template", {}) if isinstance(payload, dict) else {}
        if not isinstance(template, dict) or not template.get("templateId"):
            raise validation_failed("撤销快照数据损坏，无法恢复模板。")
        system_state = self._load_system_state()
        template_id = str(template["templateId"])
        if any(item.get("templateId") == template_id for item in system_state["paperTemplates"]):
            raise validation_failed("模板已存在，无法重复恢复。")
        system_state["paperTemplates"].append(template)
        self._save_system_state(system_state)
        return {"templateId": template_id, "restored": True}

    def list_paper_overview(self, actor: Actor) -> List[Dict[str, object]]:
        questions = self._list_published_questions_with_content_filters(
            {},
            {},
            actor.role,
            actor.user_id,
            injected_joint_group_code=actor.assigned_joint_group_code,
        )
        if actor.role == ROLE_TEACHER:
            questions = [question for question in questions if self._question_owner_user_id(question) == actor.user_id]
        paper_map: Dict[str, Dict[str, object]] = {}
        for question in questions:
            ext_json = self._load_json_object(question["extJson"])
            for binding in ext_json.get("paperBindings", []):
                row = paper_map.setdefault(
                    binding["paperId"],
                    {
                        "paperId": binding["paperId"],
                        "paperName": binding["paperName"],
                        "paperType": binding["paperType"],
                        "paperStatus": binding["paperStatus"],
                        "durationMinutes": binding["durationMinutes"],
                        "totalScore": binding["totalScore"],
                        "questionCount": 0,
                        "averageAccuracy": 0.0,
                        "attemptCount": 0,
                        "highestScore": 0,
                        "lowestScore": 0,
                    },
                )
                row["questionCount"] += 1
        for paper_id, row in paper_map.items():
            reports = self._collect_paper_reports(paper_id)
            if reports:
                scores = [item["scoreRate"] for item in reports]
                row["attemptCount"] = len(reports)
                row["averageAccuracy"] = round(sum(scores) / len(scores), 4)
                row["highestScore"] = max(item["score"] for item in reports)
                row["lowestScore"] = min(item["score"] for item in reports)
        return sorted(paper_map.values(), key=lambda item: item["paperId"], reverse=True)

    def get_question(self, question_id: str, actor: Actor) -> Dict[str, str]:
        question = self.repository.get_question(question_id)
        if not question:
            raise not_found("题目不存在。")
        self._assert_question_visible(question, actor)
        return self._public_question(question)

    def create_question(self, payload: Dict[str, str], actor: Actor) -> Dict[str, str]:
        payload = dict(payload)
        payload["id"] = str(payload.get("id") or f"question-{uuid.uuid4().hex[:8]}")
        payload["userId"] = str(payload.get("userId") or actor.user_id)
        if actor.role == ROLE_TEACHER and payload["userId"] != actor.user_id:
            raise forbidden("教师只能创建自己的题目。")
        question_ext_json = self._load_json_object(payload.get("extJson", "{}"))
        self._assert_actor_scope_write_access(
            actor,
            str(question_ext_json.get("examCategoryCode", "")).strip(),
            str(question_ext_json.get("jointExamGroupCode", "")).strip(),
        )
        question = self._build_question_record(payload)
        self.repository.create_question(question)
        return self._public_question(question)

    def batch_create_questions(
        self,
        payloads: List[Dict[str, str]],
        actor: Actor,
        source_task_id: str = "",
    ) -> Dict[str, object]:
        normalized_source_task_id = str(source_task_id or "").strip()
        created_items: List[Dict[str, str]] = []
        failures: List[Dict[str, object]] = []
        semantic_pool_cache: Dict[str, List[Dict[str, object]]] = {}
        for index, payload in enumerate(payloads or [], start=1):
            raw_payload = dict(payload or {})
            raw_payload = self._resolve_batch_question_payload_knowledge(raw_payload, actor, semantic_pool_cache)
            ext_json = self._load_json_object(raw_payload.get("extJson", "{}"))
            preview_id = str(ext_json.get("batchPreviewId") or ext_json.get("batch_preview_id") or "").strip()
            effective_source_task_id = normalized_source_task_id
            if not effective_source_task_id and preview_id:
                fingerprint_parts = [
                    actor.user_id,
                    preview_id,
                    str(raw_payload.get("stem", "")).strip(),
                    str(raw_payload.get("answer", "")).strip(),
                    str(raw_payload.get("knowledgeId", "")).strip(),
                ]
                fingerprint = hashlib.sha1("|".join(fingerprint_parts).encode("utf-8")).hexdigest()[:24]
                effective_source_task_id = f"implicit-batch-{fingerprint}"
            if preview_id:
                ext_json["batchPreviewId"] = preview_id
                ext_json["batch_preview_id"] = preview_id
            if effective_source_task_id:
                ext_json["sourceTaskId"] = effective_source_task_id
                ext_json["source_task_id"] = effective_source_task_id
            raw_payload["extJson"] = self._dump_json(ext_json)
            title = str(ext_json.get("title", "")).strip() or str(raw_payload.get("stem", "")).strip()[:60]
            try:
                if effective_source_task_id and preview_id:
                    existing_question = self.repository.get_question_by_batch_source_preview(
                        effective_source_task_id,
                        preview_id,
                    )
                    if existing_question:
                        self._assert_question_visible(existing_question, actor)
                        created_items.append(self._public_question(existing_question))
                        continue
                created_question = self.create_question(raw_payload, actor)
                created_items.append(created_question)
            except Exception as exc:
                failures.append(
                    {
                        "index": index,
                        "previewId": preview_id,
                        "title": title,
                        "message": str(exc),
                    }
                )
        created_question_ids = [str(item.get("id", "")).strip() for item in created_items if str(item.get("id", "")).strip()]
        result = {
            "sourceTaskId": normalized_source_task_id,
            "createdCount": len(created_items),
            "failedCount": len(failures),
            "items": created_items,
            "failures": failures,
            "createdQuestionIds": created_question_ids,
            "rollbackStrategy": {
                "mode": "batch_delete",
                "questionIds": created_question_ids,
                "message": "如需回滚，可使用批量删除这些新建题目。",
            },
        }
        self._attach_batch_create_result_to_task(normalized_source_task_id, result, actor)
        return result

    def _resolve_batch_question_payload_knowledge(
        self,
        raw_payload: Dict[str, object],
        actor: Actor,
        semantic_pool_cache: Optional[Dict[str, List[Dict[str, object]]]] = None,
    ) -> Dict[str, object]:
        normalized_payload = dict(raw_payload or {})
        ext_json = self._load_json_object(normalized_payload.get("extJson", "{}"))
        scope_filters = self._extract_batch_question_scope_filters(ext_json)
        candidate_values: List[object] = [normalized_payload.get("knowledgeId"), ext_json.get("knowledgePointIds")]
        resolved_knowledge_id = self._resolve_batch_knowledge_id_from_candidates(candidate_values, scope_filters)

        hints = self._collect_batch_question_knowledge_hints(ext_json)
        if not resolved_knowledge_id and hints and str(scope_filters.get("subjectCode", "")).strip():
            resolved_knowledge_id = self._match_batch_knowledge_hint_to_existing(
                hints,
                scope_filters,
                semantic_pool_cache or {},
            )

        auto_created_path: List[str] = []
        if not resolved_knowledge_id and str(scope_filters.get("subjectCode", "")).strip():
            resolved_knowledge_id, auto_created_path = self._create_batch_knowledge_from_hints(
                scope_filters,
                hints,
                normalized_payload,
                ext_json,
                actor,
            )

        if not resolved_knowledge_id:
            raise validation_failed("题目缺少可用知识点，请在文档中补充【知识点】或在纠偏列手动选择。")

        normalized_payload["knowledgeId"] = resolved_knowledge_id
        ext_json["knowledgePointIds"] = [resolved_knowledge_id]
        ext_json["knowledge_points"] = [resolved_knowledge_id]
        if hints and not isinstance(ext_json.get("batchKnowledgeHints"), list):
            ext_json["batchKnowledgeHints"] = list(hints)
        if auto_created_path:
            ext_json["autoCreatedKnowledgePath"] = auto_created_path
            ext_json["autoResolvedKnowledge"] = True
            normalize_tags = getattr(self, "_normalize_two_level_knowledge_tags", None)
            if callable(normalize_tags):
                normalized_tags = normalize_tags(auto_created_path)
                if normalized_tags:
                    ext_json["knowledgeTags"] = normalized_tags
        normalized_payload["extJson"] = self._dump_json(ext_json)
        return normalized_payload

    def _extract_batch_question_scope_filters(self, ext_json: Dict[str, object]) -> Dict[str, str]:
        exam_category_code = str(
            ext_json.get("examCategoryCode")
            or ext_json.get("exam_category_code")
            or ""
        ).strip()
        joint_exam_group_code = str(
            ext_json.get("jointExamGroupCode")
            or ext_json.get("joint_exam_group_code")
            or ""
        ).strip()
        subject_code = str(
            ext_json.get("subjectCode")
            or ext_json.get("subject_code")
            or ""
        ).strip()
        policy_version_code = str(
            ext_json.get("policyVersionCode")
            or ext_json.get("policy_version")
            or POLICY_VERSION_CODE
        ).strip() or POLICY_VERSION_CODE
        return {
            "examCategoryCode": exam_category_code,
            "jointExamGroupCode": joint_exam_group_code,
            "subjectCode": subject_code,
            "policyVersionCode": policy_version_code,
        }

    def _resolve_batch_knowledge_id_from_candidates(
        self,
        candidates: List[object],
        scope_filters: Dict[str, str],
    ) -> str:
        scope_matcher = getattr(self, "_knowledge_item_matches_scope", None)
        for item in candidates:
            raw_values = item if isinstance(item, list) else [item]
            for raw_value in raw_values:
                candidate_id = str(raw_value or "").strip()
                if not candidate_id:
                    continue
                knowledge = self.repository.get_knowledge(candidate_id)
                if not knowledge:
                    continue
                if str(knowledge.get("status", "")).strip() != "ENABLED":
                    continue
                if (
                    callable(scope_matcher)
                    and str(scope_filters.get("subjectCode", "")).strip()
                    and not scope_matcher(knowledge, scope_filters)
                ):
                    continue
                return candidate_id
        return ""

    def _collect_batch_question_knowledge_hints(
        self,
        ext_json: Dict[str, object],
    ) -> List[str]:
        candidates: List[object] = [
            ext_json.get("batchKnowledgeHints"),
            ext_json.get("batch_knowledge_hints"),
            ext_json.get("knowledgePointHints"),
            ext_json.get("knowledge_point_hints"),
            ext_json.get("knowledgePoints"),
            ext_json.get("knowledge_points"),
            ext_json.get("knowledgePointIds"),
            ext_json.get("knowledgeTags"),
            ext_json.get("pathLabel"),
            ext_json.get("path_label"),
        ]
        path_levels = ext_json.get("path_levels")
        if not isinstance(path_levels, list):
            path_levels = ext_json.get("pathLevels")
        for row in path_levels if isinstance(path_levels, list) else []:
            if not isinstance(row, dict):
                continue
            candidates.append(row.get("label"))

        normalized_hints: List[str] = []
        seen: set[str] = set()
        for item in candidates:
            raw_values = item if isinstance(item, list) else [item]
            for raw_value in raw_values:
                hint = self._normalize_batch_knowledge_hint_segment(raw_value)
                if not hint:
                    continue
                if hint in seen:
                    continue
                seen.add(hint)
                normalized_hints.append(hint)
        return normalized_hints[:20]

    def _normalize_batch_knowledge_hint_segment(self, value: object) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        text = text.replace("→", "->").replace("➜", "->").replace("⟶", "->")
        text = re.sub(r"^\s*(?:知识点|知识点标签|knowledge)\s*[:：]\s*", "", text, flags=re.IGNORECASE).strip()
        if text in {"建议手动标注", "手动标注", "none", "null", "-"}:
            return ""
        if re.match(r"^knowledge-[a-zA-Z0-9_-]+$", text) and not self.repository.get_knowledge(text):
            return ""
        return text[:120]

    def _match_batch_knowledge_hint_to_existing(
        self,
        hints: List[str],
        scope_filters: Dict[str, str],
        semantic_pool_cache: Dict[str, List[Dict[str, object]]],
    ) -> str:
        if not hints:
            return ""
        cache_key = "|".join(
            [
                str(scope_filters.get("policyVersionCode", "")).strip(),
                str(scope_filters.get("examCategoryCode", "")).strip(),
                str(scope_filters.get("jointExamGroupCode", "")).strip(),
                str(scope_filters.get("subjectCode", "")).strip(),
            ]
        )
        semantic_pool = semantic_pool_cache.get(cache_key)
        if semantic_pool is None:
            semantic_pool = self._build_question_semantic_pool(scope_filters)
            semantic_pool_cache[cache_key] = semantic_pool
        alignment = self._align_question_block_by_knowledge_hints({"knowledge_points": list(hints)}, semantic_pool)
        if not isinstance(alignment, dict):
            return ""
        return self._resolve_batch_knowledge_id_from_candidates([alignment.get("knowledgeId")], scope_filters)

    def _create_batch_knowledge_from_hints(
        self,
        scope_filters: Dict[str, str],
        hints: List[str],
        raw_payload: Dict[str, object],
        ext_json: Dict[str, object],
        actor: Actor,
    ) -> Tuple[str, List[str]]:
        subject_code = str(scope_filters.get("subjectCode", "")).strip()
        if not subject_code:
            return "", []
        self._assert_actor_scope_write_access(
            actor,
            str(scope_filters.get("examCategoryCode", "")).strip(),
            str(scope_filters.get("jointExamGroupCode", "")).strip(),
        )
        path_candidates = self._extract_batch_knowledge_path_candidates(hints)
        selected_path = path_candidates[0] if path_candidates else []
        if not selected_path:
            selected_path = ["自动补录知识点", "未识别知识点"]
        selected_path = [item for item in selected_path[:4] if item]
        if not selected_path:
            selected_path = ["未识别知识点"]

        subject_name_resolver = getattr(self, "_resolve_subject_display_name", None)
        if callable(subject_name_resolver):
            subject_name = str(
                subject_name_resolver(
                    subject_code,
                    str(scope_filters.get("jointExamGroupCode", "")).strip(),
                )
                or subject_code
            ).strip() or subject_code
        else:
            subject_name = subject_code

        root_id, _ = self._ensure_subject_root_node(scope_filters, subject_name)
        parent_id = root_id
        module_code = str(ext_json.get("moduleCode") or raw_payload.get("moduleCode") or "").strip()
        created_path: List[str] = []
        for index, segment in enumerate(selected_path):
            node_module_code = module_code if index == len(selected_path) - 1 else ""
            parent_id, _ = self._ensure_scoped_knowledge_node(
                parent_id=parent_id,
                name=segment,
                scope_filters=scope_filters,
                status="ENABLED",
                module_code=node_module_code,
            )
            created_path.append(segment)
        return str(parent_id or "").strip(), created_path

    def _extract_batch_knowledge_path_candidates(self, hints: List[str]) -> List[List[str]]:
        path_candidates: List[List[str]] = []
        single_segment_candidates: List[str] = []
        for hint in hints:
            normalized_hint = str(hint or "").strip()
            if not normalized_hint:
                continue
            split_segments = self._split_batch_knowledge_hint_segments(normalized_hint)
            if len(split_segments) > 1:
                path_candidates.append(split_segments[:4])
            elif len(split_segments) == 1:
                single_segment_candidates.append(split_segments[0])
        if not path_candidates and single_segment_candidates:
            if len(single_segment_candidates) >= 2:
                path_candidates.append(single_segment_candidates[:4])
            else:
                path_candidates.append([single_segment_candidates[0]])
        return path_candidates

    def _split_batch_knowledge_hint_segments(self, raw_hint: str) -> List[str]:
        normalizer = getattr(self, "_split_knowledge_hint_segments", None)
        if callable(normalizer):
            candidate_segments = normalizer(raw_hint)
            if candidate_segments:
                return [segment for segment in [str(item or "").strip() for item in candidate_segments] if segment]
        normalized_hint = (
            str(raw_hint or "")
            .replace("→", "->")
            .replace("➜", "->")
            .replace("⟶", "->")
            .replace("｜", "|")
            .strip()
        )
        if not normalized_hint:
            return []
        has_path_separator = any(token in normalized_hint for token in ("->", "=>", ">", "/", "\\", "|"))
        if has_path_separator:
            segments = re.split(r"\s*(?:->|=>|>|/|\\|\|)\s*", normalized_hint)
        else:
            segments = [normalized_hint]
        normalized_segments = [self._normalize_batch_knowledge_hint_segment(item) for item in segments]
        return [item for item in normalized_segments if item]

    def _attach_batch_create_result_to_task(
        self,
        source_task_id: str,
        batch_create_result: Dict[str, object],
        actor: Actor,
    ) -> None:
        normalized_task_id = str(source_task_id or "").strip()
        if not normalized_task_id:
            return
        task = self.repository.get_task(normalized_task_id)
        if not task:
            return
        self._assert_task_access(task, actor)
        ext_json = self._load_json_object(str(task.get("extJson", "{}")))
        result = ext_json.get("result", {})
        if not isinstance(result, dict):
            result = {}
        result["createdCount"] = int(batch_create_result.get("createdCount", 0) or 0)
        result["failedCount"] = int(batch_create_result.get("failedCount", 0) or 0)
        result["createdQuestionIds"] = [
            str(question_id).strip()
            for question_id in (batch_create_result.get("createdQuestionIds") or [])
            if str(question_id).strip()
        ]
        result["createFailures"] = list(batch_create_result.get("failures") or [])
        rollback_strategy = batch_create_result.get("rollbackStrategy")
        if isinstance(rollback_strategy, dict):
            result["rollbackStrategy"] = rollback_strategy
        ext_json["result"] = result
        created_count = int(batch_create_result.get("createdCount", 0) or 0)
        failed_count = int(batch_create_result.get("failedCount", 0) or 0)
        ext_json["resultSummary"] = f"解析完成，已入库 {created_count} 道题，失败 {failed_count} 道。"
        task["extJson"] = self._dump_json(ext_json)
        task["updateTime"] = self._now_iso()
        self.repository.update_task(task)

    def update_question(self, question_id: str, payload: Dict[str, str], actor: Actor) -> Dict[str, str]:
        existing = self.repository.get_question(question_id)
        if not existing:
            raise not_found("题目不存在。")
        self._assert_question_visible(existing, actor)
        payload = dict(payload)
        payload["id"] = question_id
        payload["userId"] = str(payload.get("userId") or existing["userId"])
        payload["createTime"] = existing["createTime"]
        current_status = str(existing["status"])
        target_status = str(payload.get("status") or current_status).strip()
        status_changed = target_status != current_status
        if actor.role == ROLE_TEACHER and existing["userId"] != actor.user_id:
            if not (current_status == "QA_IN_PROGRESS" and target_status == "REVIEW_PENDING"):
                raise forbidden("教师只能编辑自己的题目。")
            payload["knowledgeId"] = existing["knowledgeId"]
            payload["type"] = existing["type"]
            payload["stem"] = existing["stem"]
            payload["optionsJson"] = existing["optionsJson"]
            payload["answer"] = existing["answer"]
            payload["extJson"] = existing["extJson"]
            payload["userId"] = existing["userId"]
        if actor.role == ROLE_TEACHER and payload["userId"] != existing["userId"]:
            raise forbidden("教师不能将题目转移给其他人。")
        if status_changed:
            if target_status not in ALLOWED_TRANSITIONS.get(current_status, set()):
                raise invalid_status(f"{current_status} 不能流转到 {target_status}。")
            self._assert_transition_allowed(existing, current_status, target_status, actor)
            payload["status"] = target_status
        payload_ext_json = self._load_json_object(payload.get("extJson", existing.get("extJson", "{}")))
        self._assert_actor_scope_write_access(
            actor,
            str(payload_ext_json.get("examCategoryCode", "")).strip(),
            str(payload_ext_json.get("jointExamGroupCode", "")).strip(),
        )
        question = self._build_question_record(payload, existing)
        if status_changed:
            transition_at = question["updateTime"]
            ext_json = self._load_json_object(question["extJson"])
            ext_json["reviewRemark"] = self._build_review_remark(actor.user_id, current_status, target_status, "")
            question["extJson"] = self._dump_json(ext_json)
        self.repository.update_question(question)
        if status_changed:
            self.repository.create_review(
                {
                    "id": f"review-{uuid.uuid4().hex[:8]}",
                    "questionId": question_id,
                    "reviewerUserId": actor.user_id,
                    "reviewerId": actor.user_id,
                    "status": target_status,
                    "createTime": question["updateTime"],
                    "timestamp": question["updateTime"],
                    "extJson": self._dump_json(
                        {
                            "fromStatus": current_status,
                            "toStatus": target_status,
                            "actorRole": actor.role,
                            "reviewReason": "",
                            "operationType": "STATUS_TRANSITION",
                            "operationAt": question["updateTime"],
                        }
                    ),
                }
            )
        return self._public_question(question)

    def delete_question(self, question_id: str, actor: Actor) -> Dict[str, object]:
        existing = self.get_question(question_id, actor)
        if actor.role == ROLE_TEACHER and existing["userId"] != actor.user_id:
            raise forbidden("教师只能删除自己的题目。")
        snapshot_id = self._create_undo_snapshot(
            "question_delete",
            {"question": existing},
            actor,
        )
        self.repository.delete_question(question_id)
        return {"id": question_id, "undoSnapshotId": snapshot_id, "undoExpireSec": 600}

    def delete_questions_batch(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        request = parse_batch_question_delete_model(payload).model_dump()
        question_ids = self._deduplicate_ids(request["questionIds"], "questionIds")
        if not question_ids:
            raise validation_failed("questionIds 不能为空。")
        questions: List[Dict[str, str]] = []
        for question_id in question_ids:
            existing = self.get_question(question_id, actor)
            if actor.role == ROLE_TEACHER and existing["userId"] != actor.user_id:
                raise forbidden("教师只能删除自己的题目。")
            questions.append(existing)
        snapshot_id = self._create_undo_snapshot(
            "question_delete_batch",
            {"questions": questions},
            actor,
        )
        for question_id in question_ids:
            self.repository.delete_question(question_id)
        return {
            "questionIds": question_ids,
            "undoSnapshotId": snapshot_id,
            "undoExpireSec": 600,
        }

    def restore_deleted_question(self, snapshot_id: str, actor: Actor) -> Dict[str, object]:
        snapshot = self._consume_undo_snapshot(snapshot_id, "question_delete", actor)
        payload = snapshot.get("payload", {})
        question = payload.get("question", {}) if isinstance(payload, dict) else {}
        if not isinstance(question, dict) or not question.get("id"):
            raise validation_failed("撤销快照数据损坏，无法恢复题目。")
        question_id = str(question["id"])
        if self.repository.get_question(question_id):
            raise validation_failed("题目已存在，无法重复恢复。")
        self.repository.create_question(question)
        return {"id": question_id, "restored": True}

    def restore_deleted_questions_batch(self, snapshot_id: str, actor: Actor) -> Dict[str, object]:
        snapshot = self._consume_undo_snapshot(snapshot_id, "question_delete_batch", actor)
        payload = snapshot.get("payload", {})
        questions = payload.get("questions", []) if isinstance(payload, dict) else []
        if not isinstance(questions, list) or not questions:
            raise validation_failed("撤销快照数据损坏，无法恢复题目。")
        restored_ids: List[str] = []
        for row in questions:
            if not isinstance(row, dict) or not row.get("id"):
                continue
            question_id = str(row["id"])
            if self.repository.get_question(question_id):
                continue
            self.repository.create_question(row)
            restored_ids.append(question_id)
        if not restored_ids:
            raise validation_failed("题目已存在，无法重复恢复。")
        return {"questionIds": restored_ids, "restoredCount": len(restored_ids)}

    def list_reviews(self, question_id: str, actor: Actor) -> List[Dict[str, str]]:
        self.get_question(question_id, actor)
        return self.repository.list_reviews(question_id)

    def transition_status(
        self,
        question_id: str,
        target_status: str,
        actor: Actor,
        payload: Optional[Dict[str, object]] = None,
    ) -> Dict[str, str]:
        question = self.repository.get_question(question_id)
        if not question:
            raise not_found("题目不存在。")
        self._assert_question_visible(question, actor)
        current_status = question["status"]
        if target_status not in ALLOWED_TRANSITIONS.get(current_status, set()):
            raise invalid_status(f"{current_status} 不能流转到 {target_status}。")
        self._assert_transition_allowed(question, current_status, target_status, actor)
        reason = self._extract_review_reason(target_status, payload)
        transition_at = self._now_iso()
        question["status"] = target_status
        ext_json = self._load_json_object(question["extJson"])
        ext_json["reviewRemark"] = self._build_review_remark(actor.user_id, current_status, target_status, reason)
        question["extJson"] = self._dump_json(ext_json)
        self.repository.update_question(question)
        self.repository.create_review(
            {
                "id": f"review-{uuid.uuid4().hex[:8]}",
                "questionId": question_id,
                "reviewerUserId": actor.user_id,
                "reviewerId": actor.user_id,
                "status": target_status,
                "createTime": transition_at,
                "timestamp": transition_at,
                "extJson": self._dump_json(
                    {
                        "fromStatus": current_status,
                        "toStatus": target_status,
                        "actorRole": actor.role,
                        "reviewReason": reason,
                        "operationType": "STATUS_TRANSITION",
                        "operationAt": transition_at,
                    }
                ),
            }
        )
        self._push_message(
            [self._question_owner_user_id(question)],
            "REVIEW_NOTICE",
            "题目状态已更新",
            f"{question_id} 已从 {current_status} 更新为 {target_status}。"
        )
        return self._public_question(question)

    def transition_status_batch(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        request = parse_batch_question_status_model(payload).model_dump()
        question_ids = self._deduplicate_ids(request["questionIds"], "questionIds")
        if not question_ids:
            raise validation_failed("questionIds 不能为空。")
        target_status = request["targetStatus"]
        reason = str(request.get("reason", "")).strip()
        updated_ids: List[str] = []
        for question_id in question_ids:
            self.transition_status(
                question_id,
                target_status,
                actor,
                {"reason": reason},
            )
            updated_ids.append(question_id)
        return {
            "targetStatus": target_status,
            "questionIds": updated_ids,
            "updatedCount": len(updated_ids),
        }

    def import_template(
        self,
        file_name: str,
        file_bytes: bytes,
        knowledge_id: str,
        actor: Actor,
        selected_indexes: Optional[List[int]] = None,
    ) -> Dict[str, object]:
        preview = self.preview_template_import(file_name, file_bytes, knowledge_id, actor)
        items = self._select_preview_items(preview["items"], selected_indexes)
        for item in items:
            self.repository.create_question(item)
        errors = list(preview["errors"])
        return {
            "imported": len(items),
            "failed": preview["invalidCount"],
            "errors": errors,
            "errorLog": self._build_import_error_log(errors),
            "errorLogFileName": self._import_error_log_file_name() if errors else "",
        }

    def preview_template_import(
        self,
        file_name: str,
        file_bytes: bytes,
        knowledge_id: str,
        actor: Actor,
    ) -> Dict[str, object]:
        items, errors = self._parse_template_questions(file_name, file_bytes, knowledge_id, actor)
        return {
            "items": [self._public_question(item) for item in items],
            "errors": errors,
            "validCount": len(items),
            "invalidCount": len(errors),
            "errorLog": self._build_import_error_log(errors),
            "errorLogFileName": self._import_error_log_file_name() if errors else "",
        }

    def batch_parse_questions(
        self,
        file_name: str,
        file_bytes: bytes,
        actor: Actor,
        exam_category_code: str = "",
        joint_exam_group_code: str = "",
        subject_code: str = "",
    ) -> Dict[str, object]:
        normalized_exam_category_code = str(exam_category_code or "").strip()
        normalized_joint_exam_group_code = str(joint_exam_group_code or "").strip()
        normalized_subject_code = str(subject_code or "").strip()
        has_any_scope = any((normalized_exam_category_code, normalized_joint_exam_group_code, normalized_subject_code))
        if has_any_scope and not (
            normalized_exam_category_code
            and normalized_joint_exam_group_code
            and normalized_subject_code
        ):
            raise validation_failed("exam_category_code、joint_exam_group_code、subject_code 需同时提供。")
        if has_any_scope:
            self._assert_actor_scope_write_access(actor, normalized_exam_category_code, normalized_joint_exam_group_code)
            self._resolve_batch_parse_subject_type(
                normalized_exam_category_code,
                normalized_joint_exam_group_code,
                normalized_subject_code,
            )

        normalized_file_name = str(file_name or "").strip() or "batch-parse.docx"
        if not any(normalized_file_name.lower().endswith(suffix) for suffix in (".docx", ".doc", ".txt")):
            raise validation_failed("批量解析仅支持 doc、docx、txt 文件。")
        content = self._load_batch_parse_content(normalized_file_name, file_bytes)
        blocks = [block.strip() for block in content.split("\n---\n") if block.strip()]
        if not blocks:
            raise validation_failed("上传模板中没有可识别的题目块。")

        parsed_items: List[Dict[str, object]] = []
        errors: List[str] = []
        for index, block in enumerate(blocks, start=1):
            try:
                parsed_items.append(
                    self._build_batch_parse_item(
                        block,
                        normalized_exam_category_code,
                        normalized_joint_exam_group_code,
                        normalized_subject_code,
                    )
                )
            except Exception as exc:
                errors.append(f"第 {index} 题解析失败：{exc}")

        return {
            "policy_version": POLICY_VERSION_CODE,
            "exam_category_code": normalized_exam_category_code,
            "joint_exam_group_code": normalized_joint_exam_group_code,
            "subject_code": normalized_subject_code,
            "valid_count": len(parsed_items),
            "invalid_count": len(errors),
            "errors": errors,
            "items": parsed_items,
        }

    def _load_batch_parse_content(self, file_name: str, file_bytes: bytes) -> str:
        normalized_name = str(file_name or "").lower()
        if normalized_name.endswith(".docx"):
            docx_text = parse_word_content(file_bytes)
            image_ocr_text, _ = self._extract_docx_image_ocr_text(file_bytes)
            merged_text = "\n".join(item for item in (docx_text, image_ocr_text) if str(item or "").strip())
            if merged_text.strip():
                return self._normalize_batch_parse_text(merged_text)
        if normalized_name.endswith(".txt"):
            decoded_text = decode_uploaded_text_bytes(file_bytes)
            return self._normalize_batch_parse_text(decoded_text)
        if normalized_name.endswith(".doc") and hasattr(self, "_extract_syllabus_source_text"):
            extracted_text, _ = self._extract_syllabus_source_text(file_name, file_bytes)  # type: ignore[attr-defined]
            text = str(extracted_text or "").strip()
            if text:
                return self._normalize_batch_parse_text(text)
        try:
            decoded = decode_uploaded_text_bytes(file_bytes)
        except Exception:
            decoded = ""
        if str(decoded or "").strip():
            return self._normalize_batch_parse_text(decoded)
        raise validation_failed("无法解析上传文件内容，请使用 UTF-8 文本或标准 docx 文件。")

    def _parse_template_block_fields(self, block: str) -> Dict[str, str]:
        fields: Dict[str, str] = {}
        current_key = ""
        for raw_line in block.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("【") and "】" in line:
                key, value = line.split("】", 1)
                current_key = key[1:]
                fields[current_key] = value.strip()
                continue
            if not current_key:
                continue
            current_value = str(fields.get(current_key, "")).strip()
            fields[current_key] = f"{current_value}\n{line}".strip() if current_value else line
        return fields

    def _resolve_batch_parse_subject_type(
        self,
        exam_category_code: str,
        joint_exam_group_code: str,
        subject_code: str,
    ) -> str:
        if not subject_code:
            return ""
        public_subject_codes = {str(item.get("subjectCode", "")).strip() for item in PUBLIC_SUBJECTS if isinstance(item, dict)}
        if subject_code in public_subject_codes:
            return "PUBLIC"
        if not exam_category_code or not joint_exam_group_code:
            return ""
        joint_exam_group = get_joint_exam_group(joint_exam_group_code)
        if not joint_exam_group:
            raise validation_failed("joint_exam_group_code 不存在。")
        if str(joint_exam_group.get("examCategoryCode", "")).strip() != exam_category_code:
            raise validation_failed("joint_exam_group_code 与 exam_category_code 不匹配。")
        professional_subjects = joint_exam_group.get("professionalSubjects", [])
        if not isinstance(professional_subjects, list):
            professional_subjects = []
        matched_subject = next(
            (
                item
                for item in professional_subjects
                if isinstance(item, dict) and str(item.get("subjectCode", "")).strip() == subject_code
            ),
            None,
        )
        if not matched_subject:
            raise validation_failed("subject_code 不属于当前 joint_exam_group_code。")
        return str(matched_subject.get("subjectType", "")).strip() or "PROFESSIONAL"

    def _build_batch_parse_item(
        self,
        block: str,
        exam_category_code: str,
        joint_exam_group_code: str,
        subject_code: str,
    ) -> Dict[str, object]:
        fields = self._parse_template_block_fields(block)
        if "题干" not in fields or "答案" not in fields or "解析" not in fields:
            raise validation_failed("模板必须包含【题干】【答案】【解析】。")
        question_type = str(fields.get("题型", "single_choice")).strip() or "single_choice"

        raw_tags = [item.strip() for item in str(fields.get("知识点", "")).split(",") if item.strip()]
        if not raw_tags:
            raise validation_failed("模板中的【知识点】不能为空。")
        if len(raw_tags) > 20:
            raise validation_failed("模板中的【知识点】最多支持 20 个。")

        raw_options = fields.get("选项", "")
        options = parse_question_option_lines(str(raw_options or ""))
        if question_type in {"single_choice", "multiple_choice", "judge"} and not options:
            raise validation_failed("客观题模板必须包含【选项】。")

        try:
            score = int(str(fields.get("分值", "5")).strip() or "5")
        except Exception:
            score = 5
        score = max(1, min(score, 100))
        subject_type = self._resolve_batch_parse_subject_type(exam_category_code, joint_exam_group_code, subject_code)
        title = str(fields.get("标题", "")).strip() or str(fields["题干"])[:60]
        return {
            "policy_version": POLICY_VERSION_CODE,
            "title": title,
            "content": str(fields["题干"]).strip(),
            "type": question_type,
            "exam_category_code": exam_category_code,
            "joint_exam_group_code": joint_exam_group_code,
            "subject_code": subject_code,
            "subject_type": subject_type,
            "knowledge_points": raw_tags,
            "options": options,
            "answer": str(fields["答案"]).strip(),
            "analysis": str(fields["解析"]).strip(),
            "difficulty": str(fields.get("难度", "medium")).strip() or "medium",
            "score": score,
            "source_type": "word_batch_parse",
            "status": "DRAFT",
            "raw_template": block,
        }

    def list_paper_questions(self, filters: Dict[str, str], page: int, size: int, actor: Actor) -> Tuple[List[Dict[str, str]], int]:
        db_filters = self._pick_filters(filters, ("subjectId", "chapter", "type", "difficulty", "keyword"))
        questions = self._list_published_questions_with_content_filters(
            db_filters,
            filters,
            actor.role,
            actor.user_id,
            injected_joint_group_code=actor.assigned_joint_group_code,
        )
        matched: List[Dict[str, str]] = []
        paper_id = filters.get("paperId", "").strip()
        paper_status = filters.get("paperStatus", "").strip()
        for question in questions:
            bindings = self._filtered_paper_bindings(question, paper_id=paper_id, paper_status=paper_status)
            question = self._with_paper_bindings(question, bindings)
            if paper_id or paper_status:
                if bindings:
                    matched.append(question)
            else:
                matched.append(question)
        return self._paginate_questions(matched, page, size)

    def list_paper_question_filter_options(self, filters: Dict[str, str], actor: Actor) -> Dict[str, object]:
        scoped_filters = self._apply_required_list_scope(
            {
                "keyword": str(filters.get("keyword", "")).strip(),
                "type": str(filters.get("type", "")).strip(),
                "difficulty": str(filters.get("difficulty", "")).strip(),
                "examCategoryCode": str(filters.get("examCategoryCode", "")).strip(),
                "jointExamGroupCode": str(filters.get("jointExamGroupCode", "")).strip(),
                "subjectCode": str(filters.get("subjectCode", "")).strip(),
                "policyVersion": str(filters.get("policyVersion", "")).strip(),
            },
            actor.role,
            actor.user_id,
            injected_joint_group_code=actor.assigned_joint_group_code,
        )
        option_rows = self.repository.list_visible_published_question_filter_options(
            scoped_filters,
            actor.role,
            actor.user_id,
        )
        subject_bucket: Dict[str, Dict[str, object]] = {}
        chapter_bucket: Dict[str, int] = {}
        chapter_bucket_by_subject: Dict[str, Dict[str, int]] = {}

        for row in option_rows:
            subject_id = str(row.get("subjectId", "")).strip()
            subject_code = str(row.get("subjectCode", "")).strip()
            chapter = str(row.get("chapter", "")).strip()
            question_count = int(row.get("questionCount", 0) or 0)
            if subject_id:
                bucket = subject_bucket.setdefault(
                    subject_id,
                    {
                        "value": subject_id,
                        "label": subject_id,
                        "subjectCode": subject_code,
                        "questionCount": 0,
                        "chapters": set(),
                    },
                )
                bucket["questionCount"] = int(bucket.get("questionCount", 0) or 0) + question_count
                if chapter:
                    chapters = bucket.get("chapters")
                    if isinstance(chapters, set):
                        chapters.add(chapter)
                    chapter_bucket_by_subject.setdefault(subject_id, {})
                    chapter_bucket_by_subject[subject_id][chapter] = chapter_bucket_by_subject[subject_id].get(chapter, 0) + question_count
            if chapter:
                chapter_bucket[chapter] = chapter_bucket.get(chapter, 0) + question_count

        subject_options = []
        for subject_id, bucket in subject_bucket.items():
            chapters = bucket.get("chapters")
            chapter_count = len(chapters) if isinstance(chapters, set) else 0
            subject_options.append(
                {
                    "value": subject_id,
                    "label": str(bucket.get("label", subject_id)).strip() or subject_id,
                    "subjectCode": str(bucket.get("subjectCode", "")).strip(),
                    "questionCount": int(bucket.get("questionCount", 0) or 0),
                    "chapterCount": chapter_count,
                }
            )
        subject_options.sort(key=lambda item: str(item.get("value", "")))

        chapter_options = [
            {"value": chapter, "label": chapter, "questionCount": int(count)}
            for chapter, count in chapter_bucket.items()
            if chapter
        ]
        chapter_options.sort(key=lambda item: str(item.get("value", "")))

        chapter_options_by_subject = {}
        for subject_id, chapter_map in chapter_bucket_by_subject.items():
            rows = [
                {"value": chapter, "label": chapter, "questionCount": int(count)}
                for chapter, count in chapter_map.items()
                if chapter
            ]
            rows.sort(key=lambda item: str(item.get("value", "")))
            chapter_options_by_subject[subject_id] = rows

        return {
            "subjectOptions": subject_options,
            "chapterOptions": chapter_options,
            "chapterOptionsBySubject": chapter_options_by_subject,
        }

    def save_manual_paper(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        paper = parse_paper_manual_model(payload)
        self._assert_paper_status_allowed(paper.paperStatus)
        exam_category_code = str(getattr(paper, "examCategoryCode", "")).strip()
        joint_exam_group_code = str(getattr(paper, "jointExamGroupCode", "")).strip()
        subject_code = str(getattr(paper, "subjectCode", "")).strip()
        self._assert_actor_scope_write_access(actor, exam_category_code, joint_exam_group_code)
        question_score_map = self._build_manual_paper_question_scores(
            paper.questionIds,
            paper.totalScore,
            paper.questionScores,
        )
        paper_id = paper.paperId or f"paper-{uuid.uuid4().hex[:8]}"
        self._save_paper_bindings(
            paper_id=paper_id,
            paper_name=paper.paperName,
            subject_id=paper.subjectId,
            exam_category_code=exam_category_code,
            joint_exam_group_code=joint_exam_group_code,
            subject_code=subject_code,
            paper_type=paper.paperType,
            paper_status=paper.paperStatus,
            duration_minutes=paper.durationMinutes,
            total_score=paper.totalScore,
            visible_to_students=paper.visibleToStudents,
            target_class_ids=paper.publishClassIds,
            question_ids=paper.questionIds,
            question_score_map=question_score_map,
            rule_mode="manual",
            actor=actor,
        )
        return {"paperId": paper_id, "questionIds": paper.questionIds}

    def save_auto_paper(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        paper = parse_paper_auto_model(payload)
        self._assert_paper_status_allowed(paper.paperStatus)
        subject_id = str(getattr(paper, "subjectId", "")).strip()
        exam_category_code = str(getattr(paper, "examCategoryCode", "")).strip()
        joint_exam_group_code = str(getattr(paper, "jointExamGroupCode", "")).strip()
        subject_code = str(getattr(paper, "subjectCode", "")).strip()
        self._assert_actor_scope_write_access(actor, exam_category_code, joint_exam_group_code)
        available_questions = self._list_published_questions_with_content_filters(
            {
                "subjectId": subject_id,
                "chapter": str(getattr(paper, "chapter", "") or "").strip(),
                "type": "",
                "difficulty": str(getattr(paper, "difficulty", "") or "").strip(),
                "keyword": "",
            },
            {
                "examCategoryCode": exam_category_code,
                "jointExamGroupCode": joint_exam_group_code,
                "subjectCode": subject_code,
            },
            actor.role,
            actor.user_id,
            injected_joint_group_code=actor.assigned_joint_group_code,
        )
        if not available_questions:
            raise validation_failed("当前条件下暂无可用题目，无法自动组卷。")
        selected_ids, question_score_map = self._select_auto_paper_questions(
            available_questions,
            paper.typeRules,
            paper.totalScore,
        )
        paper_id = paper.paperId or f"paper-{uuid.uuid4().hex[:8]}"
        self._save_paper_bindings(
            paper_id=paper_id,
            paper_name=paper.paperName,
            subject_id=subject_id,
            exam_category_code=exam_category_code,
            joint_exam_group_code=joint_exam_group_code,
            subject_code=subject_code,
            paper_type=paper.paperType,
            paper_status=paper.paperStatus,
            duration_minutes=paper.durationMinutes,
            total_score=paper.totalScore,
            visible_to_students=paper.visibleToStudents,
            target_class_ids=[],
            question_ids=selected_ids,
            question_score_map=question_score_map,
            rule_mode="auto",
            actor=actor,
        )
        return {"paperId": paper_id, "questionIds": selected_ids}

    def _build_ai_generated_template_type_rules(
        self,
        selected_ids: List[str],
        selected_question_map: Dict[str, Dict[str, object]],
        question_score: int,
    ) -> List[Dict[str, object]]:
        selected_set = {str(item or "").strip() for item in selected_ids if str(item or "").strip()}
        type_counts: Dict[str, int] = {}
        for question_id in selected_ids:
            question = selected_question_map.get(str(question_id or "").strip(), {})
            question_type = str(question.get("type", "")).strip()
            if not question_type:
                continue
            type_counts[question_type] = type_counts.get(question_type, 0) + 1
        if not type_counts:
            fallback_count = max(1, len(selected_set))
            type_counts = {"single_choice": fallback_count}
        score = max(1, int(question_score))
        return [
            {
                "type": question_type,
                "count": count,
                "questionScore": score,
            }
            for question_type, count in sorted(type_counts.items())
        ]

    def _save_ai_generated_paper_template(
        self,
        paper_name: str,
        paper_id: str,
        selected_ids: List[str],
        selected_question_map: Dict[str, Dict[str, object]],
        final_subject_id: str,
        final_subject_code: str,
        exam_category_code: str,
        joint_exam_group_code: str,
        difficulty_label: str,
        total_score: int,
        duration_minutes: int,
        policy_version: str,
        actor: Actor,
    ) -> Dict[str, object]:
        selected_count = max(1, len([item for item in selected_ids if str(item or "").strip()]))
        question_score = max(1, int(round(float(total_score) / float(selected_count))))
        template_payload: Dict[str, object] = {
            "templateId": f"template-{paper_id}",
            "templateName": paper_name,
            "paperType": "simulation",
            "subjectId": final_subject_id,
            "chapter": "",
            "difficulty": difficulty_label,
            "totalScore": total_score,
            "durationMinutes": duration_minutes,
            "examCategoryCode": exam_category_code,
            "jointExamGroupCode": joint_exam_group_code,
            "subjectCode": final_subject_code,
            "policyVersion": policy_version,
            "typeRules": self._build_ai_generated_template_type_rules(
                selected_ids,
                selected_question_map,
                question_score,
            ),
        }
        return self.save_paper_template(template_payload, actor)

    def list_teacher_paper_classes(self, actor: Actor) -> List[Dict[str, str]]:
        class_options: List[Dict[str, str]] = []
        seen_values: set[str] = set()

        def append_option(value: object, label: object = "") -> None:
            normalized_value = str(value or "").strip()
            if not normalized_value or normalized_value in seen_values:
                return
            seen_values.add(normalized_value)
            normalized_label = str(label or normalized_value).strip() or normalized_value
            class_options.append({"label": normalized_label, "value": normalized_value})

        def parse_raw_class_list(raw_rows: object) -> None:
            if not isinstance(raw_rows, list):
                return
            for row in raw_rows:
                if isinstance(row, dict):
                    append_option(
                        row.get("classId")
                        or row.get("id")
                        or row.get("value"),
                        row.get("className")
                        or row.get("name")
                        or row.get("label"),
                    )
                    continue
                append_option(row)

        for row in self.list_my_classes(actor):
            if not isinstance(row, dict):
                continue
            append_option(
                row.get("classId") or row.get("value"),
                row.get("className") or row.get("label"),
            )

        managed_user = self._get_managed_user(actor.user_id) or {}
        user = self.repository.get_user_by_id(actor.user_id)
        user_ext_json = self._load_json_object(str(user.get("extJson", "{}"))) if user else {}
        for source in (managed_user, user_ext_json):
            if not isinstance(source, dict):
                continue
            parse_raw_class_list(source.get("classIds"))
            parse_raw_class_list(source.get("class_ids"))
            parse_raw_class_list(source.get("targetClassIds"))
            parse_raw_class_list(source.get("target_class_ids"))
            parse_raw_class_list(source.get("publishClassIds"))
            parse_raw_class_list(source.get("publish_class_ids"))
            parse_raw_class_list(source.get("teachingClassIds"))
            parse_raw_class_list(source.get("teaching_class_ids"))
            parse_raw_class_list(source.get("classes"))
            parse_raw_class_list(source.get("classOptions"))
            parse_raw_class_list(source.get("teachingClasses"))
            parse_raw_class_list(source.get("teacherClasses"))

        class_options.sort(key=lambda item: item["value"])
        return class_options

    def ai_generate_paper(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        subject_id = str(payload.get("subjectId") or "").strip()
        exam_category_code = str(payload.get("examCategoryCode") or "").strip()
        joint_exam_group_code = str(payload.get("jointExamGroupCode") or "").strip()
        requested_subject_code = str(payload.get("subjectCode") or "").strip()
        policy_version = str(payload.get("policyVersion") or payload.get("policy_version") or POLICY_VERSION_CODE).strip() or POLICY_VERSION_CODE
        if requested_subject_code:
            resolved_subject_id = subject_id_from_subject_code(requested_subject_code)
            if not subject_id:
                subject_id = resolved_subject_id
            elif subject_id.upper() == requested_subject_code.upper():
                # Backward compatibility: some clients pass subjectCode in subjectId.
                subject_id = resolved_subject_id
        if not subject_id and not joint_exam_group_code:
            raise validation_failed("subjectId 或 jointExamGroupCode 至少提供一个。")
        self._assert_actor_scope_write_access(actor, exam_category_code, joint_exam_group_code)

        raw_class_ids = (
            payload.get("classIds")
            if isinstance(payload.get("classIds"), list)
            else payload.get("publishClassIds")
            if isinstance(payload.get("publishClassIds"), list)
            else payload.get("targetClassIds")
            if isinstance(payload.get("targetClassIds"), list)
            else []
        )
        class_ids = [
            str(item or "").strip()
            for item in raw_class_ids
            if str(item or "").strip()
        ]
        class_ids = list(dict.fromkeys(class_ids))

        raw_total_count = payload.get("totalCount")
        if raw_total_count in {"", None}:
            raw_total_count = 20
        try:
            total_count = int(raw_total_count)
        except (TypeError, ValueError):
            raise validation_failed("totalCount 必须是 10-50 的整数。")
        if total_count < 10 or total_count > 50:
            raise validation_failed("totalCount 必须在 10-50 范围内。")

        raw_difficulty_level = payload.get("difficulty")
        try:
            difficulty_level = int(raw_difficulty_level or 0)
        except (TypeError, ValueError):
            raise validation_failed("difficulty 必须是 1-5 的整数。")
        if difficulty_level < 1 or difficulty_level > 5:
            raise validation_failed("difficulty 必须在 1-5 范围内。")

        raw_knowledge_scope = (
            payload.get("knowledgeScope")
            if isinstance(payload.get("knowledgeScope"), list)
            else []
        )
        knowledge_scope = [
            str(item or "").strip()
            for item in raw_knowledge_scope
            if str(item or "").strip()
        ]
        knowledge_scope = list(dict.fromkeys(knowledge_scope))

        difficulty_label = self._map_ai_difficulty_level(difficulty_level)
        available_questions = self._list_published_questions_with_content_filters(
            {
                "subjectId": subject_id,
                "chapter": "",
                "type": "",
                "difficulty": difficulty_label,
                "keyword": "",
            },
            {
                "examCategoryCode": exam_category_code,
                "jointExamGroupCode": joint_exam_group_code,
                "subjectCode": requested_subject_code,
            },
            actor.role,
            "" if actor.role == "teacher" else actor.user_id,
            injected_joint_group_code=actor.assigned_joint_group_code,
        )
        if knowledge_scope:
            scoped_set = set(knowledge_scope)
            available_questions = [
                question
                for question in available_questions
                if str(question.get("knowledgeId", "")).strip() in scoped_set
            ]
        if not available_questions:
            raise validation_failed("当前条件下暂无可用题目，无法智能组卷。")
        if len(available_questions) < total_count:
            total_count = len(available_questions)

        selected_ids = self._pick_ai_questions_by_weight(available_questions, knowledge_scope, total_count)
        selected_question_map = {
            str(item.get("id", "")).strip(): item
            for item in available_questions
            if isinstance(item, dict)
        }
        first_selected_question = selected_question_map.get(selected_ids[0], {}) if selected_ids else {}
        first_selected_ext = self._question_ext_json(first_selected_question) if first_selected_question else {}
        derived_subject_code = str(first_selected_ext.get("subjectCode", "")).strip()
        if not exam_category_code:
            exam_category_code = str(first_selected_ext.get("examCategoryCode", "")).strip()
        if not joint_exam_group_code:
            joint_exam_group_code = str(first_selected_ext.get("jointExamGroupCode", "")).strip()
        final_subject_code = requested_subject_code or (derived_subject_code if subject_id else "")
        final_subject_id = subject_id or (subject_id_from_subject_code(final_subject_code) if final_subject_code else "")

        total_score = total_count * 5
        paper_scope_label = final_subject_id or joint_exam_group_code or "scope"
        paper_name = f"AI智能组卷-{paper_scope_label}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        manual_payload: Dict[str, object] = {
            "paperName": paper_name,
            "paperType": "simulation",
            "paperStatus": "DRAFT",
            "durationMinutes": 45,
            "totalScore": total_score,
            "visibleToStudents": False,
            "publishClassIds": class_ids,
            "questionIds": selected_ids,
        }
        if final_subject_id:
            manual_payload["subjectId"] = final_subject_id
        if exam_category_code and joint_exam_group_code:
            manual_payload["examCategoryCode"] = exam_category_code
            manual_payload["jointExamGroupCode"] = joint_exam_group_code
            if final_subject_code:
                manual_payload["subjectCode"] = final_subject_code

        generated = self.save_manual_paper(manual_payload, actor)
        paper_id = str(generated.get("paperId", "")).strip()
        saved_template = self._save_ai_generated_paper_template(
            paper_name=paper_name,
            paper_id=paper_id,
            selected_ids=selected_ids,
            selected_question_map=selected_question_map,
            final_subject_id=final_subject_id,
            final_subject_code=final_subject_code,
            exam_category_code=exam_category_code,
            joint_exam_group_code=joint_exam_group_code,
            difficulty_label=difficulty_label,
            total_score=total_score,
            duration_minutes=45,
            policy_version=policy_version,
            actor=actor,
        )
        return {
            "paperId": paper_id,
            "paper_id": paper_id,
            "templateId": str(saved_template.get("templateId", "")).strip(),
            "template_id": str(saved_template.get("templateId", "")).strip(),
            "questionIds": selected_ids,
            "subject_id": final_subject_id,
            "exam_category_code": exam_category_code,
            "joint_exam_group_code": joint_exam_group_code,
            "subject_code": final_subject_code,
            "class_ids": class_ids,
            "total_count": total_count,
            "difficulty_level": difficulty_level,
            "knowledge_scope": knowledge_scope,
        }

    def _pick_ai_questions_by_weight(
        self,
        available_questions: List[Dict[str, str]],
        knowledge_scope: List[str],
        total_count: int,
    ) -> List[str]:
        knowledge_question_map: Dict[str, List[Dict[str, str]]] = {}
        for question in available_questions:
            knowledge_id = str(question.get("knowledgeId", "")).strip() or "__unknown__"
            knowledge_question_map.setdefault(knowledge_id, []).append(question)

        scoped_ids = [knowledge_id for knowledge_id in knowledge_scope if knowledge_id in knowledge_question_map]
        candidate_knowledge_ids = scoped_ids or list(knowledge_question_map.keys())
        target_weight_map = self.get_paper_target_weight_profile(candidate_knowledge_ids).get("targetWeightMap", {})
        if not isinstance(target_weight_map, dict):
            target_weight_map = {}

        normalized_weight_map: Dict[str, float] = {}
        for knowledge_id in candidate_knowledge_ids:
            raw_weight = target_weight_map.get(knowledge_id, 0)
            try:
                normalized_weight = float(raw_weight)
            except (TypeError, ValueError):
                normalized_weight = 0.0
            if normalized_weight < 0:
                normalized_weight = 0.0
            normalized_weight_map[knowledge_id] = normalized_weight

        if sum(normalized_weight_map.values()) <= 0:
            equal_weight = 1 / max(1, len(candidate_knowledge_ids))
            normalized_weight_map = {knowledge_id: equal_weight for knowledge_id in candidate_knowledge_ids}

        quotas: Dict[str, int] = {knowledge_id: 0 for knowledge_id in candidate_knowledge_ids}
        remaining = total_count
        total_weight = sum(normalized_weight_map.values())
        for knowledge_id in candidate_knowledge_ids:
            raw_quota = (normalized_weight_map[knowledge_id] / total_weight) * total_count if total_weight > 0 else 0
            quota = int(raw_quota)
            quota = min(quota, len(knowledge_question_map.get(knowledge_id, [])))
            quotas[knowledge_id] = quota
            remaining -= quota

        if remaining > 0:
            for knowledge_id in sorted(
                candidate_knowledge_ids,
                key=lambda value: normalized_weight_map.get(value, 0),
                reverse=True,
            ):
                if remaining <= 0:
                    break
                available = len(knowledge_question_map.get(knowledge_id, []))
                spare = available - quotas.get(knowledge_id, 0)
                if spare <= 0:
                    continue
                take = min(spare, remaining)
                quotas[knowledge_id] = quotas.get(knowledge_id, 0) + take
                remaining -= take

        selected_ids: List[str] = []
        selected_set: set[str] = set()
        for knowledge_id in candidate_knowledge_ids:
            for question in knowledge_question_map.get(knowledge_id, [])[:quotas.get(knowledge_id, 0)]:
                question_id = str(question.get("id", "")).strip()
                if not question_id or question_id in selected_set:
                    continue
                selected_set.add(question_id)
                selected_ids.append(question_id)

        if len(selected_ids) < total_count:
            for question in available_questions:
                question_id = str(question.get("id", "")).strip()
                if not question_id or question_id in selected_set:
                    continue
                selected_set.add(question_id)
                selected_ids.append(question_id)
                if len(selected_ids) >= total_count:
                    break

        if len(selected_ids) < total_count:
            raise validation_failed("可用题目不足，无法完成智能组卷。")
        return selected_ids[:total_count]

    def update_paper_status(self, paper_id: str, paper_status: str, actor: Actor) -> Dict[str, object]:
        self._assert_paper_status_allowed(paper_status)
        current_statuses = self._paper_current_statuses(paper_id, actor)
        if not current_statuses:
            raise not_found("试卷不存在。")
        if len(current_statuses) > 1:
            raise validation_failed("试卷状态数据异常，请先修复后再操作。")
        current_status = current_statuses[0]
        self._assert_paper_transition_allowed(current_status, paper_status)
        touched_question_ids = self._update_paper_bindings(
            paper_id,
            actor,
            lambda bindings: self._with_updated_paper_status(bindings, paper_id, paper_status),
        )
        return {
            "paperId": paper_id,
            "questionIds": touched_question_ids,
            "paperStatus": paper_status,
            "latestStatus": paper_status,
        }

    def delete_paper(self, paper_id: str, actor: Actor) -> Dict[str, object]:
        binding_snapshot = self._collect_paper_delete_snapshot(paper_id, actor)
        touched_question_ids = self._update_paper_bindings(
            paper_id,
            actor,
            lambda bindings: [binding for binding in bindings if binding.get("paperId") != paper_id],
        )
        snapshot_id = self._create_undo_snapshot(
            "paper_delete",
            {
                "paperId": paper_id,
                "bindingsByQuestion": binding_snapshot,
            },
            actor,
        )
        return {
            "paperId": paper_id,
            "questionIds": touched_question_ids,
            "undoSnapshotId": snapshot_id,
            "undoExpireSec": 600,
        }

    def restore_deleted_paper(self, snapshot_id: str, actor: Actor) -> Dict[str, object]:
        snapshot = self._consume_undo_snapshot(snapshot_id, "paper_delete", actor)
        payload = snapshot.get("payload", {})
        if not isinstance(payload, dict):
            raise validation_failed("撤销快照数据损坏，无法恢复试卷。")
        paper_id = str(payload.get("paperId", "")).strip()
        bindings_by_question = payload.get("bindingsByQuestion", [])
        if not paper_id or not isinstance(bindings_by_question, list):
            raise validation_failed("撤销快照数据损坏，无法恢复试卷。")
        touched_question_ids: List[str] = []
        for row in bindings_by_question:
            if not isinstance(row, dict):
                continue
            question_id = str(row.get("questionId", "")).strip()
            if not question_id:
                continue
            question = self.repository.get_question(question_id)
            if not question:
                continue
            current_bindings = self._paper_bindings(question)
            restored_bindings = row.get("paperBindings", [])
            if not isinstance(restored_bindings, list):
                continue
            merged = [binding for binding in current_bindings if binding.get("paperId") != paper_id]
            merged.extend([binding for binding in restored_bindings if isinstance(binding, dict)])
            self.repository.update_question(self._with_paper_bindings(question, merged))
            touched_question_ids.append(question_id)
        if not touched_question_ids:
            raise not_found("撤销失败：关联题目不存在或已变更。")
        return {"paperId": paper_id, "questionIds": touched_question_ids, "restored": True}

    def export_paper(self, paper_id: str, actor: Actor, export_format: str = "txt") -> Dict[str, str]:
        export_format = self._normalize_export_format(export_format, PAPER_EXPORT_FORMATS, "试卷导出", "txt")
        questions = self._list_questions_for_paper(paper_id, actor, visible_to_students=False)
        if not questions:
            raise not_found("试卷不存在。")
        lines = [f"试卷ID: {paper_id}"]
        for index, question in enumerate(questions, start=1):
            lines.extend(
                [
                    f"{index}. {question['stem']}",
                    f"选项: {question['optionsJson']}",
                    f"答案: {question['answer']}",
                    f"解析: {self._question_analysis(question)}",
                    "",
                ]
            )
        if export_format == "pdf":
            lines.insert(0, "试卷导出（PDF文本预览）")
        elif export_format == "word":
            lines.insert(0, "试卷导出（Word文本预览）")
        return {"format": export_format, "content": "\n".join(lines)}
