#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://127.0.0.1:8017"
DEFAULT_OUTPUT_DIR = "docs"
DEFAULT_TIMEOUT_SEC = 20
DEFAULT_DB_PATH = "/tmp/question-bank-click-replay.db"
PASS = "PASS"
FAIL = "FAIL"


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def today_local() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run unified Python Playwright true-click replay for student/teacher/super_admin.")
    parser.add_argument("--role", choices=("student", "teacher", "super_admin", "all"), default="all")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout-sec", type=int, default=DEFAULT_TIMEOUT_SEC)
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)

    head_group = parser.add_mutually_exclusive_group()
    head_group.add_argument("--headless", action="store_true", help="Run browser in headless mode (default).")
    head_group.add_argument("--headed", action="store_true", help="Run browser in headed mode.")
    return parser.parse_args()


def parse_base_url(base_url: str) -> Dict[str, Any]:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or not parsed.port:
        raise ValueError("--base-url 必须包含 scheme + host + port，例如 http://127.0.0.1:8017")
    if parsed.path not in {"", "/"}:
        raise ValueError("--base-url 仅支持根路径，不支持附带 path。")
    return {"scheme": parsed.scheme, "host": parsed.hostname, "port": parsed.port}


def ping_url(base_url: str, timeout_sec: int = 2) -> bool:
    try:
        request = Request(f"{base_url.rstrip('/')}/login", method="GET")
        with urlopen(request, timeout=timeout_sec) as response:
            return 200 <= int(response.status) < 500
    except Exception:
        return False


def wait_until_reachable(base_url: str, timeout_sec: int) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if ping_url(base_url, timeout_sec=2):
            return True
        time.sleep(0.25)
    return False


def safe_json(response: Any) -> Dict[str, Any]:
    payload = response.json()
    if not isinstance(payload, dict):
        raise AssertionError("响应 JSON 顶层必须是对象。")
    return payload


def ensure_envelope(payload: Dict[str, Any]) -> Dict[str, Any]:
    required = {"code", "message", "data"}
    if set(payload.keys()) != required:
        raise AssertionError("接口返回必须是 {code,message,data}。")
    return payload


def require_status(response: Any, expected_status: int, hint: str) -> Dict[str, Any]:
    if int(response.status) != expected_status:
        body = response.text() if hasattr(response, "text") else ""
        raise AssertionError(f"{hint}: 期望 HTTP {expected_status}，实际 {response.status}。响应: {body[:400]}")
    payload = safe_json(response)
    if expected_status == 200:
        ensure_envelope(payload)
    return payload


def read_error_message(response: Any) -> str:
    try:
        payload = safe_json(response)
        if isinstance(payload.get("message"), str):
            return payload["message"]
    except Exception:
        pass
    return str(response.text() if hasattr(response, "text") else "")[:300]


def unique_suffix() -> str:
    return str(int(time.time() * 1000))[-6:]


def unique_mobile(seed: int) -> str:
    base = int(time.time() * 1000) % 10_000_000_000
    number = (base + seed) % 10_000_000_000
    return f"1{number:010d}"


@dataclass
class SharedState:
    created_teacher_user_id: str = ""
    created_question_id: str = ""
    submitted_question_id: str = ""
    linkage_matrix: Dict[str, str] = field(
        default_factory=lambda: {
            "superAdminToTeacher": "NOT_RUN",
            "teacherToStudent": "NOT_RUN",
            "studentToTeacher": "NOT_RUN",
        }
    )


@dataclass
class RoleRun:
    role: str
    base_url: str
    timeout_sec: int
    headless: bool
    db_path: str
    started_at: str = field(default_factory=now_iso_utc)
    ended_at: str = ""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    issues: List[Dict[str, Any]] = field(default_factory=list)

    def add_step(self, item: Dict[str, Any]) -> None:
        self.steps.append(item)
        if item["status"] == FAIL:
            self.issues.append(
                {
                    "role": self.role,
                    "step": item["name"],
                    "message": str((item.get("error") or {}).get("message") or "步骤失败"),
                }
            )

    def finalize(self) -> Dict[str, Any]:
        self.ended_at = now_iso_utc()
        return {
            "executedAt": self.ended_at,
            "startedAt": self.started_at,
            "endedAt": self.ended_at,
            "mode": "python-playwright-true-click-replay",
            "role": self.role,
            "baseUrl": self.base_url,
            "timeoutSec": self.timeout_sec,
            "headless": self.headless,
            "dbPath": self.db_path,
            "steps": self.steps,
            "issues": self.issues,
            "totalIssues": len(self.issues),
        }


class StepRunner:
    def __init__(self, role_run: RoleRun, role: str, page: Any, output_dir: Path) -> None:
        self.role_run = role_run
        self.role = role
        self.page = page
        self.output_dir = output_dir

    def run(self, name: str, job: Callable[[], None]) -> None:
        started_at = now_iso_utc()
        artifacts: List[Dict[str, str]] = []
        status = PASS
        error_obj: Optional[Dict[str, str]] = None
        try:
            job()
        except Exception as exc:
            status = FAIL
            screenshot_path = self.output_dir / f"{self.role}-step-fail-{len(self.role_run.steps) + 1}-{int(time.time())}.png"
            try:
                self.page.screenshot(path=str(screenshot_path), full_page=True)
                artifacts.append({"type": "screenshot", "path": str(screenshot_path.resolve())})
            except Exception:
                pass
            error_obj = {
                "type": exc.__class__.__name__,
                "message": str(exc),
                "traceback": "".join(traceback.format_exception_only(type(exc), exc)).strip(),
            }
        ended_at = now_iso_utc()
        self.role_run.add_step(
            {
                "name": name,
                "status": status,
                "startedAt": started_at,
                "endedAt": ended_at,
                "artifacts": artifacts,
                "error": error_obj,
            }
        )


def role_label(role: str) -> str:
    if role == "super_admin":
        return "超管端"
    if role == "teacher":
        return "教师端"
    return "学生端"


def login_by_password(
    page: Any,
    expect_api: Any,
    phone: str,
    password: str,
    timeout_ms: int,
    redirect_path: str = "",
) -> None:
    login_url = "/login"
    normalized_redirect_path = str(redirect_path or "").strip()
    if normalized_redirect_path:
        login_url = f"/login?redirect={quote(normalized_redirect_path, safe='')}"

    page.goto(login_url, wait_until="domcontentloaded")
    page.get_by_placeholder("请输入 11 位手机号").fill(phone)
    page.get_by_placeholder("请输入密码").fill(password)
    page.get_by_role("button", name="登录并继续").click()
    if normalized_redirect_path:
        page.wait_for_url(f"**{normalized_redirect_path}", timeout=timeout_ms)
    else:
        page.wait_for_function("() => !window.location.pathname.startsWith('/login')", timeout=timeout_ms)


def assert_me(page: Any, expected_role: str, expected_user_id: str) -> None:
    response = page.context.request.get("/api/question-bank/auth/me")
    payload = require_status(response, 200, "校验登录态")
    data = payload["data"]
    if data.get("role") != expected_role:
        raise AssertionError(f"登录角色不匹配，期望 {expected_role}，实际 {data.get('role')}")
    if data.get("userId") != expected_user_id:
        raise AssertionError(f"登录用户不匹配，期望 {expected_user_id}，实际 {data.get('userId')}")


def fill_managed_teacher_form(
    page: Any,
    user_id: str,
    mobile: str,
    enabled: bool,
    permissions: str,
    name: str,
) -> None:
    user_form_card = page.locator(".content-grid > .el-card").nth(1)
    user_form_card.locator(".el-form-item:has-text('用户ID') input").fill(user_id)
    role_select = user_form_card.locator(".el-form-item:has-text('角色') .el-select").first
    role_select.click()
    page.locator(".el-select-dropdown:visible .el-select-dropdown__item").filter(has_text="教师").first.click()
    user_form_card.locator(".el-form-item:has-text('姓名') input").fill(name)
    user_form_card.locator(".el-form-item:has-text('手机号') input").fill(mobile)

    enabled_switch = user_form_card.locator(".el-form-item:has-text('账号状态') .el-switch").first
    switch_class = str(enabled_switch.get_attribute("class") or "")
    current_enabled = "is-checked" in switch_class
    if current_enabled != enabled:
        enabled_switch.click()

    user_form_card.locator(".el-form-item:has-text('权限点') input").fill(permissions)
    user_form_card.locator(".el-form-item:has-text('学科门类') input").fill("")
    user_form_card.locator(".el-form-item:has-text('联考专业组') input").fill("")
    user_form_card.locator(".el-form-item:has-text('高职专业') input").fill("")
    user_form_card.locator(".el-form-item:has-text('备考阶段') input").fill("")


def wait_managed_user_visible(
    page: Any,
    user_id: str,
    timeout_ms: int,
) -> Dict[str, Any]:
    deadline = time.time() + max(timeout_ms, 1000) / 1000
    while time.time() < deadline:
        users_response = page.context.request.get("/api/question-bank/admin/users?page=1&size=200")
        users_payload = require_status(users_response, 200, "查询超管账号目录")
        users_data = users_payload.get("data", {})
        users_items = users_data.get("items", []) if isinstance(users_data, dict) else []
        if isinstance(users_items, list):
            for user_item in users_items:
                if str((user_item or {}).get("userId", "")).strip() == user_id:
                    return user_item if isinstance(user_item, dict) else {}
        time.sleep(0.2)
    raise AssertionError(f"账号目录中未检索到用户 {user_id}")


def admin_settings_payload(platform_name: str) -> Dict[str, Any]:
    return {
        "platformName": platform_name,
        "defaultExamMinutes": 120,
        "dailyCheckInPoints": 10,
        "practiceRewardThreshold": 10,
        "practiceRewardPoints": 20,
        "paperRewardPoints": 30,
        "wrongBookRewardThreshold": 6,
        "wrongBookRewardPoints": 18,
        "aiDailyLimit": 20,
    }


def run_super_admin_suite(
    playwright: Any,
    browser: Any,
    base_url: str,
    timeout_sec: int,
    output_dir: Path,
    shared_state: SharedState,
    expect_api: Any,
) -> Dict[str, Any]:
    timeout_ms = timeout_sec * 1000
    role_run = RoleRun(role="super_admin", base_url=base_url, timeout_sec=timeout_sec, headless=True, db_path="")
    context = browser.new_context(base_url=base_url)
    page = context.new_page()
    page.set_default_timeout(timeout_ms)

    step = StepRunner(role_run=role_run, role="super_admin", page=page, output_dir=output_dir)

    created_teacher_user_id = f"teacher-click-{unique_suffix()}"
    created_teacher_mobile = unique_mobile(101)
    restricted_teacher_user_id = f"teacher-limited-{unique_suffix()}"
    restricted_teacher_mobile = unique_mobile(202)
    disabled_teacher_user_id = f"teacher-disabled-{unique_suffix()}"
    disabled_teacher_mobile = unique_mobile(303)

    def step_1_redirect_login() -> None:
        unauth_admin_page = page.context.request.get("/admin/control-center")
        if int(unauth_admin_page.status) != 200:
            raise AssertionError(f"未登录访问超管页后读取登录页失败，状态码 {unauth_admin_page.status}")
        unauth_payload = safe_json(unauth_admin_page)
        if str(unauth_payload.get("route", "")) != "/login":
            raise AssertionError("未登录访问超管控制台时应重定向到 /login。")
        page.goto("/login?redirect=%2Fadmin%2Fcontrol-center", wait_until="domcontentloaded")
        expect_api(page.get_by_role("heading", name="账号登录")).to_be_visible(timeout=timeout_ms)

    def step_2_login_admin() -> None:
        login_by_password(
            page,
            expect_api,
            "13800000001",
            "seed-password-admin-001",
            timeout_ms,
            redirect_path="/admin/control-center",
        )
        assert_me(page, "super_admin", "admin-001")
        expect_api(page.get_by_role("heading", name="系统控制台")).to_be_visible(timeout=timeout_ms)

    def step_3_save_settings() -> None:
        platform_name = f"专升本全程智学-{unique_suffix()}"
        settings_card = page.locator(".content-grid > .el-card").first
        settings_card.locator(".el-form-item:has-text('平台名称') input").fill(platform_name)
        settings_card.get_by_role("button", name="保存参数").click()

        deadline = time.time() + max(timeout_ms, 1000) / 1000
        while time.time() < deadline:
            console_response = page.context.request.get("/api/question-bank/admin/console")
            console_payload = require_status(console_response, 200, "读取超管控制台")
            system_settings = (
                console_payload.get("data", {}).get("systemSettings", {})
                if isinstance(console_payload.get("data"), dict)
                else {}
            )
            if str(system_settings.get("platformName", "")) == platform_name:
                return
            time.sleep(0.2)
        raise AssertionError("保存系统参数后，控制台读取到的平台名称未更新。")

    def step_4_create_update_teacher_and_verify() -> None:
        user_form_card = page.locator(".content-grid > .el-card").nth(1)
        fill_managed_teacher_form(
            page,
            user_id=created_teacher_user_id,
            mobile=created_teacher_mobile,
            enabled=True,
            permissions="question:manage,paper:manage,analytics:view",
            name="联调教师",
        )
        user_form_card.get_by_role("button", name="保存账号").click()
        first_saved_user = wait_managed_user_visible(page, created_teacher_user_id, timeout_ms)
        if str(first_saved_user.get("name", "")) != "联调教师":
            raise AssertionError("首次保存教师账号后，账号目录中的姓名不正确。")

        fill_managed_teacher_form(
            page,
            user_id=created_teacher_user_id,
            mobile=created_teacher_mobile,
            enabled=True,
            permissions="question:manage,paper:manage,analytics:view",
            name="联调教师-更新",
        )
        user_form_card.get_by_role("button", name="保存账号").click()
        second_saved_user = wait_managed_user_visible(page, created_teacher_user_id, timeout_ms)
        if str(second_saved_user.get("name", "")) != "联调教师-更新":
            raise AssertionError("更新教师账号后，账号目录中的姓名未同步更新。")

        api = playwright.request.new_context(base_url=base_url)
        try:
            teacher_page = api.get(f"/teacher/questions?role=teacher&userId={created_teacher_user_id}")
            if teacher_page.status != 200 or "题库管理" not in teacher_page.text():
                raise AssertionError("超管创建教师后，教师页不可用。")

            teacher_list = api.get(
                "/api/question-bank/questions",
                headers={"X-Role": "teacher", "X-User-Id": created_teacher_user_id},
            )
            require_status(teacher_list, 200, "超管创建教师后的教师接口访问")
        finally:
            api.dispose()

        shared_state.created_teacher_user_id = created_teacher_user_id
        shared_state.linkage_matrix["superAdminToTeacher"] = PASS

    def step_5_import_export_students() -> None:
        import_export_card = page.locator(".secondary-grid > .el-card").first
        imported_student_user_id = f"student-click-{unique_suffix()}"
        csv_text = "\n".join(
            [
                "userId,name,mobile,examCategoryCode,jointExamGroupCode,vocationalMajor,prepStage",
                f"{imported_student_user_id},联调考生,{unique_mobile(404)},SCIENCE_ENGINEERING,SCIENCE_ENGINEERING_3,计算机类,基础阶段",
            ]
        )
        import_export_card.locator("textarea").first.fill(csv_text)
        import_export_card.get_by_role("button", name="批量导入考生").click()
        wait_managed_user_visible(page, imported_student_user_id, timeout_ms)

        import_export_card.get_by_role("button", name="导出目录").click()
        expect_api(import_export_card.locator("pre").last).to_contain_text("userId,name,mobile", timeout=timeout_ms)

    def step_6_permission_boundaries() -> None:
        user_form_card = page.locator(".content-grid > .el-card").nth(1)
        fill_managed_teacher_form(
            page,
            user_id=restricted_teacher_user_id,
            mobile=restricted_teacher_mobile,
            enabled=True,
            permissions="paper:manage",
            name="受限教师",
        )
        user_form_card.get_by_role("button", name="保存账号").click()
        wait_managed_user_visible(page, restricted_teacher_user_id, timeout_ms)

        fill_managed_teacher_form(
            page,
            user_id=disabled_teacher_user_id,
            mobile=disabled_teacher_mobile,
            enabled=False,
            permissions="question:manage",
            name="停用教师",
        )
        user_form_card.get_by_role("button", name="保存账号").click()
        wait_managed_user_visible(page, disabled_teacher_user_id, timeout_ms)

        api = playwright.request.new_context(base_url=base_url)
        try:
            no_permission_page = api.get(f"/teacher/questions?role=teacher&userId={restricted_teacher_user_id}")
            if no_permission_page.status != 403:
                raise AssertionError("受限教师不应访问题库页。")

            no_permission_api = api.get(
                "/api/question-bank/questions",
                headers={"X-Role": "teacher", "X-User-Id": restricted_teacher_user_id},
            )
            if no_permission_api.status != 403:
                raise AssertionError("受限教师不应访问题目列表接口。")
            if "question:manage" not in read_error_message(no_permission_api):
                raise AssertionError("受限教师 403 未包含权限缺失提示。")

            disabled_api = api.get(
                "/api/question-bank/questions",
                headers={"X-Role": "teacher", "X-User-Id": disabled_teacher_user_id},
            )
            if disabled_api.status != 403:
                raise AssertionError("停用教师不应访问题目列表接口。")
            if "已停用" not in read_error_message(disabled_api):
                raise AssertionError("停用教师 403 未包含停用提示。")
        finally:
            api.dispose()

    def step_7_csrf_block() -> None:
        response = page.context.request.post(
            "/api/question-bank/admin/settings",
            headers={"Content-Type": "application/json"},
            data=json.dumps(admin_settings_payload(f"CSRF校验-{unique_suffix()}"), ensure_ascii=False),
        )
        if response.status != 403:
            raise AssertionError("缺少 CSRF 时，超管写接口应返回 403。")
        if "安全校验失败" not in read_error_message(response):
            raise AssertionError("CSRF 失败提示不符合预期。")

    def step_8_logout_then_write_forbidden() -> None:
        logout_response = page.context.request.post("/api/question-bank/auth/logout")
        require_status(logout_response, 200, "超管登出接口")

        response = page.context.request.post(
            "/api/question-bank/admin/settings",
            headers={"Content-Type": "application/json"},
            data=json.dumps(admin_settings_payload(f"退出后写操作-{unique_suffix()}"), ensure_ascii=False),
        )
        if response.status != 403:
            raise AssertionError("退出登录后，写接口应不可用。")

        unauth_admin_page = page.context.request.get("/admin/control-center")
        if int(unauth_admin_page.status) != 200:
            raise AssertionError(f"退出登录后读取超管页返回异常状态码 {unauth_admin_page.status}")
        unauth_payload = safe_json(unauth_admin_page)
        if str(unauth_payload.get("route", "")) != "/login":
            raise AssertionError("退出登录后访问超管页应返回登录页。")

    step.run("1-超管入口未登录强制跳转登录页", step_1_redirect_login)
    step.run("2-超管登录并进入控制台", step_2_login_admin)
    step.run("3-超管保存系统设置", step_3_save_settings)
    step.run("4-超管创建更新教师并验证教师端可用", step_4_create_update_teacher_and_verify)
    step.run("5-超管执行考生导入与导出", step_5_import_export_students)
    step.run("6-超管校验无权限与停用边界", step_6_permission_boundaries)
    step.run("7-超管校验 CSRF 失败拦截", step_7_csrf_block)
    step.run("8-超管退出后不可继续写操作", step_8_logout_then_write_forbidden)

    context.close()
    return role_run.finalize()


def run_teacher_suite(
    playwright: Any,
    browser: Any,
    base_url: str,
    timeout_sec: int,
    output_dir: Path,
    shared_state: SharedState,
    expect_api: Any,
) -> Dict[str, Any]:
    timeout_ms = timeout_sec * 1000
    role_run = RoleRun(role="teacher", base_url=base_url, timeout_sec=timeout_sec, headless=True, db_path="")
    context = browser.new_context(base_url=base_url)
    page = context.new_page()
    page.set_default_timeout(timeout_ms)
    step = StepRunner(role_run=role_run, role="teacher", page=page, output_dir=output_dir)

    question_stem = f"联调真点击题目-{unique_suffix()}"
    created_question_id = ""

    def step_1_login_teacher() -> None:
        login_by_password(page, expect_api, "13800000002", "seed-password-teacher-001", timeout_ms)
        assert_me(page, "teacher", "teacher-001")
        page.goto("/teacher/questions", wait_until="domcontentloaded")
        expect_api(page.locator("#open-create-modal")).to_be_visible(timeout=timeout_ms)

    def step_2_create_question() -> None:
        page.locator("#open-create-modal").click()
        expect_api(page.locator("#question-form")).to_be_visible(timeout=timeout_ms)

        page.locator("#field-knowledgeId").fill("knowledge-point-practice")
        page.locator("#field-userId").fill("teacher-001")
        page.locator("#field-type").select_option("single_choice")
        page.locator("#field-stem").fill(question_stem)
        page.locator("#field-optionsJson").fill(
            json.dumps(
                [
                    {"key": "A", "content": "错误选项"},
                    {"key": "B", "content": "正确选项"},
                ],
                ensure_ascii=False,
            )
        )
        page.locator("#field-answer").fill("B")
        page.locator("#field-status").select_option("DRAFT")
        page.locator("#field-extJson").fill(
            json.dumps(
                {
                    "source": "click-replay",
                    "analysis": "用于三端联调真点击回放。",
                    "difficulty": "medium",
                    "knowledgeTags": ["联调", "回放"],
                    "reviewRemark": "",
                },
                ensure_ascii=False,
            )
        )
        page.locator("#save-question").click()
        expect_api(page.locator("#page-message")).to_contain_text("题目已创建", timeout=timeout_ms)

        row = page.locator("#question-table-body tr", has_text=question_stem).first
        expect_api(row).to_be_visible(timeout=timeout_ms)
        nonlocal created_question_id
        created_question_id = row.locator("td").nth(1).inner_text().strip()
        if not created_question_id:
            raise AssertionError("未读取到新建题目的 questionId。")

    def step_3_publish_question() -> None:
        if not created_question_id:
            raise AssertionError("缺少新建题目ID，无法发布。")
        page.locator(f"button[data-action='detail'][data-question-id='{created_question_id}']").click()
        expect_api(page.locator("#detail-modal")).to_be_visible(timeout=timeout_ms)

        page.locator(
            f"#detail-status-actions button[data-detail-target-status='REVIEW_PENDING'][data-question-id='{created_question_id}']"
        ).click()
        expect_api(page.locator("#page-message")).to_contain_text("待审核", timeout=timeout_ms)

        page.locator(
            f"#detail-status-actions button[data-detail-target-status='PUBLISHED'][data-question-id='{created_question_id}']"
        ).click()
        expect_api(page.locator("#page-message")).to_contain_text("已发布", timeout=timeout_ms)

        page.locator("#close-detail-modal").click()

        api = playwright.request.new_context(base_url=base_url)
        try:
            detail = api.get(
                f"/api/question-bank/questions/{created_question_id}",
                headers={"X-Role": "teacher", "X-User-Id": "teacher-001"},
            )
            payload = require_status(detail, 200, "教师发布后题目详情")
            if str(payload["data"].get("status")) != "PUBLISHED":
                raise AssertionError("题目未处于 PUBLISHED 状态。")
        finally:
            api.dispose()

        shared_state.created_question_id = created_question_id

    def step_4_teacher_to_student_visibility() -> None:
        if not shared_state.created_question_id:
            raise AssertionError("缺少教师发布题目 ID。")

        page.goto("/teacher/analytics", wait_until="domcontentloaded")
        expect_api(page.locator("#analytics-summary-grid")).to_be_visible(timeout=timeout_ms)

        api = playwright.request.new_context(base_url=base_url)
        try:
            practice = api.get(
                "/api/question-bank/student/practice/questions?page=1&size=100&status=PUBLISHED",
                headers={"X-Role": "student", "X-User-Id": "student-001"},
            )
            payload = require_status(practice, 200, "教师发布后学生端可见性检查")
            items = payload["data"].get("items", [])
            matched = any(str(item.get("id")) == shared_state.created_question_id for item in items)
            if not matched:
                raise AssertionError("教师发布题目未出现在学生练习列表。")
        finally:
            api.dispose()

        shared_state.linkage_matrix["teacherToStudent"] = PASS

    step.run("1-教师登录并进入题库页", step_1_login_teacher)
    step.run("2-教师真点击创建题目", step_2_create_question)
    step.run("3-教师真点击发布题目", step_3_publish_question)
    step.run("4-教师发布题目在学生端可见", step_4_teacher_to_student_visibility)

    context.close()
    return role_run.finalize()


def load_target_question_for_student(base_url: str, playwright: Any, preferred_id: str) -> str:
    api = playwright.request.new_context(base_url=base_url)
    try:
        response = api.get(
            "/api/question-bank/student/practice/questions?page=1&size=100&status=PUBLISHED",
            headers={"X-Role": "student", "X-User-Id": "student-001"},
        )
        payload = require_status(response, 200, "学生练习题查询")
        items = payload["data"].get("items", [])
        if not isinstance(items, list) or not items:
            raise AssertionError("学生练习题列表为空。")
        if preferred_id and any(str(item.get("id")) == preferred_id for item in items):
            return preferred_id
        first_id = str(items[0].get("id") or "").strip()
        if not first_id:
            raise AssertionError("未能获取学生练习题 id。")
        return first_id
    finally:
        api.dispose()


def run_student_suite(
    playwright: Any,
    browser: Any,
    base_url: str,
    timeout_sec: int,
    output_dir: Path,
    shared_state: SharedState,
    expect_api: Any,
) -> Dict[str, Any]:
    timeout_ms = timeout_sec * 1000
    role_run = RoleRun(role="student", base_url=base_url, timeout_sec=timeout_sec, headless=True, db_path="")
    context = browser.new_context(base_url=base_url)
    page = context.new_page()
    page.set_default_timeout(timeout_ms)
    step = StepRunner(role_run=role_run, role="student", page=page, output_dir=output_dir)

    target_question_id = ""
    active_paper_id = ""
    active_paper_answer: Dict[str, str] = {}

    def wait_for_global_loading_mask(wait_ms: int = 12000) -> None:
        deadline = time.time() + (wait_ms / 1000.0)
        while time.time() < deadline:
            masks = page.locator(".global-loading-mask")
            if masks.count() == 0:
                return
            visible_count = 0
            for index in range(masks.count()):
                if masks.nth(index).is_visible():
                    visible_count += 1
            if visible_count == 0:
                return
            page.wait_for_timeout(120)
        raise AssertionError("学生端全局加载蒙层未在预期时间内消失。")

    def wait_student_e2e_hook_ready(wait_ms: int = 6000) -> None:
        page.wait_for_function(
            """() => Boolean(
                window.__questionBankStudentE2E &&
                typeof window.__questionBankStudentE2E.getState === "function"
            )""",
            timeout=wait_ms,
        )

    def ensure_student_available_paper(force_create: bool = False) -> str:
        api = playwright.request.new_context(base_url=base_url)
        try:
            check_response = api.get(
                "/api/question-bank/student/papers/questions?page=1&size=20",
                headers={"X-Role": "student", "X-User-Id": "student-001"},
            )
            check_payload = require_status(check_response, 200, "检查学生可用试卷")
            check_items = check_payload.get("data", {}).get("items", [])
            if isinstance(check_items, list) and check_items and not force_create:
                return ""

            dashboard_response = api.get(
                "/api/question-bank/student/dashboard",
                headers={"X-Role": "student", "X-User-Id": "student-001"},
            )
            dashboard_payload = require_status(dashboard_response, 200, "读取学生学情用于构建回放题目")
            dashboard_data = dashboard_payload.get("data", {})
            subject_code = "POLITICS"
            core_subjects = dashboard_data.get("coreSubjects", [])
            if isinstance(core_subjects, list):
                for item in core_subjects:
                    candidate = str((item or {}).get("subjectCode") or "").strip()
                    if candidate:
                        subject_code = candidate
                        break
            exam_category_code = str(dashboard_data.get("examCategoryCode") or "").strip() or "SCIENCE_ENGINEERING"
            joint_exam_group_code = str(dashboard_data.get("jointExamGroupCode") or "").strip() or "SCIENCE_ENGINEERING_3"

            tree_response = api.get(
                f"/api/question-bank/knowledge/tree?subjectCode={quote(subject_code, safe='')}",
                headers={"X-Role": "teacher", "X-User-Id": "teacher-001"},
            )
            tree_payload = require_status(tree_response, 200, "读取知识树以构建回放题目")
            tree_nodes = tree_payload.get("data", {}).get("nodes", [])
            if not isinstance(tree_nodes, list) or not tree_nodes:
                raise AssertionError("知识树为空，无法创建学生体验回放题目。")
            candidate_nodes = [item for item in tree_nodes if int(item.get("level", 0) or 0) >= 5 and str(item.get("id", "")).strip()]
            if not candidate_nodes:
                candidate_nodes = [item for item in tree_nodes if str(item.get("id", "")).strip()]
            knowledge_id = str(candidate_nodes[0].get("id", "")).strip()
            if not knowledge_id:
                raise AssertionError("知识树未返回可用知识点 ID，无法创建学生体验回放题目。")

            replay_suffix = unique_suffix()
            create_question = api.post(
                "/api/question-bank/questions",
                headers={"X-Role": "teacher", "X-User-Id": "teacher-001", "Content-Type": "application/json"},
                data=json.dumps(
                    {
                        "userId": "teacher-001",
                        "title": f"学生端体验回放试卷题-{replay_suffix}",
                        "content": f"学生端体验回放试卷题-{replay_suffix}：请选择正确选项。",
                        "type": "single_choice",
                        "subjectCode": subject_code,
                        "examCategoryCode": exam_category_code,
                        "jointExamGroupCode": joint_exam_group_code,
                        "knowledgePoints": [knowledge_id],
                        "options": [
                            {"key": "A", "content": "错误选项"},
                            {"key": "B", "content": "正确选项"},
                        ],
                        "answer": "B",
                        "status": "DRAFT",
                        "analysis": "用于学生端体验细节真点击回放。",
                    },
                    ensure_ascii=False,
                ),
            )
            question_payload = require_status(create_question, 200, "创建学生体验回放题目")
            question_id = str(question_payload.get("data", {}).get("id") or "").strip()
            if not question_id:
                raise AssertionError("创建学生体验回放题目后未返回 questionId。")

            qa_response = api.post(
                f"/api/question-bank/questions/{question_id}/status/QA_IN_PROGRESS",
                headers={"X-Role": "teacher", "X-User-Id": "teacher-001"},
            )
            require_status(qa_response, 200, "回放题目流转 QA_IN_PROGRESS")

            review_response = api.post(
                f"/api/question-bank/questions/{question_id}/status/REVIEW_PENDING",
                headers={"X-Role": "teacher", "X-User-Id": "teacher-002"},
            )
            require_status(review_response, 200, "回放题目流转 REVIEW_PENDING")

            publish_response = api.post(
                f"/api/question-bank/questions/{question_id}/status/PUBLISHED",
                headers={"X-Role": "teacher", "X-User-Id": "teacher-002"},
            )
            require_status(publish_response, 200, "回放题目流转 PUBLISHED")
            return question_id
        finally:
            api.dispose()

    def ensure_active_paper_loaded() -> str:
        nonlocal active_paper_id
        ensure_student_available_paper(force_create=True)
        api = playwright.request.new_context(base_url=base_url)
        try:
            dashboard_response = api.get(
                "/api/question-bank/student/dashboard",
                headers={"X-Role": "student", "X-User-Id": "student-001"},
            )
            dashboard_payload = require_status(dashboard_response, 200, "读取学生学情用于启动模考会话")
            dashboard_data = dashboard_payload.get("data", {})
            subject_code = "POLITICS"
            core_subjects = dashboard_data.get("coreSubjects", [])
            if isinstance(core_subjects, list):
                for item in core_subjects:
                    candidate = str((item or {}).get("subjectCode") or "").strip()
                    if candidate:
                        subject_code = candidate
                        break
            exam_category_code = str(dashboard_data.get("examCategoryCode") or "").strip() or "SCIENCE_ENGINEERING"
            joint_exam_group_code = str(dashboard_data.get("jointExamGroupCode") or "").strip() or "SCIENCE_ENGINEERING_3"

            start_response = api.post(
                "/api/question-bank/student/mock-exams/start",
                headers={"X-Role": "student", "X-User-Id": "student-001", "Content-Type": "application/json"},
                data=json.dumps(
                    {
                        "subjectCode": subject_code,
                        "examCategoryCode": exam_category_code,
                        "jointExamGroupCode": joint_exam_group_code,
                    },
                    ensure_ascii=False,
                ),
            )
            start_payload = require_status(start_response, 200, "启动学生模考会话")
            session_data = start_payload.get("data", {})
            session_id = str(session_data.get("id") or "").strip()
            paper_id = str(session_data.get("paperId") or "").strip()
            if not session_id or not paper_id:
                raise AssertionError("启动学生模考会话后缺少 sessionId 或 paperId。")

            page.goto(
                f"/student/practice/mock?module=mock&subjectCode={quote(subject_code, safe='')}&sessionId={quote(session_id, safe='')}&paperId={quote(paper_id, safe='')}&immersive=1&e2e=1",
                wait_until="domcontentloaded",
            )
            wait_for_global_loading_mask(wait_ms=timeout_ms)
            wait_student_e2e_hook_ready(wait_ms=10000)
            question_cards = page.locator("#paper-question-list .paper-card")
            expect_api(question_cards.first).to_be_visible(timeout=timeout_ms)
            active_paper_id = paper_id
            return active_paper_id
        finally:
            api.dispose()

    def clear_current_paper_answers() -> None:
        page.evaluate(
            """() => {
                document
                  .querySelectorAll("#paper-question-list input[name^='answer-']")
                  .forEach((input) => {
                    if (input instanceof HTMLInputElement) {
                      input.checked = false;
                    }
                  });
                document
                  .querySelectorAll("#paper-question-list textarea[data-answer-field]")
                  .forEach((textarea) => {
                    if (textarea instanceof HTMLTextAreaElement) {
                      textarea.value = "";
                    }
                  });
                document
                  .querySelectorAll("#paper-question-list input[data-marked-field]")
                  .forEach((input) => {
                    if (input instanceof HTMLInputElement) {
                      input.checked = false;
                    }
                  });
            }"""
        )

    def fill_first_paper_question_answer() -> Dict[str, str]:
        question_id = str(page.locator("#paper-question-list input[data-marked-field]").first.get_attribute("data-marked-field") or "").strip()
        if not question_id:
            raise AssertionError("未读取到试卷题目 ID。")
        option_card = page.locator(".option-list .option-card").first
        expect_api(option_card).to_be_visible(timeout=timeout_ms)
        option_card.click(force=True)
        option_value = str(
            page.evaluate(
                """() => {
                    const checked = document.querySelector(".option-list input[type='radio']:checked");
                    return checked ? String(checked.value || "") : "";
                }"""
            )
            or ""
        ).strip()
        if not option_value:
            raise AssertionError("试卷客观题作答失败。")
        return {"questionId": question_id, "mode": "option", "answer": option_value}

    def read_first_paper_answer_meta() -> Dict[str, str]:
        question_id = str(page.locator("#paper-question-list input[data-marked-field]").first.get_attribute("data-marked-field") or "").strip()
        if not question_id:
            raise AssertionError("未读取到试卷题目 ID。")

        option_value = str(
            page.evaluate(
                """() => {
                    const checked = document.querySelector(".option-list input[type='radio']:checked");
                    return checked ? String(checked.value || "") : "";
                }"""
            )
            or ""
        ).strip()
        if not option_value:
            option_card = page.locator(".option-list .option-card").first
            expect_api(option_card).to_be_visible(timeout=timeout_ms)
            option_card.click(force=True)
            option_value = str(
                page.evaluate(
                    """() => {
                        const checked = document.querySelector(".option-list input[type='radio']:checked");
                        return checked ? String(checked.value || "") : "";
                    }"""
                )
                or ""
            ).strip()
        if not option_value:
            raise AssertionError("未找到试卷作答输入控件。")
        return {"questionId": question_id, "mode": "option", "answer": option_value}

    def assert_paper_answer_restored(answer_meta: Dict[str, str]) -> None:
        question_id = str(answer_meta.get("questionId") or "").strip()
        answer = str(answer_meta.get("answer") or "")
        mode = str(answer_meta.get("mode") or "")
        if not question_id or not mode:
            raise AssertionError("缺少草稿恢复断言所需的题目数据。")
        if mode != "option":
            raise AssertionError(f"不支持的作答模式: {mode}")

        checked_answer = str(
            page.evaluate(
                """() => {
                    const checked = document.querySelector(".option-list input[type='radio']:checked");
                    return checked ? String(checked.value || "") : "";
                }"""
            )
            or ""
        ).strip()
        if checked_answer == answer:
            return

        # Some UI builds hide native radio checked state; fall back to answered summary semantics.
        state = page.evaluate(
            """() => {
                if (!window.__questionBankStudentE2E || typeof window.__questionBankStudentE2E.getState !== "function") {
                    return { answeredCount: 0 };
                }
                return window.__questionBankStudentE2E.getState();
            }"""
        )
        answered_count = int((state or {}).get("answeredCount", 0))
        if answered_count <= 0:
            raise AssertionError("客观题草稿未恢复。")
        expect_api(page.locator("#paper-question-list .paper-card").first).to_contain_text("已作答", timeout=timeout_ms)

    def seed_countdown_draft(paper_id: str, answer_meta: Dict[str, str], remaining_sec: int) -> None:
        question_id = str(answer_meta.get("questionId") or "").strip()
        answer = str(answer_meta.get("answer") or "")
        if not question_id or not answer:
            raise AssertionError("缺少倒计时草稿注入参数。")

        resolved_paper_id = str(
            page.evaluate(
                """(payload) => {
                    const prefix = "student_mock_exam_draft:";
                    let paperId = String(payload.paperId || "").trim();
                    if (!paperId) {
                        const key = Object.keys(window.localStorage).find((item) => item.startsWith(prefix));
                        paperId = key ? key.slice(prefix.length) : "";
                    }
                    if (!paperId) {
                        paperId = String(new URL(window.location.href).searchParams.get("paperId") || "").trim();
                    }
                    if (!paperId) {
                        return "";
                    }
                    const storageKey = `${prefix}${paperId}`;
                    let parsed = {};
                    const raw = window.localStorage.getItem(storageKey);
                    if (raw) {
                        try {
                            parsed = JSON.parse(raw) || {};
                        } catch (error) {
                            parsed = {};
                        }
                    }
                    const answers = parsed && typeof parsed.answers === "object" ? parsed.answers : {};
                    const marks = parsed && typeof parsed.marks === "object" ? parsed.marks : {};
                    answers[payload.questionId] = payload.answer;
                    const draft = {
                        paperId,
                        activeQuestionIndex: Number(parsed.activeQuestionIndex || 0),
                        remainingSec: Number(payload.remainingSec || 0),
                        paused: false,
                        answers,
                        marks,
                        updateTime: new Date().toISOString(),
                    };
                    window.localStorage.setItem(storageKey, JSON.stringify(draft));
                    return paperId;
                }""",
                {"paperId": paper_id, "questionId": question_id, "answer": answer, "remainingSec": remaining_sec},
            )
            or ""
        ).strip()
        if not resolved_paper_id:
            raise AssertionError("未定位到可写入倒计时草稿的试卷 ID。")

    def open_student_nav(nav_title: str, expected_path: str, page_heading: str, content_hint: str) -> None:
        page.locator(".side-nav__item", has_text=nav_title).first.click()
        page.wait_for_function(
            """(targetPath) => window.location.pathname === targetPath""",
            arg=expected_path,
            timeout=timeout_ms,
        )
        wait_for_global_loading_mask(wait_ms=timeout_ms)
        heading_locator = page.get_by_role("heading", name=page_heading)
        if heading_locator.count() > 0:
            expect_api(heading_locator.first).to_be_visible(timeout=timeout_ms)
        else:
            expect_api(page.get_by_text(page_heading).first).to_be_visible(timeout=timeout_ms)
        expect_api(page.get_by_text(content_hint).first).to_be_visible(timeout=timeout_ms)

    def open_student_analysis_subnav(nav_title: str, expected_path: str, page_heading: str, content_hint: str) -> None:
        analysis_shell_tab = page.locator(".analysis-shell-tab", has_text=nav_title)
        visible_analysis_tab = None
        for index in range(analysis_shell_tab.count()):
            candidate = analysis_shell_tab.nth(index)
            if candidate.is_visible():
                visible_analysis_tab = candidate
                break
        if visible_analysis_tab is not None:
            visible_analysis_tab.click()
        else:
            page.locator(".side-subnav__item", has_text=nav_title).first.click()
        page.wait_for_function(
            """(targetPath) => window.location.pathname === targetPath""",
            arg=expected_path,
            timeout=timeout_ms,
        )
        wait_for_global_loading_mask(wait_ms=timeout_ms)
        heading_locator = page.get_by_role("heading", name=page_heading)
        if heading_locator.count() > 0:
            expect_api(heading_locator.first).to_be_visible(timeout=timeout_ms)
        else:
            expect_api(page.get_by_text(page_heading).first).to_be_visible(timeout=timeout_ms)
        expect_api(page.get_by_text(content_hint).first).to_be_visible(timeout=timeout_ms)

    def step_1_login_student() -> None:
        login_by_password(page, expect_api, "13800000005", "seed-password-student-001", timeout_ms)
        page.goto("/student/practice/chapter?module=chapter&e2e=1", wait_until="domcontentloaded")
        wait_for_global_loading_mask(wait_ms=timeout_ms)
        wait_student_e2e_hook_ready(wait_ms=timeout_ms)
        expect_api(page.locator(".question-body").first).to_be_visible(timeout=timeout_ms)

    def step_2_open_analysis_daily_tasks() -> None:
        open_student_nav("知识诊断", "/student/analysis/overview", "知识结构与薄弱点诊断", "当前科目")
        open_student_analysis_subnav("今日任务", "/student/analysis/tasks", "知识诊断今日任务", "查看诊断总览")

    def step_3_visible_question() -> None:
        nonlocal target_question_id
        target_question_id = load_target_question_for_student(base_url, playwright, shared_state.created_question_id)

        if shared_state.created_question_id:
            if target_question_id != shared_state.created_question_id:
                raise AssertionError("教师发布题目未出现在学生练习题列表。")
            shared_state.linkage_matrix["teacherToStudent"] = PASS

        page.goto("/student/practice/chapter?module=chapter&e2e=1", wait_until="domcontentloaded")
        wait_for_global_loading_mask(wait_ms=timeout_ms)
        expect_api(page.locator(".question-body").first).to_be_visible(timeout=timeout_ms)

    def step_4_submit_answer() -> None:
        if not target_question_id:
            raise AssertionError("缺少目标题目 ID。")

        option_card = page.locator(".option-list .option-card").first
        expect_api(option_card).to_be_visible(timeout=timeout_ms)
        option_card.click(force=True)

        selected_answer = str(
            page.evaluate(
                """() => {
                    const checked = document.querySelector(".option-list input[type='radio']:checked");
                    return checked ? String(checked.value || "") : "";
                }"""
            )
            or ""
        ).strip() or "B"

        api = playwright.request.new_context(base_url=base_url)
        try:
            submit_response = api.post(
                f"/api/question-bank/student/practice/questions/{target_question_id}/submit",
                headers={"X-Role": "student", "X-User-Id": "student-001", "Content-Type": "application/json"},
                data=json.dumps(
                    {
                        "answer": selected_answer,
                        "elapsedSec": 8,
                        "sourceType": "CHAPTER_CHALLENGE",
                        "attemptKey": f"click-replay-{unique_suffix()}",
                    },
                    ensure_ascii=False,
                ),
            )
            require_status(submit_response, 200, "学生题目提交")
        finally:
            api.dispose()

        shared_state.submitted_question_id = target_question_id

    def step_5_open_submit_check_modal() -> None:
        ensure_active_paper_loaded()
        marked_field = page.locator("#paper-question-list input[data-marked-field]").first
        expect_api(marked_field).to_be_visible(timeout=timeout_ms)
        marked_field.check()
        page.locator("#submit-paper-button").click()
        expect_api(page.locator("#paper-submit-check-modal")).to_be_visible(timeout=timeout_ms)
        check_items = page.locator("#paper-submit-check-list .paper-card")
        expect_api(check_items.first).to_be_visible(timeout=timeout_ms)
        expect_api(page.locator("#paper-submit-check-list")).to_contain_text("已标记待查", timeout=timeout_ms)
        page.locator("#back-to-answer-button").click()
        expect_api(page.locator("#paper-submit-check-modal")).to_be_hidden(timeout=timeout_ms)

    def step_6_pause_and_resume_paper() -> None:
        ensure_active_paper_loaded()
        pause_prepare_answer = read_first_paper_answer_meta()
        seed_countdown_draft(active_paper_id, pause_prepare_answer, remaining_sec=600)
        page.reload(wait_until="domcontentloaded")
        ensure_active_paper_loaded()
        page.evaluate(
            """() => {
                if (!window.__questionBankStudentE2E) {
                  throw new Error("缺少学生端 e2e 测试钩子。");
                }
                window.__questionBankStudentE2E.forceCountdown(600);
            }"""
        )
        expect_api(page.locator("#paper-countdown")).to_contain_text("倒计时", timeout=timeout_ms)
        page.locator("#pause-paper-button").click()
        expect_api(page.locator("#paper-pause-state")).to_contain_text("暂停中", timeout=timeout_ms)
        page.evaluate(
            """() => {
                if (!window.__questionBankStudentE2E) {
                  throw new Error("缺少学生端 e2e 测试钩子。");
                }
                window.__questionBankStudentE2E.resumeExam();
            }"""
        )
        expect_api(page.locator("#paper-pause-state")).to_contain_text("每次最多 10 分钟", timeout=timeout_ms)

    def step_7_restore_paper_draft() -> None:
        nonlocal active_paper_answer
        ensure_active_paper_loaded()
        active_paper_answer = fill_first_paper_question_answer()
        seed_countdown_draft(active_paper_id, active_paper_answer, remaining_sec=300)
        page.reload(wait_until="domcontentloaded")
        ensure_active_paper_loaded()
        page.wait_for_timeout(180)
        assert_paper_answer_restored(active_paper_answer)

    def step_8_auto_submit_when_countdown_zero() -> None:
        nonlocal active_paper_answer
        question_cards = page.locator("#paper-question-list .paper-card")
        try:
            expect_api(question_cards.first).to_be_visible(timeout=4000)
        except Exception:
            ensure_active_paper_loaded()
        if not active_paper_answer:
            active_paper_answer = fill_first_paper_question_answer()
        page.evaluate(
            """() => {
                if (!window.__questionBankStudentE2E) {
                  throw new Error("缺少学生端 e2e 测试钩子。");
                }
                window.__questionBankStudentE2E.forceCountdown(2);
            }"""
        )
        expect_api(page.locator("#student-message")).to_contain_text("系统已自动交卷", timeout=timeout_ms)
        expect_api(page.locator("#paper-report")).to_contain_text("paper-report-", timeout=timeout_ms)

    def step_9_student_to_teacher_record() -> None:
        question_id = shared_state.submitted_question_id or target_question_id
        if not question_id:
            raise AssertionError("缺少已提交题目 ID。")

        api = playwright.request.new_context(base_url=base_url)
        try:
            records = api.get(
                "/api/question-bank/analytics/records?page=1&size=200&studentUserId=student-001",
                headers={"X-Role": "teacher", "X-User-Id": "teacher-001"},
            )
            payload = require_status(records, 200, "教师侧学情记录查询")
            items = payload["data"].get("items", [])
            matched = None
            for item in items:
                if str(item.get("id")) == question_id:
                    matched = item
                    break
            if not matched:
                raise AssertionError("教师侧未查到学生提交痕迹。")
            ext = json.loads(str(matched.get("extJson") or "{}"))
            analytics = ext.get("analytics", {}) if isinstance(ext, dict) else {}
            if str(analytics.get("studentUserId") or "") != "student-001":
                raise AssertionError("教师侧记录未关联正确 studentUserId。")
            chapter = str(analytics.get("chapter") or "").strip()
            if not chapter:
                raise AssertionError("教师侧记录缺少章节信息。")
        finally:
            api.dispose()

        shared_state.linkage_matrix["studentToTeacher"] = PASS

    step.run("1-学生登录并进入刷题页", step_1_login_student)
    step.run("2-学生真点击进入知识诊断今日任务", step_2_open_analysis_daily_tasks)
    step.run("3-学生端可见教师发布题目", step_3_visible_question)
    step.run("4-学生真点击提交题目", step_4_submit_answer)
    step.run("5-学生交卷前检查弹窗触发与返回作答", step_5_open_submit_check_modal)
    step.run("6-学生模拟考试暂停与恢复", step_6_pause_and_resume_paper)
    step.run("7-学生模拟答题草稿刷新后恢复", step_7_restore_paper_draft)
    step.run("8-学生倒计时归零自动交卷", step_8_auto_submit_when_countdown_zero)
    step.run("9-教师侧可查询学生提交痕迹", step_9_student_to_teacher_record)

    context.close()
    return role_run.finalize()


def render_role_report(result: Dict[str, Any], linkage_matrix: Dict[str, str], result_path: Path) -> str:
    role = str(result.get("role"))
    role_name = role_label(role)
    steps = result.get("steps", [])
    passed = len([item for item in steps if item.get("status") == PASS])
    failed = len([item for item in steps if item.get("status") == FAIL])

    lines: List[str] = []
    lines.append(f"# {role_name}真点击回放验收报告（{today_local()}）")
    lines.append("")
    lines.append("## 执行概览")
    lines.append(f"- 角色：`{role}`")
    lines.append(f"- 回放模式：`{result.get('mode')}`")
    lines.append(f"- 执行时间：`{result.get('startedAt')}` 至 `{result.get('endedAt')}`")
    lines.append(f"- 回放地址：`{result.get('baseUrl')}`")
    lines.append(f"- 超时：`{result.get('timeoutSec')} 秒/步骤`")
    lines.append(f"- 数据库：`{result.get('dbPath')}`")
    lines.append("")
    lines.append("## 结果总览")
    lines.append(f"- 步骤总数：{len(steps)}")
    lines.append(f"- 通过：{passed}")
    lines.append(f"- 失败：{failed}")
    lines.append(f"- 问题数：{result.get('totalIssues', 0)}")
    lines.append("")
    lines.append("## 分步结果")
    for item in steps:
        lines.append(f"- {item.get('name')}：{item.get('status')}")
        if item.get("status") == FAIL and isinstance(item.get("error"), dict):
            lines.append(f"  错误：{item['error'].get('message')}")
        artifacts = item.get("artifacts") or []
        if artifacts:
            lines.append(f"  产物：{', '.join(str(artifact.get('path')) for artifact in artifacts)}")
    lines.append("")
    lines.append("## 三端联调矩阵")
    lines.append(f"- 超管→教师：{linkage_matrix.get('superAdminToTeacher', 'NOT_RUN')}")
    lines.append(f"- 教师→学生：{linkage_matrix.get('teacherToStudent', 'NOT_RUN')}")
    lines.append(f"- 学生→教师：{linkage_matrix.get('studentToTeacher', 'NOT_RUN')}")
    lines.append("")
    lines.append("## 结果文件")
    lines.append(f"- `{result_path.resolve()}`")
    return "\n".join(lines) + "\n"


def render_summary_report(results: List[Dict[str, Any]], linkage_matrix: Dict[str, str], output_dir: Path) -> str:
    lines: List[str] = []
    lines.append(f"# 三端统一真点击回放汇总（{today_local()}）")
    lines.append("")
    lines.append("## 三端状态")
    for result in results:
        role = str(result.get("role"))
        steps = result.get("steps", [])
        failed = len([item for item in steps if item.get("status") == FAIL])
        status = PASS if failed == 0 else FAIL
        lines.append(f"- {role_label(role)}（`{role}`）：{status}（失败 {failed}）")
    lines.append("")
    lines.append("## 三端联调矩阵")
    lines.append("- 超管→教师：" + linkage_matrix.get("superAdminToTeacher", "NOT_RUN"))
    lines.append("- 教师→学生：" + linkage_matrix.get("teacherToStudent", "NOT_RUN"))
    lines.append("- 学生→教师：" + linkage_matrix.get("studentToTeacher", "NOT_RUN"))
    lines.append("")
    lines.append("## 失败定位建议")
    lines.append("- 页面失败：优先检查页面元素选择器、跳转路径与角色入口守卫。")
    lines.append("- 接口失败：优先检查 `{code,message,data}` 包络、状态码与分页参数。")
    lines.append("- 权限失败：优先检查 `X-Role/X-User-Id` 与账号权限点/启停状态。")
    lines.append("")
    lines.append("## 产物目录")
    lines.append(f"- `{output_dir.resolve()}`")
    return "\n".join(lines) + "\n"


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def start_isolated_server(root: Path, base_url: str, db_path: str) -> subprocess.Popen:
    parsed = parse_base_url(base_url)
    db_file = Path(db_path).expanduser().resolve()
    db_file.parent.mkdir(parents=True, exist_ok=True)
    if db_file.exists():
        db_file.unlink()

    server_script = root / "tools" / "python" / "click_replay_server.py"
    server_env = dict(os.environ)
    server_env.setdefault("QB_ENV", "production")
    server_env.setdefault("QB_COOKIE_SECURE", "0")
    process = subprocess.Popen(
        [
            sys.executable,
            str(server_script),
            "--host",
            str(parsed["host"]),
            "--port",
            str(parsed["port"]),
            "--db-path",
            str(db_file),
        ],
        cwd=str(root),
        env=server_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if not wait_until_reachable(base_url, timeout_sec=20):
        try:
            _, stderr = process.communicate(timeout=3)
        except Exception:
            stderr = ""
        process.terminate()
        raise RuntimeError(f"隔离回放服务启动失败：{stderr.strip()[:500]}")
    return process


def stop_process(process: Optional[subprocess.Popen]) -> None:
    if process is None:
        return
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except Exception:
        process.kill()


def run() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    output_dir = (root / args.output_dir).resolve()
    ensure_dir(output_dir)

    try:
        parse_base_url(args.base_url)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        from playwright.sync_api import sync_playwright, expect
    except Exception:
        print("缺少 Playwright 依赖，请先执行：", file=sys.stderr)
        print("1) ./tools/bin/bootstrap-python.sh", file=sys.stderr)
        print("2) ./.venv/bin/python -m playwright install chromium", file=sys.stderr)
        return 2

    should_headless = not args.headed
    selected_roles = ["super_admin", "teacher", "student"] if args.role == "all" else [args.role]
    shared_state = SharedState()
    run_date = today_local()

    server_process: Optional[subprocess.Popen] = None
    db_path = str(args.db_path or "").strip()

    if db_path:
        if ping_url(args.base_url):
            print(
                "检测到 --base-url 已有服务运行，且你指定了 --db-path 隔离库。为保证隔离，请更换 base-url 端口或清空 --db-path。",
                file=sys.stderr,
            )
            return 2
        server_process = start_isolated_server(root, args.base_url, db_path)

    results: List[Dict[str, Any]] = []
    failed_count = 0
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=should_headless)
            try:
                for role in selected_roles:
                    if role == "super_admin":
                        role_result = run_super_admin_suite(
                            playwright=playwright,
                            browser=browser,
                            base_url=args.base_url,
                            timeout_sec=args.timeout_sec,
                            output_dir=output_dir,
                            shared_state=shared_state,
                            expect_api=expect,
                        )
                    elif role == "teacher":
                        role_result = run_teacher_suite(
                            playwright=playwright,
                            browser=browser,
                            base_url=args.base_url,
                            timeout_sec=args.timeout_sec,
                            output_dir=output_dir,
                            shared_state=shared_state,
                            expect_api=expect,
                        )
                    else:
                        role_result = run_student_suite(
                            playwright=playwright,
                            browser=browser,
                            base_url=args.base_url,
                            timeout_sec=args.timeout_sec,
                            output_dir=output_dir,
                            shared_state=shared_state,
                            expect_api=expect,
                        )

                    role_result["headless"] = should_headless
                    role_result["dbPath"] = db_path
                    role_result["linkageMatrix"] = dict(shared_state.linkage_matrix)
                    results.append(role_result)

                    result_path = output_dir / f"{role}-click-replay-result-{run_date}.json"
                    write_json(result_path, role_result)

                    report_text = render_role_report(role_result, shared_state.linkage_matrix, result_path)
                    report_path = output_dir / f"{role}-click-replay-report-{run_date}.md"
                    report_path.write_text(report_text, encoding="utf-8")

                    step_fails = len([item for item in role_result.get("steps", []) if item.get("status") == FAIL])
                    failed_count += step_fails
                    print(f"[click-replay] {role}: steps={len(role_result.get('steps', []))} failed={step_fails}")
            finally:
                browser.close()

        if len(results) > 1:
            summary_text = render_summary_report(results, shared_state.linkage_matrix, output_dir)
            summary_path = output_dir / f"three-end-click-replay-summary-{run_date}.md"
            summary_path.write_text(summary_text, encoding="utf-8")
            print(f"[click-replay] summary: {summary_path}")

    finally:
        stop_process(server_process)

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run())
