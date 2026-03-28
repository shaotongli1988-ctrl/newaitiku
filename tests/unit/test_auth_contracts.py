from __future__ import annotations

from types import SimpleNamespace

import pytest
from starlette.requests import Request

from app.auth import Actor, get_actor, require_student, require_super_admin
from app.contracts import SUCCESS_CODE, SUCCESS_MESSAGE, pagination, success
from app.exceptions import QuestionBankError


def fake_request() -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
        "query_string": b"",
        "app": SimpleNamespace(state=SimpleNamespace(service=None)),
    }
    return Request(scope)


def test_get_actor_uses_student_default_user_id() -> None:
    actor = get_actor(request=fake_request(), role="student")
    assert actor.role == "student"
    assert actor.user_id == "student-001"


def test_get_actor_uses_cookie_role_and_user_id_when_query_absent() -> None:
    actor = get_actor(request=fake_request(), qb_role="teacher", qb_user_id="teacher-009")
    assert actor.role == "teacher"
    assert actor.user_id == "teacher-009"


def test_get_actor_rejects_invalid_role() -> None:
    with pytest.raises(QuestionBankError) as exc_info:
        get_actor(request=fake_request(), role="invalid-role", userId="user-001")
    assert exc_info.value.code == "QUESTION_VALIDATION_FAILED"


def test_success_and_pagination_keep_fixed_contract() -> None:
    body = success({"ok": True})
    page = pagination([{"id": "question-001"}], page=2, size=10, total=21)
    assert body == {"code": SUCCESS_CODE, "message": SUCCESS_MESSAGE, "data": {"ok": True}}
    assert page == {"items": [{"id": "question-001"}], "page": 2, "size": 10, "total": 21}


def test_role_guards_raise_fixed_forbidden_error() -> None:
    with pytest.raises(QuestionBankError) as student_error:
        require_super_admin(Actor(role="student", user_id="student-001"))
    assert student_error.value.code == "QUESTION_FORBIDDEN"

    with pytest.raises(QuestionBankError) as teacher_error:
        require_student(Actor(role="teacher", user_id="teacher-001"))
    assert teacher_error.value.code == "QUESTION_FORBIDDEN"
