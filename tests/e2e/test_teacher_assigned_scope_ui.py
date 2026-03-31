from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest

playwright_sync_api = pytest.importorskip("playwright.sync_api")
APIRequestContext = playwright_sync_api.APIRequestContext
Page = playwright_sync_api.Page
Playwright = playwright_sync_api.Playwright
expect = playwright_sync_api.expect
sync_playwright = playwright_sync_api.sync_playwright


ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT_DIR / "frontend"
GLOBAL_SUPER_ADMIN_PHONE = "15373326608"
DEFAULT_E2E_GLOBAL_SUPER_ADMIN_PASSWORD = "E2E-Global-Super-Admin-001"


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_until_ready(url: str, timeout_sec: int = 45) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=1.5) as response:
                if int(getattr(response, "status", 0)) >= 200:
                    return
        except URLError:
            time.sleep(0.2)
            continue
    raise RuntimeError(f"服务启动超时: {url}")


def _wait_for_loading_mask(page: Page, timeout_ms: int = 15000) -> None:
    deadline = time.time() + (timeout_ms / 1000.0)
    while time.time() < deadline:
        visible_count = 0
        for selector in (".global-loading-mask", ".qb-loading-mask", ".el-loading-mask"):
            masks = page.locator(selector)
            for index in range(masks.count()):
                if masks.nth(index).is_visible():
                    visible_count += 1
        if visible_count == 0:
            return
        page.wait_for_timeout(120)
    raise AssertionError("加载蒙层未在预期时间内消失。")


def _new_request_context(playwright_driver: Playwright, base_url: str, extra_headers: dict[str, str] | None = None) -> APIRequestContext:
    return playwright_driver.request.new_context(
        base_url=base_url,
        extra_http_headers=extra_headers or {},
    )


def _global_super_admin_password() -> str:
    return str(os.environ.get("QUESTION_BANK_SUPER_ADMIN_PASSWORD", DEFAULT_E2E_GLOBAL_SUPER_ADMIN_PASSWORD)).strip()


def _login_admin_and_bind_teacher_scope(playwright_driver: Playwright, backend_base_url: str) -> None:
    admin_request = _new_request_context(playwright_driver, backend_base_url)
    try:
        login_response = admin_request.post(
            "/api/question-bank/auth/login/password",
            data={
                "phone": GLOBAL_SUPER_ADMIN_PHONE,
                "password": _global_super_admin_password(),
            },
        )
        assert login_response.status == 200
        login_payload = login_response.json()
        token = str((login_payload.get("data") or {}).get("accessToken", "")).strip()
        assert token

        authed_request = _new_request_context(
            playwright_driver,
            backend_base_url,
            {"Authorization": f"Bearer {token}"},
        )
        try:
            users_response = authed_request.get("/api/question-bank/admin/users?page=1&size=200")
            assert users_response.status == 200
            users_payload = users_response.json()
            users_data = users_payload.get("data") or {}
            user_items = users_data.get("items") or []
            assert isinstance(user_items, list)

            teacher_row = next(
                (
                    item
                    for item in user_items
                    if str(item.get("userId", "")).strip() == "teacher-002"
                ),
                None,
            )
            assert teacher_row is not None
            save_response = authed_request.post(
                "/api/question-bank/admin/users",
                data={
                    "userId": "teacher-002",
                    "role": str(teacher_row.get("role", "teacher")),
                    "name": str(teacher_row.get("name", "教师B")),
                    "mobile": str(teacher_row.get("mobile", "13800000003")),
                    "enabled": bool(teacher_row.get("enabled", True)),
                    "permissions": teacher_row.get("permissions", []),
                    "examCategoryCode": "SCIENCE_ENGINEERING",
                    "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
                    "vocationalMajor": str(teacher_row.get("vocationalMajor", "")),
                    "prepStage": str(teacher_row.get("prepStage", "")),
                },
            )
            assert save_response.status == 200
        finally:
            authed_request.dispose()
    finally:
        admin_request.dispose()


def _login_teacher(page: Page, frontend_base_url: str) -> None:
    page.goto(f"{frontend_base_url}/login?redirect=%2Fteacher%2Fpapers", wait_until="domcontentloaded")
    _wait_for_loading_mask(page)

    phone_input = page.get_by_placeholder("请输入 11 位手机号")
    password_input = page.get_by_placeholder("请输入密码")
    login_button = page.get_by_role("button", name="登录并继续")

    expect(phone_input).to_be_visible(timeout=30000)
    expect(password_input).to_be_visible(timeout=30000)
    expect(login_button).to_be_enabled(timeout=30000)

    phone_input.click()
    phone_input.fill("13800000003")
    password_input.click()
    password_input.fill("seed-password-teacher-002")
    login_button.click()

    page.wait_for_url("**/teacher/papers**", timeout=45000)
    page.wait_for_load_state("networkidle")
    _wait_for_loading_mask(page)
    expect(page.get_by_role("button", name="手动组卷")).to_be_visible(timeout=20000)


def _assert_option_hidden_or_disabled(page: Page, panel_selector: str, option_label: str) -> None:
    option_label_locator = page.locator(f"{panel_selector} .el-cascader-node__label:visible", has_text=option_label)
    option_count = option_label_locator.count()
    if option_count == 0:
        return
    option_node = option_label_locator.first.locator("xpath=ancestor::li[1]")
    option_class = str(option_node.get_attribute("class") or "")
    assert re.search(r"\bis-disabled\b", option_class), f"跨组选项 {option_label} 不应可选。"


def _assert_manual_scope_is_locked(page: Page) -> None:
    page.get_by_role("button", name="手动组卷").click()
    _wait_for_loading_mask(page)
    expect(page.get_by_text("手动组卷表单")).to_be_visible()

    page.locator(".manual-dialog .el-cascader .el-input__wrapper").first.click()
    _wait_for_loading_mask(page)
    expect(page.locator(".manual-dialog .el-cascader__dropdown .el-cascader-node__label:visible", has_text="理工类")).to_have_count(1)
    _assert_option_hidden_or_disabled(page, ".manual-dialog .el-cascader__dropdown", "文学类")
    expect(page.locator(".manual-dialog .el-cascader__dropdown .el-cascader-node__label:visible", has_text="信息技术概论")).to_have_count(1)
    _assert_option_hidden_or_disabled(page, ".manual-dialog .el-cascader__dropdown", "理工 1")
    _assert_option_hidden_or_disabled(page, ".manual-dialog .el-cascader__dropdown", "理工 2")
    _assert_option_hidden_or_disabled(page, ".manual-dialog .el-cascader__dropdown", "大学语文")
    page.locator(".manual-dialog").get_by_role("button", name="取消").click()
    _wait_for_loading_mask(page)
    expect(page.locator(".manual-dialog")).not_to_be_visible()


def _assert_ai_scope_is_locked(page: Page) -> None:
    page.get_by_role("button", name="AI 智能组卷").click()
    _wait_for_loading_mask(page)
    expect(page.get_by_text("AI 智能组卷参数配置")).to_be_visible()
    expect(page.locator(".ai-form .el-cascader").first).to_be_visible()

    page.locator(".ai-form .el-cascader .el-input__wrapper").first.click()
    _wait_for_loading_mask(page)
    expect(
        page.locator(".ai-form .el-cascader__dropdown .el-cascader-node__label:visible", has_text="理工类"),
    ).to_have_count(1, timeout=15000)
    _assert_option_hidden_or_disabled(page, ".ai-form .el-cascader__dropdown", "文学类")
    expect(
        page.locator(".ai-form .el-cascader__dropdown .el-cascader-node__label:visible", has_text="信息技术概论"),
    ).to_have_count(1, timeout=15000)
    _assert_option_hidden_or_disabled(page, ".ai-form .el-cascader__dropdown", "理工 2")


@pytest.mark.e2e
def test_ui_assigned_teacher_scope_hides_cross_group_options(tmp_path_factory: pytest.TempPathFactory) -> None:
    if shutil.which("npm") is None:
        pytest.skip("未检测到 npm，跳过前端 UI 自动化用例。")

    db_path = tmp_path_factory.mktemp("teacher-scope-ui") / "question_bank.db"
    backend_port = _pick_free_port()
    frontend_port = _pick_free_port()
    backend_base_url = f"http://127.0.0.1:{backend_port}"
    frontend_base_url = f"http://127.0.0.1:{frontend_port}"

    backend_command = [
        sys.executable,
        str(ROOT_DIR / "tools/python/click_replay_server.py"),
        "--host",
        "127.0.0.1",
        "--port",
        str(backend_port),
        "--db-path",
        str(db_path),
    ]
    backend_env = os.environ.copy()
    backend_env["QB_CORS_ORIGINS"] = frontend_base_url
    backend_env.setdefault("QUESTION_BANK_SUPER_ADMIN_PASSWORD", _global_super_admin_password())
    backend_process = subprocess.Popen(
        backend_command,
        cwd=str(ROOT_DIR),
        env=backend_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    frontend_env = os.environ.copy()
    frontend_env["VITE_API_BASE_URL"] = backend_base_url
    frontend_command = [
        "npm",
        "run",
        "dev",
        "--",
        "--host",
        "127.0.0.1",
        "--port",
        str(frontend_port),
    ]
    frontend_process = subprocess.Popen(
        frontend_command,
        cwd=str(FRONTEND_DIR),
        env=frontend_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_until_ready(f"{backend_base_url}/login")
        _wait_until_ready(f"{frontend_base_url}/login")
        with sync_playwright() as playwright_driver:
            _login_admin_and_bind_teacher_scope(playwright_driver, backend_base_url)
            browser = playwright_driver.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1680, "height": 1000})
                _login_teacher(page, frontend_base_url)
                _assert_manual_scope_is_locked(page)
                _assert_ai_scope_is_locked(page)
            finally:
                browser.close()
    finally:
        if frontend_process.poll() is None:
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                frontend_process.kill()
                frontend_process.wait(timeout=3)
        if backend_process.poll() is None:
            backend_process.terminate()
            try:
                backend_process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                backend_process.kill()
                backend_process.wait(timeout=3)
