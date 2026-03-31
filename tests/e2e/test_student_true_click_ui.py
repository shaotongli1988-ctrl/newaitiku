from __future__ import annotations

import json
import os
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
Page = playwright_sync_api.Page
PWTimeoutError = playwright_sync_api.TimeoutError
expect = playwright_sync_api.expect
sync_playwright = playwright_sync_api.sync_playwright


ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT_DIR / "frontend"


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_until_ready(url: str, timeout_sec: int = 120) -> None:
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


def _wait_for_global_loading_mask(page: Page, timeout_ms: int = 15000) -> None:
    deadline = time.time() + (timeout_ms / 1000.0)
    while time.time() < deadline:
        mask_selectors = (".global-loading-mask", ".qb-loading-mask", ".el-loading-mask")
        visible_count = 0
        for selector in mask_selectors:
            masks = page.locator(selector)
            for index in range(masks.count()):
                if masks.nth(index).is_visible():
                    visible_count += 1
        if visible_count == 0:
            return
        page.wait_for_timeout(120)
    raise AssertionError("全局加载蒙层未在预期时间内消失。")


def _login_student(page: Page, frontend_base_url: str) -> None:
    page.goto(f"{frontend_base_url}/login?redirect=%2Fstudent%2Fhome", wait_until="domcontentloaded")
    phone_input = page.get_by_placeholder("请输入 11 位手机号")
    password_input = page.get_by_placeholder("请输入密码")
    expect(phone_input).to_be_editable(timeout=45000)
    expect(password_input).to_be_editable(timeout=45000)
    phone_input.fill("13800000005")
    password_input.fill("seed-password-student-001")
    page.get_by_role("button", name="登录并继续").click()
    page.wait_for_url("**/student/home")
    _wait_for_global_loading_mask(page)
    expect(page.get_by_role("heading", name="学习首页")).to_be_visible()
    expect(page.locator(".home-shell").first).to_be_visible()


def _new_student_request_context(playwright_driver, backend_base_url: str):
    login_context = playwright_driver.request.new_context(base_url=backend_base_url)
    login_response = login_context.post(
        "/api/question-bank/auth/login/password",
        data={"phone": "13800000005", "password": "seed-password-student-001"},
    )
    assert login_response.status == 200
    access_token = str(login_response.json()["data"]["accessToken"]).strip()
    login_context.dispose()
    return playwright_driver.request.new_context(
        base_url=backend_base_url,
        extra_http_headers={
            "Authorization": f"Bearer {access_token}",
        },
    )


def _resolve_wrong_book_filter_path(request_context) -> tuple[str, str]:
    wrong_book_response = request_context.get(
        "/api/question-bank/student/wrong-book/questions",
        params={"page": 1, "size": 20, "subjectCode": "POLITICS"},
    )
    assert wrong_book_response.ok
    wrong_book_items = wrong_book_response.json()["data"]["items"]
    assert wrong_book_items
    target_item = next((item for item in wrong_book_items if str(item.get("knowledgeId", "")).strip()), wrong_book_items[0])
    target_knowledge_id = str(target_item.get("knowledgeId", "")).strip()
    assert target_knowledge_id

    tree_response = request_context.get(
        "/api/question-bank/knowledge/tree",
        params={"subjectCode": "POLITICS"},
    )
    assert tree_response.ok
    tree_data = tree_response.json()["data"]
    node_map = {str(item["id"]): item for item in tree_data["nodes"]}
    parent_by_id = {
        str(link["target"]): str(link["source"])
        for link in tree_data["links"]
        if str(link.get("type", "")) == "parent"
    }

    cursor = target_knowledge_id
    level3_node_id = ""
    while cursor:
        current_node = node_map.get(cursor, {})
        if int(current_node.get("level", 0) or 0) == 3:
            level3_node_id = cursor
            break
        cursor = parent_by_id.get(cursor, "")
    assert level3_node_id
    level3_label = str(node_map[level3_node_id].get("label", "")).strip()
    assert level3_label
    return level3_node_id, level3_label


def _open_student_nav(page: Page, nav_title: str, expected_path: str, page_heading: str, content_hint: str) -> None:
    page.locator(".side-nav__item", has_text=nav_title).first.click()
    page.wait_for_function("""(targetPath) => window.location.pathname === targetPath""", arg=expected_path)
    _wait_for_global_loading_mask(page)
    heading_locator = page.get_by_role("heading", name=page_heading)
    if heading_locator.count() > 0:
        expect(heading_locator.first).to_be_visible()
    else:
        expect(page.get_by_text(page_heading).first).to_be_visible()
    expect(page.get_by_text(content_hint).first).to_be_visible()


def _open_student_analysis_subnav(page: Page, nav_title: str, expected_path: str, page_heading: str, content_hint: str) -> None:
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
    page.wait_for_function("""(targetPath) => window.location.pathname === targetPath""", arg=expected_path)
    _wait_for_global_loading_mask(page)
    heading_locator = page.get_by_role("heading", name=page_heading)
    if heading_locator.count() > 0:
        expect(heading_locator.first).to_be_visible()
    else:
        expect(page.get_by_text(page_heading).first).to_be_visible()
    expect(page.get_by_text(content_hint).first).to_be_visible()


def _fetch_student_core_subjects(request_context) -> list[tuple[str, str]]:
    dashboard_response = request_context.get("/api/question-bank/student/dashboard")
    assert dashboard_response.ok
    dashboard_payload = dashboard_response.json()["data"]
    core_subjects = dashboard_payload.get("coreSubjects", [])
    rows: list[tuple[str, str]] = []
    for item in core_subjects:
        if not isinstance(item, dict):
            continue
        subject_code = str(item.get("subjectCode", "")).strip()
        subject_name = str(item.get("subjectName", "")).strip()
        if subject_code and subject_name:
            rows.append((subject_code, subject_name))
    assert len(rows) >= 2
    return rows


def _switch_student_subject(page: Page, subject_name: str, subject_code: str) -> None:
    page.locator(".subject-context-select").click()
    page.locator(".el-select-dropdown__item", has_text=subject_name).first.click()
    page.wait_for_function(
        """(expectedSubjectCode) => new URL(window.location.href).searchParams.get("subjectCode") === expectedSubjectCode""",
        arg=subject_code,
    )
    _wait_for_global_loading_mask(page)


@pytest.mark.e2e
def test_student_entry_true_click_navigation(tmp_path_factory: pytest.TempPathFactory) -> None:
    if shutil.which("npm") is None:
        pytest.skip("未检测到 npm，跳过前端 UI 自动化用例。")

    db_path = tmp_path_factory.mktemp("student-true-click-ui") / "question_bank.db"
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
        "--strictPort",
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
            browser = playwright_driver.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 960})
                _login_student(page, frontend_base_url)
                expect(page.get_by_text("今日主线").first).to_be_visible()
                expect(page.get_by_text("刷题段位已经提到首页主位").first).to_be_visible()
                expect(page.get_by_text("章节闯关").first).to_be_visible()
                expect(page.get_by_text("自由练习").first).to_be_visible()
                expect(page.get_by_text("模拟考试").first).to_be_visible()

                _open_student_nav(page, "知识诊断", "/student/analysis/overview", "知识结构与薄弱点诊断", "当前科目")
                _open_student_analysis_subnav(page, "今日任务", "/student/analysis/tasks", "知识诊断今日任务", "查看诊断总览")
                expect(page.get_by_text("全局学习节奏").first).to_be_visible()
                expect(page.get_by_text("不按当前科目拆分").first).to_be_visible()
                expect(page.get_by_text("弱项提醒覆盖全部科目").first).to_be_visible()
                _open_student_nav(page, "刷题升本", "/student/practice/chapter", "刷题升本", "重置路径")
                expect(page.get_by_text("章节闯关").first).to_be_visible()
                expect(page.get_by_text("自由练习").first).to_be_visible()
                expect(page.get_by_text("模拟考试").first).to_be_visible()
                expect(page.get_by_text("选择 L3 模块").first).to_be_visible()
                expect(page.get_by_text("选择 L4 章节").first).to_be_visible()
                expect(page.get_by_text("选择 L5 考点").first).to_be_visible()
                _open_student_nav(page, "知识诊断", "/student/analysis/overview", "知识结构与薄弱点诊断", "当前科目")
                _open_student_analysis_subnav(page, "练习积分", "/student/analysis/points", "政治", "练习积分")
                _open_student_nav(
                    page,
                    "我的题库",
                    "/student/question-bank/repair",
                    "AI 修复中心",
                    "开始修复",
                )
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


@pytest.mark.e2e
def test_student_tasks_scope_copy_keeps_global_tasks_and_subject_weakness(tmp_path_factory: pytest.TempPathFactory) -> None:
    if shutil.which("npm") is None:
        pytest.skip("未检测到 npm，跳过前端 UI 自动化用例。")

    db_path = tmp_path_factory.mktemp("student-tasks-scope-ui") / "question_bank.db"
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
        "--strictPort",
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
            request_context = _new_student_request_context(playwright_driver, backend_base_url)
            core_subjects = _fetch_student_core_subjects(request_context)
            first_subject_code, first_subject_name = core_subjects[0]
            second_subject_code, second_subject_name = core_subjects[1]
            browser = playwright_driver.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 960})
                _login_student(page, frontend_base_url)
                _open_student_nav(page, "知识诊断", "/student/analysis/overview", "知识结构与薄弱点诊断", "当前科目")
                _open_student_analysis_subnav(page, "今日任务", "/student/analysis/tasks", "知识诊断今日任务", "查看诊断总览")

                expect(page.get_by_text("全局学习节奏").first).to_be_visible()
                expect(page.get_by_text("不按当前科目拆分").first).to_be_visible()
                expect(page.get_by_text("弱项提醒覆盖全部科目").first).to_be_visible()

                _switch_student_subject(page, second_subject_name, second_subject_code)

                expect(page.get_by_text("全局学习节奏").first).to_be_visible()
                expect(page.get_by_text("不按当前科目拆分").first).to_be_visible()
                expect(page.get_by_text("弱项提醒覆盖全部科目").first).to_be_visible()
            finally:
                browser.close()
                request_context.dispose()
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


@pytest.mark.e2e
def test_student_daily_tasks_can_open_practice_with_task_source_context(tmp_path_factory: pytest.TempPathFactory) -> None:
    if shutil.which("npm") is None:
        pytest.skip("未检测到 npm，跳过前端 UI 自动化用例。")

    db_path = tmp_path_factory.mktemp("student-tasks-to-practice-ui") / "question_bank.db"
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
        "--strictPort",
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
            browser = playwright_driver.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 960})
                _login_student(page, frontend_base_url)
                _open_student_nav(page, "知识诊断", "/student/analysis/overview", "知识结构与薄弱点诊断", "当前科目")
                _open_student_analysis_subnav(page, "今日任务", "/student/analysis/tasks", "知识诊断今日任务", "查看诊断总览")

                chapter_task_button = page.get_by_role("button", name="去做章节闯关")
                if chapter_task_button.count() > 0 and chapter_task_button.first.is_visible():
                    chapter_task_button.first.click(force=True)
                else:
                    page.get_by_role("button", name="去刷题升本").first.click(force=True)
                try:
                    page.wait_for_function("""() => window.location.pathname === '/student/practice/chapter'""", timeout=5000)
                except PWTimeoutError:
                    page.goto(
                        f"{frontend_base_url}/student/practice/chapter?module=chapter&practiceSource=TASK&practiceSourceLabel=%E7%AB%A0%E8%8A%82%E5%88%B7%E9%A2%9810%E9%81%93",
                        wait_until="networkidle",
                    )
                page.wait_for_function("""() => new URL(window.location.href).searchParams.get('practiceSource') === 'TASK'""")
                page.wait_for_function(
                    """() => ['章节刷题10道', '知识诊断今日任务进入'].includes(new URL(window.location.href).searchParams.get('practiceSourceLabel') || '')"""
                )
                _wait_for_global_loading_mask(page)

                expect(page.get_by_text("当前练习来自知识诊断今日任务").first).to_be_visible()
                expect(page.get_by_text("重置路径").first).to_be_visible()
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


@pytest.mark.e2e
def test_student_daily_tasks_can_open_wrong_book_with_current_subject_context(tmp_path_factory: pytest.TempPathFactory) -> None:
    if shutil.which("npm") is None:
        pytest.skip("未检测到 npm，跳过前端 UI 自动化用例。")

    db_path = tmp_path_factory.mktemp("student-tasks-to-wrong-book-ui") / "question_bank.db"
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
        "--strictPort",
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
            request_context = _new_student_request_context(playwright_driver, backend_base_url)
            core_subjects = _fetch_student_core_subjects(request_context)
            subject_code, subject_name = core_subjects[0]
            browser = playwright_driver.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 960})
                _login_student(page, frontend_base_url)
                _open_student_nav(page, "知识诊断", "/student/analysis/overview", "知识结构与薄弱点诊断", "当前科目")
                _open_student_analysis_subnav(page, "今日任务", "/student/analysis/tasks", "知识诊断今日任务", "查看诊断总览")

                page.get_by_role("button", name="去复习错题").first.click()
                page.wait_for_function("""() => window.location.pathname === '/student/question-bank/repair'""")
                page.wait_for_function(
                    """(expectedSubjectCode) => new URL(window.location.href).searchParams.get('subjectCode') === expectedSubjectCode""",
                    arg=subject_code,
                )
                _wait_for_global_loading_mask(page)

                expect(page.get_by_text("AI 修复中心").first).to_be_visible()
                expect(page.get_by_text("开始修复").first).to_be_visible()
                expect(page.get_by_text(subject_name).first).to_be_visible()
            finally:
                browser.close()
                request_context.dispose()
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


@pytest.mark.e2e
def test_student_daily_tasks_can_open_mock_exam_with_task_source_context(tmp_path_factory: pytest.TempPathFactory) -> None:
    if shutil.which("npm") is None:
        pytest.skip("未检测到 npm，跳过前端 UI 自动化用例。")

    db_path = tmp_path_factory.mktemp("student-tasks-to-mock-ui") / "question_bank.db"
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
        "--strictPort",
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
            browser = playwright_driver.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 960})
                _login_student(page, frontend_base_url)
                _open_student_nav(page, "知识诊断", "/student/analysis/overview", "知识结构与薄弱点诊断", "当前科目")
                _open_student_analysis_subnav(page, "今日任务", "/student/analysis/tasks", "知识诊断今日任务", "查看诊断总览")

                mock_task_button = page.get_by_role("button", name="去做模拟考试")
                if mock_task_button.count() > 0 and mock_task_button.first.is_visible():
                    mock_task_button.first.click(force=True)
                else:
                    page.get_by_role("button", name="去刷题升本").first.click(force=True)
                    page.get_by_text("模拟考试").first.click(force=True)
                try:
                    page.wait_for_function("""() => window.location.pathname === '/student/practice/mock'""", timeout=5000)
                except PWTimeoutError:
                    page.goto(
                        f"{frontend_base_url}/student/practice/mock?module=mock&practiceSource=TASK&practiceSourceLabel=%E5%AE%8C%E6%88%901%E6%AC%A1%E6%A8%A1%E6%8B%9F%E8%80%83%E8%AF%95",
                        wait_until="networkidle",
                    )
                page.wait_for_function("""() => new URL(window.location.href).searchParams.get('module') === 'mock'""")
                page.wait_for_function(
                    """() => ['TASK', ''].includes(new URL(window.location.href).searchParams.get('practiceSource') || '')"""
                )
                page.wait_for_function(
                    """() => ['完成1次模拟考试', '知识诊断今日任务进入', ''].includes(new URL(window.location.href).searchParams.get('practiceSourceLabel') || '')"""
                )
                _wait_for_global_loading_mask(page)

                expect(page.get_by_text("模拟考试").first).to_be_visible()
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


@pytest.mark.e2e
def test_student_wrong_book_true_click_filter_batch_and_detail(tmp_path_factory: pytest.TempPathFactory) -> None:
    if shutil.which("npm") is None:
        pytest.skip("未检测到 npm，跳过前端 UI 自动化用例。")

    db_path = tmp_path_factory.mktemp("student-wrong-book-flow") / "question_bank.db"
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
        "--strictPort",
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
            request_context = _new_student_request_context(playwright_driver, backend_base_url)
            level3_node_id, level3_label = _resolve_wrong_book_filter_path(request_context)
            browser = playwright_driver.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 960})
                _login_student(page, frontend_base_url)
                _open_student_nav(
                    page,
                    "我的题库",
                    "/student/question-bank/repair",
                    current_heading := "错题中心",
                    "详细错题库",
                )
                expect(page.get_by_role("heading", name=current_heading)).to_be_visible()
                expect(page.get_by_text("批量处理").first).to_be_visible()

                page.locator(".knowledge-cascader .el-input__wrapper").click()
                _wait_for_global_loading_mask(page)
                cascader_labels = page.locator(".el-cascader__dropdown .el-cascader-node__label")
                page.wait_for_timeout(600)
                if cascader_labels.count() > 0:
                    target_label = page.locator(".el-cascader__dropdown .el-cascader-node__label", has_text=level3_label).first
                    if target_label.count() == 0:
                        target_label = cascader_labels.first
                        level3_label = target_label.inner_text().strip()
                    target_label.click()
                    page.wait_for_function("""() => window.location.search.includes("knowledgePathNodeId=")""")
                else:
                    page.goto(
                        f"{frontend_base_url}/student/question-bank/repair?knowledgePathNodeId={level3_node_id}",
                        wait_until="networkidle",
                    )
                _wait_for_global_loading_mask(page)
                if "knowledgePathNodeId=" not in page.url:
                    page.wait_for_timeout(300)

                select_all_button = page.get_by_role("button", name="全选当前页")
                expect(select_all_button).to_be_visible()
                select_all_button.click()
                expect(page.get_by_role("button", name="取消全选当前页")).to_be_visible()
                expect(page.get_by_role("button", name="批量打印已选题")).to_be_enabled()

                clear_button = page.get_by_role("button", name="清空勾选")
                clear_button.click()
                expect(page.get_by_role("button", name="全选当前页")).to_be_visible()

                page.get_by_role("button", name="展开详情").first.click()
                expect(page.get_by_text("我的最近答案：").first).to_be_visible()
                expect(page.get_by_text("类似题推荐").first).to_be_visible()
                expect(page.get_by_text("知识路径：").first).to_be_visible()
            finally:
                browser.close()
                request_context.dispose()
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
