from __future__ import annotations

from app.shared.codecs import dump_json, hash_password, load_json_object
from app.service_shared import *


class InternalCoreServiceMixin:
    def __init__(self, db_path: Union[Path, str]) -> None:
        self.repository = QuestionRepository(db_path)
        self._auth_tokens: Dict[str, Dict[str, object]] = {}
        self._sms_codes: Dict[str, Dict[str, object]] = {}
        self._sms_request_timestamps: Dict[str, List[float]] = {}
        self._password_login_fail_timestamps_by_phone: Dict[str, List[float]] = {}
        self._password_login_fail_timestamps_by_ip: Dict[str, List[float]] = {}
        self._password_login_lock_until_by_phone: Dict[str, float] = {}
        self._password_login_lock_until_by_ip: Dict[str, float] = {}

    def _trim_fail_history(self, history: List[float], now: float) -> List[float]:
        return [stamp for stamp in history if now - stamp < PASSWORD_LOGIN_FAIL_WINDOW_SEC]

    def _password_login_is_locked(self, key: str, lock_map: Dict[str, float], now: float) -> bool:
        if not key:
            return False
        locked_until = float(lock_map.get(key, 0.0))
        if locked_until <= now:
            lock_map.pop(key, None)
            return False
        return True

    def _password_login_rate_limit_enabled(self) -> bool:
        disabled = os.getenv("QB_DISABLE_PASSWORD_LOGIN_RATE_LIMIT", "").strip().lower()
        return disabled not in {"1", "true", "yes"}

    def _assert_password_login_allowed(self, phone: str, client_ip: str) -> None:
        if not self._password_login_rate_limit_enabled():
            return
        now = time.time()
        if self._password_login_is_locked(phone, self._password_login_lock_until_by_phone, now):
            raise forbidden("登录尝试过于频繁，请 10 分钟后重试。")
        if self._password_login_is_locked(client_ip, self._password_login_lock_until_by_ip, now):
            raise forbidden("登录尝试过于频繁，请 10 分钟后重试。")

    def _record_password_login_failure(self, phone: str, client_ip: str) -> None:
        if not self._password_login_rate_limit_enabled():
            return
        now = time.time()
        phone_history = self._trim_fail_history(self._password_login_fail_timestamps_by_phone.get(phone, []), now)
        phone_history.append(now)
        self._password_login_fail_timestamps_by_phone[phone] = phone_history
        if len(phone_history) >= PASSWORD_LOGIN_MAX_FAIL_PER_PHONE:
            self._password_login_lock_until_by_phone[phone] = now + PASSWORD_LOGIN_FAIL_LOCK_SEC
            self._password_login_fail_timestamps_by_phone[phone] = []

        ip_history = self._trim_fail_history(self._password_login_fail_timestamps_by_ip.get(client_ip, []), now)
        ip_history.append(now)
        self._password_login_fail_timestamps_by_ip[client_ip] = ip_history
        if len(ip_history) >= PASSWORD_LOGIN_MAX_FAIL_PER_IP:
            self._password_login_lock_until_by_ip[client_ip] = now + PASSWORD_LOGIN_FAIL_LOCK_SEC
            self._password_login_fail_timestamps_by_ip[client_ip] = []

    def _clear_password_login_failures(self, phone: str) -> None:
        self._password_login_fail_timestamps_by_phone.pop(phone, None)
        self._password_login_lock_until_by_phone.pop(phone, None)

    def _deduplicate_ids(self, values: object, field_name: str) -> List[str]:
        if not isinstance(values, list):
            raise validation_failed(f"{field_name} 必须是数组。")
        seen = set()
        normalized: List[str] = []
        for raw in values:
            value = str(raw).strip()
            if not value or value in seen:
                continue
            seen.add(value)
            normalized.append(value)
        return normalized

    def _judge_answer(self, question: Dict[str, str], normalized_answer: str) -> bool:
        expected = self._normalize_answer(question["type"], question["answer"])
        if question["type"] == "subjective":
            return normalized_answer in expected or expected in normalized_answer
        return normalized_answer == expected

    def _normalize_answer(self, question_type: str, answer: str) -> str:
        text = "".join(answer.upper().split())
        if question_type == "multiple_choice":
            return "".join(sorted(text))
        return text

    def _hash_password(self, password: str) -> str:
        return hash_password(password)

    def _verify_password(self, raw_password: str, stored_password: str) -> bool:
        return self._hash_password(raw_password) == stored_password

    def _verify_sms_code(self, phone: str, purpose: str, code: str) -> None:
        saved = self._sms_codes.get(phone)
        if not saved:
            raise validation_failed("验证码不存在或已失效。")
        if float(saved.get("expireAt", 0.0)) < time.time():
            self._sms_codes.pop(phone, None)
            raise validation_failed("验证码已过期，请重新获取。")
        if str(saved.get("purpose", "")) != purpose:
            raise validation_failed("验证码用途不匹配，请重新获取。")
        if str(saved.get("code", "")) != code:
            raise validation_failed("验证码错误，请重新输入。")
        self._sms_codes.pop(phone, None)

    def _new_user_id(self, role: str) -> str:
        prefix = {
            ROLE_STUDENT: "student",
            ROLE_TEACHER: "teacher",
            ROLE_SUPER_ADMIN: "admin",
        }.get(role, "user")
        return f"{prefix}-{uuid.uuid4().hex[:8]}"

    def _default_permissions_for_role(self, role: str) -> List[str]:
        if role == ROLE_TEACHER:
            return ["question:manage", "paper:manage", "analytics:view", "message:send"]
        return list(self._allowed_permissions_for_role(role))

    def _allowed_permissions_for_role(self, role: str) -> tuple[str, ...]:
        if role == ROLE_SUPER_ADMIN:
            return tuple(MANAGED_PERMISSION_KEYS)
        if role == ROLE_TEACHER:
            return ("question:manage", "paper:manage", "analytics:view", "student:manage", "message:send")
        return ()

    def _upsert_sms_auth_binding(self, user_id: str, phone: str, now: str) -> None:
        existing = self.repository.get_user_auth_by_type_openid("SMS", phone)
        payload = {
            "id": existing["id"] if existing else f"user-auth-sms-{uuid.uuid4().hex[:8]}",
            "userId": user_id,
            "type": "SMS",
            "openid": phone,
            "unionid": "",
            "extJson": self._dump_json({"verified": True}),
            "createTime": existing["createTime"] if existing else now,
            "updateTime": now,
        }
        if existing:
            self.repository.update_user_auth(payload)
        else:
            self.repository.create_user_auth(payload)

    def _resolve_assigned_scope_codes(
        self,
        user_id: str,
        user_ext_json: Optional[Dict[str, object]] = None,
    ) -> Tuple[str, str]:
        managed_user = self._get_managed_user(user_id) if hasattr(self, "_get_managed_user") else None
        managed_exam_category_code = str((managed_user or {}).get("examCategoryCode", "")).strip()
        managed_joint_exam_group_code = str((managed_user or {}).get("jointExamGroupCode", "")).strip()

        ext_json = user_ext_json if isinstance(user_ext_json, dict) else {}
        managed_role = normalize_role(str((managed_user or {}).get("role", "")))
        ext_role = normalize_role(str(ext_json.get("role", "")))
        if managed_role == ROLE_STUDENT or ext_role == ROLE_STUDENT:
            profile_state = self.repository.get_student_profile_state(user_id)
            if profile_state:
                formal_exam_category_code = str(profile_state.get("examCategoryCode", "")).strip()
                formal_joint_exam_group_code = str(profile_state.get("jointExamGroupCode", "")).strip()
                if formal_joint_exam_group_code and not formal_exam_category_code:
                    joint_exam_group = get_joint_exam_group(formal_joint_exam_group_code)
                    if joint_exam_group:
                        formal_exam_category_code = str(joint_exam_group.get("examCategoryCode", "")).strip()
                if formal_exam_category_code or formal_joint_exam_group_code:
                    return formal_exam_category_code, formal_joint_exam_group_code
        ext_exam_category_code = str(ext_json.get("examCategoryCode", "")).strip()
        ext_joint_exam_group_code = str(ext_json.get("jointExamGroupCode", "")).strip()

        joint_exam_group_code = managed_joint_exam_group_code or ext_joint_exam_group_code
        exam_category_code = managed_exam_category_code or ext_exam_category_code
        if joint_exam_group_code and not exam_category_code:
            joint_exam_group = get_joint_exam_group(joint_exam_group_code)
            if joint_exam_group:
                exam_category_code = str(joint_exam_group.get("examCategoryCode", "")).strip()
        return exam_category_code, joint_exam_group_code

    def _build_login_response(self, user: Dict[str, str]) -> Dict[str, object]:
        ext_json = self._load_json_object(str(user["extJson"]))
        role = normalize_role(str(ext_json.get("role", "")))
        if role not in ALL_ROLES:
            raise forbidden("账号角色配置异常，请联系管理员。")
        if user["status"] != "ENABLED":
            raise forbidden("账号待审核或已停用，请联系管理员。")
        assigned_exam_category_code, assigned_joint_group_code = self._resolve_assigned_scope_codes(
            str(user["id"]),
            ext_json,
        )
        token = f"qb_{uuid.uuid4().hex}{uuid.uuid4().hex[:8]}"
        expire_at = time.time() + 12 * 3600
        self._auth_tokens[token] = {
            "userId": user["id"],
            "role": role,
            "assignedExamCategoryCode": assigned_exam_category_code,
            "assignedJointGroupCode": assigned_joint_group_code,
            "expireAt": expire_at,
        }
        return {
            "accessToken": token,
            "tokenType": "Bearer",
            "expireInSec": 12 * 3600,
            "userId": user["id"],
            "role": role,
            "status": user["status"],
            "name": str(ext_json.get("name", "")),
            "assignedExamCategoryCode": assigned_exam_category_code,
            "assignedJointGroupCode": assigned_joint_group_code,
            "assigned_exam_category_code": assigned_exam_category_code,
            "assigned_joint_group_code": assigned_joint_group_code,
        }

    def _paginate_items(self, items: List[object], page: int, size: int) -> Tuple[List[object], int]:
        total = len(items)
        start = (page - 1) * size
        end = start + size
        return items[start:end], total

    def _paginate_questions(self, questions: List[Dict[str, str]], page: int, size: int) -> Tuple[List[Dict[str, str]], int]:
        sliced, total = self._paginate_items(questions, page, size)
        return [self._public_question(question) for question in sliced], total

    def _validate_task_filters(self, filters: Dict[str, str]) -> Dict[str, str]:
        normalized = {
            "type": filters.get("type", "").strip(),
            "status": filters.get("status", "").strip(),
            "questionId": filters.get("questionId", "").strip(),
        }
        if normalized["type"] and normalized["type"] not in TASK_TYPES:
            raise task_validation_failed(f"type 仅支持 {', '.join(TASK_TYPES)}。")
        if normalized["status"] and normalized["status"] not in TASK_STATUSES:
            raise task_validation_failed(f"status 仅支持 {', '.join(TASK_STATUSES)}。")
        return normalized

    def _assert_task_access(self, task: Dict[str, object], actor: Actor) -> None:
        if actor.role == ROLE_SUPER_ADMIN:
            return
        if str(task["userId"]) != actor.user_id:
            raise task_forbidden("当前用户不可查看该任务。")

    def _create_task(self, user_id: str, task_type: str, ext_json: Dict[str, object]) -> Dict[str, object]:
        now = self._now_iso()
        payload = {
            "id": f"task-{uuid.uuid4().hex[:8]}",
            "userId": user_id,
            "type": task_type,
            "status": "QUEUED",
            "progress": 0,
            "extJson": self._dump_json(ext_json),
            "createTime": now,
            "updateTime": now,
        }
        return self.repository.create_task(payload)

    def _advance_task_queue_state(
        self,
        task: Dict[str, object],
        ext_json: Dict[str, object],
        queue: Dict[str, object],
    ) -> None:
        poll_count = int(queue.get("pollCount", 0)) + 1
        queue["pollCount"] = poll_count
        if task["status"] == "QUEUED":
            task["status"] = "RUNNING"
            task["progress"] = 35
            queue["startedAt"] = queue.get("startedAt") or self._now_iso()
            ext_json["resultSummary"] = "任务已入队，正在装载题目上下文。"
            return
        if poll_count < 3:
            task["progress"] = 75
            ext_json["resultSummary"] = "AI 正在生成结果，请继续轮询。"
            return
        self._complete_task(task, ext_json)
        queue["completedAt"] = self._now_iso()

    def _refresh_task(self, task: Dict[str, object], actor: Actor) -> Dict[str, object]:
        self._assert_task_access(task, actor)
        if task["status"] in {"COMPLETED", "FAILED", "CANCELLED"}:
            return task
        ext_json = self._load_json_object(str(task["extJson"]))
        queue = dict(ext_json.get("queue", {}))
        self._advance_task_queue_state(task, ext_json, queue)
        ext_json["queue"] = queue
        task["extJson"] = self._dump_json(ext_json)
        task["updateTime"] = self._now_iso()
        self.repository.update_task(task)
        return task

    def _complete_task(self, task: Dict[str, object], ext_json: Dict[str, object]) -> None:
        task_type = str(task["type"])
        if task_type == "QUESTION_BATCH_PARSE":
            self._complete_question_batch_parse_task(task, ext_json)
            return
        question = self._load_task_question_for_completion(task, ext_json)
        if not question:
            return
        if task_type == "AI_MARKING":
            self._complete_ai_marking_task(task, ext_json, question)
            return
        if task_type == "AI_TUTOR":
            self._complete_ai_tutor_task(task, ext_json, question)
            return
        self._fail_task(task, ext_json, f"不支持的任务类型：{task_type}。")

    def _complete_question_batch_parse_task(
        self,
        task: Dict[str, object],
        ext_json: Dict[str, object],
    ) -> None:
        request_payload = ext_json.get("requestPayload", {})
        if not isinstance(request_payload, dict):
            self._fail_task(task, ext_json, "批量解析任务上下文缺失。")
            return
        blocks = request_payload.get("blocks", [])
        scope = request_payload.get("scope", {})
        semantic_pool = request_payload.get("semanticPool", [])
        if not isinstance(blocks, list):
            blocks = []
        if not isinstance(scope, dict):
            scope = {}
        if not isinstance(semantic_pool, list):
            semantic_pool = []
        result = self._build_question_batch_parse_result(blocks, scope, semantic_pool)
        self._mark_task_completed(
            task,
            ext_json,
            result,
            f"批量题目解析完成，共识别 {int(result.get('valid_count', 0) or 0)} 道题。",
        )

    def _load_task_question_for_completion(
        self,
        task: Dict[str, object],
        ext_json: Dict[str, object],
    ) -> Optional[Dict[str, str]]:
        question_id = str(ext_json.get("questionId", ""))
        question = self.repository.get_question(question_id)
        if question and question["status"] == "PUBLISHED":
            return question
        self._fail_task(task, ext_json, "关联题目不存在或尚未发布。")
        return None

    def _mark_task_completed(
        self,
        task: Dict[str, object],
        ext_json: Dict[str, object],
        result: Dict[str, object],
        result_summary: str,
    ) -> None:
        task["status"] = "COMPLETED"
        task["progress"] = 100
        ext_json["result"] = result
        ext_json["errorMessage"] = ""
        ext_json["resultSummary"] = result_summary

    def _complete_ai_marking_task(
        self,
        task: Dict[str, object],
        ext_json: Dict[str, object],
        question: Dict[str, str],
    ) -> None:
        request_payload = ext_json.get("requestPayload", {})
        answer = str(request_payload.get("answer", ""))
        result = self._persist_ai_marking_result(
            question,
            answer,
            str(task["userId"]),
            str(task["id"]),
            request_payload,
        )
        if str(ext_json.get("source", "")) == "PAPER_SUBMIT":
            self._sync_simulation_attempt_marking(
                question["id"],
                str(task["userId"]),
                str(ext_json.get("paperId", "")),
                str(task["id"]),
                result,
            )
            self._sync_paper_report_ai_marking(
                question["id"],
                str(task["userId"]),
                str(ext_json.get("paperId", "")),
                str(task["id"]),
                result,
            )
        self._mark_task_completed(task, ext_json, result, f"AI 批改完成，总分 {result['totalScore']}。")

    def _sync_simulation_attempt_marking(
        self,
        question_id: str,
        student_user_id: str,
        paper_id: str,
        task_id: str,
        result: Dict[str, object],
    ) -> None:
        if not paper_id:
            return
        record = self.repository.get_student_question_bank(question_id, student_user_id)
        if not record:
            return
        record_ext = self._load_json_object(record["extJson"])
        attempts = record_ext.get("simulationAttempts", {})
        if not isinstance(attempts, dict):
            return
        attempt = attempts.get(paper_id)
        if not isinstance(attempt, dict):
            return
        attempt["isPendingAiMarking"] = False
        attempt["aiMarkingTaskId"] = task_id
        attempt["aiMarkingScore"] = float(result.get("totalScore", 0))
        attempt["aiMarkingCompletedAt"] = self._now_iso()
        attempts[paper_id] = attempt
        record_ext["simulationAttempts"] = attempts
        self._save_student_question_record_bundle(record, record_ext, student_user_id)

    def _sync_paper_report_ai_marking(
        self,
        question_id: str,
        student_user_id: str,
        paper_id: str,
        task_id: str,
        result: Dict[str, object],
    ) -> None:
        if not paper_id:
            return
        reports = self.repository.list_paper_reports_by_student(student_user_id)
        for report in reports:
            if str(report.get("paperId", "")) != paper_id:
                continue
            detail = report.get("reportDetail", {})
            if not isinstance(detail, dict):
                continue
            rows_raw = detail.get("questionResults")
            if not isinstance(rows_raw, list):
                continue
            question_results = self._normalize_question_results(rows_raw)
            matched_row = False
            for row in question_results:
                if str(row.get("questionId", "")) != question_id:
                    continue
                row_task_id = str(row.get("aiMarkingTaskId", "")).strip()
                if row_task_id and row_task_id != task_id:
                    continue
                row["isPendingAiMarking"] = False
                row["score"] = self._paper_ai_marking_awarded_score(float(result.get("totalScore", 0.0)), int(row.get("totalScore", 0)))
                row["aiMarkingTaskId"] = task_id
                matched_row = True
                break
            if not matched_row:
                continue
            pending_task_ids_raw = report.get("pendingSubjectiveTaskIds")
            pending_task_ids = [str(item) for item in pending_task_ids_raw] if isinstance(pending_task_ids_raw, list) else []
            report["pendingSubjectiveTaskIds"] = [item for item in pending_task_ids if item != task_id]
            report["reportDetail"] = self._build_synced_report_detail(question_results)
            report["typeAccuracy"] = list(report["reportDetail"]["typeAccuracy"])
            report["wrongQuestionIds"] = self._derive_wrong_question_ids(question_results)
            report["score"] = sum(int(item.get("score", 0)) for item in question_results)
            report["totalScore"] = sum(int(item.get("totalScore", 0)) for item in question_results)
            report["scoreRate"] = round(float(report["score"]) / float(report["totalScore"]), 4) if int(report["totalScore"]) else 0.0
            report["updateTime"] = self._now_iso()
            self.repository.upsert_paper_report_payload(report)
            break

    def _create_paper_subjective_marking_task(
        self,
        question_id: str,
        paper_id: str,
        student_user_id: str,
        answer: str,
    ) -> Dict[str, object]:
        return self._create_task(
            student_user_id,
            "AI_MARKING",
            {
                "questionId": question_id,
                "paperId": paper_id,
                "source": "PAPER_SUBMIT",
                "requestPayload": {"answer": answer, "answerImageUrl": ""},
                "result": {},
                "resultSummary": "",
                "errorMessage": "",
                "queue": {
                    "queueName": "question-bank-ai",
                    "requestedAt": self._now_iso(),
                    "startedAt": "",
                    "completedAt": "",
                    "pollCount": 0,
                },
            },
        )

    def _complete_ai_tutor_task(
        self,
        task: Dict[str, object],
        ext_json: Dict[str, object],
        question: Dict[str, str],
    ) -> None:
        request_payload = ext_json.get("requestPayload", {})
        prompt = str(request_payload.get("prompt", ""))
        result = self._persist_ai_tutor_result(question, prompt, str(task["userId"]), str(task["id"]))
        self._mark_task_completed(task, ext_json, result, "AI 老师已完成答疑。")

    def _fail_task(self, task: Dict[str, object], ext_json: Dict[str, object], error_message: str) -> None:
        task["status"] = "FAILED"
        task["progress"] = 100
        ext_json["errorMessage"] = error_message
        ext_json["resultSummary"] = "任务执行失败。"

    def _persist_ai_marking_result(
        self,
        question: Dict[str, str],
        student_answer: str,
        student_user_id: str,
        task_id: str,
        request_payload: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        record, record_ext = self._load_student_question_record_bundle(question["id"], student_user_id, create_if_missing=True)
        result = self._build_ai_marking_result(question, student_answer)
        ai_marking = record_ext.get("aiMarking", {})
        request_payload = dict(request_payload or {})
        history = list(ai_marking.get("history", []))
        history.append(
            {
                "taskId": task_id,
                "submittedAt": self._now_iso(),
                "answer": student_answer,
                "result": result,
            }
        )
        record_ext["aiMarking"] = {
            "taskId": task_id,
            "status": "COMPLETED",
            "latestAnswer": student_answer,
            "latestResult": result,
            "history": history,
        }
        self._save_student_question_record_bundle(record, record_ext, student_user_id)
        self._push_message(
            [student_user_id],
            "AI_MARKING",
            "AI批改已完成",
            f"{question['id']} 的主观题批改结果已生成。"
        )
        assignment_id = str(request_payload.get("assignmentId", "")).strip()
        if assignment_id and hasattr(self, "submit_student_exam_task"):
            try:
                self.submit_student_exam_task(
                    assignment_id,
                    {
                        "questionId": str(question.get("id", "")),
                        "score": int(round(float(result.get("totalScore", 0.0)))),
                        "totalScore": 100,
                        "pendingSubjectiveCount": 0,
                        "submittedAt": self._now_iso(),
                    },
                    Actor(role=ROLE_STUDENT, user_id=student_user_id),
                )
            except Exception:
                pass
        return result

    def _persist_ai_tutor_result(
        self,
        question: Dict[str, str],
        prompt: str,
        student_user_id: str,
        task_id: str,
    ) -> Dict[str, object]:
        _, _, profile = self._load_student_profile_bundle(student_user_id)
        ai_quota = self._current_ai_quota(profile)
        record, record_ext = self._load_student_question_record_bundle(question["id"], student_user_id, create_if_missing=True)
        ai_tutor = record_ext.get("aiTutor", {})
        conversations = list(ai_tutor.get("conversations", []))
        reply = self._build_ai_tutor_response(question, prompt)
        conversations.append({"role": "user", "content": prompt, "createTime": self._now_iso(), "taskId": task_id})
        conversations.append({"role": "assistant", "content": reply, "createTime": self._now_iso(), "taskId": task_id})
        record_ext["aiTutor"] = {
            "taskId": task_id,
            "conversations": conversations,
        }
        self._save_student_question_record_bundle(record, record_ext, student_user_id)
        self._push_message(
            [student_user_id],
            "AI_TUTOR",
            "AI老师已回复",
            f"{question['id']} 的答疑内容已更新，可继续追问。"
        )
        return {
            "reply": reply,
            "remainingQuota": int(ai_quota.get("dailyLimit", 20)) - int(ai_quota.get("usedCount", 0)),
            "conversations": conversations,
        }

    def _load_json_object(self, payload: object) -> Dict[str, object]:
        return load_json_object(payload)

    def _parse_iso_date(self, value: str, field_name: str) -> Optional[date]:
        normalized = value.strip()
        if not normalized:
            return None
        try:
            return date.fromisoformat(normalized)
        except ValueError as exc:
            raise validation_failed(f"{field_name} 必须是 YYYY-MM-DD 格式。") from exc

    def _validate_date_filters(self, filters: Dict[str, str]) -> None:
        start_date = self._parse_iso_date(filters.get("startDate", ""), "startDate")
        end_date = self._parse_iso_date(filters.get("endDate", ""), "endDate")
        if start_date and end_date and start_date > end_date:
            raise validation_failed("startDate 不能晚于 endDate。")

    def _format_time_range_label(self, filters: Dict[str, str]) -> str:
        start_date = filters.get("startDate", "").strip()
        end_date = filters.get("endDate", "").strip()
        if start_date and end_date:
            return f"{start_date} ~ {end_date}"
        if start_date:
            return f"{start_date} 之后"
        if end_date:
            return f"{end_date} 之前"
        return "全部时间"

    def _normalize_export_format(
        self,
        export_format: str,
        allowed_formats: set[str],
        label: str,
        default_format: str,
    ) -> str:
        normalized = export_format.strip().lower() or default_format
        if normalized not in allowed_formats:
            raise validation_failed(f"{label} 仅支持 {', '.join(sorted(allowed_formats))} 格式。")
        return normalized

    def _csv_cell(self, value: str) -> str:
        normalized = value.replace('"', '""').replace("\n", " ").strip()
        return f'"{normalized}"'

    def _dump_json(self, payload: object) -> str:
        return dump_json(payload)

    def _to_iso_z(self, value: datetime) -> str:
        normalized = value.astimezone(timezone.utc) if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
        return normalized.isoformat().replace("+00:00", "Z")

    def _now_iso(self) -> str:
        return self._to_iso_z(datetime.now(timezone.utc))
