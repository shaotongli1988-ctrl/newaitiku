from __future__ import annotations

# Observability note: error mapping changes should keep log/trace/metric semantics consistent across the API surface.
from fastapi import Request
from fastapi.responses import JSONResponse

from app.contracts import BaseResponse, QUESTION_ERROR_CODES

def _error_codes(namespace: str) -> dict[str, str]:
    return {
        "NOT_FOUND": f"{namespace}_NOT_FOUND",
        "FORBIDDEN": f"{namespace}_FORBIDDEN",
        "VALIDATION_FAILED": f"{namespace}_VALIDATION_FAILED",
        "INVALID_STATUS": f"{namespace}_INVALID_STATUS",
        "DATABASE_ERROR": f"{namespace}_DATABASE_ERROR",
    }


TASK_ERROR_CODES = _error_codes("TASK")
declared_error_code_messages = {
    "AUTH_UNAUTHORIZED": "Authentication is required or has expired.",
    "QUESTION_NOT_FOUND": "Question resource was not found.",
    "QUESTION_FORBIDDEN": "Question action is forbidden.",
    "QUESTION_VALIDATION_FAILED": "Question payload validation failed.",
    "QUESTION_INVALID_STATUS": "Question status transition is invalid.",
    "QUESTION_DATABASE_ERROR": "Question persistence failed.",
    "QUESTION_DEPENDENCY_FAILED": "Question dependency failed.",
    "TASK_NOT_FOUND": "Task resource was not found.",
    "TASK_FORBIDDEN": "Task action is forbidden.",
    "TASK_VALIDATION_FAILED": "Task payload validation failed.",
    "ERROR_PROFILE_INCOMPLETE": "Profile is incomplete.",
}
declared_error_code_values = ("AUTH_UNAUTHORIZED", "QUESTION_NOT_FOUND", "QUESTION_FORBIDDEN", "QUESTION_VALIDATION_FAILED", "QUESTION_INVALID_STATUS", "QUESTION_DATABASE_ERROR", "QUESTION_DEPENDENCY_FAILED", "TASK_NOT_FOUND", "TASK_FORBIDDEN", "TASK_VALIDATION_FAILED", "ERROR_PROFILE_INCOMPLETE")


class QuestionBankError(Exception):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def _question_bank_error(code: str, message: str, status_code: int) -> QuestionBankError:
    return QuestionBankError(code, message, status_code)


def not_found(message: str) -> QuestionBankError:
    return _question_bank_error(QUESTION_ERROR_CODES["NOT_FOUND"], message, 404)


def forbidden(message: str) -> QuestionBankError:
    return _question_bank_error(QUESTION_ERROR_CODES["FORBIDDEN"], message, 403)


def unauthorized(message: str) -> QuestionBankError:
    return _question_bank_error("AUTH_UNAUTHORIZED", message, 401)


def validation_failed(message: str) -> QuestionBankError:
    return _question_bank_error(QUESTION_ERROR_CODES["VALIDATION_FAILED"], message, 422)


def profile_incomplete(message: str) -> QuestionBankError:
    return _question_bank_error("ERROR_PROFILE_INCOMPLETE", message, 422)


def invalid_status(message: str) -> QuestionBankError:
    return _question_bank_error(QUESTION_ERROR_CODES["INVALID_STATUS"], message, 422)


def database_error(message: str) -> QuestionBankError:
    return _question_bank_error(QUESTION_ERROR_CODES["DATABASE_ERROR"], message, 500)


def failed_dependency(message: str) -> QuestionBankError:
    return _question_bank_error("QUESTION_DEPENDENCY_FAILED", message, 424)


def task_not_found(message: str) -> QuestionBankError:
    return _question_bank_error(TASK_ERROR_CODES["NOT_FOUND"], message, 404)


def task_forbidden(message: str) -> QuestionBankError:
    return _question_bank_error(TASK_ERROR_CODES["FORBIDDEN"], message, 403)


def task_validation_failed(message: str) -> QuestionBankError:
    return _question_bank_error(TASK_ERROR_CODES["VALIDATION_FAILED"], message, 422)


async def question_bank_exception_handler(_request: Request, exc: QuestionBankError):
    payload = BaseResponse(code=exc.code, message=exc.message, data=None).model_dump()
    return JSONResponse(payload, status_code=exc.status_code)
