from __future__ import annotations

from app.service_shared import *

# Observability note: learning-method state flow should keep log/trace/metric evidence aligned with release docs.

LEARNING_METHOD_ALLOWED_STATUSES = {"ACTIVE", "INACTIVE"}
LEARNING_METHOD_PROGRESS_STATUSES = {"NOT_STARTED", "IN_PROGRESS", "COMPLETED"}
LEARNING_METHOD_PROGRESS_ALLOWED_TRANSITIONS = {
    "NOT_STARTED": {"IN_PROGRESS", "COMPLETED"},
    "IN_PROGRESS": {"IN_PROGRESS", "COMPLETED"},
    "COMPLETED": {"IN_PROGRESS", "COMPLETED"},
}
LEARNING_METHOD_FEEDBACK_STATUSES = {"PENDING", "ACCEPTED", "PARTIAL", "REJECTED", "COMPLETED"}
LEARNING_METHOD_DIFFICULTY_MAP = {"L1": "easy", "L2": "medium", "L3": "hard"}
QUESTION_DIFFICULTIES = {"easy", "medium", "hard"}
QUESTION_DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2}
LEARNING_METHOD_RECOMMENDATION_STRATEGY_BY_PRACTICE_STRATEGY = {
    "FOUNDATION_REINFORCE": "FOUNDATION",
    "BALANCED_ADVANCE": "BALANCED",
    "SPRINT_BREAKTHROUGH": "SPRINT",
    "DEFAULT": "BALANCED",
}
LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCES = {"DEFAULT", "MANUAL", "SUGGESTED"}


class LearningMethodServiceMixin:
    def _normalize_learning_method_code(self, method_code: str) -> str:
        normalized = str(method_code or "").strip().upper()
        if not normalized:
            raise validation_failed("methodCode 不能为空。")
        return normalized

    def _normalize_learning_method_status(self, status: str, default: str = "ACTIVE") -> str:
        normalized = str(status or "").strip().upper() or default
        if normalized not in LEARNING_METHOD_ALLOWED_STATUSES:
            raise validation_failed("status 仅支持 ACTIVE、INACTIVE。")
        return normalized

    def _normalize_learning_method_progress_status(self, status: str, default: str = "NOT_STARTED") -> str:
        normalized = str(status or "").strip().upper() or default
        if normalized not in LEARNING_METHOD_PROGRESS_STATUSES:
            raise validation_failed("学习方法进度状态非法。")
        return normalized

    def _resolve_recommendation_strategy_code(self, practice_strategy: str) -> str:
        normalized_practice_strategy = str(practice_strategy or "").strip().upper()
        if not normalized_practice_strategy:
            return ""
        return str(
            LEARNING_METHOD_RECOMMENDATION_STRATEGY_BY_PRACTICE_STRATEGY.get(
                normalized_practice_strategy,
                "",
            )
        ).strip().upper()

    def _normalize_recommendation_strategy_source(self, source: str, default: str = "DEFAULT") -> str:
        normalized_source = str(source or "").strip().upper() or default
        if normalized_source not in LEARNING_METHOD_RECOMMENDATION_STRATEGY_SOURCES:
            return default
        return normalized_source

    def _canTransitionLearningMethodProgress(self, current_status: str, target_status: str) -> bool:
        normalized_current = self._normalize_learning_method_progress_status(current_status, "NOT_STARTED")
        normalized_target = self._normalize_learning_method_progress_status(target_status, "NOT_STARTED")
        return normalized_target in LEARNING_METHOD_PROGRESS_ALLOWED_TRANSITIONS.get(normalized_current, set())

    def _guard_learning_method_progress_transition(self, current_status: str, target_status: str) -> None:
        if self._canTransitionLearningMethodProgress(current_status, target_status):
            return
        raise invalid_status(f"学习方法进度状态不允许从 {current_status} 变更到 {target_status}。")

    def _default_learning_method_progress(self, student_user_id: str, method_code: str) -> Dict[str, object]:
        return {
            "id": f"slmp-{student_user_id}-{method_code.lower()}",
            "studentUserId": student_user_id,
            "methodCode": method_code,
            "startCount": 0,
            "completeCount": 0,
            "lastPracticedAt": "",
            "lastAccuracy": 0.0,
            "lastReviewSummary": "",
            "status": "NOT_STARTED",
            "extJson": {},
            "createTime": "",
            "updateTime": "",
        }

    def _serialize_learning_method(self, method: Dict[str, object]) -> Dict[str, object]:
        return {
            "id": str(method.get("id", "")),
            "methodCode": str(method.get("methodCode", "")),
            "methodName": str(method.get("methodName", "")),
            "oneLineIntro": str(method.get("oneLineIntro", "")),
            "useWhen": list(method.get("useWhen", [])) if isinstance(method.get("useWhen"), list) else [],
            "steps": list(method.get("steps", [])) if isinstance(method.get("steps"), list) else [],
            "commonMistakes": list(method.get("commonMistakes", [])) if isinstance(method.get("commonMistakes"), list) else [],
            "questionBankActions": (
                list(method.get("questionBankActions", []))
                if isinstance(method.get("questionBankActions"), list)
                else []
            ),
            "starterTask": str(method.get("starterTask", "")),
            "difficultyLevel": str(method.get("difficultyLevel", "L1")) or "L1",
            "estimatedMinutes": int(method.get("estimatedMinutes", 15) or 15),
            "sort": int(method.get("sort", 0) or 0),
            "status": str(method.get("status", "ACTIVE")) or "ACTIVE",
            "extJson": method.get("extJson", {}) if isinstance(method.get("extJson"), dict) else {},
            "createTime": str(method.get("createTime", "")),
            "updateTime": str(method.get("updateTime", "")),
        }

    def _serialize_learning_method_progress(self, progress: Dict[str, object]) -> Dict[str, object]:
        return {
            "id": str(progress.get("id", "")),
            "studentUserId": str(progress.get("studentUserId", "")),
            "methodCode": str(progress.get("methodCode", "")),
            "startCount": int(progress.get("startCount", 0) or 0),
            "completeCount": int(progress.get("completeCount", 0) or 0),
            "lastPracticedAt": str(progress.get("lastPracticedAt", "")),
            "lastAccuracy": float(progress.get("lastAccuracy", 0.0) or 0.0),
            "lastReviewSummary": str(progress.get("lastReviewSummary", "")),
            "status": self._normalize_learning_method_progress_status(str(progress.get("status", "NOT_STARTED"))),
            "extJson": progress.get("extJson", {}) if isinstance(progress.get("extJson"), dict) else {},
            "createTime": str(progress.get("createTime", "")),
            "updateTime": str(progress.get("updateTime", "")),
        }

    def list_learning_methods_for_student(self, status: str, actor: Actor) -> Dict[str, object]:
        normalized_status = self._normalize_learning_method_status(status, "ACTIVE")
        methods = self.repository.list_learning_methods(normalized_status)
        progress_rows = self.repository.list_student_learning_method_progress(actor.user_id)
        progress_map = {
            str(item.get("methodCode", "")).strip().upper(): item
            for item in progress_rows
            if str(item.get("methodCode", "")).strip()
        }
        items: List[Dict[str, object]] = []
        for method in methods:
            method_payload = self._serialize_learning_method(method)
            method_code = str(method_payload.get("methodCode", "")).strip().upper()
            progress = progress_map.get(method_code) or self._default_learning_method_progress(actor.user_id, method_code)
            summary = {
                "methodCode": method_payload["methodCode"],
                "methodName": method_payload["methodName"],
                "oneLineIntro": method_payload["oneLineIntro"],
                "difficultyLevel": method_payload["difficultyLevel"],
                "estimatedMinutes": method_payload["estimatedMinutes"],
                "sort": method_payload["sort"],
                "status": method_payload["status"],
                "progress": {
                    "status": str(progress.get("status", "NOT_STARTED")),
                    "startCount": int(progress.get("startCount", 0) or 0),
                    "completeCount": int(progress.get("completeCount", 0) or 0),
                    "lastPracticedAt": str(progress.get("lastPracticedAt", "")),
                    "lastAccuracy": float(progress.get("lastAccuracy", 0.0) or 0.0),
                },
            }
            items.append(summary)
        return {"items": items, "total": len(items)}

    def get_learning_method_detail_for_student(self, method_code: str, actor: Actor) -> Dict[str, object]:
        normalized_method_code = self._normalize_learning_method_code(method_code)
        method = self.repository.get_learning_method(normalized_method_code)
        if not method or str(method.get("status", "ACTIVE")).strip().upper() != "ACTIVE":
            raise not_found("学习方法不存在。")
        progress = self.repository.get_student_learning_method_progress(actor.user_id, normalized_method_code)
        if not progress:
            progress = self._default_learning_method_progress(actor.user_id, normalized_method_code)
        return {
            "method": self._serialize_learning_method(method),
            "progress": self._serialize_learning_method_progress(progress),
        }

    def start_learning_method_practice(self, method_code: str, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        normalized_method_code = self._normalize_learning_method_code(method_code)
        method = self.repository.get_learning_method(normalized_method_code)
        if not method or str(method.get("status", "ACTIVE")).strip().upper() != "ACTIVE":
            raise not_found("学习方法不存在。")

        practice_strategy = str(payload.get("practiceStrategy", "")).strip().upper() or "DEFAULT"
        source_type = str(payload.get("sourceType", "")).strip() or "MANUAL_START"
        now_iso = self._now_iso()
        session_id = str(payload.get("sessionId", "")).strip() or f"lm-session-{uuid.uuid4().hex[:12]}"

        existing = self.repository.get_student_learning_method_progress(actor.user_id, normalized_method_code)
        current_status = "NOT_STARTED"
        if existing:
            progress_ext = existing.get("extJson", {}) if isinstance(existing.get("extJson"), dict) else {}
            create_time = str(existing.get("createTime", "")).strip() or now_iso
            start_count = int(existing.get("startCount", 0) or 0) + 1
            complete_count = int(existing.get("completeCount", 0) or 0)
            last_accuracy = float(existing.get("lastAccuracy", 0.0) or 0.0)
            last_review_summary = str(existing.get("lastReviewSummary", ""))
            progress_id = str(existing.get("id", "")).strip() or f"slmp-{actor.user_id}-{normalized_method_code.lower()}"
            current_status = self._normalize_learning_method_progress_status(str(existing.get("status", "NOT_STARTED")))
        else:
            progress_ext = {}
            create_time = now_iso
            start_count = 1
            complete_count = 0
            last_accuracy = 0.0
            last_review_summary = ""
            progress_id = f"slmp-{actor.user_id}-{normalized_method_code.lower()}"

        self._guard_learning_method_progress_transition(current_status, "IN_PROGRESS")
        history = list(progress_ext.get("history", [])) if isinstance(progress_ext.get("history"), list) else []
        history.append(
            {
                "event": "START",
                "sessionId": session_id,
                "traceId": session_id,
                "practiceStrategy": practice_strategy,
                "sourceType": source_type,
                "eventAt": now_iso,
            }
        )
        if len(history) > 100:
            history = history[-100:]
        progress_ext["history"] = history
        progress_ext["currentSession"] = {
            "sessionId": session_id,
            "practiceStrategy": practice_strategy,
            "sourceType": source_type,
            "startedAt": now_iso,
        }
        progress_ext["traceContext"] = {"traceId": session_id, "updateTime": now_iso}
        progress_ext["metricSnapshot"] = {
            "startCount": start_count,
            "completeCount": complete_count,
        }

        saved = self.repository.upsert_student_learning_method_progress(
            {
                "id": progress_id,
                "studentUserId": actor.user_id,
                "methodCode": normalized_method_code,
                "startCount": start_count,
                "completeCount": complete_count,
                "lastPracticedAt": now_iso,
                "lastAccuracy": last_accuracy,
                "lastReviewSummary": last_review_summary,
                "status": "IN_PROGRESS",
                "extJson": progress_ext,
                "createTime": create_time,
                "updateTime": now_iso,
            }
        )
        return {
            "sessionId": session_id,
            "recommendedQuestionPack": {
                "methodCode": normalized_method_code,
                "practiceStrategy": practice_strategy,
                "sourceType": source_type,
                "questionCount": 10,
            },
            "updatedProgress": self._serialize_learning_method_progress(saved),
        }

    def complete_learning_method_practice(self, method_code: str, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        normalized_method_code = self._normalize_learning_method_code(method_code)
        method = self.repository.get_learning_method(normalized_method_code)
        if not method or str(method.get("status", "ACTIVE")).strip().upper() != "ACTIVE":
            raise not_found("学习方法不存在。")

        session_id = str(payload.get("sessionId", "")).strip()
        if not session_id:
            raise validation_failed("sessionId 不能为空。")
        raw_accuracy = float(payload.get("accuracy", 0.0) or 0.0)
        accuracy = raw_accuracy / 100.0 if raw_accuracy > 1.0 and raw_accuracy <= 100.0 else raw_accuracy
        if accuracy < 0.0 or accuracy > 1.0:
            raise validation_failed("accuracy 必须是 0~1 之间的小数，或 0~100 的百分比数值。")
        review_summary = str(payload.get("reviewSummary", "")).strip()
        duration_sec = max(0, int(payload.get("durationSec", 0) or 0))
        now_iso = self._now_iso()

        existing = self.repository.get_student_learning_method_progress(actor.user_id, normalized_method_code)
        current_status = "NOT_STARTED"
        if existing:
            progress_ext = existing.get("extJson", {}) if isinstance(existing.get("extJson"), dict) else {}
            create_time = str(existing.get("createTime", "")).strip() or now_iso
            start_count = max(1, int(existing.get("startCount", 0) or 0))
            complete_count = int(existing.get("completeCount", 0) or 0) + 1
            progress_id = str(existing.get("id", "")).strip() or f"slmp-{actor.user_id}-{normalized_method_code.lower()}"
            current_status = self._normalize_learning_method_progress_status(str(existing.get("status", "NOT_STARTED")))
        else:
            progress_ext = {}
            create_time = now_iso
            start_count = 1
            complete_count = 1
            progress_id = f"slmp-{actor.user_id}-{normalized_method_code.lower()}"

        self._guard_learning_method_progress_transition(current_status, "COMPLETED")
        history = list(progress_ext.get("history", [])) if isinstance(progress_ext.get("history"), list) else []
        history.append(
            {
                "event": "COMPLETE",
                "sessionId": session_id,
                "traceId": session_id,
                "accuracy": round(accuracy, 4),
                "durationSec": duration_sec,
                "reviewSummary": review_summary,
                "eventAt": now_iso,
            }
        )
        if len(history) > 100:
            history = history[-100:]
        progress_ext["history"] = history
        progress_ext["lastSession"] = {
            "sessionId": session_id,
            "completedAt": now_iso,
            "accuracy": round(accuracy, 4),
            "durationSec": duration_sec,
        }
        progress_ext["traceContext"] = {"traceId": session_id, "updateTime": now_iso}
        progress_ext["metricSnapshot"] = {
            "startCount": start_count,
            "completeCount": complete_count,
            "lastAccuracy": round(accuracy, 4),
        }
        progress_ext.pop("currentSession", None)

        saved = self.repository.upsert_student_learning_method_progress(
            {
                "id": progress_id,
                "studentUserId": actor.user_id,
                "methodCode": normalized_method_code,
                "startCount": start_count,
                "completeCount": complete_count,
                "lastPracticedAt": now_iso,
                "lastAccuracy": round(accuracy, 4),
                "lastReviewSummary": review_summary,
                "status": "COMPLETED",
                "extJson": progress_ext,
                "createTime": create_time,
                "updateTime": now_iso,
            }
        )
        return {
            "sessionId": session_id,
            "updatedProgress": self._serialize_learning_method_progress(saved),
        }

    def list_admin_learning_methods(self, status: str) -> Dict[str, object]:
        normalized_status = str(status or "").strip().upper()
        if normalized_status:
            normalized_status = self._normalize_learning_method_status(normalized_status)
        methods = self.repository.list_learning_methods(normalized_status)
        return {"items": [self._serialize_learning_method(item) for item in methods], "total": len(methods)}

    def create_admin_learning_method(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        method_code = self._normalize_learning_method_code(
            str(payload.get("methodCode", "")).strip()
            or str(payload.get("method_code", "")).strip()
        )
        if self.repository.get_learning_method(method_code):
            raise validation_failed("methodCode 已存在。")
        now_iso = self._now_iso()
        existing_methods = self.repository.list_learning_methods("")
        next_sort = max((int(item.get("sort", 0) or 0) for item in existing_methods), default=0) + 1
        requested_sort = int(payload.get("sort", 0) or 0)
        ext_json = payload.get("extJson", {})
        if not isinstance(ext_json, dict):
            ext_json = {}
        ext_json["operatorUserId"] = actor.user_id
        ext_json["updatedBy"] = actor.user_id

        saved = self.repository.upsert_learning_method(
            {
                "id": str(payload.get("id", "")).strip() or f"learning-method-{method_code.lower()}",
                "methodCode": method_code,
                "methodName": str(payload.get("methodName", "")).strip(),
                "oneLineIntro": str(payload.get("oneLineIntro", "")).strip(),
                "useWhen": payload.get("useWhen", []),
                "steps": payload.get("steps", []),
                "commonMistakes": payload.get("commonMistakes", []),
                "questionBankActions": payload.get("questionBankActions", []),
                "starterTask": str(payload.get("starterTask", "")).strip(),
                "difficultyLevel": str(payload.get("difficultyLevel", "L1")).strip() or "L1",
                "estimatedMinutes": int(payload.get("estimatedMinutes", 15) or 15),
                "sort": requested_sort if requested_sort > 0 else next_sort,
                "status": self._normalize_learning_method_status(str(payload.get("status", "ACTIVE")).strip(), "ACTIVE"),
                "extJson": ext_json,
                "createTime": now_iso,
                "updateTime": now_iso,
            }
        )
        return self._serialize_learning_method(saved)

    def update_admin_learning_method(self, method_code: str, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        normalized_method_code = self._normalize_learning_method_code(method_code)
        existing = self.repository.get_learning_method(normalized_method_code)
        if not existing:
            raise not_found("学习方法不存在。")

        incoming_method_code = str(payload.get("methodCode", "")).strip()
        if incoming_method_code and self._normalize_learning_method_code(incoming_method_code) != normalized_method_code:
            raise validation_failed("methodCode 不允许在更新时变更。")
        now_iso = self._now_iso()
        existing_payload = self._serialize_learning_method(existing)

        ext_json = dict(existing_payload.get("extJson", {}))
        incoming_ext_json = payload.get("extJson", {})
        if isinstance(incoming_ext_json, dict):
            ext_json.update(incoming_ext_json)
        ext_json["operatorUserId"] = actor.user_id
        ext_json["updatedBy"] = actor.user_id

        merged = {
            "id": existing_payload["id"],
            "methodCode": normalized_method_code,
            "methodName": str(payload.get("methodName", existing_payload["methodName"])).strip(),
            "oneLineIntro": str(payload.get("oneLineIntro", existing_payload["oneLineIntro"])).strip(),
            "useWhen": payload.get("useWhen", existing_payload.get("useWhen", [])),
            "steps": payload.get("steps", existing_payload.get("steps", [])),
            "commonMistakes": payload.get("commonMistakes", existing_payload.get("commonMistakes", [])),
            "questionBankActions": payload.get("questionBankActions", existing_payload.get("questionBankActions", [])),
            "starterTask": str(payload.get("starterTask", existing_payload.get("starterTask", ""))).strip(),
            "difficultyLevel": str(payload.get("difficultyLevel", existing_payload.get("difficultyLevel", "L1"))).strip() or "L1",
            "estimatedMinutes": int(payload.get("estimatedMinutes", existing_payload.get("estimatedMinutes", 15)) or 15),
            "sort": int(payload.get("sort", existing_payload.get("sort", 0)) or 0),
            "status": self._normalize_learning_method_status(
                str(payload.get("status", existing_payload.get("status", "ACTIVE"))).strip(),
                "ACTIVE",
            ),
            "extJson": ext_json,
            "createTime": str(existing_payload.get("createTime", "")) or now_iso,
            "updateTime": now_iso,
        }
        saved = self.repository.upsert_learning_method(merged)
        return self._serialize_learning_method(saved)

    def sort_admin_learning_methods(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        method_codes_raw = payload.get("methodCodes", payload.get("method_codes", []))
        if not isinstance(method_codes_raw, list) or not method_codes_raw:
            raise validation_failed("methodCodes 不能为空。")
        normalized_codes: List[str] = []
        seen_codes: set[str] = set()
        for raw_code in method_codes_raw:
            normalized_code = self._normalize_learning_method_code(str(raw_code))
            if normalized_code in seen_codes:
                continue
            seen_codes.add(normalized_code)
            normalized_codes.append(normalized_code)
        if not normalized_codes:
            raise validation_failed("methodCodes 不能为空。")

        existing_methods = self.repository.list_learning_methods("")
        method_map = {
            str(item.get("methodCode", "")).strip().upper(): item
            for item in existing_methods
            if str(item.get("methodCode", "")).strip()
        }
        for code in normalized_codes:
            if code not in method_map:
                raise not_found(f"学习方法不存在：{code}")

        tail_codes = [code for code in method_map.keys() if code not in set(normalized_codes)]
        ordered_codes = normalized_codes + tail_codes
        now_iso = self._now_iso()
        for index, code in enumerate(ordered_codes, start=1):
            method_item = method_map[code]
            method_payload = self._serialize_learning_method(method_item)
            ext_json = dict(method_payload.get("extJson", {}))
            ext_json["sortOperatorUserId"] = actor.user_id
            saved_payload = {
                "id": method_payload["id"],
                "methodCode": method_payload["methodCode"],
                "methodName": method_payload["methodName"],
                "oneLineIntro": method_payload["oneLineIntro"],
                "useWhen": method_payload["useWhen"],
                "steps": method_payload["steps"],
                "commonMistakes": method_payload["commonMistakes"],
                "questionBankActions": method_payload["questionBankActions"],
                "starterTask": method_payload["starterTask"],
                "difficultyLevel": method_payload["difficultyLevel"],
                "estimatedMinutes": method_payload["estimatedMinutes"],
                "sort": index,
                "status": method_payload["status"],
                "extJson": ext_json,
                "createTime": method_payload["createTime"] or now_iso,
                "updateTime": now_iso,
            }
            method_map[code] = self.repository.upsert_learning_method(saved_payload)

        ordered_items = [self._serialize_learning_method(method_map[code]) for code in ordered_codes]
        return {"items": ordered_items, "total": len(ordered_items)}

    def _normalize_learning_method_feedback_status(self, status: str, default: str = "ACCEPTED") -> str:
        normalized = str(status or "").strip().upper() or default
        if normalized not in LEARNING_METHOD_FEEDBACK_STATUSES:
            raise validation_failed("feedbackStatus 仅支持 PENDING、ACCEPTED、PARTIAL、REJECTED、COMPLETED。")
        return normalized

    def _normalize_question_difficulty(self, difficulty: object, fallback: str = "medium") -> str:
        normalized = str(difficulty or "").strip().lower()
        return normalized if normalized in QUESTION_DIFFICULTIES else fallback

    def _learning_method_text_blob(self, method: Dict[str, object]) -> str:
        parts: List[str] = [
            str(method.get("methodName", "")),
            str(method.get("oneLineIntro", "")),
            str(method.get("starterTask", "")),
        ]
        for key in ("useWhen", "steps", "commonMistakes", "questionBankActions"):
            value = method.get(key, [])
            if isinstance(value, list):
                parts.extend(str(item) for item in value)
        return "\n".join(item.strip() for item in parts if str(item).strip())

    def _auto_generate_learning_method_profile_payload(
        self,
        method: Dict[str, object],
        profile_version: str,
        strategy_type: str,
        actor: Actor,
    ) -> Dict[str, object]:
        method_payload = self._serialize_learning_method(method)
        method_code = str(method_payload.get("methodCode", "")).strip().upper()
        text_blob = self._learning_method_text_blob(method_payload)

        keyword_rules = {
            "concept": ["概念", "理解", "理论", "定义", "原理", "why"],
            "calculation": ["计算", "推导", "公式", "运算", "证明", "求"],
            "application": ["应用", "案例", "实战", "情境", "综合"],
            "memory": ["记忆", "背诵", "口诀", "模板", "高频"],
            "review": ["复盘", "错题", "纠错", "回顾", "反思"],
            "speed": ["限时", "冲刺", "提速", "快", "效率"],
        }
        method_tags: List[str] = []
        matched_keywords = 0
        lowered_blob = text_blob.lower()
        for tag, keywords in keyword_rules.items():
            if any(keyword.lower() in lowered_blob for keyword in keywords):
                method_tags.append(tag)
                matched_keywords += 1

        if not method_tags:
            method_tags = ["concept", "application"]

        question_type_weights = {
            "single_choice": 0.35,
            "multiple_choice": 0.25,
            "judge": 0.1,
            "subjective": 0.3,
        }
        if "calculation" in method_tags:
            question_type_weights["subjective"] = 0.45
            question_type_weights["single_choice"] = 0.25
        if "memory" in method_tags:
            question_type_weights["single_choice"] = 0.45
            question_type_weights["multiple_choice"] = 0.35
            question_type_weights["subjective"] = 0.15
        if "review" in method_tags:
            question_type_weights["single_choice"] = 0.3
            question_type_weights["multiple_choice"] = 0.3
            question_type_weights["subjective"] = 0.3

        difficulty_level = str(method_payload.get("difficultyLevel", "L2")).strip().upper() or "L2"
        primary_difficulty = LEARNING_METHOD_DIFFICULTY_MAP.get(difficulty_level, "medium")
        difficulty_weights = {"easy": 0.2, "medium": 0.5, "hard": 0.3}
        if primary_difficulty == "easy":
            difficulty_weights = {"easy": 0.55, "medium": 0.35, "hard": 0.1}
        elif primary_difficulty == "hard":
            difficulty_weights = {"easy": 0.1, "medium": 0.35, "hard": 0.55}

        weakness_focus = ["wrong_rate", "knowledge_gap"]
        if "review" in method_tags:
            weakness_focus.append("wrong_book")

        score_weights = {
            "methodFit": 0.33,
            "weaknessFit": 0.27,
            "difficultyFit": 0.15,
            "freshnessFit": 0.1,
            "studentProfileFit": 0.15,
        }
        if "speed" in method_tags:
            score_weights["methodFit"] = 0.28
            score_weights["weaknessFit"] = 0.22
            score_weights["freshnessFit"] = 0.2

        confidence = min(0.95, max(0.45, 0.45 + matched_keywords * 0.08))
        now_iso = self._now_iso()
        return {
            "id": f"learning-method-profile-{method_code.lower()}",
            "methodCode": method_code,
            "profileVersion": profile_version,
            "strategyType": strategy_type,
            "profile": {
                "methodTags": method_tags,
                "questionTypeWeights": question_type_weights,
                "difficultyWeights": difficulty_weights,
                "weaknessFocus": weakness_focus,
                "scoreWeights": score_weights,
                "estimatedMinutes": int(method_payload.get("estimatedMinutes", 15) or 15),
                "starterTask": str(method_payload.get("starterTask", "")).strip(),
            },
            "confidence": round(confidence, 4),
            "extJson": {
                "generatedBy": "AUTO_RULE",
                "operatorUserId": actor.user_id,
                "methodName": method_payload.get("methodName", ""),
                "generatedAt": now_iso,
            },
            "createTime": now_iso,
            "updateTime": now_iso,
        }

    def _extract_question_match_feature(self, question: Dict[str, object]) -> Dict[str, object]:
        ext_json = self._load_json_object(str(question.get("extJson", "{}")))
        stem = str(question.get("stem", "")).strip()
        question_type = str(question.get("type", "")).strip() or "single_choice"
        difficulty = self._normalize_question_difficulty(ext_json.get("difficulty"), "medium")

        knowledge_tags = ext_json.get("knowledgeTags", [])
        normalized_knowledge_tags = []
        if isinstance(knowledge_tags, list):
            normalized_knowledge_tags = [str(item).strip() for item in knowledge_tags if str(item).strip()]

        method_tags: List[str] = []
        keyword_map = {
            "concept": ["概念", "定义", "理论", "原理", "辨析"],
            "calculation": ["计算", "求", "推导", "证明", "函数", "方程"],
            "application": ["应用", "案例", "情景", "材料", "实践"],
            "memory": ["记忆", "背诵", "术语", "单词", "高频"],
            "review": ["纠错", "复盘", "错因", "易错", "陷阱"],
            "speed": ["限时", "快速", "高效", "秒", "速度"],
        }
        lowered_stem = stem.lower()
        for tag, keywords in keyword_map.items():
            if any(keyword.lower() in lowered_stem for keyword in keywords):
                method_tags.append(tag)

        if question_type == "subjective" and "calculation" not in method_tags:
            method_tags.append("calculation")
        if question_type in {"single_choice", "multiple_choice"} and "memory" not in method_tags:
            method_tags.append("memory")

        if not method_tags:
            method_tags = ["concept", "application"]

        metadata_hit_count = 0
        if str(ext_json.get("subjectCode", "")).strip():
            metadata_hit_count += 1
        if str(question.get("knowledgeId", "")).strip():
            metadata_hit_count += 1
        if normalized_knowledge_tags:
            metadata_hit_count += 1
        if str(ext_json.get("chapterCode", "")).strip() or str(ext_json.get("pointCode", "")).strip():
            metadata_hit_count += 1
        quality_score = min(0.98, 0.55 + metadata_hit_count * 0.1)

        return {
            "methodTags": sorted(set(method_tags)),
            "feature": {
                "questionType": question_type,
                "difficulty": difficulty,
                "subjectCode": str(ext_json.get("subjectCode", "")).strip(),
                "knowledgeId": str(question.get("knowledgeId", "")).strip(),
                "knowledgeTags": normalized_knowledge_tags[:8],
                "chapterCode": str(ext_json.get("chapterCode", "")).strip(),
                "pointCode": str(ext_json.get("pointCode", "")).strip(),
                "keywords": sorted(set(method_tags))[:6],
            },
            "qualityScore": round(quality_score, 4),
        }

    def auto_generate_learning_method_profile(
        self,
        method_code: str,
        payload: Dict[str, object],
        actor: Actor,
    ) -> Dict[str, object]:
        normalized_method_code = self._normalize_learning_method_code(method_code)
        method = self.repository.get_learning_method(normalized_method_code)
        if not method:
            raise not_found("学习方法不存在。")

        profile_version = str(payload.get("profileVersion", "v1")).strip() or "v1"
        strategy_type = str(payload.get("strategyType", "RULE_BASED")).strip().upper() or "RULE_BASED"
        generated_payload = self._auto_generate_learning_method_profile_payload(method, profile_version, strategy_type, actor)
        saved = self.repository.upsert_learning_method_profile(generated_payload)
        return {
            "methodCode": normalized_method_code,
            "profileVersion": str(saved.get("profileVersion", profile_version)),
            "strategyType": str(saved.get("strategyType", strategy_type)),
            "confidence": float(saved.get("confidence", 0.0) or 0.0),
            "profile": saved.get("profile", {}) if isinstance(saved.get("profile"), dict) else {},
            "extJson": saved.get("extJson", {}) if isinstance(saved.get("extJson"), dict) else {},
            "updateTime": str(saved.get("updateTime", "")),
        }

    def auto_batch_question_match_features(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        limit = max(1, min(2000, int(payload.get("limit", 200) or 200)))
        source_type = str(payload.get("sourceType", "AUTO_RULE")).strip().upper() or "AUTO_RULE"
        force_refresh = bool(payload.get("forceRefresh", False))

        question_ids_raw = payload.get("questionIds", [])
        normalized_question_ids: List[str] = []
        if isinstance(question_ids_raw, list):
            for item in question_ids_raw:
                question_id = str(item or "").strip()
                if question_id and question_id not in normalized_question_ids:
                    normalized_question_ids.append(question_id)

        if normalized_question_ids:
            questions = self.repository.list_questions_by_ids(normalized_question_ids[:limit])
        else:
            questions, _ = self.repository.list_questions(
                {
                    "status": "PUBLISHED",
                    "policyVersion": POLICY_VERSION_CODE,
                },
                1,
                limit,
                ROLE_SUPER_ADMIN,
                actor.user_id,
            )

        processed = 0
        skipped = 0
        saved_ids: List[str] = []
        for question in questions:
            question_id = str(question.get("id", "")).strip()
            if not question_id:
                continue
            if not force_refresh and self.repository.get_question_match_feature(question_id):
                skipped += 1
                continue
            feature_payload = self._extract_question_match_feature(question)
            now_iso = self._now_iso()
            saved = self.repository.upsert_question_match_feature(
                {
                    "id": f"question-match-feature-{question_id}",
                    "questionId": question_id,
                    "methodTags": feature_payload["methodTags"],
                    "feature": feature_payload["feature"],
                    "qualityScore": feature_payload["qualityScore"],
                    "sourceType": source_type,
                    "extJson": {
                        "updatedBy": actor.user_id,
                        "updateTime": now_iso,
                        "forceRefresh": force_refresh,
                    },
                    "createTime": now_iso,
                    "updateTime": now_iso,
                }
            )
            processed += 1
            saved_ids.append(str(saved.get("questionId", question_id)))

        return {
            "totalQuestions": len(questions),
            "processed": processed,
            "skipped": skipped,
            "sourceType": source_type,
            "sampleQuestionIds": saved_ids[:20],
        }

    def _resolve_learning_method_profile_for_recommend(
        self,
        method: Dict[str, object],
        actor: Actor,
    ) -> Dict[str, object]:
        method_code = str(method.get("methodCode", "")).strip().upper()
        profile = self.repository.get_learning_method_profile(method_code)
        if profile:
            return profile
        generated = self._auto_generate_learning_method_profile_payload(method, "v1", "RULE_BASED", actor)
        return self.repository.upsert_learning_method_profile(generated)

    def _student_question_weakness_map(self, student_user_id: str) -> Dict[str, Dict[str, float]]:
        rows = self.repository.list_student_question_record_rows(student_user_id)
        question_weakness: Dict[str, float] = {}
        knowledge_totals: Dict[str, Dict[str, int]] = {}
        for row in rows:
            question_id = str(row.get("questionId", "")).strip()
            answer_count = max(0, int(row.get("answerCount", 0) or 0))
            wrong_count = max(0, int(row.get("wrongCount", 0) or 0))
            knowledge_id = str(row.get("questionId", "")).strip()
            if question_id and answer_count > 0:
                question_weakness[question_id] = min(1.0, max(0.0, wrong_count / float(answer_count)))
            if not question_id:
                continue
            question = self.repository.get_question(question_id)
            if not question:
                continue
            knowledge_id = str(question.get("knowledgeId", "")).strip()
            if not knowledge_id:
                continue
            counters = knowledge_totals.setdefault(knowledge_id, {"answer": 0, "wrong": 0})
            counters["answer"] += answer_count
            counters["wrong"] += wrong_count

        knowledge_weakness: Dict[str, float] = {}
        for knowledge_id, counters in knowledge_totals.items():
            answer_total = max(0, int(counters.get("answer", 0) or 0))
            wrong_total = max(0, int(counters.get("wrong", 0) or 0))
            knowledge_weakness[knowledge_id] = min(1.0, max(0.0, wrong_total / float(answer_total))) if answer_total else 0.0
        return {
            "question": question_weakness,
            "knowledge": knowledge_weakness,
        }

    def _build_recommendation_candidates(
        self,
        actor: Actor,
        payload: Dict[str, object],
    ) -> List[Dict[str, str]]:
        profile = self._get_student_profile(actor.user_id)
        subject_code = str(payload.get("subjectCode", "")).strip()
        filters = {
            "policyVersion": POLICY_VERSION_CODE,
            "examCategoryCode": str(profile.get("examCategoryCode", "")).strip(),
            "jointExamGroupCode": str(profile.get("jointExamGroupCode", "")).strip(),
            "subjectCode": subject_code,
        }
        questions = self.repository.list_visible_published_questions(filters, actor.role, actor.user_id)
        if questions:
            return questions
        fallback_filters = {
            "policyVersion": POLICY_VERSION_CODE,
            "subjectCode": subject_code,
        }
        return self.repository.list_visible_published_questions(fallback_filters, actor.role, actor.user_id)

    def _score_learning_method_question(
        self,
        question: Dict[str, str],
        question_feature: Dict[str, object],
        profile_payload: Dict[str, object],
        weakness_map: Dict[str, Dict[str, float]],
        student_profile_fit_context: Dict[str, object],
    ) -> Dict[str, object]:
        profile_method_tags = {
            str(item).strip()
            for item in profile_payload.get("methodTags", [])
            if str(item).strip()
        }
        question_method_tags = {
            str(item).strip()
            for item in question_feature.get("methodTags", [])
            if str(item).strip()
        }
        method_overlap = len(profile_method_tags.intersection(question_method_tags))
        method_fit = min(1.0, method_overlap / max(1, len(profile_method_tags)))

        question_id = str(question.get("id", "")).strip()
        knowledge_id = str(question.get("knowledgeId", "")).strip()
        weakness_question = float(weakness_map.get("question", {}).get(question_id, 0.0) or 0.0)
        weakness_knowledge = float(weakness_map.get("knowledge", {}).get(knowledge_id, 0.0) or 0.0)
        weakness_fit = min(1.0, 0.65 * weakness_question + 0.35 * weakness_knowledge)

        feature = question_feature.get("feature", {}) if isinstance(question_feature.get("feature"), dict) else {}
        question_difficulty = self._normalize_question_difficulty(feature.get("difficulty"), "medium")
        difficulty_weights = profile_payload.get("difficultyWeights", {}) if isinstance(profile_payload.get("difficultyWeights"), dict) else {}
        difficulty_fit = float(difficulty_weights.get(question_difficulty, 0.0) or 0.0)

        freshness_fit = 1.0 - min(1.0, weakness_question * 0.6)
        if weakness_question == 0.0:
            freshness_fit = 0.95

        profile_tags = {
            str(item).strip()
            for item in student_profile_fit_context.get("profileTags", [])
            if str(item).strip()
        }
        student_tag_fit = min(1.0, len(profile_tags.intersection(question_method_tags)) / max(1, len(profile_tags)))

        profile_question_type_weights = student_profile_fit_context.get("questionTypeWeights", {})
        if not isinstance(profile_question_type_weights, dict):
            profile_question_type_weights = {}
        question_type = str(feature.get("questionType", question.get("type", ""))).strip()
        raw_type_weight = float(profile_question_type_weights.get(question_type, 0.0) or 0.0)
        max_type_weight = max((float(item or 0.0) for item in profile_question_type_weights.values()), default=0.0)
        student_type_fit = raw_type_weight / max_type_weight if max_type_weight > 0 else 0.0

        preferred_difficulty = self._normalize_question_difficulty(
            student_profile_fit_context.get("difficultyPreference"),
            "medium",
        )
        difficulty_distance = abs(
            QUESTION_DIFFICULTY_ORDER.get(question_difficulty, 1)
            - QUESTION_DIFFICULTY_ORDER.get(preferred_difficulty, 1)
        )
        student_difficulty_fit = max(0.3, 1.0 - difficulty_distance * 0.35)
        student_profile_fit = (
            student_tag_fit * 0.5
            + student_type_fit * 0.3
            + student_difficulty_fit * 0.2
        )

        score_weights = profile_payload.get("scoreWeights", {}) if isinstance(profile_payload.get("scoreWeights"), dict) else {}
        weight_method = float(score_weights.get("methodFit", 0.33) or 0.33)
        weight_weakness = float(score_weights.get("weaknessFit", 0.27) or 0.27)
        weight_difficulty = float(score_weights.get("difficultyFit", 0.15) or 0.15)
        weight_freshness = float(score_weights.get("freshnessFit", 0.1) or 0.1)
        weight_profile = float(score_weights.get("studentProfileFit", 0.15) or 0.15)
        weight_sum = weight_method + weight_weakness + weight_difficulty + weight_freshness + weight_profile
        if weight_sum <= 0:
            weight_method, weight_weakness, weight_difficulty, weight_freshness, weight_profile = 0.33, 0.27, 0.15, 0.1, 0.15
            weight_sum = 1.0

        score = (
            method_fit * weight_method
            + weakness_fit * weight_weakness
            + difficulty_fit * weight_difficulty
            + freshness_fit * weight_freshness
            + student_profile_fit * weight_profile
        ) / weight_sum

        reason_tags: List[str] = []
        if method_fit >= 0.5:
            reason_tags.append("method_fit")
        if weakness_fit >= 0.45:
            reason_tags.append("weakness_hit")
        if difficulty_fit >= 0.45:
            reason_tags.append("difficulty_aligned")
        if freshness_fit >= 0.8:
            reason_tags.append("fresh_question")
        if student_profile_fit >= 0.5:
            reason_tags.append("profile_fit")
        if not reason_tags:
            reason_tags.append("balanced_mix")

        return {
            "score": round(score, 6),
            "scoreBreakdown": {
                "methodFit": round(method_fit, 6),
                "weaknessFit": round(weakness_fit, 6),
                "difficultyFit": round(difficulty_fit, 6),
                "freshnessFit": round(freshness_fit, 6),
                "studentProfileFit": round(student_profile_fit, 6),
                "weights": {
                    "methodFit": round(weight_method, 6),
                    "weaknessFit": round(weight_weakness, 6),
                    "difficultyFit": round(weight_difficulty, 6),
                    "freshnessFit": round(weight_freshness, 6),
                    "studentProfileFit": round(weight_profile, 6),
                },
                "profileContext": {
                    "profileTags": sorted(profile_tags),
                    "questionTypeWeights": profile_question_type_weights,
                    "difficultyPreference": preferred_difficulty,
                },
            },
            "reasonTags": reason_tags,
            "difficulty": question_difficulty,
            "questionType": question_type,
            "knowledgeId": knowledge_id,
            "methodTags": sorted(question_method_tags),
        }

    def _build_student_profile_fit_context(
        self,
        profile: Dict[str, object],
        weakness_map: Dict[str, Dict[str, float]],
    ) -> Dict[str, object]:
        prep_stage = str(profile.get("prepStage", "")).strip().lower()
        vocational_major = str(profile.get("vocationalMajor", "")).strip().lower()
        exam_category_code = str(profile.get("examCategoryCode", "")).strip().upper()
        joint_exam_group_code = str(profile.get("jointExamGroupCode", "")).strip().upper()
        tags: set[str] = set()

        if prep_stage:
            if any(keyword in prep_stage for keyword in ("基础", "入门", "一轮", "basic")):
                tags.update({"concept", "memory"})
            if any(keyword in prep_stage for keyword in ("强化", "进阶", "二轮", "专项", "提高", "advanced")):
                tags.update({"application", "calculation"})
            if any(keyword in prep_stage for keyword in ("冲刺", "考前", "模考", "sprint")):
                tags.update({"speed", "review"})

        if vocational_major:
            if any(keyword in vocational_major for keyword in ("数学", "理工", "机械", "计算机", "工程", "化学", "物理")):
                tags.add("calculation")
            if any(keyword in vocational_major for keyword in ("法", "史", "文", "语言", "教育", "护理")):
                tags.update({"concept", "memory"})
            if any(keyword in vocational_major for keyword in ("管理", "经济", "金融", "市场", "运营")):
                tags.update({"application", "review"})

        question_weakness = weakness_map.get("question", {}) if isinstance(weakness_map.get("question"), dict) else {}
        if question_weakness:
            avg_weakness = sum(float(value or 0.0) for value in question_weakness.values()) / max(1, len(question_weakness))
            if avg_weakness >= 0.35:
                tags.add("review")
            if avg_weakness >= 0.55:
                tags.update({"memory", "concept"})

        if exam_category_code.startswith("SCIENCE"):
            tags.update({"calculation", "application"})
        if exam_category_code.startswith("ARTS"):
            tags.update({"concept", "memory"})
        if "MEDICINE" in joint_exam_group_code:
            tags.update({"memory", "review"})

        if not tags:
            tags.update({"concept", "review"})

        difficulty_preference = "medium"
        if prep_stage and any(keyword in prep_stage for keyword in ("基础", "入门", "一轮", "basic")):
            difficulty_preference = "easy"
        elif prep_stage and any(keyword in prep_stage for keyword in ("冲刺", "考前", "三轮", "sprint")):
            difficulty_preference = "hard"

        question_type_weights = {
            "single_choice": 0.3,
            "multiple_choice": 0.25,
            "judge": 0.1,
            "subjective": 0.35,
        }
        if "memory" in tags:
            question_type_weights["single_choice"] = 0.4
            question_type_weights["multiple_choice"] = 0.35
            question_type_weights["subjective"] = 0.2
        if "calculation" in tags:
            question_type_weights["subjective"] = max(question_type_weights["subjective"], 0.45)
        if "speed" in tags:
            question_type_weights["judge"] = max(question_type_weights["judge"], 0.2)

        return {
            "profileTags": sorted(tags),
            "difficultyPreference": difficulty_preference,
            "questionTypeWeights": question_type_weights,
        }

    def recommend_learning_method_question_pack(
        self,
        method_code: str,
        payload: Dict[str, object],
        actor: Actor,
    ) -> Dict[str, object]:
        normalized_method_code = self._normalize_learning_method_code(method_code)
        method = self.repository.get_learning_method(normalized_method_code)
        if not method or str(method.get("status", "ACTIVE")).strip().upper() != "ACTIVE":
            raise not_found("学习方法不存在。")

        question_count = max(5, min(30, int(payload.get("questionCount", 12) or 12)))
        session_id = str(payload.get("sessionId", "")).strip() or f"lm-session-{uuid.uuid4().hex[:12]}"
        source_type = str(payload.get("sourceType", "LEARNING_METHOD_PAGE")).strip() or "LEARNING_METHOD_PAGE"
        subject_code = str(payload.get("subjectCode", "")).strip()
        difficulty_preference = self._normalize_question_difficulty(payload.get("difficultyPreference", ""), "")
        practice_strategy = str(payload.get("practiceStrategy", "")).strip().upper() or "DEFAULT"
        recommendation_strategy_code = self._resolve_recommendation_strategy_code(practice_strategy)
        strategy_source = self._normalize_recommendation_strategy_source(
            str(payload.get("strategySource", "")).strip(),
            "DEFAULT",
        )

        profile = self._resolve_learning_method_profile_for_recommend(method, actor)
        profile_payload = profile.get("profile", {}) if isinstance(profile.get("profile"), dict) else {}

        candidates = self._build_recommendation_candidates(actor, {"subjectCode": subject_code})
        if not candidates:
            raise not_found("暂无可推荐题目，请先补充已发布题目。")

        candidate_ids = [str(item.get("id", "")).strip() for item in candidates if str(item.get("id", "")).strip()]
        feature_rows = self.repository.list_question_match_features_by_question_ids(candidate_ids)
        feature_map = {str(item.get("questionId", "")).strip(): item for item in feature_rows}

        weakness_map = self._student_question_weakness_map(actor.user_id)
        student_profile = self._get_student_profile(actor.user_id)
        student_profile_fit_context = self._build_student_profile_fit_context(student_profile, weakness_map)

        scored_items: List[Dict[str, object]] = []
        for question in candidates:
            question_id = str(question.get("id", "")).strip()
            if not question_id:
                continue
            question_feature = feature_map.get(question_id)
            if not question_feature:
                extracted = self._extract_question_match_feature(question)
                now_iso = self._now_iso()
                question_feature = self.repository.upsert_question_match_feature(
                    {
                        "id": f"question-match-feature-{question_id}",
                        "questionId": question_id,
                        "methodTags": extracted["methodTags"],
                        "feature": extracted["feature"],
                        "qualityScore": extracted["qualityScore"],
                        "sourceType": "AUTO_ON_DEMAND",
                        "extJson": {
                            "updateTime": now_iso,
                            "sourceType": source_type,
                        },
                        "createTime": now_iso,
                        "updateTime": now_iso,
                    }
                )
                feature_map[question_id] = question_feature

            score_payload = self._score_learning_method_question(
                question,
                question_feature,
                profile_payload,
                weakness_map,
                student_profile_fit_context,
            )
            if difficulty_preference and score_payload["difficulty"] != difficulty_preference:
                score_payload["score"] = float(score_payload["score"]) * 0.85
                score_payload["scoreBreakdown"]["difficultyPreferencePenalty"] = 0.15
            scored_items.append(
                {
                    "question": question,
                    "questionFeature": question_feature,
                    "score": float(score_payload["score"]),
                    "scoreBreakdown": score_payload["scoreBreakdown"],
                    "reasonTags": score_payload["reasonTags"],
                    "difficulty": score_payload["difficulty"],
                    "questionType": score_payload["questionType"],
                    "knowledgeId": score_payload["knowledgeId"],
                    "methodTags": score_payload["methodTags"],
                }
            )

        scored_items.sort(key=lambda item: (item["score"], str(item["question"].get("id", ""))), reverse=True)
        selected_items = scored_items[:question_count]
        if not selected_items:
            raise not_found("暂无匹配题目，请稍后重试。")

        recommendation_id = f"lm-rec-{uuid.uuid4().hex[:12]}"
        now_iso = self._now_iso()
        selected_question_ids = [str(item["question"].get("id", "")).strip() for item in selected_items]
        aggregate_reason_tags = sorted(
            {
                reason_tag
                for item in selected_items
                for reason_tag in item.get("reasonTags", [])
                if str(reason_tag).strip()
            }
        )

        score_summary = {
            "averageScore": round(sum(float(item["score"]) for item in selected_items) / len(selected_items), 6),
            "maxScore": round(max(float(item["score"]) for item in selected_items), 6),
            "minScore": round(min(float(item["score"]) for item in selected_items), 6),
            "weights": profile_payload.get("scoreWeights", {}),
            "items": [
                {
                    "questionId": str(item["question"].get("id", "")),
                    "score": round(float(item["score"]), 6),
                    "scoreBreakdown": item.get("scoreBreakdown", {}),
                    "reasonTags": item.get("reasonTags", []),
                }
                for item in selected_items
            ],
            "studentProfile": {
                "tags": student_profile_fit_context.get("profileTags", []),
                "difficultyPreference": student_profile_fit_context.get("difficultyPreference", "medium"),
                "questionTypeWeights": student_profile_fit_context.get("questionTypeWeights", {}),
            },
        }

        saved_log = self.repository.upsert_learning_method_recommendation_log(
            {
                "id": f"learning-method-recommendation-{actor.user_id}-{recommendation_id}",
                "studentUserId": actor.user_id,
                "methodCode": normalized_method_code,
                "recommendationId": recommendation_id,
                "sessionId": session_id,
                "questionIds": selected_question_ids,
                "score": score_summary,
                "reasonTags": aggregate_reason_tags,
                "feedbackStatus": "PENDING",
                "feedback": {},
                "recommendedAt": now_iso,
                "feedbackAt": "",
                "extJson": {
                    "sourceType": source_type,
                    "subjectCode": subject_code,
                    "difficultyPreference": difficulty_preference,
                    "practiceStrategy": practice_strategy,
                    "recommendationStrategyCode": recommendation_strategy_code,
                    "strategySource": strategy_source,
                    "profileVersion": str(profile.get("profileVersion", "v1")),
                },
                "createTime": now_iso,
                "updateTime": now_iso,
            }
        )

        return {
            "recommendationId": recommendation_id,
            "sessionId": session_id,
            "methodCode": normalized_method_code,
            "questionCount": len(selected_items),
            "profileVersion": str(profile.get("profileVersion", "v1")),
            "strategyType": str(profile.get("strategyType", "RULE_BASED")),
            "difficultyPreference": difficulty_preference,
            "practiceStrategy": practice_strategy,
            "recommendationStrategyCode": recommendation_strategy_code,
            "recommendationStrategySource": strategy_source,
            "reasonTags": aggregate_reason_tags,
            "scoreSummary": score_summary,
            "questions": [
                {
                    "questionId": str(item["question"].get("id", "")),
                    "type": str(item["questionType"]),
                    "difficulty": str(item["difficulty"]),
                    "knowledgeId": str(item["knowledgeId"]),
                    "score": round(float(item["score"]), 6),
                    "reasonTags": item.get("reasonTags", []),
                    "scoreBreakdown": item.get("scoreBreakdown", {}),
                }
                for item in selected_items
            ],
            "recommendationLog": {
                "id": str(saved_log.get("id", "")),
                "feedbackStatus": str(saved_log.get("feedbackStatus", "PENDING")),
                "recommendedAt": str(saved_log.get("recommendedAt", now_iso)),
                "difficultyPreference": difficulty_preference,
                "practiceStrategy": practice_strategy,
                "recommendationStrategyCode": recommendation_strategy_code,
                "strategySource": strategy_source,
            },
        }

    def feedback_learning_method_question_pack(
        self,
        method_code: str,
        payload: Dict[str, object],
        actor: Actor,
    ) -> Dict[str, object]:
        normalized_method_code = self._normalize_learning_method_code(method_code)
        method = self.repository.get_learning_method(normalized_method_code)
        if not method or str(method.get("status", "ACTIVE")).strip().upper() != "ACTIVE":
            raise not_found("学习方法不存在。")

        recommendation_id = str(payload.get("recommendationId", "")).strip()
        if not recommendation_id:
            raise validation_failed("recommendationId 不能为空。")

        saved_log = self.repository.get_learning_method_recommendation_log(actor.user_id, recommendation_id)
        if not saved_log:
            raise not_found("推荐记录不存在。")
        if str(saved_log.get("methodCode", "")).strip().upper() != normalized_method_code:
            raise validation_failed("recommendationId 与 methodCode 不匹配。")

        feedback_status = self._normalize_learning_method_feedback_status(str(payload.get("feedbackStatus", "ACCEPTED")))
        completed_question_ids = [
            str(item).strip()
            for item in payload.get("completedQuestionIds", [])
            if str(item).strip()
        ] if isinstance(payload.get("completedQuestionIds", []), list) else []
        skipped_question_ids = [
            str(item).strip()
            for item in payload.get("skippedQuestionIds", [])
            if str(item).strip()
        ] if isinstance(payload.get("skippedQuestionIds", []), list) else []
        now_iso = self._now_iso()

        feedback_payload = {
            "isHelpful": bool(payload.get("isHelpful", True)),
            "completedQuestionIds": completed_question_ids,
            "skippedQuestionIds": skipped_question_ids,
            "note": str(payload.get("note", "")).strip(),
            "operatorUserId": actor.user_id,
            "feedbackAt": now_iso,
        }

        ext_payload = saved_log.get("extJson", {}) if isinstance(saved_log.get("extJson"), dict) else {}
        ext_payload["lastFeedbackSource"] = "LEARNING_METHOD_PAGE"
        ext_payload["lastFeedbackAt"] = now_iso

        updated_log = self.repository.upsert_learning_method_recommendation_log(
            {
                "id": str(saved_log.get("id", "")),
                "studentUserId": actor.user_id,
                "methodCode": normalized_method_code,
                "recommendationId": recommendation_id,
                "sessionId": str(payload.get("sessionId", "")).strip() or str(saved_log.get("sessionId", "")).strip(),
                "questionIds": saved_log.get("questionIds", []),
                "score": saved_log.get("score", {}),
                "reasonTags": saved_log.get("reasonTags", []),
                "feedbackStatus": feedback_status,
                "feedback": feedback_payload,
                "recommendedAt": str(saved_log.get("recommendedAt", "")).strip() or now_iso,
                "feedbackAt": now_iso,
                "extJson": ext_payload,
                "createTime": str(saved_log.get("createTime", "")).strip() or now_iso,
                "updateTime": now_iso,
            }
        )

        progress = self.repository.get_student_learning_method_progress(actor.user_id, normalized_method_code)
        if progress:
            progress_ext = progress.get("extJson", {}) if isinstance(progress.get("extJson"), dict) else {}
            feedback_history = list(progress_ext.get("recommendationFeedbackHistory", [])) if isinstance(progress_ext.get("recommendationFeedbackHistory"), list) else []
            feedback_history.append(
                {
                    "recommendationId": recommendation_id,
                    "feedbackStatus": feedback_status,
                    "isHelpful": bool(feedback_payload.get("isHelpful", True)),
                    "feedbackAt": now_iso,
                }
            )
            if len(feedback_history) > 100:
                feedback_history = feedback_history[-100:]
            progress_ext["recommendationFeedbackHistory"] = feedback_history
            progress_ext["lastRecommendationFeedback"] = {
                "recommendationId": recommendation_id,
                "feedbackStatus": feedback_status,
                "isHelpful": bool(feedback_payload.get("isHelpful", True)),
                "feedbackAt": now_iso,
            }
            self.repository.upsert_student_learning_method_progress(
                {
                    "id": str(progress.get("id", "")).strip() or f"slmp-{actor.user_id}-{normalized_method_code.lower()}",
                    "studentUserId": actor.user_id,
                    "methodCode": normalized_method_code,
                    "startCount": int(progress.get("startCount", 0) or 0),
                    "completeCount": int(progress.get("completeCount", 0) or 0),
                    "lastPracticedAt": str(progress.get("lastPracticedAt", "")).strip(),
                    "lastAccuracy": float(progress.get("lastAccuracy", 0.0) or 0.0),
                    "lastReviewSummary": str(progress.get("lastReviewSummary", "")).strip(),
                    "status": str(progress.get("status", "NOT_STARTED")).strip() or "NOT_STARTED",
                    "extJson": progress_ext,
                    "createTime": str(progress.get("createTime", "")).strip() or now_iso,
                    "updateTime": now_iso,
                }
            )

        return {
            "recommendationId": recommendation_id,
            "methodCode": normalized_method_code,
            "feedbackStatus": str(updated_log.get("feedbackStatus", feedback_status)),
            "feedbackAt": str(updated_log.get("feedbackAt", now_iso)),
            "feedback": updated_log.get("feedback", feedback_payload),
        }

    def list_learning_method_question_pack_recommendations(
        self,
        method_code: str,
        limit: int,
        actor: Actor,
    ) -> Dict[str, object]:
        normalized_method_code = self._normalize_learning_method_code(method_code)
        method = self.repository.get_learning_method(normalized_method_code)
        if not method:
            raise not_found("学习方法不存在。")

        normalized_limit = max(1, min(50, int(limit or 10)))
        rows = self.repository.list_learning_method_recommendation_logs(
            actor.user_id,
            normalized_method_code,
            normalized_limit,
        )

        items: List[Dict[str, object]] = []
        for row in rows:
            score_payload = row.get("score", {}) if isinstance(row.get("score"), dict) else {}
            score_items = score_payload.get("items", [])
            if not isinstance(score_items, list):
                score_items = []
            ext_payload = row.get("extJson", {}) if isinstance(row.get("extJson"), dict) else {}
            student_profile_payload = score_payload.get("studentProfile", {})
            if not isinstance(student_profile_payload, dict):
                student_profile_payload = {}
            reason_tags = row.get("reasonTags", []) if isinstance(row.get("reasonTags"), list) else []
            question_ids = row.get("questionIds", []) if isinstance(row.get("questionIds"), list) else []
            feedback_payload = row.get("feedback", {}) if isinstance(row.get("feedback"), dict) else {}
            completed_question_ids = feedback_payload.get("completedQuestionIds", [])
            if not isinstance(completed_question_ids, list):
                completed_question_ids = []
            skipped_question_ids = feedback_payload.get("skippedQuestionIds", [])
            if not isinstance(skipped_question_ids, list):
                skipped_question_ids = []
            practice_strategy = str(ext_payload.get("practiceStrategy", "")).strip().upper()
            recommendation_strategy_code = (
                str(ext_payload.get("recommendationStrategyCode", "")).strip().upper()
                or self._resolve_recommendation_strategy_code(practice_strategy)
            )
            strategy_source = self._normalize_recommendation_strategy_source(
                str(ext_payload.get("strategySource", "")).strip(),
                "DEFAULT",
            )
            profile_fit_values: List[float] = []
            for score_item in score_items:
                if not isinstance(score_item, dict):
                    continue
                score_breakdown = score_item.get("scoreBreakdown", {})
                if not isinstance(score_breakdown, dict):
                    continue
                profile_fit_values.append(float(score_breakdown.get("studentProfileFit", 0.0) or 0.0))
            student_profile_fit_average = (
                round(sum(profile_fit_values) / len(profile_fit_values), 6)
                if profile_fit_values
                else 0.0
            )
            items.append(
                {
                    "recommendationId": str(row.get("recommendationId", "")),
                    "sessionId": str(row.get("sessionId", "")),
                    "questionCount": len(question_ids),
                    "questionIds": [str(item).strip() for item in question_ids if str(item).strip()][:30],
                    "completedQuestionIds": [
                        str(item).strip()
                        for item in completed_question_ids
                        if str(item).strip()
                    ][:30],
                    "skippedQuestionIds": [
                        str(item).strip()
                        for item in skipped_question_ids
                        if str(item).strip()
                    ][:30],
                    "feedbackStatus": str(row.get("feedbackStatus", "PENDING")).strip() or "PENDING",
                    "recommendedAt": str(row.get("recommendedAt", "")),
                    "feedbackAt": str(row.get("feedbackAt", "")),
                    "reasonTags": [str(item).strip() for item in reason_tags if str(item).strip()][:8],
                    "averageScore": float(score_payload.get("averageScore", 0.0) or 0.0),
                    "maxScore": float(score_payload.get("maxScore", 0.0) or 0.0),
                    "minScore": float(score_payload.get("minScore", 0.0) or 0.0),
                    "difficultyPreference": str(ext_payload.get("difficultyPreference", "")).strip().lower(),
                    "practiceStrategy": practice_strategy,
                    "recommendationStrategyCode": recommendation_strategy_code,
                    "recommendationStrategySource": strategy_source,
                    "studentProfileFitAverage": float(student_profile_fit_average),
                    "studentProfile": {
                        "tags": [
                            str(tag).strip()
                            for tag in student_profile_payload.get("tags", [])
                            if str(tag).strip()
                        ][:12] if isinstance(student_profile_payload.get("tags", []), list) else [],
                        "difficultyPreference": str(student_profile_payload.get("difficultyPreference", "")).strip().lower(),
                        "questionTypeWeights": (
                            student_profile_payload.get("questionTypeWeights", {})
                            if isinstance(student_profile_payload.get("questionTypeWeights", {}), dict)
                            else {}
                        ),
                    },
                    "extJson": ext_payload,
                }
            )

        return {
            "items": items,
            "total": len(items),
            "limit": normalized_limit,
        }
