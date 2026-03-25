from __future__ import annotations

from app.service_shared import *

DEFAULT_SUBSCRIPTION_PLAN_CODE = "AI_SCORE_BOOST_30D"
SUBSCRIPTION_STATUS_INACTIVE = "INACTIVE"
SUBSCRIPTION_STATUS_ACTIVE = "ACTIVE"
SUBSCRIPTION_STATUS_EXPIRED = "EXPIRED"
REDEEM_STATUS_UNUSED = "UNUSED"
ORDER_STATUS_CREATED = "CREATED"
ORDER_STATUS_PAID = "PAID"


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
