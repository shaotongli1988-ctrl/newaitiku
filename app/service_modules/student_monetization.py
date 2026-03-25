from __future__ import annotations

from app.service_shared import *

DEFAULT_SUBSCRIPTION_PLAN_CODE = "AI_SCORE_BOOST_30D"
SUBSCRIPTION_STATUS_INACTIVE = "INACTIVE"
SUBSCRIPTION_STATUS_ACTIVE = "ACTIVE"
SUBSCRIPTION_STATUS_EXPIRED = "EXPIRED"
REDEEM_STATUS_UNUSED = "UNUSED"
ORDER_STATUS_CREATED = "CREATED"
ORDER_STATUS_PAID = "PAID"
QUICK_DIAGNOSIS_SESSION_EXT_KEY = "quickDiagnosisSession"
QUICK_DIAGNOSIS_STATUS_STARTED = "STARTED"
QUICK_DIAGNOSIS_STATUS_COMPLETED = "COMPLETED"
STUDENT_PROFILE_STATE_BASE_KEYS = {
    "id",
    "studentUserId",
    "examCategoryCode",
    "jointExamGroupCode",
    "points",
    "title",
    "unlockedTitles",
    "checkInDates",
    "aiQuota",
    "examSession",
    "createTime",
    "updateTime",
}
CONVERSION_OVERVIEW_EVENT_KEYS = {
    "QUICK_DIAGNOSIS_START": "quickDiagnosisStartCount",
    "QUICK_DIAGNOSIS_COMPLETE": "quickDiagnosisCompleteCount",
    "REDEEM_SUBMIT": "redeemSubmitCount",
    "REDEEM_SUCCESS": "redeemSuccessCount",
    "MOCK_ORDER_CREATED": "mockOrderCreatedCount",
    "MOCK_PAYMENT_SUCCESS": "mockPaymentSuccessCount",
    "SUBSCRIPTION_ACTIVATED": "subscriptionActivatedCount",
}


class StudentMonetizationServiceMixin:
    def _parse_iso_datetime_or_none(self, value: str) -> Optional[datetime]:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        try:
            return datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _ensure_student_subscription_row(self, student_user_id: str) -> Dict[str, object]:
        existing = self.repository.get_student_subscription(student_user_id)
        if existing:
            return existing
        now_iso = self._now_iso()
        return self.repository.upsert_student_subscription(
            {
                "id": f"student-subscription-{student_user_id}",
                "studentUserId": student_user_id,
                "currentPlanCode": "",
                "status": SUBSCRIPTION_STATUS_INACTIVE,
                "startTime": "",
                "endTime": "",
                "lastActivatedAt": "",
                "lastExpiredAt": "",
                "sourceType": "",
                "sourceOrderId": "",
                "sourceRedeemCode": "",
                "totalActivatedDays": 0,
                "extJson": {},
                "createTime": now_iso,
                "updateTime": now_iso,
            }
        )

    def _refresh_subscription_expired_status(self, row: Dict[str, object]) -> Dict[str, object]:
        status = str(row.get("status", "")).strip().upper()
        if status != SUBSCRIPTION_STATUS_ACTIVE:
            return row
        end_time = str(row.get("endTime", "")).strip()
        end_dt = self._parse_iso_datetime_or_none(end_time)
        if not end_dt:
            return row
        now_dt = datetime.now(timezone.utc)
        if end_dt > now_dt:
            return row
        now_iso = self._now_iso()
        return self.repository.upsert_student_subscription(
            {
                **row,
                "status": SUBSCRIPTION_STATUS_EXPIRED,
                "lastExpiredAt": now_iso,
                "updateTime": now_iso,
            }
        )

    def _public_subscription_plan(self, row: Dict[str, object]) -> Dict[str, object]:
        return {
            "planCode": str(row.get("planCode", "")).strip(),
            "planName": str(row.get("planName", "")).strip(),
            "durationDays": int(row.get("durationDays", 0) or 0),
            "listPriceFen": int(row.get("listPriceFen", 0) or 0),
            "salePriceFen": int(row.get("salePriceFen", 0) or 0),
            "status": str(row.get("status", "")).strip(),
        }

    def _public_subscription_status(self, row: Dict[str, object]) -> Dict[str, object]:
        status = str(row.get("status", SUBSCRIPTION_STATUS_INACTIVE)).strip().upper() or SUBSCRIPTION_STATUS_INACTIVE
        end_time = str(row.get("endTime", "")).strip()
        end_dt = self._parse_iso_datetime_or_none(end_time)
        now_dt = datetime.now(timezone.utc)
        is_active = status == SUBSCRIPTION_STATUS_ACTIVE and bool(end_dt and end_dt > now_dt)
        return {
            "planCode": str(row.get("currentPlanCode", "")).strip(),
            "status": status,
            "subscriptionActive": is_active,
            "startTime": str(row.get("startTime", "")).strip(),
            "endTime": end_time,
            "lastActivatedAt": str(row.get("lastActivatedAt", "")).strip(),
            "lastExpiredAt": str(row.get("lastExpiredAt", "")).strip(),
            "totalActivatedDays": int(row.get("totalActivatedDays", 0) or 0),
            "sourceType": str(row.get("sourceType", "")).strip(),
        }

    def _activate_student_subscription(
        self,
        student_user_id: str,
        plan_code: str,
        source_type: str,
        source_order_id: str = "",
        source_redeem_code: str = "",
    ) -> Dict[str, object]:
        normalized_plan_code = str(plan_code or "").strip().upper() or DEFAULT_SUBSCRIPTION_PLAN_CODE
        plan = self.repository.get_subscription_plan(normalized_plan_code)
        if not plan:
            raise validation_failed("订阅套餐不存在。")
        if str(plan.get("status", "")).strip().upper() != "ACTIVE":
            raise validation_failed("订阅套餐当前不可用。")

        duration_days = max(1, int(plan.get("durationDays", 30) or 30))
        now_dt = datetime.now(timezone.utc)
        now_iso = self._now_iso()
        current = self._refresh_subscription_expired_status(self._ensure_student_subscription_row(student_user_id))

        current_status = str(current.get("status", SUBSCRIPTION_STATUS_INACTIVE)).strip().upper()
        current_end_dt = self._parse_iso_datetime_or_none(str(current.get("endTime", "")).strip())
        should_extend = current_status == SUBSCRIPTION_STATUS_ACTIVE and bool(current_end_dt and current_end_dt > now_dt)

        start_dt = current_end_dt if should_extend and current_end_dt else now_dt
        next_end_iso = self._to_iso_z(start_dt + timedelta(days=duration_days))
        next_start_time = str(current.get("startTime", "")).strip() if should_extend else now_iso

        updated = self.repository.upsert_student_subscription(
            {
                **current,
                "studentUserId": student_user_id,
                "currentPlanCode": normalized_plan_code,
                "status": SUBSCRIPTION_STATUS_ACTIVE,
                "startTime": next_start_time,
                "endTime": next_end_iso,
                "lastActivatedAt": now_iso,
                "sourceType": str(source_type or "").strip().upper(),
                "sourceOrderId": str(source_order_id or "").strip(),
                "sourceRedeemCode": str(source_redeem_code or "").strip().upper(),
                "totalActivatedDays": int(current.get("totalActivatedDays", 0) or 0) + duration_days,
                "updateTime": now_iso,
            }
        )
        self.repository.create_conversion_event_log(
            {
                "id": f"conversion-event-{uuid.uuid4().hex[:12]}",
                "studentUserId": student_user_id,
                "eventType": "SUBSCRIPTION_ACTIVATED",
                "eventTime": now_iso,
                "eventDate": now_iso[:10],
                "planCode": normalized_plan_code,
                "orderId": str(source_order_id or "").strip(),
                "redeemCode": str(source_redeem_code or "").strip().upper(),
                "channelCode": "SUBSCRIPTION",
                "extJson": {
                    "sourceType": str(source_type or "").strip().upper(),
                    "durationDays": duration_days,
                    "isExtend": should_extend,
                },
                "createTime": now_iso,
                "updateTime": now_iso,
            }
        )
        return updated

    def _normalize_quick_diagnosis_answer(self, answer: object) -> str:
        normalized = str(answer or "").strip().upper()
        normalized = re.sub(r"\s+", "", normalized)
        alnum_only = re.sub(r"[^A-Z0-9]", "", normalized)
        if not alnum_only:
            return normalized
        if re.fullmatch(r"[A-Z]+", alnum_only):
            deduplicated = "".join(dict.fromkeys(alnum_only))
            return "".join(sorted(deduplicated))
        return alnum_only

    def _load_student_profile_state_ext_json(self, student_user_id: str) -> Tuple[Dict[str, object], Dict[str, object]]:
        state = self.repository.get_student_profile_state(student_user_id) or {}
        ext_json = state.get("extJson", {})
        if not isinstance(ext_json, dict):
            ext_json = {}
        if not ext_json and isinstance(state, dict):
            ext_json = {
                key: value
                for key, value in state.items()
                if key not in STUDENT_PROFILE_STATE_BASE_KEYS
            }
        return state, ext_json

    def _save_quick_diagnosis_session_state(
        self,
        student_user_id: str,
        session_payload: Dict[str, object],
        now_iso: str,
    ) -> None:
        state, ext_json = self._load_student_profile_state_ext_json(student_user_id)
        next_ext_json = dict(ext_json)
        next_ext_json[QUICK_DIAGNOSIS_SESSION_EXT_KEY] = session_payload
        payload = {
            **state,
            "studentUserId": student_user_id,
            "extJson": next_ext_json,
            "updateTime": now_iso,
        }
        if not str(payload.get("createTime", "")).strip():
            payload["createTime"] = now_iso
        self.repository.upsert_student_profile_state(payload)

    def _build_quick_diagnosis_recommendation(self, accuracy: float) -> Dict[str, str]:
        if accuracy >= 0.8:
            return {
                "level": "HIGH",
                "title": "基础较稳，建议直接进入提分强化",
                "nextAction": "优先使用 AI 提分订阅，针对薄弱章节点做高频训练。",
            }
        if accuracy >= 0.5:
            return {
                "level": "MEDIUM",
                "title": "有提升空间，建议先补关键知识点",
                "nextAction": "先完成今日诊断建议，再使用订阅权益进行专项练习。",
            }
        return {
            "level": "LOW",
            "title": "基础待夯实，建议尽快开启系统训练",
            "nextAction": "建议立即开通提分权益，按系统推荐路径完成首周任务。",
        }

    def start_student_quick_diagnosis(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        _, _, profile = self._load_student_profile_bundle(actor.user_id)
        self._assert_student_profile_complete(profile)
        now_dt = datetime.now(timezone.utc)
        now_iso = self._to_iso_z(now_dt)

        question_count = int(payload.get("questionCount", 5) or 5)
        question_count = min(5, max(3, question_count))
        subject_code = str(payload.get("subjectCode", "")).strip()
        source_type = str(payload.get("sourceType", "ONBOARDING")).strip().upper() or "ONBOARDING"

        filters = {
            "knowledgeId": "",
            "subjectId": "",
            "chapter": "",
            "type": "",
            "difficulty": "",
            "keyword": "",
            "examCategoryCode": str(profile.get("examCategoryCode", "")).strip(),
            "jointExamGroupCode": str(profile.get("jointExamGroupCode", "")).strip(),
            "subjectCode": subject_code,
        }
        rows = self.repository.list_visible_published_questions(filters, actor.role, actor.user_id)
        objective_rows = [
            row
            for row in rows
            if str(row.get("type", "")).strip() in {"single_choice", "multiple_choice", "judge"}
            and str(row.get("answer", "")).strip()
        ]
        if len(objective_rows) < question_count:
            raise failed_dependency("当前可用于快诊的题目不足，请稍后重试。")

        selected_question_ids: List[str] = []
        seen_question_ids: set[str] = set()
        for row in objective_rows:
            question_id = str(row.get("id", "")).strip()
            if not question_id or question_id in seen_question_ids:
                continue
            seen_question_ids.add(question_id)
            selected_question_ids.append(question_id)
            if len(selected_question_ids) >= question_count:
                break
        if len(selected_question_ids) < question_count:
            raise failed_dependency("当前可用于快诊的题目不足，请稍后重试。")

        session_id = f"quick-diag-{uuid.uuid4().hex[:12]}"
        expires_at = self._to_iso_z(now_dt + timedelta(minutes=30))
        session_payload: Dict[str, object] = {
            "sessionId": session_id,
            "status": QUICK_DIAGNOSIS_STATUS_STARTED,
            "questionIds": selected_question_ids,
            "questionCount": question_count,
            "subjectCode": subject_code,
            "sourceType": source_type,
            "startedAt": now_iso,
            "submittedAt": "",
            "expiresAt": expires_at,
            "answerCount": 0,
            "correctCount": 0,
            "accuracy": 0.0,
            "elapsedSec": 0,
            "result": {},
        }
        self._save_quick_diagnosis_session_state(actor.user_id, session_payload, now_iso)
        self.repository.create_conversion_event_log(
            {
                "id": f"conversion-event-{uuid.uuid4().hex[:12]}",
                "studentUserId": actor.user_id,
                "eventType": "QUICK_DIAGNOSIS_START",
                "eventTime": now_iso,
                "eventDate": now_iso[:10],
                "sessionId": session_id,
                "channelCode": "DIAGNOSIS",
                "extJson": {
                    "questionCount": question_count,
                    "subjectCode": subject_code,
                    "sourceType": source_type,
                },
                "createTime": now_iso,
                "updateTime": now_iso,
            }
        )
        return {
            "sessionId": session_id,
            "status": QUICK_DIAGNOSIS_STATUS_STARTED,
            "questionIds": selected_question_ids,
            "questionCount": question_count,
            "subjectCode": subject_code,
            "startedAt": now_iso,
            "expiresAt": expires_at,
        }

    def submit_student_quick_diagnosis(self, session_id: str, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        normalized_session_id = str(session_id or "").strip()
        if not normalized_session_id:
            raise validation_failed("sessionId 不能为空。")
        now_iso = self._now_iso()
        _, _, profile = self._load_student_profile_bundle(actor.user_id)
        self._assert_student_profile_complete(profile)
        _, ext_json = self._load_student_profile_state_ext_json(actor.user_id)
        session_payload = ext_json.get(QUICK_DIAGNOSIS_SESSION_EXT_KEY, {})
        if not isinstance(session_payload, dict):
            session_payload = {}
        if str(session_payload.get("sessionId", "")).strip() != normalized_session_id:
            raise not_found("快诊会话不存在。")

        session_status = str(session_payload.get("status", "")).strip().upper()
        if session_status == QUICK_DIAGNOSIS_STATUS_COMPLETED:
            result = session_payload.get("result", {})
            if not isinstance(result, dict):
                result = {}
            return {
                "idempotent": True,
                "sessionId": normalized_session_id,
                "status": QUICK_DIAGNOSIS_STATUS_COMPLETED,
                "answeredCount": int(session_payload.get("answerCount", 0) or 0),
                "correctCount": int(session_payload.get("correctCount", 0) or 0),
                "accuracy": float(session_payload.get("accuracy", 0.0) or 0.0),
                "elapsedSec": int(session_payload.get("elapsedSec", 0) or 0),
                "submittedAt": str(session_payload.get("submittedAt", "")).strip(),
                "result": result,
            }

        expires_at = str(session_payload.get("expiresAt", "")).strip()
        expires_dt = self._parse_iso_datetime_or_none(expires_at)
        if expires_dt and expires_dt <= datetime.now(timezone.utc):
            raise validation_failed("快诊会话已过期，请重新开始。")

        question_ids = [
            str(item).strip()
            for item in (session_payload.get("questionIds", []) if isinstance(session_payload.get("questionIds", []), list) else [])
            if str(item).strip()
        ]
        if not question_ids:
            raise validation_failed("快诊会话题目为空，请重新开始。")
        question_rows = self.repository.list_questions_by_ids(question_ids)
        question_map = {str(row.get("id", "")).strip(): row for row in question_rows if str(row.get("id", "")).strip()}

        answer_rows = payload.get("answers", [])
        if not isinstance(answer_rows, list) or not answer_rows:
            raise validation_failed("answers 不能为空。")

        merged_answers: Dict[str, Dict[str, object]] = {}
        for row in answer_rows:
            if not isinstance(row, dict):
                continue
            question_id = str(row.get("questionId", "")).strip()
            if not question_id or question_id not in question_map:
                continue
            merged_answers[question_id] = {
                "questionId": question_id,
                "answer": str(row.get("answer", "")).strip(),
                "elapsedSec": max(0, int(row.get("elapsedSec", 0) or 0)),
            }
        if not merged_answers:
            raise validation_failed("提交答案与快诊题目不匹配。")

        submitted_items: List[Dict[str, object]] = []
        correct_count = 0
        elapsed_sec = 0
        for question_id in question_ids:
            submitted = merged_answers.get(question_id)
            if not isinstance(submitted, dict):
                continue
            question = question_map.get(question_id, {})
            expected_answer = self._normalize_quick_diagnosis_answer(question.get("answer", ""))
            actual_answer = self._normalize_quick_diagnosis_answer(submitted.get("answer", ""))
            is_correct = bool(expected_answer and actual_answer and expected_answer == actual_answer)
            if is_correct:
                correct_count += 1
            elapsed_sec += max(0, int(submitted.get("elapsedSec", 0) or 0))
            submitted_items.append(
                {
                    "questionId": question_id,
                    "isCorrect": is_correct,
                    "elapsedSec": max(0, int(submitted.get("elapsedSec", 0) or 0)),
                }
            )
        answered_count = len(submitted_items)
        if answered_count <= 0:
            raise validation_failed("请至少提交 1 道快诊题答案。")
        accuracy = round((correct_count / answered_count), 4) if answered_count > 0 else 0.0
        recommendation = self._build_quick_diagnosis_recommendation(accuracy)

        completed_payload = {
            **session_payload,
            "status": QUICK_DIAGNOSIS_STATUS_COMPLETED,
            "submittedAt": now_iso,
            "answerCount": answered_count,
            "correctCount": correct_count,
            "accuracy": accuracy,
            "elapsedSec": elapsed_sec,
            "result": {
                "recommendation": recommendation,
                "submittedItems": submitted_items,
            },
        }
        self._save_quick_diagnosis_session_state(actor.user_id, completed_payload, now_iso)

        profile_state = self.repository.get_student_profile_state(actor.user_id) or {}
        exam_session = profile_state.get("examSession", {})
        if not isinstance(exam_session, dict):
            exam_session = {}
        self.repository.set_student_profile_exam_session(
            actor.user_id,
            {
                "answeredCount": max(int(exam_session.get("answeredCount", 0) or 0), answered_count),
                "elapsedSec": max(int(exam_session.get("elapsedSec", 0) or 0), elapsed_sec),
                "updateTime": now_iso,
            },
            now_iso,
        )
        # Keep diagnosis session snapshot in profile extJson after exam session hot-state update.
        self._save_quick_diagnosis_session_state(actor.user_id, completed_payload, now_iso)
        source_type = str(payload.get("sourceType", "")).strip().upper() or str(session_payload.get("sourceType", "")).strip().upper()
        self.repository.create_conversion_event_log(
            {
                "id": f"conversion-event-{uuid.uuid4().hex[:12]}",
                "studentUserId": actor.user_id,
                "eventType": "QUICK_DIAGNOSIS_COMPLETE",
                "eventTime": now_iso,
                "eventDate": now_iso[:10],
                "sessionId": normalized_session_id,
                "channelCode": "DIAGNOSIS",
                "extJson": {
                    "answeredCount": answered_count,
                    "correctCount": correct_count,
                    "accuracy": accuracy,
                    "sourceType": source_type,
                },
                "createTime": now_iso,
                "updateTime": now_iso,
            }
        )
        return {
            "idempotent": False,
            "sessionId": normalized_session_id,
            "status": QUICK_DIAGNOSIS_STATUS_COMPLETED,
            "answeredCount": answered_count,
            "correctCount": correct_count,
            "accuracy": accuracy,
            "elapsedSec": elapsed_sec,
            "submittedAt": now_iso,
            "result": {
                "recommendation": recommendation,
                "submittedItems": submitted_items,
            },
        }

    def list_student_subscription_plans(self, actor: Actor) -> List[Dict[str, object]]:
        _ = actor
        plans = self.repository.list_subscription_plans("ACTIVE")
        return [self._public_subscription_plan(plan) for plan in plans]

    def get_student_subscription_status(self, actor: Actor) -> Dict[str, object]:
        subscription = self._refresh_subscription_expired_status(self._ensure_student_subscription_row(actor.user_id))
        active_plan = None
        current_plan_code = str(subscription.get("currentPlanCode", "")).strip()
        if current_plan_code:
            plan = self.repository.get_subscription_plan(current_plan_code)
            if plan:
                active_plan = self._public_subscription_plan(plan)
        public_subscription = self._public_subscription_status(subscription)
        return {
            "subscription": public_subscription,
            "activePlan": active_plan,
            "subscriptionActive": bool(public_subscription.get("subscriptionActive", False)),
        }

    def redeem_student_subscription(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        redeem_code = str(payload.get("code", "")).strip().upper()
        if not redeem_code:
            raise validation_failed("兑换码不能为空。")
        now_iso = self._now_iso()
        self.repository.create_conversion_event_log(
            {
                "id": f"conversion-event-{uuid.uuid4().hex[:12]}",
                "studentUserId": actor.user_id,
                "eventType": "REDEEM_SUBMIT",
                "eventTime": now_iso,
                "eventDate": now_iso[:10],
                "redeemCode": redeem_code,
                "channelCode": "REDEEM",
                "extJson": {
                    "requestId": str(payload.get("requestId", "")).strip(),
                },
                "createTime": now_iso,
                "updateTime": now_iso,
            }
        )
        if self.repository.has_used_redeem_code_by_user(actor.user_id):
            raise validation_failed("每个账号仅可兑换一次拉新体验码。")

        row = self.repository.get_redeem_code(redeem_code)
        if not row:
            raise validation_failed("兑换码不存在。")
        if str(row.get("status", "")).strip().upper() != REDEEM_STATUS_UNUSED:
            raise validation_failed("兑换码已使用或不可用。")
        expires_at = str(row.get("expiresAt", "")).strip()
        expires_dt = self._parse_iso_datetime_or_none(expires_at)
        if expires_dt and expires_dt <= datetime.now(timezone.utc):
            raise validation_failed("兑换码已过期。")

        consumed = self.repository.consume_redeem_code(
            redeem_code,
            actor.user_id,
            now_iso,
            now_iso,
            "",
        )
        if not consumed:
            raise validation_failed("兑换码已使用或不可用。")

        plan_code = str(row.get("planCode", "")).strip().upper() or DEFAULT_SUBSCRIPTION_PLAN_CODE
        subscription = self._activate_student_subscription(
            actor.user_id,
            plan_code,
            source_type="REDEEM_CODE",
            source_redeem_code=redeem_code,
        )
        self.repository.create_conversion_event_log(
            {
                "id": f"conversion-event-{uuid.uuid4().hex[:12]}",
                "studentUserId": actor.user_id,
                "eventType": "REDEEM_SUCCESS",
                "eventTime": now_iso,
                "eventDate": now_iso[:10],
                "planCode": plan_code,
                "redeemCode": redeem_code,
                "channelCode": "REDEEM",
                "extJson": {},
                "createTime": now_iso,
                "updateTime": now_iso,
            }
        )
        public_subscription = self._public_subscription_status(subscription)
        return {
            "redeemCode": redeem_code,
            "subscription": public_subscription,
            "subscriptionActive": bool(public_subscription.get("subscriptionActive", False)),
        }

    def _public_subscription_order(self, row: Dict[str, object]) -> Dict[str, object]:
        return {
            "orderId": str(row.get("id", "")).strip(),
            "orderNo": str(row.get("orderNo", "")).strip(),
            "planCode": str(row.get("planCode", "")).strip(),
            "amountFen": int(row.get("amountFen", 0) or 0),
            "channel": str(row.get("channel", "")).strip(),
            "status": str(row.get("status", "")).strip(),
            "paidAt": str(row.get("paidAt", "")).strip(),
            "createTime": str(row.get("createTime", "")).strip(),
        }

    def create_student_subscription_mock_order(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        plan_code = str(payload.get("planCode", "")).strip().upper() or DEFAULT_SUBSCRIPTION_PLAN_CODE
        plan = self.repository.get_subscription_plan(plan_code)
        if not plan:
            raise validation_failed("订阅套餐不存在。")
        if str(plan.get("status", "")).strip().upper() != "ACTIVE":
            raise validation_failed("订阅套餐当前不可用。")

        now_iso = self._now_iso()
        order_id = f"subscription-order-{uuid.uuid4().hex[:12]}"
        order_no = f"MOCK{uuid.uuid4().hex[:16].upper()}"
        order = self.repository.create_subscription_order(
            {
                "id": order_id,
                "orderNo": order_no,
                "studentUserId": actor.user_id,
                "planCode": plan_code,
                "amountFen": int(plan.get("salePriceFen", 0) or 0),
                "channel": "MOCK",
                "status": ORDER_STATUS_CREATED,
                "paidAt": "",
                "closedAt": "",
                "extJson": {
                    "sourceType": str(payload.get("sourceType", "")).strip().upper(),
                    "sessionId": str(payload.get("sessionId", "")).strip(),
                },
                "createTime": now_iso,
                "updateTime": now_iso,
            }
        )
        self.repository.create_conversion_event_log(
            {
                "id": f"conversion-event-{uuid.uuid4().hex[:12]}",
                "studentUserId": actor.user_id,
                "eventType": "MOCK_ORDER_CREATED",
                "eventTime": now_iso,
                "eventDate": now_iso[:10],
                "planCode": plan_code,
                "orderId": order_id,
                "channelCode": "MOCK",
                "extJson": {},
                "createTime": now_iso,
                "updateTime": now_iso,
            }
        )
        return {
            "order": self._public_subscription_order(order),
            "plan": self._public_subscription_plan(plan),
        }

    def confirm_student_subscription_mock_order(
        self,
        order_id: str,
        payload: Dict[str, object],
        actor: Actor,
    ) -> Dict[str, object]:
        normalized_order_id = str(order_id or "").strip()
        if not normalized_order_id:
            raise validation_failed("orderId 不能为空。")
        order = self.repository.get_subscription_order(normalized_order_id)
        if not order:
            raise not_found("订单不存在。")
        if str(order.get("studentUserId", "")).strip() != actor.user_id:
            raise forbidden("当前用户不可操作该订单。")

        transaction_no = str(payload.get("transactionNo", "")).strip()
        if not transaction_no:
            raise validation_failed("transactionNo 不能为空。")
        existing_transaction = self.repository.get_payment_transaction_mock_by_transaction_no(transaction_no)
        if existing_transaction:
            if str(existing_transaction.get("orderId", "")).strip() != normalized_order_id:
                raise validation_failed("transactionNo 已被其他订单使用。")
            current_order = self.repository.get_subscription_order(normalized_order_id) or order
            subscription = self._refresh_subscription_expired_status(self._ensure_student_subscription_row(actor.user_id))
            return {
                "idempotent": True,
                "transactionNo": transaction_no,
                "order": self._public_subscription_order(current_order),
                "subscription": self._public_subscription_status(subscription),
            }

        paid_at = str(payload.get("paidAt", "")).strip() or self._now_iso()
        now_iso = self._now_iso()
        self.repository.create_payment_transaction_mock(
            {
                "id": f"mock-transaction-{uuid.uuid4().hex[:12]}",
                "orderId": normalized_order_id,
                "transactionNo": transaction_no,
                "requestId": str(payload.get("requestId", "")).strip(),
                "status": "SUCCESS",
                "payloadJson": {"paidAt": paid_at},
                "createTime": now_iso,
                "updateTime": now_iso,
            }
        )

        order_status = str(order.get("status", "")).strip().upper()
        if order_status != ORDER_STATUS_PAID:
            order_ext = order.get("extJson", {})
            if not isinstance(order_ext, dict):
                order_ext = {}
            order_ext["mockPaidAt"] = paid_at
            order_ext["mockTransactionNo"] = transaction_no
            order = self.repository.update_subscription_order(
                {
                    **order,
                    "status": ORDER_STATUS_PAID,
                    "paidAt": paid_at,
                    "updateTime": now_iso,
                    "extJson": order_ext,
                }
            )
            self.repository.create_conversion_event_log(
                {
                    "id": f"conversion-event-{uuid.uuid4().hex[:12]}",
                    "studentUserId": actor.user_id,
                    "eventType": "MOCK_PAYMENT_SUCCESS",
                    "eventTime": now_iso,
                    "eventDate": now_iso[:10],
                    "planCode": str(order.get("planCode", "")).strip().upper(),
                    "orderId": normalized_order_id,
                    "channelCode": "MOCK",
                    "extJson": {"transactionNo": transaction_no},
                    "createTime": now_iso,
                    "updateTime": now_iso,
                }
            )

        plan_code = str(order.get("planCode", "")).strip().upper() or DEFAULT_SUBSCRIPTION_PLAN_CODE
        subscription = self._activate_student_subscription(
            actor.user_id,
            plan_code,
            source_type="MOCK_PAYMENT",
            source_order_id=normalized_order_id,
        )
        return {
            "idempotent": False,
            "transactionNo": transaction_no,
            "order": self._public_subscription_order(order),
            "subscription": self._public_subscription_status(subscription),
        }

    def _public_admin_redeem_code_batch(
        self,
        row: Dict[str, object],
        usage_summary: Optional[Dict[str, int]] = None,
    ) -> Dict[str, object]:
        summary = usage_summary if isinstance(usage_summary, dict) else {}
        total_count = int(summary.get("totalCodes", row.get("totalCount", 0)) or 0)
        used_count = int(summary.get("usedCodes", row.get("usedCount", 0)) or 0)
        unused_count = int(summary.get("unusedCodes", max(0, total_count - used_count)) or 0)
        if total_count <= 0 and used_count > 0:
            total_count = used_count + max(unused_count, 0)
        usage_rate = round((used_count / total_count), 4) if total_count > 0 else 0.0
        return {
            "id": str(row.get("id", "")).strip(),
            "batchCode": str(row.get("batchCode", "")).strip(),
            "batchName": str(row.get("batchName", "")).strip(),
            "channelCode": str(row.get("channelCode", "")).strip(),
            "planCode": str(row.get("planCode", "")).strip(),
            "totalCount": total_count,
            "usedCount": max(0, used_count),
            "unusedCount": max(0, unused_count),
            "usageRate": usage_rate,
            "expiresAt": str(row.get("expiresAt", "")).strip(),
            "status": str(row.get("status", "")).strip(),
            "createdByUserId": str(row.get("createdByUserId", "")).strip(),
            "createTime": str(row.get("createTime", "")).strip(),
            "updateTime": str(row.get("updateTime", "")).strip(),
        }

    def _generate_redeem_codes(self, code_prefix: str, total_count: int) -> List[str]:
        normalized_prefix = re.sub(r"[^A-Z0-9]", "", str(code_prefix or "").strip().upper())[:16] or "RC"
        generated_codes: List[str] = []
        generated_set: set[str] = set()
        max_attempts = max(total_count * 20, 100)
        attempts = 0
        while len(generated_codes) < total_count and attempts < max_attempts:
            attempts += 1
            candidate = f"{normalized_prefix}-{uuid.uuid4().hex[:10].upper()}"
            if candidate in generated_set:
                continue
            if self.repository.get_redeem_code(candidate):
                continue
            generated_set.add(candidate)
            generated_codes.append(candidate)
        if len(generated_codes) != total_count:
            raise failed_dependency("兑换码生成失败，请重试。")
        return generated_codes

    def create_admin_redeem_code_batch(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        plan_code = str(payload.get("planCode", "")).strip().upper() or DEFAULT_SUBSCRIPTION_PLAN_CODE
        plan = self.repository.get_subscription_plan(plan_code)
        if not plan:
            raise validation_failed("订阅套餐不存在。")
        if str(plan.get("status", "")).strip().upper() != "ACTIVE":
            raise validation_failed("订阅套餐当前不可用。")

        batch_name = str(payload.get("batchName", "")).strip()
        if not batch_name:
            raise validation_failed("batchName 不能为空。")
        total_count = max(1, int(payload.get("totalCount", 1) or 1))
        if total_count > 5000:
            raise validation_failed("totalCount 不能超过 5000。")

        now_dt = datetime.now(timezone.utc)
        now_iso = self._to_iso_z(now_dt)
        expires_at = str(payload.get("expiresAt", "")).strip()
        expires_dt = self._parse_iso_datetime_or_none(expires_at) if expires_at else (now_dt + timedelta(days=30))
        if not expires_dt:
            raise validation_failed("expiresAt 格式非法。")
        if expires_dt <= now_dt:
            raise validation_failed("expiresAt 必须晚于当前时间。")
        normalized_expires_at = self._to_iso_z(expires_dt)

        batch_id = f"redeem-batch-{uuid.uuid4().hex[:12]}"
        batch_code = str(payload.get("batchCode", "")).strip().upper() or f"BATCH-{uuid.uuid4().hex[:8].upper()}"
        channel_code = str(payload.get("channelCode", "")).strip().upper() or "MANUAL"
        code_prefix = str(payload.get("codePrefix", "")).strip()

        batch = self.repository.create_redeem_code_batch(
            {
                "id": batch_id,
                "batchCode": batch_code,
                "batchName": batch_name,
                "channelCode": channel_code,
                "planCode": plan_code,
                "totalCount": total_count,
                "usedCount": 0,
                "expiresAt": normalized_expires_at,
                "status": "ACTIVE",
                "createdByUserId": actor.user_id,
                "extJson": {
                    "operatorUserId": actor.user_id,
                    "codePrefix": code_prefix,
                },
                "createTime": now_iso,
                "updateTime": now_iso,
            }
        )

        redeem_codes = self._generate_redeem_codes(code_prefix or batch_code, total_count)
        for code in redeem_codes:
            self.repository.create_redeem_code(
                {
                    "id": f"redeem-code-{uuid.uuid4().hex[:12]}",
                    "batchId": batch_id,
                    "code": code,
                    "planCode": plan_code,
                    "status": REDEEM_STATUS_UNUSED,
                    "expiresAt": normalized_expires_at,
                    "usedByUserId": "",
                    "usedAt": "",
                    "sourceOrderId": "",
                    "extJson": {"batchCode": batch_code, "channelCode": channel_code},
                    "createTime": now_iso,
                    "updateTime": now_iso,
                }
            )

        usage_summary = self.repository.get_redeem_code_batch_usage_summary([batch_id]).get(batch_id, {})
        return {
            "batch": self._public_admin_redeem_code_batch(batch, usage_summary),
            "codes": redeem_codes,
        }

    def list_admin_redeem_code_batches(
        self,
        filters: Dict[str, str],
        page: int,
        size: int,
        actor: Actor,
    ) -> Tuple[List[Dict[str, object]], int]:
        _ = actor
        status = str(filters.get("status", "")).strip().upper()
        keyword = str(filters.get("keyword", "")).strip()
        rows, total = self.repository.list_redeem_code_batches_paginated(status, keyword, page, size)
        batch_ids = [str(item.get("id", "")).strip() for item in rows if str(item.get("id", "")).strip()]
        usage_summary = self.repository.get_redeem_code_batch_usage_summary(batch_ids)
        items = [
            self._public_admin_redeem_code_batch(
                row,
                usage_summary.get(str(row.get("id", "")).strip(), {}),
            )
            for row in rows
        ]
        return items, total

    def get_admin_conversion_overview(self, filters: Dict[str, str], actor: Actor) -> Dict[str, object]:
        _ = actor
        end_date = str(filters.get("endDate", "")).strip() or datetime.now(timezone.utc).date().isoformat()
        start_date = str(filters.get("startDate", "")).strip()
        if not start_date:
            start_date = (datetime.now(timezone.utc).date() - timedelta(days=29)).isoformat()
        try:
            start_day = date.fromisoformat(start_date)
            end_day = date.fromisoformat(end_date)
        except ValueError:
            raise validation_failed("startDate/endDate 格式非法，应为 YYYY-MM-DD。")
        if start_day > end_day:
            raise validation_failed("startDate 不能晚于 endDate。")

        event_counter_rows = self.repository.aggregate_conversion_event_counts(start_day.isoformat(), end_day.isoformat())
        daily_rows = self.repository.aggregate_conversion_event_daily_counts(start_day.isoformat(), end_day.isoformat())

        event_count_map: Dict[str, int] = {}
        for row in event_counter_rows:
            event_type = str(row.get("eventType", "")).strip()
            if not event_type:
                continue
            event_count_map[event_type] = int(row.get("eventCount", 0) or 0)

        summary: Dict[str, object] = {}
        for event_type, field_name in CONVERSION_OVERVIEW_EVENT_KEYS.items():
            summary[field_name] = int(event_count_map.get(event_type, 0) or 0)
        redeem_submit_count = int(summary["redeemSubmitCount"])
        redeem_success_count = int(summary["redeemSuccessCount"])
        mock_order_created_count = int(summary["mockOrderCreatedCount"])
        mock_payment_success_count = int(summary["mockPaymentSuccessCount"])
        summary["redeemConversionRate"] = round((redeem_success_count / redeem_submit_count), 4) if redeem_submit_count > 0 else 0.0
        summary["mockPaymentRate"] = (
            round((mock_payment_success_count / mock_order_created_count), 4)
            if mock_order_created_count > 0
            else 0.0
        )

        daily_map: Dict[str, Dict[str, object]] = {}
        for row in daily_rows:
            event_date = str(row.get("eventDate", "")).strip()
            event_type = str(row.get("eventType", "")).strip()
            event_count = int(row.get("eventCount", 0) or 0)
            if not event_date:
                continue
            if event_date not in daily_map:
                daily_map[event_date] = {"eventDate": event_date}
                for key in CONVERSION_OVERVIEW_EVENT_KEYS.values():
                    daily_map[event_date][key] = 0
            field_name = CONVERSION_OVERVIEW_EVENT_KEYS.get(event_type, "")
            if field_name:
                daily_map[event_date][field_name] = int(daily_map[event_date].get(field_name, 0) or 0) + event_count

        daily_trend = [daily_map[key] for key in sorted(daily_map.keys())]
        return {
            "dateRange": {"startDate": start_day.isoformat(), "endDate": end_day.isoformat()},
            "summary": summary,
            "eventTypeCounters": event_counter_rows,
            "dailyTrend": daily_trend,
        }
