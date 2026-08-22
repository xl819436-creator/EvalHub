"""EvalHub 统一业务异常与 FastAPI 异常处理器（Day 16）。"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas import ErrorResponse


class AppError(Exception):
    """业务异常基类。"""

    status_code = 500
    code = "INTERNAL_ERROR"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(AppError):
    """资源不存在 -> 404。"""

    status_code = 404
    code = "NOT_FOUND"


class ConflictError(AppError):
    """资源冲突（如重复创建）-> 409。"""

    status_code = 409
    code = "CONFLICT"


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _error_body(code: str, message: str, request_id: str, details: dict | None) -> dict:
    return ErrorResponse(
        code=code,
        message=message,
        request_id=request_id,
        details=details,
    ).model_dump()


def register_error_handlers(app: FastAPI) -> None:
    """把业务异常、HTTP 错误、校验错误统一成 ErrorResponse 结构。"""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, _request_id(request), exc.details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body("HTTP_ERROR", message, _request_id(request), None),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = []
        for item in exc.errors():
            cleaned = {key: value for key, value in item.items() if key != "ctx"}
            if isinstance(item.get("ctx"), dict):
                cleaned["ctx"] = {
                    key: (str(value) if not isinstance(value, (str, int, float, bool)) else value)
                    for key, value in item["ctx"].items()
                }
            errors.append(cleaned)
        return JSONResponse(
            status_code=422,
            content=_error_body(
                "VALIDATION_ERROR",
                "request validation failed",
                _request_id(request),
                {"errors": errors},
            ),
        )