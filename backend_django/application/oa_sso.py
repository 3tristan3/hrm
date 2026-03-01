"""OA 集成登录票据服务：处理入口参数校验、票据签发与安全重定向。"""
from __future__ import annotations

import secrets
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.core import signing
from django.core.cache import cache


OA_SSO_TICKET_SIGN_SALT = "application.oa_sso.ticket"
OA_SSO_USED_TICKET_CACHE_PREFIX = "oa_sso:used:"


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_lower_set(values: list[str] | tuple[str, ...] | set[str]) -> set[str]:
    return {str(item).strip().lower() for item in (values or []) if str(item).strip()}


def oa_sso_ticket_ttl_seconds() -> int:
    return max(int(getattr(settings, "OA_SSO_TICKET_TTL_SECONDS", 120) or 120), 30)


def is_oa_sso_enabled() -> bool:
    return bool(getattr(settings, "OA_SSO_ENABLED", False))


def is_oa_sso_appid_allowed(appid: str) -> bool:
    allowed = _normalize_lower_set(getattr(settings, "OA_SSO_ALLOWED_APPIDS", []))
    if not allowed:
        return True
    return _normalize_text(appid).lower() in allowed


def is_oa_sso_ip_allowed(client_ip: str) -> bool:
    allowed = _normalize_lower_set(getattr(settings, "OA_SSO_ALLOWED_IPS", []))
    if not allowed:
        return True
    return _normalize_text(client_ip).lower() in allowed


def resolve_oa_sso_client_ip(request) -> str:
    x_real_ip = _normalize_text(request.META.get("HTTP_X_REAL_IP"))
    if x_real_ip:
        return x_real_ip
    x_forwarded_for = _normalize_text(request.META.get("HTTP_X_FORWARDED_FOR"))
    if x_forwarded_for:
        parts = [item.strip() for item in x_forwarded_for.split(",") if item.strip()]
        if parts:
            # 取最后一跳，规避客户端伪造首位 X-Forwarded-For 的场景。
            return _normalize_text(parts[-1])
    return _normalize_text(request.META.get("REMOTE_ADDR"))


def merge_oa_sso_payload(request) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    query_params = getattr(request, "query_params", None)
    if query_params is not None:
        for key in query_params.keys():
            payload[key] = query_params.get(key)
    data = getattr(request, "data", None)
    if isinstance(data, dict):
        for key, value in data.items():
            payload[key] = value
    return payload


def pick_oa_sso_username(payload: dict[str, Any]) -> str:
    for key in ("username", "loginid", "oa_loginid", "user", "account"):
        value = _normalize_text(payload.get(key))
        if value:
            return value
    return ""


def create_oa_sso_login_ticket(*, user_id: int, username: str, appid: str = "", source_ip: str = "") -> str:
    payload = {
        "jti": secrets.token_urlsafe(12),
        "user_id": int(user_id),
        "username": _normalize_text(username),
        "appid": _normalize_text(appid),
        "source_ip": _normalize_text(source_ip),
    }
    return signing.dumps(
        payload,
        salt=OA_SSO_TICKET_SIGN_SALT,
        compress=True,
    )


def consume_oa_sso_login_ticket(ticket: str) -> dict[str, Any] | None:
    normalized_ticket = _normalize_text(ticket)
    if not normalized_ticket:
        return None
    try:
        payload = signing.loads(
            normalized_ticket,
            salt=OA_SSO_TICKET_SIGN_SALT,
            max_age=oa_sso_ticket_ttl_seconds(),
        )
    except signing.BadSignature:
        return None
    except signing.SignatureExpired:
        return None
    if not isinstance(payload, dict):
        return None
    jti = _normalize_text(payload.get("jti"))
    if not jti:
        return None
    used_key = f"{OA_SSO_USED_TICKET_CACHE_PREFIX}{jti}"
    if cache.get(used_key):
        return None
    cache.set(used_key, "1", timeout=oa_sso_ticket_ttl_seconds())
    return payload


def _sanitize_relative_url(raw_url: str) -> str:
    split_result = urlsplit(raw_url)
    path = split_result.path or "/"
    if not path.startswith("/"):
        path = f"/{path}"
    return urlunsplit(("", "", path, split_result.query, split_result.fragment))


def sanitize_oa_sso_next_url(next_url: str) -> str:
    default_url = _normalize_text(getattr(settings, "OA_SSO_DEFAULT_NEXT_URL", "/")) or "/"
    candidate = _normalize_text(next_url) or default_url
    split_result = urlsplit(candidate)
    if not split_result.scheme and not split_result.netloc:
        return _sanitize_relative_url(candidate)

    allowed_hosts = _normalize_lower_set(getattr(settings, "OA_SSO_ALLOWED_NEXT_HOSTS", []))
    if split_result.hostname and split_result.hostname.lower() in allowed_hosts:
        return candidate
    return _sanitize_relative_url(default_url)


def build_oa_sso_redirect_url(next_url: str, *, ticket: str) -> str:
    safe_url = sanitize_oa_sso_next_url(next_url)
    split_result = urlsplit(safe_url)
    query_items = [
        (key, value)
        for key, value in parse_qsl(split_result.query, keep_blank_values=True)
        if key != "oa_ticket"
    ]
    query_items.append(("oa_ticket", ticket))
    query = urlencode(query_items, doseq=True)
    return urlunsplit(
        (split_result.scheme, split_result.netloc, split_result.path, query, split_result.fragment)
    )
