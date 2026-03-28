from __future__ import annotations

import os
from pathlib import Path

import httpx
import pytest
import pytest_asyncio

# Keep test logs stable: disable optional local formula OCR auto-loading in tests.
# This avoids heavy third-party OCR stack initialization warnings that are unrelated
# to business assertions in the default test suites.
os.environ.setdefault("QB_FORMULA_OCR_ENGINE", "disabled")
os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

from app.main import create_app


SUITE_MARKERS = {
    "unit": "Unit tests for isolated contracts, helpers, and validation rules.",
    "integration": "Integration tests for HTTP endpoints and persistence boundaries.",
    "regression": "Regression tests that protect existing question-bank behavior.",
    "e2e": "End-to-end workflow tests that exercise full user journeys.",
}


def infer_suite_marker(relative_path: str) -> str | None:
    normalized = relative_path.replace("\\", "/")
    if normalized.startswith("tests/unit/"):
        return "unit"
    if normalized.startswith("tests/integration/"):
        return "integration"
    if normalized.startswith("tests/e2e/"):
        return "e2e"
    if normalized.startswith("tests/regression/") or normalized == "tests/test_question_bank.py":
        return "regression"
    return None


def pytest_configure(config: pytest.Config) -> None:
    for marker, description in SUITE_MARKERS.items():
        config.addinivalue_line("markers", f"{marker}: {description}")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    root = Path(str(config.rootpath)).resolve()
    for item in items:
        path = Path(str(item.fspath)).resolve()
        try:
            relative_path = path.relative_to(root).as_posix()
        except ValueError:
            continue
        marker = infer_suite_marker(relative_path)
        if marker:
            item.add_marker(getattr(pytest.mark, marker))


@pytest.fixture
def app(tmp_path: Path):
    return create_app(tmp_path / "question_bank.db")


@pytest_asyncio.fixture
async def async_client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


async def _login_token(async_client: httpx.AsyncClient, phone: str, password: str) -> str:
    response = await async_client.post(
        "/api/question-bank/auth/login/password",
        json={"phone": phone, "password": password},
    )
    assert response.status_code == 200
    return str(response.json()["data"]["accessToken"])


@pytest_asyncio.fixture
async def admin_token(async_client: httpx.AsyncClient) -> str:
    return await _login_token(async_client, "13800000001", "seed-password-admin-001")


@pytest_asyncio.fixture
async def teacher_token(async_client: httpx.AsyncClient) -> str:
    return await _login_token(async_client, "13800000002", "seed-password-teacher-001")


@pytest_asyncio.fixture
async def teacher_b_token(async_client: httpx.AsyncClient) -> str:
    return await _login_token(async_client, "13800000003", "seed-password-teacher-002")


@pytest_asyncio.fixture
async def student_token(async_client: httpx.AsyncClient) -> str:
    return await _login_token(async_client, "13800000005", "seed-password-student-001")


@pytest.fixture
def admin_auth_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def teacher_auth_headers(teacher_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {teacher_token}"}


@pytest.fixture
def teacher_b_auth_headers(teacher_b_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {teacher_b_token}"}


@pytest.fixture
def student_auth_headers(student_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {student_token}"}
