from __future__ import annotations

from app.service_shared import *


class MessageServiceMixin:
    def list_messages(self, filters: Dict[str, str], page: int, size: int, actor: Actor) -> Tuple[List[Dict[str, object]], int]:
        self._dispatch_due_scheduled_messages()
        messages = self._filter_messages_for_actor(self._system_messages(), actor)
        messages = self._apply_message_filters(messages, filters)
        messages.sort(key=lambda item: item["createTime"], reverse=True)
        paged, total = self._paginate_items(messages, page, size)
        return paged, total

    def mark_message_read(self, message_id: str, actor: Actor) -> Dict[str, object]:
        system_state = self._load_system_state()
        if not self._mark_message_read_in_state(system_state, message_id, actor.user_id):
            raise not_found("消息不存在。")
        self._save_system_state(system_state)
        return {"messageId": message_id, "unreadCount": self._count_unread_messages(actor.user_id)}

    def mark_messages_read_batch(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        message_ids_raw = payload.get("messageIds", [])
        if not isinstance(message_ids_raw, list):
            raise validation_failed("messageIds 必须是数组。")
        message_ids = []
        for value in message_ids_raw:
            message_id = str(value).strip()
            if message_id and message_id not in message_ids:
                message_ids.append(message_id)
        if not message_ids:
            raise validation_failed("messageIds 不能为空。")
        system_state = self._load_system_state()
        marked_count = 0
        for message_id in message_ids:
            if self._mark_message_read_in_state(system_state, message_id, actor.user_id):
                marked_count += 1
        if marked_count <= 0:
            raise not_found("未找到可标记的消息。")
        self._save_system_state(system_state)
        return {"markedCount": marked_count, "unreadCount": self._count_unread_messages(actor.user_id)}

    def get_message_unread_summary(self, actor: Actor) -> Dict[str, object]:
        return {
            "userId": actor.user_id,
            "unreadCount": self._count_unread_messages(actor.user_id),
        }

    def get_message_settings(self, actor: Actor) -> Dict[str, object]:
        return self._message_settings_for_user(actor.user_id)

    def save_message_settings(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        settings = parse_message_settings_model(payload).model_dump()
        self._save_message_settings_value(actor.user_id, settings)
        return settings

    def send_messages(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        self._dispatch_due_scheduled_messages()
        message = parse_send_message_model(payload).model_dump()
        target_user_ids = self._resolve_message_target_user_ids(message)
        invalid_user_ids = self._invalid_message_target_user_ids(target_user_ids)
        if invalid_user_ids:
            raise validation_failed(f"以下账号不存在或已停用：{', '.join(sorted(invalid_user_ids))}。")
        send_at = self._parse_optional_send_at(message.get("sendAt", ""))
        trace_id = f"msg-send-{uuid.uuid4().hex[:10]}"
        if send_at and send_at > datetime.now(timezone.utc):
            schedule_id = self._create_message_schedule(message, target_user_ids, actor.user_id, trace_id, send_at)
            self._append_message_send_history(
                {
                    "traceId": trace_id,
                    "scheduleId": schedule_id,
                    "senderUserId": actor.user_id,
                    "targetMode": message["targetMode"],
                    "targetCount": len(target_user_ids),
                    "category": message["category"],
                    "title": message["title"],
                    "sendAt": self._to_iso_z(send_at),
                    "status": "SCHEDULED",
                    "createTime": self._now_iso(),
                }
            )
            return {
                "sentCount": 0,
                "scheduledCount": len(target_user_ids),
                "scheduleId": schedule_id,
                "traceId": trace_id,
            }
        sent_count = self._dispatch_message_payload(
            target_user_ids,
            message["category"],
            message["title"],
            message["content"],
            sender_user_id=actor.user_id,
            trace_id=trace_id,
            send_at=self._now_iso(),
        )
        self._append_message_send_history(
            {
                "traceId": trace_id,
                "scheduleId": "",
                "senderUserId": actor.user_id,
                "targetMode": message["targetMode"],
                "targetCount": len(target_user_ids),
                "category": message["category"],
                "title": message["title"],
                "sendAt": self._now_iso(),
                "status": "SENT",
                "createTime": self._now_iso(),
            }
        )
        return {"sentCount": sent_count, "traceId": trace_id}

    def list_message_send_history(self, page: int, size: int, actor: Actor) -> Tuple[List[Dict[str, object]], int]:
        self._dispatch_due_scheduled_messages()
        history = self.repository.list_message_send_history_by_sender(actor.user_id)
        history.sort(key=lambda item: str(item.get("createTime", "")), reverse=True)
        return self._paginate_items(history, page, size)

    def recall_message_send(self, trace_id: str, actor: Actor) -> Dict[str, object]:
        trace_id = trace_id.strip()
        if not trace_id:
            raise validation_failed("traceId 不能为空。")
        self._dispatch_due_scheduled_messages()
        now = datetime.now(timezone.utc)
        system_state = self._load_system_state()
        history_item = self.repository.get_message_send_history_payload(trace_id)
        if not history_item:
            raise not_found("发送记录不存在。")
        if str(history_item.get("senderUserId", "")) != actor.user_id:
            raise forbidden("当前用户不可撤回该发送记录。")
        if str(history_item.get("status", "")) == "RECALLED":
            raise validation_failed("该发送记录已撤回。")
        sent_at_text = str(history_item.get("sendAt", ""))
        sent_at = self._parse_optional_send_at(sent_at_text)
        if sent_at and now - sent_at > timedelta(minutes=10):
            raise validation_failed("已超过 10 分钟撤回时效。")

        recalled_count = 0
        for row in system_state["messages"]:
            if str(row.get("sendTraceId", "")) != trace_id:
                continue
            if row.get("isRead"):
                continue
            row["isRecalled"] = True
            row["recalledAt"] = self._now_iso()
            recalled_count += 1

        schedules = list(system_state.get("messageSchedules", []))
        for schedule in schedules:
            if str(schedule.get("traceId", "")) == trace_id and str(schedule.get("status", "")) == "SCHEDULED":
                schedule["status"] = "CANCELLED"
                schedule["cancelledAt"] = self._now_iso()
                recalled_count += int(schedule.get("targetCount", 0))

        system_state["messageSchedules"] = schedules
        self._save_system_state(system_state)
        history_item["status"] = "RECALLED"
        history_item["recalledAt"] = self._now_iso()
        history_item["updateTime"] = str(history_item["recalledAt"])
        self.repository.upsert_message_send_history_payload(history_item)
        return {"traceId": trace_id, "recalledCount": recalled_count}

    def list_teacher_qa_threads(
        self,
        filters: Dict[str, str],
        page: int,
        size: int,
        actor: Actor,
    ) -> Tuple[List[Dict[str, object]], int]:
        system_state = self._load_system_state()
        threads = []
        status_filter = str(filters.get("status", "")).strip().upper()
        subject_filter = str(filters.get("subjectCode", "")).strip().upper()
        for thread in self._teacher_qa_threads(system_state):
            if not self._can_access_teacher_qa_thread(thread, actor):
                continue
            if status_filter and str(thread.get("status", "")).strip().upper() != status_filter:
                continue
            if subject_filter and str(thread.get("subjectCode", "")).strip().upper() != subject_filter:
                continue
            threads.append(self._build_teacher_qa_thread_summary(thread, actor))
        threads.sort(
            key=lambda item: (
                str(item.get("lastReplyTime") or item.get("updateTime") or ""),
                str(item.get("threadId", "")),
            ),
            reverse=True,
        )
        return self._paginate_items(threads, page, size)

    def get_teacher_qa_thread(self, thread_id: str, actor: Actor) -> Dict[str, object]:
        normalized_thread_id = str(thread_id or "").strip()
        if not normalized_thread_id:
            raise validation_failed("threadId 不能为空。")
        system_state = self._load_system_state()
        thread = self._find_teacher_qa_thread(system_state, normalized_thread_id)
        if not thread:
            raise not_found("答疑会话不存在。")
        if not self._can_access_teacher_qa_thread(thread, actor):
            raise forbidden("当前账号无权访问该答疑会话。")
        if actor.role == ROLE_STUDENT:
            thread["studentUnreadCount"] = 0
        else:
            thread["teacherUnreadCount"] = 0
        thread["updateTime"] = self._now_iso()
        self._save_system_state(system_state)
        return self._build_teacher_qa_thread_detail(thread, actor)

    def create_teacher_qa_thread(
        self,
        payload: Dict[str, object],
        attachments: Optional[List[Tuple[str, bytes, str]]] = None,
        actor: Actor = Actor(role=ROLE_STUDENT, user_id="", assigned_joint_group_code=""),
    ) -> Dict[str, object]:
        if actor.role != ROLE_STUDENT:
            raise forbidden("仅学生可以发起老师答疑。")
        subject_code = str(payload.get("subjectCode", "")).strip().upper()
        title = str(payload.get("title", "")).strip()
        content = str(payload.get("content", "")).strip()
        if not subject_code:
            raise validation_failed("subjectCode 不能为空。")
        if not title:
            raise validation_failed("title 不能为空。")
        if not content and not attachments:
            raise validation_failed("问题描述与图片至少填写一项。")

        available_subjects = self._teacher_qa_subject_options_for_actor(actor)
        matched_subject = next(
            (item for item in available_subjects if str(item.get("subjectCode", "")).strip().upper() == subject_code),
            None,
        )
        if not matched_subject:
            raise validation_failed("subjectCode 不属于当前学生账号可提问范围。")

        classification = self._classify_teacher_qa_knowledge(subject_code, f"{title}\n{content}", actor)
        teacher_profile = self._select_teacher_for_teacher_qa(actor)
        student_profile = self._teacher_qa_student_profile(actor)
        now = self._now_iso()
        thread_id = f"teacher-qa-{uuid.uuid4().hex[:10]}"
        message_id = f"teacher-qa-message-{uuid.uuid4().hex[:10]}"
        stored_attachments = self._store_teacher_qa_attachments(thread_id, attachments or [])
        message_row = {
            "messageId": message_id,
            "senderRole": ROLE_STUDENT,
            "senderUserId": actor.user_id,
            "senderName": str(student_profile.get("name", "")),
            "content": content,
            "attachments": stored_attachments,
            "createTime": now,
        }
        thread = {
            "threadId": thread_id,
            "title": title,
            "status": "PENDING_TEACHER",
            "studentUserId": actor.user_id,
            "studentName": str(student_profile.get("name", "")),
            "studentPhone": str(student_profile.get("phone", "")),
            "examCategoryCode": str(student_profile.get("examCategoryCode", "")),
            "jointExamGroupCode": str(student_profile.get("jointExamGroupCode", "")),
            "vocationalMajor": str(student_profile.get("vocationalMajor", "")),
            "assignedTeacherUserId": str(teacher_profile.get("userId", "")),
            "assignedTeacherName": str(teacher_profile.get("name", "")),
            "subjectCode": subject_code,
            "subjectName": str(matched_subject.get("subjectName", subject_code)),
            "knowledgeId": str(classification.get("knowledgeId", "")),
            "knowledgePathIds": list(classification.get("knowledgePathIds", [])),
            "knowledgePathLabels": list(classification.get("knowledgePathLabels", [])),
            "knowledgePathLabel": str(classification.get("knowledgePathLabel", "")),
            "category": "TEACHER_QA",
            "teacherUnreadCount": 1,
            "studentUnreadCount": 0,
            "latestMessagePreview": self._teacher_qa_message_preview(content, stored_attachments),
            "latestSenderRole": ROLE_STUDENT,
            "messages": [message_row],
            "createTime": now,
            "updateTime": now,
            "lastReplyTime": now,
        }
        system_state = self._load_system_state()
        system_state.setdefault("teacherQaThreads", [])
        system_state["teacherQaThreads"].append(thread)
        self._save_system_state(system_state)
        self._push_message(
            [str(teacher_profile.get("userId", ""))],
            "TEACHER_QA",
            f"学生答疑待处理：{title}",
            f"{student_profile.get('name', '学生')} 发起了老师答疑，请及时查看并回复。",
            sender_user_id=actor.user_id,
        )
        return self._build_teacher_qa_thread_detail(thread, actor)

    def reply_teacher_qa_thread(
        self,
        thread_id: str,
        payload: Dict[str, object],
        attachments: Optional[List[Tuple[str, bytes, str]]] = None,
        actor: Actor = Actor(role=ROLE_STUDENT, user_id="", assigned_joint_group_code=""),
    ) -> Dict[str, object]:
        normalized_thread_id = str(thread_id or "").strip()
        if not normalized_thread_id:
            raise validation_failed("threadId 不能为空。")
        content = str(payload.get("content", "")).strip()
        if not content and not attachments:
            raise validation_failed("回复内容与图片至少填写一项。")

        system_state = self._load_system_state()
        thread = self._find_teacher_qa_thread(system_state, normalized_thread_id)
        if not thread:
            raise not_found("答疑会话不存在。")
        if not self._can_access_teacher_qa_thread(thread, actor):
            raise forbidden("当前账号无权回复该答疑会话。")

        now = self._now_iso()
        stored_attachments = self._store_teacher_qa_attachments(normalized_thread_id, attachments or [])
        sender_profile = self.whoami(actor)
        thread["messages"].append(
            {
                "messageId": f"teacher-qa-message-{uuid.uuid4().hex[:10]}",
                "senderRole": actor.role,
                "senderUserId": actor.user_id,
                "senderName": str(sender_profile.get("name", "")),
                "content": content,
                "attachments": stored_attachments,
                "createTime": now,
            }
        )
        thread["latestMessagePreview"] = self._teacher_qa_message_preview(content, stored_attachments)
        thread["latestSenderRole"] = actor.role
        thread["lastReplyTime"] = now
        thread["updateTime"] = now

        if actor.role == ROLE_STUDENT:
            thread["status"] = "PENDING_TEACHER"
            thread["teacherUnreadCount"] = int(thread.get("teacherUnreadCount", 0) or 0) + 1
            target_user_id = str(thread.get("assignedTeacherUserId", ""))
            notification_title = f"学生追问：{thread.get('title', '老师答疑')}"
            notification_content = f"{thread.get('studentName', '学生')} 更新了答疑内容，请及时查看。"
        else:
            thread["status"] = "ANSWERED"
            thread["studentUnreadCount"] = int(thread.get("studentUnreadCount", 0) or 0) + 1
            target_user_id = str(thread.get("studentUserId", ""))
            notification_title = f"老师已回复：{thread.get('title', '老师答疑')}"
            notification_content = f"{sender_profile.get('name', '老师')} 已回复你的问题，点击继续查看。"

        self._save_system_state(system_state)
        if target_user_id:
            self._push_message(
                [target_user_id],
                "TEACHER_QA",
                notification_title,
                notification_content,
                sender_user_id=actor.user_id,
            )
        return self._build_teacher_qa_thread_detail(thread, actor)

    def resolve_teacher_qa_attachment(self, attachment_id: str, actor: Actor) -> Dict[str, str]:
        normalized_attachment_id = str(attachment_id or "").strip()
        if not normalized_attachment_id:
            raise validation_failed("attachmentId 不能为空。")
        system_state = self._load_system_state()
        for thread in self._teacher_qa_threads(system_state):
            if not self._can_access_teacher_qa_thread(thread, actor):
                continue
            for message in thread.get("messages", []):
                for attachment in message.get("attachments", []):
                    if str(attachment.get("attachmentId", "")).strip() != normalized_attachment_id:
                        continue
                    file_path = Path(str(attachment.get("storagePath", "")).strip())
                    if not file_path.exists() or not file_path.is_file():
                        raise not_found("答疑附件不存在。")
                    return {
                        "filePath": str(file_path),
                        "fileName": str(attachment.get("fileName", "")).strip() or file_path.name,
                        "mediaType": str(attachment.get("mediaType", "")).strip() or "application/octet-stream",
                    }
        raise not_found("答疑附件不存在。")

    def _teacher_qa_threads(self, system_state: Optional[Dict[str, object]] = None) -> List[Dict[str, object]]:
        state = system_state if isinstance(system_state, dict) else self._load_system_state()
        source = state.setdefault("teacherQaThreads", [])
        normalized_threads: List[Dict[str, object]] = []
        if not isinstance(source, list):
            state["teacherQaThreads"] = []
            return []
        for item in source:
            if not isinstance(item, dict):
                continue
            thread_id = str(item.get("threadId", "")).strip()
            if not thread_id:
                continue
            messages = self._normalize_teacher_qa_messages(item.get("messages", []))
            normalized_threads.append(
                {
                    "threadId": thread_id,
                    "title": str(item.get("title", "")).strip(),
                    "status": str(item.get("status", "PENDING_TEACHER")).strip() or "PENDING_TEACHER",
                    "studentUserId": str(item.get("studentUserId", "")).strip(),
                    "studentName": str(item.get("studentName", "")).strip(),
                    "studentPhone": str(item.get("studentPhone", "")).strip(),
                    "examCategoryCode": str(item.get("examCategoryCode", "")).strip(),
                    "jointExamGroupCode": str(item.get("jointExamGroupCode", "")).strip(),
                    "vocationalMajor": str(item.get("vocationalMajor", "")).strip(),
                    "assignedTeacherUserId": str(item.get("assignedTeacherUserId", "")).strip(),
                    "assignedTeacherName": str(item.get("assignedTeacherName", "")).strip(),
                    "subjectCode": str(item.get("subjectCode", "")).strip(),
                    "subjectName": str(item.get("subjectName", "")).strip(),
                    "knowledgeId": str(item.get("knowledgeId", "")).strip(),
                    "knowledgePathIds": [
                        str(node_id).strip()
                        for node_id in item.get("knowledgePathIds", [])
                        if str(node_id).strip()
                    ]
                    if isinstance(item.get("knowledgePathIds", []), list)
                    else [],
                    "knowledgePathLabels": [
                        str(label).strip()
                        for label in item.get("knowledgePathLabels", [])
                        if str(label).strip()
                    ]
                    if isinstance(item.get("knowledgePathLabels", []), list)
                    else [],
                    "knowledgePathLabel": str(item.get("knowledgePathLabel", "")).strip(),
                    "teacherUnreadCount": max(0, int(item.get("teacherUnreadCount", 0) or 0)),
                    "studentUnreadCount": max(0, int(item.get("studentUnreadCount", 0) or 0)),
                    "latestMessagePreview": str(item.get("latestMessagePreview", "")).strip(),
                    "latestSenderRole": str(item.get("latestSenderRole", "")).strip(),
                    "messages": messages,
                    "createTime": str(item.get("createTime", "")).strip(),
                    "updateTime": str(item.get("updateTime", "")).strip(),
                    "lastReplyTime": str(item.get("lastReplyTime", "")).strip(),
                }
            )
        state["teacherQaThreads"] = normalized_threads
        return normalized_threads

    def _normalize_teacher_qa_messages(self, rows: object) -> List[Dict[str, object]]:
        if not isinstance(rows, list):
            return []
        normalized_rows: List[Dict[str, object]] = []
        for item in rows:
            if not isinstance(item, dict):
                continue
            message_id = str(item.get("messageId", "")).strip()
            if not message_id:
                continue
            normalized_rows.append(
                {
                    "messageId": message_id,
                    "senderRole": str(item.get("senderRole", "")).strip(),
                    "senderUserId": str(item.get("senderUserId", "")).strip(),
                    "senderName": str(item.get("senderName", "")).strip(),
                    "content": str(item.get("content", "")).strip(),
                    "attachments": self._normalize_teacher_qa_attachments(item.get("attachments", [])),
                    "createTime": str(item.get("createTime", "")).strip(),
                }
            )
        return normalized_rows

    def _normalize_teacher_qa_attachments(self, rows: object) -> List[Dict[str, object]]:
        if not isinstance(rows, list):
            return []
        normalized_rows: List[Dict[str, object]] = []
        for item in rows:
            if not isinstance(item, dict):
                continue
            attachment_id = str(item.get("attachmentId", "")).strip()
            if not attachment_id:
                continue
            normalized_rows.append(
                {
                    "attachmentId": attachment_id,
                    "fileName": str(item.get("fileName", "")).strip(),
                    "mediaType": str(item.get("mediaType", "")).strip(),
                    "size": max(0, int(item.get("size", 0) or 0)),
                    "storagePath": str(item.get("storagePath", "")).strip(),
                    "url": f"/api/question-bank/messages/teacher-qa/attachments/{attachment_id}",
                }
            )
        return normalized_rows

    def _find_teacher_qa_thread(self, system_state: Dict[str, object], thread_id: str) -> Optional[Dict[str, object]]:
        normalized_thread_id = str(thread_id or "").strip()
        for item in self._teacher_qa_threads(system_state):
            if str(item.get("threadId", "")).strip() == normalized_thread_id:
                return item
        return None

    def _can_access_teacher_qa_thread(self, thread: Dict[str, object], actor: Actor) -> bool:
        if actor.role == ROLE_SUPER_ADMIN:
            return True
        if actor.role == ROLE_STUDENT:
            return str(thread.get("studentUserId", "")).strip() == actor.user_id
        return str(thread.get("assignedTeacherUserId", "")).strip() == actor.user_id

    def _build_teacher_qa_thread_summary(self, thread: Dict[str, object], actor: Actor) -> Dict[str, object]:
        return {
            "threadId": str(thread.get("threadId", "")),
            "title": str(thread.get("title", "")),
            "status": str(thread.get("status", "")),
            "studentUserId": str(thread.get("studentUserId", "")),
            "studentName": str(thread.get("studentName", "")),
            "studentPhone": str(thread.get("studentPhone", "")),
            "examCategoryCode": str(thread.get("examCategoryCode", "")),
            "jointExamGroupCode": str(thread.get("jointExamGroupCode", "")),
            "vocationalMajor": str(thread.get("vocationalMajor", "")),
            "assignedTeacherUserId": str(thread.get("assignedTeacherUserId", "")),
            "assignedTeacherName": str(thread.get("assignedTeacherName", "")),
            "subjectCode": str(thread.get("subjectCode", "")),
            "subjectName": str(thread.get("subjectName", "")),
            "knowledgeId": str(thread.get("knowledgeId", "")),
            "knowledgePathIds": list(thread.get("knowledgePathIds", [])),
            "knowledgePathLabels": list(thread.get("knowledgePathLabels", [])),
            "knowledgePathLabel": str(thread.get("knowledgePathLabel", "")),
            "latestMessagePreview": str(thread.get("latestMessagePreview", "")),
            "latestSenderRole": str(thread.get("latestSenderRole", "")),
            "unreadCount": int(
                thread.get("studentUnreadCount", 0) if actor.role == ROLE_STUDENT else thread.get("teacherUnreadCount", 0)
            ),
            "messageCount": len(thread.get("messages", [])),
            "createTime": str(thread.get("createTime", "")),
            "updateTime": str(thread.get("updateTime", "")),
            "lastReplyTime": str(thread.get("lastReplyTime", "")),
        }

    def _build_teacher_qa_thread_detail(self, thread: Dict[str, object], actor: Actor) -> Dict[str, object]:
        payload = self._build_teacher_qa_thread_summary(thread, actor)
        payload["messages"] = [
            {
                **message,
                "attachments": [
                    {
                        key: value
                        for key, value in attachment.items()
                        if key != "storagePath"
                    }
                    for attachment in message.get("attachments", [])
                ],
            }
            for message in thread.get("messages", [])
        ]
        return payload

    def _teacher_qa_message_preview(self, content: str, attachments: List[Dict[str, object]]) -> str:
        normalized = str(content or "").strip()
        if normalized:
            return normalized[:120]
        if attachments:
            return f"上传了 {len(attachments)} 张图片"
        return "新消息"

    def _teacher_qa_subject_options_for_actor(self, actor: Actor) -> List[Dict[str, str]]:
        scope = self.resolve_actor_assigned_scope(actor.user_id)
        joint_group_code = str(scope.get("joint_exam_group_code", "")).strip()
        joint_group = get_joint_exam_group(joint_group_code) if joint_group_code else None
        rows: List[Dict[str, str]] = []
        seen_codes: set[str] = set()
        for subject in PUBLIC_SUBJECTS:
            if not isinstance(subject, dict):
                continue
            subject_code = str(subject.get("subjectCode", "")).strip().upper()
            if not subject_code or subject_code in seen_codes:
                continue
            seen_codes.add(subject_code)
            rows.append(
                {
                    "subjectCode": subject_code,
                    "subjectName": str(subject.get("subjectName", "")).strip() or subject_code,
                    "subjectType": str(subject.get("subjectType", "PUBLIC")).strip() or "PUBLIC",
                }
            )
        for subject in joint_group.get("professionalSubjects", []) if isinstance(joint_group, dict) else []:
            if not isinstance(subject, dict):
                continue
            subject_code = str(subject.get("subjectCode", "")).strip().upper()
            if not subject_code or subject_code in seen_codes:
                continue
            seen_codes.add(subject_code)
            rows.append(
                {
                    "subjectCode": subject_code,
                    "subjectName": str(subject.get("subjectName", "")).strip() or subject_code,
                    "subjectType": str(subject.get("subjectType", "PROFESSIONAL")).strip() or "PROFESSIONAL",
                }
            )
        return rows

    def _teacher_qa_student_profile(self, actor: Actor) -> Dict[str, str]:
        user = self.repository.get_user_by_id(actor.user_id)
        ext_json = self._load_json_object(str(user.get("extJson", "{}"))) if user else {}
        profile = self._get_student_profile(actor.user_id)
        return {
            "name": str(ext_json.get("name", "")).strip() or actor.user_id,
            "phone": str(user.get("phone", "")).strip(),
            "examCategoryCode": str(profile.get("examCategoryCode", "")).strip(),
            "jointExamGroupCode": str(profile.get("jointExamGroupCode", "")).strip(),
            "vocationalMajor": str(profile.get("vocationalMajor", "")).strip(),
        }

    def _select_teacher_for_teacher_qa(self, actor: Actor) -> Dict[str, str]:
        teacher_rows = [
            item
            for item in self._managed_users()
            if str(item.get("role", "")).strip() == ROLE_TEACHER and bool(item.get("enabled", True))
        ]
        teacher_rows.sort(key=lambda item: str(item.get("userId", "")))
        if not teacher_rows:
            raise failed_dependency("当前暂无可用教师账号接收答疑。")
        selected = teacher_rows[0]
        return {
            "userId": str(selected.get("userId", "")).strip(),
            "name": str(selected.get("name", "")).strip() or str(selected.get("userId", "")).strip(),
        }

    def _teacher_qa_search_text(self, value: str) -> str:
        normalized = re.sub(r"[^\w\u4e00-\u9fff]+", "", str(value or "").lower())
        return normalized.strip()

    def _classify_teacher_qa_knowledge(self, subject_code: str, raw_text: str, actor: Actor) -> Dict[str, object]:
        student_profile = self._teacher_qa_student_profile(actor)
        scope_filters = {
            "policyVersionCode": POLICY_VERSION_CODE,
            "examCategoryCode": str(student_profile.get("examCategoryCode", "")),
            "jointExamGroupCode": str(student_profile.get("jointExamGroupCode", "")),
            "subjectCode": str(subject_code or "").strip().upper(),
        }
        rows = self._load_subject_knowledge_points_list(scope_filters)
        if not rows:
            return {
                "knowledgeId": "",
                "knowledgePathIds": [],
                "knowledgePathLabels": [],
                "knowledgePathLabel": "",
            }
        name_by_id = {
            str(item.get("id", "")).strip(): str(item.get("name", "")).strip()
            for item in rows
            if str(item.get("id", "")).strip()
        }
        parent_by_id = {
            str(item.get("id", "")).strip(): str(item.get("parent_id", "")).strip()
            for item in rows
            if str(item.get("id", "")).strip()
        }
        max_level = max(int(item.get("level", 0) or 0) for item in rows)
        target_level = 5 if any(int(item.get("level", 0) or 0) == 5 for item in rows) else max_level
        candidates = [item for item in rows if int(item.get("level", 0) or 0) == target_level]
        normalized_text = self._teacher_qa_search_text(raw_text)
        text_chars = set(normalized_text)

        def build_path(knowledge_id: str) -> Tuple[List[str], List[str]]:
            path_ids: List[str] = []
            seen_ids: set[str] = set()
            cursor = str(knowledge_id or "").strip()
            while cursor and cursor not in seen_ids:
                seen_ids.add(cursor)
                path_ids.append(cursor)
                cursor = parent_by_id.get(cursor, "")
            path_ids.reverse()
            path_labels = [name_by_id.get(node_id, node_id) for node_id in path_ids if name_by_id.get(node_id, node_id)]
            return path_ids, path_labels

        def candidate_score(candidate: Dict[str, object]) -> Tuple[int, str]:
            knowledge_id = str(candidate.get("id", "")).strip()
            _, path_labels = build_path(knowledge_id)
            score = 0
            for index, label in enumerate(path_labels):
                normalized_label = self._teacher_qa_search_text(label)
                if not normalized_label:
                    continue
                if normalized_label in normalized_text:
                    score += 400 if index == len(path_labels) - 1 else 90
                overlap = len(set(normalized_label).intersection(text_chars))
                score += overlap * (5 if index == len(path_labels) - 1 else 1)
            return score, " / ".join(path_labels)

        ranked = sorted(
            candidates,
            key=lambda item: (
                candidate_score(item)[0],
                candidate_score(item)[1],
            ),
            reverse=True,
        )
        selected = ranked[0] if ranked else rows[0]
        selected_id = str(selected.get("id", "")).strip()
        path_ids, path_labels = build_path(selected_id)
        return {
            "knowledgeId": selected_id,
            "knowledgePathIds": path_ids,
            "knowledgePathLabels": path_labels,
            "knowledgePathLabel": " / ".join(path_labels),
        }

    def _teacher_qa_upload_root(self) -> Path:
        root = self.repository.db_path.parent / "teacher_qa_uploads"
        root.mkdir(parents=True, exist_ok=True)
        return root

    def _store_teacher_qa_attachments(
        self,
        thread_id: str,
        attachments: List[Tuple[str, bytes, str]],
    ) -> List[Dict[str, object]]:
        if len(attachments) > 6:
            raise validation_failed("单次最多上传 6 张图片。")
        stored_rows: List[Dict[str, object]] = []
        thread_dir = self._teacher_qa_upload_root() / str(thread_id or "").strip()
        thread_dir.mkdir(parents=True, exist_ok=True)
        for file_name, file_bytes, media_type in attachments:
            normalized_name = str(file_name or "").strip() or "answer.png"
            normalized_media_type = str(media_type or "").strip().lower()
            if not normalized_media_type.startswith("image/"):
                raise validation_failed("老师答疑仅支持上传图片附件。")
            size = len(file_bytes or b"")
            if size <= 0:
                raise validation_failed("上传图片不能为空。")
            if size > 8 * 1024 * 1024:
                raise validation_failed("单张图片大小不能超过 8MB。")
            suffix = Path(normalized_name).suffix.lower() or ".png"
            attachment_id = f"teacher-qa-attachment-{uuid.uuid4().hex[:10]}"
            file_path = thread_dir / f"{attachment_id}{suffix}"
            file_path.write_bytes(file_bytes)
            stored_rows.append(
                {
                    "attachmentId": attachment_id,
                    "fileName": normalized_name,
                    "mediaType": normalized_media_type,
                    "size": size,
                    "storagePath": str(file_path),
                    "url": f"/api/question-bank/messages/teacher-qa/attachments/{attachment_id}",
                }
            )
        return stored_rows
