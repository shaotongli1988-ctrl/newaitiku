from __future__ import annotations

from app.service_shared import *


class InternalSystemAdminServiceMixin:
    def _build_system_console_summary(self, directory: List[Dict[str, object]]) -> Dict[str, int]:
        return {
            "studentCount": len([item for item in directory if item["role"] == ROLE_STUDENT]),
            "teacherCount": len([item for item in directory if item["role"] == ROLE_TEACHER]),
            "disabledCount": len([item for item in directory if not item.get("enabled", True)]),
            "messageCount": len(self._system_messages()),
            "templateCount": len(self._paper_templates()),
        }

    def _save_system_settings_value(self, settings: Dict[str, object]) -> None:
        system_state = self._load_system_state()
        system_state["systemSettings"] = settings
        self._save_system_state(system_state)

    def _notify_system_settings_updated(self, user_id: str) -> None:
        self._push_message(
            user_ids=[user_id],
            category="SYSTEM_NOTICE",
            title="系统设置已更新",
            content=f"{user_id} 已更新平台基础设置。",
        )

    def _filter_managed_users(
        self,
        users: List[Dict[str, object]],
        filters: Dict[str, str],
    ) -> List[Dict[str, object]]:
        role = normalize_role(filters.get("role", "").strip())
        keyword = filters.get("keyword", "").strip()
        if role:
            users = [item for item in users if item["role"] == role]
        if keyword:
            users = [
                item
                for item in users
                if keyword in item["userId"] or keyword in item["name"] or keyword in item.get("mobile", "")
            ]
        return users

    def _build_managed_students_export_lines(
        self,
        students: List[Dict[str, object]],
        export_format: str,
    ) -> List[str]:
        if export_format == "pdf":
            lines = [
                "考生目录导出",
                f"studentCount: {len(students)}",
            ]
            for item in students:
                lines.append(
                    " / ".join(
                        [
                            str(item["userId"]),
                            str(item["name"]),
                            str(item["examCategoryCode"] or "-"),
                            str(item["jointExamGroupCode"] or "-"),
                        ]
                    )
                )
            return lines
        lines = ["userId,name,mobile,examCategoryCode,jointExamGroupCode,vocationalMajor,prepStage"]
        for item in students:
            lines.append(
                ",".join(
                    [
                        str(item["userId"]),
                        self._csv_cell(str(item["name"])),
                        str(item["mobile"]),
                        str(item["examCategoryCode"]),
                        str(item["jointExamGroupCode"]),
                        self._csv_cell(str(item["vocationalMajor"])),
                        self._csv_cell(str(item["prepStage"])),
                    ]
                )
            )
        return lines

    def _validate_managed_user_payload(self, user: Dict[str, object]) -> None:
        if user["role"] == ROLE_STUDENT:
            self._validate_student_managed_user(user)
            return
        self._validate_backoffice_managed_user(user)

    def _validate_student_managed_user(self, user: Dict[str, object]) -> None:
        if user["permissions"]:
            raise validation_failed("学生账号不可配置后台权限点。")
        if not user["examCategoryCode"] or not user["jointExamGroupCode"]:
            raise validation_failed("学生账号必须绑定 examCategoryCode 与 jointExamGroupCode。")
        joint_exam_group = get_joint_exam_group(user["jointExamGroupCode"])
        if not joint_exam_group or joint_exam_group["examCategoryCode"] != user["examCategoryCode"]:
            raise validation_failed("jointExamGroupCode 与 examCategoryCode 不匹配。")

    def _validate_backoffice_managed_user(self, user: Dict[str, object]) -> None:
        allowed = set(self._allowed_permissions_for_role(str(user["role"])))
        if not allowed:
            raise validation_failed("后台账号角色不支持配置 permissions。")
        for key in user["permissions"]:
            if str(key) not in allowed:
                raise validation_failed(f"{user['role']} 角色仅可配置 {', '.join(sorted(allowed))}。")
        if not user["permissions"]:
            raise validation_failed("后台账号至少需要配置一个 permissions 权限点。")

    def _assert_managed_user_mobile_unique(
        self,
        managed_users: List[Dict[str, object]],
        user: Dict[str, object],
    ) -> None:
        for item in managed_users:
            if item["mobile"] == user["mobile"] and item["userId"] != user["userId"]:
                raise validation_failed("mobile 必须唯一。")

    def _prepare_managed_user_for_save(
        self,
        user: Dict[str, object],
        existing: Optional[Dict[str, object]],
    ) -> Dict[str, object]:
        saved = dict(user)
        saved["updateTime"] = self._now_iso()
        saved["createTime"] = existing.get("createTime", saved["updateTime"]) if existing else saved["updateTime"]
        return saved

    def _managed_user_storage_payload(self, user: Dict[str, object]) -> Dict[str, object]:
        saved = dict(user)
        if normalize_role(str(saved.get("role", "")).strip()) == ROLE_STUDENT:
            saved["examCategoryCode"] = ""
            saved["jointExamGroupCode"] = ""
        return saved

    def _upsert_managed_user_list(
        self,
        managed_users: List[Dict[str, object]],
        user: Dict[str, object],
        existing: Optional[Dict[str, object]],
    ) -> List[Dict[str, object]]:
        stored_user = self._managed_user_storage_payload(user)
        if existing:
            return [stored_user if item["userId"] == user["userId"] else item for item in managed_users]
        return [*managed_users, stored_user]

    def _after_managed_user_saved(self, user: Dict[str, object]) -> None:
        if user["role"] == ROLE_STUDENT:
            self._sync_student_directory_profile(user)
        self._push_message(
            user_ids=[user["userId"]],
            category="SYSTEM_NOTICE",
            title="账号信息已更新",
            content="管理员已更新你的账号信息与备考配置。",
        )

    def _student_import_header(self) -> List[str]:
        return [
            "userId",
            "name",
            "mobile",
            "examCategoryCode",
            "jointExamGroupCode",
            "vocationalMajor",
            "prepStage",
        ]

    def _parse_student_import_rows(self, csv_text: str) -> List[List[str]]:
        parsed_rows = []
        reader = csv.reader(io.StringIO(csv_text))
        for row in reader:
            cleaned = [str(item).strip() for item in row]
            if not cleaned or not any(cleaned):
                continue
            parsed_rows.append(cleaned)
        if len(parsed_rows) < 2:
            raise validation_failed("批量导入至少需要表头和一行数据。")
        header = parsed_rows[0]
        if header != self._student_import_header():
            raise validation_failed("导入模板字段必须为 userId,name,mobile,examCategoryCode,jointExamGroupCode,vocationalMajor,prepStage。")
        return parsed_rows

    def _parse_student_import_row(
        self,
        values: List[str],
        index: int,
        expected: List[str],
        batch_user_ids: set[str],
        batch_mobiles: set[str],
    ) -> Tuple[Optional[Dict[str, str]], Optional[Dict[str, object]]]:
        if len(values) != len(expected):
            return None, self._build_import_error_detail(index, "FIELD_COUNT_INVALID", f"第 {index} 行字段数不正确。")
        row = dict(zip(expected, values))
        if row["userId"] in batch_user_ids:
            return None, self._build_import_error_detail(index, "USER_ID_DUPLICATED", f"第 {index} 行导入失败：userId 重复。")
        if row["mobile"] in batch_mobiles:
            return None, self._build_import_error_detail(index, "MOBILE_DUPLICATED", f"第 {index} 行导入失败：mobile 重复。")
        return row, None

    def _build_import_error_detail(self, row_number: int, error_code: str, error_message: str) -> Dict[str, object]:
        return {
            "rowNumber": row_number,
            "errorCode": error_code,
            "errorMessage": error_message,
        }

    def _filter_messages_for_actor(
        self,
        messages: List[Dict[str, object]],
        actor: Actor,
    ) -> List[Dict[str, object]]:
        return [
            item
            for item in messages
            if not item.get("isRecalled")
            and (item["userId"] == actor.user_id or (actor.role == ROLE_SUPER_ADMIN and item["userId"] == "*"))
        ]

    def _apply_message_filters(
        self,
        messages: List[Dict[str, object]],
        filters: Dict[str, str],
    ) -> List[Dict[str, object]]:
        category = filters.get("category", "").strip()
        read_status = filters.get("readStatus", "").strip()
        if category:
            messages = [item for item in messages if item["category"] == category]
        if read_status == "read":
            return [item for item in messages if item.get("isRead")]
        if read_status == "unread":
            return [item for item in messages if not item.get("isRead")]
        return messages

    def _mark_message_read_in_state(
        self,
        system_state: Dict[str, object],
        message_id: str,
        user_id: str,
    ) -> bool:
        for item in system_state["messages"]:
            if item["messageId"] == message_id and item["userId"] == user_id:
                item["isRead"] = True
                item["readAt"] = self._now_iso()
                return True
        return False

    def _save_message_settings_value(self, user_id: str, settings: Dict[str, object]) -> None:
        system_state = self._load_system_state()
        system_state["messageSettingsByUser"][user_id] = settings
        self._save_system_state(system_state)

    def _invalid_message_target_user_ids(self, user_ids: List[str]) -> List[str]:
        invalid: List[str] = []
        for user_id in user_ids:
            managed_user = self._get_managed_user(user_id)
            if not managed_user or not managed_user.get("enabled", True):
                invalid.append(user_id)
        return invalid

    def _resolve_message_target_user_ids(self, payload: Dict[str, object]) -> List[str]:
        target_mode = str(payload.get("targetMode", "userIds")).strip() or "userIds"
        if target_mode == "userIds":
            return self._deduplicate_ids(payload.get("userIds", []), "userIds")
        students = [item for item in self._managed_users() if item.get("role") == ROLE_STUDENT and item.get("enabled", True)]
        exam_category_code = str(payload.get("examCategoryCode", "")).strip()
        joint_exam_group_code = str(payload.get("jointExamGroupCode", "")).strip()
        subject_code = str(payload.get("subjectCode", "")).strip()
        matched: List[str] = []
        for item in students:
            if exam_category_code and str(item.get("examCategoryCode", "")) != exam_category_code:
                continue
            if joint_exam_group_code and str(item.get("jointExamGroupCode", "")) != joint_exam_group_code:
                continue
            if subject_code and not self._managed_student_matches_subject(item, subject_code):
                continue
            matched.append(str(item.get("userId", "")))
        matched = self._deduplicate_ids(matched, "userIds")
        if not matched:
            raise validation_failed("分群条件下未匹配到可发送账号。")
        return matched

    def _managed_student_matches_subject(self, user: Dict[str, object], subject_code: str) -> bool:
        if not subject_code:
            return True
        if subject_code in {item["subjectCode"] for item in PUBLIC_SUBJECTS}:
            return True
        joint_exam_group = get_joint_exam_group(str(user.get("jointExamGroupCode", "")))
        if not joint_exam_group:
            return False
        return any(str(item.get("subjectCode", "")) == subject_code for item in joint_exam_group.get("professionalSubjects", []))

    def _parse_optional_send_at(self, value: str) -> Optional[datetime]:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        try:
            candidate = normalized.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(candidate)
        except ValueError as exc:
            raise validation_failed("sendAt 必须是 ISO 时间格式。") from exc
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _create_message_schedule(
        self,
        message: Dict[str, object],
        target_user_ids: List[str],
        sender_user_id: str,
        trace_id: str,
        send_at: datetime,
    ) -> str:
        schedule_id = f"message-schedule-{uuid.uuid4().hex[:10]}"
        system_state = self._load_system_state()
        schedules = list(system_state.get("messageSchedules", []))
        schedules.append(
            {
                "scheduleId": schedule_id,
                "traceId": trace_id,
                "senderUserId": sender_user_id,
                "targetUserIds": target_user_ids,
                "targetCount": len(target_user_ids),
                "category": str(message["category"]),
                "title": str(message["title"]),
                "content": str(message["content"]),
                "sendAt": self._to_iso_z(send_at),
                "status": "SCHEDULED",
                "createTime": self._now_iso(),
            }
        )
        system_state["messageSchedules"] = schedules[-300:]
        self._save_system_state(system_state)
        return schedule_id

    def _append_message_send_history(self, payload: Dict[str, object]) -> None:
        normalized = dict(payload)
        normalized.setdefault("sentCount", int(normalized.get("targetCount", 0)))
        normalized.setdefault("updateTime", self._now_iso())
        self.repository.upsert_message_send_history_payload(normalized)

    def _message_send_history(self) -> List[Dict[str, object]]:
        return self.repository.list_message_send_history_by_sender("")

    def _dispatch_due_scheduled_messages(self) -> None:
        system_state = self._load_system_state()
        schedules = list(system_state.get("messageSchedules", []))
        if not schedules:
            return
        now = datetime.now(timezone.utc)
        changed = False
        for item in schedules:
            if str(item.get("status", "")) != "SCHEDULED":
                continue
            send_at = self._parse_optional_send_at(str(item.get("sendAt", "")))
            if not send_at or send_at > now:
                continue
            target_user_ids = self._deduplicate_ids(item.get("targetUserIds", []), "targetUserIds")
            sent_count = self._dispatch_message_payload(
                target_user_ids,
                str(item.get("category", "")),
                str(item.get("title", "")),
                str(item.get("content", "")),
                sender_user_id=str(item.get("senderUserId", "")),
                trace_id=str(item.get("traceId", "")),
                send_at=str(item.get("sendAt", "")) or self._now_iso(),
                system_state=system_state,
            )
            item["status"] = "SENT"
            item["sentAt"] = self._now_iso()
            item["sentCount"] = sent_count
            history = self.repository.get_message_send_history_payload(str(item.get("traceId", "")))
            if history:
                history["status"] = "SENT"
                history["sendAt"] = str(item.get("sentAt", ""))
                history["sentCount"] = sent_count
                history["updateTime"] = str(item.get("sentAt", ""))
                self.repository.upsert_message_send_history_payload(history)
            changed = True
        if changed:
            system_state["messageSchedules"] = schedules
            self._save_system_state(system_state)

    def _dispatch_message_payload(
        self,
        target_user_ids: List[str],
        category: str,
        title: str,
        content: str,
        sender_user_id: str,
        trace_id: str,
        send_at: str,
        system_state: Optional[Dict[str, object]] = None,
    ) -> int:
        return self._push_message(
            user_ids=target_user_ids,
            category=category,
            title=title,
            content=content,
            sender_user_id=sender_user_id,
            send_trace_id=trace_id,
            send_at=send_at,
            system_state=system_state,
        )

    def _default_system_settings(self) -> Dict[str, object]:
        return {
            "platformName": "专升本 ALL AI",
            "defaultExamMinutes": 120,
            "dailyCheckInPoints": 2,
            "practiceRewardThreshold": 10,
            "practiceRewardPoints": 2,
            "paperRewardPoints": 2,
            "wrongBookRewardThreshold": 5,
            "wrongBookRewardPoints": 2,
            "aiDailyLimit": 20,
            "mockExamRuleProfiles": {
                "POLITICS": {
                    "durationMinutes": 90,
                    "typeRules": [
                        {"type": "single_choice", "count": 20, "questionScore": 2},
                        {"type": "multiple_choice", "count": 5, "questionScore": 4},
                        {"type": "judge", "count": 10, "questionScore": 2},
                        {"type": "subjective", "count": 2, "questionScore": 10},
                    ],
                    "difficultyRatio": {"easy": 0.3, "medium": 0.5, "hard": 0.2},
                },
                "ENGLISH": {
                    "durationMinutes": 90,
                    "typeRules": [
                        {"type": "single_choice", "count": 25, "questionScore": 2},
                        {"type": "judge", "count": 10, "questionScore": 1},
                        {"type": "subjective", "count": 4, "questionScore": 10},
                    ],
                    "difficultyRatio": {"easy": 0.25, "medium": 0.55, "hard": 0.2},
                },
                "__DEFAULT_150__": {
                    "durationMinutes": 120,
                    "typeRules": [
                        {"type": "single_choice", "count": 20, "questionScore": 2},
                        {"type": "multiple_choice", "count": 10, "questionScore": 4},
                        {"type": "judge", "count": 10, "questionScore": 2},
                        {"type": "subjective", "count": 5, "questionScore": 10},
                    ],
                    "difficultyRatio": {"easy": 0.25, "medium": 0.5, "hard": 0.25},
                },
                "__DEFAULT_100__": {
                    "durationMinutes": 90,
                    "typeRules": [
                        {"type": "single_choice", "count": 20, "questionScore": 2},
                        {"type": "multiple_choice", "count": 5, "questionScore": 4},
                        {"type": "judge", "count": 10, "questionScore": 2},
                        {"type": "subjective", "count": 2, "questionScore": 10},
                    ],
                    "difficultyRatio": {"easy": 0.3, "medium": 0.5, "hard": 0.2},
                },
            },
        }

    def _normalize_system_settings(self, settings: object) -> Dict[str, object]:
        defaults = self._default_system_settings()
        normalized = dict(defaults)
        if isinstance(settings, dict):
            normalized.update(settings)
        legacy_reward_signature = (
            int(normalized.get("dailyCheckInPoints", 0) or 0),
            int(normalized.get("practiceRewardPoints", 0) or 0),
            int(normalized.get("paperRewardPoints", 0) or 0),
            int(normalized.get("wrongBookRewardPoints", 0) or 0),
        )
        if legacy_reward_signature == (10, 20, 30, 15):
            normalized["dailyCheckInPoints"] = 2
            normalized["practiceRewardPoints"] = 2
            normalized["paperRewardPoints"] = 2
            normalized["wrongBookRewardPoints"] = 2
        return normalized

    def _default_message_settings(self) -> Dict[str, object]:
        return {
            "allowAiTutor": True,
            "allowSystemNotice": True,
            "allowReviewNotice": True,
            "allowStudyReminder": True,
            "allowWeeklyReport": True,
            "allowPointsNotice": True,
        }

    def _default_managed_users(self) -> List[Dict[str, object]]:
        return [
            {
                "userId": "admin-001",
                "role": ROLE_SUPER_ADMIN,
                "name": "总管理员",
                "mobile": "13800000001",
                "enabled": True,
                "permissions": self._default_permissions_for_role(ROLE_SUPER_ADMIN),
                "examCategoryCode": "",
                "jointExamGroupCode": "",
                "vocationalMajor": "",
                "prepStage": "",
                "createTime": self._now_iso(),
                "updateTime": self._now_iso(),
            },
            {
                "userId": "teacher-001",
                "role": ROLE_TEACHER,
                "name": "教师A",
                "mobile": "13800000002",
                "enabled": True,
                "permissions": self._default_permissions_for_role(ROLE_TEACHER),
                "examCategoryCode": "",
                "jointExamGroupCode": "",
                "vocationalMajor": "",
                "prepStage": "",
                "createTime": self._now_iso(),
                "updateTime": self._now_iso(),
            },
            {
                "userId": "teacher-002",
                "role": ROLE_TEACHER,
                "name": "教师B",
                "mobile": "13800000003",
                "enabled": True,
                "permissions": self._default_permissions_for_role(ROLE_TEACHER),
                "examCategoryCode": "",
                "jointExamGroupCode": "",
                "vocationalMajor": "",
                "prepStage": "",
                "createTime": self._now_iso(),
                "updateTime": self._now_iso(),
            },
            {
                "userId": "academic-001",
                "role": ROLE_TEACHER,
                "name": "教师学情专员",
                "mobile": "13800000004",
                "enabled": True,
                "permissions": self._default_permissions_for_role(ROLE_TEACHER),
                "examCategoryCode": "",
                "jointExamGroupCode": "",
                "vocationalMajor": "",
                "prepStage": "",
                "createTime": self._now_iso(),
                "updateTime": self._now_iso(),
            },
            {
                "userId": "student-001",
                "role": ROLE_STUDENT,
                "name": "理工考生",
                "mobile": "13800000005",
                "enabled": True,
                "permissions": [],
                "examCategoryCode": "",
                "jointExamGroupCode": "",
                "vocationalMajor": "计算机类",
                "prepStage": "强化阶段",
                "createTime": self._now_iso(),
                "updateTime": self._now_iso(),
            },
            {
                "userId": "student-002",
                "role": ROLE_STUDENT,
                "name": "文学考生",
                "mobile": "13800000006",
                "enabled": True,
                "permissions": [],
                "examCategoryCode": "",
                "jointExamGroupCode": "",
                "vocationalMajor": "语言类",
                "prepStage": "冲刺阶段",
                "createTime": self._now_iso(),
                "updateTime": self._now_iso(),
            },
        ]

    def _ensure_system_record(self) -> Dict[str, str]:
        record = self.repository.get_student_question_bank("question-seed-001", SYSTEM_RECORD_USER_ID)
        if record:
            return record
        anchor_question = self.repository.get_first_published_question()
        if not anchor_question:
            raise not_found("当前没有可用题目，无法初始化系统配置。")
        payload = {
            "id": f"student-bank-{uuid.uuid4().hex[:8]}",
            "questionId": anchor_question["id"],
            "studentUserId": SYSTEM_RECORD_USER_ID,
            "status": "ACTIVE",
            "extJson": self._dump_json(
                {
                    "stateVersion": 0,
                    "systemSettings": self._default_system_settings(),
                    "managedUsers": self._default_managed_users(),
                    "messages": [],
                    "messageSettingsByUser": {},
                    "messageSchedules": [],
                    "teacherQaThreads": [],
                    "paperTemplates": [],
                }
            ),
        }
        self.repository.upsert_student_question_bank(payload)
        return payload

    def _load_system_state(self) -> Dict[str, object]:
        record = self._ensure_system_record()
        state = self._load_json_object(record["extJson"])
        state["stateVersion"] = self._safe_state_version(state.get("stateVersion", 0))
        state["systemSettings"] = self._normalize_system_settings(state.get("systemSettings", {}))
        state.setdefault("managedUsers", self._default_managed_users())
        state["managedUsers"] = self._normalize_managed_users(state["managedUsers"])
        state.setdefault("messages", [])
        state.setdefault("messageSettingsByUser", {})
        state.setdefault("messageSchedules", [])
        state.pop("messageSendHistory", None)
        state.setdefault("teacherQaThreads", [])
        state.setdefault("paperTemplates", [])
        state.pop("paperReports", None)
        state.setdefault("syllabusVersions", self._default_syllabus_versions())
        state["syllabusVersions"] = self._normalize_syllabus_versions(state["syllabusVersions"])
        state.setdefault("undoSnapshots", [])
        return state

    def _active_undo_snapshots(self, snapshots: object) -> List[Dict[str, object]]:
        if not isinstance(snapshots, list):
            return []
        now = self._now_iso()
        active: List[Dict[str, object]] = []
        for item in snapshots:
            if not isinstance(item, dict):
                continue
            snapshot_id = str(item.get("snapshotId", "")).strip()
            resource_type = str(item.get("resourceType", "")).strip()
            owner_user_id = str(item.get("ownerUserId", "")).strip()
            expire_at = str(item.get("expireAt", "")).strip()
            if not snapshot_id or not resource_type or not owner_user_id or not expire_at:
                continue
            if expire_at <= now:
                continue
            normalized = dict(item)
            normalized["snapshotId"] = snapshot_id
            normalized["resourceType"] = resource_type
            normalized["ownerUserId"] = owner_user_id
            normalized["expireAt"] = expire_at
            active.append(normalized)
        return active

    def _create_undo_snapshot(
        self,
        resource_type: str,
        payload: Dict[str, object],
        actor: Actor,
        ttl_sec: int = 600,
    ) -> str:
        now = datetime.now(timezone.utc)
        snapshot_id = f"undo-{uuid.uuid4().hex[:10]}"
        expire_at = now + timedelta(seconds=ttl_sec)
        snapshot = {
            "snapshotId": snapshot_id,
            "resourceType": resource_type,
            "ownerUserId": actor.user_id,
            "ownerRole": actor.role,
            "createTime": self._to_iso_z(now),
            "expireAt": self._to_iso_z(expire_at),
            "payload": payload,
        }
        system_state = self._load_system_state()
        snapshots = self._active_undo_snapshots(system_state.get("undoSnapshots", []))
        snapshots.append(snapshot)
        system_state["undoSnapshots"] = snapshots[-200:]
        self._save_system_state(system_state)
        return snapshot_id

    def _consume_undo_snapshot(
        self,
        snapshot_id: str,
        expected_resource_type: str,
        actor: Actor,
    ) -> Dict[str, object]:
        system_state = self._load_system_state()
        snapshots = self._active_undo_snapshots(system_state.get("undoSnapshots", []))
        matched: Optional[Dict[str, object]] = None
        remained: List[Dict[str, object]] = []
        for item in snapshots:
            if item.get("snapshotId") == snapshot_id:
                matched = item
                continue
            remained.append(item)
        system_state["undoSnapshots"] = remained
        self._save_system_state(system_state)
        if not matched:
            raise not_found("撤销快照不存在或已过期。")
        if str(matched.get("resourceType", "")) != expected_resource_type:
            raise validation_failed("撤销快照类型不匹配。")
        if actor.role != ROLE_SUPER_ADMIN and str(matched.get("ownerUserId", "")) != actor.user_id:
            raise forbidden("当前账号不可使用该撤销快照。")
        return matched

    def _normalize_managed_users(self, users: object) -> List[Dict[str, object]]:
        if not isinstance(users, list):
            return self._default_managed_users()
        normalized: List[Dict[str, object]] = []
        for raw in users:
            if not isinstance(raw, dict):
                continue
            item = dict(raw)
            role = normalize_role(str(item.get("role", "")).strip())
            if role not in ALL_ROLES:
                continue
            item["role"] = role
            item.setdefault("enabled", True)
            item.setdefault("examCategoryCode", "")
            item.setdefault("jointExamGroupCode", "")
            item.setdefault("vocationalMajor", "")
            item.setdefault("prepStage", "")
            if role == ROLE_STUDENT:
                item["permissions"] = []
                item["examCategoryCode"] = ""
                item["jointExamGroupCode"] = ""
            else:
                allowed_permissions = set(self._allowed_permissions_for_role(role))
                existing_permissions = item.get("permissions", [])
                normalized_permissions = []
                if isinstance(existing_permissions, list):
                    for value in existing_permissions:
                        key = str(value).strip()
                        if key in allowed_permissions and key not in normalized_permissions:
                            normalized_permissions.append(key)
                if not normalized_permissions:
                    normalized_permissions = self._default_permissions_for_role(role)
                item["permissions"] = normalized_permissions
            normalized.append(item)
        return normalized or self._default_managed_users()

    def _system_settings(self) -> Dict[str, object]:
        return dict(self._load_system_state()["systemSettings"])

    def _apply_student_scope_projection_to_managed_user(self, user: Dict[str, object]) -> Dict[str, object]:
        if normalize_role(str(user.get("role", ""))) != ROLE_STUDENT:
            return dict(user)
        student_user_id = str(user.get("userId", "")).strip()
        if not student_user_id:
            return dict(user)
        profile_state = self.repository.get_student_profile_state(student_user_id)
        if not profile_state:
            return dict(user)
        projected = dict(user)
        exam_category_code = str(profile_state.get("examCategoryCode", "")).strip()
        joint_exam_group_code = str(profile_state.get("jointExamGroupCode", "")).strip()
        vocational_major = str(profile_state.get("vocationalMajor", "")).strip()
        prep_stage = str(profile_state.get("prepStage", "")).strip()
        if exam_category_code:
            projected["examCategoryCode"] = exam_category_code
        if joint_exam_group_code:
            projected["jointExamGroupCode"] = joint_exam_group_code
        if vocational_major:
            projected["vocationalMajor"] = vocational_major
        if prep_stage:
            projected["prepStage"] = prep_stage
        return projected

    def _raw_managed_users(self, system_state: Optional[Dict[str, object]] = None) -> List[Dict[str, object]]:
        state = system_state if system_state is not None else self._load_system_state()
        return list(state["managedUsers"])

    def _managed_users(self) -> List[Dict[str, object]]:
        return [
            self._apply_student_scope_projection_to_managed_user(item)
            for item in self._raw_managed_users()
        ]

    def _system_messages(self) -> List[Dict[str, object]]:
        return list(self._load_system_state()["messages"])

    def _message_settings_for_user(
        self,
        user_id: str,
        system_state: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        source = system_state or self._load_system_state()
        return dict(source["messageSettingsByUser"].get(user_id, self._default_message_settings()))

    def _paper_templates(self) -> List[Dict[str, object]]:
        return list(self._load_system_state()["paperTemplates"])

    def _paper_reports(self) -> List[Dict[str, object]]:
        return self.repository.list_paper_reports_by_student("")

    def _syllabus_versions(self) -> List[Dict[str, object]]:
        return list(self._load_system_state()["syllabusVersions"])

    def _sorted_syllabus_versions(self, versions: List[Dict[str, object]]) -> List[Dict[str, object]]:
        return sorted(
            [item for item in versions if isinstance(item, dict)],
            key=lambda item: (str(item.get("updateTime", "")), str(item.get("createTime", "")), str(item.get("versionId", ""))),
            reverse=True,
        )

    def _serialize_syllabus_version(self, version: Dict[str, object]) -> Dict[str, object]:
        knowledge_weights = [
            {
                "knowledgeId": str(weight.get("knowledgeId", "")),
                "knowledgeName": str(weight.get("knowledgeName", "")),
                "targetWeight": float(weight.get("targetWeight", 0.0)),
                "sort": int(weight.get("sort", 0)),
            }
            for weight in version.get("knowledgeWeights", [])
            if isinstance(weight, dict)
        ]
        weight_total = round(sum(float(item["targetWeight"]) for item in knowledge_weights), 6)
        return {
            "versionId": str(version.get("versionId", "")),
            "versionName": str(version.get("versionName", "")),
            "knowledgeWeights": knowledge_weights,
            "weightTotal": weight_total,
            "createTime": str(version.get("createTime", "")),
            "updateTime": str(version.get("updateTime", "")),
            "operatorUserId": str(version.get("operatorUserId", "")),
        }

    def _default_syllabus_versions(self) -> List[Dict[str, object]]:
        default_weights = self._default_syllabus_knowledge_weights()
        if not default_weights:
            return []
        now = self._now_iso()
        return [
            {
                "versionId": "syllabus-default",
                "versionName": "默认大纲",
                "knowledgeWeights": default_weights,
                "createTime": now,
                "updateTime": now,
                "operatorUserId": SYSTEM_RECORD_USER_ID,
            }
        ]

    def _default_syllabus_knowledge_weights(self) -> List[Dict[str, object]]:
        knowledge_items = self._sorted_syllabus_knowledge_items()
        if not knowledge_items:
            return []
        units = self._allocate_equal_weight_units(len(knowledge_items))
        return [
            {
                "knowledgeId": str(item["id"]),
                "knowledgeName": str(item["name"]),
                "targetWeight": float(Decimal(units[index]) / Decimal(SYLLABUS_WEIGHT_SCALE)),
                "sort": int(item["sort"]),
            }
            for index, item in enumerate(knowledge_items)
        ]

    def _sorted_syllabus_knowledge_items(self) -> List[Dict[str, object]]:
        candidates = self.repository.list_knowledge("ENABLED")
        if not candidates:
            candidates = self.repository.list_knowledge("")
        point_level_candidates = [
            row
            for row in candidates
            if int(self._load_json_object(str(row.get("extJson", "{}"))).get("level", 0) or 0) == 5
        ]
        if point_level_candidates:
            candidates = point_level_candidates
        normalized: List[Dict[str, object]] = []
        for row in candidates:
            knowledge_id = str(row.get("id", "")).strip()
            if not knowledge_id:
                continue
            normalized.append(
                {
                    "id": knowledge_id,
                    "name": str(row.get("name", "")).strip() or knowledge_id,
                    "sort": int(row.get("sort", 0)),
                }
            )
        normalized.sort(key=lambda item: (int(item["sort"]), str(item["id"])))
        return normalized

    def _syllabus_knowledge_lookup(self) -> Dict[str, Dict[str, object]]:
        lookup: Dict[str, Dict[str, object]] = {}
        for row in self._sorted_syllabus_knowledge_items():
            lookup[str(row["id"])] = {"name": str(row["name"]), "sort": int(row["sort"])}
        return lookup

    def _normalize_syllabus_versions(self, versions: object) -> List[Dict[str, object]]:
        if not isinstance(versions, list):
            return self._default_syllabus_versions()
        knowledge_lookup = self._syllabus_knowledge_lookup()
        normalized_versions: List[Dict[str, object]] = []
        for raw_version in versions:
            if not isinstance(raw_version, dict):
                continue
            version_id = str(raw_version.get("versionId", "")).strip()
            version_name = str(raw_version.get("versionName", "")).strip()
            if not version_id or not version_name:
                continue
            raw_weights = raw_version.get("knowledgeWeights", [])
            if not isinstance(raw_weights, list) or not raw_weights:
                continue
            normalized_weights: List[Dict[str, object]] = []
            seen_ids: set[str] = set()
            for order_index, raw_weight in enumerate(raw_weights):
                if not isinstance(raw_weight, dict):
                    continue
                knowledge_id = str(raw_weight.get("knowledgeId", "")).strip()
                if not knowledge_id or knowledge_id in seen_ids:
                    continue
                seen_ids.add(knowledge_id)
                lookup_item = knowledge_lookup.get(knowledge_id, {})
                target_weight = self._safe_syllabus_weight(raw_weight.get("targetWeight", 0))
                normalized_weights.append(
                    {
                        "knowledgeId": knowledge_id,
                        "knowledgeName": str(raw_weight.get("knowledgeName", "")).strip() or str(lookup_item.get("name", knowledge_id)),
                        "targetWeight": target_weight,
                        "sort": int(raw_weight.get("sort", int(lookup_item.get("sort", (order_index + 1) * 10)))),
                    }
                )
            if not normalized_weights:
                continue
            normalized_weights = self._rebalance_syllabus_weights(normalized_weights)
            normalized_versions.append(
                {
                    "versionId": version_id,
                    "versionName": version_name,
                    "knowledgeWeights": normalized_weights,
                    "createTime": str(raw_version.get("createTime", "")),
                    "updateTime": str(raw_version.get("updateTime", "")) or str(raw_version.get("createTime", "")),
                    "operatorUserId": str(raw_version.get("operatorUserId", "")),
                }
            )
        return normalized_versions or self._default_syllabus_versions()

    def _safe_syllabus_weight(self, value: object) -> float:
        try:
            normalized = float(value)
        except (TypeError, ValueError):
            return 0.0
        if not math.isfinite(normalized):
            return 0.0
        if normalized < 0:
            return 0.0
        if normalized > 1:
            return 1.0
        return normalized

    def _rebalance_syllabus_weights(self, weights: List[Dict[str, object]]) -> List[Dict[str, object]]:
        if not weights:
            return []
        base_values: List[Decimal] = []
        for item in weights:
            try:
                decimal_value = Decimal(str(item.get("targetWeight", 0)))
            except (TypeError, ValueError, InvalidOperation):
                decimal_value = Decimal("0")
            if decimal_value < 0:
                decimal_value = Decimal("0")
            base_values.append(decimal_value)
        if sum(base_values, Decimal("0")) <= Decimal("0"):
            units = self._allocate_equal_weight_units(len(weights))
        else:
            units = self._allocate_weight_units(base_values)
        normalized_weights: List[Dict[str, object]] = []
        for index, item in enumerate(weights):
            normalized_weights.append(
                {
                    "knowledgeId": str(item.get("knowledgeId", "")),
                    "knowledgeName": str(item.get("knowledgeName", "")),
                    "targetWeight": float(Decimal(units[index]) / Decimal(SYLLABUS_WEIGHT_SCALE)),
                    "sort": int(item.get("sort", (index + 1) * 10)),
                }
            )
        return normalized_weights

    def _allocate_equal_weight_units(self, count: int) -> List[int]:
        if count <= 0:
            return []
        base_unit = SYLLABUS_WEIGHT_SCALE // count
        remainder = SYLLABUS_WEIGHT_SCALE - (base_unit * count)
        units: List[int] = []
        for index in range(count):
            units.append(base_unit + (1 if index < remainder else 0))
        return units

    def _allocate_weight_units(self, values: List[Decimal]) -> List[int]:
        if not values:
            return []
        total = sum(values, Decimal("0"))
        if total <= Decimal("0"):
            return self._allocate_equal_weight_units(len(values))
        units: List[int] = []
        remainders: List[Tuple[Decimal, int]] = []
        for index, value in enumerate(values):
            exact_units = (value / total) * Decimal(SYLLABUS_WEIGHT_SCALE)
            floor_units = int(exact_units.to_integral_value(rounding=ROUND_FLOOR))
            units.append(floor_units)
            remainders.append((exact_units - Decimal(floor_units), index))
        assigned = sum(units)
        remainder = max(0, SYLLABUS_WEIGHT_SCALE - assigned)
        remainders.sort(key=lambda item: (item[0], -item[1]), reverse=True)
        for _, index in remainders[:remainder]:
            units[index] += 1
        return units

    def _to_syllabus_weight_decimal(self, value: object) -> Decimal:
        try:
            normalized = Decimal(str(value)).quantize(Decimal("0.000001"))
        except (TypeError, ValueError, InvalidOperation) as exc:
            raise validation_failed("targetWeight 必须是合法数字。") from exc
        if normalized < Decimal("0") or normalized > Decimal("1"):
            raise validation_failed("targetWeight 必须在 0 到 1 之间。")
        return normalized

    def _extract_syllabus_source_text(self, file_name: str, file_bytes: bytes) -> Tuple[str, Dict[str, object]]:
        suffix = Path(file_name).suffix.lower().strip()
        if suffix not in SYLLABUS_AI_IMPORT_SUFFIXES:
            raise validation_failed("大纲解析仅支持 PDF、DOC、DOCX 文件。")
        if suffix == ".pdf":
            return self._extract_pdf_text_with_ocr(file_bytes)
        return self._extract_word_text(file_name, file_bytes)

    def _extract_pdf_text_with_ocr(self, file_bytes: bytes) -> Tuple[str, Dict[str, object]]:
        with tempfile.TemporaryDirectory(prefix="qb-syllabus-pdf-") as temp_dir:
            temp_path = Path(temp_dir)
            pdf_path = temp_path / "syllabus.pdf"
            txt_path = temp_path / "syllabus.txt"
            pdf_path.write_bytes(file_bytes)

            extracted = ""
            method = "pdf_raw"
            if shutil.which("pdftotext"):
                proc = subprocess.run(
                    ["pdftotext", "-layout", str(pdf_path), str(txt_path)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if proc.returncode == 0 and txt_path.exists():
                    extracted = txt_path.read_text(encoding="utf-8", errors="ignore")
                    method = "pdftotext"

            if len(extracted.strip()) >= 40:
                return extracted, {"method": method}

            ocr_chunks: List[str] = []
            if shutil.which("pdftoppm") and shutil.which("tesseract"):
                page_prefix = temp_path / "page"
                render_proc = subprocess.run(
                    ["pdftoppm", "-f", "1", "-l", "30", "-png", str(pdf_path), str(page_prefix)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if render_proc.returncode == 0:
                    for image_path in sorted(temp_path.glob("page-*.png")):
                        ocr_text = self._run_ocr_tesseract(image_path, "chi_sim+eng")
                        if not ocr_text.strip():
                            ocr_text = self._run_ocr_tesseract(image_path, "eng")
                        if ocr_text.strip():
                            ocr_chunks.append(ocr_text)

            ocr_text_full = "\n".join(ocr_chunks).strip()
            if ocr_text_full:
                if extracted.strip():
                    return f"{extracted.strip()}\n{ocr_text_full}", {"method": "pdftotext+tesseract"}
                return ocr_text_full, {"method": "tesseract"}
            return extracted, {"method": method}

    def _run_ocr_tesseract(self, image_path: Path, lang: str) -> str:
        proc = subprocess.run(
            ["tesseract", str(image_path), "stdout", "-l", lang],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            return ""
        return str(proc.stdout or "")

    def _extract_word_text(self, file_name: str, file_bytes: bytes) -> Tuple[str, Dict[str, object]]:
        suffix = Path(file_name).suffix.lower().strip()
        with tempfile.TemporaryDirectory(prefix="qb-syllabus-word-") as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / f"syllabus{suffix or '.docx'}"
            input_path.write_bytes(file_bytes)

            if shutil.which("textutil"):
                proc = subprocess.run(
                    ["textutil", "-convert", "txt", "-stdout", str(input_path)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if proc.returncode == 0 and str(proc.stdout or "").strip():
                    return str(proc.stdout), {"method": "textutil"}

        if suffix == ".docx":
            text = parse_word_content(file_bytes)
            if text.strip():
                return text, {"method": "python-docx"}

        fallback = file_bytes.decode("utf-8", errors="ignore")
        return fallback, {"method": "binary-decode"}

    def _parse_syllabus_text_with_ai(
        self,
        source_text: str,
        current_rows: List[Dict[str, object]],
    ) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
        llm_suggestions, llm_meta = self._try_parse_syllabus_with_llm(source_text, current_rows)
        if llm_suggestions:
            return llm_suggestions, llm_meta
        heuristic = self._heuristic_syllabus_suggestions(source_text, current_rows)
        return heuristic, {"mode": "heuristic", "model": ""}

    def _try_parse_syllabus_with_llm(
        self,
        source_text: str,
        current_rows: List[Dict[str, object]],
    ) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
        api_key = str(os.getenv("QB_OPENAI_API_KEY", "")).strip()
        if not api_key:
            return [], {"mode": "heuristic", "model": ""}
        base_url = str(os.getenv("QB_OPENAI_BASE_URL", "https://api.openai.com/v1")).strip().rstrip("/")
        model = str(os.getenv("QB_OPENAI_MODEL", "gpt-4o-mini")).strip() or "gpt-4o-mini"
        knowledge_catalog = [str(item.get("knowledgeName", "")) for item in current_rows if str(item.get("knowledgeName", "")).strip()]
        prompt = self._build_syllabus_llm_prompt(source_text, knowledge_catalog)
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
                            "content": "你是大纲解析助手，只返回 JSON，不要返回多余文字。",
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
            suggestions = self._normalize_ai_syllabus_suggestions(json_payload)
            if suggestions:
                return suggestions, {"mode": "llm", "model": model}
        except Exception:
            return [], {"mode": "heuristic", "model": model}
        return [], {"mode": "heuristic", "model": model}

    def _build_syllabus_llm_prompt(self, source_text: str, knowledge_catalog: List[str]) -> str:
        catalog_text = "\n".join(f"- {item}" for item in knowledge_catalog if str(item).strip())[:4000]
        source_excerpt = source_text[:16000]
        return (
            "请从以下大纲文本中提取知识点及其建议的分值占比，并按 JSON 格式输出。\n"
            "输出 JSON Schema：\n"
            "{\n"
            '  "knowledgePoints": [\n'
            '    {"knowledgeName": "知识点名称", "suggestedWeight": 0.25, "reason": "一句话依据"}\n'
            "  ]\n"
            "}\n"
            "要求：\n"
            "1. suggestedWeight 范围 0-1。\n"
            "2. 所有 suggestedWeight 之和尽量为 1。\n"
            "3. 优先使用以下候选知识点名称，不在候选中的也可输出。\n"
            f"候选知识点：\n{catalog_text}\n\n"
            f"大纲文本：\n{source_excerpt}"
        )

    def _extract_json_payload_from_text(self, content: str) -> Dict[str, object]:
        text = str(content or "").strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                parsed = json.loads(text[start : end + 1])
                return parsed if isinstance(parsed, dict) else {}
            except (TypeError, ValueError, json.JSONDecodeError):
                return {}
        return {}

    def _normalize_ai_syllabus_suggestions(self, payload: Dict[str, object]) -> List[Dict[str, object]]:
        rows = payload.get("knowledgePoints", []) if isinstance(payload, dict) else []
        if not isinstance(rows, list):
            return []
        suggestions: List[Dict[str, object]] = []
        for item in rows:
            if not isinstance(item, dict):
                continue
            knowledge_name = str(item.get("knowledgeName", "")).strip()
            if not knowledge_name:
                continue
            try:
                weight = Decimal(str(item.get("suggestedWeight", 0))).quantize(Decimal("0.000001"))
            except (TypeError, ValueError, InvalidOperation):
                continue
            if weight < Decimal("0"):
                continue
            if weight > Decimal("1"):
                weight = Decimal("1")
            suggestions.append(
                {
                    "knowledgeName": knowledge_name,
                    "targetWeight": float(weight),
                    "reason": str(item.get("reason", "")).strip(),
                }
            )
        return suggestions

    def _heuristic_syllabus_suggestions(
        self,
        source_text: str,
        current_rows: List[Dict[str, object]],
    ) -> List[Dict[str, object]]:
        normalized_text = str(source_text or "")
        if not normalized_text.strip():
            return []
        scores: List[Decimal] = []
        percent_score_by_id: Dict[str, Decimal] = {}
        for line in normalized_text.splitlines():
            line_text = str(line).strip()
            if not line_text:
                continue
            percent_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*%", line_text)
            if not percent_match:
                continue
            try:
                percent_score = Decimal(percent_match.group(1)) / Decimal("100")
            except (TypeError, ValueError, InvalidOperation):
                continue
            if percent_score <= Decimal("0"):
                continue
            for row in current_rows:
                knowledge_name = str(row.get("knowledgeName", "")).strip()
                knowledge_id = str(row.get("knowledgeId", "")).strip()
                if not knowledge_name or not knowledge_id:
                    continue
                if knowledge_name in line_text:
                    percent_score_by_id[knowledge_id] = percent_score

        for row in current_rows:
            knowledge_name = str(row.get("knowledgeName", "")).strip()
            knowledge_id = str(row.get("knowledgeId", "")).strip()
            if knowledge_id in percent_score_by_id:
                scores.append(percent_score_by_id[knowledge_id])
                continue
            hit_count = normalized_text.count(knowledge_name) if knowledge_name else 0
            if hit_count > 0:
                scores.append(Decimal(hit_count))
            else:
                scores.append(Decimal("0"))

        if sum(scores, Decimal("0")) <= Decimal("0"):
            scores = [Decimal("1") for _ in current_rows]
        units = self._allocate_weight_units(scores)
        suggestions: List[Dict[str, object]] = []
        for index, row in enumerate(current_rows):
            suggestions.append(
                {
                    "knowledgeName": str(row.get("knowledgeName", "")),
                    "targetWeight": float(Decimal(units[index]) / Decimal(SYLLABUS_WEIGHT_SCALE)),
                    "reason": "根据大纲文本命中频次估算。",
                }
            )
        return suggestions

    def _build_syllabus_prefill_rows(
        self,
        current_rows: List[Dict[str, object]],
        suggestions: List[Dict[str, object]],
    ) -> Tuple[List[Dict[str, object]], Dict[str, int]]:
        normalized_rows = [
            {
                "knowledgeId": str(item.get("knowledgeId", "")),
                "knowledgeName": str(item.get("knowledgeName", "")),
                "targetWeight": float(item.get("targetWeight", 0)),
                "sort": int(item.get("sort", 0)),
            }
            for item in current_rows
            if isinstance(item, dict) and str(item.get("knowledgeId", "")).strip()
        ]
        if not normalized_rows:
            return [], {"matchedCount": 0, "unmatchedCount": 0}
        if not suggestions:
            return self._rebalance_syllabus_weights(normalized_rows), {"matchedCount": 0, "unmatchedCount": 0}

        matched_weights: Dict[str, Decimal] = {}
        unmatched_count = 0
        for suggestion in suggestions:
            if not isinstance(suggestion, dict):
                continue
            suggestion_name = str(suggestion.get("knowledgeName", "")).strip()
            if not suggestion_name:
                continue
            row = self._best_syllabus_row_match(suggestion_name, normalized_rows)
            if not row:
                unmatched_count += 1
                continue
            knowledge_id = str(row["knowledgeId"])
            try:
                weight = Decimal(str(suggestion.get("targetWeight", 0))).quantize(Decimal("0.000001"))
            except (TypeError, ValueError, InvalidOperation):
                continue
            if weight <= Decimal("0"):
                continue
            matched_weights[knowledge_id] = matched_weights.get(knowledge_id, Decimal("0")) + weight

        if not matched_weights:
            return self._rebalance_syllabus_weights(normalized_rows), {"matchedCount": 0, "unmatchedCount": unmatched_count}

        matched_total = sum(matched_weights.values(), Decimal("0"))
        blended_rows: List[Dict[str, object]] = []
        if matched_total >= Decimal("1"):
            for row in normalized_rows:
                knowledge_id = str(row["knowledgeId"])
                weight = matched_weights.get(knowledge_id, Decimal("0"))
                blended_rows.append(
                    {
                        **row,
                        "targetWeight": float(weight / matched_total) if matched_total > 0 else 0.0,
                    }
                )
        else:
            remainder = Decimal("1") - matched_total
            unmatched_rows = [row for row in normalized_rows if str(row["knowledgeId"]) not in matched_weights]
            unmatched_current_total = sum(Decimal(str(row.get("targetWeight", 0))) for row in unmatched_rows)
            for row in normalized_rows:
                knowledge_id = str(row["knowledgeId"])
                if knowledge_id in matched_weights:
                    blended_rows.append(
                        {
                            **row,
                            "targetWeight": float(matched_weights[knowledge_id]),
                        }
                    )
                    continue
                if unmatched_current_total > 0:
                    base_weight = Decimal(str(row.get("targetWeight", 0)))
                    target_weight = remainder * (base_weight / unmatched_current_total)
                elif unmatched_rows:
                    target_weight = remainder / Decimal(len(unmatched_rows))
                else:
                    target_weight = Decimal("0")
                blended_rows.append(
                    {
                        **row,
                        "targetWeight": float(max(Decimal("0"), target_weight)),
                    }
                )
        return self._rebalance_syllabus_weights(blended_rows), {
            "matchedCount": len(matched_weights),
            "unmatchedCount": unmatched_count,
        }

    def _best_syllabus_row_match(
        self,
        suggestion_name: str,
        rows: List[Dict[str, object]],
    ) -> Optional[Dict[str, object]]:
        target_key = self._normalize_syllabus_name_key(suggestion_name)
        if not target_key:
            return None
        for row in rows:
            if self._normalize_syllabus_name_key(str(row.get("knowledgeName", ""))) == target_key:
                return row
        for row in rows:
            row_key = self._normalize_syllabus_name_key(str(row.get("knowledgeName", "")))
            if not row_key:
                continue
            if target_key in row_key or row_key in target_key:
                return row
        return None

    def _normalize_syllabus_name_key(self, value: str) -> str:
        return re.sub(r"[\\s\\W_]+", "", str(value or "").strip().lower())

    def _save_system_state(self, state: Dict[str, object]) -> None:
        record = self._ensure_system_record()
        latest_state = self._load_json_object(record["extJson"])
        latest_version = self._safe_state_version(latest_state.get("stateVersion", 0))
        expected_version = self._safe_state_version(state.get("stateVersion", 0))
        if latest_version != expected_version:
            raise validation_failed("系统状态已被其他管理员更新，请刷新页面后重试。")
        saved_state = dict(state)
        saved_state["stateVersion"] = expected_version + 1
        self.repository.upsert_student_question_bank(
            {
                "id": record["id"],
                "questionId": record["questionId"],
                "studentUserId": SYSTEM_RECORD_USER_ID,
                "status": "ACTIVE",
                "extJson": self._dump_json(saved_state),
            }
        )
        state["stateVersion"] = expected_version + 1

    def _safe_state_version(self, value: object) -> int:
        try:
            version = int(value)
        except (TypeError, ValueError):
            return 0
        return version if version >= 0 else 0

    def _get_managed_user(self, user_id: str) -> Optional[Dict[str, object]]:
        for item in self._managed_users():
            if item["userId"] == user_id:
                return item
        return None

    def _student_directory_ids(self) -> List[str]:
        return [item["userId"] for item in self._managed_users() if item["role"] == ROLE_STUDENT]

    def _sync_student_directory_profile(self, user: Dict[str, object]) -> None:
        now_iso = self._now_iso()
        self._sync_student_profile_cold_snapshot(
            str(user["userId"]),
            str(user.get("examCategoryCode", "")).strip(),
            str(user.get("jointExamGroupCode", "")).strip(),
        )
        self.repository.set_student_profile_bio(
            str(user["userId"]),
            str(user.get("vocationalMajor", "")).strip(),
            str(user.get("prepStage", "")).strip(),
            now_iso,
        )

    def _sync_student_directory_scope_projection(
        self,
        student_user_id: str,
        exam_category_code: str,
        joint_exam_group_code: str,
    ) -> None:
        normalized_student_user_id = str(student_user_id or "").strip()
        if not normalized_student_user_id:
            return
        record = self._ensure_system_record()
        raw_state = self._load_json_object(record["extJson"])
        raw_managed_users = raw_state.get("managedUsers", [])
        if not isinstance(raw_managed_users, list):
            return
        existing = next(
            (
                item
                for item in raw_managed_users
                if str(item.get("userId", "")).strip() == normalized_student_user_id
            ),
            None,
        )
        if not existing or normalize_role(str(existing.get("role", ""))) != ROLE_STUDENT:
            return
        if (
            not str(existing.get("examCategoryCode", "")).strip()
            and not str(existing.get("jointExamGroupCode", "")).strip()
        ):
            return
        system_state = self._load_system_state()
        self._save_system_state(system_state)

    def _count_unread_messages(self, user_id: str) -> int:
        return len(
            [
                item
                for item in self._system_messages()
                if item["userId"] == user_id and not item.get("isRead") and not item.get("isRecalled")
            ]
        )

    def _push_message(
        self,
        user_ids: List[str],
        category: str,
        title: str,
        content: str,
        sender_user_id: str = "",
        send_trace_id: str = "",
        send_at: str = "",
        system_state: Optional[Dict[str, object]] = None,
    ) -> int:
        state = system_state if system_state is not None else self._load_system_state()
        sent_count = 0
        for user_id in user_ids:
            settings = self._message_settings_for_user(user_id, state)
            if not self._message_enabled(settings, category):
                continue
            state["messages"].append(
                {
                    "messageId": f"message-{uuid.uuid4().hex[:8]}",
                    "userId": user_id,
                    "category": category,
                    "title": title,
                    "content": content,
                    "isRead": False,
                    "createTime": send_at or self._now_iso(),
                    "senderUserId": sender_user_id,
                    "sendTraceId": send_trace_id,
                    "isRecalled": False,
                }
            )
            sent_count += 1
        if system_state is None:
            self._save_system_state(state)
        return sent_count

    def _message_enabled(self, settings: Dict[str, object], category: str) -> bool:
        mapping = {
            "TEACHER_QA": "allowAiTutor",
            "AI_TUTOR": "allowAiTutor",
            "AI_MARKING": "allowAiTutor",
            "SYSTEM_NOTICE": "allowSystemNotice",
            "REVIEW_NOTICE": "allowReviewNotice",
            "STUDY_REMINDER": "allowStudyReminder",
            "WEEKLY_REPORT": "allowWeeklyReport",
            "POINTS_NOTICE": "allowPointsNotice",
        }
        return bool(settings.get(mapping.get(category, "allowSystemNotice"), True))
