from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from playwright.sync_api import APIRequestContext, Playwright, sync_playwright


ROOT_DIR = Path(__file__).resolve().parents[2]


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_until_ready(base_url: str, timeout_sec: int = 20) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            with urlopen(f"{base_url}/login", timeout=1.5) as response:
                if int(getattr(response, "status", 0)) >= 200:
                    return
        except URLError:
            time.sleep(0.2)
            continue
    raise RuntimeError(f"测试服务启动超时: {base_url}")


def _expect_envelope(payload: dict) -> dict:
    assert set(payload.keys()) == {"code", "message", "data"}
    return payload


ROLE_LOGIN_CREDENTIALS: dict[tuple[str, str], tuple[str, str]] = {
    ("student", "student-001"): ("13800000005", "seed-password-student-001"),
    ("teacher", "teacher-001"): ("13800000002", "seed-password-teacher-001"),
    ("teacher", "teacher-002"): ("13800000003", "seed-password-teacher-002"),
    ("super_admin", "admin-001"): ("13800000001", "seed-password-admin-001"),
}


@pytest.fixture(scope="module")
def live_base_url(tmp_path_factory: pytest.TempPathFactory) -> str:
    db_path = tmp_path_factory.mktemp("playwright-e2e") / "question_bank.db"
    port = _pick_free_port()
    command = [
        sys.executable,
        str(ROOT_DIR / "tools/python/click_replay_server.py"),
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--db-path",
        str(db_path),
    ]
    process = subprocess.Popen(
        command,
        cwd=str(ROOT_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        _wait_until_ready(base_url)
        yield base_url
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)


def _new_request_context(base_url: str, role: str, user_id: str) -> tuple[Playwright, APIRequestContext]:
    playwright_driver = sync_playwright().start()
    login_context = playwright_driver.request.new_context(base_url=base_url)
    credentials = ROLE_LOGIN_CREDENTIALS.get((role, user_id))
    if credentials is None:
        login_context.dispose()
        playwright_driver.stop()
        raise RuntimeError(f"缺少测试账号凭据映射: role={role}, user_id={user_id}")
    login_response = login_context.post(
        "/api/question-bank/auth/login/password",
        data={"phone": credentials[0], "password": credentials[1]},
    )
    if login_response.status != 200:
        login_context.dispose()
        playwright_driver.stop()
        raise RuntimeError(f"登录失败，status={login_response.status}")
    token = str(_expect_envelope(login_response.json())["data"].get("accessToken", "")).strip()
    login_context.dispose()
    request_context = playwright_driver.request.new_context(
        base_url=base_url,
        extra_http_headers={"Authorization": f"Bearer {token}"},
    )
    return playwright_driver, request_context


def _close_request_context(playwright_driver: Playwright, request_context: APIRequestContext) -> None:
    request_context.dispose()
    playwright_driver.stop()


def test_playwright_exam_category_switch_refreshes_dashboard(live_base_url: str) -> None:
    playwright_driver, request_context = _new_request_context(live_base_url, "student", "student-001")
    try:
        dashboard_before_response = request_context.get("/api/question-bank/student/dashboard")
        assert dashboard_before_response.status == 200
        dashboard_before = _expect_envelope(dashboard_before_response.json())["data"]

        available_categories = dashboard_before.get("availableExamCategories", [])
        assert isinstance(available_categories, list) and available_categories
        current_exam_category_code = str(dashboard_before.get("examCategoryCode", ""))

        candidate = next(
            (
                item
                for item in available_categories
                if str(item.get("examCategoryCode", "")) != current_exam_category_code
                and isinstance(item.get("jointExamGroups"), list)
                and item.get("jointExamGroups")
            ),
            None,
        )
        if candidate is None:
            pytest.skip("当前种子数据未命中可切换的学科门类")

        next_exam_category_code = str(candidate.get("examCategoryCode", ""))
        next_joint_exam_group_code = str(candidate["jointExamGroups"][0].get("jointExamGroupCode", ""))
        assert next_exam_category_code and next_joint_exam_group_code

        profile_response = request_context.post(
            "/api/question-bank/student/profile",
            data={
                "examCategoryCode": next_exam_category_code,
                "jointExamGroupCode": next_joint_exam_group_code,
            },
        )
        assert profile_response.status == 200
        profile_data = _expect_envelope(profile_response.json())["data"]
        assert str(profile_data.get("examCategoryCode", "")) == next_exam_category_code
        assert str(profile_data.get("jointExamGroupCode", "")) == next_joint_exam_group_code

        dashboard_after_response = request_context.get("/api/question-bank/student/dashboard")
        assert dashboard_after_response.status == 200
        dashboard_after = _expect_envelope(dashboard_after_response.json())["data"]
        assert str(dashboard_after.get("examCategoryCode", "")) == next_exam_category_code
        assert str(dashboard_after.get("jointExamGroupCode", "")) == next_joint_exam_group_code
    finally:
        _close_request_context(playwright_driver, request_context)


def test_playwright_ai_task_queue_transitions_are_observable(live_base_url: str) -> None:
    playwright_driver, request_context = _new_request_context(live_base_url, "student", "student-001")
    try:
        create_task_response = request_context.post(
            "/api/question-bank/student/practice/questions/question-seed-005/ai-tutor",
            data={
                "prompt": "请给出本题解题思路与评分点。",
                "promptImageUrl": "",
            },
        )
        assert create_task_response.status == 200
        task_data = _expect_envelope(create_task_response.json())["data"]
        task_id = str(task_data.get("id", ""))
        assert task_id

        statuses = []
        for _ in range(5):
            poll_response = request_context.get(f"/api/question-bank/tasks/{task_id}")
            assert poll_response.status == 200
            latest = _expect_envelope(poll_response.json())["data"]
            statuses.append(str(latest.get("status", "")))
            if str(latest.get("status", "")) == "COMPLETED":
                break

        assert "RUNNING" in statuses
        assert statuses[-1] == "COMPLETED"
    finally:
        _close_request_context(playwright_driver, request_context)


def test_playwright_illegal_route_access_is_intercepted(live_base_url: str) -> None:
    playwright_driver, request_context = _new_request_context(live_base_url, "student", "student-001")
    try:
        forbidden_page_response = request_context.get("/teacher/questions", max_redirects=0)
        assert forbidden_page_response.status in {301, 302, 303, 307, 308}
        redirect_location = forbidden_page_response.headers.get("location", "")
        assert "/student/home" in redirect_location

        redirected_response = request_context.get("/teacher/questions")
        assert redirected_response.status == 200
        redirected_payload = redirected_response.json()
        assert redirected_payload.get("route") == "/student/home"
        assert redirected_payload.get("actor") == {"role": "student", "userId": "student-001"}
    finally:
        _close_request_context(playwright_driver, request_context)
