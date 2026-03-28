from __future__ import annotations

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
expect = playwright_sync_api.expect
sync_playwright = playwright_sync_api.sync_playwright


ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT_DIR / "frontend"


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


def _login_from_student_entry(page: Page, frontend_base_url: str) -> None:
    page.goto(f"{frontend_base_url}/login?redirect=%2Fstudent%2Fhome", wait_until="networkidle")
    page.get_by_placeholder("请输入 11 位手机号").fill("13800000001")
    page.get_by_placeholder("请输入密码").fill("seed-password-admin-001")
    page.get_by_role("button", name="登录并继续").click()


@pytest.mark.e2e
def test_super_admin_login_from_student_entry_redirects_to_admin_home(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    if shutil.which("npm") is None:
        pytest.skip("未检测到 npm，跳过前端 UI 自动化用例。")

    db_path = tmp_path_factory.mktemp("cross-entry-login") / "question_bank.db"
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
    backend_env = dict(os.environ)
    backend_env["QB_CORS_ORIGINS"] = frontend_base_url
    backend_process = subprocess.Popen(
        backend_command,
        cwd=str(ROOT_DIR),
        env=backend_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    frontend_env = dict(os.environ)
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
            browser = playwright_driver.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 960})
                _login_from_student_entry(page, frontend_base_url)
                page.wait_for_url("**/admin/home")
                assert "/admin/home" in page.url
                assert "/student/" not in page.url
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
