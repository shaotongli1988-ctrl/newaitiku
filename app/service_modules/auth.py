from __future__ import annotations

from app.service_shared import *


class AuthServiceMixin:
    def resolve_actor_assigned_scope(self, user_id: str) -> Dict[str, str]:
        user = self.repository.get_user_by_id(str(user_id or "").strip())
        ext_json = self._load_json_object(str(user.get("extJson", "{}"))) if user else {}
        exam_category_code, joint_exam_group_code = self._resolve_assigned_scope_codes(str(user_id or "").strip(), ext_json)
        return {
            "exam_category_code": exam_category_code,
            "joint_exam_group_code": joint_exam_group_code,
        }

    def assert_actor_enabled(self, actor: Actor) -> Dict[str, object]:
        if actor.role == ROLE_SUPER_ADMIN:
            user = self.repository.get_user_by_id(actor.user_id)
            if not user:
                raise forbidden("当前账号未开通或角色配置不匹配。")
            ext_json = self._load_json_object(str(user.get("extJson", "{}")))
            if normalize_role(str(ext_json.get("role", ""))) != ROLE_SUPER_ADMIN:
                raise forbidden("当前账号未开通或角色配置不匹配。")
            if str(user.get("status", "")) != "ENABLED":
                raise forbidden("当前账号已停用，请联系管理员。")
            permissions = ext_json.get("permissions", [])
            return {
                "userId": str(user.get("id", "")),
                "role": ROLE_SUPER_ADMIN,
                "enabled": True,
                "permissions": permissions if isinstance(permissions, list) else [],
            }

        managed_user = self._get_managed_user(actor.user_id)
        if not managed_user or normalize_role(str(managed_user.get("role", ""))) != actor.role:
            raise forbidden("当前账号未开通或角色配置不匹配。")
        if not managed_user.get("enabled", True):
            raise forbidden("当前账号已停用，请联系管理员。")
        return managed_user

    def assert_actor_permission(self, actor: Actor, permission_key: str) -> Dict[str, object]:
        managed_user = self.assert_actor_enabled(actor)
        if actor.role == ROLE_SUPER_ADMIN:
            return managed_user
        if actor.role == ROLE_STUDENT:
            return managed_user
        permissions = managed_user.get("permissions", [])
        if permission_key and permission_key not in permissions:
            raise forbidden(f"当前账号缺少 {permission_key} 权限。")
        return managed_user

    def send_sms_code(self, payload: Dict[str, object]) -> Dict[str, object]:
        request = parse_sms_code_request_model(payload).model_dump()
        phone = request["phone"]
        purpose = request["purpose"]
        now = time.time()
        last = self._sms_codes.get(phone, {})
        last_send_at = float(last.get("sentAt", 0.0))
        if now - last_send_at < 60:
            raise validation_failed("验证码发送过于频繁，请稍后再试。")
        history = [stamp for stamp in self._sms_request_timestamps.get(phone, []) if now - stamp < 3600]
        if len(history) >= 5:
            raise validation_failed("同一手机号 1 小时内最多获取 5 次验证码。")
        code = f"{(uuid.uuid4().int % 900000) + 100000:06d}"
        self._sms_codes[phone] = {
            "code": code,
            "purpose": purpose,
            "expireAt": now + 300,
            "sentAt": now,
        }
        history.append(now)
        self._sms_request_timestamps[phone] = history
        return {
            "phone": phone,
            "purpose": purpose,
            "expireInSec": 300,
            "resendInSec": 60,
            "devCode": code,
        }

    def register_user(self, payload: Dict[str, object]) -> Dict[str, object]:
        request = parse_auth_register_model(payload).model_dump()
        self._verify_sms_code(request["phone"], "register", request["smsCode"])
        if self.repository.get_user_by_phone(request["phone"]):
            raise validation_failed("该手机号已注册，请直接登录。")
        role = normalize_role(request["role"])
        if role not in ALL_ROLES:
            raise validation_failed("role 不合法。")
        if role == ROLE_STUDENT and (not request["examCategoryCode"] or not request["jointExamGroupCode"]):
            raise validation_failed("学生注册必须填写 examCategoryCode 与 jointExamGroupCode。")
        now = self._now_iso()
        user_id = self._new_user_id(role)
        ext_json = {
            "role": role,
            "name": request["name"],
            "permissions": self._default_permissions_for_role(role),
            "vocationalMajor": request["vocationalMajor"],
            "prepStage": request["prepStage"],
            "employeeNo": request["employeeNo"],
            "createTime": now,
            "updateTime": now,
        }
        if role != ROLE_STUDENT:
            ext_json["examCategoryCode"] = request["examCategoryCode"]
            ext_json["jointExamGroupCode"] = request["jointExamGroupCode"]
        user_payload = {
            "id": user_id,
            "phone": request["phone"],
            "password": self._hash_password(request["password"]),
            "status": "ENABLED" if role == ROLE_STUDENT else "DISABLED",
            "extJson": self._dump_json(ext_json),
            "createTime": now,
            "updateTime": now,
        }
        self.repository.create_user(user_payload)
        if role == ROLE_STUDENT:
            self.repository.set_student_profile_selection(
                user_id,
                request["examCategoryCode"],
                request["jointExamGroupCode"],
                now,
            )
            self.repository.set_student_profile_bio(
                user_id,
                request["vocationalMajor"],
                request["prepStage"],
                now,
            )
        self._upsert_sms_auth_binding(user_id, request["phone"], now)
        return {
            "userId": user_id,
            "role": role,
            "status": user_payload["status"],
            "auditRequired": role != ROLE_STUDENT,
        }

    def login_by_password(self, payload: Dict[str, object], client_ip: str = "") -> Dict[str, object]:
        request = parse_auth_login_password_model(payload).model_dump()
        normalized_ip = str(client_ip or "").strip() or "unknown"
        self._assert_password_login_allowed(request["phone"], normalized_ip)
        user = self.repository.get_user_by_phone(request["phone"])
        if not user:
            self._record_password_login_failure(request["phone"], normalized_ip)
            raise forbidden("账号或密码错误。")
        if not self._verify_password(request["password"], str(user["password"])):
            self._record_password_login_failure(request["phone"], normalized_ip)
            raise forbidden("账号或密码错误。")
        self._clear_password_login_failures(request["phone"])
        return self._build_login_response(user)

    def login_by_sms(self, payload: Dict[str, object]) -> Dict[str, object]:
        request = parse_auth_login_sms_model(payload).model_dump()
        self._verify_sms_code(request["phone"], "login", request["smsCode"])
        user = self.repository.get_user_by_phone(request["phone"])
        if not user:
            raise not_found("账号不存在，请先注册。")
        return self._build_login_response(user)

    def reset_password(self, payload: Dict[str, object]) -> Dict[str, object]:
        request = parse_auth_password_reset_model(payload).model_dump()
        self._verify_sms_code(request["phone"], "reset_password", request["smsCode"])
        user = self.repository.get_user_by_phone(request["phone"])
        if not user:
            raise not_found("账号不存在。")
        updated = dict(user)
        updated["password"] = self._hash_password(request["newPassword"])
        updated["updateTime"] = self._now_iso()
        self.repository.update_user(updated)
        return {"userId": updated["id"]}

    def resolve_actor_token(self, token: str) -> Optional[Actor]:
        session = self._auth_tokens.get(token)
        if not session:
            return None
        if float(session.get("expireAt", 0.0)) < time.time():
            self._auth_tokens.pop(token, None)
            return None
        return Actor(
            role=str(session["role"]),
            user_id=str(session["userId"]),
            assigned_joint_group_code=str(session.get("assignedJointGroupCode", "")).strip(),
        )

    def revoke_token(self, token: str) -> None:
        self._auth_tokens.pop(token, None)

    def whoami(self, actor: Actor) -> Dict[str, object]:
        user = self.repository.get_user_by_id(actor.user_id)
        if not user:
            raise not_found("账号不存在。")
        ext_json = self._load_json_object(str(user["extJson"]))
        role = normalize_role(str(ext_json.get("role", actor.role)))
        managed_user = self._get_managed_user(user["id"])
        managed_permissions = managed_user.get("permissions", []) if isinstance(managed_user, dict) else []
        ext_permissions = ext_json.get("permissions", [])
        permissions = managed_permissions if isinstance(managed_permissions, list) else ext_permissions
        assigned_exam_category_code, assigned_joint_group_code = self._resolve_assigned_scope_codes(str(user["id"]), ext_json)
        return {
            "userId": user["id"],
            "role": role,
            "name": ext_json.get("name", ""),
            "phone": user["phone"],
            "status": user["status"],
            "permissions": permissions if isinstance(permissions, list) else [],
            "examCategoryCode": assigned_exam_category_code,
            "jointExamGroupCode": assigned_joint_group_code,
            "assignedExamCategoryCode": assigned_exam_category_code,
            "assignedJointGroupCode": assigned_joint_group_code,
            "assigned_exam_category_code": assigned_exam_category_code,
            "assigned_joint_group_code": assigned_joint_group_code,
        }

    def list_subjects(self) -> List[Dict[str, Optional[str]]]:
        return self.repository.list_subjects()

    def list_my_classes(self, actor: Actor) -> List[Dict[str, object]]:
        if actor.role not in {ROLE_TEACHER, ROLE_SUPER_ADMIN}:
            return []

        managed_user = self._get_managed_user(actor.user_id) or {}
        teacher_exam_category_code = str(managed_user.get("examCategoryCode", "")).strip()
        teacher_joint_exam_group_code = str(managed_user.get("jointExamGroupCode", "")).strip()

        class_map: Dict[str, Dict[str, object]] = {}
        for item in self._managed_users():
            if normalize_role(str(item.get("role", ""))) != ROLE_STUDENT:
                continue
            if not bool(item.get("enabled", True)):
                continue
            exam_category_code = str(item.get("examCategoryCode", "")).strip()
            class_id = str(item.get("jointExamGroupCode", "")).strip()
            if not class_id:
                continue
            if actor.role == ROLE_TEACHER:
                if teacher_exam_category_code and exam_category_code != teacher_exam_category_code:
                    continue
                if teacher_joint_exam_group_code and class_id != teacher_joint_exam_group_code:
                    continue

            joint_exam_group = get_joint_exam_group(class_id)
            class_name = str(joint_exam_group.get("jointExamGroupName", "")).strip() if joint_exam_group else ""
            if not class_name:
                class_name = class_id
            row = class_map.setdefault(
                class_id,
                {
                    "class_id": class_id,
                    "class_name": class_name,
                    "exam_category_code": exam_category_code,
                    "student_count": 0,
                },
            )
            row["student_count"] = int(row.get("student_count", 0)) + 1

        rows = sorted(
            class_map.values(),
            key=lambda item: (
                str(item.get("exam_category_code", "")),
                str(item.get("class_name", "")),
                str(item.get("class_id", "")),
            ),
        )
        return [
            {
                **item,
                "classId": item["class_id"],
                "className": item["class_name"],
                "examCategoryCode": item["exam_category_code"],
                "studentCount": item["student_count"],
            }
            for item in rows
        ]
