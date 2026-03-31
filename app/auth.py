from __future__ import annotations

# Observability note: auth flow changes should keep log/trace/metric evidence aligned with release docs.
from dataclasses import dataclass
import os
import secrets
from typing import Optional, Sequence

from fastapi import Cookie, Header, Query, Request
from fastapi.responses import RedirectResponse

from app.contracts import (
    ACCEPTED_ROLES,
    ALL_ROLES,
    ANALYTICS_OPERATE_ROLES,
    PAPER_OPERATE_ROLES,
    QUESTION_OPERATE_ROLES,
    ROLE_SUPER_ADMIN,
    ROLE_TEACHER,
    ROLE_STUDENT,
    STUDENT_OPERATE_ROLES,
    normalize_role,
)
from app.exceptions import forbidden, validation_failed
from app.exceptions import unauthorized


@dataclass(frozen=True)
class Actor:
    role: str
    user_id: str
    assigned_joint_group_code: str = ""


AUTH_COOKIE_NAME = "qbAccessToken"
CSRF_COOKIE_NAME = "qbCsrfToken"
HEADER_ACTOR_FALLBACK_ENV_KEY = "QB_ALLOW_HEADER_ACTOR_FALLBACK"

API_LOGIN_OPTIONAL_PATHS = {
    "/api/question-bank/auth/sms-code",
    "/api/question-bank/auth/register",
    "/api/question-bank/auth/login/password",
    "/api/question-bank/auth/login/sms",
    "/api/question-bank/auth/password/reset",
    "/api/question-bank/auth/logout",
}

ROLE_HOME_PATH = {
    ROLE_SUPER_ADMIN: "/admin/home",
    ROLE_TEACHER: "/teacher/home",
    ROLE_STUDENT: "/student/home",
}


def parse_bearer_token(authorization: Optional[str]) -> str:
    if not isinstance(authorization, str):
        return ""
    return authorization.replace("Bearer ", "").strip()


def is_production_env() -> bool:
    return os.getenv("QB_ENV", "").strip().lower() in {"prod", "production"}


def is_question_bank_api_path(path: str) -> bool:
    return str(path or "").strip().startswith("/api/question-bank/")


def requires_authenticated_question_bank_api(path: str) -> bool:
    normalized = str(path or "").strip()
    return is_question_bank_api_path(normalized) and normalized not in API_LOGIN_OPTIONAL_PATHS


def header_actor_fallback_enabled() -> bool:
    raw = os.getenv(HEADER_ACTOR_FALLBACK_ENV_KEY, "").strip().lower()
    if raw not in {"1", "true", "yes", "on"}:
        return False
    return not is_production_env()


def _resolve_actor_from_token(
    request: Request,
    authorization: Optional[str],
    cookie_token: Optional[str],
) -> Optional[Actor]:
    token = parse_bearer_token(authorization)
    if not token and isinstance(cookie_token, str):
        token = cookie_token.strip()
    if not token:
        return None
    service = getattr(request.app.state, "service", None)
    if service:
        actor = service.resolve_actor_token(token)
        if actor:
            return actor
    raise unauthorized("登录态已失效，请重新登录。")


def _apply_injected_joint_group_scope(
    request: Request,
    actor: Actor,
    injected_joint_group_code: str,
) -> Actor:
    normalized_injected = str(injected_joint_group_code or "").strip()
    if not normalized_injected:
        return actor

    assigned_joint_group_code = str(actor.assigned_joint_group_code or "").strip()
    if not assigned_joint_group_code:
        service = getattr(request.app.state, "service", None)
        if service and hasattr(service, "resolve_actor_assigned_scope"):
            try:
                scope = service.resolve_actor_assigned_scope(actor.user_id)
            except Exception:
                scope = {}
            if isinstance(scope, dict):
                assigned_joint_group_code = str(scope.get("joint_exam_group_code", "")).strip()

    if assigned_joint_group_code and normalized_injected != assigned_joint_group_code:
        raise forbidden("X-Joint-Group 与账号分配专业组不一致。")

    return Actor(
        role=actor.role,
        user_id=actor.user_id,
        assigned_joint_group_code=normalized_injected,
    )


def get_actor(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    qb_access_token: Optional[str] = Cookie(default=None, alias=AUTH_COOKIE_NAME),
    qb_role: Optional[str] = Cookie(default=None, alias="qbRole"),
    qb_user_id: Optional[str] = Cookie(default=None, alias="qbUserId"),
    x_role: Optional[str] = Header(default=None),
    x_user_id: Optional[str] = Header(default=None),
    x_joint_group: Optional[str] = Header(default=None, alias="X-Joint-Group"),
    role: Optional[str] = Query(default=None),
    userId: Optional[str] = Query(default=None),
) -> Actor:
    request_path = str(request.url.path or "").strip()
    requires_authenticated_api = requires_authenticated_question_bank_api(request_path)
    normalized_injected_joint_group = str(x_joint_group or "").strip()
    token_actor = _resolve_actor_from_token(request, authorization, qb_access_token)
    if token_actor:
        return _apply_injected_joint_group_scope(request, token_actor, normalized_injected_joint_group)
    if not isinstance(x_role, str):
        x_role = None
    if not isinstance(x_user_id, str):
        x_user_id = None
    if not isinstance(qb_role, str):
        qb_role = None
    if not isinstance(qb_user_id, str):
        qb_user_id = None
    if not isinstance(role, str):
        role = None
    if not isinstance(userId, str):
        userId = None
    fallback_enabled = header_actor_fallback_enabled()
    if requires_authenticated_api:
        if not fallback_enabled:
            raise unauthorized("该模块仅支持登录态访问，请先登录。")
        if not str(x_role or role or qb_role or "").strip() or not str(x_user_id or userId or qb_user_id or "").strip():
            raise unauthorized("该模块仅支持登录态访问，请先登录。")
    raw_role = str(x_role or role or qb_role or ("" if requires_authenticated_api else ROLE_TEACHER)).strip()
    resolved_role = normalize_role(raw_role)
    if requires_authenticated_api:
        resolved_user_id = x_user_id or userId or qb_user_id or ""
    else:
        default_user_id = "teacher-001"
        if resolved_role == ROLE_SUPER_ADMIN:
            default_user_id = "admin-001"
        elif resolved_role == ROLE_STUDENT:
            default_user_id = "student-001"
        resolved_user_id = x_user_id or userId or qb_user_id or default_user_id
    if raw_role not in ACCEPTED_ROLES or resolved_role not in ALL_ROLES:
        raise validation_failed("角色不合法，请使用 super_admin、teacher 或 student。")
    if not resolved_user_id.strip():
        raise validation_failed("userId 不能为空。")
    assigned_joint_group_code = ""
    service = getattr(request.app.state, "service", None)
    if service and hasattr(service, "resolve_actor_assigned_scope"):
        try:
            scope = service.resolve_actor_assigned_scope(resolved_user_id.strip())
            if isinstance(scope, dict):
                assigned_joint_group_code = str(scope.get("joint_exam_group_code", "")).strip()
        except Exception:
            assigned_joint_group_code = ""
    if normalized_injected_joint_group and assigned_joint_group_code and normalized_injected_joint_group != assigned_joint_group_code:
        raise forbidden("X-Joint-Group 与账号分配专业组不一致。")
    return Actor(
        role=resolved_role,
        user_id=resolved_user_id.strip(),
        assigned_joint_group_code=normalized_injected_joint_group or assigned_joint_group_code,
    )


def get_token_actor(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    qb_access_token: Optional[str] = Cookie(default=None, alias=AUTH_COOKIE_NAME),
) -> Actor:
    actor = _resolve_actor_from_token(request, authorization, qb_access_token)
    if actor:
        return actor
    raise unauthorized("该模块仅支持登录态访问，请先登录。")


def get_optional_token_actor(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    qb_access_token: Optional[str] = Cookie(default=None, alias=AUTH_COOKIE_NAME),
) -> Optional[Actor]:
    actor = _resolve_actor_from_token(request, authorization, qb_access_token)
    if actor:
        return actor
    return None


def require_admin_csrf(
    authorization: Optional[str] = Header(default=None),
    csrf_token: Optional[str] = Header(default=None, alias="X-CSRF-Token"),
    qb_csrf_token: Optional[str] = Cookie(default=None, alias=CSRF_COOKIE_NAME),
) -> None:
    if parse_bearer_token(authorization):
        return
    header_token = str(csrf_token or "").strip()
    cookie_token = str(qb_csrf_token or "").strip()
    if not header_token or not cookie_token:
        raise forbidden("安全校验失败，请刷新页面后重试。")
    if not secrets.compare_digest(header_token, cookie_token):
        raise forbidden("安全校验失败，请刷新页面后重试。")


def require_question_operator(actor: Actor) -> Actor:
    if actor.role not in QUESTION_OPERATE_ROLES:
        raise forbidden("当前角色不可进入题库管理。")
    return actor


def require_paper_operator(actor: Actor) -> Actor:
    if actor.role == ROLE_SUPER_ADMIN:
        return actor
    if actor.role not in PAPER_OPERATE_ROLES:
        raise forbidden("当前角色不可进入试卷管理。")
    return actor


def require_analytics_operator(actor: Actor) -> Actor:
    if actor.role == ROLE_SUPER_ADMIN:
        return actor
    if actor.role not in ANALYTICS_OPERATE_ROLES:
        raise forbidden("当前角色不可进入学情管理。")
    return actor


def require_student(actor: Actor) -> Actor:
    if actor.role == ROLE_SUPER_ADMIN:
        return actor
    if actor.role not in STUDENT_OPERATE_ROLES:
        raise forbidden("当前角色不可进入学生刷题页。")
    return actor


def require_super_admin(actor: Actor) -> Actor:
    if actor.role != ROLE_SUPER_ADMIN:
        raise forbidden("仅总管理员可进入该模块。")
    return actor


def require_admin_api_access(actor: Actor, request: Request) -> Actor:
    path = str(request.url.path or "").strip()
    if path.startswith("/api/question-bank/admin/"):
        if path in {
            "/api/question-bank/admin/users",
            "/api/question-bank/admin/students/import",
            "/api/question-bank/admin/students/export",
        }:
            if actor.role in {ROLE_SUPER_ADMIN, ROLE_TEACHER}:
                return actor
            raise forbidden("仅教师或总管理员可进入该模块。")
        return require_super_admin(actor)
    return actor


def role_home_path(role: str) -> str:
    normalized = normalize_role(role)
    return ROLE_HOME_PATH.get(normalized, ROLE_HOME_PATH[ROLE_TEACHER])


def role_home_url(actor: Actor) -> str:
    path = role_home_path(actor.role)
    if actor.role == ROLE_SUPER_ADMIN:
        return path
    return f"{path}?role={actor.role}&userId={actor.user_id}"


def redirect_for_page_role(actor: Actor, allowed_roles: Sequence[str]) -> Optional[RedirectResponse]:
    normalized_allowed = {normalize_role(item) for item in allowed_roles}
    if actor.role == ROLE_SUPER_ADMIN:
        if ROLE_SUPER_ADMIN in normalized_allowed:
            return None
        return RedirectResponse(url=role_home_url(actor), status_code=302)
    if actor.role in normalized_allowed:
        return None
    return RedirectResponse(url=role_home_url(actor), status_code=302)
