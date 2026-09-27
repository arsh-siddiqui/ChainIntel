"""Consistent API response envelope: {success, data, meta, error}."""
from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger("envelope")


class AppError(Exception):
    """Application error carrying an HTTP status and a stable error code."""

    def __init__(self, status_code: int, code: str, message: str, meta: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.meta = meta or {}


def ok(data: Any, meta: dict | None = None) -> dict:
    return {"success": True, "data": data, "meta": meta or {}, "error": None}


def err(code: str, message: str, meta: dict | None = None) -> dict:
    return {"success": False, "data": None, "meta": meta or {}, "error": {"code": code, "message": message}}


def error_response(status_code: int, code: str, message: str, meta: dict | None = None) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=err(code, message, meta))


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return error_response(exc.status_code, exc.code, exc.message, exc.meta)


async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    return error_response(exc.status_code, "HTTP_ERROR", str(exc.detail))


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    summary = "; ".join(
        f"{'.'.join(str(loc) for loc in e.get('loc', []))}: {e.get('msg', 'invalid')}" for e in exc.errors()[:5]
    )
    return error_response(422, "VALIDATION_ERROR", summary or "Invalid request payload.")


async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    # Never leak stack traces to clients; log them server-side only.
    logger.exception("Unhandled server error: %s", exc)
    return error_response(500, "INTERNAL_ERROR", "An unexpected internal error occurred.")
