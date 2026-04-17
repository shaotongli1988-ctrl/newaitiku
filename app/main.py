from __future__ import annotations

import os
from pathlib import Path
import secrets
from typing import List, Optional, Union
from urllib.parse import urlencode

from fastapi import Body, Depends, FastAPI, File, Form, Header, HTTPException, Query, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, Field

from app.content_baseline import POLICY_VERSION_CODE, subject_code_from_subject_id
from app.auth import (
    AUTH_COOKIE_NAME,
    CSRF_COOKIE_NAME,
    Actor,
    get_actor,
    get_optional_token_actor,
    get_token_actor,
    parse_bearer_token,
    redirect_for_page_role,
    require_admin_csrf,
    require_admin_api_access,
    require_analytics_operator,
    require_paper_operator,
    require_question_operator,
    require_student,
    require_super_admin,
)
from app.contracts import (
    AdminManagedUserSaveRequest,
    AdminRedeemCodeBatchCreateRequest,
    AdminSyllabusVersionCreateRequest,
    AdminSyllabusWeightsSaveRequest,
    AdminStudentsImportRequest,
    AdaptivePracticeRequest,
    AdaptivePracticeResponse,
    AdminSystemSettingsSaveRequest,
    APP_TITLE,
    AuthLoginPasswordRequest,
    AuthLoginSmsRequest,
    AuthPasswordResetRequest,
    AuthRegisterRequest,
    AuthSmsCodeRequest,
    BaseResponse,
    BatchQuestionCreateRequest,
    ExamTaskCreateRequest,
    LearningMethodAdminSaveRequest,
    LearningMethodAdminSortRequest,
    LearningMethodAdminUpdateRequest,
    LearningMethodPracticeCompleteRequest,
    LearningMethodPracticeStartRequest,
    LearningMethodProfileAutoGenerateRequest,
    LearningMethodQuestionFeatureAutoBatchRequest,
    LearningMethodQuestionPackRecommendRequest,
    LearningMethodQuestionPackFeedbackRequest,
    KnowledgeGraphEnvelopeResponse,
    KnowledgeLayoutSaveRequest,
    KnowledgePrerequisiteUpdateRequest,
    KnowledgeWriteRequest,
    ManualPaperCreateRequest,
    MessagesReadBatchRequest,
    MessagesSendRequest,
    MessagesSettingsSaveRequest,
    PaperAutoSaveRequest,
    PaperAiGenerateRequest,
    PaperTemplateSaveRequest,
    ProfessionalTreeResponse,
    QUESTION_STATUSES,
    QUESTION_TYPES,
    ROLE_SUPER_ADMIN,
    ROLE_STUDENT,
    QuestionCreateRequest,
    QuestionDeleteBatchRequest,
    QuestionStatusBatchTransitionRequest,
    StudentProfileUpdateRequest,
    QuestionTransitionRequest,
    QuestionUpdateRequest,
    StudentAiMarkingSubmitRequest,
    StudentAiTutorAskRequest,
    StudentDiagnosisQuickStartRequest,
    StudentDiagnosisQuickSubmitRequest,
    StudentSubscriptionMockOrderConfirmRequest,
    StudentSubscriptionMockOrderCreateRequest,
    StudentSubscriptionRedeemRequest,
    StudentMockExamStartRequest,
    StudentPaperSubmitRequest,
    StudentPersonalBankToggleRequest,
    StudentPracticeSubmitRequest,
    StudentSessionSubmitRequest,
    pagination,
    success,
)
from app.db import DEFAULT_DB_PATH, init_db
from app.exceptions import QuestionBankError, question_bank_exception_handler
from app.service import QuestionBankService


class PageActor(BaseModel):
    role: str
    userId: str


class PageBootstrapResponse(BaseModel):
    route: str
    viewKey: str
    pageTitle: str
    actor: Optional[PageActor] = None
    permissions: List[str] = Field(default_factory=list)
    questionStatuses: List[str] = Field(default_factory=list)
    questionTypes: List[str] = Field(default_factory=list)
    csrfToken: Optional[str] = None


def create_app(db_path: Union[Path, str] = DEFAULT_DB_PATH) -> FastAPI:
    init_db(db_path)
    app = FastAPI(title=APP_TITLE)
    camelcase_only_query_keys = {
        "subject_code",
        "subject_id",
        "joint_exam_group_code",
        "exam_category_code",
        "chapter_code",
        "point_code",
        "knowledge_id",
        "question_ids",
        "user_id",
        "policy_version",
    }
    cors_origins = os.getenv("QB_CORS_ORIGINS", "").strip()
    allow_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
    if not allow_origins:
        allow_origins = [
            "http://localhost:4173",
            "http://127.0.0.1:4173",
            "http://localhost:4174",
            "http://127.0.0.1:4174",
            "http://localhost:4175",
            "http://127.0.0.1:4175",
            "http://localhost:4176",
            "http://127.0.0.1:4176",
            "http://localhost:4273",
            "http://127.0.0.1:4273",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:5175",
            "http://127.0.0.1:5175",
        ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.db_path = Path(db_path)
    app.state.service = QuestionBankService(db_path)
    app.state.service.preload_knowledge_tree_snapshot()
    app.add_exception_handler(QuestionBankError, question_bank_exception_handler)

    def service() -> QuestionBankService:
        return app.state.service

    def ensure_actor_ready(actor: Actor, svc: QuestionBankService, permission_key: str = "") -> None:
        if permission_key:
            svc.assert_actor_permission(actor, permission_key)
            return
        svc.assert_actor_enabled(actor)

    def ensure_admin_api_actor(request: Request, actor: Actor = Depends(get_token_actor)) -> Actor:
        return require_admin_api_access(actor, request)

    def is_production_env() -> bool:
        return os.getenv("QB_ENV", "").strip().lower() in {"prod", "production"}

    def cookie_secure_flag() -> bool:
        raw = os.getenv("QB_COOKIE_SECURE", "").strip().lower()
        if raw in {"1", "true", "yes", "on"}:
            return True
        if raw in {"0", "false", "no", "off"}:
            return False
        return is_production_env()

    def cookie_samesite_mode(secure: bool) -> str:
        raw = os.getenv("QB_COOKIE_SAMESITE", "").strip().lower()
        if raw in {"lax", "strict", "none"}:
            mode = raw
        else:
            mode = "strict" if is_production_env() else "lax"
        if mode == "none" and not secure:
            return "lax"
        return mode

    def set_csrf_cookie(response: Response, csrf_token: str, max_age: Optional[int]) -> str:
        secure = cookie_secure_flag()
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=csrf_token,
            httponly=False,
            samesite=cookie_samesite_mode(secure),
            secure=secure,
            path="/",
            max_age=max_age,
        )
        return csrf_token

    def ensure_csrf_cookie(request: Request, response: Response, max_age: Optional[int] = 12 * 3600) -> str:
        existing_csrf = request.cookies.get(CSRF_COOKIE_NAME, "").strip()
        if existing_csrf:
            return existing_csrf
        return set_csrf_cookie(response, secrets.token_urlsafe(32), max_age)

    def set_auth_cookie(response: Response, login_result: dict) -> None:
        expire_in_sec = int(login_result.get("expireInSec") or 0)
        max_age = expire_in_sec if expire_in_sec > 0 else None
        secure = cookie_secure_flag()
        response.set_cookie(
            key=AUTH_COOKIE_NAME,
            value=str(login_result.get("accessToken", "")),
            httponly=True,
            samesite=cookie_samesite_mode(secure),
            secure=secure,
            path="/",
            max_age=max_age,
        )
        set_csrf_cookie(response, secrets.token_urlsafe(32), max_age)

    def request_client_ip(request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if forwarded_for:
            return forwarded_for
        real_ip = request.headers.get("x-real-ip", "").strip()
        if real_ip:
            return real_ip
        if request.client and request.client.host:
            return request.client.host
        return "unknown"

    def frontend_dev_server_url() -> str:
        if is_production_env():
            return ""
        configured_url = str(os.getenv("QB_FRONTEND_DEV_SERVER_URL", "")).strip().rstrip("/")
        if configured_url:
            return configured_url
        return "http://127.0.0.1:5173"

    def frontend_dist_dir() -> Path:
        return Path(__file__).resolve().parents[1] / "frontend" / "dist"

    def frontend_dist_index_path() -> Path:
        return frontend_dist_dir() / "index.html"

    def request_prefers_html_document(request: Request) -> bool:
        accept_header = str(request.headers.get("accept", "")).lower()
        if "text/html" in accept_header:
            return True
        return str(request.headers.get("sec-fetch-dest", "")).lower() == "document"

    def reject_snake_case_query_params(request: Request, forbidden_keys: set[str]) -> None:
        snake_keys = [key for key in request.query_params.keys() if key in forbidden_keys]
        if snake_keys:
            raise HTTPException(
                status_code=422,
                detail=f"Only camelCase query parameters are supported: replace {', '.join(sorted(set(snake_keys)))}",
            )

    def build_frontend_dev_page_redirect(request: Request) -> Optional[RedirectResponse]:
        frontend_url = frontend_dev_server_url()
        if not frontend_url or not request_prefers_html_document(request):
            return None

        query_string = urlencode(list(request.query_params.multi_items()))
        target_url = f"{frontend_url}{request.url.path}"
        if query_string:
            target_url = f"{target_url}?{query_string}"
        return RedirectResponse(url=target_url, status_code=307)

    def build_frontend_entry_response(request: Request) -> Optional[Response]:
        if not request_prefers_html_document(request):
            return None

        frontend_redirect = build_frontend_dev_page_redirect(request)
        if frontend_redirect:
            return frontend_redirect

        index_path = frontend_dist_index_path()
        if index_path.is_file():
            return FileResponse(index_path)

        return Response(
            content="Frontend entry is not available. Start the Vite dev server or build frontend/dist first.",
            status_code=503,
            media_type="text/plain",
        )

    def resolve_frontend_dist_file(frontend_path: str) -> Optional[Path]:
        normalized_path = str(frontend_path or "").strip().lstrip("/")
        if not normalized_path:
            return None

        dist_dir = frontend_dist_dir().resolve()
        candidate_path = (dist_dir / normalized_path).resolve()
        try:
            candidate_path.relative_to(dist_dir)
        except ValueError:
            return None
        if not candidate_path.is_file():
            return None
        return candidate_path

    def resolve_page_actor(request: Request) -> Actor:
        return get_actor(
            request,
            authorization=request.headers.get("authorization"),
            qb_access_token=request.cookies.get(AUTH_COOKIE_NAME),
            qb_role=request.cookies.get("qbRole"),
            qb_user_id=request.cookies.get("qbUserId"),
            x_role=request.headers.get("x-role"),
            x_user_id=request.headers.get("x-user-id"),
            x_joint_group=request.headers.get("x-joint-group"),
            role=request.query_params.get("role"),
            userId=request.query_params.get("userId"),
        )

    def resolve_optional_page_token_actor(request: Request) -> Optional[Actor]:
        return get_optional_token_actor(
            request,
            authorization=request.headers.get("authorization"),
            qb_access_token=request.cookies.get(AUTH_COOKIE_NAME),
        )

    def page_bootstrap(
        route: str,
        view_key: str,
        page_title: str,
        actor: Optional[Actor] = None,
        permissions: Optional[List[str]] = None,
        csrf_token: Optional[str] = None,
        include_question_meta: bool = True,
    ) -> PageBootstrapResponse:
        normalized_permissions: List[str] = []
        if permissions:
            normalized_permissions = [str(item).strip() for item in permissions if str(item or "").strip()]
        return PageBootstrapResponse(
            route=route,
            viewKey=view_key,
            pageTitle=page_title,
            actor=PageActor(role=actor.role, userId=actor.user_id) if actor else None,
            permissions=normalized_permissions,
            questionStatuses=list(QUESTION_STATUSES) if include_question_meta else [],
            questionTypes=list(QUESTION_TYPES) if include_question_meta else [],
            csrfToken=csrf_token,
        )

    def redirect_student_question_bank(request: Request, target_path: str) -> RedirectResponse:
        query_string = urlencode(list(request.query_params.multi_items()))
        target_url = str(target_path or "").strip() or "/student/question-bank/repair"
        if query_string:
            target_url = f"{target_url}?{query_string}"
        return RedirectResponse(url=target_url, status_code=307)

    async def read_teacher_qa_uploads(files: Optional[List[UploadFile]]) -> List[tuple[str, bytes, str]]:
        rows: List[tuple[str, bytes, str]] = []
        for upload in files or []:
            rows.append(
                (
                    str(upload.filename or "teacher-qa.png"),
                    await upload.read(),
                    str(upload.content_type or "application/octet-stream"),
                )
            )
        return rows

    @app.get("/", response_model=PageBootstrapResponse, include_in_schema=False)
    async def portal_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        ensure_actor_ready(actor, svc)
        return page_bootstrap("/", "portal", "三角色门户", actor=actor)

    @app.get("/teacher/home", response_model=PageBootstrapResponse, include_in_schema=False)
    async def teacher_home_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("teacher",))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc)
        return page_bootstrap("/teacher/home", "teacher-home", "教师工作台", actor=actor)

    @app.get("/teacher/questions", response_model=PageBootstrapResponse, include_in_schema=False)
    async def teacher_questions_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("teacher",))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc, "question:manage")
        return page_bootstrap("/teacher/questions", "teacher-questions", "题库管理", actor=actor)

    @app.get("/teacher/student-accounts", response_model=PageBootstrapResponse, include_in_schema=False)
    async def teacher_student_accounts_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("teacher",))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc, "student:manage")
        return page_bootstrap("/teacher/student-accounts", "teacher-student-accounts", "学生账号开通", actor=actor)

    @app.get("/teacher/import-history", include_in_schema=False)
    async def teacher_import_history_redirect(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("teacher",))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc, "question:manage")
        query_string = str(request.url.query or "").strip()
        target = "/teacher/questions"
        if query_string:
            target = f"{target}?{query_string}"
        return RedirectResponse(url=f"{target}#import-history", status_code=307)

    @app.get("/teacher/import-history/task/{taskId}", response_model=PageBootstrapResponse, include_in_schema=False)
    async def teacher_import_history_detail_page(taskId: str, request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("teacher",))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc, "question:manage")
        route_path = f"/teacher/import-history/task/{str(taskId).strip()}"
        return page_bootstrap(route_path, "teacher-import-history-detail", "导入任务详情", actor=actor)

    @app.get("/login", response_model=PageBootstrapResponse, include_in_schema=False)
    async def login_page(request: Request):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        return page_bootstrap("/login", "login", "注册登录", include_question_meta=False)

    @app.get("/student/practice", response_model=PageBootstrapResponse, include_in_schema=False)
    async def student_practice_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("student", "super_admin"))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc)
        return page_bootstrap("/student/practice", "student-practice", "学生端刷题页", actor=actor)

    @app.get("/student/practice/chapter", response_model=PageBootstrapResponse, include_in_schema=False)
    async def student_practice_chapter_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("student", "super_admin"))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc)
        return page_bootstrap("/student/practice/chapter", "student-practice", "章节闯关", actor=actor)

    @app.get("/student/practice/free", response_model=PageBootstrapResponse, include_in_schema=False)
    async def student_practice_free_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("student", "super_admin"))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc)
        return page_bootstrap("/student/practice/free", "student-practice", "自由练习", actor=actor)

    @app.get("/student/practice/mock", response_model=PageBootstrapResponse, include_in_schema=False)
    async def student_practice_mock_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("student", "super_admin"))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc)
        return page_bootstrap("/student/practice/mock", "student-practice", "模拟考试", actor=actor)

    @app.get("/student/practice/tasks", response_model=PageBootstrapResponse, include_in_schema=False)
    async def student_exam_tasks_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("student", "super_admin"))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc)
        return page_bootstrap("/student/practice/tasks", "student-exam-tasks", "考试任务", actor=actor)

    @app.get("/student/home", response_model=PageBootstrapResponse, include_in_schema=False)
    async def student_home_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("student", "super_admin"))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc)
        return page_bootstrap("/student/home", "student-home", "专属学习台", actor=actor)

    @app.get("/student/analysis", response_model=PageBootstrapResponse, include_in_schema=False)
    async def student_analysis_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("student", "super_admin"))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc)
        return page_bootstrap("/student/analysis", "student-analysis", "知识诊断", actor=actor)

    @app.get("/student/analysis/overview", response_model=PageBootstrapResponse, include_in_schema=False)
    async def student_analysis_overview_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("student", "super_admin"))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc)
        return page_bootstrap("/student/analysis/overview", "student-analysis", "知识诊断", actor=actor)

    @app.get("/student/analysis/tasks", response_model=PageBootstrapResponse, include_in_schema=False)
    async def student_analysis_tasks_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("student", "super_admin"))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc)
        return page_bootstrap("/student/analysis/tasks", "student-analysis", "知识诊断今日任务", actor=actor)

    @app.get("/student/analysis/points", response_model=PageBootstrapResponse, include_in_schema=False)
    async def student_analysis_points_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("student", "super_admin"))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc)
        return page_bootstrap("/student/analysis/points", "student-analysis", "练习积分", actor=actor)

    @app.get("/student/points", include_in_schema=False)
    async def student_points_legacy_redirect(request: Request):
        query = str(request.url.query or "").strip()
        target = "/student/analysis/points"
        if query:
            target = f"{target}?{query}"
        return RedirectResponse(url=target, status_code=307)

    @app.get("/student/wrong-book", response_model=PageBootstrapResponse, include_in_schema=False)
    async def student_wrong_book_page(request: Request, svc: QuestionBankService = Depends(service)):
        return redirect_student_question_bank(request, "/student/question-bank/repair")

    @app.get("/student/personal-bank", response_model=PageBootstrapResponse, include_in_schema=False)
    async def student_personal_bank_page(request: Request, svc: QuestionBankService = Depends(service)):
        return redirect_student_question_bank(request, "/student/question-bank/archive")

    @app.get("/student/question-bank/guide", response_model=PageBootstrapResponse, include_in_schema=False)
    async def student_question_bank_guide_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("student", "super_admin"))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc)
        return page_bootstrap("/student/question-bank/guide", "student-question-bank-guide", "使用文档", actor=actor)

    @app.get("/teacher/papers", response_model=PageBootstrapResponse, include_in_schema=False)
    async def teacher_papers_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("teacher",))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc, "paper:manage")
        return page_bootstrap("/teacher/papers", "teacher-papers", "试卷管理", actor=actor)

    @app.get("/teacher/exam-tasks", response_model=PageBootstrapResponse, include_in_schema=False)
    async def teacher_exam_tasks_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("teacher",))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc, "paper:manage")
        return page_bootstrap("/teacher/exam-tasks", "teacher-exam-tasks", "考试任务管理", actor=actor)

    @app.get("/teacher/analytics", response_model=PageBootstrapResponse, include_in_schema=False)
    async def teacher_analytics_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("teacher",))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc, "analytics:view")
        return page_bootstrap("/teacher/analytics", "teacher-analytics", "学情页", actor=actor)

    @app.get("/teacher/content-system", response_model=PageBootstrapResponse, include_in_schema=False)
    async def teacher_content_system_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("teacher",))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc, "paper:manage")
        return page_bootstrap("/teacher/content-system", "teacher-content-system", "内容体系字典", actor=actor)

    @app.get("/teacher/knowledge", response_model=PageBootstrapResponse, include_in_schema=False)
    async def teacher_knowledge_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("teacher",))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc, "question:manage")
        return page_bootstrap("/teacher/knowledge", "teacher-knowledge", "知识点三级树", actor=actor)

    @app.get("/teacher/guide", response_model=PageBootstrapResponse, include_in_schema=False)
    async def teacher_guide_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        redirect = redirect_for_page_role(actor, ("teacher",))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc)
        return page_bootstrap("/teacher/guide", "teacher-guide", "使用文档", actor=actor)

    @app.get("/admin/home", response_model=PageBootstrapResponse, include_in_schema=False)
    async def admin_home_page(
        request: Request,
        response: Response,
        svc: QuestionBankService = Depends(service),
    ):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_optional_page_token_actor(request)
        if actor is None:
            return RedirectResponse(url="/login", status_code=302)
        redirect = redirect_for_page_role(actor, ("super_admin",))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc, "settings:manage")
        csrf_token = ensure_csrf_cookie(request, response)
        return page_bootstrap(
            "/admin/home",
            "admin-home",
            "管理驾驶舱",
            actor=actor,
            csrf_token=csrf_token,
        )

    @app.get("/admin/control-center", response_model=PageBootstrapResponse, include_in_schema=False)
    async def admin_control_center_page(
        request: Request,
        response: Response,
        svc: QuestionBankService = Depends(service),
    ):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_optional_page_token_actor(request)
        if actor is None:
            return RedirectResponse(url="/login", status_code=302)
        redirect = redirect_for_page_role(actor, ("super_admin",))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc, "settings:manage")
        csrf_token = ensure_csrf_cookie(request, response)
        return page_bootstrap(
            "/admin/control-center",
            "admin-control-center",
            "超管控制台",
            actor=actor,
            csrf_token=csrf_token,
        )

    @app.get("/admin/syllabus", response_model=PageBootstrapResponse, include_in_schema=False)
    async def admin_syllabus_page(
        request: Request,
        response: Response,
        svc: QuestionBankService = Depends(service),
    ):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_optional_page_token_actor(request)
        if actor is None:
            return RedirectResponse(url="/login", status_code=302)
        redirect = redirect_for_page_role(actor, ("super_admin",))
        if redirect:
            return redirect
        ensure_actor_ready(actor, svc, "settings:manage")
        csrf_token = ensure_csrf_cookie(request, response)
        return page_bootstrap(
            "/admin/syllabus",
            "admin-syllabus",
            "大纲仓库",
            actor=actor,
            csrf_token=csrf_token,
        )

    @app.get("/messages", response_model=PageBootstrapResponse, include_in_schema=False)
    async def message_center_page(request: Request, svc: QuestionBankService = Depends(service)):
        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response
        actor = resolve_page_actor(request)
        ensure_actor_ready(actor, svc)
        whoami = svc.whoami(actor)
        permissions = whoami.get("permissions", []) if isinstance(whoami, dict) else []
        return page_bootstrap("/messages", "messages", "消息中心", actor=actor, permissions=permissions if isinstance(permissions, list) else [])

    @app.get("/api/question-bank/subjects", response_model=BaseResponse)
    async def list_subjects(
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc)
        return success(svc.list_subjects())

    @app.get("/api/question-bank/student/syllabus/catalog", response_model=BaseResponse)
    async def student_syllabus_catalog(
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc)
        return success(svc.get_student_syllabus_catalog())

    @app.get("/api/question-bank/user/my-classes", response_model=BaseResponse)
    @app.get("/api/user/my-classes", response_model=BaseResponse)
    async def list_my_classes(
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        return success(svc.list_my_classes(actor))

    @app.post("/api/question-bank/auth/sms-code", response_model=BaseResponse)
    async def send_sms_code(
        payload: AuthSmsCodeRequest,
        svc: QuestionBankService = Depends(service),
    ):
        return success(svc.send_sms_code(payload.model_dump(by_alias=True)))

    @app.post("/api/question-bank/auth/register", response_model=BaseResponse)
    async def register_user(
        payload: AuthRegisterRequest,
        svc: QuestionBankService = Depends(service),
    ):
        return success(svc.register_user(payload.model_dump(by_alias=True)))

    @app.post("/api/question-bank/auth/login/password", response_model=BaseResponse)
    async def login_by_password(
        payload: AuthLoginPasswordRequest,
        request: Request,
        response: Response,
        svc: QuestionBankService = Depends(service),
    ):
        data = svc.login_by_password(payload.model_dump(by_alias=True), request_client_ip(request))
        set_auth_cookie(response, data)
        return success(data)

    @app.post("/api/question-bank/auth/login/sms", response_model=BaseResponse)
    async def login_by_sms(
        payload: AuthLoginSmsRequest,
        response: Response,
        svc: QuestionBankService = Depends(service),
    ):
        data = svc.login_by_sms(payload.model_dump(by_alias=True))
        set_auth_cookie(response, data)
        return success(data)

    @app.post("/api/question-bank/auth/password/reset", response_model=BaseResponse)
    async def reset_password(
        payload: AuthPasswordResetRequest,
        svc: QuestionBankService = Depends(service),
    ):
        return success(svc.reset_password(payload.model_dump(by_alias=True)))

    @app.post("/api/question-bank/auth/logout", response_model=BaseResponse)
    async def logout(
        request: Request,
        response: Response,
        authorization: str = Header(default=""),
        svc: QuestionBankService = Depends(service),
    ):
        tokens_to_revoke = []
        auth_token = parse_bearer_token(authorization)
        if auth_token:
            tokens_to_revoke.append(auth_token)
        cookie_token = request.cookies.get(AUTH_COOKIE_NAME, "").strip()
        if cookie_token and cookie_token not in tokens_to_revoke:
            tokens_to_revoke.append(cookie_token)
        for token in tokens_to_revoke:
            svc.revoke_token(token)
        response.delete_cookie(AUTH_COOKIE_NAME, path="/")
        response.delete_cookie(CSRF_COOKIE_NAME, path="/")
        return success({"loggedOut": True})

    @app.get("/api/question-bank/auth/me", response_model=BaseResponse)
    async def auth_me(
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc)
        return success(svc.whoami(actor))

    @app.get("/api/knowledge-tree", response_model=KnowledgeGraphEnvelopeResponse)
    @app.get("/api/question-bank/knowledge/tree", response_model=KnowledgeGraphEnvelopeResponse)
    async def knowledge_tree(
        request: Request,
        status: str = Query(default=""),
        chapter_code: str = Query(default="", alias="chapterCode"),
        point_code: str = Query(default="", alias="pointCode"),
        subject_id: str = Query(default="", alias="subjectId"),
        exam_category_code: str = Query(default="", alias="examCategoryCode"),
        joint_exam_group_code: str = Query(default="", alias="jointExamGroupCode"),
        subject_code: str = Query(default="", alias="subjectCode"),
        policy_version: str = Query(default="", alias="policyVersion"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        reject_snake_case_query_params(request, camelcase_only_query_keys)
        normalized_exam_category_code = exam_category_code.strip()
        normalized_joint_exam_group_code = joint_exam_group_code.strip()
        normalized_subject_code = subject_code.strip()
        normalized_subject_id = subject_id.strip()
        if normalized_subject_id and not normalized_subject_code:
            normalized_subject_code = subject_code_from_subject_id(normalized_subject_id)
        normalized_policy_version = policy_version.strip() or POLICY_VERSION_CODE
        if actor.role in {ROLE_STUDENT, ROLE_SUPER_ADMIN}:
            ensure_actor_ready(actor, svc)
            return success(
                svc.list_knowledge_tree(
                    status.strip(),
                    actor,
                    normalized_exam_category_code,
                    normalized_joint_exam_group_code,
                    normalized_subject_code,
                    normalized_policy_version,
                )
            )
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(
            svc.list_knowledge_tree(
                status.strip(),
                actor,
                normalized_exam_category_code,
                normalized_joint_exam_group_code,
                normalized_subject_code,
                normalized_policy_version,
            )
        )

    @app.get("/api/question-bank/knowledge/children", response_model=BaseResponse)
    async def knowledge_children(
        parentId: str = Query(default=""),
        status: str = Query(default=""),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.list_knowledge_children(parentId.strip(), status.strip()))

    @app.get("/api/question-bank/knowledge/{knowledgeId}", response_model=BaseResponse)
    async def get_knowledge(
        knowledgeId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.get_knowledge(knowledgeId))

    @app.post("/api/question-bank/knowledge", response_model=BaseResponse)
    async def create_knowledge(
        payload: KnowledgeWriteRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.create_knowledge(payload.model_dump(by_alias=True, exclude_unset=True)))

    @app.put("/api/question-bank/knowledge/{knowledgeId}", response_model=BaseResponse)
    async def update_knowledge(
        knowledgeId: str,
        payload: KnowledgeWriteRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.update_knowledge(knowledgeId, payload.model_dump(by_alias=True, exclude_unset=True)))

    @app.post("/api/question-bank/knowledge/{knowledgeId}/prerequisites", response_model=BaseResponse)
    async def update_prerequisites(
        knowledgeId: str,
        payload: KnowledgePrerequisiteUpdateRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.update_knowledge_prerequisites(knowledgeId, payload.model_dump(by_alias=True)))

    @app.post("/api/question-bank/knowledge/layout", response_model=BaseResponse)
    async def save_knowledge_layout(
        payload: KnowledgeLayoutSaveRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.save_knowledge_layout(payload.model_dump(by_alias=True)))

    @app.delete("/api/question-bank/knowledge/{knowledgeId}", response_model=BaseResponse)
    async def delete_knowledge(
        knowledgeId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.delete_knowledge(knowledgeId, actor))

    @app.post("/api/question-bank/knowledge/deleted/{snapshotId}/restore", response_model=BaseResponse)
    async def restore_deleted_knowledge(
        snapshotId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.restore_deleted_knowledge(snapshotId, actor))

    @app.post("/api/question-bank/knowledge/{knowledgeId}/sort/{direction}", response_model=BaseResponse)
    async def move_knowledge(
        knowledgeId: str,
        direction: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.move_knowledge(knowledgeId, direction))

    @app.get("/api/question-bank/content/baseline", response_model=BaseResponse)
    async def content_baseline(
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        return success(svc.get_content_baseline())

    @app.get("/api/question-bank/professional-tree", response_model=ProfessionalTreeResponse)
    async def professional_tree(
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.get_professional_tree())

    @app.get("/api/question-bank/admin/console", response_model=BaseResponse)
    async def admin_console(
        actor: Actor = Depends(ensure_admin_api_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_super_admin(actor)
        ensure_actor_ready(actor, svc, "settings:manage")
        return success(svc.get_system_console())

    @app.get("/api/question-bank/admin/settings", response_model=BaseResponse)
    async def admin_settings(
        actor: Actor = Depends(ensure_admin_api_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_super_admin(actor)
        ensure_actor_ready(actor, svc, "settings:manage")
        return success(svc.get_system_settings())

    @app.post("/api/question-bank/admin/settings", response_model=BaseResponse)
    async def save_admin_settings(
        payload: AdminSystemSettingsSaveRequest,
        csrf_checked: None = Depends(require_admin_csrf),
        actor: Actor = Depends(ensure_admin_api_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_super_admin(actor)
        ensure_actor_ready(actor, svc, "settings:manage")
        return success(svc.save_system_settings(payload.model_dump(by_alias=True), actor))

    @app.get("/api/question-bank/admin/syllabus", response_model=BaseResponse)
    async def list_admin_syllabus(
        actor: Actor = Depends(ensure_admin_api_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_super_admin(actor)
        ensure_actor_ready(actor, svc, "settings:manage")
        return success(svc.list_syllabus_versions())

    @app.post("/api/question-bank/admin/syllabus/versions", response_model=BaseResponse)
    async def create_admin_syllabus_version(
        payload: AdminSyllabusVersionCreateRequest,
        csrf_checked: None = Depends(require_admin_csrf),
        actor: Actor = Depends(ensure_admin_api_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_super_admin(actor)
        ensure_actor_ready(actor, svc, "settings:manage")
        return success(svc.create_syllabus_version(payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/admin/syllabus/{versionId}/weights", response_model=BaseResponse)
    async def save_admin_syllabus_weights(
        versionId: str,
        payload: AdminSyllabusWeightsSaveRequest,
        csrf_checked: None = Depends(require_admin_csrf),
        actor: Actor = Depends(ensure_admin_api_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_super_admin(actor)
        ensure_actor_ready(actor, svc, "settings:manage")
        return success(svc.save_syllabus_weights(versionId, payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/admin/syllabus/{versionId}/ai-parse", response_model=BaseResponse)
    async def ai_parse_admin_syllabus(
        versionId: str,
        file: UploadFile = File(...),
        csrf_checked: None = Depends(require_admin_csrf),
        actor: Actor = Depends(ensure_admin_api_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_super_admin(actor)
        ensure_actor_ready(actor, svc, "settings:manage")
        file_content = await file.read()
        return success(svc.ai_parse_syllabus_document(versionId, file.filename or "syllabus.pdf", file_content, actor))

    @app.get("/api/question-bank/admin/users", response_model=BaseResponse)
    async def list_managed_users(
        page: int = Query(default=1, ge=1),
        size: int = Query(default=20, ge=1, le=200),
        role: str = Query(default=""),
        keyword: str = Query(default=""),
        actor: Actor = Depends(ensure_admin_api_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc, "student:manage")
        items, total = svc.list_managed_users({"role": role.strip(), "keyword": keyword.strip()}, page, size, actor)
        return success(pagination(items, page, size, total))

    @app.post("/api/question-bank/admin/users", response_model=BaseResponse)
    async def save_managed_user(
        payload: AdminManagedUserSaveRequest,
        csrf_checked: None = Depends(require_admin_csrf),
        actor: Actor = Depends(ensure_admin_api_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc, "student:manage")
        return success(svc.save_managed_user(payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/admin/students/import", response_model=BaseResponse)
    async def import_students(
        payload: AdminStudentsImportRequest,
        csrf_checked: None = Depends(require_admin_csrf),
        actor: Actor = Depends(ensure_admin_api_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc, "student:manage")
        return success(svc.import_students_csv(payload.csv_text, actor))

    @app.get("/api/question-bank/admin/students/export", response_model=BaseResponse)
    async def export_students(
        format: str = Query(default="csv"),
        actor: Actor = Depends(ensure_admin_api_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc, "student:manage")
        return success(svc.export_managed_students(format, actor))

    @app.post("/api/question-bank/admin/redeem-code/batches", response_model=BaseResponse)
    async def create_admin_redeem_code_batch(
        payload: AdminRedeemCodeBatchCreateRequest,
        csrf_checked: None = Depends(require_admin_csrf),
        actor: Actor = Depends(ensure_admin_api_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_super_admin(actor)
        ensure_actor_ready(actor, svc, "settings:manage")
        return success(svc.create_admin_redeem_code_batch(payload.model_dump(by_alias=True), actor))

    @app.get("/api/question-bank/admin/redeem-code/batches", response_model=BaseResponse)
    async def list_admin_redeem_code_batches(
        page: int = Query(default=1, ge=1),
        size: int = Query(default=20, ge=1, le=200),
        status: str = Query(default=""),
        keyword: str = Query(default=""),
        actor: Actor = Depends(ensure_admin_api_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_super_admin(actor)
        ensure_actor_ready(actor, svc, "settings:manage")
        items, total = svc.list_admin_redeem_code_batches(
            {"status": status.strip(), "keyword": keyword.strip()},
            page,
            size,
            actor,
        )
        return success(pagination(items, page, size, total))

    @app.get("/api/question-bank/admin/conversion/overview", response_model=BaseResponse)
    async def admin_conversion_overview(
        startDate: str = Query(default="", alias="startDate"),
        endDate: str = Query(default="", alias="endDate"),
        actor: Actor = Depends(ensure_admin_api_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_super_admin(actor)
        ensure_actor_ready(actor, svc, "settings:manage")
        return success(svc.get_admin_conversion_overview({"startDate": startDate.strip(), "endDate": endDate.strip()}, actor))

    @app.get("/api/question-bank/admin/learning-methods", response_model=BaseResponse)
    async def list_admin_learning_methods(
        status: str = Query(default=""),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        if actor.role != ROLE_SUPER_ADMIN:
            require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.list_admin_learning_methods(status.strip()))

    @app.post("/api/question-bank/admin/learning-methods", response_model=BaseResponse)
    async def create_admin_learning_method(
        payload: LearningMethodAdminSaveRequest,
        csrf_checked: None = Depends(require_admin_csrf),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        if actor.role != ROLE_SUPER_ADMIN:
            require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.create_admin_learning_method(payload.model_dump(by_alias=True), actor))

    @app.put("/api/question-bank/admin/learning-methods/{methodCode}", response_model=BaseResponse)
    async def update_admin_learning_method(
        methodCode: str,
        payload: LearningMethodAdminUpdateRequest,
        csrf_checked: None = Depends(require_admin_csrf),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        if actor.role != ROLE_SUPER_ADMIN:
            require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(
            svc.update_admin_learning_method(
                methodCode,
                payload.model_dump(by_alias=True, exclude_none=True),
                actor,
            )
        )

    @app.post("/api/question-bank/admin/learning-methods/sort", response_model=BaseResponse)
    async def sort_admin_learning_methods(
        payload: LearningMethodAdminSortRequest,
        csrf_checked: None = Depends(require_admin_csrf),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        if actor.role != ROLE_SUPER_ADMIN:
            require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.sort_admin_learning_methods(payload.model_dump(by_alias=True), actor))


    @app.post("/api/question-bank/admin/learning-methods/{methodCode}/profile/auto-generate", response_model=BaseResponse)
    async def auto_generate_admin_learning_method_profile(
        methodCode: str,
        payload: LearningMethodProfileAutoGenerateRequest,
        csrf_checked: None = Depends(require_admin_csrf),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        if actor.role != ROLE_SUPER_ADMIN:
            require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.auto_generate_learning_method_profile(methodCode, payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/admin/questions/match-features/auto-batch", response_model=BaseResponse)
    async def auto_batch_admin_question_match_features(
        payload: LearningMethodQuestionFeatureAutoBatchRequest,
        csrf_checked: None = Depends(require_admin_csrf),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        if actor.role != ROLE_SUPER_ADMIN:
            require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.auto_batch_question_match_features(payload.model_dump(by_alias=True), actor))

    @app.get("/api/question-bank/messages", response_model=BaseResponse)
    async def list_messages(
        page: int = Query(default=1, ge=1),
        size: int = Query(default=20, ge=1, le=100),
        category: str = Query(default=""),
        readStatus: str = Query(default=""),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc)
        items, total = svc.list_messages(
            {"category": category.strip(), "readStatus": readStatus.strip()},
            page,
            size,
            actor,
        )
        return success(pagination(items, page, size, total))

    @app.post("/api/question-bank/messages/{messageId}/read", response_model=BaseResponse)
    async def mark_message_read(
        messageId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc)
        return success(svc.mark_message_read(messageId, actor))

    @app.post("/api/question-bank/messages/read/batch", response_model=BaseResponse)
    async def mark_messages_read_batch(
        payload: MessagesReadBatchRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc)
        return success(svc.mark_messages_read_batch(payload.model_dump(by_alias=True), actor))

    @app.get("/api/question-bank/messages/unread-count", response_model=BaseResponse)
    async def get_message_unread_count(
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc)
        return success(svc.get_message_unread_summary(actor))

    @app.get("/api/question-bank/messages/settings", response_model=BaseResponse)
    async def get_message_settings(
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc)
        return success(svc.get_message_settings(actor))

    @app.post("/api/question-bank/messages/settings", response_model=BaseResponse)
    async def save_message_settings(
        payload: MessagesSettingsSaveRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc)
        return success(svc.save_message_settings(payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/messages/send", response_model=BaseResponse)
    async def send_messages(
        payload: MessagesSendRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_analytics_operator(actor)
        ensure_actor_ready(actor, svc, "message:send")
        return success(svc.send_messages(payload.model_dump(by_alias=True, exclude_unset=True), actor))

    @app.get("/api/question-bank/messages/send-history", response_model=BaseResponse)
    async def list_message_send_history(
        page: int = Query(default=1, ge=1),
        size: int = Query(default=20, ge=1, le=100),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_analytics_operator(actor)
        ensure_actor_ready(actor, svc, "message:send")
        items, total = svc.list_message_send_history(page, size, actor)
        return success(pagination(items, page, size, total))

    @app.post("/api/question-bank/messages/send-history/{traceId}/recall", response_model=BaseResponse)
    async def recall_message_send(
        traceId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_analytics_operator(actor)
        ensure_actor_ready(actor, svc, "message:send")
        return success(svc.recall_message_send(traceId, actor))

    @app.get("/api/question-bank/messages/teacher-qa/threads", response_model=BaseResponse)
    async def list_teacher_qa_threads(
        page: int = Query(default=1, ge=1),
        size: int = Query(default=10, ge=1, le=100),
        status: str = Query(default=""),
        subject_code: str = Query(default="", alias="subjectCode"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc)
        items, total = svc.list_teacher_qa_threads(
            {
                "status": status.strip(),
                "subjectCode": subject_code.strip(),
            },
            page,
            size,
            actor,
        )
        return success(pagination(items, page, size, total))

    @app.get("/api/question-bank/messages/teacher-qa/threads/{threadId}", response_model=BaseResponse)
    async def get_teacher_qa_thread(
        threadId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc)
        return success(svc.get_teacher_qa_thread(threadId, actor))

    @app.post("/api/question-bank/messages/teacher-qa/threads", response_model=BaseResponse)
    async def create_teacher_qa_thread(
        title: str = Form(...),
        content: str = Form(default=""),
        subject_code: str = Form(default="", alias="subjectCode"),
        attachments: Optional[List[UploadFile]] = File(default=None),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(
            svc.create_teacher_qa_thread(
                {
                    "subjectCode": subject_code,
                    "title": title,
                    "content": content,
                },
                await read_teacher_qa_uploads(attachments),
                actor,
            )
        )

    @app.post("/api/question-bank/messages/teacher-qa/threads/{threadId}/reply", response_model=BaseResponse)
    async def reply_teacher_qa_thread(
        threadId: str,
        content: str = Form(default=""),
        attachments: Optional[List[UploadFile]] = File(default=None),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc)
        return success(
            svc.reply_teacher_qa_thread(
                threadId,
                {"content": content},
                await read_teacher_qa_uploads(attachments),
                actor,
            )
        )

    @app.get("/api/question-bank/messages/teacher-qa/attachments/{attachmentId}")
    async def get_teacher_qa_attachment(
        attachmentId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc)
        attachment = svc.resolve_teacher_qa_attachment(attachmentId, actor)
        return FileResponse(
            attachment["filePath"],
            media_type=attachment["mediaType"],
            filename=attachment["fileName"],
        )

    @app.get("/api/question-bank/tasks", response_model=BaseResponse)
    async def list_tasks(
        page: int = Query(default=1, ge=1),
        size: int = Query(default=10, ge=1, le=100),
        type: str = Query(default=""),
        status: str = Query(default=""),
        questionId: str = Query(default=""),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc)
        items, total = svc.list_tasks(
            {
                "type": type.strip(),
                "status": status.strip(),
                "questionId": questionId.strip(),
            },
            page,
            size,
            actor,
        )
        response_data = pagination(items, page, size, total)
        response_data["aiQuota"] = svc.get_actor_task_ai_quota(actor)
        return success(response_data)

    @app.get("/api/question-bank/tasks/{taskId}", response_model=BaseResponse)
    async def get_task(
        taskId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc)
        return success(svc.get_task(taskId, actor))

    @app.post("/api/question-bank/tasks/{taskId}/cancel", response_model=BaseResponse)
    async def cancel_task(
        taskId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        ensure_actor_ready(actor, svc)
        return success(svc.cancel_task(taskId, actor))

    @app.get("/api/question-bank/questions", response_model=BaseResponse)
    async def list_questions(
        request: Request,
        page: int = Query(default=1, ge=1),
        size: int = Query(default=10, ge=1, le=100),
        knowledgeId: str = Query(default="", alias="knowledgeId"),
        question_ids: str = Query(default="", alias="questionIds"),
        user_id: str = Query(default="", alias="userId"),
        keyword: str = Query(default=""),
        type: str = Query(default=""),
        status: str = Query(default=""),
        chapter_code: str = Query(default="", alias="chapterCode"),
        point_code: str = Query(default="", alias="pointCode"),
        exam_category_code: str = Query(default="", alias="examCategoryCode"),
        joint_exam_group_code: str = Query(default="", alias="jointExamGroupCode"),
        subject_code: str = Query(default="", alias="subjectCode"),
        policy_version: str = Query(default="HB_ZSB_2026", alias="policyVersion"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        reject_snake_case_query_params(request, camelcase_only_query_keys)
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        normalized_exam_category_code = exam_category_code.strip()
        normalized_joint_exam_group_code = joint_exam_group_code.strip()
        normalized_subject_code = subject_code.strip()
        normalized_policy_version = policy_version.strip() or "HB_ZSB_2026"
        items, total = svc.list_questions(
            {
                "knowledgeId": knowledgeId.strip(),
                "questionIds": question_ids.strip(),
                "userId": user_id.strip(),
                "keyword": keyword.strip(),
                "type": type.strip(),
                "status": status.strip(),
                "chapterCode": chapter_code.strip(),
                "pointCode": point_code.strip(),
                "examCategoryCode": normalized_exam_category_code,
                "jointExamGroupCode": normalized_joint_exam_group_code,
                "subjectCode": normalized_subject_code,
                "policyVersion": normalized_policy_version,
            },
            page,
            size,
            actor,
        )
        return success(pagination(items, page, size, total))

    @app.get("/api/question-bank/questions/{questionId}", response_model=BaseResponse)
    async def get_question(
        questionId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.get_question(questionId, actor))

    @app.get("/api/question-bank/questions/{questionId}/reviews", response_model=BaseResponse)
    async def list_reviews(
        questionId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.list_reviews(questionId, actor))

    @app.post("/api/question-bank/questions", response_model=BaseResponse)
    async def create_question(
        payload: QuestionCreateRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.create_question(payload.to_service_payload(), actor))

    @app.post("/api/question-bank/batch-create", response_model=BaseResponse)
    async def batch_create_questions(
        payload: BatchQuestionCreateRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(
            svc.batch_create_questions(
                [item.to_service_payload() for item in payload.items],
                actor,
                source_task_id=str(payload.source_task_id or "").strip(),
            )
        )

    @app.put("/api/question-bank/questions/{questionId}", response_model=BaseResponse)
    async def update_question(
        questionId: str,
        payload: QuestionUpdateRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        existing_question = svc.get_question(questionId, actor)
        return success(svc.update_question(questionId, payload.to_service_payload(existing_question), actor))

    @app.delete("/api/question-bank/questions/{questionId}", response_model=BaseResponse)
    async def delete_question(
        questionId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.delete_question(questionId, actor))

    @app.post("/api/question-bank/questions/deleted/{snapshotId}/restore", response_model=BaseResponse)
    async def restore_deleted_question(
        snapshotId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.restore_deleted_question(snapshotId, actor))

    @app.post("/api/question-bank/questions/delete/batch", response_model=BaseResponse)
    async def delete_questions_batch(
        payload: QuestionDeleteBatchRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.delete_questions_batch(payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/questions/deleted/batch/{snapshotId}/restore", response_model=BaseResponse)
    async def restore_deleted_questions_batch(
        snapshotId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.restore_deleted_questions_batch(snapshotId, actor))

    @app.post("/api/question-bank/questions/{questionId}/status/{targetStatus}", response_model=BaseResponse)
    async def transition_status(
        questionId: str,
        targetStatus: str,
        payload: Optional[QuestionTransitionRequest] = None,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(
            svc.transition_status(
                questionId,
                targetStatus,
                actor,
                payload.model_dump(by_alias=True)
                if payload
                else {"policyVersion": POLICY_VERSION_CODE, "reason": ""},
            )
        )

    @app.post("/api/question-bank/questions/status/batch", response_model=BaseResponse)
    async def transition_status_batch(
        payload: QuestionStatusBatchTransitionRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.transition_status_batch(payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/imports/template", response_model=BaseResponse)
    async def import_template(
        selectedIndexes: Optional[List[int]] = Form(default=None),
        knowledgeId: str = Form(..., alias="knowledgeId"),
        file: UploadFile = File(...),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        content = await file.read()
        return success(
            svc.import_template(
                file.filename or "template.txt",
                content,
                knowledgeId,
                actor,
                selected_indexes=selectedIndexes,
            )
        )

    @app.post("/api/question-bank/imports/template/preview", response_model=BaseResponse)
    async def preview_template_import(
        knowledgeId: str = Form(..., alias="knowledgeId"),
        file: UploadFile = File(...),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        content = await file.read()
        return success(svc.preview_template_import(file.filename or "template.txt", content, knowledgeId, actor))

    @app.post("/api/question-bank/batch-parse", response_model=BaseResponse)
    async def batch_parse_questions(
        file: UploadFile = File(...),
        exam_category_code: str = Form(default="", alias="examCategoryCode"),
        joint_exam_group_code: str = Form(default="", alias="jointExamGroupCode"),
        subject_code: str = Form(default="", alias="subjectCode"),
        policy_version: str = Form(default="", alias="policyVersion"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        content = await file.read()
        return success(
            svc.parse_question_batch_from_word(
                file.filename or "batch-parse.docx",
                content,
                actor,
                exam_category_code.strip(),
                joint_exam_group_code.strip(),
                subject_code.strip(),
                policy_version.strip() or POLICY_VERSION_CODE,
            )
        )

    @app.post("/api/knowledge-graph/parse-from-word", response_model=BaseResponse)
    @app.post("/api/question-bank/knowledge-graph/parse-from-word", response_model=BaseResponse, include_in_schema=False)
    async def parse_knowledge_graph_from_word(
        file: UploadFile = File(...),
        parse_mode: str = Form(default="", alias="parseMode"),
        exam_category_code: str = Form(default="", alias="examCategoryCode"),
        joint_exam_group_code: str = Form(default="", alias="jointExamGroupCode"),
        subject_code: str = Form(default="", alias="subjectCode"),
        policy_version: str = Form(default="", alias="policyVersion"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        content = await file.read()
        normalized_parse_mode = parse_mode.strip() or "knowledge_graph"
        if normalized_parse_mode == "question_batch":
            return success(
                svc.parse_question_batch_from_word(
                    file.filename or "question-batch.docx",
                    content,
                    actor,
                    exam_category_code.strip(),
                    joint_exam_group_code.strip(),
                    subject_code.strip(),
                    policy_version.strip() or POLICY_VERSION_CODE,
                )
            )
        return success(
            svc.parse_knowledge_graph_from_word(
                file.filename or "knowledge-graph.docx",
                content,
                actor,
                exam_category_code.strip(),
                joint_exam_group_code.strip(),
                subject_code.strip(),
                policy_version.strip() or POLICY_VERSION_CODE,
            )
        )

    @app.get("/api/question-bank/imports/template/example", response_model=BaseResponse)
    async def template_import_example(
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_question_operator(actor)
        ensure_actor_ready(actor, svc, "question:manage")
        return success(svc.get_question_import_template_example())

    @app.get("/api/question-bank/papers/questions", response_model=BaseResponse)
    async def list_paper_questions(
        page: int = Query(default=1, ge=1),
        size: int = Query(default=20, ge=1, le=200),
        subject_id: str = Query(default="", alias="subjectId"),
        chapter: str = Query(default=""),
        keyword: str = Query(default=""),
        type: str = Query(default=""),
        difficulty: str = Query(default=""),
        paperId: str = Query(default="", alias="paperId"),
        paperStatus: str = Query(default="", alias="paperStatus"),
        exam_category_code: str = Query(default="", alias="examCategoryCode"),
        joint_exam_group_code: str = Query(default="", alias="jointExamGroupCode"),
        subject_code: str = Query(default="", alias="subjectCode"),
        policy_version: str = Query(default="", alias="policyVersion"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        normalized_exam_category_code = exam_category_code.strip()
        normalized_joint_exam_group_code = joint_exam_group_code.strip()
        normalized_subject_code = subject_code.strip()
        normalized_policy_version = policy_version.strip() or "HB_ZSB_2026"
        items, total = svc.list_paper_questions(
            {
                "subjectId": subject_id.strip(),
                "chapter": chapter.strip(),
                "keyword": keyword.strip(),
                "type": type.strip(),
                "difficulty": difficulty.strip(),
                "paperId": paperId.strip(),
                "paperStatus": paperStatus.strip(),
                "examCategoryCode": normalized_exam_category_code,
                "jointExamGroupCode": normalized_joint_exam_group_code,
                "subjectCode": normalized_subject_code,
                "policyVersion": normalized_policy_version,
            },
            page,
            size,
            actor,
        )
        return success(pagination(items, page, size, total))

    @app.get("/api/question-bank/papers/questions/filter-options", response_model=BaseResponse)
    async def list_paper_question_filter_options(
        keyword: str = Query(default=""),
        type: str = Query(default=""),
        difficulty: str = Query(default=""),
        exam_category_code: str = Query(default="", alias="examCategoryCode"),
        joint_exam_group_code: str = Query(default="", alias="jointExamGroupCode"),
        subject_code: str = Query(default="", alias="subjectCode"),
        policy_version: str = Query(default="", alias="policyVersion"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        return success(
            svc.list_paper_question_filter_options(
                {
                    "keyword": keyword.strip(),
                    "type": type.strip(),
                    "difficulty": difficulty.strip(),
                    "examCategoryCode": exam_category_code.strip(),
                    "jointExamGroupCode": joint_exam_group_code.strip(),
                    "subjectCode": subject_code.strip(),
                    "policyVersion": policy_version.strip() or "HB_ZSB_2026",
                },
                actor,
            )
        )

    @app.post("/api/question-bank/papers/manual", response_model=BaseResponse)
    async def save_manual_paper(
        payload: ManualPaperCreateRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        return success(svc.save_manual_paper(payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/papers/auto", response_model=BaseResponse)
    async def save_auto_paper(
        payload: PaperAutoSaveRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        return success(svc.save_auto_paper(payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/papers/ai-generate", response_model=BaseResponse)
    async def ai_generate_paper(
        payload: PaperAiGenerateRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        return success(svc.ai_generate_paper(payload.model_dump(by_alias=True), actor))

    @app.get("/api/question-bank/papers/teacher-classes", response_model=BaseResponse)
    async def list_teacher_paper_classes(
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        return success(svc.list_teacher_paper_classes(actor))

    @app.get("/api/question-bank/papers/target-weights", response_model=BaseResponse)
    async def paper_target_weights(
        knowledgeIds: str = Query(default=""),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        knowledge_ids = [
            item.strip()
            for item in knowledgeIds.split(",")
            if item.strip()
        ]
        return success(svc.get_paper_target_weight_profile(knowledge_ids))

    @app.post("/api/question-bank/papers/{paperId}/status/{paperStatus}", response_model=BaseResponse)
    async def update_paper_status(
        paperId: str,
        paperStatus: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        return success(svc.update_paper_status(paperId, paperStatus, actor))

    @app.delete("/api/question-bank/papers/{paperId}", response_model=BaseResponse)
    async def delete_paper(
        paperId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        return success(svc.delete_paper(paperId, actor))

    @app.post("/api/question-bank/papers/deleted/{snapshotId}/restore", response_model=BaseResponse)
    async def restore_deleted_paper(
        snapshotId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        return success(svc.restore_deleted_paper(snapshotId, actor))

    @app.get("/api/question-bank/papers/{paperId}/export", response_model=BaseResponse)
    async def export_paper(
        paperId: str,
        format: str = Query(default="txt"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        return success(svc.export_paper(paperId, actor, format.strip()))

    @app.get("/api/question-bank/papers/overview", response_model=BaseResponse)
    async def paper_overview(
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        return success(svc.list_paper_overview(actor))

    @app.get("/api/question-bank/papers/templates", response_model=BaseResponse)
    async def paper_templates(
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        return success(svc.list_paper_templates())

    @app.post("/api/question-bank/papers/templates", response_model=BaseResponse)
    async def save_paper_template(
        payload: PaperTemplateSaveRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        return success(svc.save_paper_template(payload.model_dump(by_alias=True), actor))

    @app.delete("/api/question-bank/papers/templates/{templateId}", response_model=BaseResponse)
    async def delete_paper_template(
        templateId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        return success(svc.delete_paper_template(templateId, actor))

    @app.post("/api/question-bank/papers/templates/deleted/{snapshotId}/restore", response_model=BaseResponse)
    async def restore_deleted_paper_template(
        snapshotId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        return success(svc.restore_deleted_paper_template(snapshotId, actor))

    @app.get("/api/question-bank/exam-tasks", response_model=BaseResponse)
    async def list_exam_tasks(
        page: int = Query(default=1, ge=1),
        size: int = Query(default=20, ge=1, le=200),
        taskType: str = Query(default=""),
        status: str = Query(default=""),
        keyword: str = Query(default=""),
        subject_code: str = Query(default="", alias="subjectCode"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        items, total = svc.list_exam_tasks(
            {
                "taskType": taskType.strip(),
                "status": status.strip(),
                "subjectCode": subject_code.strip(),
                "keyword": keyword.strip(),
            },
            page,
            size,
            actor,
        )
        return success(pagination(items, page, size, total))

    @app.post("/api/question-bank/exam-tasks", response_model=BaseResponse)
    async def create_exam_task(
        payload: ExamTaskCreateRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        return success(svc.create_exam_task(payload.model_dump(by_alias=True), actor))

    @app.get("/api/question-bank/exam-tasks/{taskId}", response_model=BaseResponse)
    async def get_exam_task_detail(
        taskId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_paper_operator(actor)
        ensure_actor_ready(actor, svc, "paper:manage")
        return success(svc.get_exam_task_detail(taskId, actor))

    @app.post("/api/adaptive-practice/generate", response_model=AdaptivePracticeResponse)
    async def generate_adaptive_practice(
        payload: AdaptivePracticeRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.generate_adaptive_practice(payload.model_dump(by_alias=True), actor))

    @app.get("/api/question-bank/learning-methods", response_model=BaseResponse)
    async def list_learning_methods(
        status: str = Query(default="ACTIVE"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.list_learning_methods_for_student(status.strip(), actor))

    @app.get("/api/question-bank/learning-methods/{methodCode}", response_model=BaseResponse)
    async def get_learning_method_detail(
        methodCode: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.get_learning_method_detail_for_student(methodCode, actor))

    @app.post("/api/question-bank/learning-methods/{methodCode}/start", response_model=BaseResponse)
    async def start_learning_method(
        methodCode: str,
        payload: LearningMethodPracticeStartRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.start_learning_method_practice(methodCode, payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/learning-methods/{methodCode}/complete", response_model=BaseResponse)
    async def complete_learning_method(
        methodCode: str,
        payload: LearningMethodPracticeCompleteRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.complete_learning_method_practice(methodCode, payload.model_dump(by_alias=True), actor))


    @app.post("/api/question-bank/learning-methods/{methodCode}/question-pack/recommend", response_model=BaseResponse)
    async def recommend_learning_method_question_pack(
        methodCode: str,
        payload: LearningMethodQuestionPackRecommendRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.recommend_learning_method_question_pack(methodCode, payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/learning-methods/{methodCode}/question-pack/feedback", response_model=BaseResponse)
    async def feedback_learning_method_question_pack(
        methodCode: str,
        payload: LearningMethodQuestionPackFeedbackRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.feedback_learning_method_question_pack(methodCode, payload.model_dump(by_alias=True), actor))


    @app.get("/api/question-bank/learning-methods/{methodCode}/question-pack/recommendations", response_model=BaseResponse)
    async def list_learning_method_question_pack_recommendations(
        methodCode: str,
        limit: int = Query(default=10, ge=1, le=50),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.list_learning_method_question_pack_recommendations(methodCode, limit, actor))

    @app.get("/api/question-bank/student/practice/questions", response_model=BaseResponse)
    async def list_student_practice_questions(
        page: int = Query(default=1, ge=1),
        size: int = Query(default=10, ge=1, le=100),
        knowledgeId: str = Query(default="", alias="knowledgeId"),
        knowledge_path_node_id: str = Query(default="", alias="knowledgePathNodeId"),
        subject_id: str = Query(default="", alias="subjectId"),
        exam_category_code: str = Query(default="", alias="examCategoryCode"),
        joint_exam_group_code: str = Query(default="", alias="jointExamGroupCode"),
        subject_code: str = Query(default="", alias="subjectCode"),
        chapter: str = Query(default=""),
        chapter_code: str = Query(default="", alias="chapterCode"),
        point_code: str = Query(default="", alias="pointCode"),
        type: str = Query(default=""),
        difficulty: str = Query(default=""),
        keyword: str = Query(default=""),
        sourceType: str = Query(default=""),
        module: str = Query(default=""),
        onlyPersonalBank: str = Query(default=""),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        items, total = svc.list_student_practice_questions(
            {
                "knowledgeId": knowledgeId.strip(),
                "knowledgePathNodeId": knowledge_path_node_id.strip(),
                "subjectId": subject_id.strip(),
                "chapter": chapter.strip(),
                "chapterCode": chapter_code.strip(),
                "pointCode": point_code.strip(),
                "type": type.strip(),
                "difficulty": difficulty.strip(),
                "keyword": keyword.strip(),
                "sourceType": sourceType.strip(),
                "module": module.strip(),
                "onlyPersonalBank": onlyPersonalBank.strip(),
                "examCategoryCode": exam_category_code.strip(),
                "jointExamGroupCode": joint_exam_group_code.strip(),
                "subjectCode": subject_code.strip(),
            },
            page,
            size,
            actor,
        )
        return success(pagination(items, page, size, total))

    @app.get("/api/question-bank/student/practice/chapters", response_model=BaseResponse)
    async def list_student_practice_chapters(
        subject_id: str = Query(default="", alias="subjectId"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.list_student_practice_chapters(subject_id.strip(), actor))

    @app.get("/api/question-bank/student/dashboard", response_model=BaseResponse)
    async def student_dashboard(
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.get_student_dashboard(actor))

    @app.get("/api/question-bank/student/subscription/plans", response_model=BaseResponse)
    async def list_student_subscription_plans(
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.list_student_subscription_plans(actor))

    @app.get("/api/question-bank/student/subscription/status", response_model=BaseResponse)
    async def get_student_subscription_status(
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.get_student_subscription_status(actor))

    @app.post("/api/question-bank/student/diagnosis/quick/start", response_model=BaseResponse)
    async def start_student_quick_diagnosis(
        payload: StudentDiagnosisQuickStartRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.start_student_quick_diagnosis(payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/student/diagnosis/quick/{sessionId}/submit", response_model=BaseResponse)
    async def submit_student_quick_diagnosis(
        sessionId: str,
        payload: StudentDiagnosisQuickSubmitRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.submit_student_quick_diagnosis(sessionId, payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/student/subscription/redeem", response_model=BaseResponse)
    async def redeem_student_subscription(
        payload: StudentSubscriptionRedeemRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.redeem_student_subscription(payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/student/subscription/mock-orders", response_model=BaseResponse)
    async def create_student_subscription_mock_order(
        payload: StudentSubscriptionMockOrderCreateRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.create_student_subscription_mock_order(payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/student/subscription/mock-orders/{orderId}/confirm", response_model=BaseResponse)
    async def confirm_student_subscription_mock_order(
        orderId: str,
        payload: StudentSubscriptionMockOrderConfirmRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.confirm_student_subscription_mock_order(orderId, payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/student/profile", response_model=BaseResponse)
    async def save_student_profile(
        payload: StudentProfileUpdateRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.save_student_profile(payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/student/submit", response_model=BaseResponse)
    async def submit_student_session(
        payload: StudentSessionSubmitRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.submit_student_session(payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/student/check-in", response_model=BaseResponse)
    async def student_check_in(
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.student_daily_check_in(actor))

    @app.post("/api/question-bank/student/practice/questions/{questionId}/submit", response_model=BaseResponse)
    async def submit_practice_answer(
        questionId: str,
        payload: StudentPracticeSubmitRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.submit_practice_answer(questionId, payload.model_dump(by_alias=True), actor))

    @app.get("/api/question-bank/student/challenge-points", response_model=BaseResponse)
    async def student_challenge_points(
        subject_code: str = Query(default="", alias="subjectCode"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.get_student_challenge_point_summary(subject_code.strip(), actor))

    @app.post("/api/question-bank/student/practice/questions/{questionId}/wrong-book", response_model=BaseResponse)
    async def collect_wrong_book_question(
        questionId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.collect_wrong_book_question(questionId, actor))

    @app.post("/api/question-bank/student/practice/questions/{questionId}/personal-bank", response_model=BaseResponse)
    async def toggle_personal_bank_question(
        questionId: str,
        payload: StudentPersonalBankToggleRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.toggle_personal_bank_question(questionId, payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/student/practice/questions/{questionId}/ai-marking", response_model=BaseResponse)
    async def submit_ai_marking(
        questionId: str,
        payload: StudentAiMarkingSubmitRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.submit_ai_marking(questionId, payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/student/practice/questions/{questionId}/ai-tutor", response_model=BaseResponse)
    async def ask_ai_tutor(
        questionId: str,
        payload: StudentAiTutorAskRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.ask_ai_tutor(questionId, payload.model_dump(by_alias=True), actor))

    @app.get("/api/question-bank/student/personal-bank/questions", response_model=BaseResponse)
    async def list_student_personal_bank_questions(
        page: int = Query(default=1, ge=1),
        size: int = Query(default=20, ge=1, le=100),
        subject_id: str = Query(default="", alias="subjectId"),
        exam_category_code: str = Query(default="", alias="examCategoryCode"),
        joint_exam_group_code: str = Query(default="", alias="jointExamGroupCode"),
        subject_code: str = Query(default="", alias="subjectCode"),
        question_ids: str = Query(default="", alias="questionIds"),
        chapter: str = Query(default=""),
        type: str = Query(default=""),
        difficulty: str = Query(default=""),
        keyword: str = Query(default=""),
        sourceType: str = Query(default=""),
        archiveWindow: str = Query(default=""),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        items, total = svc.list_personal_bank_questions(
            {
                "subjectId": subject_id.strip(),
                "chapter": chapter.strip(),
                "type": type.strip(),
                "difficulty": difficulty.strip(),
                "keyword": keyword.strip(),
                "sourceType": sourceType.strip(),
                "examCategoryCode": exam_category_code.strip(),
                "jointExamGroupCode": joint_exam_group_code.strip(),
                "subjectCode": subject_code.strip(),
                "archiveWindow": archiveWindow.strip(),
                "questionIds": question_ids.strip(),
            },
            page,
            size,
            actor,
        )
        return success(pagination(items, page, size, total))

    @app.get("/api/question-bank/student/personal-bank/summary", response_model=BaseResponse)
    async def student_personal_bank_summary(
        subject_id: str = Query(default="", alias="subjectId"),
        exam_category_code: str = Query(default="", alias="examCategoryCode"),
        joint_exam_group_code: str = Query(default="", alias="jointExamGroupCode"),
        subject_code: str = Query(default="", alias="subjectCode"),
        question_ids: str = Query(default="", alias="questionIds"),
        chapter: str = Query(default=""),
        keyword: str = Query(default=""),
        sourceType: str = Query(default=""),
        archiveWindow: str = Query(default=""),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(
            svc.get_personal_bank_summary(
                {
                    "subjectId": subject_id.strip(),
                    "chapter": chapter.strip(),
                    "keyword": keyword.strip(),
                    "sourceType": sourceType.strip(),
                    "examCategoryCode": exam_category_code.strip(),
                    "jointExamGroupCode": joint_exam_group_code.strip(),
                    "subjectCode": subject_code.strip(),
                    "archiveWindow": archiveWindow.strip(),
                    "questionIds": question_ids.strip(),
                },
                actor,
            )
        )

    @app.get("/api/question-bank/student/personal-bank/export", response_model=BaseResponse)
    async def student_personal_bank_export(
        subject_id: str = Query(default="", alias="subjectId"),
        exam_category_code: str = Query(default="", alias="examCategoryCode"),
        joint_exam_group_code: str = Query(default="", alias="jointExamGroupCode"),
        subject_code: str = Query(default="", alias="subjectCode"),
        question_ids: str = Query(default="", alias="questionIds"),
        chapter: str = Query(default=""),
        keyword: str = Query(default=""),
        sourceType: str = Query(default=""),
        format: str = Query(default="csv"),
        archiveWindow: str = Query(default=""),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(
            svc.export_personal_bank(
                {
                    "subjectId": subject_id.strip(),
                    "chapter": chapter.strip(),
                    "keyword": keyword.strip(),
                    "sourceType": sourceType.strip(),
                    "format": format.strip(),
                    "examCategoryCode": exam_category_code.strip(),
                    "jointExamGroupCode": joint_exam_group_code.strip(),
                    "subjectCode": subject_code.strip(),
                    "archiveWindow": archiveWindow.strip(),
                    "questionIds": question_ids.strip(),
                },
                actor,
            )
        )

    @app.get("/api/question-bank/student/personal-bank/review-plans", response_model=BaseResponse)
    async def list_student_personal_bank_review_plans(
        subject_id: str = Query(default="", alias="subjectId"),
        exam_category_code: str = Query(default="", alias="examCategoryCode"),
        joint_exam_group_code: str = Query(default="", alias="jointExamGroupCode"),
        subject_code: str = Query(default="", alias="subjectCode"),
        question_ids: str = Query(default="", alias="questionIds"),
        chapter: str = Query(default=""),
        keyword: str = Query(default=""),
        sourceType: str = Query(default=""),
        archiveWindow: str = Query(default=""),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(
            svc.list_student_personal_bank_review_plans(
                {
                    "subjectId": subject_id.strip(),
                    "chapter": chapter.strip(),
                    "keyword": keyword.strip(),
                    "sourceType": sourceType.strip(),
                    "examCategoryCode": exam_category_code.strip(),
                    "jointExamGroupCode": joint_exam_group_code.strip(),
                    "subjectCode": subject_code.strip(),
                    "archiveWindow": archiveWindow.strip(),
                    "questionIds": question_ids.strip(),
                },
                actor,
            )
        )

    @app.get("/api/question-bank/student/personal-bank/review-plans/{planId}", response_model=BaseResponse)
    async def get_student_personal_bank_review_plan(
        planId: str,
        subject_id: str = Query(default="", alias="subjectId"),
        exam_category_code: str = Query(default="", alias="examCategoryCode"),
        joint_exam_group_code: str = Query(default="", alias="jointExamGroupCode"),
        subject_code: str = Query(default="", alias="subjectCode"),
        question_ids: str = Query(default="", alias="questionIds"),
        chapter: str = Query(default=""),
        keyword: str = Query(default=""),
        sourceType: str = Query(default=""),
        archiveWindow: str = Query(default=""),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(
            svc.get_student_personal_bank_review_plan(
                planId,
                {
                    "subjectId": subject_id.strip(),
                    "chapter": chapter.strip(),
                    "keyword": keyword.strip(),
                    "sourceType": sourceType.strip(),
                    "examCategoryCode": exam_category_code.strip(),
                    "jointExamGroupCode": joint_exam_group_code.strip(),
                    "subjectCode": subject_code.strip(),
                    "archiveWindow": archiveWindow.strip(),
                    "questionIds": question_ids.strip(),
                },
                actor,
            )
        )

    @app.post("/api/question-bank/student/personal-bank/review-plans/{planId}/start", response_model=BaseResponse)
    async def start_student_personal_bank_review_plan(
        planId: str,
        subject_id: str = Query(default="", alias="subjectId"),
        exam_category_code: str = Query(default="", alias="examCategoryCode"),
        joint_exam_group_code: str = Query(default="", alias="jointExamGroupCode"),
        subject_code: str = Query(default="", alias="subjectCode"),
        question_ids: str = Query(default="", alias="questionIds"),
        chapter: str = Query(default=""),
        keyword: str = Query(default=""),
        sourceType: str = Query(default=""),
        archiveWindow: str = Query(default=""),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(
            svc.start_student_personal_bank_review_plan(
                planId,
                {
                    "subjectId": subject_id.strip(),
                    "chapter": chapter.strip(),
                    "keyword": keyword.strip(),
                    "sourceType": sourceType.strip(),
                    "examCategoryCode": exam_category_code.strip(),
                    "jointExamGroupCode": joint_exam_group_code.strip(),
                    "subjectCode": subject_code.strip(),
                    "archiveWindow": archiveWindow.strip(),
                    "questionIds": question_ids.strip(),
                },
                actor,
            )
        )

    @app.post("/api/question-bank/student/personal-bank/review-plans/{planId}/questions/{questionId}/complete", response_model=BaseResponse)
    async def complete_student_personal_bank_review_plan_question(
        planId: str,
        questionId: str,
        subject_id: str = Query(default="", alias="subjectId"),
        exam_category_code: str = Query(default="", alias="examCategoryCode"),
        joint_exam_group_code: str = Query(default="", alias="jointExamGroupCode"),
        subject_code: str = Query(default="", alias="subjectCode"),
        question_ids: str = Query(default="", alias="questionIds"),
        chapter: str = Query(default=""),
        keyword: str = Query(default=""),
        sourceType: str = Query(default=""),
        archiveWindow: str = Query(default=""),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(
            svc.complete_student_personal_bank_review_plan_question(
                planId,
                questionId,
                {
                    "subjectId": subject_id.strip(),
                    "chapter": chapter.strip(),
                    "keyword": keyword.strip(),
                    "sourceType": sourceType.strip(),
                    "examCategoryCode": exam_category_code.strip(),
                    "jointExamGroupCode": joint_exam_group_code.strip(),
                    "subjectCode": subject_code.strip(),
                    "archiveWindow": archiveWindow.strip(),
                    "questionIds": question_ids.strip(),
                },
                actor,
            )
        )

    @app.get("/api/question-bank/student/wrong-book/questions", response_model=BaseResponse)
    async def list_wrong_book_questions(
        page: int = Query(default=1, ge=1),
        size: int = Query(default=20, ge=1, le=100),
        knowledgeId: str = Query(default="", alias="knowledgeId"),
        knowledge_path_node_id: str = Query(default="", alias="knowledgePathNodeId"),
        chapter: str = Query(default=""),
        chapter_code: str = Query(default="", alias="chapterCode"),
        point_code: str = Query(default="", alias="pointCode"),
        subject_code: str = Query(default="", alias="subjectCode"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        items, total = svc.list_wrong_book_questions(
            page,
            size,
            actor,
            {
                "knowledgeId": knowledgeId.strip(),
                "knowledgePathNodeId": knowledge_path_node_id.strip(),
                "chapter": chapter.strip(),
                "chapterCode": chapter_code.strip(),
                "pointCode": point_code.strip(),
                "subjectCode": subject_code.strip(),
            },
        )
        return success(pagination(items, page, size, total))

    @app.get("/api/student/error-book/summary", response_model=BaseResponse, include_in_schema=False)
    @app.get("/api/question-bank/student/wrong-book/summary", response_model=BaseResponse)
    async def student_error_book_summary(
        subject_code: str = Query(default="", alias="subjectCode"),
        knowledgeId: str = Query(default="", alias="knowledgeId"),
        knowledge_path_node_id: str = Query(default="", alias="knowledgePathNodeId"),
        chapter: str = Query(default=""),
        chapter_code: str = Query(default="", alias="chapterCode"),
        point_code: str = Query(default="", alias="pointCode"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(
            svc.get_student_error_book_summary(
                {
                    "subjectCode": subject_code.strip(),
                    "knowledgeId": knowledgeId.strip(),
                    "knowledgePathNodeId": knowledge_path_node_id.strip(),
                    "chapter": chapter.strip(),
                    "chapterCode": chapter_code.strip(),
                    "pointCode": point_code.strip(),
                },
                actor,
            )
        )

    @app.get("/api/question-bank/teacher/error-book/students", response_model=BaseResponse)
    async def teacher_error_book_students(
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_analytics_operator(actor)
        ensure_actor_ready(actor, svc, "analytics:view")
        return success(svc.list_teacher_error_book_students(actor))

    @app.get("/api/question-bank/teacher/error-book/summary", response_model=BaseResponse)
    async def teacher_error_book_summary(
        student_user_id: str = Query(default="", alias="studentUserId"),
        legacy_user_id: str = Query(default="", alias="userId"),
        subject_code: str = Query(default="", alias="subjectCode"),
        subject_codes: str = Query(default="", alias="subjectCodes"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_analytics_operator(actor)
        ensure_actor_ready(actor, svc, "analytics:view")
        normalized_student_user_id = student_user_id.strip() or legacy_user_id.strip()
        return success(
            svc.get_teacher_error_book_summary(
                {
                    "studentUserId": normalized_student_user_id,
                    "subjectCode": subject_code.strip(),
                    "subjectCodes": subject_codes.strip(),
                },
                actor,
            )
        )

    @app.get("/api/question-bank/teacher/error-book/class-overview", response_model=BaseResponse)
    async def teacher_error_book_class_overview(
        class_id: str = Query(default="", alias="classId"),
        subject_code: str = Query(default="", alias="subjectCode"),
        subject_codes: str = Query(default="", alias="subjectCodes"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_analytics_operator(actor)
        ensure_actor_ready(actor, svc, "analytics:view")
        return success(
            svc.get_teacher_error_book_class_overview(
                {
                    "classId": class_id.strip(),
                    "subjectCode": subject_code.strip(),
                    "subjectCodes": subject_codes.strip(),
                },
                actor,
            )
        )

    @app.post("/api/question-bank/teacher/error-book/class-exports/report", response_model=BaseResponse)
    async def teacher_error_book_class_report(
        payload: Optional[dict[str, object]] = Body(default=None),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_analytics_operator(actor)
        ensure_actor_ready(actor, svc, "analytics:view")
        return success(svc.export_teacher_error_book_class_report(payload or {}, actor))

    @app.post("/api/question-bank/teacher/error-book/class-exports/package", response_model=BaseResponse)
    async def teacher_error_book_class_package(
        payload: Optional[dict[str, object]] = Body(default=None),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_analytics_operator(actor)
        ensure_actor_ready(actor, svc, "analytics:view")
        return success(svc.export_teacher_error_book_class_package(payload or {}, actor))

    @app.get("/api/question-bank/teacher/error-book/questions", response_model=BaseResponse)
    async def teacher_error_book_questions(
        page: int = Query(default=1, ge=1),
        size: int = Query(default=100, ge=1, le=200),
        student_user_id: str = Query(default="", alias="studentUserId"),
        legacy_user_id: str = Query(default="", alias="userId"),
        subject_code: str = Query(default="", alias="subjectCode"),
        subject_codes: str = Query(default="", alias="subjectCodes"),
        knowledgeId: str = Query(default="", alias="knowledgeId"),
        knowledge_path_node_id: str = Query(default="", alias="knowledgePathNodeId"),
        chapter: str = Query(default=""),
        chapter_code: str = Query(default="", alias="chapterCode"),
        point_code: str = Query(default="", alias="pointCode"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_analytics_operator(actor)
        ensure_actor_ready(actor, svc, "analytics:view")
        normalized_student_user_id = student_user_id.strip() or legacy_user_id.strip()
        items, total = svc.list_teacher_wrong_book_questions(
            {
                "studentUserId": normalized_student_user_id,
                "subjectCode": subject_code.strip(),
                "subjectCodes": subject_codes.strip(),
                "knowledgeId": knowledgeId.strip(),
                "knowledgePathNodeId": knowledge_path_node_id.strip(),
                "chapter": chapter.strip(),
                "chapterCode": chapter_code.strip(),
                "pointCode": point_code.strip(),
            },
            page,
            size,
            actor,
        )
        return success(pagination(items, page, size, total))

    @app.get("/api/question-bank/teacher/error-book/questions/{questionId}/similar", response_model=BaseResponse)
    async def teacher_error_book_similar_questions(
        questionId: str,
        student_user_id: str = Query(default="", alias="studentUserId"),
        legacy_user_id: str = Query(default="", alias="userId"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_analytics_operator(actor)
        ensure_actor_ready(actor, svc, "analytics:view")
        normalized_student_user_id = student_user_id.strip() or legacy_user_id.strip()
        return success(
            svc.list_teacher_similar_wrong_book_questions(
                questionId,
                {
                    "studentUserId": normalized_student_user_id,
                },
                actor,
            )
        )

    @app.post("/api/question-bank/teacher/error-book/exports/word", response_model=BaseResponse)
    async def teacher_error_book_export_word(
        payload: Optional[dict[str, object]] = Body(default=None),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_analytics_operator(actor)
        ensure_actor_ready(actor, svc, "analytics:view")
        return success(svc.export_teacher_error_book_word(payload or {}, actor))

    @app.get("/api/student/error-book/questions/{questionId}/similar", response_model=BaseResponse, include_in_schema=False)
    @app.get("/api/question-bank/student/wrong-book/questions/{questionId}/similar", response_model=BaseResponse)
    async def student_error_book_similar_questions(
        questionId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.list_similar_wrong_book_questions(questionId, actor))

    @app.post("/api/student/error-book/exports/word", response_model=BaseResponse, include_in_schema=False)
    @app.post("/api/question-bank/student/wrong-book/exports/word", response_model=BaseResponse)
    async def student_error_book_export_word(
        payload: Optional[dict[str, object]] = Body(default=None),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.export_wrong_book_word(payload or {}, actor))

    @app.post("/api/question-bank/student/wrong-book/questions/{questionId}/review", response_model=BaseResponse)
    async def review_wrong_book_question(
        questionId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.review_wrong_book_question(questionId, actor))

    @app.post("/api/question-bank/student/wrong-book/archive-harvested", response_model=BaseResponse)
    async def archive_student_wrong_book_harvested(
        payload: Optional[dict[str, object]] = Body(default=None),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.archive_wrong_book_questions(payload or {}, actor))

    @app.post("/api/question-bank/student/wrong-book/restore-archived", response_model=BaseResponse)
    async def restore_student_wrong_book_archived(
        payload: Optional[dict[str, object]] = Body(default=None),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.restore_archived_wrong_book_questions(payload or {}, actor))

    @app.post("/api/question-bank/student/wrong-book/papers", response_model=BaseResponse)
    async def generate_personalized_wrong_book_paper(
        subject_code: str = Query(default="", alias="subjectCode"),
        knowledgeId: str = Query(default="", alias="knowledgeId"),
        knowledge_path_node_id: str = Query(default="", alias="knowledgePathNodeId"),
        chapter: str = Query(default=""),
        chapter_code: str = Query(default="", alias="chapterCode"),
        point_code: str = Query(default="", alias="pointCode"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(
            svc.generate_personalized_wrong_book_paper(
                actor,
                {
                    "subjectCode": subject_code.strip(),
                    "knowledgeId": knowledgeId.strip(),
                    "knowledgePathNodeId": knowledge_path_node_id.strip(),
                    "chapter": chapter.strip(),
                    "chapterCode": chapter_code.strip(),
                    "pointCode": point_code.strip(),
                },
            )
        )

    @app.post("/api/question-bank/student/wrong-book/papers/reasoned", response_model=BaseResponse)
    async def generate_reasoned_wrong_book_paper(
        reasonCode: str = Query(default=""),
        questionCount: int = Query(default=12, ge=5, le=30),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.generate_reasoned_wrong_book_paper(actor, reasonCode.strip(), questionCount))

    @app.get("/api/question-bank/student/papers/questions", response_model=BaseResponse)
    async def list_student_available_paper_questions(
        page: int = Query(default=1, ge=1),
        size: int = Query(default=100, ge=1, le=200),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        items, total = svc.list_student_available_paper_questions(page, size, actor)
        return success(pagination(items, page, size, total))

    @app.get("/api/question-bank/student/exam-tasks", response_model=BaseResponse)
    async def list_student_exam_tasks(
        page: int = Query(default=1, ge=1),
        size: int = Query(default=20, ge=1, le=200),
        status: str = Query(default=""),
        taskType: str = Query(default=""),
        subject_code: str = Query(default="", alias="subjectCode"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        items, total = svc.list_student_exam_tasks(
            {
                "status": status.strip(),
                "taskType": taskType.strip(),
                "subjectCode": subject_code.strip(),
            },
            page,
            size,
            actor,
        )
        return success(pagination(items, page, size, total))

    @app.get("/api/question-bank/student/exam-tasks/{assignmentId}", response_model=BaseResponse)
    async def get_student_exam_task_detail(
        assignmentId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.get_student_exam_task_detail(assignmentId, actor))

    @app.post("/api/question-bank/student/exam-tasks/{assignmentId}/start", response_model=BaseResponse)
    async def start_student_exam_task(
        assignmentId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.start_student_exam_task(assignmentId, actor))

    @app.post("/api/question-bank/student/exam-tasks/{assignmentId}/submit", response_model=BaseResponse)
    async def submit_student_exam_task(
        assignmentId: str,
        payload: dict = Body(default_factory=dict),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.submit_student_exam_task(assignmentId, payload, actor))

    @app.post("/api/question-bank/student/mock-exams/start", response_model=BaseResponse)
    async def start_student_mock_exam(
        payload: StudentMockExamStartRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.start_student_mock_exam(payload.model_dump(by_alias=True), actor))

    @app.get("/api/question-bank/student/mock-exams/{sessionId}", response_model=BaseResponse)
    async def get_student_mock_exam_session(
        sessionId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.get_student_mock_exam_session(sessionId, actor))

    @app.get("/api/question-bank/student/papers/reports", response_model=BaseResponse)
    async def list_student_paper_reports(
        page: int = Query(default=1, ge=1),
        size: int = Query(default=20, ge=1, le=200),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        items, total = svc.list_student_paper_reports(page, size, actor)
        return success(pagination(items, page, size, total))

    @app.get("/api/question-bank/student/papers/reports/{reportId}", response_model=BaseResponse)
    async def get_student_paper_report_detail(
        reportId: str,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.get_student_paper_report_detail(reportId, actor))

    @app.get("/api/question-bank/student/papers/{paperId}/questions", response_model=BaseResponse)
    async def list_student_paper_questions(
        paperId: str,
        page: int = Query(default=1, ge=1),
        size: int = Query(default=50, ge=1, le=200),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        items, total = svc.list_student_paper_questions(paperId, page, size, actor)
        return success(pagination(items, page, size, total))

    @app.post("/api/question-bank/student/papers/{paperId}/submit", response_model=BaseResponse)
    async def submit_student_paper(
        paperId: str,
        payload: StudentPaperSubmitRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.submit_student_paper(paperId, payload.model_dump(by_alias=True), actor))

    @app.post("/api/question-bank/student/papers/{paperId}/questions/{questionId}/check", response_model=BaseResponse)
    async def submit_student_paper_question(
        paperId: str,
        questionId: str,
        payload: StudentPracticeSubmitRequest,
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_student(actor)
        ensure_actor_ready(actor, svc)
        return success(svc.submit_student_paper_question(paperId, questionId, payload.model_dump(by_alias=True), actor))

    @app.get("/api/question-bank/analytics/records", response_model=BaseResponse)
    async def list_analytics_records(
        page: int = Query(default=1, ge=1),
        size: int = Query(default=20, ge=1, le=200),
        keyword: str = Query(default=""),
        subject_id: str = Query(default="", alias="subjectId"),
        chapter: str = Query(default=""),
        student_user_id: str = Query(default="", alias="userId"),
        start_date: str = Query(default="", alias="startDate"),
        end_date: str = Query(default="", alias="endDate"),
        exam_category_code: str = Query(default="", alias="examCategoryCode"),
        joint_exam_group_code: str = Query(default="", alias="jointExamGroupCode"),
        subject_code: str = Query(default="", alias="subjectCode"),
        policy_version: str = Query(default="HB_ZSB_2026", alias="policyVersion"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_analytics_operator(actor)
        ensure_actor_ready(actor, svc, "analytics:view")
        normalized_exam_category_code = exam_category_code.strip()
        normalized_joint_exam_group_code = joint_exam_group_code.strip()
        normalized_subject_code = subject_code.strip()
        normalized_policy_version = policy_version.strip() or "HB_ZSB_2026"
        items, total = svc.list_analytics_records(
            {
                "subjectId": subject_id.strip(),
                "chapter": chapter.strip(),
                "keyword": keyword.strip(),
                "studentUserId": student_user_id.strip(),
                "startDate": start_date.strip(),
                "endDate": end_date.strip(),
                "examCategoryCode": normalized_exam_category_code,
                "jointExamGroupCode": normalized_joint_exam_group_code,
                "subjectCode": normalized_subject_code,
                "policyVersion": normalized_policy_version,
            },
            page,
            size,
            actor,
        )
        return success(pagination(items, page, size, total))

    @app.get("/api/question-bank/analytics/summary", response_model=BaseResponse)
    async def analytics_summary(
        keyword: str = Query(default=""),
        subject_id: str = Query(default="", alias="subjectId"),
        chapter: str = Query(default=""),
        student_user_id: str = Query(default="", alias="userId"),
        start_date: str = Query(default="", alias="startDate"),
        end_date: str = Query(default="", alias="endDate"),
        exam_category_code: str = Query(default="", alias="examCategoryCode"),
        joint_exam_group_code: str = Query(default="", alias="jointExamGroupCode"),
        subject_code: str = Query(default="", alias="subjectCode"),
        policy_version: str = Query(default="HB_ZSB_2026", alias="policyVersion"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        normalized_student_user_id = student_user_id.strip()
        if actor.role == "student":
            require_student(actor)
            ensure_actor_ready(actor, svc)
            normalized_student_user_id = actor.user_id
        else:
            require_analytics_operator(actor)
            ensure_actor_ready(actor, svc, "analytics:view")
        normalized_exam_category_code = exam_category_code.strip()
        normalized_joint_exam_group_code = joint_exam_group_code.strip()
        normalized_subject_code = subject_code.strip()
        normalized_policy_version = policy_version.strip() or "HB_ZSB_2026"
        return success(
            svc.build_analytics_summary(
                {
                    "subjectId": subject_id.strip(),
                    "chapter": chapter.strip(),
                    "keyword": keyword.strip(),
                    "studentUserId": normalized_student_user_id,
                    "startDate": start_date.strip(),
                    "endDate": end_date.strip(),
                    "examCategoryCode": normalized_exam_category_code,
                    "jointExamGroupCode": normalized_joint_exam_group_code,
                    "subjectCode": normalized_subject_code,
                    "policyVersion": normalized_policy_version,
                },
                actor,
            )
        )

    @app.get("/api/question-bank/analytics/export", response_model=BaseResponse)
    async def analytics_export(
        keyword: str = Query(default=""),
        subject_id: str = Query(default="", alias="subjectId"),
        chapter: str = Query(default=""),
        student_user_id: str = Query(default="", alias="userId"),
        start_date: str = Query(default="", alias="startDate"),
        end_date: str = Query(default="", alias="endDate"),
        format: str = Query(default="csv"),
        exam_category_code: str = Query(default="", alias="examCategoryCode"),
        joint_exam_group_code: str = Query(default="", alias="jointExamGroupCode"),
        subject_code: str = Query(default="", alias="subjectCode"),
        policy_version: str = Query(default="HB_ZSB_2026", alias="policyVersion"),
        actor: Actor = Depends(get_actor),
        svc: QuestionBankService = Depends(service),
    ):
        require_analytics_operator(actor)
        ensure_actor_ready(actor, svc, "analytics:view")
        normalized_exam_category_code = exam_category_code.strip()
        normalized_joint_exam_group_code = joint_exam_group_code.strip()
        normalized_subject_code = subject_code.strip()
        normalized_policy_version = policy_version.strip() or "HB_ZSB_2026"
        return success(
            svc.export_analytics(
                {
                    "subjectId": subject_id.strip(),
                    "chapter": chapter.strip(),
                    "keyword": keyword.strip(),
                    "studentUserId": student_user_id.strip(),
                    "startDate": start_date.strip(),
                    "endDate": end_date.strip(),
                    "format": format.strip(),
                    "examCategoryCode": normalized_exam_category_code,
                    "jointExamGroupCode": normalized_joint_exam_group_code,
                    "subjectCode": normalized_subject_code,
                    "policyVersion": normalized_policy_version,
                },
                actor,
            )
        )

    @app.get("/{frontend_path:path}", include_in_schema=False)
    async def frontend_entry_fallback(frontend_path: str, request: Request):
        normalized_path = str(frontend_path or "").strip()
        if normalized_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")

        frontend_file = resolve_frontend_dist_file(normalized_path)
        if frontend_file is not None:
            return FileResponse(frontend_file)

        frontend_response = build_frontend_entry_response(request)
        if frontend_response:
            return frontend_response

        raise HTTPException(status_code=404, detail="Not Found")

    return app


app = create_app()
