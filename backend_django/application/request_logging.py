"""统一请求日志中间件：为所有后端请求补齐 request_id、耗时与状态日志。"""

from __future__ import annotations

import logging
import time
from uuid import uuid4

from .audit import request_id_from_request

logger = logging.getLogger("application.request")


def _client_ip(request) -> str:
    forwarded_for = str(request.META.get("HTTP_X_FORWARDED_FOR", "") or "").strip()
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return str(request.META.get("REMOTE_ADDR", "") or "").strip()


def _user_label(request) -> str:
    user = getattr(request, "user", None)
    if user and getattr(user, "is_authenticated", False):
        return str(getattr(user, "username", "") or "authenticated")[:64]
    return "anonymous"


def _trim_text(value: str, max_len: int) -> str:
    text = str(value or "")
    return text[:max_len]


class RequestLoggingMiddleware:
    """记录请求完成/异常日志，并回传 X-Request-ID。"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started_at = time.monotonic()
        request_id = request_id_from_request(request) or uuid4().hex
        request.request_id = request_id
        request.META["REQUEST_ID"] = request_id

        method = _trim_text(getattr(request, "method", ""), 16)
        path = _trim_text(request.get_full_path(), 240)
        ip = _trim_text(_client_ip(request), 64)
        user_label = _user_label(request)
        ua = _trim_text(request.META.get("HTTP_USER_AGENT", ""), 180)

        try:
            response = self.get_response(request)
        except Exception:
            duration_ms = int((time.monotonic() - started_at) * 1000)
            logger.exception(
                "backend_request_exception method=%s path=%s request_id=%s ip=%s user=%s duration_ms=%s ua=%s",
                method,
                path,
                request_id,
                ip,
                user_label,
                duration_ms,
                ua,
            )
            raise

        duration_ms = int((time.monotonic() - started_at) * 1000)
        status_code = int(getattr(response, "status_code", 0) or 0)

        if status_code >= 500:
            level = logging.ERROR
        elif status_code >= 400:
            level = logging.WARNING
        else:
            level = logging.INFO

        logger.log(
            level,
            "backend_request_complete method=%s path=%s status=%s request_id=%s ip=%s user=%s duration_ms=%s ua=%s",
            method,
            path,
            status_code,
            request_id,
            ip,
            user_label,
            duration_ms,
            ua,
        )
        response["X-Request-ID"] = request_id
        return response
